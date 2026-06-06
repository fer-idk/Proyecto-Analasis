"""
animaciones.py
==============
Motor de animaciones de la interfaz + cache de texto. Es una capa PURAMENTE
VISUAL y ADITIVA: no toca la logica del juego (core/).

Incluye:
    - CacheTexto    : crea objetos arcade.Text una sola vez y los reutiliza.
                      Reemplaza a arcade.draw_text (que recalcula el texto en
                      cada frame y es muy lento) por la via recomendada por
                      Arcade. Cada texto en pantalla se identifica por una
                      'clave' estable; el cache lo crea la primera vez y solo
                      actualiza posicion/color/contenido despues.
    - TextoFlotante : un texto que sube y se desvanece ("+5", "r<0", "GANO").
    - Particula     : un punto con velocidad y gravedad (estallidos).
    - Pulso         : un anillo que late sobre un departamento.

Idea: la ventana "dispara" un efecto cuando pasa algo (batalla, crecimiento,
habilidad) y luego en cada frame le pide al gestor que se dibuje. El gestor
olvida solo los efectos expirados.
"""

import math
import random

import arcade


# ---------- Utilidades de interpolacion y color ----------

def ease_out(frac):
    """Suavizado easeOutCubic: rapido al inicio, lento al final (0..1)."""
    frac = max(0.0, min(1.0, frac))
    return 1.0 - (1.0 - frac) ** 3


def mezclar_color(c1, c2, frac):
    """Interpola linealmente entre dos colores RGB (frac 0..1)."""
    frac = max(0.0, min(1.0, frac))
    return tuple(int(a + (b - a) * frac) for a, b in zip(c1, c2))


def con_alfa(color, alfa):
    """Devuelve el color con canal alfa (0..255), aceptado por Arcade 3.x."""
    r, g, b = color[0], color[1], color[2]
    return (r, g, b, max(0, min(255, int(alfa))))


# ---------- Cache de texto (reemplazo rapido de draw_text) ----------

class CacheTexto:
    """Mantiene un arcade.Text por 'clave' y lo reutiliza entre frames.

    Uso:
        cache.dibujar("hud_titulo", "RISK", x, y, color, tam=17, bold=True)

    La primera vez crea el objeto Text; despues solo actualiza lo que cambia.
    Esto evita la PerformanceWarning de arcade.draw_text (que rehace el texto
    en cada llamada) y es mucho mas rapido."""

    def __init__(self):
        self._t = {}

    def dibujar(self, clave, texto, x, y, color, tam=12,
                anchor_x="left", bold=False):
        texto = str(texto)
        obj = self._t.get(clave)
        if obj is None:
            obj = arcade.Text(texto, x, y, color, tam,
                              anchor_x=anchor_x, bold=bold)
            self._t[clave] = obj
        else:
            if obj.text != texto:
                obj.text = texto
            obj.x = x
            obj.y = y
            obj.color = color
        obj.draw()


# ---------- Efectos individuales ----------

class _TextoFlotante:
    def __init__(self, t0, x, y, texto, color, dur, vy, tam):
        self.t0 = t0
        self.x, self.y = x, y
        self.color = color
        self.dur = dur
        self.vy = vy          # px/seg que sube
        # Objeto Text reutilizado a lo largo de la vida del efecto (no draw_text)
        self.obj = arcade.Text(str(texto), x, y, color, tam,
                               anchor_x="center", bold=True)

    def vivo(self, t):
        return (t - self.t0) < self.dur

    def dibujar(self, t):
        frac = (t - self.t0) / self.dur
        alfa = 255 * (1.0 - ease_out(frac))           # se desvanece
        self.obj.y = self.y + self.vy * (t - self.t0)
        self.obj.color = con_alfa(self.color, alfa)
        self.obj.draw()


class _Particula:
    def __init__(self, x, y, vx, vy, color, vida, radio):
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.color = color
        self.vida = vida
        self.vida_max = vida
        self.radio = radio

    def actualizar(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy -= 220 * dt                            # gravedad
        self.vida -= dt

    def vivo(self):
        return self.vida > 0

    def dibujar(self):
        frac = max(0.0, self.vida / self.vida_max)
        arcade.draw_circle_filled(self.x, self.y, self.radio * frac,
                                  con_alfa(self.color, 255 * frac))


# ---------- Gestor central ----------

class GestorAnimaciones:
    """Reloj + colecciones de efectos. La ventana lo actualiza una vez por
    frame y luego le pide que dibuje el "mundo" (sobre el mapa)."""

    def __init__(self):
        self.t = 0.0
        self._textos = []
        self._particulas = []
        self._pulsos = {}        # id_territorio -> dict(t0, dur, color, fuerza)

    # --- ciclo ---
    def actualizar(self, dt):
        self.t += dt
        self._textos = [tx for tx in self._textos if tx.vivo(self.t)]
        for p in self._particulas:
            p.actualizar(dt)
        self._particulas = [p for p in self._particulas if p.vivo()]
        self._pulsos = {k: v for k, v in self._pulsos.items()
                        if (self.t - v["t0"]) < v["dur"]}

    # --- disparadores (los llama la ventana cuando pasa algo) ---
    def texto(self, x, y, texto, color, dur=1.1, vy=34, tam=14):
        self._textos.append(_TextoFlotante(self.t, x, y, texto, color,
                                            dur, vy, tam))

    def explosion(self, x, y, color, n=18, rapidez=170, vida=0.7, radio=4):
        for _ in range(n):
            ang = random.uniform(0, 2 * math.pi)
            v = random.uniform(0.4, 1.0) * rapidez
            self._particulas.append(
                _Particula(x, y, math.cos(ang) * v, math.sin(ang) * v,
                           color, random.uniform(0.5, 1.0) * vida, radio))

    def pulso(self, id_territorio, color, fuerza=1.0, dur=0.6):
        self._pulsos[id_territorio] = {
            "t0": self.t, "dur": dur, "color": color, "fuerza": fuerza}

    def estela(self, x0, y0, x1, y1, color, n=10):
        """Rastro de tropas que 'vuelan' del origen al destino (batalla)."""
        for i in range(n):
            f = i / max(1, n - 1)
            x = x0 + (x1 - x0) * f
            y = y0 + (y1 - y0) * f
            jx, jy = random.uniform(-6, 6), random.uniform(-6, 6)
            self._particulas.append(
                _Particula(x + jx, y + jy, (x1 - x0) * 0.6, (y1 - y0) * 0.6,
                           color, 0.45, 5))

    # --- consultas (las usan las vistas al dibujar) ---
    def intensidad_pulso(self, id_territorio):
        """(intensidad 0..1, color) del pulso activo de un territorio, o
        (0.0, None) si no hay. Decae con easeOut."""
        p = self._pulsos.get(id_territorio)
        if p is None:
            return 0.0, None
        frac = (self.t - p["t0"]) / p["dur"]
        return (1.0 - ease_out(frac)) * p["fuerza"], p["color"]

    def latido(self, periodo=0.8):
        """Onda 0..1 continua para resaltes que 'respiran'. No expira."""
        return 0.5 + 0.5 * math.sin(2 * math.pi * self.t / periodo)

    # --- dibujo ---
    def dibujar_mundo(self):
        """Efectos sobre el area del mapa (particulas y textos flotantes)."""
        for p in self._particulas:
            p.dibujar()
        for tx in self._textos:
            tx.dibujar(self.t)
