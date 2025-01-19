import ollama

class ConexionOLlama:
    def __init__(self, modelo: str = "llama3.2"):
        """
        Inicializa la conexión con OLlama.
        :param modelo: Nombre del modelo a utilizar (por defecto 'llama3.2').
        """
        self.modelo = modelo

    def enviar_mensaje(self, mensaje: str) -> str:
        """
        Envía un mensaje al modelo OLlama y obtiene una respuesta.
        :param mensaje: Mensaje de entrada del usuario.
        :return: Respuesta generada por OLlama.
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
    # Inicializar la conexión
    conexion = ConexionOLlama(modelo="llama3.2")
    
    # Interacción con el usuario
    mensaje_usuario = input("Escribe un mensaje: ")
    respuesta = conexion.enviar_mensaje(mensaje_usuario)
    
    print(f"IA: {respuesta}")
