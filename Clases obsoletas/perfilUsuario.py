#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import mysql.connector
from mysql.connector import Error

# Ajusta estos valores a tu configuración
DB_CONFIG = {
    'host': '127.0.0.1',
    'user': 'root',
    'password': '',
    'database': 'iasocial'
}

def crear_tablas(cursor):
    """
    Crea las tablas necesarias si no existen. 
    Se ajusta 'perfil_usuario' para que 'usuario' sea PRIMARY KEY.
    """
    # Tabla perfil_usuario
    create_perfil_usuario = """
    CREATE TABLE IF NOT EXISTS `perfil_usuario` (
      `usuario` VARCHAR(255) NOT NULL,
      `rasgos_personalidad` TEXT DEFAULT NULL,
      `sentimiento_dominante` VARCHAR(50) DEFAULT NULL,
      `etiquetas` TEXT DEFAULT NULL,
      `timestamp` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
      PRIMARY KEY (`usuario`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
    """

    # Tabla user_match para similitudes
    create_user_match = """
    CREATE TABLE IF NOT EXISTS `user_match` (
      `id` INT(11) NOT NULL AUTO_INCREMENT,
      `usuario1` VARCHAR(255) NOT NULL,
      `usuario2` VARCHAR(255) NOT NULL,
      `similitud` FLOAT NOT NULL,
      `timestamp` DATETIME DEFAULT CURRENT_TIMESTAMP,
      PRIMARY KEY (`id`),
      UNIQUE KEY `unique_pair` (`usuario1`,`usuario2`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
    """

    cursor.execute(create_perfil_usuario)
    cursor.execute(create_user_match)


def actualizar_perfil_usuario(cursor):
    """
    Actualiza la tabla perfil_usuario con la última información disponible
    en:
      - resumen_usuario (rasgos de personalidad)
      - sentimiento_ia (sentimiento más reciente)
      - chat_memoria (etiquetas basadas en la última interacción)
    De manera que cada usuario quede con una sola fila (PRIMARY KEY = usuario).
    """

    # ---------------------------------------------------------------------
    # 1. Actualizar/inserción de rasgos de personalidad desde resumen_usuario
    #
    #    Usamos ON DUPLICATE KEY UPDATE para asegurarnos de que, si el usuario
    #    ya existe en perfil_usuario, se actualicen sus rasgos.
    # ---------------------------------------------------------------------
    upsert_personalidad = """
    INSERT INTO perfil_usuario (usuario, rasgos_personalidad)
    SELECT r.usuario, r.personalidad_us
    FROM resumen_usuario r
    /* Podrías filtrar si hay múltiples filas por usuario. Aquí asume 1 fila x usuario. */
    ON DUPLICATE KEY UPDATE
      rasgos_personalidad = VALUES(rasgos_personalidad),
      timestamp = CURRENT_TIMESTAMP;
    """
    cursor.execute(upsert_personalidad)

    # ---------------------------------------------------------------------
    # 2. Actualizar sentimiento dominante con el registro más reciente.
    #
    #    Para cada usuario, tomamos el 'sentimiento_texto' del último timestamp
    #    en sentimiento_ia. Hacemos un JOIN con una subconsulta que obtiene
    #    el max(timestamp) por usuario.
    # ---------------------------------------------------------------------
    update_sentimiento_sql = """
    UPDATE perfil_usuario p
    JOIN (
      SELECT s1.usuario, s1.sentimiento_texto
      FROM sentimiento_ia s1
      INNER JOIN (
        SELECT usuario, MAX(`timestamp`) as max_ts
        FROM sentimiento_ia
        GROUP BY usuario
      ) s2
      ON s1.usuario = s2.usuario AND s1.timestamp = s2.max_ts
    ) ult
    ON p.usuario = ult.usuario
    SET p.sentimiento_dominante = ult.sentimiento_texto,
        p.timestamp = CURRENT_TIMESTAMP;
    """
    cursor.execute(update_sentimiento_sql)

    # ---------------------------------------------------------------------
    # 3. Extraer etiquetas (keywords) de la ÚLTIMA interacción en chat_memoria.
    #
    #    - Tomamos el último registro (por timestamp) para cada usuario.
    #    - Analizamos pregunta_us + respuesta_ia buscando keywords.
    #    - Actualizamos el campo 'etiquetas' en perfil_usuario con las
    #      nuevas palabras clave (sin duplicar usuario).
    # ---------------------------------------------------------------------
    select_ultimo_chat = """
    SELECT c.usuario, c.pregunta_us, c.respuesta_ia
    FROM chat_memoria c
    INNER JOIN (
      SELECT usuario, MAX(timestamp) as max_ts
      FROM chat_memoria
      GROUP BY usuario
    ) tmax
      ON c.usuario = tmax.usuario AND c.timestamp = tmax.max_ts;
    """
    cursor.execute(select_ultimo_chat)
    rows = cursor.fetchall()  # [(usuario, pregunta_us, respuesta_ia), ...]

    # Diccionario: { user: set_de_etiquetas }
    etiquetas_usuarios = {}

    # Definir lista de keywords relevantes
    posibles_etiquetas = [
        "rock", "fútbol", "videojuegos", "cine", "anime",
        "programación", "música", "viajes", "senderismo"
    ]

    for (usuario, pregunta_us, respuesta_ia) in rows:
        # Combina la pregunta y la respuesta en minúscula
        texto = f"{pregunta_us} {respuesta_ia}".lower() if pregunta_us and respuesta_ia else ""
        if usuario not in etiquetas_usuarios:
            etiquetas_usuarios[usuario] = set()

        for kw in posibles_etiquetas:
            if kw in texto:
                etiquetas_usuarios[usuario].add(kw)

    # ---------------------------------------------------------------------
    # 4. Para cada usuario, actualizamos (con ON DUPLICATE KEY) el campo etiquetas.
    #    - Si el usuario no existe en perfil_usuario, se inserta.
    #    - Si ya existe, se hace un UPDATE de etiquetas concatenadas.
    #
    #    Sin embargo, como ya hicimos un upsert en el paso 1, es probable
    #    que todos existan. Para no duplicar, podremos:
    #      - Consultar las etiquetas que ya tiene
    #      - Combinar con las nuevas
    #      - Hacer UPDATE final
    # ---------------------------------------------------------------------
    for user, set_etiquetas in etiquetas_usuarios.items():
        if not set_etiquetas:
            continue

        # Primero, obtén las etiquetas actuales que tiene en la BD
        cursor.execute("SELECT etiquetas FROM perfil_usuario WHERE usuario = %s", (user,))
        row = cursor.fetchone()

        if row is not None:
            etiquetas_actuales = row[0] if row[0] else ""
        else:
            etiquetas_actuales = ""

        etiquetas_actuales_set = set(x.strip() for x in etiquetas_actuales.split(',') if x.strip())
        # Unión con las nuevas
        etiquetas_finales = etiquetas_actuales_set.union(set_etiquetas)
        etiquetas_str = ",".join(etiquetas_finales)

        # Hacemos un UPDATE directo
        update_et_sql = """
        UPDATE perfil_usuario
        SET etiquetas = %s,
            timestamp = CURRENT_TIMESTAMP
        WHERE usuario = %s;
        """
        cursor.execute(update_et_sql, (etiquetas_str, user))


def calcular_similitud_y_guardar(cursor):
    """
    Calcula la similitud entre los usuarios en base a sus etiquetas.
    similitud = (numEtiquetasEnComun / numEtiquetasEnUnion) * 100
    Los resultados se guardan/actualizan en user_match.
    """

    # 1. Obtenemos todos los usuarios y sus etiquetas desde perfil_usuario
    sql_perfil = "SELECT usuario, etiquetas FROM perfil_usuario;"
    cursor.execute(sql_perfil)
    rows = cursor.fetchall()

    perfil_data = {}
    for (usuario, et) in rows:
        if et is None:
            et = ""
        etiqueta_list = [x.strip() for x in et.split(',') if x.strip()]
        perfil_data[usuario] = set(etiqueta_list)

    # 2. Calculamos la similitud para cada par de usuarios
    usuarios = list(perfil_data.keys())

    for i in range(len(usuarios)):
        for j in range(i+1, len(usuarios)):
            u1 = usuarios[i]
            u2 = usuarios[j]

            tags1 = perfil_data[u1]
            tags2 = perfil_data[u2]

            interseccion = tags1.intersection(tags2)
            union = tags1.union(tags2)

            if len(union) == 0:
                similitud = 0.0
            else:
                similitud = (len(interseccion) / len(union)) * 100

            # 3. Guardamos en user_match con ON DUPLICATE KEY
            insert_match_sql = """
            INSERT INTO user_match (usuario1, usuario2, similitud)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE similitud = VALUES(similitud);
            """
            cursor.execute(insert_match_sql, (u1, u2, similitud))


def main():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            print("Conectado a la base de datos.")
            cursor = connection.cursor()

            # 1. Crear tablas si no existen (perfil_usuario y user_match)
            crear_tablas(cursor)
            connection.commit()

            # 2. Actualizar la tabla perfil_usuario con la información MÁS RECIENTE
            actualizar_perfil_usuario(cursor)
            connection.commit()

            # 3. Calcular la similitud (por etiquetas) y guardarla en user_match
            calcular_similitud_y_guardar(cursor)
            connection.commit()

            print("Proceso completado con éxito.")
    except Error as e:
        print("Error al conectar o ejecutar en MySQL:", e)
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("Conexión cerrada.")

if __name__ == "__main__":
    main()
