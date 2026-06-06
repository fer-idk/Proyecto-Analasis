"""
colores.py
==========
Constantes visuales y de ventana. Un solo lugar para tamanos y colores, para
no repetir numeros magicos por toda la interfaz.
"""

# --- Dimensiones (el mapa ocupa la izquierda; el HUD ira a la derecha) ---
MAPA_ANCHO = 960
MAPA_ALTO = 560
HUD_ANCHO = 300
VENTANA_ANCHO = MAPA_ANCHO + HUD_ANCHO       # 1260
VENTANA_ALTO = MAPA_ALTO                      # 560

# --- Colores base (RGB) ---
FONDO = (24, 26, 32)
BLANCO = (245, 245, 245)
NEGRO = (20, 20, 20)
GRIS = (90, 90, 90)
AMARILLO = (255, 210, 40)
PANEL = (34, 37, 45)
ROJO = (220, 60, 60)

# --- Color por dueno de territorio ---
COLOR_JUGADOR = {
    "j1": (40, 120, 220),     # azul
    "j2": (220, 70, 70),      # rojo
    None: (150, 150, 150),    # neutral
}


def color_jugador(dueno):
    return COLOR_JUGADOR.get(dueno, (150, 150, 150))


def hex_a_rgb(h):
    """'#E6194B' -> (230, 25, 75)."""
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))