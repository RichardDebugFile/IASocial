import ollama

class ConexionDeepSeek:
    def __init__(self, modelo: str = "deepseek-r1:8b"):
        """
        Inicializa la conexión con DeepSeek a través de OLlama.
        :param modelo: Nombre del modelo a utilizar (por defecto 'deepseek-r1:8b').
        """
        self.modelo = modelo

    def enviar_mensaje(self, mensaje: str) -> str:
        """
        Envía un mensaje al modelo DeepSeek y obtiene una respuesta.
        :param mensaje: Mensaje de entrada del usuario.
        :return: Respuesta generada por el modelo.
        """
        try:
            response = ollama.chat(
                model=self.modelo,
                messages=[
                    {"role": "user", "content": mensaje}
                ]
            )
            return response['message']['content']
        except Exception as e:
            return f"Error en la conexión: {str(e)}"

if __name__ == "__main__":
    # Inicializar la conexión con el modelo DeepSeek
    conexion = ConexionDeepSeek(modelo="deepseek-r1:8b")
    
    # Interacción con el usuario
    mensaje_usuario = input("Escribe un mensaje: ")
    respuesta = conexion.enviar_mensaje(mensaje_usuario)
    
    print(f"IA: {respuesta}")
