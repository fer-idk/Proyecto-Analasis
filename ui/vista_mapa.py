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
        self.seleccion = None     
        self.cache = anim.CacheTexto()
        
        # --- NUEVO: Cargar los departamentos como Sprites ---
        self.sprites_deptos = {}
        for depto_id in territorios.keys():
            # Asumimos que guardaste las imágenes como 'assets/mapa/deptos/san_miguel.png', etc.
            ruta_imagen = f"assets/mapa/deptos/{depto_id}.png"
            try:
                sprite = arcade.Sprite(ruta_imagen)
                # Centramos la imagen de 960x560 exactamente en medio de la pantalla del mapa
                sprite.center_x = colores.MAPA_ANCHO / 2
                sprite.center_y = colores.MAPA_ALTO / 2
                self.sprites_deptos[depto_id] = sprite
            except Exception as e:
                print(f"Aviso: No se encontró la imagen para {depto_id}")

    def pos(self, territorio_id):
        """Centro de la ficha en coordenadas de Arcade (y hacia arriba)."""
        cx, cy = self.territorios[territorio_id].centro
        return cx, colores.MAPA_ALTO - cy

    def dibujar(self, gestor=None, objetivos=None, hovered=None, mx=0, my=0):
        objetivos = objetivos or set()
        
        # --- CAMBIO 1: Fondo del océano en lugar de la imagen estática ---
        arcade.draw_rect_filled(arcade.LBWH(0, 0, colores.MAPA_ANCHO, colores.MAPA_ALTO), (30, 40, 50))

        # --- CAMBIO 2: Dibujar los departamentos con el color de su dueño ---
        for t in self.territorios.values():
            # Verificamos que el sprite exista (por si falta alguna imagen)
            if hasattr(self, 'sprites_deptos') and t.id in self.sprites_deptos:
                sprite = self.sprites_deptos[t.id]
                
                # Obtener el color del dueño actual
                color_dueno = colores.COLOR_JUGADOR.get(t.tropas["dueno"], colores.GRIS)
                
                # Si el ratón está encima (hover), lo hacemos brillar un poco más
                if hovered == t.id:
                    color_dueno = (min(255, color_dueno[0]+40), min(255, color_dueno[1]+40), min(255, color_dueno[2]+40))
                
                # Aplicamos el tinte y dibujamos la forma del departamento
                sprite.color = color_dueno
                sprite.draw()

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
            
            # --- Anillo de capacidad logística (K) ---
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

        # --- Dibujar el Tooltip al pasar el ratón (Hover) ---
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