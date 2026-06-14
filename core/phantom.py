# phantom_3d.py
# Genera el volumen 3D ("phantom"): una matriz NxNxN donde cada voxel
# representa el coeficiente de atenuacion lineal mu(x, y, z).
#
# Aqui se decide QUE forma 3D tiene la pieza y DONDE se ubica 
# (centrada o en una posicion aleatoria espacial).

# --- Terceros ---
import numpy as np

# --- Locales ---
# Nota: Podrías querer definir un TAMANO_VOLUMEN (ej. 128) en config.py
# distinto al TAMANO_IMAGEN (256) para cuidar la memoria y el rendimiento.
from config import MU_FONDO, MU_PIEZA
from shapes import generator


def _mascara_desde_forma_3d(tamano: int, forma: str, centro, rng) -> np.ndarray:
    # Traduce el nombre de forma 3D a una llamada concreta del generador.
    radio = tamano // 5  # radio base de referencia

    if forma == "esfera":
        return generator.esfera(tamano, radio, centro)

    if forma == "elipsoide":
        return generator.elipsoide(
            tamano,
            radio_x=tamano // 4,
            radio_y=tamano // 7,
            radio_z=tamano // 5,
            centro=centro,
        )

    if forma == "masa_irregular_3d":
        return generator.masa_irregular_3d(
            tamano,
            radio_base=tamano // 4,
            centro=centro,
            rng=rng,
        )

    if forma == "cilindro":
        return generator.cilindro(
            tamano,
            radio=tamano // 4,
            altura=tamano // 2,
            centro=centro,
        )

    if forma == "L_3d":
        return generator.forma_L_3d(
            tamano, 
            ancho=tamano // 3, 
            alto=tamano // 3, 
            prof=tamano // 4, 
            grosor=tamano // 9, 
            centro=centro
        )

    if forma == "aleatoria":
        return generator.forma_aleatoria_3d(tamano, centro=centro, rng=rng)

    raise ValueError(f"Forma 3D no soportada: {forma!r}")


def crear_phantom_3d(
    tamano: int = 128,  # Por defecto 128 para mantener UI responsiva
    forma: str = "esfera",
    mu_fondo: float = MU_FONDO,
    mu_pieza: float = MU_PIEZA,
    posicion_aleatoria: bool = False,
    semilla=None,
) -> np.ndarray:
    # Construye el phantom volumetrico 3D.
    #
    # tamano             : lado del cubo (volumen) en voxeles (NxNxN).
    # forma              : tipo de pieza 3D (esfera, elipsoide, cilindro,
    #                      masa_irregular_3d, L_3d, aleatoria).
    # mu_fondo / mu_pieza: coeficientes de atenuacion del fondo y la pieza.
    # posicion_aleatoria : si True, la pieza se ubica en un punto espacial al azar.
    # semilla            : semilla del generador aleatorio para reproducibilidad.
    #
    # Retorna un ndarray 3D (float) con el mapa de coeficientes mu(x, y, z).

    rng = np.random.default_rng(semilla)

    # Posicion del centro de la pieza en 3D (x, y, z).
    if posicion_aleatoria:
        margen = tamano // 4
        cx = int(rng.integers(margen, tamano - margen))
        cy = int(rng.integers(margen, tamano - margen))
        cz = int(rng.integers(margen, tamano - margen))
        centro = (cx, cy, cz)
    else:
        centro = (tamano / 2.0, tamano / 2.0, tamano / 2.0)

    # Obtenemos la mascara booleana 3D de la pieza pedida.
    mascara = _mascara_desde_forma_3d(tamano, forma, centro, rng)

    # Lienzo volumetrico de fondo + se "estampa" la pieza con su coeficiente.
    phantom = np.full((tamano, tamano, tamano), float(mu_fondo), dtype=float)
    phantom[mascara] = float(mu_pieza)
    
    return phantom