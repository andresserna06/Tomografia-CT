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
