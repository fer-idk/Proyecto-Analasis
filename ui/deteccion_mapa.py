# ui/deteccion_mapa.py
from PIL import Image

class DetectorMapa:
    def __init__(self, ruta_mascara):
        # Cargamos la imagen de la máscara en memoria
        self.imagen_mascara = Image.open(ruta_mascara).convert('RGB')
        
        # Mapeamos el color RGB de la máscara al nombre del departamento
        self.colores_departamentos = {
            (250, 190, 212): "san_miguel",  # Reemplaza con tus colores reales
            (67, 99, 216): "santa_ana",
            (255, 225, 25): "san_salvador",
            (70, 153, 144): "la_union",
            (220, 190, 255): "morazan",
            (191, 239, 69): "usulutan",
            (66, 212, 244): "san_vicente",
            (145, 30, 180): "la_paz",
            (230, 25, 75): "la_libertad",
            (240, 50, 230): "chalatenango",
            (245, 130, 49): "cuscatlan",
            (154, 99, 36): "cabañas",
            (128, 0, 0): "sonsonate",
            (60, 180, 75): "ahuachapan"
        }

    def obtener_departamento_por_coordenada(self, x, y_pillow):
        """Devuelve el nombre del departamento o None si hizo clic en el mar/frontera"""
        try:
            color_pixel = self.imagen_mascara.getpixel((x, y_pillow))
            return self.colores_departamentos.get(color_pixel, None)
        except IndexError:
            # Por si el usuario hace clic fuera de los límites de la imagen
            return None
        

    def departamento_en(self, x, y):
            # Acordate que si tu ventana_juego.py ya te invirtió la coordenada 'y', la usás directo.
            # Si no, tenés que restarle la altura de la ventana (height - y).
            try:
                color_pixel = self.imagen_mascara.getpixel((x, int(y)))
                return self.colores_departamentos.get(color_pixel, None)
            except IndexError:
                return None