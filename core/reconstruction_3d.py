# reconstruction_3d.py
# Reconstruccion volumetrica (Objetivo 4).
# Un volumen 3D no se tomografia de golpe: se trata como una PILA DE CORTES
# TRANSVERSALES (axiales). Para cada corte se reutiliza exactamente el pipeline
# 2D que ya funciona: corte -> radon() -> iradon(). Luego los cortes
# reconstruidos se apilan de nuevo en un volumen 3D.
#
# Parametro clave: 'paso' = distancia (en voxeles) entre cortes reconstruidos.
# Es el analogo del "grosor de corte" de un CT real y controla la RESOLUCION
# AXIAL (eje Z):
#   - paso = 1 : se reconstruye cada corte (maxima resolucion, mas lento).
#   - paso > 1 : se saltan cortes; cada corte reconstruido se REPITE a lo alto
#                de su rebanada, de modo que el objeto se ve escalonado en Z.
#                Esto evidencia, de forma honesta, el costo de muestrear pocos
#                cortes (no se interpola para no "maquillar" la perdida).

# --- Terceros ---
import numpy as np

# --- Locales ---
from core.acquisition import generar_sinograma
from core.reconstruction import reconstruir_fbp


def reconstruir_volumen(
    volumen: np.ndarray,
    num_angulos: int,
    paso: int = 1,
    unir_cortes: bool = True,  # <--- Nuevo parámetro
) -> tuple[np.ndarray, list[int]]:
    
    n = volumen.shape[0]
    paso = max(1, int(paso))
    reconstruccion = np.zeros_like(volumen)
    indices = list(range(0, n, paso))

    for z in indices:
        corte = volumen[z]
        sinograma, angulos = generar_sinograma(corte, num_angulos)
        corte_recon = reconstruir_fbp(sinograma, angulos, tamano_salida=n)

        if unir_cortes:
            # MODO UNIDO (Bloques/Minecraft): Repetimos el corte en el bloque
            z_fin = min(z + paso, n)
            reconstruccion[z:z_fin] = corte_recon
        else:
            # MODO SEPARADO (Discos): Solo guardamos el corte exacto en su sitio
            reconstruccion[z] = corte_recon

    return reconstruccion, indices
