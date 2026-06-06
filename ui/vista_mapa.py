"""
vista_mapa.py
=============
Dibuja el mapa y, encima, una ficha por departamento con el color de su dueno y
el numero de tropas. Resalta el departamento seleccionado y los objetivos
legales. El texto usa objetos arcade.Text (via CacheTexto), no draw_text.

Nota de coordenadas: los 'centro' del JSON estan en coordenadas de imagen
(y hacia abajo). Arcade dibuja con y hacia arriba, asi que al posicionar las
fichas se convierte con:  y_arcade = MAPA_ALTO - cy.
"""

import arcade

from ui import colores
from ui import animaciones as anim


class VistaMapa:
    def __init__(self, territorios, ruta_visible):
        self.territorios = territorios
        self.textura = arcade.load_texture(ruta_visible)
        self.seleccion = None     # id del departamento seleccionado
        self.cache = anim.CacheTexto()

    def pos(self, territorio_id):
        """Centro de la ficha en coordenadas de Arcade (y hacia arriba)."""
        cx, cy = self.territorios[territorio_id].centro
        return cx, colores.MAPA_ALTO - cy

    def dibujar(self, gestor=None, objetivos=None):
        objetivos = objetivos or set()
        # Fondo del mapa
        arcade.draw_texture_rect(
            self.textura,
            arcade.LBWH(0, 0, colores.MAPA_ANCHO, colores.MAPA_ALTO))

        # Resaltado de OBJETIVOS LEGALES (vecinos enemigos del origen elegido)
        if gestor is not None and objetivos:
            lat = gestor.latido(0.7)
            for oid in objetivos:
                if oid in self.territorios:
                    ox, oy = self.pos(oid)
                    arcade.draw_circle_outline(
                        ox, oy, 20 + 5 * lat,
                        anim.con_alfa(colores.AMARILLO, 120 + 100 * lat), 3)

        # Fichas de cada departamento
        for t in self.territorios.values():
            cx, cy = t.centro
            ay = colores.MAPA_ALTO - cy

            # Pulso de animacion (crecimiento, golpe, conquista)
            if gestor is not None:
                inten, col_p = gestor.intensidad_pulso(t.id)
                if inten > 0 and col_p is not None:
                    arcade.draw_circle_outline(
                        cx, ay, 15 + 16 * inten,
                        anim.con_alfa(col_p, 220 * inten), 3)

            col = colores.color_jugador(t.tropas["dueno"])
            arcade.draw_circle_filled(cx, ay, 15, col)
            arcade.draw_circle_outline(cx, ay, 15, colores.NEGRO, 2)
            self.cache.dibujar(
                f"n_{t.id}", f"{t.tropas['poblacion_actual']:.0f}",
                cx, ay - 7, colores.BLANCO, 11, anchor_x="center", bold=True)

        # Resalte de la seleccion (origen)
        if self.seleccion and self.seleccion in self.territorios:
            cx, ay = self.pos(self.seleccion)
            arcade.draw_circle_outline(cx, ay, 22, colores.AMARILLO, 4)
