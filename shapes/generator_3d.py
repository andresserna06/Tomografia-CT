# generator_3d.py
# Generadores de formas 3D. Cada funcion devuelve una MASCARA BOOLEANA NxNxN:
# True en los voxeles que pertenecen a la pieza, False en el fondo.
# Esa mascara la usa core/phantom_3d.py para "estampar" el coeficiente de
# absorcion de la pieza sobre el volumen de fondo.
#
# Convencion de ejes (importante): el volumen se indexa como volumen[z, y, x].
#   - eje 0 = z -> profundidad / cortes axiales (cada volumen[z] es una imagen 2D)
#   - eje 1 = y -> fila
#   - eje 2 = x -> columna
# Asi, "rebanar" en el eje 0 entrega directamente cortes transversales listos
# para la transformada de Radon, igual que en el pipeline 2D.

# --- Terceros ---
import numpy as np


# ---------------------------------------------------------------------------
# Utilidades internas
# ---------------------------------------------------------------------------

def _centro_por_defecto(tamano, centro):
    # El centro se expresa como (cx, cy, cz) = (columna, fila, profundidad).
    # Si no se especifica, se usa el centro geometrico del volumen.
    if centro is None:
        c = tamano / 2.0
        return c, c, c
    return float(centro[0]), float(centro[1]), float(centro[2])


def _malla(tamano):
    # Devuelve las tres mallas de coordenadas con ogrid (broadcasting, sin gastar
    # memoria en arreglos NxNxN completos hasta que se hace la comparacion final).
    # zz varia en el eje 0, yy en el eje 1, xx en el eje 2.
    zz, yy, xx = np.ogrid[:tamano, :tamano, :tamano]
    return zz, yy, xx


# ---------------------------------------------------------------------------
# Formas 3D
# ---------------------------------------------------------------------------

def esfera(tamano, radio, centro=None):
    # Esfera de radio dado: todos los voxeles cuya distancia al centro <= radio.
    cx, cy, cz = _centro_por_defecto(tamano, centro)
    zz, yy, xx = _malla(tamano)
    return (xx - cx) ** 2 + (yy - cy) ** 2 + (zz - cz) ** 2 <= radio ** 2


def elipsoide(tamano, radio_x, radio_y, radio_z, centro=None):
    # Elipsoide con semiejes distintos en cada direccion (esfera "estirada").
    # Ecuacion canonica: (x/a)^2 + (y/b)^2 + (z/c)^2 <= 1.
    cx, cy, cz = _centro_por_defecto(tamano, centro)
    zz, yy, xx = _malla(tamano)
    return (
        ((xx - cx) / radio_x) ** 2
        + ((yy - cy) / radio_y) ** 2
        + ((zz - cz) / radio_z) ** 2
        <= 1.0
    )


def cilindro(tamano, radio, altura, centro=None):
    # Cilindro con su eje a lo largo de Z: un disco de radio 'radio' en el plano
    # XY, extruido una altura dada. Es la condicion radial (disco) combinada con
    # un limite en Z.
    cx, cy, cz = _centro_por_defecto(tamano, centro)
    zz, yy, xx = _malla(tamano)
    disco = (xx - cx) ** 2 + (yy - cy) ** 2 <= radio ** 2
    tapa = np.abs(zz - cz) <= altura / 2.0
    return disco & tapa


def prisma(tamano, lado_x, lado_y, lado_z, centro=None):
    # Caja rectangular (prisma) centrada. Si los tres lados son iguales es un cubo.
    cx, cy, cz = _centro_por_defecto(tamano, centro)
    zz, yy, xx = _malla(tamano)
    return (
        (np.abs(xx - cx) <= lado_x / 2.0)
        & (np.abs(yy - cy) <= lado_y / 2.0)
        & (np.abs(zz - cz) <= lado_z / 2.0)
    )


def toroide(tamano, radio_mayor, radio_menor, centro=None):
    # Toroide (dona) con su eje de revolucion en Z.
    # radio_mayor: distancia del centro del tubo al eje Z.
    # radio_menor: radio del tubo.
    # La condicion mide la distancia de cada voxel a la circunferencia central
    # del tubo y la compara con el radio del tubo.
    cx, cy, cz = _centro_por_defecto(tamano, centro)
    zz, yy, xx = _malla(tamano)
    dist_radial = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    return (dist_radial - radio_mayor) ** 2 + (zz - cz) ** 2 <= radio_menor ** 2


def forma_aleatoria_3d(tamano, centro=None, rng=None):
    # Devuelve una forma 3D impredecible: elige al azar un tipo y sus parametros.
    # Con un rng sembrado el resultado es reproducible; sin semilla, cambia en
    # cada llamada.
    if rng is None:
        rng = np.random.default_rng()

    cx, cy, cz = _centro_por_defecto(tamano, centro)
    centro = (cx, cy, cz)

    tipo = rng.choice(["esfera", "elipsoide", "cilindro", "prisma", "toroide"])

    if tipo == "esfera":
        return esfera(tamano, int(rng.integers(tamano // 8, tamano // 4)), centro)
    if tipo == "elipsoide":
        return elipsoide(
            tamano,
            radio_x=int(rng.integers(tamano // 6, tamano // 3)),
            radio_y=int(rng.integers(tamano // 8, tamano // 4)),
            radio_z=int(rng.integers(tamano // 10, tamano // 5)),
            centro=centro,
        )
    if tipo == "cilindro":
        return cilindro(
            tamano,
            radio=int(rng.integers(tamano // 8, tamano // 4)),
            altura=int(rng.integers(tamano // 3, tamano // 2)),
            centro=centro,
        )
    if tipo == "prisma":
        lado = int(rng.integers(tamano // 5, tamano // 3))
        return prisma(tamano, lado, lado, lado, centro)
    return toroide(
        tamano,
        radio_mayor=int(rng.integers(tamano // 5, tamano // 4)),
        radio_menor=int(rng.integers(tamano // 12, tamano // 8)),
        centro=centro,
    )
