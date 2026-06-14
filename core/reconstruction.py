# reconstruction_3d.py
# Reconstruye el volumen 3D a partir de un "sinograma volumetrico" (stack de 
# sinogramas 2D) iterando rebanada por rebanada en el eje Z.
#
# Para mantener la UI interactiva, permite calcular solo un subconjunto de 
# rebanadas (step_z) e interpolar los cortes intermedios.

# --- Terceros ---
import numpy as np
from skimage.transform import iradon
from scipy.interpolate import interp1d

def reconstruir_fbp_3d(
    sinograma_3d: np.ndarray,
    angulos: np.ndarray,
    filtro: str = "ramp",
    step_z: int = 1,
) -> np.ndarray:
    # Reconstruye el volumen 3D mediante retroproyeccion filtrada iterativa.
    #
    # sinograma_3d : stack de proyecciones con forma (Z, posicion_detector, angulos).
    # angulos      : angulos de cada proyeccion (en grados).
    # filtro       : nombre del filtro FBP (ej. "ramp", "shepp-logan").
    # step_z       : factor de salto. Si es 2, reconstruye la mitad del volumen
    #                y calcula el resto por interpolacion lineal espacial.
    #
    # Retorna un ndarray 3D con el volumen reconstruido.

    # Limpieza del nombre del filtro por si llega como "ramp-filter"
    filtro_skimage = filtro.replace("-filter", "")
    
    # Extraemos las dimensiones: profundidad (Z), tamaño de imagen, y cantidad de ángulos
    size_z, size_det, num_angulos = sinograma_3d.shape
    
    # ¡CAMBIO 1! Usamos size_z para que el volumen sea (128, 128, 128)
    # y coincida perfectamente con el phantom original.
    volumen_reconstruido = np.zeros((size_z, size_z, size_z), dtype=float)
    
    slices_calculados = []
    
    # 1. Bucle de Reconstruccion Slice-by-Slice
    for z in range(0, size_z, step_z):
        sino_2d = sinograma_3d[z, :, :]
        
        recon_2d = iradon(
            sino_2d,
            theta=angulos,
            filter_name=filtro_skimage,
            circle=False,
            output_size=size_z,  # <--- ¡CAMBIO 2! Obligamos a iradon a devolver 128x128
        )
        
        volumen_reconstruido[z, :, :] = recon_2d
        slices_calculados.append(z)
        
    # 2. Interpolacion en el eje Z (Aceleracion de rendimiento)
    if step_z > 1 and len(slices_calculados) > 1:
        # Extraemos unicamente los cortes que pasaron por iradon()
        datos_reales = volumen_reconstruido[slices_calculados, :, :]
        
        # Creamos una funcion interpoladora a lo largo de la profundidad (axis=0)
        f_interp = interp1d(
            slices_calculados, 
            datos_reales, 
            axis=0, 
            kind='linear', 
            fill_value="extrapolate"
        )
        
        # Sobrescribimos el volumen completo evaluando la funcion en cada Z
        volumen_reconstruido = f_interp(np.arange(size_z))
        
    return volumen_reconstruido