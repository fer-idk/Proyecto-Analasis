"""
vista_batalla.py
================
Panel previo a resolver una batalla. Muestra la proyeccion de las tropas del
defensor a varios turnos con Euler y RK4 al paso h actual. La curva se dibuja
ANIMADA y el tramo donde Euler sobrepasa K (sobre-disparo inestable) se
resalta: es el momento didactico central del juego. Texto via arcade.Text.

El jugador ve ambas predicciones y decide: Confirmar o Cancelar.
"""

import arcade

from core import estabilidad
from ui import colores
from ui import animaciones as anim

# Marco del panel (sobre el area del mapa)
PX, PY, PW, PH = 180, 80, 600, 410
# Area de la grafica dentro del panel
GX, GY, GW, GH = PX + 30, PY + 90, 340, 250
BTN = {
    "confirmar": (PX + 70, PY + 25, 150, 38),
    "cancelar":  (PX + 380, PY + 25, 150, 38),
}


def _dentro(x, y, rect):
    rx, ry, rw, rh = rect
    return rx <= x <= rx + rw and ry <= y <= ry + rh


class PanelBatalla:
    def __init__(self, gestor=None):
        self.gestor = gestor
        self.activo = False
        self.origen = None
        self.destino = None
        self.pred = None
        self._t0 = 0.0          # momento en que se abrio (para animar la curva)
        self.cache = anim.CacheTexto()

    def mostrar(self, origen, destino, prediccion):
        self.origen, self.destino, self.pred = origen, destino, prediccion
        self.activo = True
        self._t0 = self.gestor.t if self.gestor is not None else 0.0

    def ocultar(self):
        self.activo = False
        self.origen = self.destino = self.pred = None

    def boton_en(self, x, y):
        if not self.activo:
            return None
        for nombre, rect in BTN.items():
            if _dentro(x, y, rect):
                return nombre
        return None

    # ---------- Dibujo ----------
    def dibujar(self, metodo_activo, h):
        if not self.activo:
            return
        self._h = h
        c = self.cache
        arcade.draw_rect_filled(arcade.LBWH(PX, PY, PW, PH), (28, 30, 38))
        arcade.draw_rect_outline(arcade.LBWH(PX, PY, PW, PH), colores.AMARILLO, 3)

        c.dibujar("titulo",
                  f"Batalla: {self.origen.nombre}  ->  {self.destino.nombre}",
                  PX + 20, PY + PH - 34, colores.AMARILLO, 16, bold=True)
        c.dibujar("subtitulo",
                  f"Proyeccion de defensa de {self.destino.nombre} "
                  f"(metodo activo: {metodo_activo.upper()}, h={h})",
                  PX + 20, PY + PH - 56, colores.BLANCO, 10)

        self._dibujar_grafica()
        self._dibujar_datos()

        for nombre, etiqueta, col in (("confirmar", "ATACAR", (60, 120, 60)),
                                      ("cancelar", "CANCELAR", (120, 60, 60))):
            rx, ry, rw, rh = BTN[nombre]
            arcade.draw_rect_filled(arcade.LBWH(rx, ry, rw, rh), col)
            c.dibujar(f"btn_{nombre}", etiqueta, rx + rw / 2, ry + 12,
                      colores.BLANCO, 13, anchor_x="center", bold=True)

    def _dibujar_grafica(self):
        c = self.cache
        p = self.pred
        ts, ye, yr = p["ts"], p["euler_traj"], p["rk4_traj"]
        K = p["K_efectiva"]
        xmax = ts[-1] if ts[-1] > 0 else 1.0
        ymax = max(K * 1.3, max(yr) * 1.1, 1.0)
        ymax = min(ymax, K * 2.0) if max(ye) > K * 2.0 else max(ymax, max(ye) * 1.05)

        arcade.draw_rect_outline(arcade.LBWH(GX, GY, GW, GH), colores.GRIS, 1)

        def esc(t, v):
            sx = GX + (t / xmax) * GW
            sy = GY + (max(0.0, min(v, ymax)) / ymax) * GH
            return sx, sy

        # Linea de capacidad K
        _, ky = esc(0, K)
        arcade.draw_line(GX, ky, GX + GW, ky, (120, 120, 120), 1)
        c.dibujar("K_lbl", "K", GX + GW + 4, ky - 6, (140, 140, 140), 9)

        # Animacion: la curva se dibuja de izquierda a derecha
        if self.gestor is not None:
            prog = anim.ease_out((self.gestor.t - self._t0) / 0.7)
        else:
            prog = 1.0
        n = len(ts)
        vis = max(2, int(round(prog * n)))

        pts_rk4 = [esc(t, v) for t, v in zip(ts[:vis], yr[:vis])]
        pts_eul = [esc(t, v) for t, v in zip(ts[:vis], ye[:vis])]

        # Resaltar el tramo de Euler que SOBREPASA K (sobre-disparo inestable)
        glow = [esc(t, v) for t, v in zip(ts[:vis], ye[:vis]) if v > K]
        if len(glow) >= 2:
            arcade.draw_line_strip(glow, anim.con_alfa((255, 90, 90), 90), 9)

        arcade.draw_line_strip(pts_rk4, (90, 200, 110), 2)
        arcade.draw_line_strip(pts_eul, (220, 90, 90), 2)

        # Cabezas que avanzan mientras se dibuja
        if vis < n:
            arcade.draw_circle_filled(*pts_rk4[-1], 4, (90, 200, 110))
            arcade.draw_circle_filled(*pts_eul[-1], 4, (220, 90, 90))

        c.dibujar("g_rk4", "RK4", GX + 8, GY + GH - 16, (90, 200, 110), 11, bold=True)
        c.dibujar("g_eul", "Euler", GX + 60, GY + GH - 16, (220, 90, 90), 11, bold=True)
        c.dibujar("g_turnos", "turnos", GX + GW - 44, GY - 16, colores.GRIS, 9)

        if prog >= 1.0 and max(ye) > K * 1.05:
            c.dibujar("g_aviso", "Euler > K  (inestable)", GX + 8, GY + 6,
                      (255, 120, 90), 10, bold=True)
        else:
            c.dibujar("g_aviso", "", GX + 8, GY + 6, (255, 120, 90), 10, bold=True)

    def _dibujar_datos(self):
        c = self.cache
        p = self.pred
        x = GX + GW + 40
        y = GY + GH - 10
        zona = estabilidad.clasificar(self._h, p["r_efectiva"])
        col_zona = {"verde": (90, 200, 110), "amarilla": (220, 200, 80),
                    "roja": (220, 120, 80), "caos": (220, 80, 80)}[zona]
        filas = [
            (f"Atacante: {self.origen.tropas['poblacion_actual']:.0f} tropas", colores.BLANCO),
            (f"Defensor ahora: {self.destino.tropas['poblacion_actual']:.0f}", colores.BLANCO),
            ("", colores.BLANCO),
            (f"Prediccion RK4:  {p['rk4']:.1f}", (90, 200, 110)),
            (f"Prediccion Euler: {p['euler']:.1f}", (220, 90, 90)),
            (f"Divergencia: {p['divergencia']:.1f}", colores.AMARILLO),
            ("", colores.BLANCO),
            (f"Zona: {zona.upper()}", col_zona),
            (estabilidad.DESCRIPCION[zona], col_zona),
        ]
        for i, (texto, color) in enumerate(filas):
            c.dibujar(f"dato_{i}", texto, x, y, color, 11, bold=True)
            y -= 22
