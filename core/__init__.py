"""Paquete core: logica del juego (modelo, heroes, eventos, prediccion,
jugador, economia, batalla, motor de turnos, estado, estabilidad, gestor de eventos)."""
from . import (territorio, comandantes, eventos, prediccion, cargador,  # noqa: F401
               jugador, economia, batalla, turnos, game_state,
               estabilidad, gestor_eventos)