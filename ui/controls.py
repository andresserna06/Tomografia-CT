# controls.py
# Barra de controles superior del Modo 2D (diseno nuevo).
# Solo DECLARA los componentes y sus IDs (mismos IDs que antes, para no
# romper los callbacks). El estilo vive en assets/style.css.

# --- Terceros ---
import dash_bootstrap_components as dbc
from dash import dcc, html

# --- Locales ---
from config import ANGULOS_DEFAULT, MU_PIEZA, MU_FONDO

OPCIONES_FORMA = [
    {"label": "Circulo", "value": "circulo"},
    {"label": "Elipse", "value": "elipse"},
    {"label": "Poligono irregular", "value": "poligono_irregular"},
    {"label": "Estrella", "value": "estrella"},
    {"label": "Forma L", "value": "L"},
    {"label": "Forma T", "value": "T"},
    {"label": "Aleatoria", "value": "aleatoria"},
]


def _campo(label_children, control, extra_class=""):
    # Envoltorio comun: etiqueta mono arriba + control debajo.
    return html.Div(
        [html.Div(label_children, className="clbl"), control],
        className=f"field {extra_class}".strip(),
    )


def crear_controles():
    # Devuelve la barra de controles del Modo 2D en DOS FILAS (mismo patron que
    # el Modo 3D para mantener la coherencia entre modos):
    #   - Fila superior (.row-top): forma + sliders (parametros continuos).
    #   - Fila inferior (.row-bottom): switch de modo oculto + acciones.
    return html.Div(
        [
            # ===== Fila 1: forma + adquisicion + material =====
            html.Div(
                [
                    # --- Forma de la pieza ---
                    # Se usa dbc.Select (un <select> nativo) en vez de dcc.Dropdown:
                    # es estable entre versiones de Dash y trivial de estilar por CSS.
                    _campo(
                        "Forma de la pieza",
                        dbc.Select(
                            id="dropdown-forma",
                            options=OPCIONES_FORMA,
                            value="circulo",
                        ),
                    ),

                    # --- Numero de angulos ---
                    _campo(
                        "N.o de angulos",
                        dcc.Slider(
                            id="slider-angulos",
                            min=5, max=360, step=1, value=ANGULOS_DEFAULT,
                            marks={5: "5", 90: "90", 180: "180", 360: "360"},
                            tooltip={"placement": "bottom", "always_visible": True},
                        ),
                    ),

                    # --- mu pieza (track ambar via .hot) ---
                    _campo(
                        [html.Span("\u03bc", className="mu"), " pieza"],
                        dcc.Slider(
                            id="slider-mu-pieza",
                            min=1.0, max=10.0, step=0.5, value=MU_PIEZA,
                            marks={1: "1", 5: "5", 10: "10"},
                            tooltip={"placement": "bottom", "always_visible": True},
                        ),
                        extra_class="hot",
                    ),

                    # --- mu fondo ---
                    _campo(
                        [html.Span("\u03bc", className="mu"), " fondo"],
                        dcc.Slider(
                            id="slider-mu-fondo",
                            min=0.1, max=2.0, step=0.1, value=MU_FONDO,
                            marks={0.1: "0.1", 1: "1", 2: "2"},
                            tooltip={"placement": "bottom", "always_visible": True},
                        ),
                    ),
                ],
                className="row-top",
            ),

            # ===== Fila 2: escena + acciones =====
            html.Div(
                [
                    # --- Modo oculto: un solo switch. ON esconde la pieza en una
                    #     posicion aleatoria; OFF la revela en su sitio real (sin
                    #     regenerarla), por eso ya no hace falta el boton "Revelar". ---
                    _campo(
                        "Pieza",
                        dbc.Switch(id="switch-oculto", label="Modo oculto", value=False),
                    ),

                    # --- Acciones (empujadas a la derecha por CSS) ---
                    _campo(
                        "Acciones",
                        html.Div(
                            [
                                dbc.Button("Generar nueva", id="btn-generar", color="primary"),
                            ],
                            className="btns",
                        ),
                        extra_class="acciones",
                    ),
                ],
                className="row-bottom",
            ),
        ],
        className="ct-card controls cols-4",
    )
