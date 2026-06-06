"""
turnos.py
=========
Motor de turnos. Orquesta las fases y, sobre todo, ejecuta la FASE DE REFUERZO,
que es donde el metodo numerico rige el estado real del juego: cada turno las
tropas y los recursos de cada territorio crecen UN PASO de tamano h con el
metodo activo (Euler o RK4).

Consecuencia jugable directa: si el jugador elige Euler con un h grande, el
crecimiento de UN turno puede sobrepasar la capacidad K y desestabilizarse;
con RK4 (o con h pequeno) se mantiene fiel. Asi, la eleccion de metodo y paso
tiene un costo real, y queda registrada en la base de datos turno a turno.

Fases: refuerzo -> eventos -> ataque -> fin
(eventos y ataque los disparan las acciones del jugador; el motor provee
refuerzo y el cierre de turno).
"""

from metodos import euler, rk4
from metodos.modelos import logistica
from core import economia

FASES = ("refuerzo", "eventos", "ataque", "fin")


class MotorTurnos:
    def __init__(self, estado, repo=None, partida_id=None):
        self.estado = estado
        self.repo = repo
        self.partida_id = partida_id

    def _metodo(self):
        return euler if self.estado.metodo_activo == "euler" else rk4

    def _crecer_un_paso(self, valor, r, K):
        """Avanza la variable un paso h con el metodo activo."""
        f = logistica(r, K)
        return self._metodo().paso(f, 0.0, valor, self.estado.h_activo)

    def fase_refuerzo(self, solo_dueno=None):
        """Crece tropas y recursos de los territorios con dueno. Si se pasa
        'solo_dueno', solo crecen los de ese jugador (su turno)."""
        metodo_nombre = self.estado.metodo_activo
        h = self.estado.h_activo
        for t in self.estado.territorios.values():
            if t.tropas["dueno"] is None:
                continue
            if solo_dueno is not None and t.tropas["dueno"] != solo_dueno:
                continue
            evento = t.eventos_activos[0] if t.eventos_activos else None

            # --- Tropas ---
            r, K = t.parametros_tropas()
            # Pupusas (energia): si el dueno tiene pupusas, aceleran el
            # crecimiento de las tropas (consume un poco por territorio).
            jug = self.estado.jugadores.get(t.tropas["dueno"])
            if jug is not None and jug.recursos.get("pupusas", 0) >= 2:
                r = r * 1.15
                jug.recursos["pupusas"] -= 2
            N = t.tropas["poblacion_actual"]
            N_next = max(0.0, self._crecer_un_paso(N, r, K))
            t.tropas["poblacion_actual"] = N_next
            if self.repo is not None:
                self.repo.registrar_calculo(
                    self.partida_id, self.estado.turno, t.id, "tropas",
                    metodo_nombre, h, r, K, paso_n=0, t=h, valor=N_next,
                    heroe=t.heroe_presente, evento=evento)

            # --- Recursos (si la produccion no esta anulada) ---
            if not t.produccion_anulada:
                rr, KK = t.parametros_recurso()
                C = t.recurso["cantidad_actual"]
                C_next = max(0.0, self._crecer_un_paso(C, rr, KK))
                t.recurso["cantidad_actual"] = C_next
                if self.repo is not None:
                    self.repo.registrar_calculo(
                        self.partida_id, self.estado.turno, t.id, "recurso",
                        metodo_nombre, h, rr, KK, paso_n=0, t=h, valor=C_next,
                        heroe=t.heroe_presente, evento=evento)

    def fase_economia(self, solo_dueno=None):
        """Cada territorio entrega a su dueno la cosecha SOSTENIBLE de su
        recurso (r*K/4), sin agotarlo. Cafe = moneda, pupusas = energia."""
        for t in self.estado.territorios.values():
            dueno = t.tropas["dueno"]
            if dueno is None:
                continue
            if solo_dueno is not None and dueno != solo_dueno:
                continue
            if t.produccion_anulada:
                continue
            r, K = t.parametros_recurso()
            sostenible = economia.rendimiento_maximo_sostenible(r, K)
            res = economia.extraer(t, sostenible)
            jug = self.estado.jugadores.get(dueno)
            if jug is not None:
                jug.ingresar(t.recurso["tipo"], res["extraido"])

    def fin_de_turno(self):
        """Cierra el turno: expira modificadores temporales, baja cooldowns y
        avanza el contador de turno."""
        for t in self.estado.territorios.values():
            t.fin_de_turno()
        for j in self.estado.jugadores.values():
            j.tick()
        self.estado.turno += 1