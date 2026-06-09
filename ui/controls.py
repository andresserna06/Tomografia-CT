# controls.py
# Define el panel de controles del Modo 2D. Aqui solo se DECLARAN los
# componentes y sus IDs; la logica reactiva vive en ui/callbacks.py.

# --- Terceros ---
import dash_bootstrap_components as dbc
from dash import dcc, html

# --- Locales ---
from config import ANGULOS_DEFAULT, MU_PIEZA, MU_FONDO

# Opciones del selector de forma. El 'value' debe coincidir con los nombres
# que entiende core/phantom.py.
OPCIONES_FORMA = [
    {"label": "Circulo", "value": "circulo"},
    {"label": "Elipse", "value": "elipse"},
    {"label": "Poligono irregular", "value": "poligono_irregular"},
    {"label": "Estrella", "value": "estrella"},
    {"label": "Forma L", "value": "L"},
    {"label": "Forma T", "value": "T"},
    {"label": "Aleatoria", "value": "aleatoria"},
]


def crear_controles():
    # Devuelve la tarjeta con todos los controles del panel izquierdo.
    return dbc.Card(
        dbc.CardBody(
            [
                html.H5("Controles", className="mb-3"),

                # --- Forma de la pieza ---
                html.Label("Forma de la pieza"),
                dcc.Dropdown(
                    id="dropdown-forma",
                    options=OPCIONES_FORMA,
                    value="circulo",
                    clearable=False,
                ),
                html.Hr(),

                # --- Numero de angulos de proyeccion ---
                html.Label("Numero de angulos"),
                dcc.Slider(
                    id="slider-angulos",
                    min=5,
                    max=360,
                    step=1,
                    value=ANGULOS_DEFAULT,
                    marks={5: "5", 90: "90", 180: "180", 270: "270", 360: "360"},
                    tooltip={"placement": "bottom", "always_visible": True},
                ),

                # --- Coeficiente de absorcion de la pieza ---
                html.Label("Coef. absorcion pieza (mu)"),
                dcc.Slider(
                    id="slider-mu-pieza",
                    min=1.0,
                    max=10.0,
                    step=0.5,
                    value=MU_PIEZA,
                    marks={1: "1", 5: "5", 10: "10"},
                    tooltip={"placement": "bottom", "always_visible": True},
                ),

                # --- Coeficiente de absorcion del fondo ---
                html.Label("Coef. absorcion fondo (mu)"),
                dcc.Slider(
                    id="slider-mu-fondo",
                    min=0.1,
                    max=2.0,
                    step=0.1,
                    value=MU_FONDO,
                    marks={0.1: "0.1", 1: "1", 2: "2"},
                    tooltip={"placement": "bottom", "always_visible": True},
                ),
                html.Hr(),

                # --- Modo oculto y acciones ---
                dbc.Switch(id="switch-oculto", label="Modo oculto", value=False),
                html.Div(
                    [
                        dbc.Button(
                            "Revelar pieza",
                            id="btn-revelar",
                            color="secondary",
                            className="mb-2",
                        ),
                        dbc.Button(
                            "Generar nueva pieza",
                            id="btn-generar",
                            color="primary",
                        ),
                    ],
                    className="d-grid gap-2 mt-2",
                ),
            ]
        ),
    )
