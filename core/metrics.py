# metrics.py
# Cuantificacion de la FORMA reconstruida.
# El enunciado pide "comprobar que por la tomografia se logro cuantificar la
# forma" de la pieza escondida. Eso NO es una comparacion pixel a pixel de
# intensidades (RMSE/SSIM/PSNR castigan el ruido de fondo de la FBP y dan
# valores enganosos), sino medir cuanto coincide la SILUETA reconstruida con la
# real. Para eso binarizamos ambas (pieza vs fondo) y comparamos las mascaras
# con indices de solapamiento: Dice e IoU, mas el error de area.

# --- Terceros ---
import numpy as np
from skimage.filters import threshold_otsu


def _mascara_pieza(img: np.ndarray) -> np.ndarray:
    # Binariza una imagen/volumen en pieza (True) vs fondo (False).
    # La pieza es la region MAS densa (mayor mu -> mayor intensidad, tanto en el
    # phantom como en la reconstruccion), asi que tomamos lo que queda por encima
    # de un umbral. Usamos Otsu, que halla automaticamente el corte que mejor
    # separa las dos poblaciones (fondo vs pieza) sin fijar un valor a mano.
    img = img.astype(np.float64)

    # Si la imagen es casi uniforme no hay pieza distinguible (evita que Otsu
    # falle ante un histograma de un solo pico).
    if img.max() - img.min() < 1e-9:
        return np.zeros(img.shape, dtype=bool)

    try:
        umbral = float(threshold_otsu(img))
    except Exception:
        # Plan B: punto medio del rango.
        umbral = 0.5 * (float(img.min()) + float(img.max()))

    return img > umbral


def cuantificar_forma(original: np.ndarray, reconstruida: np.ndarray) -> dict:
    # Compara la SILUETA de la pieza original contra la reconstruida.
    # Devuelve:
    #   dice : coeficiente de Dice 2|A∩B| / (|A|+|B|)   (1 = solape perfecto).
    #   iou  : interseccion sobre union |A∩B| / |A∪B|   ( que Dice).
    #   area : error de area relativo en %  (0 = misma cantidad de pixeles/voxeles).
    a = _mascara_pieza(original)
    b = _mascara_pieza(reconstruida)

    interseccion = float(np.logical_and(a, b).sum())
    union = float(np.logical_or(a, b).sum())
    area_a = float(a.sum())
    area_b = float(b.sum())

    dice = (2.0 * interseccion / (area_a + area_b)) if (area_a + area_b) > 0 else 0.0
    iou = (interseccion / union) if union > 0 else 0.0
    # Error de area: cuanto se desvia el tamano reconstruido del real (en %).
    err_area = (abs(area_b - area_a) / area_a * 100.0) if area_a > 0 else 100.0

    return {"dice": dice, "iou": iou, "area": err_area}


# Umbrales para traducir cada metrica a un veredicto cualitativo (Buena /
# Aceptable / Pobre). Se centralizan aqui para que 2D y 3D usen el MISMO criterio.
# Cada entrada: (mejor_alto, (corte_buena, corte_aceptable)).
#   mejor_alto=True  -> valores ALTOS son mejores (Dice, IoU).
#   mejor_alto=False -> valores BAJOS son mejores (error de area).
_UMBRALES = {
    # Dice [0,1]: >=0.90 buena, >=0.70 aceptable, resto pobre.
    "dice": (True, (0.90, 0.70)),
    # IoU [0,1]: >=0.80 buena, >=0.55 aceptable, resto pobre (IoU es mas exigente).
    "iou": (True, (0.80, 0.55)),
    # Error de area en %: <=10 buena, <=25 aceptable, resto pobre.
    "area": (False, (10.0, 25.0)),
}


def clasificar_metrica(nombre: str, valor: float) -> tuple[str, str]:
    # Traduce el valor numerico de una metrica a (etiqueta, clase_css):
    #   ("Buena", "good") / ("Aceptable", "ok") / ("Pobre", "bad").
    # La clase_css la usa la UI para pintar el veredicto de color (verde/ambar/rojo).
    mejor_alto, (corte_buena, corte_aceptable) = _UMBRALES[nombre]

    if mejor_alto:
        # Mas alto = mejor: se compara hacia abajo desde el corte "buena".
        if valor >= corte_buena:
            return "Buena", "good"
        if valor >= corte_aceptable:
            return "Aceptable", "ok"
        return "Pobre", "bad"

    # Mas bajo = mejor (error de area): se compara hacia arriba desde "buena".
    if valor <= corte_buena:
        return "Buena", "good"
    if valor <= corte_aceptable:
        return "Aceptable", "ok"
    return "Pobre", "bad"
