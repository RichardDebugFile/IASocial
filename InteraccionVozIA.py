import speech_recognition as sr
import pyttsx3
from ConexionOLlama import ConexionOLlama

class InteraccionVozIA:
    def __init__(self, modelo_ia: str = "llama3.2"):
        """
        Inicializa la interacción por voz con la IA.
        :param modelo_ia: Modelo de IA a utilizar (por defecto 'llama3.2').
        """
        # Inicializar el reconocimiento de voz y síntesis de voz
        self.reconocedor = sr.Recognizer()
        self.sintetizador = pyttsx3.init()
        
        # Configurar la velocidad y el volumen de la voz
        self.sintetizador.setProperty('rate', 150)  # Velocidad de la voz
        self.sintetizador.setProperty('volume', 0.9)  # Volumen de la voz
        
        # Inicializar la conexión con OLlama
        self.conexion_ia = ConexionOLlama(modelo=modelo_ia)

    def escuchar_usuario(self) -> str:
        """
        Escucha la entrada de voz del usuario y la convierte en texto.
        :return: Texto reconocido o un mensaje de error.
        """
        with sr.Microphone() as fuente:
            print("Escuchando... (habla ahora)")
            try:
                audio = self.reconocedor.listen(fuente, timeout=5)
                texto = self.reconocedor.recognize_google(audio, language="es-ES")
                print(f"Tú: {texto}")
                return texto
            except sr.UnknownValueError:
                return "No entendí lo que dijiste. ¿Puedes repetirlo?"
            except sr.RequestError:
                return "Error al conectar con el servicio de reconocimiento de voz."

    def hablar_ia(self, texto: str):
        """
        Habla la respuesta generada por la IA.
        :param texto: Texto que será convertido a voz.
        """
        print(f"IA: {texto}")
        self.sintetizador.say(texto)
        self.sintetizador.runAndWait()

    def iniciar_conversacion(self):
        """
        Inicia una conversación por voz con la IA.
        """
        while True:
            # Escuchar al usuario
            mensaje_usuario = self.escuchar_usuario()
            
            if mensaje_usuario.lower() in ["salir", "adiós", "terminar"]:
                self.hablar_ia("¡Adiós! Fue un gusto hablar contigo.")
                break

            # Enviar el mensaje a la IA y obtener respuesta
            respuesta_ia = self.conexion_ia.enviar_mensaje(mensaje_usuario)
            
            # Hablar la respuesta de la IA
            self.hablar_ia(respuesta_ia)

if __name__ == "__main__":
    # Crear la interacción por voz
    interaccion = InteraccionVozIA(modelo_ia="llama3.2")
    interaccion.iniciar_conversacion()
