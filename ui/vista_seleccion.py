import arcade
from ui import colores
from ui.ventana_juego import VistaJuego

class VistaSeleccion(arcade.View):
    def __init__(self):
        super().__init__()
        self.turno_jugador = 1  # Empieza eligiendo el Jugador 1
        self.heroe_j1 = None
        self.heroe_j2 = None

        # Definimos los botones de los héroes (x, y, ancho, alto, id_heroe, nombre_mostrar)
        self.botones = [
            (colores.VENTANA_ANCHO // 2 - 150, colores.VENTANA_ALTO // 2, 200, 80, 
             "vendedor_minutas", "Vendedor de Minutas (+K)"),
            (colores.VENTANA_ANCHO // 2 + 150, colores.VENTANA_ALTO // 2, 200, 80, 
             "siguanaba", "La Siguanaba (r < 0)")
        ]

    def on_show_view(self):
        arcade.set_background_color(colores.FONDO)

    def on_draw(self):
        self.clear()
        
        # Título dinámico dependiendo de quién elige
        titulo = f"Jugador {self.turno_jugador}: Selecciona tu Comandante"
        color_titulo = (90, 200, 110) if self.turno_jugador == 1 else (220, 90, 90)
        
        arcade.draw_text(titulo, colores.VENTANA_ANCHO // 2, colores.VENTANA_ALTO - 100, 
                         color_titulo, 24, anchor_x="center", bold=True)

        # Dibujar los botones
        for bx, by, bw, bh, heroe_id, texto in self.botones:
            # Dibujar caja del botón
            arcade.draw_rect_filled(arcade.LBWH(bx - bw//2, by - bh//2, bw, bh), colores.PANEL)
            arcade.draw_rect_outline(arcade.LBWH(bx - bw//2, by - bh//2, bw, bh), colores.AMARILLO, 2)
            
            # Dibujar texto del botón
            arcade.draw_text(texto, bx, by, colores.BLANCO, 12, 
                             anchor_x="center", anchor_y="center", bold=True)

    def on_mouse_press(self, x, y, button, modifiers):
        # Detectar clics en los botones
        heroe_seleccionado = None
        for bx, by, bw, bh, heroe_id, texto in self.botones:
            if (bx - bw//2 <= x <= bx + bw//2) and (by - bh//2 <= y <= by + bh//2):
                heroe_seleccionado = heroe_id
                break

        if heroe_seleccionado:
            if self.turno_jugador == 1:
                self.heroe_j1 = heroe_seleccionado
                self.turno_jugador = 2  # Pasa el turno al Jugador 2
            else:
                self.heroe_j2 = heroe_seleccionado
                # Ambos eligieron, ¡iniciamos el juego pasándole los personajes!
                vista_juego = VistaJuego(heroe_j1=self.heroe_j1, heroe_j2=self.heroe_j2)
                self.window.show_view(vista_juego)