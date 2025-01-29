import pygame
import os
import mysql.connector
from Memoria import Memoria

# -------------------------------------------------------
# CONFIG DB
# -------------------------------------------------------
db_params = {
    "host": "127.0.0.1",
    "user": "root",  
    "password": "",  
    "database": "iasocial"
}

memoria = Memoria(db_params=db_params, script_path="script_personalidad.txt")

# -------------------------------------------------------
# INICIALIZAR PYGAME
# -------------------------------------------------------
pygame.init()
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 400
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Interfaz Emocional en Pygame")

# -------------------------------------------------------
# COLORES Y FUENTES
# -------------------------------------------------------
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
LIGHT_GRAY = (220, 220, 220)
DARK_GRAY = (100, 100, 100)

font = pygame.font.SysFont("Arial", 18)
small_font = pygame.font.SysFont("Arial", 14)

# -------------------------------------------------------
# FUNCIONES DE DB
# -------------------------------------------------------
def obtener_usuarios_similares(db_params, usuario_actual):
    db = mysql.connector.connect(**db_params)
    cursor = db.cursor()
    query = """
        SELECT usuario2
        FROM user_matches
        WHERE usuario1 = %s
          AND similarity > 0.8
    """
    cursor.execute(query, (usuario_actual,))
    resultado = cursor.fetchall()
    db.close()
    return [fila[0] for fila in resultado]


def obtener_lista_usuarios_chateados(db_params, usuario_actual):
    db = mysql.connector.connect(**db_params)
    cursor = db.cursor()
    
    # (1) Usuarios con los que ha habido mensajes
    query_mensajes = """
        SELECT DISTINCT sender
        FROM mensajes
        WHERE receiver = %s

        UNION

        SELECT DISTINCT receiver
        FROM mensajes
        WHERE sender = %s
    """
    cursor.execute(query_mensajes, (usuario_actual, usuario_actual))
    usuarios_mensajes = [fila[0] for fila in cursor.fetchall()]

    # (2) Usuarios con similarity > 0.8
    query_matches = """
        SELECT usuario2
        FROM user_matches
        WHERE usuario1 = %s
          AND similarity > 0.8
    """
    cursor.execute(query_matches, (usuario_actual,))
    usuarios_similares = [fila[0] for fila in cursor.fetchall()]
    
    db.close()
    
    # Unificamos las dos listas sin duplicados
    lista_completa = list(set(usuarios_mensajes + usuarios_similares))
    return lista_completa


def enviar_mensaje(db_params, sender, receiver, content):
    db = mysql.connector.connect(**db_params)
    cursor = db.cursor()
    query = """
    INSERT INTO mensajes (sender, receiver, content)
    VALUES (%s, %s, %s)
    """
    cursor.execute(query, (sender, receiver, content))
    db.commit()
    db.close()


def obtener_sentimiento_principal(usuario):
    try:
        db = mysql.connector.connect(**db_params)
        cursor = db.cursor()
        
        cursor.execute(
            "SELECT sentimiento_principal FROM sentimiento_ia WHERE usuario = %s",
            (usuario,)
        )
        resultado = cursor.fetchone()
        db.close()
        
        if resultado:
            return int(resultado[0])  # Retorna el número del sentimiento
        return 1  # Por defecto, si no hay datos, se usa "Alegría"
    except Exception as e:
        print(f"Error al obtener sentimiento principal: {e}")
        return 1


# -------------------------------------------------------
# NUEVO: Función para cargar los mensajes una sola vez
# -------------------------------------------------------
mensajes_cache = []  # Aquí guardamos los mensajes del chat actual

def cargar_mensajes_chat(db_params, user1, user2):
    """
    Carga los mensajes entre user1 y user2 y los guarda en mensajes_cache.
    """
    global mensajes_cache
    db = mysql.connector.connect(**db_params)
    cursor = db.cursor()
    query = """
    SELECT sender, receiver, content, timestamp
    FROM mensajes
    WHERE (sender = %s AND receiver = %s)
       OR (sender = %s AND receiver = %s)
    ORDER BY timestamp ASC
    """
    cursor.execute(query, (user1, user2, user2, user1))
    mensajes_cache = cursor.fetchall()
    db.close()


# -------------------------------------------------------
# OTRAS FUNCIONES: PEDIR NOMBRE, CARGAR IMAGEN, ETC.
# -------------------------------------------------------
def obtener_nombre_usuario():
    input_box = pygame.Rect(200, 150, 400, 40)
    input_text = ""
    running = True
    while running:
        screen.fill(LIGHT_GRAY)
        
        title_surface = font.render("Por favor, ingresa tu nombre de usuario:", True, BLACK)
        screen.blit(title_surface, (250, 100))
        
        # Cuadro de entrada
        pygame.draw.rect(screen, WHITE, input_box)
        pygame.draw.rect(screen, BLACK, input_box, 2)
        text_surface = font.render(input_text, True, BLACK)
        screen.blit(text_surface, (input_box.x + 10, input_box.y + 10))
        
        # Botón de confirmar
        confirm_button = pygame.Rect(300, 220, 200, 40)
        pygame.draw.rect(screen, DARK_GRAY, confirm_button)
        confirm_text = font.render("Confirmar", True, WHITE)
        screen.blit(confirm_text, (confirm_button.x + 50, confirm_button.y + 10))
        
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and input_text.strip():
                    return input_text.strip()
                elif event.key == pygame.K_BACKSPACE:
                    input_text = input_text[:-1]
                else:
                    input_text += event.unicode
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if confirm_button.collidepoint(event.pos) and input_text.strip():
                    return input_text.strip()


# -------------------------------------------------------
# INICIALIZACIÓN
# -------------------------------------------------------
usuario = obtener_nombre_usuario()
current_emotion = obtener_sentimiento_principal(usuario)

RESOURCE_PATH = "images"
LOGO_PATH = os.path.join(RESOURCE_PATH, "logo.png")
SPRITE_SIZE = (200, 200)
SPRITE_PATHS = {
    1: ("Alegría", os.path.join(RESOURCE_PATH, "alegria.png")),
    2: ("Tristeza", os.path.join(RESOURCE_PATH, "tristeza.png")),
    3: ("Ira", os.path.join(RESOURCE_PATH, "ira.png")),
    4: ("Sorpresa", os.path.join(RESOURCE_PATH, "sorpresa.png")),
    5: ("Confianza", os.path.join(RESOURCE_PATH, "confianza.png")),
    6: ("Decepción", os.path.join(RESOURCE_PATH, "decepcion.png")),
    7: ("Optimismo", os.path.join(RESOURCE_PATH, "optimismo.png"))
}

logo = pygame.image.load(LOGO_PATH)
logo = pygame.transform.smoothscale(logo, (80, 80))

sprite = pygame.image.load(SPRITE_PATHS[current_emotion][1])
sprite = pygame.transform.smoothscale(sprite, SPRITE_SIZE)
emotion_text = SPRITE_PATHS[current_emotion][0]

# Texto para la IA
input_text = ""
ai_response = f"Hola {usuario}, soy Ghostly. ¿En qué puedo ayudarte hoy?"

# Texto para el chat con otros usuarios
chat_input_text = ""

# Botones
send_button = pygame.Rect(750, 350, 30, 30)
ver_chats_button = pygame.Rect(600, 20, 180, 40)

# -------------------------------------------------------
# MODO DE PANTALLA
# -------------------------------------------------------
modo_actual = "principal"        # "principal", "lista_chats", "chat"
lista_usuarios_chats = []        # Para mostrar en pantalla de lista
usuario_seleccionado = None      # El usuario con quien estamos chateando

# -------------------------------------------------------
# 1) Guardar la lista de usuarios similares
#    (O consultarla 1 vez y guardarla)
# -------------------------------------------------------
usuarios_similares_cache = obtener_usuarios_similares(db_params, usuario)

# -------------------------------------------------------
# VARIABLES PARA LISTA DE CHATS
# -------------------------------------------------------
rects_usuarios = {}  # Guardamos rectángulos donde se dibujan los usuarios

# -------------------------------------------------------
# FUNCIONES DE DIBUJO PARA CADA MODO
# -------------------------------------------------------
def draw_principal_screen():
    """Dibuja la pantalla principal con Ghostly."""
    screen.fill(LIGHT_GRAY)
    pygame.draw.line(screen, DARK_GRAY, (120, 0), (120, SCREEN_HEIGHT), 2)
    screen.blit(logo, (20, 20))

    # Recuadro para la respuesta de la IA
    pygame.draw.rect(screen, WHITE, (140, 20, 400, 290))
    pygame.draw.rect(screen, BLACK, (140, 20, 400, 290), 2)

    # Render de la respuesta IA con wrapping
    wrapped_text = []
    words = ai_response.split()
    line = ""
    for word in words:
        test_line = line + word + " "
        if font.size(test_line)[0] > 380:
            wrapped_text.append(line)
            line = word + " "
        else:
            line = test_line
    wrapped_text.append(line)

    y_position = 30
    for text_line in wrapped_text:
        ai_text_surface = font.render(text_line, True, BLACK)
        screen.blit(ai_text_surface, (150, y_position))
        y_position += 22

    # -- Notificación debajo del recuadro de la IA -- #
    if usuarios_similares_cache:
        # Antes estaba en (200, 80,...)
        notif_rect = pygame.Rect(140, 320, 600, 25)  # <-- Cambios
        pygame.draw.rect(screen, (255, 0, 0), notif_rect)
        notif_text = font.render("¡Tienes un usuario bastante similar a ti!", True, WHITE)
        screen.blit(notif_text, (notif_rect.x + 10, notif_rect.y + 2))

    # Botón "Ver Chats"
    pygame.draw.rect(screen, DARK_GRAY, ver_chats_button)
    ver_chats_text = font.render("Ver Chats", True, WHITE)
    screen.blit(ver_chats_text, (ver_chats_button.x + 10, ver_chats_button.y + 10))

    # Personaje
    # Se mueve la caja de la emoción debajo del botón "Ver Chats"
    # Antes estaba en (580, 40, 200, 60)
    pygame.draw.rect(screen, WHITE, (580, 70, 200, 60))  # <-- Cambios
    pygame.draw.rect(screen, BLACK, (580, 70, 200, 60), 2)
    emotion_text_surface = small_font.render(f"Emoción: {emotion_text}", True, BLACK)
    # Se dibuja el texto un poco más centrado en la nueva caja
    screen.blit(emotion_text_surface, (590, 95))         # <-- Cambios

    # Se baja un poco más el sprite para que no se traslape
    # Antes estaba en (580, 120)
    screen.blit(sprite, (580, 150))                     # <-- Cambios

    # Entrada de texto (para la IA)
    pygame.draw.rect(screen, WHITE, (140, 350, 600, 30))
    pygame.draw.rect(screen, BLACK, (140, 350, 600, 30), 2)
    text_surface = font.render(input_text, True, BLACK)
    screen.blit(text_surface, (150, 354))

    # Botón enviar (IA)
    pygame.draw.rect(screen, BLACK, send_button)
    arrow = font.render("↑", True, WHITE)
    screen.blit(arrow, (send_button.x + 10, send_button.y + 2))

    pygame.display.flip()


def draw_lista_chats(lista_usuarios):
    """Dibuja la pantalla con la lista de usuarios chateados o similares."""
    screen.fill(LIGHT_GRAY)

    title_surface = font.render("Lista de Chats / Usuarios Similares", True, BLACK)
    screen.blit(title_surface, (200, 50))
    
    y_offset = 100
    for i, usr in enumerate(lista_usuarios):
        rect = pygame.Rect(200, y_offset, 300, 30)
        pygame.draw.rect(screen, WHITE, rect)
        pygame.draw.rect(screen, BLACK, rect, 2)

        text_surface = font.render(usr, True, BLACK)
        screen.blit(text_surface, (rect.x + 10, rect.y + 5))

        # Guardar el rectángulo para detectar clicks
        rects_usuarios[i] = rect  

        y_offset += 40

    pygame.display.flip()


def draw_chat_screen(usuario, usuario_seleccionado, chat_input):
    """
    Dibuja la pantalla de chat con usuario_seleccionado
    usando la variable global mensajes_cache (ya cargada).
    """
    screen.fill(LIGHT_GRAY)
    
    # Título
    title = f"Chat con {usuario_seleccionado}"
    title_surface = font.render(title, True, BLACK)
    screen.blit(title_surface, (20, 20))
    
    # Mostramos los mensajes del chat DESDE mensajes_cache
    y_offset = 60
    for msg in mensajes_cache:
        sender, receiver, content, timestamp = msg
        # Color distinto si lo envió el usuario actual
        color = (200, 255, 200) if sender == usuario else (255, 255, 255)

        rect_msg = pygame.Rect(20, y_offset, 600, 30)
        pygame.draw.rect(screen, color, rect_msg)

        text_surface = small_font.render(f"{sender}: {content}", True, BLACK)
        screen.blit(text_surface, (rect_msg.x + 5, rect_msg.y + 5))
        
        y_offset += 35

    # Caja de texto para nuevo mensaje
    input_rect = pygame.Rect(20, 350, 600, 30)
    pygame.draw.rect(screen, WHITE, input_rect)
    pygame.draw.rect(screen, BLACK, input_rect, 2)
    text_surface = font.render(chat_input, True, BLACK)
    screen.blit(text_surface, (input_rect.x + 5, input_rect.y + 5))
    
    # Botón enviar
    send_rect = pygame.Rect(630, 350, 100, 30)
    pygame.draw.rect(screen, DARK_GRAY, send_rect)
    send_text = font.render("Enviar", True, WHITE)
    screen.blit(send_text, (send_rect.x + 10, send_rect.y + 5))
    
    pygame.display.flip()

    return send_rect


# -------------------------------------------------------
# BUCLE PRINCIPAL
# -------------------------------------------------------
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:
            if modo_actual == "principal":
                # Teclado para la IA
                if event.key == pygame.K_RETURN:
                    if input_text.strip():
                        ai_response = memoria.interactuar(usuario, input_text.strip())
                        input_text = ""
                elif event.key == pygame.K_BACKSPACE:
                    input_text = input_text[:-1]
                else:
                    input_text += event.unicode

            elif modo_actual == "chat":
                # Teclado para el chat
                if event.key == pygame.K_RETURN:
                    if chat_input_text.strip():
                        # Enviamos el mensaje
                        enviar_mensaje(db_params, usuario, usuario_seleccionado, chat_input_text.strip())
                        chat_input_text = ""
                        # Recargamos los mensajes una sola vez
                        cargar_mensajes_chat(db_params, usuario, usuario_seleccionado)

                elif event.key == pygame.K_BACKSPACE:
                    chat_input_text = chat_input_text[:-1]
                else:
                    chat_input_text += event.unicode

        elif event.type == pygame.MOUSEBUTTONDOWN:
            # Modo PRINCIPAL
            if modo_actual == "principal":
                # Botón enviar IA
                if send_button.collidepoint(event.pos):
                    if input_text.strip():
                        ai_response = memoria.interactuar(usuario, input_text.strip())
                        input_text = ""

                # Botón "Ver Chats"
                if ver_chats_button.collidepoint(event.pos):
                    # Cargamos la lista de usuarios
                    lista_usuarios_chats = obtener_lista_usuarios_chateados(db_params, usuario)
                    modo_actual = "lista_chats"

            # Modo LISTA_CHATS
            elif modo_actual == "lista_chats":
                # Ver si se hace click sobre algún usuario
                for i, usr in enumerate(lista_usuarios_chats):
                    if i in rects_usuarios:
                        if rects_usuarios[i].collidepoint(event.pos):
                            # Iniciar chat con 'usr'
                            usuario_seleccionado = usr
                            modo_actual = "chat"
                            chat_input_text = ""
                            # Cargar mensajes del chat (una vez)
                            cargar_mensajes_chat(db_params, usuario, usuario_seleccionado)

            # Modo CHAT
            elif modo_actual == "chat":
                # Dibujamos la pantalla de chat (ya sin abrir BD)
                send_rect = draw_chat_screen(usuario, usuario_seleccionado, chat_input_text)
                # Si click en "Enviar"
                if send_rect.collidepoint(event.pos):
                    if chat_input_text.strip():
                        enviar_mensaje(db_params, usuario, usuario_seleccionado, chat_input_text.strip())
                        chat_input_text = ""
                        # Recargar mensajes:
                        cargar_mensajes_chat(db_params, usuario, usuario_seleccionado)

    # Dibujo según modo
    if modo_actual == "principal":
        draw_principal_screen()
    elif modo_actual == "lista_chats":
        draw_lista_chats(lista_usuarios_chats)
    elif modo_actual == "chat":
        draw_chat_screen(usuario, usuario_seleccionado, chat_input_text)

pygame.quit()
memoria.cerrar_conexiones()
