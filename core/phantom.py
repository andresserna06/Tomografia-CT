# phantom.py
# Genera la escena 2D ("phantom"): una matriz donde cada pixel representa
# el coeficiente de absorcion lineal mu(x, y) del material en ese punto.
# Es la "verdad" contra la que luego se compara la reconstruccion.
#
# Aqui se decide QUE forma tiene la pieza (delegando en shapes/generator.py)
# y DONDE se ubica (centrada o en posicion aleatoria).

# --- Terceros ---
import numpy as np

# --- Locales ---
from config import TAMANO_IMAGEN, MU_FONDO, MU_PIEZA
from shapes import generator


def _mascara_desde_forma(tamano: int, forma: str, centro, rng) -> np.ndarray:
    # Traduce el nombre de forma (el value del dropdown) a una llamada concreta
    # del generador, con parametros por defecto escalados al tamano de imagen.
    radio = tamano // 5  # radio base de referencia para las formas regulares

    if forma == "circulo":
        return generator.circulo(tamano, radio, centro)

    if forma == "elipse":
        return generator.elipse(
            tamano,
            radio_x=tamano // 4,
            radio_y=tamano // 7,
            angulo_rotacion=30.0,
            centro=centro,
        )

    if forma == "poligono_irregular":
        return generator.poligono_irregular(
            tamano,
            num_vertices=12,
            radio_min=tamano // 8,
            radio_max=tamano // 4,
            centro=centro,
            rng=rng,
        )

    if forma == "estrella":
        return generator.estrella(
            tamano,
            num_puntas=5,
            radio_ext=tamano // 4,
            radio_int=tamano // 9,
            centro=centro,
        )

    if forma == "L":
        return generator.forma_L(tamano, tamano // 3, tamano // 3, tamano // 9, centro)

    if forma == "T":
        return generator.forma_T(tamano, tamano // 3, tamano // 3, tamano // 9, centro)

    if forma == "aleatoria":
        return generator.forma_aleatoria(tamano, centro=centro, rng=rng)

    raise ValueError(f"Forma no soportada: {forma!r}")


def crear_phantom(
    tamano: int = TAMANO_IMAGEN,
    forma: str = "circulo",
    mu_fondo: float = MU_FONDO,
    mu_pieza: float = MU_PIEZA,
    posicion_aleatoria: bool = False,
    semilla=None,
) -> np.ndarray:
    # Construye el phantom 2D.
    #
    # tamano             : lado de la imagen cuadrada en pixeles.
    # forma              : tipo de pieza (circulo, elipse, estrella, L, T,
    #                      poligono_irregular, aleatoria).
    # mu_fondo / mu_pieza: coeficientes de absorcion del fondo y de la pieza.
    # posicion_aleatoria : si True, la pieza se ubica en un punto al azar
    #                      (util para el "modo oculto"); si False, va centrada.
    # semilla            : semilla del generador aleatorio. Fijarla hace que la
    #                      forma y la posicion sean reproducibles -> permite
    #                      cambiar mu sin que la pieza "salte" a otra figura.
    #
    # Retorna un ndarray 2D (float) con el mapa de coeficientes mu(x, y).

    # Un unico generador aleatorio gobierna posicion y forma: asi, a igual
    # semilla, se obtiene exactamente la misma pieza.
    rng = np.random.default_rng(semilla)

    # Posicion del centro de la pieza.
    if posicion_aleatoria:
        # Se deja un margen para que la pieza no quede pegada al borde.
        margen = tamano // 4
        cx = int(rng.integers(margen, tamano - margen))
        cy = int(rng.integers(margen, tamano - margen))
        centro = (cx, cy)
    else:
        centro = (tamano / 2.0, tamano / 2.0)

    # Mascara booleana de la pieza segun la forma pedida.
    mascara = _mascara_desde_forma(tamano, forma, centro, rng)

    # Lienzo de fondo + se "estampa" la pieza con su coeficiente de absorcion.
    phantom = np.full((tamano, tamano), float(mu_fondo), dtype=float)
    phantom[mascara] = float(mu_pieza)
    return phantom
