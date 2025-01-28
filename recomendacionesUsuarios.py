import mysql.connector
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# Configuración inicial
model = SentenceTransformer('hiiamsid/sentence_similarity_spanish_es')

def get_user_features():
    # Conexión a DB
    db = mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password="",
        database="iasocial"
    )
    
    # Usar cursor buffered
    cursor = db.cursor(buffered=True)
    
    # Obtener todos los usuarios
    cursor.execute("SELECT usuario FROM resumen_usuario")
    users = [row[0] for row in cursor.fetchall()]
    
    user_features = {}
    
    for user in users:
        # Crear nuevo cursor para cada consulta interna
        with db.cursor(buffered=True) as int_cursor:
            # 1. Datos de personalidad y resumen
            int_cursor.execute(
                "SELECT personalidad_us, resumen_us FROM resumen_usuario WHERE usuario = %s",
                (user,)
            )
            personalidad, resumen = int_cursor.fetchone()
            
            # 2. Datos de sentimiento
            int_cursor.execute(
                "SELECT total_sentimiento FROM sentimiento_ia WHERE usuario = %s",
                (user,)
            )
            sentimientos = list(map(int, int_cursor.fetchone()[0].split(',')))
            
            # 3. Resúmenes de conversación
            int_cursor.execute(
                "SELECT resumen_ia FROM chat_memoria WHERE usuario = %s AND resumen_ia IS NOT NULL",
                (user,)
            )
            conversaciones = ' '.join([row[0] for row in int_cursor.fetchall()])
        
        # Procesamiento de features
        text_data = f"{personalidad} {resumen} {conversaciones}"
        text_vector = model.encode(text_data)
        
        # Cálculo de métricas de sentimiento
        avg_sentiment = np.mean(sentimientos)
        sentiment_variance = np.var(sentimientos)
        
        # Vector final (texto + sentimiento)
        final_vector = np.concatenate([
            text_vector,
            [avg_sentiment, sentiment_variance]
        ])
        
        user_features[user] = final_vector
    
    db.close()
    return user_features

def calculate_similarities(user_features):
    users = list(user_features.keys())
    vectors = np.array([user_features[user] for user in users])
    
    similarity_matrix = cosine_similarity(vectors)
    
    matches = {}
    for i, user in enumerate(users):
        user_scores = list(enumerate(similarity_matrix[i]))
        user_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Excluir autosimilaridad y tomar top 5
        top_matches = [
            (users[j], score) 
            for j, score in user_scores[1:6]
        ]
        
        matches[user] = top_matches
    
    return matches

def save_matches(matches):
    # Conexión correctamente configurada
    db = mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password="",
        database="iasocial"
    )
    cursor = db.cursor()
    
    cursor.execute("TRUNCATE TABLE user_matches")
    
    for user, user_matches in matches.items():
        for match, score in user_matches:
            cursor.execute(
                "INSERT INTO user_matches (usuario1, usuario2, similarity) VALUES (%s, %s, %s)",
                (user, match, float(score))
            )
    
    db.commit()
    db.close()

# Ejecución completa
if __name__ == "__main__":
    features = get_user_features()
    matches = calculate_similarities(features)
    save_matches(matches)