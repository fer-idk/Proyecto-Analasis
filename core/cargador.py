"""
cargador.py
===========
Carga el departamentos.json y lo convierte en un diccionario de objetos
Territorio listos para jugar: { "san_salvador": <Territorio>, ... }.

Tambien devuelve la config_global (h por defecto, turnos de prediccion, etc.)
y valida que los vecinos sean simetricos, para detectar errores del mapa al
arrancar en vez de a mitad de partida.
"""

import json

from core.territorio import Territorio


def cargar_mapa(ruta_json):
    """Devuelve (territorios, config) donde territorios es un dict id->Territorio."""
    with open(ruta_json, encoding="utf-8") as f:
        data = json.load(f)

    territorios = {d["id"]: Territorio(d) for d in data["departamentos"]}
    config = data.get("config_global", {})

    _validar_vecinos(territorios)
    return territorios, config


def _validar_vecinos(territorios):
    """Falla temprano si la topologia es incoherente."""
    for t in territorios.values():
        for v in t.vecinos:
            if v not in territorios:
                raise ValueError(f"{t.id} apunta a vecino inexistente: {v}")
            if t.id not in territorios[v].vecinos:
                raise ValueError(
                    f"Vecindad asimetrica: {t.id}->{v} pero {v} no lista a {t.id}")