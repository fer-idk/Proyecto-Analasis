"""
vista_menu.py
=============
Pantallas previas a la partida, como vistas de Arcade (arcade.View):

    VistaMenu    -> Jugar / Reglas / Cerrar
    VistaReglas  -> explicacion del juego + Volver

Todo el texto usa objetos arcade.Text creados una sola vez (no draw_text), que
es la forma recomendada y rapida. La ventana (VentanaApp) cambia entre estas
vistas y la partida con window.show_view(...).
"""

import arcade

from ui import colores
from ui import animaciones as anim
from ui.ventana_juego import VistaJuego, RUTA_MAPA
from ui.vista_seleccion import VistaSeleccion

CX = colores.VENTANA_ANCHO // 2
BTN_W, BTN_H = 280, 56


def _dentro(x, y, rect):
    rx, ry, rw, rh = rect
    return rx <= x <= rx + rw and ry <= y <= ry + rh


class VistaMenu(arcade.View):
    def __init__(self):
        super().__init__()
        try:
            self.fondo = arcade.load_texture(RUTA_MAPA)
        except Exception:
            self.fondo = None

        # Botones: (clave, etiqueta, rect LBWH, accion)
        self.botones = [
            ("jugar", "JUGAR", (CX - BTN_W // 2, 300, BTN_W, BTN_H)),
            ("reglas", "REGLAS", (CX - BTN_W // 2, 222, BTN_W, BTN_H)),
            ("cerrar", "CERRAR", (CX - BTN_W // 2, 144, BTN_W, BTN_H)),
        ]
        self.hover = None

        # Objetos Text (creados una sola vez)
        self.t_titulo = arcade.Text(
            "RISK MATEMATICO", CX, 470, colores.AMARILLO, 40,
            anchor_x="center", bold=True)
        self.t_sub = arcade.Text(
            "El Salvador  -  Euler vs Runge-Kutta 4", CX, 432,
            colores.BLANCO, 16, anchor_x="center")
        self.t_pie = arcade.Text(
            "Analisis Numerico  -  proyecto final", CX, 40,
            colores.GRIS, 11, anchor_x="center")
        self.t_botones = {
            clave: arcade.Text(etq, rx + rw / 2, ry + rh / 2, colores.BLANCO,
                               18, anchor_x="center", anchor_y="center", bold=True)
            for clave, etq, (rx, ry, rw, rh) in self.botones
        }

    def on_show_view(self):
        self.window.background_color = colores.FONDO

    def on_draw(self):
        self.clear()
        # Fondo del mapa atenuado
        if self.fondo is not None:
            arcade.draw_texture_rect(
                self.fondo,
                arcade.LBWH(0, 0, colores.VENTANA_ANCHO, colores.VENTANA_ALTO))
            arcade.draw_rect_filled(
                arcade.LBWH(0, 0, colores.VENTANA_ANCHO, colores.VENTANA_ALTO),
                (18, 20, 26, 205))

        self.t_titulo.draw()
        self.t_sub.draw()
        self.t_pie.draw()

        for clave, _etq, rect in self.botones:
            rx, ry, rw, rh = rect
            resaltado = self.hover == clave
            base = (70, 120, 90) if clave == "jugar" else (60, 64, 74)
            col = anim.mezclar_color(base, (255, 210, 40), 0.25) if resaltado else base
            arcade.draw_rect_filled(arcade.LBWH(rx, ry, rw, rh), col)
            arcade.draw_rect_outline(
                arcade.LBWH(rx, ry, rw, rh),
                colores.AMARILLO if resaltado else (40, 42, 50), 2)
            self.t_botones[clave].draw()

    def on_mouse_motion(self, x, y, dx, dy):
        self.hover = None
        for clave, _etq, rect in self.botones:
            if _dentro(x, y, rect):
                self.hover = clave
                break

    def on_mouse_press(self, x, y, button, modifiers):
        for clave, _etq, rect in self.botones:
            if _dentro(x, y, rect):
                self._accion(clave)
                return

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ENTER:
            self._accion("jugar")
        elif key == arcade.key.ESCAPE:
            self.window.close()

    def _accion(self, clave):
        if clave == "jugar":
            vista_seleccion = VistaSeleccion()
            self.window.show_view(vista_seleccion)
        elif clave == "reglas":
            self.window.show_view(VistaReglas())
        elif clave == "cerrar":
            self.window.close()


class VistaReglas(arcade.View):
    LINEAS = [
        ("Objetivo", colores.AMARILLO),
        ("Conquista los 14 departamentos de El Salvador. Ganas cuando", colores.BLANCO),
        ("controlas todos los territorios del rival.", colores.BLANCO),
        ("", colores.BLANCO),
        ("Tu turno", colores.AMARILLO),
        ("- Elige el metodo (Euler o RK4) y el paso h. Las tropas crecen", colores.BLANCO),
        ("  con la ecuacion logistica resuelta con ESE metodo y paso.", colores.BLANCO),
        ("- Atacar: clic en un territorio tuyo (origen) y luego en un", colores.BLANCO),
        ("  vecino enemigo. Veras la prediccion de Euler vs RK4.", colores.BLANCO),
        ("- Cuidado con h: en zona ROJA/CAOS Euler se vuelve inestable", colores.BLANCO),
        ("  y tu ataque pierde fuerza. RK4 aguanta pasos mas grandes.", colores.BLANCO),
        ("", colores.BLANCO),
        ("Heroes y eventos", colores.AMARILLO),
        ("- Vendedor de Minutas: sube K en tu territorio (mas tropas).", colores.BLANCO),
        ("- La Siguanaba: vuelve r negativa en un enemigo (desgaste).", colores.BLANCO),
        ("- Huracan, Erupcion y Marcha en la UES alteran el mapa.", colores.BLANCO),
        ("- Cafe y pupusas tambien crecen con la logistica; sobre-", colores.BLANCO),
        ("  explotar un recurso lo colapsa.", colores.BLANCO),
        ("", colores.BLANCO),
        ("En partida, pulsa Esc para volver al menu.", colores.GRIS),
    ]

    def __init__(self):
        super().__init__()
        self.t_titulo = arcade.Text("REGLAS", CX, colores.VENTANA_ALTO - 36,
                                     colores.AMARILLO, 28, anchor_x="center", bold=True)
        x0 = 120
        y0 = colores.VENTANA_ALTO - 80
        self.textos = []
        for i, (txt, col) in enumerate(self.LINEAS):
            es_titulo = col == colores.AMARILLO and txt
            self.textos.append(arcade.Text(
                txt, x0, y0 - i * 22, col, 14 if es_titulo else 12,
                bold=bool(es_titulo)))
        self.btn_volver = (CX - 80, 24, 160, 44)
        self.t_volver = arcade.Text("VOLVER", CX, 24 + 22, colores.BLANCO, 16,
                                    anchor_x="center", anchor_y="center", bold=True)
        self.hover = False

    def on_show_view(self):
        self.window.background_color = colores.FONDO

    def on_draw(self):
        self.clear()
        self.t_titulo.draw()
        for t in self.textos:
            t.draw()
        rx, ry, rw, rh = self.btn_volver
        col = (90, 100, 120) if self.hover else (60, 64, 74)
        arcade.draw_rect_filled(arcade.LBWH(rx, ry, rw, rh), col)
        arcade.draw_rect_outline(arcade.LBWH(rx, ry, rw, rh),
                                 colores.AMARILLO if self.hover else (40, 42, 50), 2)
        self.t_volver.draw()

    def on_mouse_motion(self, x, y, dx, dy):
        self.hover = _dentro(x, y, self.btn_volver)

    def on_mouse_press(self, x, y, button, modifiers):
        if _dentro(x, y, self.btn_volver):
            self.window.show_view(VistaMenu())

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ESCAPE:
            self.window.show_view(VistaMenu())
