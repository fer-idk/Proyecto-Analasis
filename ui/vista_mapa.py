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

    def dibujar(self, gestor=None, objetivos=None, hovered=None, mx=0, my=0):
        objetivos = objetivos or set()
        # Fondo del mapa
        arcade.draw_texture_rect(
            self.textura,
            arcade.LBWH(0, 0, colores.MAPA_ANCHO, colores.MAPA_ALTO))

        # 1. Resaltado interactivo de OBJETIVOS LEGALES
        if gestor is not None and objetivos:
            lat = gestor.latido(0.7)
            for oid in objetivos:
                if oid in self.territorios:
                    ox, oy = self.pos(oid)
                    # Marcador tipo mira de francotirador/objetivo
                    arcade.draw_circle_outline(
                        ox, oy, 20 + 5 * lat,
                        anim.con_alfa(colores.ROJO, 150 + 100 * lat), 3)

        # 2. Fichas de cada departamento CON ANILLOS DE CAPACIDAD
        for t in self.territorios.values():
            cx, cy = t.centro
            ay = colores.MAPA_ALTO - cy
            
            # Obtener datos matemáticos para visualizar
            r_ef, K_ef = t.parametros_tropas()
            pob = t.tropas['poblacion_actual']
            ratio_llenado = max(0.0, min(1.0, pob / max(1.0, K_ef)))

            # Pulso de animacion (crecimiento, golpe, conquista)
            if gestor is not None:
                inten, col_p = gestor.intensidad_pulso(t.id)
                if inten > 0 and col_p is not None:
                    arcade.draw_circle_outline(
                        cx, ay, 18 + 20 * inten,
                        anim.con_alfa(col_p, 220 * inten), 4)

            # Fondo de la ficha
            col = colores.color_jugador(t.tropas["dueno"])
            arcade.draw_circle_filled(cx, ay, 15, col)
            arcade.draw_circle_outline(cx, ay, 15, colores.NEGRO, 2)
            
            # --- NUEVO: Anillo de capacidad logística (K) ---
            # Dibuja un arco alrededor de la ficha. 
            color_anillo = colores.BLANCO
            if pob > K_ef:
                # ¡Euler rompió la capacidad límite! Peligro visual
                color_anillo = colores.ROJO
                arcade.draw_circle_outline(cx, ay, 19, colores.ROJO, 2)
            else:
                # Arco normal indicando qué tan lleno está (0 a 360 grados)
                arcade.draw_arc_outline(cx, ay, 34, 34, color_anillo, 90, 90 + (360 * ratio_llenado), border_width=3)

            # Número de tropas
            self.cache.dibujar(
                f"n_{t.id}", f"{pob:.0f}",
                cx, ay - 7, colores.BLANCO, 11, anchor_x="center", bold=True)

        # 3. Resalte de la seleccion (origen) ROTATORIO
        if self.seleccion and self.seleccion in self.territorios:
            cx, ay = self.pos(self.seleccion)
            # Hacemos que el anillo de selección gire usando el tiempo del gestor
            rot = (gestor.t * 90) % 360 if gestor else 0
            arcade.draw_arc_outline(cx, ay, 46, 46, colores.AMARILLO, rot, rot + 270, border_width=4)

        # --- NUEVO: Dibujar el Tooltip al pasar el ratón (Hover) ---
        if hovered and hovered in self.territorios:
            t_hover = self.territorios[hovered]
            # Fondo semitransparente
            arcade.draw_rect_filled(arcade.LBWH(mx + 15, my - 40, 140, 60), anim.con_alfa(colores.NEGRO, 200))
            arcade.draw_rect_outline(arcade.LBWH(mx + 15, my - 40, 140, 60), colores.GRIS, 2)
            
            # Textos del tooltip
            self.cache.dibujar("tt_nombre", t_hover.nombre, mx + 20, my, colores.AMARILLO, 12, bold=True)
            self.cache.dibujar("tt_tropas", f"Tropas: {t_hover.tropas['poblacion_actual']:.1f}", mx + 20, my - 16, colores.BLANCO, 10)
            if t_hover.eventos_activos:
                self.cache.dibujar("tt_evt", f"¡{t_hover.eventos_activos[0]}!", mx + 20, my - 32, colores.ROJO, 10, bold=True)
