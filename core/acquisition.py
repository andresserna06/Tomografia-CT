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


def generar_sinograma_3d(
    phantom_3d: np.ndarray, 
    num_angulos: int = 180
) -> tuple[np.ndarray, np.ndarray]:
    # Simula la adquisicion tomografica de un volumen 3D.
    # Itera sobre cada corte transversal (eje Z) aplicando la Transformada 
    # de Radon 2D para construir un "stack" de sinogramas.
    #
    # phantom_3d  : volumen 3D (Z, Y, X) con las atenuaciones mu.
    # num_angulos : cantidad de proyecciones distribuidas en 180 grados.
    #
    # Retorna:
    #   - sinograma_3d: ndarray con forma (Z, detectores, num_angulos)
    #   - angulos: ndarray 1D con los angulos evaluados.

    # Generamos el vector de angulos (de 0 a 180 grados)
    angulos = np.linspace(0.0, 180.0, num_angulos, endpoint=False)
    
    # Extraemos la profundidad del volumen (eje Z)
    size_z = phantom_3d.shape[0]
    
    # Aplicamos Radon a la primera rebanada solo para descubrir 
    # dinamicamente el tamano del array de detectores que devuelve skimage
    sino_prueba = radon(phantom_3d[0], theta=angulos, circle=False)
    size_det = sino_prueba.shape[0]
    
    # Preasignamos la matriz 3D del sinograma para ser eficientes en memoria
    sinograma_3d = np.zeros((size_z, size_det, num_angulos), dtype=float)
    
    # Bucle de adquisicion slice-by-slice
    for z in range(size_z):
        corte_2d = phantom_3d[z, :, :]
        sinograma_3d[z, :, :] = radon(corte_2d, theta=angulos, circle=False)
        
    return sinograma_3d, angulos
