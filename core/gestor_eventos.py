"""
gestor_eventos.py
=================
Hace que "el mapa este vivo": cada turno, con cierta probabilidad, dispara uno
de los eventos dinamicos y gestiona los que duran varios turnos.

Mantiene el estado de los eventos discretos que hay que levantar a mano
(la Marcha en la UES y el Trafico). Los eventos continuos (Huracan) se apagan
solos cuando expira su modificador en territorio.fin_de_turno().

Devuelve mensajes legibles para mostrarlos en el HUD.
"""

import random

from core import eventos

COSTA = ["usulutan", "la_paz", "sonsonate"]


class GestorEventos:
    def __init__(self, probabilidad=0.45, semilla=None):
        self.prob = probabilidad
        self.rng = random.Random(semilla)
        self.marcha_en = None          # id del depto con Marcha activa
        self.marcha_turnos = 0
        self.trafico_activo = False

    def paso(self, estado):
        """Llamar una vez por turno. Devuelve lista de mensajes."""
        msgs = []
        T = estado.territorios

        # 1) Levantar la Marcha si ya cumplio su tiempo
        if self.marcha_en is not None:
            self.marcha_turnos -= 1
            if self.marcha_turnos <= 0:
                eventos.fin_marcha_ues(T[self.marcha_en])
                msgs.append(f"Termina la Marcha en {T[self.marcha_en].nombre}.")
                self.marcha_en = None

        # 2) Posible nuevo evento
        if self.rng.random() <= self.prob:
            m = self._disparar(estado)
            if m:
                msgs.append(m)
        return msgs

    def _disparar(self, estado):
        T = estado.territorios
        opciones = ["huracan", "erupcion", "marcha", "trafico"]
        ev = self.rng.choice(opciones)

        if ev == "huracan":
            costa = [d for d in COSTA if d in T]
            dep = self.rng.choice(costa)
            eventos.huracan(T[dep])
            return f"Huracan en {T[dep].nombre}: r negativa por 2 turnos."

        if ev == "erupcion" and "san_miguel" in T:
            perd = eventos.erupcion_chaparrastique(T["san_miguel"])
            return f"Erupcion del Chaparrastique: -{perd:.0f} tropas en San Miguel."

        if ev == "marcha" and "san_salvador" in T and self.marcha_en is None:
            eventos.marcha_ues(T["san_salvador"])
            self.marcha_en = "san_salvador"
            self.marcha_turnos = 2
            return "Marcha en la UES: San Salvador bloqueado (+defensa) 2 turnos."

        if ev == "trafico":
            self.trafico_activo = not self.trafico_activo
            estado_txt = "activado" if self.trafico_activo else "despejado"
            return f"Trafico en Los Chorros {estado_txt}."

        return None