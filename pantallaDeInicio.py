import pygame
import os
from Memoria import Memoria

# Configuración de conexión a la base de datos
db_params = {
    "host": "127.0.0.1",
    "user": "root",  
    "password": "",  
    "database": "iasocial"
}

# Inicializar la clase Memoria
memoria = Memoria(db_params=db_params, script_path="script_personalidad.txt")

# Inicializar Pygame
pygame.init()

# Configuración de la pantalla
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 400
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Interfaz Emocional en Pygame")

# Colores
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
LIGHT_GRAY = (220, 220, 220)
DARK_GRAY = (100, 100, 100)

# Fuente
font = pygame.font.SysFont("Arial", 18)
small_font = pygame.font.SysFont("Arial", 14)

# Función para mostrar un cuadro de diálogo para ingresar el nombre de usuario
def obtener_nombre_usuario():
    input_box = pygame.Rect(200, 150, 400, 40)
    input_text = ""
    running = True
    while running:
        screen.fill(LIGHT_GRAY)
        
        # Título
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

# Obtener el nombre de usuario
usuario = obtener_nombre_usuario()

# Variables iniciales
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

# Cargar imágenes
logo = pygame.image.load(LOGO_PATH)
logo = pygame.transform.smoothscale(logo, (80, 80))

# Estado inicial
current_emotion = 1
sprite = pygame.image.load(SPRITE_PATHS[current_emotion][1])
sprite = pygame.transform.smoothscale(sprite, SPRITE_SIZE)
emotion_text = "Alegría"

# Variables para entrada de texto y respuesta de la IA
input_text = ""
ai_response = f"Hola {usuario}, soy Ghostly. ¿En qué puedo ayudarte hoy?"

send_button = pygame.Rect(750, 350, 30, 30)

def draw_screen():
    """Dibuja todos los elementos en la pantalla"""
    screen.fill(LIGHT_GRAY)
    pygame.draw.line(screen, DARK_GRAY, (120, 0), (120, SCREEN_HEIGHT), 2)
    screen.blit(logo, (20, 20))

    # Respuesta de la IA
    pygame.draw.rect(screen, WHITE, (140, 20, 400, 290))
    pygame.draw.rect(screen, BLACK, (140, 20, 400, 290), 2)
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
    for line in wrapped_text:
        ai_text_surface = font.render(line, True, BLACK)
        screen.blit(ai_text_surface, (150, y_position))
        y_position += 22

    # Personaje
    screen.blit(sprite, (580, 120))
    pygame.draw.rect(screen, WHITE, (580, 40, 200, 60))
    pygame.draw.rect(screen, BLACK, (580, 40, 200, 60), 2)
    emotion_text_surface = small_font.render(f"Emoción: {emotion_text}", True, BLACK)
    screen.blit(emotion_text_surface, (590, 60))

    # Entrada de texto
    pygame.draw.rect(screen, WHITE, (140, 350, 600, 30))
    pygame.draw.rect(screen, BLACK, (140, 350, 600, 30), 2)
    text_surface = font.render(input_text, True, BLACK)
    screen.blit(text_surface, (150, 354))

    # Botón de enviar
    pygame.draw.rect(screen, BLACK, send_button)
    arrow = font.render("↑", True, WHITE)
    screen.blit(arrow, (send_button.x + 10, send_button.y + 2))

    pygame.display.flip()

# Bucle principal
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                if input_text.strip():
                    ai_response = memoria.interactuar(usuario, input_text.strip())
                    input_text = ""
            elif event.key == pygame.K_BACKSPACE:
                input_text = input_text[:-1]
            else:
                input_text += event.unicode
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if send_button.collidepoint(event.pos):
                if input_text.strip():
                    ai_response = memoria.interactuar(usuario, input_text.strip())
                    input_text = ""
    draw_screen()

pygame.quit()
memoria.cerrar_conexiones()

pygame.quit()
memoria.cerrar_conexiones()
