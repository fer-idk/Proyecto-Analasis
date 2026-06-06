"""
repositorio.py
==============
API de alto nivel para guardar y consultar datos. El resto del juego usa
SOLO estas funciones; nadie mas escribe SQL.

Uso tipico desde el motor del juego:

    from persistencia.repositorio import Repositorio
    from metodos import euler, rk4
    from metodos.modelos import logistica

    repo = Repositorio("partidas/risk.db")
    pid = repo.crear_partida(notas="Partida de prueba")

    f = logistica(r_ef, k_ef)
    ts, ys = euler.integrar(f, N0, 0, turnos, h)
    pred = repo.registrar_trayectoria(pid, turno, "san_miguel", "tropas",
                                      "euler", h, r_ef, k_ef, ts, ys,
                                      evento="erupcion_chaparrastique")
    ...
    repo.finalizar_partida(pid, ganador="jugador_1")
    repo.cerrar()
"""

from persistencia import db


class Repositorio:
    def __init__(self, ruta_db):
        self.ruta_db = ruta_db
        self.con = db.inicializar(ruta_db)

    # ---------- Partidas ----------
    def crear_partida(self, notas=""):
        cur = self.con.execute(
            "INSERT INTO partidas (notas) VALUES (?)", (notas,))
        self.con.commit()
        return cur.lastrowid

    def finalizar_partida(self, partida_id, ganador):
        self.con.execute(
            "UPDATE partidas SET ganador = ?, "
            "fecha_fin = datetime('now','localtime') WHERE id = ?",
            (ganador, partida_id))
        self.con.commit()

    # ---------- Calculos ----------
    def registrar_calculo(self, partida_id, turno, departamento_id, variable,
                          metodo, h, r_ef, k_ef, paso_n, t, valor,
                          heroe=None, evento=None):
        """Guarda un solo paso de calculo."""
        self.con.execute(
            """INSERT INTO calculos
               (partida_id, turno, departamento_id, variable, metodo, h,
                r_efectiva, k_efectiva, paso_n, t, valor,
                heroe_activo, evento_activo)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (partida_id, turno, departamento_id, variable, metodo, h,
             r_ef, k_ef, paso_n, t, valor, heroe, evento))
        self.con.commit()

    def registrar_trayectoria(self, partida_id, turno, departamento_id,
                              variable, metodo, h, r_ef, k_ef, ts, ys,
                              heroe=None, evento=None):
        """Guarda TODA la trayectoria (cada paso) que devuelve integrar().
        Inserta en una sola transaccion y devuelve la prediccion final
        (el ultimo valor), que es lo que el juego muestra al jugador."""
        filas = [
            (partida_id, turno, departamento_id, variable, metodo, h,
             r_ef, k_ef, i, t, y, heroe, evento)
            for i, (t, y) in enumerate(zip(ts, ys))
        ]
        self.con.executemany(
            """INSERT INTO calculos
               (partida_id, turno, departamento_id, variable, metodo, h,
                r_efectiva, k_efectiva, paso_n, t, valor,
                heroe_activo, evento_activo)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""", filas)
        self.con.commit()
        return ys[-1]

    # ---------- Batallas ----------
    def registrar_batalla(self, partida_id, turno, atacante, defensor, h_usado,
                          prediccion_euler, prediccion_rk4, metodo_confiado,
                          resultado, tropas_atacante, tropas_defensor):
        cur = self.con.execute(
            """INSERT INTO batallas
               (partida_id, turno, atacante, defensor, h_usado,
                prediccion_euler, prediccion_rk4, metodo_confiado, resultado,
                tropas_atacante, tropas_defensor)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (partida_id, turno, atacante, defensor, h_usado,
             prediccion_euler, prediccion_rk4, metodo_confiado, resultado,
             tropas_atacante, tropas_defensor))
        self.con.commit()
        return cur.lastrowid

    # ---------- Consultas para el analisis ----------
    def obtener_calculos(self, partida_id=None):
        if partida_id is None:
            cur = self.con.execute("SELECT * FROM calculos ORDER BY id")
        else:
            cur = self.con.execute(
                "SELECT * FROM calculos WHERE partida_id = ? ORDER BY id",
                (partida_id,))
        return [dict(f) for f in cur.fetchall()]

    def obtener_batallas(self, partida_id=None):
        if partida_id is None:
            cur = self.con.execute("SELECT * FROM batallas ORDER BY id")
        else:
            cur = self.con.execute(
                "SELECT * FROM batallas WHERE partida_id = ? ORDER BY id",
                (partida_id,))
        return [dict(f) for f in cur.fetchall()]

    def divergencia_por_h(self):
        """Para cada prediccion, compara el valor FINAL de Euler contra el de
        RK4 en las mismas condiciones y devuelve la divergencia |Euler - RK4|.
        Es la consulta clave del analisis: muestra como crece la diferencia
        entre ambos metodos a medida que el paso h aumenta."""
        cur = self.con.execute("""
            WITH finales AS (
                SELECT *,
                       ROW_NUMBER() OVER (
                           PARTITION BY partida_id, turno, departamento_id,
                                        variable, metodo, h
                           ORDER BY t DESC) AS rn
                FROM calculos
            )
            SELECT e.h                      AS h,
                   e.departamento_id        AS departamento,
                   e.variable               AS variable,
                   ROUND(e.valor, 3)        AS pred_euler,
                   ROUND(r.valor, 3)        AS pred_rk4,
                   ROUND(ABS(e.valor - r.valor), 3) AS divergencia
            FROM finales e
            JOIN finales r
              ON  e.partida_id = r.partida_id AND e.turno = r.turno
              AND e.departamento_id = r.departamento_id
              AND e.variable = r.variable AND e.h = r.h
            WHERE e.metodo = 'euler' AND r.metodo = 'rk4'
              AND e.rn = 1 AND r.rn = 1
            ORDER BY e.h, e.departamento_id
        """)
        return [dict(f) for f in cur.fetchall()]

    # ---------- Cierre ----------
    def cerrar(self):
        self.con.close()