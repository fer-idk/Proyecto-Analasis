"""
hud.py
======
Panel lateral (HUD). Dibuja y gestiona los controles interactivos:
    - Datos del jugador en turno y del territorio seleccionado.
    - Selector de metodo (Euler / RK4).
    - Slider del paso h (con gradiente de zona y knob que late en peligro).
    - Botones "Usar heroe" y "Fin de turno".

El texto se dibuja con objetos arcade.Text reutilizados (CacheTexto), no con
draw_text. El HUD no decide la logica: solo dibuja y responde donde se hizo
clic; la ventana toma esas respuestas y actua.
"""

import arcade

from core import estabilidad
from ui import colores
from ui import animaciones as anim

ZONA_COLOR = {
    "verde": (90, 200, 110),
    "amarilla": (220, 200, 80),
    "roja": (220, 120, 80),
    "caos": (220, 80, 80),
}

PANEL_X = colores.MAPA_ANCHO
PANEL_W = colores.HUD_ANCHO
TX = PANEL_X + 20

# Geometria de los controles (en coordenadas Arcade, y desde abajo)
BTN = {
    "euler":      (PANEL_X + 20, 205, 110, 30),
    "rk4":        (PANEL_X + 150, 205, 110, 30),
    "heroe":      (PANEL_X + 20, 30, 120, 34),
    "fin_turno":  (PANEL_X + 160, 30, 120, 34),
}
SLIDER_X0 = PANEL_X + 25
SLIDER_X1 = PANEL_X + PANEL_W - 25
SLIDER_Y = 120


def _dentro(x, y, rect):
    rx, ry, rw, rh = rect
    return rx <= x <= rx + rw and ry <= y <= ry + rh


class HUD:
    def __init__(self, estado, config):
        self.estado = estado
        self.h_min = config.get("h_min", 0.05)
        self.h_max = config.get("h_max", 3.0)
        self.cache = anim.CacheTexto()

    # ---------- Slider ----------
    def _x_de_h(self, h):
        frac = (h - self.h_min) / (self.h_max - self.h_min)
        return SLIDER_X0 + frac * (SLIDER_X1 - SLIDER_X0)

    def set_h_por_x(self, x):
        frac = (x - SLIDER_X0) / (SLIDER_X1 - SLIDER_X0)
        frac = max(0.0, min(1.0, frac))
        h = self.h_min + frac * (self.h_max - self.h_min)
        self.estado.h_activo = round(h, 2)

    def en_slider(self, x, y):
        return (SLIDER_X0 - 12 <= x <= SLIDER_X1 + 12
                and SLIDER_Y - 14 <= y <= SLIDER_Y + 14)

    # ---------- Botones ----------
    def boton_en(self, x, y):
        for nombre, rect in BTN.items():
            if _dentro(x, y, rect):
                return nombre
        return None

    # ---------- Dibujo ----------
    def dibujar(self, territorio_sel, gestor=None):
        c = self.cache
        arcade.draw_rect_filled(
            arcade.LBWH(PANEL_X, 0, PANEL_W, colores.VENTANA_ALTO), colores.PANEL)

        c.dibujar("titulo", "RISK MATEMATICO", TX, colores.VENTANA_ALTO - 34,
                  colores.AMARILLO, 17, bold=True)

        jug = self.estado.jugadores.get(self.estado.jugador_actual)
        col_j = colores.color_jugador(self.estado.jugador_actual)
        c.dibujar("turno", f"Turno {self.estado.turno}", TX,
                  colores.VENTANA_ALTO - 58, colores.BLANCO, 12)
        if jug:
            arcade.draw_circle_filled(TX + 6, colores.VENTANA_ALTO - 78, 7, col_j)
            c.dibujar("jugador", f"{jug.nombre}  (heroe: {jug.comandante or '-'})",
                      TX + 20, colores.VENTANA_ALTO - 84, colores.BLANCO, 11)
            c.dibujar("recursos",
                      f"cafe {jug.recursos['cafe']:.0f}   "
                      f"pupusas {jug.recursos['pupusas']:.0f}",
                      TX, colores.VENTANA_ALTO - 104, colores.BLANCO, 11)

        # Datos del territorio seleccionado (posiciones fijas, contenido variable)
        if territorio_sel is None:
            c.dibujar("sel_nombre", "Clic en un departamento.", TX,
                      colores.VENTANA_ALTO - 134, colores.GRIS, 11)
            for i in range(5):
                c.dibujar(f"sel_{i}", "", TX, colores.VENTANA_ALTO - 156 - i * 20,
                          colores.BLANCO, 11)
        else:
            t = self.estado.territorios[territorio_sel]
            r_ef, K_ef = t.parametros_tropas()
            c.dibujar("sel_nombre", t.nombre, TX, colores.VENTANA_ALTO - 134,
                      colores.AMARILLO, 14, bold=True)
            lineas = [
                f"Dueno: {t.tropas['dueno'] or 'neutral'}",
                f"Tropas: {t.tropas['poblacion_actual']:.1f}",
                f"r ef: {r_ef:+.2f}    K ef: {K_ef:.0f}",
                f"{t.recurso['tipo']}: {t.recurso['cantidad_actual']:.1f}",
                f"Eventos: {', '.join(t.eventos_activos) or '-'}",
            ]
            for i, texto in enumerate(lineas):
                c.dibujar(f"sel_{i}", texto, TX,
                          colores.VENTANA_ALTO - 156 - i * 20, colores.BLANCO, 11)

        # Selector de metodo
        c.dibujar("metodo_lbl", "Metodo:", TX, 240, colores.BLANCO, 11)
        for nombre in ("euler", "rk4"):
            rx, ry, rw, rh = BTN[nombre]
            activo = self.estado.metodo_activo == nombre
            arcade.draw_rect_filled(arcade.LBWH(rx, ry, rw, rh),
                                    (60, 90, 60) if activo else (55, 58, 66))
            if activo:
                arcade.draw_rect_outline(arcade.LBWH(rx, ry, rw, rh),
                                         colores.AMARILLO, 2)
            c.dibujar(f"btn_{nombre}", nombre.upper(), rx + rw / 2, ry + 8,
                      colores.BLANCO, 12, anchor_x="center", bold=True)

        # Slider de h -----------------------------------------------------
        if territorio_sel is not None:
            r_ref, _ = self.estado.territorios[territorio_sel].parametros_tropas()
            r_ref = abs(r_ref) or 1.0
        else:
            r_ref = 1.0
        zona_actual = estabilidad.clasificar(self.estado.h_activo, r_ref)
        col_zona = ZONA_COLOR[zona_actual]

        c.dibujar("h_lbl", f"Paso h = {self.estado.h_activo}", TX, SLIDER_Y + 22,
                  colores.BLANCO, 12, bold=True)
        c.dibujar("zona_lbl", zona_actual.upper(), SLIDER_X1 - 50, SLIDER_Y + 22,
                  col_zona, 11, bold=True)

        # Pista pintada por zona (el peligro se ve antes de llegar)
        segs = 60
        for i in range(segs):
            f0, f1 = i / segs, (i + 1) / segs
            hx = self.h_min + f0 * (self.h_max - self.h_min)
            z = estabilidad.clasificar(hx, r_ref)
            x0 = SLIDER_X0 + f0 * (SLIDER_X1 - SLIDER_X0)
            x1 = SLIDER_X0 + f1 * (SLIDER_X1 - SLIDER_X0)
            arcade.draw_line(x0, SLIDER_Y, x1, SLIDER_Y, ZONA_COLOR[z], 4)

        # Marca del umbral de inestabilidad de Euler (h*r = 2)
        h_umbral = min(self.h_max, 2.0 / r_ref)
        xk = self._x_de_h(h_umbral)
        arcade.draw_line(xk, SLIDER_Y - 9, xk, SLIDER_Y + 9, (40, 40, 40), 2)

        # Knob: late en zona roja/caos para avisar del riesgo
        kx = self._x_de_h(self.estado.h_activo)
        peligro = zona_actual in ("roja", "caos")
        lat = gestor.latido(0.5) if (gestor is not None and peligro) else 0.0
        radio = 9 + 3 * lat
        col_knob = anim.mezclar_color(colores.AMARILLO, (255, 60, 60), lat) \
            if peligro else colores.AMARILLO
        if peligro:
            arcade.draw_circle_outline(kx, SLIDER_Y, radio + 5,
                                       anim.con_alfa((255, 60, 60), 120 + 120 * lat), 2)
        arcade.draw_circle_filled(kx, SLIDER_Y, radio, col_knob)

        c.dibujar("hmin", f"{self.h_min}", SLIDER_X0 - 4, SLIDER_Y - 24,
                  colores.GRIS, 9)
        c.dibujar("hmax", f"{self.h_max}", SLIDER_X1 - 12, SLIDER_Y - 24,
                  colores.GRIS, 9)

        # Botones de accion
        for nombre, etiqueta in (("heroe", "Usar heroe"), ("fin_turno", "Fin turno")):
            rx, ry, rw, rh = BTN[nombre]
            arcade.draw_rect_filled(arcade.LBWH(rx, ry, rw, rh), (70, 74, 84))
            c.dibujar(f"lbl_{nombre}", etiqueta, rx + rw / 2, ry + 10,
                      colores.BLANCO, 11, anchor_x="center", bold=True)
