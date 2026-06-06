"""
db.py
=====
Conexion a SQLite y definicion del esquema. Es la unica parte del proyecto
que conoce la estructura fisica de la base de datos.

Tres tablas:
    partidas : una fila por partida jugada.
    calculos : UN PASO de Euler o RK4 por fila (cada calculo del metodo,
               como exige la guia). De aqui se reconstruyen las graficas.
    batallas : resultado de cada batalla junto con las predicciones de ambos
               metodos, para relacionar precision numerica con desenlace.

inicializar() es idempotente: se puede llamar siempre, crea las tablas solo
si no existen.
"""

import sqlite3

ESQUEMA = """
CREATE TABLE IF NOT EXISTS partidas (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha_inicio  TEXT NOT NULL DEFAULT (datetime('now','localtime')),
    fecha_fin     TEXT,
    ganador       TEXT,
    notas         TEXT
);

CREATE TABLE IF NOT EXISTS calculos (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    partida_id      INTEGER NOT NULL REFERENCES partidas(id),
    turno           INTEGER NOT NULL,
    departamento_id TEXT    NOT NULL,
    variable        TEXT    NOT NULL,   -- 'tropas' o 'recurso'
    metodo          TEXT    NOT NULL,   -- 'euler' o 'rk4'
    h               REAL    NOT NULL,
    r_efectiva      REAL    NOT NULL,
    k_efectiva      REAL    NOT NULL,
    paso_n          INTEGER NOT NULL,   -- indice del paso dentro de la trayectoria
    t               REAL    NOT NULL,
    valor           REAL    NOT NULL,   -- N (poblacion/recurso) en ese t
    heroe_activo    TEXT,
    evento_activo   TEXT,
    creado_en       TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS batallas (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    partida_id        INTEGER NOT NULL REFERENCES partidas(id),
    turno             INTEGER NOT NULL,
    atacante          TEXT    NOT NULL,
    defensor          TEXT    NOT NULL,
    h_usado           REAL    NOT NULL,
    prediccion_euler  REAL,
    prediccion_rk4    REAL,
    metodo_confiado   TEXT,             -- en cual prediccion se baso la decision
    resultado         TEXT    NOT NULL, -- 'gano_atacante' / 'gano_defensor'
    tropas_atacante   REAL,
    tropas_defensor   REAL,
    creado_en         TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
);

CREATE INDEX IF NOT EXISTS idx_calc_partida ON calculos(partida_id);
CREATE INDEX IF NOT EXISTS idx_calc_grupo
    ON calculos(partida_id, turno, departamento_id, variable, metodo, h);
CREATE INDEX IF NOT EXISTS idx_bat_partida ON batallas(partida_id);
"""


def conectar(ruta_db):
    """Abre una conexion a SQLite con claves foraneas activadas y filas
    accesibles por nombre de columna."""
    con = sqlite3.connect(str(ruta_db))
    con.execute("PRAGMA foreign_keys = ON")
    con.row_factory = sqlite3.Row
    return con


def inicializar(ruta_db):
    """Abre la conexion y crea las tablas si no existen. Devuelve la conexion."""
    con = conectar(ruta_db)
    con.executescript(ESQUEMA)
    con.commit()
    return con