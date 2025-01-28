from ConexionDeepSeek import ConexionDeepSeek
from ConexionMySQL import ConexionMySQL
import re

# Diccionario para mapear número de sentimiento a texto
SENTIMIENTO_MAP = {
    1: "Alegría",
    2: "Tristeza",
    3: "Ira",
    4: "Sorpresa",
    5: "Confianza",
    6: "Decepción",
    7: "Optimismo"
}

class AnalisisSentimientoIA:
    def __init__(self, db_params, modelo_sentimiento="deepseek-r1:8b"):
        """
        Inicializa la gestión de sentimientos con DeepSeek.
        :param db_params: Parámetros para la conexión a MySQL.
        :param modelo_sentimiento: Modelo de IA para analizar sentimientos (por defecto 'deepseek-r1:8b').
        """
        self.db = ConexionMySQL(**db_params)
        self.db.conectar()
        self.conexion_sentimiento = ConexionDeepSeek(modelo=modelo_sentimiento)

    def obtener_resumen_usuario(self, usuario):
        """
        Obtiene el último resumen del usuario desde la base de datos.
        :param usuario: Nombre del usuario.
        :return: Texto del resumen o None si no existe.
        """
        query = """
        SELECT resumen_us
        FROM resumen_usuario 
        WHERE usuario = %s
        ORDER BY id DESC
        LIMIT 1;
        """
        resultado = self.db.ejecutar_consulta(query, (usuario,))
        return resultado[0][0] if resultado else None

    def obtener_historial_sentimientos(self, usuario):
        """
        Obtiene el historial de sentimientos del usuario.
        :param usuario: Nombre del usuario.
        :return: Lista con los últimos sentimientos (separados por comas) o lista vacía.
        """
        query = """
        SELECT total_sentimiento 
        FROM sentimiento_ia
        WHERE usuario = %s
        ORDER BY id DESC
        LIMIT 1;
        """
        resultado = self.db.ejecutar_consulta(query, (usuario,))
        return resultado[0][0].split(",") if resultado else []

    def analizar_sentimiento_con_ia(self, resumen):
        """
        Envía el resumen del usuario a DeepSeek para analizar su sentimiento.
        :param resumen: Texto del resumen de la interacción.
        :return: Número del sentimiento detectado (1 a 7).
        """
        try:
            print("\n[IA] Analizando sentimiento con DeepSeek...")

            prompt = (
                "Analiza este texto y determina el sentimiento predominante del chat con UN SOLO NÚMERO. "
                "Opciones: 1=Alegría, 2=Tristeza, 3=Ira, 4=Sorpresa, 5=Confianza, 6=Decepción, 7=Optimismo. "
                "Responde solo con el número (1-7), sin explicaciones ni formato:\n"
                f"{resumen}"
            )

            print("[IA] Prompt enviado:")
            print("--------------------------------------")
            print(prompt)
            print("--------------------------------------")

            respuesta = self.conexion_sentimiento.enviar_mensaje(prompt)

            print("\n[IA] Respuesta cruda recibida:")
            print("------------------------------")
            print(respuesta)
            print("------------------------------")

            # Extraer la parte después de </think> si existe
            if '</think>' in respuesta:
                parte_respuesta = respuesta.split('</think>', 1)[-1].strip()
            else:
                parte_respuesta = respuesta

            # Buscar el último número válido en la parte relevante
            match = re.search(r'\b[1-7]\b', parte_respuesta)
            
            if match:
                return int(match.group())
            else:
                print("No se encontró un número válido (1-7) en la respuesta. Asumiendo 1 (Alegría).")
                return 1  # Por defecto, "Alegría"

        except Exception as e:
            print(f"Error al analizar el sentimiento: {e}")
            return 1

    def actualizar_sentimientos(self, usuario):
        """
        Actualiza los sentimientos en la tabla 'sentimiento_ia' basándose en la IA.
        :param usuario: Nombre del usuario.
        """
        # 1. Obtener el resumen más reciente del usuario
        resumen = self.obtener_resumen_usuario(usuario)
        if not resumen:
            print(f"❌ No se encontró resumen para el usuario {usuario}, no se actualizarán sentimientos.")
            return

        # 2. Obtener el historial de sentimientos
        historial = self.obtener_historial_sentimientos(usuario)

        # 3. Analizar el nuevo sentimiento con la IA
        nuevo_sentimiento_num = self.analizar_sentimiento_con_ia(resumen)

        # 4. Actualizar el historial (mantén un máximo de 10 sentimientos)
        historial.append(str(nuevo_sentimiento_num))
        if len(historial) > 10:
            historial.pop(0)

        # 5. Determinar el sentimiento más frecuente (sentimiento_principal)
        sentimiento_principal_num = int(max(set(historial), key=historial.count))

        # 6. Mapeo numérico a texto (p. ej. 1 -> 'Alegría')
        sentimiento_principal_texto = SENTIMIENTO_MAP.get(sentimiento_principal_num, "Desconocido")

        # 7. Convertir historial a string
        nuevo_historial = ",".join(historial)

        print("\n=== SENTIMIENTOS ACTUALIZADOS ===")
        print(f"Historial completo: {nuevo_historial}")
        print(f"Sentimiento Principal (número): {sentimiento_principal_num}")
        print(f"Sentimiento Principal (texto):  {sentimiento_principal_texto}")

        # 8. Eliminar registros anteriores del usuario y agregar el nuevo
        try:
            # Eliminar registros existentes
            delete_query = "DELETE FROM sentimiento_ia WHERE usuario = %s;"
            self.db.ejecutar_consulta(delete_query, (usuario,))
            
            # Insertar nuevo registro
            insert_query = """
            INSERT INTO sentimiento_ia (usuario, sentimiento_principal, sentimiento_texto, total_sentimiento)
            VALUES (%s, %s, %s, %s);
            """
            self.db.ejecutar_consulta(
                insert_query,
                (
                    usuario,
                    sentimiento_principal_num,
                    sentimiento_principal_texto,
                    nuevo_historial
                )
            )

        except Exception as e:
            print(f"Error en transacción de base de datos: {e}")
            raise

        print("\n✅ Sentimientos guardados exitosamente.")

    def cerrar_conexion(self):
        """
        Cierra la conexión a la base de datos.
        """
        self.db.cerrar_conexion()


# ========================
#         PRUEBA
# ========================
if __name__ == "__main__":
    # Configuración de la base de datos
    db_params = {
        "host": "127.0.0.1",
        "user": "root",
        "password": "",
        "database": "iasocial"
    }

    # Crear instancia de la clase
    sentimiento_ia = AnalisisSentimientoIA(db_params=db_params)

    # Solicitar el nombre del usuario
    usuario = input("Por favor, ingresa el nombre del usuario para analizar su sentimiento: ").strip()

    # Procesar el usuario
    sentimiento_ia.actualizar_sentimientos(usuario)

    # Cerrar conexión
    sentimiento_ia.cerrar_conexion()