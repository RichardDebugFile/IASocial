from Memoria import Memoria

def main():
    # Configuración de la base de datos y modelo IA
    db_params = {
        "host": "localhost",
        "user": "root",
        "password": "",
        "database": "IASocial"
    }
    script_path = "script_personalidad.txt"
    modelo_ia = "llama3.2"

    # Inicializar Memoria con la conexión a MySQL y el script de personalidad
    memoria = Memoria(db_params=db_params, script_path=script_path, modelo_ia=modelo_ia)

    usuario = input("Por favor, ingresa tu nombre: ")
    print("\nIA: Hola. Espero que tengas algo interesante que decir, ya que no suelo perder mi tiempo.")
    
    while True:
        mensaje_usuario = input("Tú: ")
        if mensaje_usuario.lower() in ["salir", "adiós", "terminar"]:
            print("IA: Bueno, si no puedes seguir el ritmo, lo entiendo. ¡Adiós!")
            break

        # Interactuar con la IA
        respuesta = memoria.interactuar(usuario, mensaje_usuario)
        print(f"IA: {respuesta}")
    
    # Cerrar conexiones
    memoria.cerrar_conexiones()

if __name__ == "__main__":
    main()
