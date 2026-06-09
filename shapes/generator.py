# generator.py
# Generadores de formas 2D. Cada funcion devuelve una MASCARA BOOLEANA NxN:
# True en los pixeles que pertenecen a la pieza, False en el fondo.
# Esa mascara la usa core/phantom.py para "estampar" el coeficiente de
# absorcion de la pieza sobre el fondo.

# --- Terceros ---
import numpy as np
from scipy.ndimage import gaussian_filter
from skimage.draw import polygon


# ---------------------------------------------------------------------------
# Utilidades internas
# ---------------------------------------------------------------------------

def _centro_por_defecto(tamano, centro):
    # Si no se especifica centro, se usa el centro geometrico de la imagen.
    # El centro se expresa como (cx, cy) = (columna, fila).
    if centro is None:
        return tamano / 2.0, tamano / 2.0
    return float(centro[0]), float(centro[1])


def _pintar_rectangulo(mascara, fila0, fila1, col0, col1):
    # Marca como True un rectangulo, recortando los indices al rango valido.
    # Evita los indices negativos de numpy (que "envuelven" por el otro lado).
    alto, ancho = mascara.shape
    fila0 = max(0, int(fila0))
    col0 = max(0, int(col0))
    fila1 = min(alto, int(fila1))
    col1 = min(ancho, int(col1))
    if fila1 > fila0 and col1 > col0:
        mascara[fila0:fila1, col0:col1] = True


def _mascara_desde_poligono(tamano, xs, ys):
    # Rasteriza un poligono (coordenadas de sus vertices) a una mascara booleana.
    # skimage.draw.polygon trabaja en (fila, columna) = (y, x).
    rr, cc = polygon(ys, xs, shape=(tamano, tamano))
    mascara = np.zeros((tamano, tamano), dtype=bool)
    mascara[rr, cc] = True
    return mascara


# ---------------------------------------------------------------------------
# Formas regulares
# ---------------------------------------------------------------------------

def circulo(tamano, radio, centro=None):
    # Circulo de radio dado centrado en 'centro'.
    cx, cy = _centro_por_defecto(tamano, centro)
    yy, xx = np.ogrid[:tamano, :tamano]
    return (xx - cx) ** 2 + (yy - cy) ** 2 <= radio ** 2


def elipse(tamano, radio_x, radio_y, angulo_rotacion=0.0, centro=None):
    # Elipse con semiejes radio_x / radio_y, rotada 'angulo_rotacion' grados.
    cx, cy = _centro_por_defecto(tamano, centro)
    yy, xx = np.ogrid[:tamano, :tamano]

    # Se trasladan las coordenadas al centro de la elipse...
    x = xx - cx
    y = yy - cy

    # ...y se rotan al sistema propio de la elipse (rotacion inversa del angulo).
    theta = np.deg2rad(angulo_rotacion)
    x_rot = x * np.cos(theta) + y * np.sin(theta)
    y_rot = -x * np.sin(theta) + y * np.cos(theta)

    # Ecuacion canonica de la elipse: (x/a)^2 + (y/b)^2 <= 1.
    return (x_rot / radio_x) ** 2 + (y_rot / radio_y) ** 2 <= 1.0


def estrella(tamano, num_puntas, radio_ext, radio_int, centro=None):
    # Estrella de 'num_puntas' alternando radio exterior (puntas) e interior
    # (valles). Se construye como un poligono de 2*num_puntas vertices.
    cx, cy = _centro_por_defecto(tamano, centro)

    angulos = np.linspace(0.0, 2.0 * np.pi, 2 * num_puntas, endpoint=False)
    radios = np.empty(2 * num_puntas)
    radios[0::2] = radio_ext  # vertices pares -> puntas
    radios[1::2] = radio_int  # vertices impares -> valles

    xs = cx + radios * np.cos(angulos)
    ys = cy + radios * np.sin(angulos)
    return _mascara_desde_poligono(tamano, xs, ys)


def forma_L(tamano, ancho, alto, grosor, centro=None):
    # Pieza con forma de "L": una barra vertical y una base horizontal.
    cx, cy = _centro_por_defecto(tamano, centro)
    x0 = cx - ancho / 2.0  # esquina superior-izquierda del bounding box
    y0 = cy - alto / 2.0

    mascara = np.zeros((tamano, tamano), dtype=bool)
    _pintar_rectangulo(mascara, y0, y0 + alto, x0, x0 + grosor)          # barra vertical
    _pintar_rectangulo(mascara, y0 + alto - grosor, y0 + alto, x0, x0 + ancho)  # base
    return mascara


def forma_T(tamano, ancho, alto, grosor, centro=None):
    # Pieza con forma de "T": una barra horizontal arriba y una vertical central.
    cx, cy = _centro_por_defecto(tamano, centro)
    x0 = cx - ancho / 2.0
    y0 = cy - alto / 2.0

    mascara = np.zeros((tamano, tamano), dtype=bool)
    _pintar_rectangulo(mascara, y0, y0 + grosor, x0, x0 + ancho)                 # barra superior
    _pintar_rectangulo(mascara, y0, y0 + alto, cx - grosor / 2.0, cx + grosor / 2.0)  # barra vertical
    return mascara


# ---------------------------------------------------------------------------
# Formas irregulares
# ---------------------------------------------------------------------------

def poligono_irregular(tamano, num_vertices, radio_min, radio_max,
                       centro=None, rng=None, sigma=None):
    # Poligono de aspecto organico e impredecible.
    #
    # Estrategia: se generan vertices a angulos aleatorios con radios aleatorios
    # entre radio_min y radio_max (esto ya da una silueta muy irregular). Luego
    # se rasteriza y se SUAVIZAN los bordes con un filtro gaussiano, de modo que
    # las esquinas duras se redondean y la pieza parece una mancha natural, no
    # un poligono regular con ruido minimo.
    cx, cy = _centro_por_defecto(tamano, centro)
    if rng is None:
        rng = np.random.default_rng()

    # Angulos ordenados para que el poligono sea "estrellado" (radial) y no se
    # auto-intersecte; radios independientes por vertice -> mucha irregularidad.
    angulos = np.sort(rng.uniform(0.0, 2.0 * np.pi, num_vertices))
    radios = rng.uniform(radio_min, radio_max, num_vertices)

    xs = cx + radios * np.cos(angulos)
    ys = cy + radios * np.sin(angulos)

    # Mascara dura del poligono (0/1) para poder filtrarla como imagen.
    relleno = _mascara_desde_poligono(tamano, xs, ys).astype(float)

    # Suavizado gaussiano de los bordes. sigma ~ 2% del tamano redondea las
    # esquinas sin disolver la pieza.
    if sigma is None:
        sigma = tamano * 0.02
    suavizada = gaussian_filter(relleno, sigma=sigma)

    # Se re-binariza en el nivel 0.5 (borde "medio" del difuminado).
    return suavizada >= 0.5


def forma_aleatoria(tamano, centro=None, rng=None):
    # Devuelve una forma impredecible: elige al azar un tipo y parametros.
    # Con un rng sembrado el resultado es reproducible; sin semilla, cambia
    # en cada llamada.
    if rng is None:
        rng = np.random.default_rng()

    cx, cy = _centro_por_defecto(tamano, centro)
    centro = (cx, cy)

    tipo = rng.choice(
        ["circulo", "elipse", "poligono_irregular", "estrella", "L", "T"]
    )

    if tipo == "circulo":
        return circulo(tamano, int(rng.integers(tamano // 8, tamano // 4)), centro)
    if tipo == "elipse":
        return elipse(
            tamano,
            radio_x=int(rng.integers(tamano // 6, tamano // 3)),
            radio_y=int(rng.integers(tamano // 10, tamano // 5)),
            angulo_rotacion=float(rng.uniform(0.0, 180.0)),
            centro=centro,
        )
    if tipo == "poligono_irregular":
        return poligono_irregular(
            tamano,
            num_vertices=int(rng.integers(7, 15)),
            radio_min=tamano // 8,
            radio_max=tamano // 4,
            centro=centro,
            rng=rng,
        )
    if tipo == "estrella":
        return estrella(
            tamano,
            num_puntas=int(rng.integers(5, 9)),
            radio_ext=tamano // 4,
            radio_int=tamano // 9,
            centro=centro,
        )
    if tipo == "L":
        return forma_L(tamano, tamano // 3, tamano // 3, tamano // 9, centro)
    return forma_T(tamano, tamano // 3, tamano // 3, tamano // 9, centro)
