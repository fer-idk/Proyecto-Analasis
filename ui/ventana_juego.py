"""
ventana_juego.py
================
La partida como arcade.View (VistaJuego). El menu (VistaMenu) la crea al pulsar
"Jugar". La ventana (VentanaApp) es unica y solo cambia de vista.

Flujo de una accion:
    1. Clic en un territorio propio (con tropas)  -> queda como ORIGEN.
    2. Clic en un vecino enemigo                   -> abre el panel de batalla
       con la prediccion Euler vs RK4 al h actual.
    3. Mover el slider de h o cambiar de metodo cambia la prediccion en vivo.
    4. ATACAR resuelve la batalla (y la guarda en la BD); CANCELAR vuelve atras.

"Fin turno" hace crecer las tropas del jugador en turno UN paso de tamano h con
el metodo activo (aqui el metodo rige el estado real) y pasa el turno.

La base de datos NO se borra entre partidas: cada partida jugada se acumula en
partidas/risk_partida.db, de modo que jugar varias veces deja datos reales de
varias partidas (requisito de la rubrica).

Ejecutar desde la raiz:  python3 main.py   (abre el menu)
"""

import arcade

from core.cargador import cargar_mapa
from core.game_state import EstadoJuego
from core.jugador import Jugador
from core.turnos import MotorTurnos
from core import comandantes
from core import estabilidad
from core.gestor_eventos import GestorEventos, GestorCaos
from core.batalla import resolver as resolver_batalla
from core.prediccion import predecir
from persistencia.repositorio import Repositorio
from ui import colores
from ui import animaciones as anim
from ui.vista_mapa import VistaMapa
from ui.deteccion_pixel import DetectorPixelPerfect
from ui.hud import HUD
from ui.vista_batalla import PanelBatalla
from ui.animaciones import GestorAnimaciones, CacheTexto

RUTA_JSON = "data/departamentos.json"
RUTA_MAPA = "assets/mapa/el_salvador.png"
RUTA_MASCARA = "assets/mapa/el_salvador_mask.png"
RUTA_DB = "partidas/risk_partida.db"


class VistaJuego(arcade.View):
    # Añadimos los parámetros heroe_j1 y heroe_j2
    def __init__(self, heroe_j1="vendedor_minutas", heroe_j2="siguanaba"):
        super().__init__()

        territorios, config = cargar_mapa(RUTA_JSON)
        for tid in ("santa_ana", "ahuachapan", "sonsonate", "la_libertad",
                    "chalatenango", "san_salvador", "cuscatlan"):
            territorios[tid].tropas["dueno"] = "j1"
        for tid in ("cabanas", "la_paz", "san_vicente", "usulutan",
                    "san_miguel", "morazan", "la_union"):
            territorios[tid].tropas["dueno"] = "j2"
            
        # ¡AQUÍ ESTÁ EL CAMBIO PRINCIPAL! Usamos las variables en lugar del texto fijo
        jugadores = {
            "j1": Jugador("j1", "Cuscatlecos", comandante=heroe_j1),
            "j2": Jugador("j2", "Pipiles", comandante=heroe_j2),
        }

        self.estado = EstadoJuego(territorios, jugadores, config)
        self.cfg = config

        # Base de datos real (se ACUMULAN partidas, no se borra el archivo)
        self.repo = Repositorio(RUTA_DB)
        self.partida_id = self.repo.crear_partida(notas="Partida jugada")
        self._cerrada = False

        self.motor = MotorTurnos(self.estado, self.repo, self.partida_id)
        self.anim = GestorAnimaciones()
        self.cache = CacheTexto()
        self.vista_mapa = VistaMapa(territorios, RUTA_MAPA)
        # Detector pixel-perfect: usa los MISMOS sprites que se dibujan (su
        # center_x/center_y/scale en vivo) y cachea el canal alfa de cada PNG.
        _sprites = self.vista_mapa.sprites_departamentos
        _rutas = {
            n: (f"assets/sprites/{n}.png" if n != "cabanas" else "assets/sprites/cabañas.png")
            for n in _sprites
        }
        self.detector = DetectorPixelPerfect(_sprites, _rutas)
        self.hud = HUD(self.estado, config)
        self.panel_batalla = PanelBatalla(self.anim)
        self.gestor = GestorEventos(probabilidad=0.45)
        self.gestor_caos = GestorCaos(self.estado.territorios)

        self.origen = None            # id del territorio de origen elegido
        self.objetivos = set()        # vecinos enemigos atacables del origen
        self.sel = None               # territorio mostrado en el HUD
        self.terminado = False
        self._arrastrando = False
        self.mensaje = ""

        # La ventana guarda una referencia para cerrar la BD si se cierra todo
        self.window.juego = self

        self._arrastrando = False
        self.mensaje = ""
        
        # --- NUEVAS VARIABLES PARA EL HOVER ---
        self.hovered_depto = None
        self.mouse_x = 0
        self.mouse_y = 0

    # ---------- Ciclo de vista ----------
    def on_show_view(self):
        self.window.background_color = colores.FONDO

    def on_hide_view(self):
        self.cerrar_partida()

    def cerrar_partida(self):
        """Finaliza la partida y cierra la BD una sola vez (idempotente)."""
        if self._cerrada or self.repo is None:
            return
        ganador = self.estado.ganador()
        try:
            self.repo.finalizar_partida(self.partida_id, ganador=ganador)
        finally:
            self.repo.cerrar()
        self._cerrada = True
        if getattr(self.window, "juego", None) is self:
            self.window.juego = None

    # ---------- Dibujo ----------
    def on_draw(self):
        self.clear()
        # Actualizamos la llamada a dibujar pasándole el hovered y el ratón
        self.vista_mapa.dibujar(self.anim, self.objetivos, self.hovered_depto, self.mouse_x, self.mouse_y)
        self.anim.dibujar_mundo()
        self._tint_peligro()
        self.hud.dibujar(self.sel, self.anim)
        if self.mensaje:
            self.cache.dibujar("mensaje", self.mensaje, 12, 10, colores.AMARILLO, 12, bold=True)
        self.panel_batalla.dibujar(self.estado.metodo_activo, self.estado.h_activo)

    def on_update(self, dt):
        self.anim.actualizar(dt)

    def _tint_peligro(self):
        """Si el h actual cae en zona roja/caos (para un r tipico ~1), tinta
        el borde del mapa de rojo, latiendo: el jugador SIENTE el riesgo antes
        de pagarlo en batalla."""
        zona = estabilidad.clasificar(self.estado.h_activo, 1.0)
        if zona not in ("roja", "caos"):
            return
        lat = self.anim.latido(0.6)
        a = (40 if zona == "roja" else 70) * (0.5 + 0.5 * lat)
        franja = 16
        for lbwh in (
            arcade.LBWH(0, 0, colores.MAPA_ANCHO, franja),
            arcade.LBWH(0, colores.MAPA_ALTO - franja, colores.MAPA_ANCHO, franja),
            arcade.LBWH(0, 0, franja, colores.MAPA_ALTO),
            arcade.LBWH(colores.MAPA_ANCHO - franja, 0, franja, colores.MAPA_ALTO),
        ):
            arcade.draw_rect_filled(lbwh, anim.con_alfa((255, 60, 60), a))

    # ---------- Teclado ----------
    def on_key_press(self, key, modifiers):
        if key == arcade.key.ESCAPE:
            self.cerrar_partida()
            from ui.vista_menu import VistaMenu
            self.window.show_view(VistaMenu())

    # ---------- Raton ----------
    def on_mouse_press(self, x, y, button, modifiers):
        # 1) Panel de batalla tiene prioridad
        if self.panel_batalla.activo:
            accion = self.panel_batalla.boton_en(x, y)
            if accion == "confirmar":
                self._confirmar_batalla()
            elif accion == "cancelar":
                self._cancelar_batalla()
            return

        if self.terminado:
            return

        # 2) Controles del HUD
        boton = self.hud.boton_en(x, y)
        if boton in ("euler", "rk4"):
            self.estado.metodo_activo = boton
            return
        if boton == "fin_turno":
            self._fin_de_turno()
            return
        if boton == "heroe":
            self._usar_heroe()
            return
        if self.hud.en_slider(x, y):
            self.hud.set_h_por_x(x)
            self._arrastrando = True
            return

        # 3) Clic en el mapa
        depto = self.detector.departamento_en(x, y)
        if depto is not None:
            self._clic_territorio(depto)

    def on_mouse_motion(self, x, y, dx, dy):
        """Detecta por dónde se mueve el ratón para los tooltips."""
        self.mouse_x = x
        self.mouse_y = y
        
        if self.terminado or self.panel_batalla.activo:
            self.hovered_depto = None
            return

        # Vemos si el ratón está sobre algún departamento válido
        depto = self.detector.departamento_en(x, y)
        self.hovered_depto = depto

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if self._arrastrando:
            self.hud.set_h_por_x(x)

    def on_mouse_release(self, x, y, button, modifiers):
        self._arrastrando = False

    # ---------- Logica de juego ----------
    def _clic_territorio(self, depto):
        t = self.estado.territorios[depto]
        self.sel = depto
        jugador = self.estado.jugador_actual

        if self.origen is None:
            if t.tropas["dueno"] == jugador and t.tropas["poblacion_actual"] > 1:
                self.origen = depto
                self.vista_mapa.seleccion = depto
                self.objetivos = {
                    v for v in t.vecinos
                    if v in self.estado.territorios
                    and self.estado.territorios[v].tropas["dueno"] != jugador}
                self.mensaje = f"Origen: {t.nombre}. Elige un vecino enemigo."
            else:
                self.mensaje = "Elige un territorio tuyo con tropas."
        else:
            if depto == self.origen:
                self.origen = None
                self.objetivos = set()
                self.vista_mapa.seleccion = None
                self.mensaje = ""
                return
            origen_t = self.estado.territorios[self.origen]
            if t.tropas["dueno"] != jugador and origen_t.es_vecino_de(depto):
                self._abrir_batalla(origen_t, t)
            else:
                self.mensaje = "Debe ser un vecino enemigo. (Clic en origen para cancelar.)"

    def _abrir_batalla(self, origen_t, destino_t):
        # Prediccion de PREVISUALIZACION (no se guarda todavia)
        pred = predecir(destino_t, "tropas", self.estado.h_activo,
                        self.cfg["turnos_prediccion"])
        self.panel_batalla.mostrar(origen_t, destino_t, pred)

    def _confirmar_batalla(self):
        origen_t = self.panel_batalla.origen
        destino_t = self.panel_batalla.destino
        # Recalcular guardando en la BD el calculo realmente usado
        pred = predecir(destino_t, "tropas", self.estado.h_activo,
                        self.cfg["turnos_prediccion"],
                        repo=self.repo, partida_id=self.partida_id,
                        turno=self.estado.turno)
        res = resolver_batalla(
            self.estado, origen_t, destino_t,
            tropas_comprometidas=origen_t.tropas["poblacion_actual"],
            prediccion=pred, metodo_confiado=self.estado.metodo_activo,
            factor_atacante=estabilidad.factor_combate(
                self.estado.metodo_activo,
                estabilidad.clasificar(self.estado.h_activo, pred["r_efectiva"])),
            repo=self.repo, partida_id=self.partida_id, turno=self.estado.turno)
        self.mensaje = (f"{origen_t.nombre} -> {destino_t.nombre}: "
                        f"{res['resultado']}")
        self._fx_batalla(origen_t, destino_t, res)
        self.panel_batalla.ocultar()
        self.origen = None
        self.objetivos = set()
        self.vista_mapa.seleccion = None

    def _fx_batalla(self, origen_t, destino_t, res):
        """Tropas que vuelan al objetivo, estallido en el choque y texto del
        resultado. Visualiza el ataque sin tocar la logica de batalla."""
        ox, oy = self.vista_mapa.pos(origen_t.id)
        dx, dy = self.vista_mapa.pos(destino_t.id)
        col_atk = colores.color_jugador(origen_t.tropas["dueno"])
        self.anim.estela(ox, oy, dx, dy, col_atk, n=12)
        gano = res["gano_atacante"]
        col = (90, 200, 110) if gano else (220, 90, 90)
        self.anim.explosion(dx, dy, col, n=22, rapidez=190)
        self.anim.pulso(destino_t.id, col, fuerza=1.2, dur=0.7)
        self.anim.texto(dx, dy + 18, "CONQUISTA" if gano else "RESISTE", col,
                        dur=1.2, tam=14)

    def _cancelar_batalla(self):
        self.panel_batalla.ocultar()
        self.mensaje = "Batalla cancelada."

    def _usar_heroe(self):
        jugador = self.estado.jugadores[self.estado.jugador_actual]
        if not jugador.heroe_disponible():
            self.mensaje = f"Heroe en recarga ({jugador.cooldown_heroe})."
            return
        if self.sel is None:
            self.mensaje = "Selecciona un territorio para el heroe."
            return
        t = self.estado.territorios[self.sel]
        if jugador.comandante == "vendedor_minutas" and t.tropas["dueno"] == jugador.id:
            comandantes.vendedor_minutas_fresco(t)
            self.mensaje = f"Vendedor de Minutas: +K en {t.nombre}."
            jugador.usar_heroe()
            tx, ty = self.vista_mapa.pos(t.id)
            self.anim.pulso(t.id, (90, 200, 110), fuerza=1.2, dur=0.8)
            self.anim.texto(tx, ty + 18, "+K", (90, 220, 120), dur=1.2, tam=15)
        elif jugador.comandante == "siguanaba" and t.tropas["dueno"] != jugador.id:
            comandantes.siguanaba_terror(t)
            self.mensaje = f"La Siguanaba: r negativa en {t.nombre}."
            jugador.usar_heroe()
            tx, ty = self.vista_mapa.pos(t.id)
            # r se vuelve NEGATIVA: lo que la habilidad hace a la EDO, visible.
            self.anim.pulso(t.id, (150, 80, 210), fuerza=1.4, dur=1.0)
            self.anim.explosion(tx, ty, (150, 80, 210), n=16, rapidez=120)
            self.anim.texto(tx, ty + 18, "r < 0", (200, 120, 230), dur=1.4, tam=15)
        else:
            self.mensaje = "Ese heroe no aplica a ese territorio."

    def _fin_de_turno(self):
        # El jugador en turno crece sus territorios un paso con el metodo/h activos
        actual = self.estado.jugador_actual
        antes = {tid: t.tropas["poblacion_actual"]
                 for tid, t in self.estado.territorios.items()
                 if t.tropas["dueno"] == actual}
        self.motor.fase_refuerzo(solo_dueno=actual)
        self._fx_crecimiento(antes)
        self.motor.fase_economia(solo_dueno=actual)
        eventos_msgs = self.gestor.paso(self.estado)
        self._fx_eventos(eventos_msgs)
        self.motor.fin_de_turno()

        ganador = self.estado.ganador()
        if ganador is not None:
            nombre = self.estado.jugadores[ganador].nombre
            self.mensaje = f"FIN: gana {nombre}!  (Esc para volver al menu)"
            self.terminado = True
            return

        self.estado.alternar_jugador()
        self.origen = None
        self.objetivos = set()
        self.vista_mapa.seleccion = None
        nombre = self.estado.jugadores[self.estado.jugador_actual].nombre
        base = f"Turno de {nombre}."
        self.mensaje = " | ".join(eventos_msgs + [base]) if eventos_msgs else base

    def _fx_crecimiento(self, antes):
        """Texto flotante +/- y pulso por cada territorio que crecio (o decayo,
        por huracan o Siguanaba). El crecimiento se VE."""
        for tid, valor_antes in antes.items():
            t = self.estado.territorios[tid]
            delta = t.tropas["poblacion_actual"] - valor_antes
            if abs(delta) < 0.5:
                continue
            x, y = self.vista_mapa.pos(tid)
            if delta > 0:
                self.anim.texto(x, y + 14, f"+{delta:.0f}", (120, 220, 140), tam=12)
                self.anim.pulso(tid, (90, 200, 110), fuerza=0.7, dur=0.5)
            else:
                self.anim.texto(x, y + 14, f"{delta:.0f}", (235, 120, 120), tam=12)
                self.anim.pulso(tid, (220, 90, 90), fuerza=0.7, dur=0.5)

    def _fx_eventos(self, msgs):
        """Espectaculo para los eventos dinamicos del mapa."""
        T = self.estado.territorios
        for m in msgs:
            if "Erupcion" in m and "san_miguel" in T:
                x, y = self.vista_mapa.pos("san_miguel")
                self.anim.explosion(x, y, (240, 140, 50), n=30, rapidez=230)
                self.anim.pulso("san_miguel", (240, 140, 50), fuerza=1.4, dur=0.8)
                self.anim.texto(x, y + 18, "ERUPCION", (255, 160, 60), dur=1.3, tam=14)
            elif "Marcha" in m and "Termina" not in m and "san_salvador" in T:
                x, y = self.vista_mapa.pos("san_salvador")
                self.anim.pulso("san_salvador", (120, 160, 240), fuerza=1.2, dur=0.9)
                self.anim.texto(x, y + 18, "MARCHA UES", (140, 180, 255), dur=1.3, tam=13)
            elif "Huracan" in m:
                for tid in T:
                    if "huracan" in T[tid].eventos_activos:
                        x, y = self.vista_mapa.pos(tid)
                        self.anim.pulso(tid, (80, 160, 220), fuerza=1.1, dur=0.9)
                        self.anim.texto(x, y + 18, "HURACAN", (120, 190, 240),
                                        dur=1.3, tam=13)


class VentanaApp(arcade.Window):
    """Ventana unica de la aplicacion. Cambia entre Menu, Reglas y Juego."""

    def __init__(self):
        super().__init__(colores.VENTANA_ANCHO, colores.VENTANA_ALTO,
                         "Risk Matematico - El Salvador")
        self.juego = None

    def on_close(self):
        # Si hay una partida en curso, cierra su base de datos limpiamente
        if self.juego is not None:
            self.juego.cerrar_partida()
        super().on_close()


def main():
    ventana = VentanaApp()
    from ui.vista_menu import VistaMenu
    ventana.show_view(VistaMenu())
    arcade.run()


if __name__ == "__main__":
    main()