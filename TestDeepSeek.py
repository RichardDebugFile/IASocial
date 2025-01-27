from ConexionDeepSeek import ConexionDeepSeek
from ConexionMySQL import ConexionMySQL
import re


class TestDeepSeek:
    def __init__(self, db_params, modelo_resumen="deepseek-r1:8b"):
        """
        Inicializa la prueba para DeepSeek.
        :param db_params: Parámetros para la conexión a MySQL.
        :param modelo_resumen: Modelo de IA para resúmenes (por defecto 'deepseek-r1:8b').
        """
        self.db = ConexionMySQL(**db_params)
        self.db.conectar()
        self.conexion_resumen = ConexionDeepSeek(modelo=modelo_resumen)

    def obtener_chats(self, usuario, limite=10):
        """
        Obtiene los últimos chats de un usuario de la base de datos.
        :param usuario: Nombre del usuario.
        :param limite: Número máximo de chats a obtener (por defecto 10).
        :return: Lista de chats.
        """
        query = """
        SELECT pregunta_us, respuesta_ia
        FROM chat_memoria
        WHERE usuario = %s
        ORDER BY id DESC
        LIMIT %s;
        """
        return self.db.ejecutar_consulta(query, (usuario, limite))

    def guardar_resumen(self, usuario, resumen):
        """
        Guarda el resumen generado en la tabla 'resumen_usuario'.
        :param usuario: Nombre del usuario.
        :param resumen: Resumen generado por DeepSeek.
        """
        query = """
        INSERT INTO resumen_usuario (usuario, resumen_temp_us, personalidad_us)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE resumen_temp_us = %s, personalidad_us = %s;
        """
        personalidad = "Personalidad generada: Reflexiva y curiosa."  # Ejemplo de personalidad
        self.db.ejecutar_consulta(query, (usuario, resumen, personalidad, resumen, personalidad))

    def actualizar_sentimientos(self, usuario):
        """
        Actualiza los sentimientos en la tabla 'sentimiento_ia' basándose en las interacciones.
        :param usuario: Nombre del usuario.
        """
        query_historial = """
        SELECT total_sentimiento FROM sentimiento_ia WHERE usuario = %s ORDER BY id DESC LIMIT 1;
        """
        resultado = self.db.ejecutar_consulta(query_historial, (usuario,))
        historial = resultado[0][0].split(",") if resultado else []

        # Generar un sentimiento aleatorio para probar (puede ser reemplazado por un análisis real)
        import random
        sentimiento = random.choice([1, 2, 3, 4, 5, 6, 7])  # Alegría, tristeza, etc.

        # Actualizar el historial
        historial.append(str(sentimiento))
        if len(historial) > 20:
            historial.pop(0)
        sentimiento_principal = max(set(historial), key=historial.count)
        nuevo_historial = ",".join(historial)

        # Insertar o actualizar sentimiento
        query_update = """
        INSERT INTO sentimiento_ia (usuario, sentimiento_principal, total_sentimiento)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE sentimiento_principal = %s, total_sentimiento = %s;
        """
        self.db.ejecutar_consulta(query_update, (usuario, sentimiento_principal, nuevo_historial, sentimiento_principal, nuevo_historial))

    def generar_resumen(self, usuario):
        """
        Genera un resumen utilizando DeepSeek, lo imprime y almacena en la base de datos.
        :param usuario: Nombre del usuario.
        """
        chats = self.obtener_chats(usuario)
        if not chats:
            print(f"No se encontraron chats para el usuario '{usuario}'.")
            return

        # Combina los chats en un solo texto para enviar a DeepSeek
        conversaciones = "\n".join([f"Usuario: {chat[0]}\nIA: {chat[1]}" for chat in chats])
        print("Chats obtenidos:")
        print(conversaciones)

        # Enviar la solicitud a DeepSeek
        print("\nEnviando a DeepSeek...")
        resumen = self.conexion_resumen.enviar_mensaje(
            "Por favor, genera un resumen conciso de 20 palabras o menos del siguiente diálogo en español:\n" + conversaciones
        )

        # Imprimir la respuesta de DeepSeek
        print("Respuesta de DeepSeek:")
        print(resumen)

        # Limpia el resumen para eliminar etiquetas <think> y su contenido
        def eliminar_think(texto):
            return re.sub(r"<think>.*?</think>", "", texto, flags=re.DOTALL).strip()

        resumen_limpio = eliminar_think(resumen)
        print("\nResumen generado por DeepSeek (limpio):")
        print(resumen_limpio)

        # Guardar resumen en la tabla 'resumen_usuario'
        self.guardar_resumen(usuario, resumen_limpio)

        # Actualizar sentimientos
        self.actualizar_sentimientos(usuario)




    

    def cerrar_conexion(self):
        """
        Cierra la conexión a la base de datos.
        """
        self.db.cerrar_conexion()


if __name__ == "__main__":
    # Configuración de la base de datos
    db_params = {
        "host": "127.0.0.1",
        "user": "root",  # Cambia esto por el usuario de tu base de datos
        "password": "",  # Cambia esto por tu contraseña
        "database": "iasocial"
    }

    # Inicializar la prueba
    test = TestDeepSeek(db_params=db_params)

    # Solicitar el nombre del usuario
    usuario = input("Por favor, ingresa el nombre del usuario para probar los resúmenes: ").strip()

    # Generar el resumen
    test.generar_resumen(usuario)

    # Cerrar conexión
    test.cerrar_conexion()
