# reconstruction.py
# Reconstruye la imagen 2D a partir del sinograma usando FBP
# (Filtered Back-Projection / retroproyeccion filtrada).
# La retroproyeccion simple difumina la imagen; el filtro (p. ej. "ramp")
# compensa ese difuminado realzando las altas frecuencias antes de
# redistribuir cada proyeccion sobre el plano.

# --- Terceros ---
import numpy as np
from skimage.transform import iradon


def reconstruir_fbp(
    sinograma: np.ndarray,
    angulos: np.ndarray,
    filtro: str = "ramp-filter",
) -> np.ndarray:
    # Reconstruye la imagen mediante retroproyeccion filtrada.
    #
    # sinograma : proyecciones (posicion_detector x angulos).
    # angulos   : angulos de cada proyeccion (en grados).
    # filtro    : nombre del filtro de reconstruccion.
    #
    # Retorna un ndarray 2D con la imagen reconstruida.

    # skimage espera nombres como "ramp", "shepp-logan", etc.
    # Se normaliza el sufijo "-filter" para aceptar tambien "ramp-filter".
    filtro_skimage = filtro.replace("-filter", "")

    reconstruccion = iradon(
        sinograma,
        theta=angulos,
        filter_name=filtro_skimage,
        circle=False,
    )

    return reconstruccion
