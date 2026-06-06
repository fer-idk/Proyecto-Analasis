"""
main.py
=======
Punto de entrada del juego. Ejecutar desde la raiz del proyecto:

    python3 main.py

Requisitos: Python 3.12 y las dependencias de requirements.txt
(arcade, pillow, numpy). Antes de la primera ejecucion, genera el mapa de
demostracion con:  python3 generar_mapa_demo.py
"""

from ui.ventana_juego import main

if __name__ == "__main__":
    main()