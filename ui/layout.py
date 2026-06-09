# layout.py
# Layout general de la app. Define la estructura de tabs de nivel superior
# (Modo 2D / Modo 3D) y, dentro del Modo 2D, el panel de controles (izquierda)
# y el panel de graficas (centro).

# --- Terceros ---
import dash_bootstrap_components as dbc
from dash import dcc, html

# --- Locales ---
from ui.controls import crear_controles


def _contenido_2d():
    # Modo 2D: controles (col-3) + graficas (col-9).
    panel_graficas = dbc.Col(
        dbc.Row(
            [
                dbc.Col(dcc.Graph(id="graf-phantom"), md=4),
                dbc.Col(dcc.Graph(id="graf-sinograma"), md=4),
                dbc.Col(dcc.Graph(id="graf-reconstruccion"), md=4),
            ]
        ),
        md=9,
    )

    return dbc.Row(
        [
            dbc.Col(crear_controles(), md=3),
            panel_graficas,
        ],
        className="mt-3",
    )


def _contenido_3d():
    # Placeholder. La reconstruccion volumetrica se implementa en el Objetivo 4.
    return html.Div(
        [
            html.H4("Modo 3D", className="mt-4"),
            html.P("Proximamente.", className="text-muted"),
        ],
        className="p-4",
    )


def crear_layout():
    # Construye el layout completo de la aplicacion.
    return dbc.Container(
        [
            html.H2(
                "Simulador de Tomografia Computacional (CT)",
                className="my-3",
            ),

            dcc.Tabs(
                id="tabs-modo",
                value="tab-2d",
                children=[
                    dcc.Tab(label="Modo 2D", value="tab-2d", children=_contenido_2d()),
                    dcc.Tab(label="Modo 3D", value="tab-3d", children=_contenido_3d()),
                ],
            ),

            # Almacenes de estado (fuera de los tabs para que siempre existan):
            #   store-seed  -> semilla aleatoria de la pieza actual.
            #   store-token -> contador que avisa cuando el phantom cambio.
            dcc.Store(id="store-seed", data=0),
            dcc.Store(id="store-token", data=0),
        ],
        fluid=True,
    )
