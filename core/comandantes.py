"""
comandantes.py
==============
Los comandantes locales (heroes) y sus habilidades. Cada habilidad se expresa
como un cambio sobre un Territorio.

Lo importante para la defensa: dos de las tres habilidades son CONTINUAS
(modifican r o K, es decir, entran a la EDO que resuelven Euler y RK4), y una
es DISCRETA (mueve tropas, no toca ninguna ecuacion). El codigo refleja esa
distincion:

    La Siguanaba (Terror)          -> CONTINUO: vuelve r negativa (desgaste).
    El Vendedor de Minutas (Fresco)-> CONTINUO: sube K (mas capacidad).
    El Cipitio (Teletransporte)    -> DISCRETO: mueve tropas sin fronteras.
"""

CATALOGO = {
    "cipitio": {
        "nombre": "El Cipitio",
        "habilidad": "Teletransporte",
        "tipo": "discreto",
        "descripcion": "Mueve tropas entre departamentos no fronterizos.",
    },
    "siguanaba": {
        "nombre": "La Siguanaba",
        "habilidad": "Terror",
        "tipo": "continuo",
        "descripcion": "Vuelve negativa la tasa r de un territorio enemigo vecino.",
    },
    "vendedor_minutas": {
        "nombre": "El Vendedor de Minutas",
        "habilidad": "Fresco",
        "tipo": "continuo",
        "descripcion": "Aumenta la capacidad K del territorio donde se encuentra.",
    },
}


def siguanaba_terror(territorio_enemigo, valor_r=-0.5, turnos=1):
    """TERROR (continuo): fuerza r de las tropas enemigas a un valor negativo
    durante 'turnos'. Al ser r < 0, la logistica se vuelve desgaste: las
    tropas decaen en vez de crecer. El efecto se siente directo en la EDO."""
    territorio_enemigo.agregar_ajuste(
        fuente="heroe:siguanaba", objetivo="r_tropas",
        operacion="set", valor=valor_r, turnos=turnos)


def vendedor_minutas_fresco(territorio, bono_K=25.0):
    """FRESCO (continuo): suma capacidad K a las tropas mientras el heroe este
    presente (turnos = -1). Mas K = la poblacion puede crecer y estabilizarse
    mas alto. Se limpia primero para no duplicar el bono si se reaplica."""
    territorio.quitar_ajustes_de("heroe:vendedor_minutas")
    territorio.agregar_ajuste(
        fuente="heroe:vendedor_minutas", objetivo="K_tropas",
        operacion="add", valor=bono_K, turnos=-1)
    territorio.heroe_presente = "vendedor_minutas"


def vendedor_minutas_se_retira(territorio):
    """Cuando el Vendedor se va, su bono de K desaparece solo."""
    territorio.quitar_ajustes_de("heroe:vendedor_minutas")
    if territorio.heroe_presente == "vendedor_minutas":
        territorio.heroe_presente = None


def cipitio_teletransporte(origen, destino, n_tropas):
    """TELETRANSPORTE (discreto): mueve hasta n_tropas de un territorio a otro
    SIN exigir que sean vecinos. No modifica ninguna ecuacion: es una regla de
    movimiento. Devuelve cuantas tropas se movieron realmente."""
    disponibles = origen.tropas["poblacion_actual"]
    n = min(n_tropas, disponibles)
    origen.tropas["poblacion_actual"] -= n
    destino.tropas["poblacion_actual"] += n
    return n