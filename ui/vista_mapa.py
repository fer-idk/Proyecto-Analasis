"""
vista_mapa.py
=============
Dibuja el mapa visual (sprites departamentos con tinte de dueño) y, encima,
fichas con círculos, números de tropas, anillos de capacidad logística y tooltips.

Nota de coordenadas: los 'centro' del JSON están en coordenadas de imagen
(y hacia abajo). Arcade dibuja con y hacia arriba, así que la conversión es:
y_arcade = MAPA_ALTO - y_imagen.
"""

import arcade

from ui import colores
from ui import animaciones as anim


class VistaMapa:
    def __init__(self, territorios, ruta_mapa):
        self.territorios = territorios
        self.seleccion = None
        self.cache = anim.CacheTexto()

        # Fondo del mapa (imagen full)
        self.fondo = arcade.Sprite(ruta_mapa)
        self.fondo.center_x = colores.MAPA_ANCHO / 2
        self.fondo.center_y = colores.MAPA_ALTO / 2

        # Sprites de departamentos (para tintado visual por dueño)
        # Las imágenes son 760×444 pero el JSON usa 960×560
        # Redimensionar para que ocupen todo el área de mapa
        target_width = colores.MAPA_ANCHO
        target_height = colores.MAPA_ALTO
        
        self.sprites_departamentos = {
            "ahuachapan": arcade.Sprite("assets/sprites/ahuachapan.png", 
                                       center_x=self.fondo.center_x, center_y=self.fondo.center_y),
            "santa_ana": arcade.Sprite("assets/sprites/santa_ana.png", 
                                       center_x=self.fondo.center_x, center_y=self.fondo.center_y),
            "sonsonate": arcade.Sprite("assets/sprites/sonsonate.png", 
                                       center_x=self.fondo.center_x, center_y=self.fondo.center_y),
            "la_libertad": arcade.Sprite("assets/sprites/la_libertad.png", 
                                         center_x=self.fondo.center_x, center_y=self.fondo.center_y),
            "chalatenango": arcade.Sprite("assets/sprites/chalatenango.png", 
                                          center_x=self.fondo.center_x, center_y=self.fondo.center_y),
            "san_salvador": arcade.Sprite("assets/sprites/san_salvador.png", 
                                          center_x=self.fondo.center_x, center_y=self.fondo.center_y),
            "cuscatlan": arcade.Sprite("assets/sprites/cuscatlan.png", 
                                       center_x=self.fondo.center_x, center_y=self.fondo.center_y),
            "cabanas": arcade.Sprite("assets/sprites/cabañas.png", 
                                     center_x=self.fondo.center_x, center_y=self.fondo.center_y),
            "la_paz": arcade.Sprite("assets/sprites/la_paz.png", 
                                    center_x=self.fondo.center_x, center_y=self.fondo.center_y),
            "san_vicente": arcade.Sprite("assets/sprites/san_vicente.png", 
                                         center_x=self.fondo.center_x, center_y=self.fondo.center_y),
            "usulutan": arcade.Sprite("assets/sprites/usulutan.png", 
                                      center_x=self.fondo.center_x, center_y=self.fondo.center_y),
            "san_miguel": arcade.Sprite("assets/sprites/san_miguel.png", 
                                        center_x=self.fondo.center_x, center_y=self.fondo.center_y),
            "morazan": arcade.Sprite("assets/sprites/morazan.png", 
                                     center_x=self.fondo.center_x, center_y=self.fondo.center_y),
            "la_union": arcade.Sprite("assets/sprites/la_union.png", 
                                      center_x=self.fondo.center_x, center_y=self.fondo.center_y),
        }
        
        # Redimensionar todos los sprites para llenar el área de mapa
        for sprite in self.sprites_departamentos.values():
            sprite.width = target_width
            sprite.height = target_height

    def pos(self, territorio_id):
        """Centro de la ficha en coordenadas de Arcade (y hacia arriba)."""
        cx, cy = self.territorios[territorio_id].centro
        return cx, colores.MAPA_ALTO - cy

    def dibujar(self, gestor=None, objetivos=None, hovered=None, mx=0, my=0):
        objetivos = objetivos or set()

        # Dibujar fondo del mapa
        arcade.draw_sprite(self.fondo)

        # Dibujar sprites departamentos con tinte del dueño
        for t in self.territorios.values():
            if t.id in self.sprites_departamentos:
                sprite = self.sprites_departamentos[t.id]
                # Color del dueño; si está hovereado, más brillante
                col = colores.color_jugador(t.tropas["dueno"])
                if hovered == t.id:
                    col = (min(255, col[0]+50), min(255, col[1]+50), min(255, col[2]+50))
                sprite.color = col
                arcade.draw_sprite(sprite)

        # 1. Resaltado interactivo de OBJETIVOS LEGALES
        if gestor is not None and objetivos:
            lat = gestor.latido(0.7)
            for oid in objetivos:
                if oid in self.territorios:
                    ox, oy = self.pos(oid)
                    arcade.draw_circle_outline(
                        ox, oy, 20 + 5 * lat,
                        anim.con_alfa(colores.ROJO, 150 + 100 * lat), 3)

        # 2. Fichas de cada departamento CON ANILLOS DE CAPACIDAD
        for t in self.territorios.values():
            cx, cy = t.centro
            ay = colores.MAPA_ALTO - cy

            # Parámetros matemáticos
            r_ef, K_ef = t.parametros_tropas()
            pob = t.tropas['poblacion_actual']
            ratio_llenado = max(0.0, min(1.0, pob / max(1.0, K_ef)))

            # Pulso de animación (crecimiento, golpe, conquista)
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

            # Anillo de capacidad logística (K)
            color_anillo = colores.BLANCO
            if pob > K_ef:
                color_anillo = colores.ROJO
                arcade.draw_circle_outline(cx, ay, 19, colores.ROJO, 2)
            else:
                arcade.draw_arc_outline(cx, ay, 34, 34, color_anillo, 90, 90 + (360 * ratio_llenado), border_width=3)

            # Número de tropas
            self.cache.dibujar(
                f"n_{t.id}", f"{pob:.0f}",
                cx, ay - 7, colores.BLANCO, 11, anchor_x="center", bold=True)

        # 3. Resalte de selección (origen) ROTATORIO
        if self.seleccion and self.seleccion in self.territorios:
            cx, cy = self.pos(self.seleccion)
            rot = (gestor.t * 90) % 360 if gestor else 0
            arcade.draw_arc_outline(cx, cy, 46, 46, colores.AMARILLO, rot, rot + 270, border_width=4)

        # Tooltip al pasar el ratón (Hover)
        if hovered and hovered in self.territorios:
            t_hover = self.territorios[hovered]
            arcade.draw_rect_filled(arcade.LBWH(mx + 15, my - 40, 140, 60), 
                                   anim.con_alfa(colores.NEGRO, 200))
            arcade.draw_rect_outline(arcade.LBWH(mx + 15, my - 40, 140, 60), colores.GRIS, 2)

            self.cache.dibujar("tt_nombre", t_hover.nombre, mx + 20, my, colores.AMARILLO, 12, bold=True)
            self.cache.dibujar("tt_tropas", f"Tropas: {t_hover.tropas['poblacion_actual']:.1f}", 
                              mx + 20, my - 16, colores.BLANCO, 10)
            if t_hover.eventos_activos:
                self.cache.dibujar("tt_evt", f"¡{t_hover.eventos_activos[0]}!", 
                                  mx + 20, my - 32, colores.ROJO, 10, bold=True)

    def on_draw(self):
        """Fallback si VistaMapa se usa como View (no es el caso aquí)."""
        self.clear()
        self.dibujar()

    def on_mouse_press(self, x, y, button, modifiers):
        """Fallback si VistaMapa se usa como View."""
        pass