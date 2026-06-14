# config.py
# Constantes y configuraciones globales del simulador CT.
# Centralizar aqui los valores evita "numeros magicos" dispersos por el codigo.

# Lado en pixeles de la imagen cuadrada (phantom y reconstruccion)
TAMANO_IMAGEN = 256

# Numero de angulos de proyeccion por defecto.
# A mas angulos, mejor reconstruccion pero mayor costo de computo.
ANGULOS_DEFAULT = 180

# Coeficiente de absorcion lineal del fondo (mu).
# Aparece en la Ley de Beer-Lambert: I = I0 * exp(-integral de mu dl).
MU_FONDO = 1.0

# Coeficiente de absorcion lineal de la pieza (mas denso que el fondo).
MU_PIEZA = 5.0

# --- Modo 3D (Objetivo 4) ---
# El 3D reconstruye el volumen CORTE POR CORTE (axial), asi que el costo crece
# de forma ~lineal con el numero de cortes. Por eso el volumen es mas pequeno
# que la imagen 2D: hay que hacer una reconstruccion 2D por cada corte.

# Lado del volumen cubico en voxeles (el volumen es TAMANO_VOLUMEN^3).
# 64 da un buen equilibrio entre detalle de la isosuperficie y fluidez en la app.
TAMANO_VOLUMEN = 64

# Numero de angulos de proyeccion por corte en 3D. Se usa menos que en 2D
# porque la adquisicion se repite por cada corte; 90 mantiene la app agil.
ANGULOS_3D_DEFAULT = 90

# Distancia (en voxeles) entre cortes transversales reconstruidos.
#   1  -> se reconstruye cada corte: maxima resolucion axial (eje Z), mas lento.
#   >1 -> se saltan cortes: mas rapido, pero el objeto se ve "escalonado" en Z
#         porque cada corte reconstruido se repite a lo alto de su rebanada
#         (equivale al "grosor de corte" de un CT real).
PASO_CORTE_DEFAULT = 2
