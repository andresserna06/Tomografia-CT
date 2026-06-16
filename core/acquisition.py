# acquisition.py
# Simula la adquisicion tomografica: girar la fuente/detector alrededor de la
# pieza y, en cada angulo, medir las proyecciones del haz.
# Matematicamente esto es la Transformada de Radon del phantom.
# El conjunto de todas las proyecciones apiladas es el SINOGRAMA.

# --- Terceros ---
import numpy as np
from skimage.transform import radon

# --- Locales ---
from config import ANGULOS_DEFAULT


def generar_sinograma(
    phantom: np.ndarray,
    num_angulos: int = ANGULOS_DEFAULT,
) -> tuple[np.ndarray, np.ndarray]:
    # Genera el sinograma de un phantom 2D.
    #
    # phantom     : mapa de coeficientes de absorcion mu(x, y).
    # num_angulos : cuantas proyecciones tomar entre 0 y 180 grados.
    #
    # Retorna (sinograma, angulos):
    #   sinograma -> ndarray 2D (posicion_detector x angulos)
    #   angulos   -> ndarray 1D con los angulos usados (en grados)

    # Angulos equiespaciados en [0, 180). Se excluye 180 porque la
    # proyeccion a 180 grados es redundante con la de 0 grados.
    angulos = np.linspace(0.0, 180.0, num_angulos, endpoint=False)

    # radon() integra el phantom a lo largo de lineas paralelas para cada
    # angulo. circle=False asume que el objeto puede ocupar toda la imagen.
    sinograma = radon(phantom, theta=angulos, circle=False)

    return sinograma, angulos


def proyeccion_en_angulo(imagen: np.ndarray, angulo_grados: float) -> np.ndarray:
    # La "sombra" que produce UN solo angulo: el perfil 1D de las integrales de
    # linea (integral de mu dl) a lo largo de los rayos paralelos a ese angulo.
    # Es, literalmente, una sola columna del sinograma. Asi se ve "lo que mide el
    # detector" desde una direccion concreta.
    #
    # imagen        : corte 2D (mapa de mu).
    # angulo_grados : direccion del haz, en grados.
    #
    # Retorna un ndarray 1D (perfil de la proyeccion en ese angulo).
    return radon(imagen, theta=[float(angulo_grados)], circle=False)[:, 0]
