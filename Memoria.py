from ConexionMySQL import ConexionMySQL
from ConexionOLlama import ConexionOLlama


class Memoria:
    def __init__(self, db_params, script_path="script_personalidad.txt", modelo_ia="llama3.2"):
        """
        Inicializa la clase Memoria para gestionar la base de datos y conectarse con la IA.
        :param db_params: Parámetros para la conexión a MySQL (diccionario con host, user, password, database).
        :param script_path: Ruta del archivo de personalidad base de la IA.
        :param modelo_ia: Modelo de IA a utilizar (por defecto 'llama3.2').
        """
        self.db = ConexionMySQL(**db_params)
        self.db.conectar()
        self.script_personalidad = self.cargar_script(script_path)
        self.conexion_ia = ConexionOLlama(modelo=modelo_ia)

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

    def obtener_sentimiento_principal(self, usuario):
        """
        Obtiene el sentimiento principal más reciente del usuario.
        :param usuario: Nombre del usuario.
        :return: Sentimiento principal o None si no hay registros.
        """
        query = """
        SELECT sentimiento_principal 
        FROM sentimiento_IA 
        WHERE usuario = %s 
        ORDER BY id DESC LIMIT 1;
        """
        resultado = self.db.ejecutar_consulta(query, (usuario,))
        return resultado[0][0] if resultado else None

    def actualizar_sentimiento(self, usuario, nuevo_sentimiento):
        """
        Actualiza la tabla de sentimiento_IA con un nuevo sentimiento.
        :param usuario: Nombre del usuario.
        :param nuevo_sentimiento: Sentimiento numérico a registrar.
        """
        query_historial = """
        SELECT total_sentimiento 
        FROM sentimiento_IA 
        WHERE usuario = %s 
        ORDER BY id DESC LIMIT 1;
        """
        resultado = self.db.ejecutar_consulta(query_historial, (usuario,))
        historial = resultado[0][0].split(",") if resultado else []

        # Actualizar el historial con el nuevo sentimiento
        historial.append(str(nuevo_sentimiento))
        if len(historial) > 20:
            historial.pop(0)
        nuevo_historial = ",".join(historial)

        # Determinar el nuevo sentimiento principal
        sentimiento_principal = max(set(historial), key=historial.count)

        # Insertar el nuevo registro
        query_insert = """
        INSERT INTO sentimiento_IA (usuario, sentimiento_principal, total_sentimiento)
        VALUES (%s, %s, %s);
        """
        self.db.ejecutar_consulta(query_insert, (usuario, sentimiento_principal, nuevo_historial))

    def generar_resumen_memoria(self, usuario):
        """
        Genera un resumen combinando la memoria del usuario y la personalidad de la IA.
        :param usuario: Nombre del usuario.
        :return: Resumen combinado.
        """
        query = """
        SELECT resumen_temp_ia, resumen_ia 
        FROM chat_memoria 
        WHERE usuario = %s 
        ORDER BY id DESC LIMIT 1;
        """
        resultado = self.db.ejecutar_consulta(query, (usuario,))
        resumen_temp_ia, resumen_ia = resultado[0] if resultado else ("", "")

        resumen_memoria = f"""
        Sentimiento principal: {self.obtener_sentimiento_principal(usuario)}
        Resumen temporal IA: {resumen_temp_ia}
        Resumen IA: {resumen_ia}
        Personalidad base: {self.script_personalidad}
        """
        return resumen_memoria

    def guardar_chat(self, usuario, pregunta, respuesta):
        """
        Guarda un chat en la tabla chat_memoria.
        :param usuario: Nombre del usuario.
        :param pregunta: Pregunta o mensaje del usuario.
        :param respuesta: Respuesta de la IA.
        """
        query = """
        INSERT INTO chat_memoria (usuario, pregunta_us, respuesta_ia)
        VALUES (%s, %s, %s);
        """
        self.db.ejecutar_consulta(query, (usuario, pregunta, respuesta))

    def interactuar(self, usuario, mensaje_usuario):
        """
        Gestiona la interacción entre el usuario y la IA, incluyendo memoria y análisis.
        :param usuario: Nombre del usuario.
        :param mensaje_usuario: Mensaje ingresado por el usuario.
        :return: Respuesta generada por la IA.
        """
        # Generar resumen memoria
        resumen_memoria = self.generar_resumen_memoria(usuario)

        # Combinar el mensaje del usuario con la memoria
        entrada_ia = f"{resumen_memoria}\nUsuario: {mensaje_usuario}"

        # Obtener respuesta de la IA
        respuesta_ia = self.conexion_ia.enviar_mensaje(entrada_ia)

        # Guardar el chat en la base de datos
        self.guardar_chat(usuario, mensaje_usuario, respuesta_ia)

        return respuesta_ia

    def cerrar_conexiones(self):
        """
        Cierra todas las conexiones abiertas (MySQL).
        """
        self.db.cerrar_conexion()
