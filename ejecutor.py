import recomendacionesUsuarios

def ejecutar_recomendaciones():
    try:
        # Obtener los vectores de características de los usuarios
        features = recomendacionesUsuarios.get_user_features()
        
        # Calcular similitudes entre usuarios
        matches = recomendacionesUsuarios.calculate_similarities(features)
        
        # Guardar los resultados en la base de datos
        recomendacionesUsuarios.save_matches(matches)
        
        print("Proceso de recomendaciones completado con éxito.")
    
    except Exception as e:
        print(f"Error durante la ejecución: {e}")

if __name__ == "__main__":
    ejecutar_recomendaciones()
