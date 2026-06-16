# controls_3d.py
# Barra de controles del Modo 3D. Misma estructura visual que los controles 2D
# (reutiliza las clases CSS .controls / .field), pero con IDs propios con sufijo
# "-3d" para no chocar con los callbacks del Modo 2D.

# --- Terceros ---
import dash_bootstrap_components as dbc
from dash import dcc, html

# --- Locales ---
from config import ANGULOS_3D_DEFAULT, PASO_CORTE_DEFAULT, MU_PIEZA, MU_FONDO

OPCIONES_FORMA_3D = [
    {"label": "Esfera", "value": "esfera"},
    {"label": "Elipsoide", "value": "elipsoide"},
    {"label": "Cilindro", "value": "cilindro"},
    {"label": "Prisma", "value": "prisma"},
    {"label": "Toroide", "value": "toroide"},
    {"label": "Aleatoria", "value": "aleatoria"},
]


def _campo(label_children, control, extra_class=""):
    # Envoltorio comun: etiqueta mono arriba + control debajo (igual que en 2D).
    return html.Div(
        [html.Div(label_children, className="clbl"), control],
        className=f"field {extra_class}".strip(),
    )


def crear_controles_3d():
    # Devuelve la barra de controles del Modo 3D en DOS FILAS:
    #   - Fila superior (.row-top): los parametros continuos (sliders + forma),
    #     que necesitan ancho horizontal para leerse comodos.
    #   - Fila inferior (.row-bottom): los switches y los botones de accion,
    #     mas compactos, separados por un divisor para que no compitan con los
    #     sliders. Esto evita el "apeñuscamiento" que daba reutilizar el grid 2D.
    return html.Div(
        [
            # ===== Fila 1: geometria + adquisicion + material =====
            html.Div(
                [
                    # --- Forma de la pieza 3D ---
                    _campo(
                        "Forma de la pieza",
                        dbc.Select(
                            id="dropdown-forma-3d",
                            options=OPCIONES_FORMA_3D,
                            value="esfera",
                        ),
                    ),

                    # --- Numero de angulos (proyecciones por corte) ---
                    _campo(
                        "N.o de angulos",
                        dcc.Slider(
                            id="slider-angulos-3d",
                            min=1, max=180, step=1, value=ANGULOS_3D_DEFAULT,
                            marks={1: "1", 45: "45", 90: "90", 180: "180"},
                            tooltip={"placement": "bottom", "always_visible": True},
                        ),
                    ),

                    # --- Distancia entre cortes transversales (resolucion axial Z) ---
                    _campo(
                        "Dist. entre cortes",
                        dcc.Slider(
                            id="slider-paso",
                            min=1, max=8, step=1, value=PASO_CORTE_DEFAULT,
                            marks={1: "1", 2: "2", 4: "4", 8: "8"},
                            tooltip={"placement": "bottom", "always_visible": True},
                        ),
                    ),

                    # --- mu pieza (track ambar via .hot) ---
                    _campo(
                        [html.Span("μ", className="mu"), " pieza"],
                        dcc.Slider(
                            id="slider-mu-pieza-3d",
                            min=1.0, max=10.0, step=0.5, value=MU_PIEZA,
                            marks={1: "1", 5: "5", 10: "10"},
                            tooltip={"placement": "bottom", "always_visible": True},
                        ),
                        extra_class="hot",
                    ),

                    # --- mu fondo ---
                    _campo(
                        [html.Span("μ", className="mu"), " fondo"],
                        dcc.Slider(
                            id="slider-mu-fondo-3d",
                            min=0.1, max=2.0, step=0.1, value=MU_FONDO,
                            marks={0.1: "0.1", 1: "1", 2: "2"},
                            tooltip={"placement": "bottom", "always_visible": True},
                        ),
                    ),
                ],
                className="row-top",
            ),

            # ===== Fila 2: visualizacion + escena + acciones =====
            html.Div(
                [
                    # --- Continuidad Z: unir cortes o mostrarlos separados ---
                    _campo(
                        "Eje Z (Visualización)",
                        dbc.Switch(
                            id="switch-unir-3d",
                            label="Unir rebanadas",
                            value=True,
                        ),
                    ),

                    # --- Modo oculto (figura escondida en la caja) ---
                    _campo(
                        "Pieza",
                        dbc.Switch(
                            id="switch-oculto-3d",
                            label="Oculta en la caja",
                            value=False,
                        ),
                    ),

                    # --- Acciones (empujadas a la derecha por CSS) ---
                    # Solo "Generar nueva": el ocultar/revelar lo maneja ahora el
                    # switch de arriba (ON esconde en posicion aleatoria, OFF revela
                    # la pieza en su sitio real), asi que el boton "Revelar" sobraba.
                    _campo(
                        "Acciones",
                        html.Div(
                            [
                                dbc.Button("Generar nueva", id="btn-generar-3d", color="primary"),
                            ],
                            className="btns",
                        ),
                        extra_class="acciones",
                    ),
                ],
                className="row-bottom",
            ),
        ],
        className="ct-card controls cols-5",
    )
