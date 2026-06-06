"""
test_core.py
============
Pruebas de la logica del juego. Ejecutar desde la raiz:  pytest -v
"""

from core.cargador import cargar_mapa
from core.game_state import EstadoJuego
from core.jugador import Jugador
from core.turnos import MotorTurnos
from core import comandantes, eventos, economia, estabilidad
from core.batalla import resolver

RUTA_JSON = "data/departamentos.json"


def _territorios():
    terr, cfg = cargar_mapa(RUTA_JSON)
    return terr, cfg


# ---------- Modificadores (continuo) ----------
def test_siguanaba_vuelve_r_negativa():
    terr, _ = _territorios()
    t = terr["usulutan"]
    r0, _ = t.parametros_tropas()
    comandantes.siguanaba_terror(t)
    r1, _ = t.parametros_tropas()
    assert r0 > 0 and r1 < 0


def test_vendedor_sube_K_y_persiste():
    terr, _ = _territorios()
    t = terr["san_salvador"]
    _, K0 = t.parametros_tropas()
    comandantes.vendedor_minutas_fresco(t)
    _, K1 = t.parametros_tropas()
    assert K1 > K0
    t.fin_de_turno()
    t.fin_de_turno()
    _, K2 = t.parametros_tropas()
    assert K2 == K1   # permanente mientras el heroe este presente


def test_huracan_expira_en_dos_turnos():
    terr, _ = _territorios()
    t = terr["la_paz"]
    r0, _ = t.parametros_tropas()
    eventos.huracan(t)
    assert t.parametros_tropas()[0] < 0
    t.fin_de_turno()
    t.fin_de_turno()
    assert t.parametros_tropas()[0] == r0   # vuelve a la base


# ---------- Economia ----------
def test_extraccion_sostenible_no_colapsa():
    terr, _ = _territorios()
    t = terr["santa_ana"]
    r, K = t.parametros_recurso()
    sostenible = economia.rendimiento_maximo_sostenible(r, K)
    res = economia.extraer(t, sostenible * 0.5)
    assert not res["sobreexplota"]


def test_sobreexplotacion_marca_colapso():
    terr, _ = _territorios()
    t = terr["la_union"]
    r, K = t.parametros_recurso()
    sostenible = economia.rendimiento_maximo_sostenible(r, K)
    res = economia.extraer(t, sostenible * 5)
    assert res["sobreexplota"]


# ---------- Batalla ----------
def test_batalla_no_deja_origen_negativo():
    terr, cfg = _territorios()
    terr["san_miguel"].tropas["dueno"] = "j1"
    terr["usulutan"].tropas["dueno"] = "j2"
    est = EstadoJuego(terr, {"j1": Jugador("j1", "A"), "j2": Jugador("j2", "B")}, cfg)
    resolver(est, terr["san_miguel"], terr["usulutan"],
             tropas_comprometidas=9999)   # mas de las que hay
    assert terr["san_miguel"].tropas["poblacion_actual"] >= 0


# ---------- Estabilidad ----------
def test_zonas_de_estabilidad():
    assert estabilidad.clasificar(0.1, 1.0) == "verde"
    assert estabilidad.clasificar(1.5, 1.0) == "amarilla"
    assert estabilidad.clasificar(2.2, 1.0) == "roja"
    assert estabilidad.clasificar(3.0, 1.0) == "caos"


def test_euler_penalizado_mas_que_rk4_en_caos():
    f_euler = estabilidad.factor_combate("euler", "caos")
    f_rk4 = estabilidad.factor_combate("rk4", "caos")
    assert f_euler < f_rk4