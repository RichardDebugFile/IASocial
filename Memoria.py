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

    def actualizar_sentimiento(self, usuario, sentimiento):
        query_historial = """
        SELECT total_sentimiento FROM sentimiento_ia WHERE usuario = %s ORDER BY id DESC LIMIT 1;
        """
        resultado = self.db.ejecutar_consulta(query_historial, (usuario,))
        historial = resultado[0][0].split(",") if resultado else []

        # Actualizar historial y sentimiento principal
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
        query = """
        SELECT pregunta_us, respuesta_ia FROM chat_memoria WHERE usuario = %s ORDER BY id DESC LIMIT 10;
        """
        chats = self.db.ejecutar_consulta(query, (usuario,))
        if chats:
            conversaciones = "\n".join([f"Usuario: {c[0]}\nIA: {c[1]}" for c in chats])
            resumen = self.conexion_resumen.enviar_mensaje(f"Resumen del chat:\n{conversaciones}")
            resumen_limpio = self.limpiar_respuesta(resumen)

            # Guardar el resumen en la tabla chat_memoria
            query_update = """
            UPDATE chat_memoria SET resumen_temp_ia = %s WHERE usuario = %s ORDER BY id DESC LIMIT 1;
            """
            self.db.ejecutar_consulta(query_update, (resumen_limpio, usuario))

            # Eliminar los 10 chats más antiguos
            query_delete = """
            DELETE FROM chat_memoria WHERE usuario = %s ORDER BY id ASC LIMIT 10;
            """
            self.db.ejecutar_consulta(query_delete, (usuario,))

    def interactuar(self, usuario, mensaje_usuario):
        # Obtener sentimiento principal y contexto
        query = """
        SELECT sentimiento_principal FROM sentimiento_ia WHERE usuario = %s ORDER BY id DESC LIMIT 1;
        """
        resultado = self.db.ejecutar_consulta(query, (usuario,))
        sentimiento_principal = resultado[0][0] if resultado else 1

        # Generar contexto
        contexto = f"Sentimiento principal: {sentimiento_principal}\n{self.script_personalidad}"

        entrada_ia = f"{contexto}\nUsuario: {mensaje_usuario}"
        respuesta_ia = self.conexion_ia.enviar_mensaje(entrada_ia)

        # Guardar chat
        self.guardar_chat(usuario, mensaje_usuario, respuesta_ia)

        # Resumen automático cada 10 chats
        if self.chat_counter >= 10:
            threading.Thread(target=self.generar_resumen, args=(usuario,), daemon=True).start()
            self.chat_counter = 0

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
