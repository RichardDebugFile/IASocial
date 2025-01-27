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

    def obtener_chats_usuario(self, usuario, limite=10):
        """
        Obtiene los últimos mensajes del usuario desde la base de datos.
        :param usuario: Nombre del usuario.
        :param limite: Número máximo de mensajes a obtener (por defecto 10).
        :return: Lista de mensajes del usuario.
        """
        query = """
        SELECT pregunta_us
        FROM chat_memoria
        WHERE usuario = %s
        ORDER BY id DESC
        LIMIT %s;
        """
        return self.db.ejecutar_consulta(query, (usuario, limite))

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

    def guardar_resumen_temp(self, usuario, resumen):
        """
        Guarda un nuevo resumen general (resumen_temp_us) en la tabla 'resumen_usuario' con un identificador único.
        :param usuario: Nombre del usuario.
        :param resumen: Resumen generado por DeepSeek.
        """
        query = """
        INSERT INTO resumen_usuario (usuario, resumen_temp_us, timestamp)
        VALUES (%s, %s, NOW());
        """
        self.db.ejecutar_consulta(query, (usuario, resumen))

    def guardar_resumen_y_personalidad(self, usuario, resumen, personalidad):
        """
        Guarda un nuevo resumen del usuario y su personalidad en la tabla 'resumen_usuario' con un identificador único.
        :param usuario: Nombre del usuario.
        :param resumen: Resumen generado por DeepSeek.
        :param personalidad: Personalidad interpretada del usuario.
        """
        query = """
        INSERT INTO resumen_usuario (usuario, resumen_us, personalidad_us, timestamp)
        VALUES (%s, %s, %s, NOW());
        """
        self.db.ejecutar_consulta(query, (usuario, resumen, personalidad))

    def interpretar_personalidad(self, resumen_usuario):
        """
        Interpreta la personalidad del usuario a partir de su resumen.
        :param resumen_usuario: Resumen generado del usuario.
        :return: Personalidad interpretada.
        """
        try:
            print("\nInterpretando la personalidad del usuario...")
            personalidad = self.conexion_resumen.enviar_mensaje(
                f"Analiza el siguiente texto y determina si la personalidad refleja características como optimista, renegada, celosa, positiva, peligrosa, etc. Proporciona solo una palabra o frase: \n{resumen_usuario}"
            )
            return personalidad.strip()
        except Exception as e:
            print(f"Error al interpretar la personalidad: {e}")
            return "Desconocida"

    def generar_resumen_temp_us(self, usuario):
        """
        Genera un resumen general (resumen_temp_us) basado en todas las interacciones del usuario.
        :param usuario: Nombre del usuario.
        """
        chats = self.obtener_chats(usuario, limite=10)  # Limitar a las últimas 10 interacciones
        if not chats:
            print(f"No se encontraron chats para el usuario '{usuario}'.")
            return

        # Combina los chats en un solo texto para enviar a DeepSeek
        conversaciones = "\n".join([f"Usuario: {chat[0]}\nIA: {chat[1]}" for chat in chats])
        print("Chats obtenidos:")
        print(conversaciones)

        # Enviar la solicitud a DeepSeek con manejo de errores
        try:
            print("\nEnviando a DeepSeek para generar resumen general...")
            resumen = self.conexion_resumen.enviar_mensaje(
                f"Por favor, genera un resumen conciso de 40 palabras o menos del siguiente diálogo en español:\n{conversaciones}"
            )
            print("Resumen general generado por DeepSeek:")
            print(resumen)
        except Exception as e:
            print(f"Error en la conexión con DeepSeek: {e}")
            resumen = "Error en la conexión con DeepSeek"

        # Limpia el resumen para eliminar etiquetas <think> y su contenido
        def eliminar_think(texto):
            return re.sub(r"<think>.*?</think>", "", texto, flags=re.DOTALL).strip()

        resumen_limpio = eliminar_think(resumen)
        print("\nResumen limpio generado por DeepSeek:")
        print(resumen_limpio)

        # Guardar resumen en la tabla 'resumen_usuario'
        self.guardar_resumen_temp(usuario, resumen_limpio)

    def generar_resumen_usuario(self, usuario):
        """
        Genera un resumen solo del usuario y guarda su personalidad interpretada.
        :param usuario: Nombre del usuario.
        """
        chats_usuario = self.obtener_chats_usuario(usuario, limite=10)  # Limitar a las últimas 10 interacciones
        if not chats_usuario:
            print(f"No se encontraron mensajes para el usuario '{usuario}'.")
            return

        # Combina los mensajes del usuario en un solo texto para enviar a DeepSeek
        mensajes_usuario = "\n".join([chat[0] for chat in chats_usuario])
        print("Mensajes obtenidos del usuario:")
        print(mensajes_usuario)

        # Enviar la solicitud a DeepSeek para generar el resumen
        try:
            print("\nEnviando a DeepSeek para generar resumen del usuario...")
            resumen = self.conexion_resumen.enviar_mensaje(
                f"Por favor, genera un resumen conciso de 40 palabras o menos basado únicamente en los siguientes mensajes del usuario en español:\n{mensajes_usuario}"
            )
            print("Resumen generado por DeepSeek:")
            print(resumen)
        except Exception as e:
            print(f"Error en la conexión con DeepSeek: {e}")
            resumen = "Error en la conexión con DeepSeek"

        # Limpia el resumen para eliminar etiquetas <think> y su contenido
        def eliminar_think(texto):
            return re.sub(r"<think>.*?</think>", "", texto, flags=re.DOTALL).strip()

        resumen_limpio = eliminar_think(resumen)
        print("\nResumen limpio generado por DeepSeek:")
        print(resumen_limpio)

        # Interpretar la personalidad del usuario
        personalidad = self.interpretar_personalidad(resumen_limpio)
        print("Personalidad interpretada:", personalidad)

        # Guardar resumen y personalidad en la base de datos
        self.guardar_resumen_y_personalidad(usuario, resumen_limpio, personalidad)

    def procesar_usuario(self, usuario):
        """
        Ejecuta el proceso completo: genera resumen general, resumen del usuario y analiza personalidad.
        :param usuario: Nombre del usuario.
        """
        print(f"Iniciando procesamiento para el usuario: {usuario}")
        self.generar_resumen_temp_us(usuario)
        self.generar_resumen_usuario(usuario)

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
    usuario = input("Por favor, ingresa el nombre del usuario para analizar: ").strip()

    # Procesar el usuario
    test.procesar_usuario(usuario)

    # Cerrar conexión
    test.cerrar_conexion()
