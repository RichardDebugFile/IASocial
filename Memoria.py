import threading
from ConexionMySQL import ConexionMySQL
from ConexionOLlama import ConexionOLlama
from ConexionDeepSeek import ConexionDeepSeek

class Memoria:
    def __init__(self, db_params, script_path="script_personalidad.txt", modelo_ia="llama3.2", modelo_resumen="deepseek-r1:8b"):
        self.db = ConexionMySQL(**db_params)
        self.db.conectar()
        self.script_personalidad = self.cargar_script(script_path)
        self.conexion_ia = ConexionOLlama(modelo=modelo_ia)
        self.conexion_resumen = ConexionDeepSeek(modelo=modelo_resumen)
        self.chat_counter = 0  # Contador para activación del resumen

    def cargar_script(self, path):
        """
        Carga el script de personalidad base desde un archivo.
        :param path: Ruta al archivo de script.
        :return: Contenido del script.
        """
        try:
            with open(path, "r", encoding="utf-8") as file:
                return file.read()
        except FileNotFoundError:
            return "No se encontró el archivo de personalidad base."

    def guardar_chat(self, usuario, pregunta, respuesta):
        query = """
        INSERT INTO chat_memoria (usuario, pregunta_us, respuesta_ia)
        VALUES (%s, %s, %s);
        """
        self.db.ejecutar_consulta(query, (usuario, pregunta, respuesta))
        self.chat_counter += 1

    def obtener_interacciones_pasadas(self, usuario, limite=10):
        """
        Obtiene las últimas interacciones del usuario desde la base de datos.
        :param usuario: Nombre del usuario.
        :param limite: Número máximo de interacciones a recuperar.
        :return: Cadena con las interacciones pasadas.
        """
        query = """
        SELECT pregunta_us, respuesta_ia FROM chat_memoria
        WHERE usuario = %s
        ORDER BY id DESC
        LIMIT %s;
        """
        resultados = self.db.ejecutar_consulta(query, (usuario, limite))
        if resultados:
            interacciones = "\n".join([f"Usuario: {pregunta}\nIA: {respuesta}" for pregunta, respuesta in resultados])
            return f"Tus interacciones pasadas fueron:\n{interacciones}"
        return ""

    def obtener_resumen_usuario(self, usuario):
        """
        Obtiene el último resumen del usuario desde la base de datos.
        :param usuario: Nombre del usuario.
        :return: Cadena con el resumen del usuario.
        """
        query = """
        SELECT resumen_temp_us FROM resumen_usuario
        WHERE usuario = %s
        ORDER BY id DESC
        LIMIT 1;
        """
        resultado = self.db.ejecutar_consulta(query, (usuario,))
        if resultado:
            return f"Resumen de conversaciones mucho más anteriores:\n{resultado[0][0]}"
        return ""

    def interactuar(self, usuario, mensaje_usuario):
        # Obtener interacciones pasadas
        interacciones_pasadas = self.obtener_interacciones_pasadas(usuario)
        
        # Obtener resumen del usuario
        resumen_usuario = self.obtener_resumen_usuario(usuario)

        # Generar contexto
        contexto = (
            f"Simularás esta personalidad:\n{self.script_personalidad}\n\n"
            f"{resumen_usuario}\n\n"
            f"{interacciones_pasadas}\n\n"
        )
        print(contexto)

        entrada_ia = f"{contexto}\nEl Usuario te dice: {mensaje_usuario}"
        respuesta_ia = self.conexion_ia.enviar_mensaje(entrada_ia)

        # Guardar chat
        self.guardar_chat(usuario, mensaje_usuario, respuesta_ia)

        return respuesta_ia

    def limpiar_respuesta(self, texto):
        import re
        texto = re.sub(r"[^\w\s,.!?]", "", texto)  # Eliminar emojis
        texto = texto.replace("Think", "").strip()
        return texto

    def cerrar_conexiones(self):
        """
        Cierra todas las conexiones abiertas (MySQL).
        """
        self.db.cerrar_conexion()