"""
generar_mapa_demo.py
====================
Genera un MAPA DE DEMOSTRACION (visible + mascara) a partir de
data/departamentos.json, para poder jugar antes de tener un mapa real de
El Salvador dibujado a mano.

Produce dos PNG del mismo tamano:
    assets/mapa/el_salvador.png       -> lo que ve el jugador (regiones, bordes, nombres)
    assets/mapa/el_salvador_mask.png  -> mascara: cada departamento en su color plano unico

La mascara asigna cada pixel al departamento mas cercano a su 'centro'
(regiones de Voronoi), de modo que TODO el mapa es clicable. Cuando tengas un
mapa real, basta con calcar cada departamento usando EXACTAMENTE los mismos
colores 'color_mask' del JSON y el resto del codigo seguira funcionando.

Ejecutar desde la raiz:  python3 generar_mapa_demo.py
"""

import json

import numpy as np
from PIL import Image, ImageDraw

ANCHO, ALTO = 960, 560
RUTA_JSON = "data/departamentos.json"


def hex_a_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def main():
    data = json.load(open(RUTA_JSON, encoding="utf-8"))
    deps = data["departamentos"]
    centros = np.array([d["centro"] for d in deps], dtype=float)      # (n,2) en (x,y)
    colores = np.array([hex_a_rgb(d["color_mask"]) for d in deps], dtype=np.uint8)

    # --- Voronoi: id del departamento mas cercano por pixel ---
    xs = np.arange(ANCHO)
    ys = np.arange(ALTO)
    gx, gy = np.meshgrid(xs, ys)                                       # (ALTO, ANCHO)
    mejor = np.full((ALTO, ANCHO), -1, dtype=int)
    mejor_d = np.full((ALTO, ANCHO), np.inf)
    for i, (cx, cy) in enumerate(centros):
        d2 = (gx - cx) ** 2 + (gy - cy) ** 2
        mas_cerca = d2 < mejor_d
        mejor[mas_cerca] = i
        mejor_d[mas_cerca] = d2[mas_cerca]

    # --- Mascara: color plano por region ---
    mask_rgb = colores[mejor]
    Image.fromarray(mask_rgb, "RGB").save("assets/mapa/el_salvador_mask.png")

    # --- Mapa visible: tinte claro + bordes + nombres ---
    visible = (mask_rgb.astype(float) * 0.45 + 255 * 0.55).astype(np.uint8)
    borde = np.zeros((ALTO, ANCHO), dtype=bool)
    borde[:, :-1] |= mejor[:, :-1] != mejor[:, 1:]
    borde[:-1, :] |= mejor[:-1, :] != mejor[1:, :]
    visible[borde] = (70, 70, 70)

    img = Image.fromarray(visible, "RGB")
    draw = ImageDraw.Draw(img)
    for d in deps:
        cx, cy = d["centro"]
        draw.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], fill=(30, 30, 30))
        draw.text((cx + 7, cy - 6), d["nombre"], fill=(15, 15, 15))
    img.save("assets/mapa/el_salvador.png")

    print(f"Generados (size {ANCHO}x{ALTO}):")
    print("  assets/mapa/el_salvador.png")
    print("  assets/mapa/el_salvador_mask.png")

    # --- Verificacion: el centro de cada depto debe tener su color en la mascara ---
    mask = Image.open("assets/mapa/el_salvador_mask.png").convert("RGB")
    errores = 0
    for d in deps:
        cx, cy = d["centro"]
        if mask.getpixel((cx, cy)) != hex_a_rgb(d["color_mask"]):
            errores += 1
            print(f"  ERROR: {d['id']} no coincide en su centro")
    print(f"Verificacion de centros: {'OK' if errores == 0 else f'{errores} errores'}")


if __name__ == "__main__":
    main()