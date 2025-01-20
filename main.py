from ConexionOLlama import ConexionOLlama

def main():
    # Inicializar la conexión
    conexion = ConexionOLlama(modelo="llama3.2")
    
    while True:
        # Solicitar entrada del usuario
        mensaje_usuario = input("Escribe un mensaje (o 'salir' para terminar): ")
        
        if mensaje_usuario.lower() == "salir":
            print("¡Adiós!")
            break
        
        # Enviar el mensaje a la IA y obtener la respuesta
        respuesta = conexion.enviar_mensaje(mensaje_usuario)
        print(f"IA: {respuesta}")

if __name__ == "__main__":
    main()
