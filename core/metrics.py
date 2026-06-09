# metrics.py
# Metricas de validacion de la reconstruccion (Objetivo 3).
# Comparan la imagen ORIGINAL (phantom) contra la RECONSTRUIDA para
# cuantificar que tan fiel fue la tomografia.

# --- Terceros ---
import numpy as np
from skimage.metrics import structural_similarity, peak_signal_noise_ratio


def _normalizar(img: np.ndarray) -> np.ndarray:
    # Lleva la imagen al rango [0, 1]. La reconstruccion FBP puede salir
    # en una escala distinta a la del phantom; normalizar ambas hace que
    # las metricas sean comparables y estables.
    img = img.astype(np.float64)
    minimo, maximo = float(img.min()), float(img.max())
    if maximo - minimo < 1e-12:
        return np.zeros_like(img)
    return (img - minimo) / (maximo - minimo)


def calcular_metricas(original: np.ndarray, reconstruida: np.ndarray) -> dict:
    # Devuelve un dict con RMSE, SSIM y PSNR entre original y reconstruida.
    #
    #   RMSE : error cuadratico medio (0 = identicas; menor es mejor).
    #   SSIM : similitud estructural (1 = identicas; mayor es mejor).
    #   PSNR : relacion senal-ruido pico en dB (mayor es mejor).

    a = _normalizar(original)
    b = _normalizar(reconstruida)

    rmse = float(np.sqrt(np.mean((a - b) ** 2)))
    ssim = float(structural_similarity(a, b, data_range=1.0))
    # PSNR puede ser infinito si las imagenes son identicas: lo acotamos.
    try:
        psnr = float(peak_signal_noise_ratio(a, b, data_range=1.0))
        if not np.isfinite(psnr):
            psnr = 99.0
    except Exception:
        psnr = 0.0

    return {"rmse": rmse, "ssim": ssim, "psnr": psnr}
