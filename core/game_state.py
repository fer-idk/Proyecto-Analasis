"""
game_state.py
=============
Contenedor del estado global de una partida. Es el objeto que se pasa entre
las distintas piezas (motor de turnos, batalla, economia) y que concentra:

    - territorios : dict id -> Territorio
    - jugadores   : dict id -> Jugador
    - turno       : numero de turno actual
    - metodo_activo / h_activo : el metodo y paso que RIGEN el estado real.
      Son lo que el jugador ajusta con el slider; cambiarlos afecta como
      crecen las tropas cada turno (y por tanto la estabilidad numerica).
"""


class EstadoJuego:
    def __init__(self, territorios, jugadores, config):
        self.territorios = territorios          # dict id -> Territorio
        self.jugadores = jugadores              # dict id -> Jugador
        self.config = config
        self.turno = 1
        self.metodo_activo = config.get("metodo_default", "rk4")  # 'euler' o 'rk4'
        self.h_activo = config.get("h_default", 0.1)
        self.orden = list(jugadores.keys())
        self.jugador_actual = self.orden[0] if self.orden else None

    def alternar_jugador(self):
        """Pasa el turno al siguiente jugador (hotseat)."""
        if not self.orden:
            return
        i = self.orden.index(self.jugador_actual)
        self.jugador_actual = self.orden[(i + 1) % len(self.orden)]

    def territorios_de(self, jugador_id):
        return [t for t in self.territorios.values()
                if t.tropas["dueno"] == jugador_id]

    def sigue_vivo(self, jugador_id):
        """Un jugador sigue en juego si controla al menos un territorio."""
        return len(self.territorios_de(jugador_id)) > 0

    def total_tropas(self, jugador_id):
        return sum(t.tropas["poblacion_actual"]
                   for t in self.territorios_de(jugador_id))

    def ganador(self):
        """Devuelve el id del jugador ganador si solo queda uno con
        territorios; None si la partida sigue."""
        vivos = [j for j in self.orden if self.sigue_vivo(j)]
        return vivos[0] if len(vivos) == 1 else None