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
    tamano_salida: int | None = None,
) -> np.ndarray:
    # Reconstruye la imagen mediante retroproyeccion filtrada.
    #
    # sinograma     : proyecciones (posicion_detector x angulos).
    # angulos       : angulos de cada proyeccion (en grados).
    # filtro        : nombre del filtro de reconstruccion.
    # tamano_salida : lado (en px) de la imagen reconstruida. Si es None, iradon
    #                 lo deduce del sinograma. Forzarlo es util en 3D, donde cada
    #                 corte reconstruido debe conservar el lado N exacto del
    #                 volumen para poder apilarse sin desajustes de tamano.
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
        output_size=tamano_salida,
    )

    return reconstruccion
