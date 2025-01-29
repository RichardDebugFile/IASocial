from ConexionDeepSeek import ConexionDeepSeek
from ConexionMySQL import ConexionMySQL
import re
import time

class ResumenDeepSeek:
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

    def obtener_resumen_anterior(self, usuario):
        """
        Obtiene el resumen anterior del usuario, si existe.
        :param usuario: Nombre del usuario.
        :return: Resumen anterior o None si no existe.
        """
        query = """
        SELECT resumen_us
        FROM resumen_usuario
        WHERE usuario = %s
        ORDER BY timestamp DESC
        LIMIT 1;
        """
        result = self.db.ejecutar_consulta(query, (usuario,))
        return result[0][0] if result else None

    def eliminar_chats_antiguos(self, usuario, limite=10):
        """
        Elimina los chats antiguos del usuario.
        :param usuario: Nombre del usuario.
        :param limite: Número máximo de chats a eliminar (por defecto 10).
        """
        query = """
        DELETE FROM chat_memoria
        WHERE usuario = %s
        ORDER BY id ASC
        LIMIT %s;
        """
        self.db.ejecutar_consulta(query, (usuario, limite))

    def interpretar_personalidad(self, resumen_usuario):
        """
        Interpreta la personalidad del usuario a partir de su resumen.
        :param resumen_usuario: Resumen generado del usuario.
        :return: Personalidad interpretada.
        """
        try:
            print("\nInterpretando la personalidad del usuario...")
            prompt = (
                "Analiza este texto y determina la personalidad con UNA SOLA PALABRA. "
                "Opciones: optimista, pesimista, neutral, curiosa, analítica, emocional, tímida, extrovertida, cuidadosa. "
                "Responde solo con la palabra, sin explicaciones ni formato:\n"
                f"{resumen_usuario}"
            )

            print("[IA] Prompt enviado para personalidad:")
            print("--------------------------------------")
            print(prompt)
            print("--------------------------------------")

            respuesta = self.conexion_resumen.enviar_mensaje(prompt)

            print("\n[IA] Respuesta cruda recibida:")
            print("------------------------------")
            print(respuesta)
            print("------------------------------")

            # Limpiar etiquetas <think> y tomar la primera palabra
            respuesta_limpia = re.sub(r"<think>.*?</think>", "", respuesta, flags=re.DOTALL)
            palabras = respuesta_limpia.strip().split()  # Dividir por espacios
            return palabras[0].lower() if palabras else "desconocida"

        except Exception as e:
            print(f"Error al interpretar la personalidad: {e}")
            return "desconocida"

    def guardar_resumen_completo(self, usuario, resumen_temp, resumen_usuario, personalidad):
        """
        Guarda TODOS los datos en una sola fila.
        """
        query = """
        INSERT INTO resumen_usuario 
            (usuario, resumen_temp_us, resumen_us, personalidad_us, timestamp)
        VALUES (%s, %s, %s, %s, NOW());
        """
        self.db.ejecutar_consulta(query, (usuario, resumen_temp, resumen_usuario, personalidad))

    def generar_resumen_temp_us(self, usuario):
        """
        Modificado para RETORNAR el resumen en lugar de guardarlo.
        """
        print(f"\n=== GENERANDO RESUMEN TEMPORAL PARA {usuario.upper()} ===")
        chats = self.obtener_chats(usuario, limite=10)
        if not chats:
            print(f"No se encontraron chats para el usuario '{usuario}'.")
            return None

        print("\nChats recuperados de la base de datos:")
        for i, (pregunta, respuesta) in enumerate(chats, 1):
            print(f"Chat {i}:")
            print(f"  Usuario: {pregunta}")
            print(f"  IA: {respuesta}")

        conversaciones = "\n".join([f"Usuario: {chat[0]}\nIA: {chat[1]}" for chat in chats])
        
        try:
            prompt = (
                "Por favor, genera un resumen conciso de 40 palabras o menos "
                f"del siguiente diálogo en español:\n{conversaciones}"
            )
            
            print("\n[IA] Prompt enviado para resumen temporal:")
            print("-----------------------------------------")
            print(prompt)
            print("-----------------------------------------")
            
            resumen = self.conexion_resumen.enviar_mensaje(prompt)
            
            print("\n[IA] Respuesta cruda recibida:")
            print("------------------------------")
            print(resumen)
            print("------------------------------")
            
            resumen_limpio = re.sub(r"<think>.*?</think>", "", resumen, flags=re.DOTALL).strip() # Limpiar etiquetas <think>
            
            print("\nResumen temporal limpio:")
            print("------------------------")
            print(resumen_limpio)
            
            return resumen_limpio
        
        except Exception as e:
            print(f"Error en la conexión con DeepSeek: {e}")
            resumen = "Error en la conexión con DeepSeek"

        # Limpieza del resumen
        resumen_limpio = re.sub(r"<think>.*?</think>", "", resumen, flags=re.DOTALL).strip()
        return resumen_limpio

    def generar_resumen_usuario(self, usuario):
        """
        Modificado para RETORNAR ambos valores.
        """
        print(f"\n=== GENERANDO RESUMEN DE USUARIO PARA {usuario.upper()} ===")
        chats_usuario = self.obtener_chats_usuario(usuario, limite=10)

        if not chats_usuario:
            print(f"No se encontraron mensajes para el usuario '{usuario}'.")
            return None, None

        mensajes_usuario = "\n".join([chat[0] for chat in chats_usuario])
        
        try:
            prompt = (
                "Por favor, genera un resumen conciso de 40 palabras o menos "
                f"basado únicamente en los siguientes mensajes del usuario en español:\n{mensajes_usuario}"
            )
            
            print("\n[IA] Prompt enviado para resumen de usuario:")
            print("-------------------------------------------")
            print(prompt)
            print("-------------------------------------------")
            
            resumen = self.conexion_resumen.enviar_mensaje(prompt)
            
            print("\n[IA] Respuesta cruda recibida:")
            print("------------------------------")
            print(resumen)
            print("------------------------------")
            
            resumen_limpio = re.sub(r"<think>.*?</think>", "", resumen, flags=re.DOTALL).strip()
            
            print("\nResumen de usuario limpio:")
            print("--------------------------")
            print(resumen_limpio)
            
            personalidad = self.interpretar_personalidad(resumen_limpio)
            return resumen_limpio, personalidad
            
        except Exception as e:
            print(f"\n!!! Error generando resumen de usuario: {str(e)}")
            return None, None

    def verificar_chats_suficientes(self, usuario, limite=10):
        """
        Verifica si hay suficientes chats para el usuario.
        :param usuario: Nombre del usuario.
        :param limite: Número mínimo de chats requeridos (por defecto 10).
        :return: True si hay suficientes chats, False en caso contrario.
        """
        query = """
        SELECT COUNT(*) as total
        FROM chat_memoria
        WHERE usuario = %s;
        """
        result = self.db.ejecutar_consulta(query, (usuario,))
        total_chats = result[0][0] if result else 0
        return total_chats >= limite

    def procesar_usuario(self, usuario):
        """
        Proceso modificado para guardar todo en una sola operación.
        """
        print(f"\n{'='*50}")
        print(f" INICIANDO PROCESO PARA USUARIO: {usuario.upper()} ")
        print(f"{'='*50}")
        
        # Verificar si hay suficientes chats
        if not self.verificar_chats_suficientes(usuario):
            print("No hay suficientes chats para generar un resumen.")
            return
        
        # Verificar si existe un resumen anterior
        resumen_anterior = self.obtener_resumen_anterior(usuario)
        
        # Generar ambos resúmenes
        resumen_temp = self.generar_resumen_temp_us(usuario)
        if not resumen_temp:
            print("Error: No se pudo generar el resumen temporal")
            return
        
        # Combinar el resumen anterior con el nuevo resumen temporal si existe
        if resumen_anterior:
            resumen_temp = f"{resumen_anterior}\n{resumen_temp}"
        
        resumen_usuario, personalidad = self.generar_resumen_usuario(usuario)
        if not all([resumen_usuario, personalidad]):
            print("Error: No se pudo generar el resumen del usuario o la personalidad")
            return
        
        try:
            print("\n=== GUARDANDO RESULTADOS ===")
            print("Resumen Temporal:", resumen_temp[:50] + "...")
            print("Resumen Usuario:", resumen_usuario[:50] + "...")
            print("Personalidad Detectada:", personalidad)
            
            self.guardar_resumen_completo(usuario, resumen_temp, resumen_usuario, personalidad)
            print("\n✅ Datos guardados exitosamente!")
            
            # Eliminar los 10 chats antiguos
            self.eliminar_chats_antiguos(usuario)
            print("\n✅ Chats antiguos eliminados exitosamente!")
            
        except Exception as e:
            print(f"\n!!! Error crítico al guardar: {str(e)}")

    def cerrar_conexion(self):
        """Cierra la conexión a la base de datos."""
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
    test = ResumenDeepSeek(db_params=db_params)

    # Solicitar el nombre del usuario
    usuario = input("Por favor, ingresa el nombre del usuario para analizar: ").strip()

    # Procesar el usuario
    test.procesar_usuario(usuario)

    # Cerrar conexión
    test.cerrar_conexion()