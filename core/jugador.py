"""
jugador.py
==========
Modelo de un jugador: su comandante (heroe), sus recursos y el cooldown de la
habilidad. Los territorios que controla NO se guardan aqui; se derivan del
campo tropas['dueno'] de cada Territorio (una sola fuente de verdad evita
inconsistencias).
"""


class Jugador:
    def __init__(self, id, nombre, comandante=None):
        self.id = id
        self.nombre = nombre
        self.comandante = comandante            # 'cipitio'|'siguanaba'|'vendedor_minutas'
        self.recursos = {"cafe": 0.0, "pupusas": 0.0}
        self.cooldown_heroe = 0

    # ---------- Recursos ----------
    def puede_pagar(self, recurso, costo):
        return self.recursos.get(recurso, 0.0) >= costo

    def gastar(self, recurso, costo):
        if not self.puede_pagar(recurso, costo):
            return False
        self.recursos[recurso] -= costo
        return True

    def ingresar(self, recurso, cantidad):
        self.recursos[recurso] = self.recursos.get(recurso, 0.0) + cantidad

    # ---------- Heroe ----------
    def heroe_disponible(self):
        return self.cooldown_heroe == 0

    def usar_heroe(self, cooldown=2):
        """Marca la habilidad como usada (entra en cooldown)."""
        self.cooldown_heroe = cooldown

    def reducir_cooldown(self, cantidad=1):
        """El cafe puede acelerar la recarga del heroe."""
        self.cooldown_heroe = max(0, self.cooldown_heroe - cantidad)

    def tick(self):
        """Avanza un turno: baja el cooldown del heroe."""
        if self.cooldown_heroe > 0:
            self.cooldown_heroe -= 1

    def __repr__(self):
        return (f"<Jugador {self.id} ({self.nombre}) comandante={self.comandante} "
                f"cafe={self.recursos['cafe']:.0f} pupusas={self.recursos['pupusas']:.0f}>")