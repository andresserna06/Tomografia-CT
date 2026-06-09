# app.py
# Aplicacion Dash principal del simulador CT.
# Solo orquesta: arma la app, monta el layout y registra los callbacks.
# La logica vive en core/ (fisica) y ui/ (presentacion).

# --- Stdlib ---
import os
import sys

# Directorio donde vive ESTE archivo (app.py).
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Asegura que este directorio este en sys.path para que funcionen los imports
# "from config import ...", "from core ...", "from ui ..." tanto si se ejecuta
# "python app.py" como "python tomografia_ct/app.py".
sys.path.insert(0, BASE_DIR)

# --- Terceros ---
import dash
import dash_bootstrap_components as dbc

# --- Locales ---
from ui.layout import crear_layout
from ui.callbacks import registrar_callbacks


# Instancia de la app Dash.
# Tema DARKLY: base oscura neutra para evitar parpadeos blancos en los
# componentes de dash-bootstrap. El aspecto final lo da assets/style.css.
#
# assets_folder con ruta ABSOLUTA: garantiza que Dash encuentre la carpeta
# assets/ (style.css + theme.js) sin importar desde que carpeta se ejecute.
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.DARKLY],
    assets_folder=os.path.join(BASE_DIR, "assets"),
)
app.title = "Simulador CT"

# Layout y callbacks.
app.layout = crear_layout()
registrar_callbacks(app)


if __name__ == "__main__":
    # Servidor de desarrollo en el puerto 8050.
    app.run(debug=True, port=8050)
