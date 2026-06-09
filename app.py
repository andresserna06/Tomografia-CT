# app.py
# Aplicacion Dash principal del simulador CT.
# Solo orquesta: arma la app, monta el layout y registra los callbacks.
# La logica vive en core/ (fisica) y ui/ (presentacion).

# --- Stdlib ---
import os
import sys

# Asegura que el directorio de este archivo este en sys.path para que
# funcionen los imports "from config import ...", "from core ...", "from ui ..."
# tanto si se ejecuta "python app.py" como "python tomografia_ct/app.py".
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# --- Terceros ---
import dash
import dash_bootstrap_components as dbc

# --- Locales ---
from ui.layout import crear_layout
from ui.callbacks import registrar_callbacks


# Instancia de la app Dash con tema Bootstrap.
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Simulador CT"

# Layout y callbacks.
app.layout = crear_layout()
registrar_callbacks(app)


if __name__ == "__main__":
    # Servidor de desarrollo en el puerto 8050.
    app.run(debug=True, port=8050)
