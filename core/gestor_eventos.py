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

class GestorCaos:
    def __init__(self, territorios):
        self.territorios = territorios
        # Turnos faltantes para que estalle el primer evento aleatorio
        self.turnos_para_evento = random.randint(2, 5) 
        self.evento_actual = None

        # Catálogo de caos geográfico
        self.catalogo_eventos = [
            {
                "nombre": "¡Feria de San Miguel!",
                "afectados": ["san_miguel", "usulutan", "morazan", "la_union"],
                "tipo": "boom",
                "multiplicador": 3.0, # Triplica el crecimiento
                "duracion": 2
            },
            {
                "nombre": "Desborde del Río Lempa",
                "afectados": ["chalatenango", "san_vicente", "usulutan"],
                "tipo": "desastre",
                "multiplicador": -2.0, # Mata tropas en lugar de crearlas
                "duracion": 1
            },
            {
                "nombre": "Fiebre Turística",
                "afectados": ["la_libertad", "san_salvador", "sonsonate"],
                "tipo": "mercenarios",
                "multiplicador": 2.5,
                "duracion": 3
            }
        ]

    def procesar_turno(self):
        """Llama a esta función cada vez que termine una ronda o turno global."""
        
        # 1. Reducir la duración del evento activo
        if self.evento_actual:
            self.evento_actual["duracion"] -= 1
            if self.evento_actual["duracion"] <= 0:
                self.limpiar_evento()

        # 2. Cuenta regresiva para el siguiente desastre/milagro
        if not self.evento_actual:
            self.turnos_para_evento -= 1
            if self.turnos_para_evento <= 0:
                self.disparar_evento()

        # 3. Aplicar las matemáticas de crecimiento a todo el mapa
        self.crecer_tropas()

    def disparar_evento(self):
        self.evento_actual = random.choice(self.catalogo_eventos).copy()
        # Resetear el temporizador para el siguiente evento (aleatorio entre 4 y 7 turnos)
        self.turnos_para_evento = random.randint(4, 7) 

        # Añadir la etiqueta al territorio (esto hará que tu UI lo muestre en rojo en los tooltips)
        for dep in self.evento_actual["afectados"]:
            if dep in self.territorios:
                self.territorios[dep].eventos_activos.append(self.evento_actual["nombre"])

    def limpiar_evento(self):
        for dep in self.evento_actual["afectados"]:
            if dep in self.territorios:
                nombre_evt = self.evento_actual["nombre"]
                if nombre_evt in self.territorios[dep].eventos_activos:
                    self.territorios[dep].eventos_activos.remove(nombre_evt)
        self.evento_actual = None

    def crecer_tropas(self):
        crecimiento_base = 1.2 # Tropas generadas por turno normal

        for id_t, t in self.territorios.items():
            # Obtener el límite logístico del territorio
            r_ef, K_ef = t.parametros_tropas() 
            pob = t.tropas['poblacion_actual']

            multiplicador = 1.0

            # Verificar si el departamento actual es víctima del caos
            if self.evento_actual and id_t in self.evento_actual["afectados"]:
                multiplicador = self.evento_actual["multiplicador"]

            # Solo crecemos si no hemos llegado al tope del anillo logístico (K_ef)
            # O si el multiplicador es negativo (desastre natural quitando tropas)
            if pob < K_ef or multiplicador < 0:
                nuevas_tropas = crecimiento_base * multiplicador
                
                # Actualizar población, asegurando que nunca baje de 1 tropa
                t.tropas['poblacion_actual'] = max(1.0, pob + nuevas_tropas)
                
                # Opcional: Si supera la capacidad por un boom, lo topamos al máximo
                if multiplicador > 0 and t.tropas['poblacion_actual'] > K_ef:
                    t.tropas['poblacion_actual'] = K_ef