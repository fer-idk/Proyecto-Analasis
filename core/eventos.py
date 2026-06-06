"""
eventos.py
==========
Eventos dinamicos del mapa. Igual que los heroes, se dividen en continuos
(tocan la EDO) y discretos (reglas de juego).

    Temporal / Huracan          -> CONTINUO: r negativa en la costa (desgaste).
    Marcha en la UES            -> DISCRETO: bloqueo total + bono de defensa.
    Erupcion del Chaparrastique -> DISCRETO: golpe instantaneo -30% tropas.
    Trafico en Los Chorros      -> DISCRETO de ARISTA: encarece un corredor.
"""

# Departamentos costeros que golpea el huracan
COSTA = ["usulutan", "la_paz", "sonsonate"]


def huracan(territorio, valor_r=-0.4, turnos=2):
    """TEMPORAL (continuo): durante 'turnos', la tasa de crecimiento de tropas
    se vuelve negativa, causando desgaste. Igual mecanismo que el Terror de la
    Siguanaba, pero por clima y sobre la zona costera."""
    territorio.agregar_ajuste(
        fuente="evento:huracan", objetivo="r_tropas",
        operacion="set", valor=valor_r, turnos=turnos)
    if "huracan" not in territorio.eventos_activos:
        territorio.eventos_activos.append("huracan")


def marcha_ues(territorio, bono_defensa=15):
    """MARCHA EN LA UES (discreto): bloquea por completo el movimiento dentro y
    fuera del departamento y otorga un bono de defensa a quien lo controle. No
    toca r ni K: lo gestiona la logica de turnos y de batalla."""
    territorio.flags["movimiento_bloqueado"] = True
    territorio.flags["bono_defensa"] = bono_defensa
    if "marcha_ues" not in territorio.eventos_activos:
        territorio.eventos_activos.append("marcha_ues")


def fin_marcha_ues(territorio):
    """Levanta el bloqueo de la Marcha."""
    territorio.flags["movimiento_bloqueado"] = False
    territorio.flags["bono_defensa"] = 0
    if "marcha_ues" in territorio.eventos_activos:
        territorio.eventos_activos.remove("marcha_ues")


def erupcion_chaparrastique(territorio, fraccion=0.30):
    """ERUPCION (discreto): elimina instantaneamente una fraccion de las tropas
    y anula la produccion de recursos por un turno. Es un golpe puntual, no un
    modificador continuo. Devuelve las tropas perdidas."""
    perdidas = territorio.tropas["poblacion_actual"] * fraccion
    territorio.tropas["poblacion_actual"] -= perdidas
    territorio.produccion_anulada = True
    if "erupcion_chaparrastique" not in territorio.eventos_activos:
        territorio.eventos_activos.append("erupcion_chaparrastique")
    return perdidas


# El trafico es propiedad de la CONEXION entre departamentos, no de uno solo,
# por eso no recibe un Territorio. El motor de movimiento consulta este costo.
CORREDOR_TRAFICO = {
    ("santa_ana", "san_salvador"): 2,
    ("la_libertad", "san_salvador"): 2,
}


def costo_movimiento(origen_id, destino_id, trafico_activo=False):
    """Devuelve cuantos turnos tarda mover tropas entre dos departamentos.
    Normalmente 1; si el Trafico esta activo y el par esta en el corredor, 2."""
    if not trafico_activo:
        return 1
    par = (origen_id, destino_id)
    par_inv = (destino_id, origen_id)
    return CORREDOR_TRAFICO.get(par, CORREDOR_TRAFICO.get(par_inv, 1))