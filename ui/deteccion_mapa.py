"""
deteccion_mapa.py
=================
Detecta sobre que departamento hizo clic el jugador, leyendo el color del
pixel correspondiente en la imagen-mascara. Es la unica fuente de verdad para
el mapeo color -> departamento (evita duplicar la tabla de colores).

DETALLE CRITICO de coordenadas:
    Arcade tiene el origen (0,0) abajo-izquierda, con y hacia ARRIBA.
    Las imagenes (PIL) tienen el origen arriba-izquierda, con y hacia ABAJO.
    Por eso hay que VOLTEAR la y al convertir un clic de Arcade a pixel de la
    mascara:  pixel_y = alto - 1 - clic_y
Si se omite este volteo, los clics seleccionan el departamento equivocado
(reflejado verticalmente). Es el error mas comun en este tipo de deteccion.

No depende de Arcade: usa solo PIL, por lo que se puede probar sin pantalla.
"""

from PIL import Image


class DetectorMapa:
    def __init__(self, ruta_mascara, color_a_id):
        """
        ruta_mascara : PNG de la mascara (colores planos por departamento)
        color_a_id   : dict {(r,g,b): id_departamento}
        """
        self.mascara = Image.open(ruta_mascara).convert("RGB")
        self.ancho, self.alto = self.mascara.size
        self.color_a_id = color_a_id

    def departamento_en(self, clic_x, clic_y):
        """Devuelve el id del departamento bajo (clic_x, clic_y) en coordenadas
        de Arcade, o None si el clic cae fuera del mapa o en color desconocido."""
        ix = int(clic_x)
        iy = int(self.alto - 1 - clic_y)          # volteo de Y (ver nota arriba)
        if not (0 <= ix < self.ancho and 0 <= iy < self.alto):
            return None
        rgb = self.mascara.getpixel((ix, iy))
        return self.color_a_id.get(rgb)

    @classmethod
    def desde_territorios(cls, ruta_mascara, territorios):
        """Construye el detector tomando los color_mask de los Territorio."""
        from ui.colores import hex_a_rgb
        color_a_id = {hex_a_rgb(t.color_mask): t.id for t in territorios.values()}
        return cls(ruta_mascara, color_a_id)