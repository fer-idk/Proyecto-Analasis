"""
territorio.py
=============
Modelo de un departamento durante la partida. Envuelve los datos del
departamentos.json y anade el comportamiento que el juego necesita.

Principio central (el que defiende todo el diseno):
    - r_base y K_base NUNCA se modifican.
    - Heroes y eventos se apilan como MODIFICADORES.
    - parametros() pliega los modificadores activos sobre la base y devuelve
      el (r, K) EFECTIVO que se le pasa a euler/rk4.

Asi, cuando un modificador expira, basta con quitarlo de la lista: el
territorio vuelve solo a su base. No hay nada que "restaurar" a mano.

Distincion clave:
    - ajustes_continuos  -> entran a la EDO (cambian r o K). Ej: Siguanaba.
    - flags_discretos    -> NO entran a la EDO (bloqueos, bonos). Ej: Marcha UES.
"""


class Territorio:
    def __init__(self, datos):
        self.id = datos["id"]
        self.nombre = datos["nombre"]
        self.zona = datos["zona"]
        self.vecinos = list(datos["vecinos"])
        self.color_mask = datos["color_mask"]
        self.centro = tuple(datos["centro"])

        # Copias propias para no mutar el dict original cargado del JSON
        self.tropas = dict(datos["tropas"])      # dueno, poblacion_actual, r_base, K_base
        self.recurso = dict(datos["recurso"])    # tipo, cantidad_actual, r_base, K_base

        m = datos.get("modificadores", {})
        self.heroe_presente = m.get("heroe_presente")
        self.eventos_activos = list(m.get("eventos_activos", []))
        self.flags = dict(m.get("flags_discretos", {}))
        self.ajustes = [dict(a) for a in m.get("ajustes_continuos", [])]
        self.produccion_anulada = False

    # ---------- Plegado de modificadores (continuo -> EDO) ----------
    @staticmethod
    def _aplicar_op(base, operacion, valor):
        if operacion == "add":
            return base + valor
        if operacion == "mult":
            return base * valor
        if operacion == "set":
            return valor
        return base

    def parametros(self, variable):
        """Devuelve (r_efectiva, K_efectiva) para 'tropas' o 'recurso',
        plegando en orden los ajustes_continuos que apunten a esa variable.
        K se mantiene > 0 para no romper la division N/K de la logistica."""
        fuente = self.tropas if variable == "tropas" else self.recurso
        r = fuente["r_base"]
        K = fuente["K_base"]
        obj_r, obj_K = f"r_{variable}", f"K_{variable}"
        for a in self.ajustes:
            if a["objetivo"] == obj_r:
                r = self._aplicar_op(r, a["operacion"], a["valor"])
            elif a["objetivo"] == obj_K:
                K = self._aplicar_op(K, a["operacion"], a["valor"])
        if K <= 0:
            K = 1e-6
        return r, K

    def parametros_tropas(self):
        return self.parametros("tropas")

    def parametros_recurso(self):
        return self.parametros("recurso")

    # ---------- Gestion de modificadores ----------
    def agregar_ajuste(self, fuente, objetivo, operacion, valor, turnos):
        """Apila un ajuste continuo. turnos = -1 significa 'mientras la fuente
        este presente' (no expira solo); turnos >= 1 expira tras ese numero."""
        self.ajustes.append({
            "fuente": fuente, "objetivo": objetivo, "operacion": operacion,
            "valor": valor, "turnos_restantes": turnos,
        })

    def quitar_ajustes_de(self, fuente):
        """Elimina los ajustes de una fuente (ej. cuando un heroe se va)."""
        self.ajustes = [a for a in self.ajustes if a["fuente"] != fuente]

    def fin_de_turno(self):
        """Avanza el reloj de los modificadores: descuenta un turno y elimina
        los que expiran. Los permanentes (turnos_restantes < 0) se conservan.
        La anulacion de produccion dura un solo turno."""
        conservados = []
        for a in self.ajustes:
            tr = a["turnos_restantes"]
            if tr < 0:
                conservados.append(a)              # permanente
            elif tr > 1:
                a["turnos_restantes"] = tr - 1
                conservados.append(a)
            # tr == 1  -> expira este turno (no se conserva)
        self.ajustes = conservados
        self.produccion_anulada = False

    # ---------- Accesos discretos ----------
    @property
    def bloqueado(self):
        return self.flags.get("movimiento_bloqueado", False)

    @property
    def bono_defensa(self):
        return self.flags.get("bono_defensa", 0)

    def es_vecino_de(self, otro_id):
        return otro_id in self.vecinos

    def __repr__(self):
        r, K = self.parametros_tropas()
        return (f"<Territorio {self.id} dueno={self.tropas['dueno']} "
                f"N={self.tropas['poblacion_actual']:.1f} r_ef={r:.2f} K_ef={K:.1f}>")