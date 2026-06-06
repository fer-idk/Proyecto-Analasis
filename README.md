# Risk Matematico - El Salvador

Juego de estrategia territorial sobre el mapa de El Salvador (14 departamentos)
para la asignatura de Analisis Numerico. Los metodos de **Euler** y
**Runge-Kutta 4** operan internamente: gobiernan el crecimiento de tropas y
recursos (ecuacion logistica) y sus predicciones se muestran antes de cada
batalla. El jugador ajusta el paso `h` y observa como Euler se vuelve inestable
mientras RK4 se mantiene preciso. Cada calculo se guarda en SQLite.

## Requisitos e instalacion

- Python 3.12
- `pip install -r requirements.txt`  (arcade, pillow, numpy, matplotlib, pytest)

Los metodos numericos estan implementados a mano en `metodos/` (sin scipy).

## Como ejecutar

Siempre desde la raiz del proyecto:

    python3 generar_mapa_demo.py     # genera el mapa de demostracion (1a vez)
    python3 main.py                  # abre el juego

Pruebas:

    pytest -v

Scripts de demostracion (generan bases de datos de prueba en partidas/):

    python3 demo_core.py    # heroes y eventos modificando r y K
    python3 demo_juego.py   # partida completa integrada
    python3 seed_demo.py    # poblar la BD con varias partidas

## Estructura

    main.py                  Punto de entrada
    generar_mapa_demo.py     Genera el mapa visible + mascara desde el JSON
    requirements.txt

    data/
      departamentos.json     Mapa base: 14 deptos, vecinos, parametros r/K

    metodos/                 Nucleo numerico (sin librerias que resuelvan la EDO)
      modelos.py             Ecuacion logistica y su solucion exacta
      euler.py               Metodo de Euler (orden 1)
      rk4.py                 Runge-Kutta 4 (orden 4)

    core/                    Logica del juego
      territorio.py          Modelo de depto; pliega modificadores -> r,K efectivos
      comandantes.py         Heroes (Cipitio, Siguanaba, Vendedor de Minutas)
      eventos.py             Eventos (huracan, marcha UES, erupcion, trafico)
      gestor_eventos.py      Dispara eventos aleatorios cada turno
      economia.py            Extraccion de recursos y colapso (rendimiento r*K/4)
      estabilidad.py         Zonas de estabilidad (Verde/Amarilla/Roja/Caos)
      batalla.py             Resolucion de combates
      turnos.py              Motor de fases; el refuerzo aplica el metodo activo
      jugador.py, game_state.py, prediccion.py, cargador.py

    persistencia/            SQLite
      db.py                  Conexion y esquema (partidas, calculos, batallas)
      repositorio.py         API para guardar y consultar

    ui/                      Interfaz (Arcade 3.x)
      colores.py             Paleta y dimensiones
      deteccion_mapa.py      Clic -> departamento por color de mascara
      vista_mapa.py          Dibujo del mapa y fichas
      hud.py                 Panel: slider de h, selector metodo, botones
      vista_batalla.py       Grafica Euler vs RK4 antes de batalla
      ventana_juego.py       Ventana principal y flujo de juego

    tests/                   pytest (metodos y core)
    partidas/                Bases de datos generadas (.db)
    assets/mapa/             el_salvador.png y el_salvador_mask.png

## El metodo numerico en el juego

La ecuacion central es la logistica `dN/dt = r*N*(1 - N/K)`, donde `N` son tropas
o cantidad de recurso, `r` la tasa de crecimiento y `K` la capacidad maxima.
La misma ecuacion gobierna tropas y recursos.

- **Continuo vs discreto.** Heroes y eventos que cambian `r` o `K` entran a la
  EDO (Siguanaba, Vendedor de Minutas, Huracan). Los que son reglas (Marcha en
  la UES, Erupcion, Cipitio, Trafico) no tocan las ecuaciones.
- **Estabilidad.** Un turno = un paso de tamano `h`. Cuando `h*r > 2`, Euler
  sobrepasa `K` y oscila; RK4 sigue estable. Las zonas de estabilidad penalizan
  confiar en Euler con `h` grande en batalla.
- **Economia.** La extraccion sigue la logistica; cosechar por encima del
  rendimiento sostenible `r*K/4` colapsa el recurso.

## Reemplazar el mapa de demostracion

El mapa generado es esquematico. Para usar un mapa real de El Salvador, crea dos
PNG del mismo tamano (definido en `ui/colores.py`): el visible y una mascara
donde cada departamento tenga EXACTAMENTE el `color_mask` de `departamentos.json`.
No hace falta cambiar codigo.