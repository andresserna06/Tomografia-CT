# phantom_3d.py
# Genera la escena 3D ("phantom volumetrico"): un volumen NxNxN donde cada
# voxel representa el coeficiente de absorcion lineal mu(x, y, z) del material.
# Es la "verdad" 3D contra la que luego se compara la reconstruccion volumetrica.
#
# Es el analogo 3D de core/phantom.py: aqui se decide QUE forma tiene la pieza
# (delegando en shapes/generator_3d.py) y DONDE se ubica dentro de la "caja"
# (centrada o en una posicion aleatoria, para el modo oculto).

# --- Terceros ---
import numpy as np

# --- Locales ---
from config import TAMANO_VOLUMEN, MU_FONDO, MU_PIEZA
from shapes import generator_3d


def _mascara_desde_forma(tamano: int, forma: str, centro, rng) -> np.ndarray:
    # Traduce el nombre de forma (value del dropdown) a una llamada concreta del
    # generador 3D, con parametros por defecto escalados al tamano del volumen.
    radio = tamano // 5  # radio base de referencia para las formas

    if forma == "esfera":
        return generator_3d.esfera(tamano, radio, centro)

    if forma == "elipsoide":
        return generator_3d.elipsoide(
            tamano,
            radio_x=tamano // 4,
            radio_y=tamano // 6,
            radio_z=tamano // 8,
            centro=centro,
        )

    if forma == "cilindro":
        return generator_3d.cilindro(
            tamano, radio=tamano // 5, altura=tamano // 2, centro=centro
        )

    if forma == "prisma":
        return generator_3d.prisma(
            tamano, tamano // 3, tamano // 4, tamano // 3, centro=centro
        )

    if forma == "toroide":
        return generator_3d.toroide(
            tamano, radio_mayor=tamano // 4, radio_menor=tamano // 10, centro=centro
        )

    if forma == "aleatoria":
        return generator_3d.forma_aleatoria_3d(tamano, centro=centro, rng=rng)

    raise ValueError(f"Forma 3D no soportada: {forma!r}")


def crear_phantom_3d(
    tamano: int = TAMANO_VOLUMEN,
    forma: str = "esfera",
    mu_fondo: float = MU_FONDO,
    mu_pieza: float = MU_PIEZA,
    posicion_aleatoria: bool = False,
    semilla=None,
) -> np.ndarray:
    # Construye el phantom 3D (volumen de coeficientes de absorcion).
    #
    # tamano             : lado del volumen cubico en voxeles.
    # forma              : tipo de pieza (esfera, elipsoide, cilindro, prisma,
    #                      toroide, aleatoria).
    # mu_fondo / mu_pieza: coeficientes de absorcion del fondo y de la pieza.
    # posicion_aleatoria : si True, la pieza se ubica en un punto al azar de la
    #                      caja (modo oculto); si False, va centrada.
    # semilla            : semilla del generador aleatorio. Fijarla hace que la
    #                      forma y la posicion sean reproducibles -> permite
    #                      cambiar mu sin que la pieza "salte" a otra figura.
    #
    # Retorna un ndarray 3D (float) con el mapa de coeficientes mu(x, y, z),
    # indexado como volumen[z, y, x].

    # Un unico generador aleatorio gobierna posicion y forma: asi, a igual
    # semilla, se obtiene exactamente la misma pieza.
    rng = np.random.default_rng(semilla)

    # Posicion del centro de la pieza dentro de la caja.
    if posicion_aleatoria:
        # Margen para que la pieza no quede pegada a las paredes de la caja.
        margen = tamano // 4
        cx = int(rng.integers(margen, tamano - margen))
        cy = int(rng.integers(margen, tamano - margen))
        cz = int(rng.integers(margen, tamano - margen))
        centro = (cx, cy, cz)
    else:
        c = tamano / 2.0
        centro = (c, c, c)

    # Mascara booleana 3D de la pieza segun la forma pedida.
    mascara = _mascara_desde_forma(tamano, forma, centro, rng)

    # Volumen de fondo + se "estampa" la pieza con su coeficiente de absorcion.
    volumen = np.full((tamano, tamano, tamano), float(mu_fondo), dtype=float)
    volumen[mascara] = float(mu_pieza)
    return volumen
