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
) -> tuple[np.ndarray, list[int]]:
    # Reconstruye un volumen 3D corte por corte.
    #
    # volumen     : phantom 3D (mu por voxel), indexado como volumen[z, y, x].
    # num_angulos : numero de proyecciones por corte.
    # paso        : distancia en voxeles entre cortes reconstruidos.
    #
    # Retorna (reconstruccion, indices_reconstruidos):
    #   reconstruccion        -> volumen 3D del mismo tamano que la entrada.
    #   indices_reconstruidos -> lista de indices z donde SI se reconstruyo
    #                            (el resto son repeticiones de esos cortes).

    n = volumen.shape[0]
    paso = max(1, int(paso))

    reconstruccion = np.zeros_like(volumen)
    indices = list(range(0, n, paso))

    for z in indices:
        # Corte axial: una imagen 2D lista para el pipeline 2D.
        corte = volumen[z]

        # Pipeline 2D reutilizado tal cual: adquisicion + retroproyeccion filtrada.
        sinograma, angulos = generar_sinograma(corte, num_angulos)
        # Se fuerza el tamano de salida al lado N del volumen para que el corte
        # reconstruido encaje exactamente al apilarlo.
        corte_recon = reconstruir_fbp(sinograma, angulos, tamano_salida=n)

        # [MODIFICACIÓN]
        # Para dejar los espacios completamente vacíos y ver los cortes separados, 
        # asignamos la reconstrucción ÚNICAMENTE a su posición 'z'. 
        # Como inicializamos la matriz con np.zeros_like, el resto quedará vacío.
        reconstruccion[z] = corte_recon
        
        # (Las siguientes líneas quedarían eliminadas o comentadas)
        # z_fin = min(z + paso, n)
        # reconstruccion[z:z_fin] = corte_recon

    return reconstruccion, indices
