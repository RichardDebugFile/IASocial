from Memoria import Memoria

def main():
    # Configuración de conexión a la base de datos
    db_params = {
        "host": "127.0.0.1",
        "user": "root",  # Cambia esto por el usuario de tu base de datos
        "password": "",  # Cambia esto por tu contraseña
        "database": "iasocial"
    }

    # Inicializar la clase Memoria
    memoria = Memoria(db_params=db_params, script_path="script_personalidad.txt")

    print("¡Bienvenido al chat con la IA!")
    print("Escribe 'salir' para terminar la conversación.")

    usuario = input("Por favor, ingresa tu nombre de usuario: ").strip()
    if not usuario:
        print("El nombre de usuario no puede estar vacío. Saliendo...")
        return

    while True:
        # Solicitar entrada del usuario
        mensaje_usuario = input(f"{usuario}: ").strip()
        if mensaje_usuario.lower() == "salir":
            print("Terminando la conversación. ¡Hasta luego!")
            break

        # Enviar mensaje a la IA de Llama y obtener respuesta
        respuesta_ia = memoria.interactuar(usuario, mensaje_usuario)
        print(f"IA: {respuesta_ia}")

    # Cerrar conexiones al finalizar
    memoria.cerrar_conexiones()

if __name__ == "__main__":
    main()
