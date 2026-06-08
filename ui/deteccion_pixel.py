# ui/deteccion_pixel.py
"""
Deteccion pixel-perfect por canal alfa.

Cada sprite de departamento es un PNG de lienzo completo (mismo tamano que el
mapa) que solo tiene pixeles opacos dentro de su propio departamento; el resto
es transparente. En vez de usar la bounding box rectangular del sprite (que se
solapa con las de los vecinos por las formas irregulares), miramos el alfa del
pixel exacto bajo el puntero, relativo a la posicion/escala del sprite.

Las mascaras (canal alfa aplanado a bytes) se cachean una sola vez en __init__;
en cada consulta solo se hace una indexacion O(1), apto para on_mouse_motion.
"""

from PIL import Image


class DetectorPixelPerfect:
    def __init__(self, sprites_departamentos, rutas_png, umbral_alfa=0):
        """
        sprites_departamentos: dict[str, arcade.Sprite]  -> geometria en vivo
        rutas_png:             dict[str, str]            -> ruta del PNG por nombre
        umbral_alfa:           alfa <= umbral se considera transparente (ignora)
        """
        self.sprites = sprites_departamentos
        self.umbral = umbral_alfa

        # Cache: nombre -> (bytes_alfa, ancho, alto). Una sola lectura de disco.
        self.mascaras = {}
        for nombre, ruta in rutas_png.items():
            img = Image.open(ruta).convert("RGBA")
            alfa = img.getchannel("A")           # banda 'A' como imagen L
            ancho, alto = img.size
            self.mascaras[nombre] = (alfa.tobytes(), ancho, alto)

    def _es_opaco(self, nombre, world_x, world_y):
        """True si el pixel del sprite 'nombre' bajo (world_x, world_y) es opaco."""
        datos = self.mascaras.get(nombre)
        if datos is None:
            return False
        alfa, ancho_img, alto_img = datos

        sprite = self.sprites[nombre]
        
        # Usar width/height del sprite (ya redimensionado) en lugar de scale
        ancho_mundo = sprite.width
        alto_mundo = sprite.height
        
        # Escala relativa a imagen original
        escala_x = ancho_mundo / ancho_img
        escala_y = alto_mundo / alto_img

        # Borde superior-izquierdo del sprite en coordenadas de mundo
        izquierda = sprite.center_x - ancho_mundo / 2.0
        arriba_mundo = sprite.center_y + alto_mundo / 2.0

        # Mundo -> píxel de imagen
        col = int((world_x - izquierda) / escala_x)
        fila = int((arriba_mundo - world_y) / escala_y)

        if col < 0 or col >= ancho_img or fila < 0 or fila >= alto_img:
            return False

        return alfa[fila * ancho_img + col] > self.umbral

    def departamento_en(self, x, y):
        """
        Devuelve el nombre del departamento bajo el mouse, o None.
        x, y vienen en coordenadas de arcade (origen abajo-izquierda).
        No hace falta invertir Y aqui: la conversion a pixel ya lo hace.
        """
        alto_ventana = next(iter(self.sprites.values())).center_y * 2  # no usado
        for nombre in self.sprites:
            if self._es_opaco(nombre, x, y):
                return nombre
        return None