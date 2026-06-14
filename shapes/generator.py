# generator_3d.py
# Generadores de formas 3D. Cada funcion devuelve una MASCARA BOOLEANA NxNxN:
# True en los voxeles que pertenecen a la pieza, False en el fondo.
# Esa mascara la usa core/phantom_3d.py para "estampar" el coeficiente de
# atenuacion de la pieza sobre el fondo volumetrico.

import numpy as np
from scipy.ndimage import gaussian_filter

# ---------------------------------------------------------------------------
# Utilidades internas 3D
# ---------------------------------------------------------------------------

def _centro_por_defecto_3d(tamano, centro):
    # Si no se especifica centro, se usa el centro geometrico del volumen.
    # El centro se expresa como (cx, cy, cz) = (x, y, z).
    if centro is None:
        return tamano / 2.0, tamano / 2.0, tamano / 2.0
    return float(centro[0]), float(centro[1]), float(centro[2])

def _pintar_bloque_3d(mascara, z0, z1, y0, y1, x0, x1):
    # Marca como True un paralelepipedo (caja 3D).
    prof, alto, ancho = mascara.shape
    z0, y0, x0 = max(0, int(z0)), max(0, int(y0)), max(0, int(x0))
    z1, y1, x1 = min(prof, int(z1)), min(alto, int(y1)), min(ancho, int(x1))
    
    if z1 > z0 and y1 > y0 and x1 > x0:
        mascara[z0:z1, y0:y1, x0:x1] = True

# ---------------------------------------------------------------------------
# Formas regulares 3D
# ---------------------------------------------------------------------------

def esfera(tamano, radio, centro=None):
    # Esfera de radio dado. Equivalente 3D del circulo.
    cx, cy, cz = _centro_por_defecto_3d(tamano, centro)
    zz, yy, xx = np.ogrid[:tamano, :tamano, :tamano]
    
    # Ecuacion de la esfera
    return (xx - cx)**2 + (yy - cy)**2 + (zz - cz)**2 <= radio**2

def elipsoide(tamano, radio_x, radio_y, radio_z, centro=None):
    # Elipsoide con tres semiejes (sin rotacion para simplificar computo).
    cx, cy, cz = _centro_por_defecto_3d(tamano, centro)
    zz, yy, xx = np.ogrid[:tamano, :tamano, :tamano]

    return ((xx - cx) / radio_x)**2 + ((yy - cy) / radio_y)**2 + ((zz - cz) / radio_z)**2 <= 1.0

def cilindro(tamano, radio, altura, centro=None):
    # Cilindro alineado con el eje Z.
    cx, cy, cz = _centro_por_defecto_3d(tamano, centro)
    zz, yy, xx = np.ogrid[:tamano, :tamano, :tamano]
    
    # Mascara del circulo en 2D (plano XY)
    mascara_xy = (xx - cx)**2 + (yy - cy)**2 <= radio**2
    # Mascara de la altura en el eje Z
    mascara_z = (zz >= cz - altura / 2.0) & (zz <= cz + altura / 2.0)
    
    # Interseccion de ambas mascaras
    return mascara_xy & mascara_z

def forma_L_3d(tamano, ancho, alto, prof, grosor, centro=None):
    # Equivalente 3D de la forma L (como dos bloques interceptados).
    cx, cy, cz = _centro_por_defecto_3d(tamano, centro)
    x0 = cx - ancho / 2.0
    y0 = cy - alto / 2.0
    z0 = cz - prof / 2.0
    
    mascara = np.zeros((tamano, tamano, tamano), dtype=bool)
    # Bloque vertical
    _pintar_bloque_3d(mascara, z0, z0 + prof, y0, y0 + alto, x0, x0 + grosor)
    # Bloque horizontal (base)
    _pintar_bloque_3d(mascara, z0, z0 + prof, y0 + alto - grosor, y0 + alto, x0, x0 + ancho)
    return mascara

# ---------------------------------------------------------------------------
# Formas irregulares 3D
# ---------------------------------------------------------------------------

def masa_irregular_3d(tamano, radio_base, centro=None, rng=None, sigma=None):
    # Genera un volumen organico 3D (similar al poligono irregular).
    # Estrategia: Crea una esfera base, le anade ruido aleatorio tridimensional,
    # y luego suaviza fuertemente el volumen completo.
    cx, cy, cz = _centro_por_defecto_3d(tamano, centro)
    if rng is None:
        rng = np.random.default_rng()

    # Empezamos con una matriz vacia y colocamos algunas "semillas" (bloques o esferas)
    # aleatorias cerca del centro.
    volumen_crudo = np.zeros((tamano, tamano, tamano), dtype=float)
    
    num_semillas = int(rng.integers(5, 12))
    for _ in range(num_semillas):
        # Desviacion aleatoria desde el centro
        dx = rng.uniform(-radio_base, radio_base)
        dy = rng.uniform(-radio_base, radio_base)
        dz = rng.uniform(-radio_base, radio_base)
        r_semilla = rng.uniform(radio_base/4, radio_base)
        
        # Generar mascara de esta semilla
        zz, yy, xx = np.ogrid[:tamano, :tamano, :tamano]
        semilla_mask = (xx - (cx+dx))**2 + (yy - (cy+dy))**2 + (zz - (cz+dz))**2 <= r_semilla**2
        volumen_crudo[semilla_mask] = 1.0

    # Suavizado gaussiano 3D para fundir las semillas en una sola masa organica
    if sigma is None:
        sigma = tamano * 0.04
    suavizada = gaussian_filter(volumen_crudo, sigma=sigma)

    # Re-binarizar
    return suavizada >= 0.4

def forma_aleatoria_3d(tamano, centro=None, rng=None):
    if rng is None:
        rng = np.random.default_rng()

    cx, cy, cz = _centro_por_defecto_3d(tamano, centro)
    centro_3d = (cx, cy, cz)

    tipo = rng.choice(["esfera", "elipsoide", "cilindro", "masa_irregular_3d", "L_3d"])

    if tipo == "esfera":
        return esfera(tamano, radio=int(rng.integers(tamano // 8, tamano // 3)), centro=centro_3d)
    
    if tipo == "elipsoide":
        return elipsoide(
            tamano,
            radio_x=int(rng.integers(tamano // 6, tamano // 3)),
            radio_y=int(rng.integers(tamano // 10, tamano // 4)),
            radio_z=int(rng.integers(tamano // 8, tamano // 3)),
            centro=centro_3d
        )
        
    if tipo == "cilindro":
        return cilindro(
            tamano, 
            radio=int(rng.integers(tamano // 8, tamano // 4)), 
            altura=int(rng.integers(tamano // 3, tamano // 1.5)), 
            centro=centro_3d
        )
        
    if tipo == "masa_irregular_3d":
        return masa_irregular_3d(
            tamano,
            radio_base=tamano // 4,
            centro=centro_3d,
            rng=rng
        )
        
    if tipo == "L_3d":
        return forma_L_3d(
            tamano, 
            ancho=tamano // 3, 
            alto=tamano // 3, 
            prof=tamano // 4, 
            grosor=tamano // 8, 
            centro=centro_3d
        )