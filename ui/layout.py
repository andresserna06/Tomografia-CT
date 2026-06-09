# layout.py
# Layout general del simulador (diseno nuevo).
# Estructura: encabezado (marca + tema) -> titulo -> tabs (2D/3D) ->
# barra de controles -> pipeline (phantom -> sinograma -> reconstruccion)
# -> panel de validacion (metricas + perfil de corte).
# Todo el estilo vive en assets/style.css; aqui solo se ponen classNames e IDs.

# --- Terceros ---
import dash_bootstrap_components as dbc
from dash import dcc, html

# --- Locales ---
from ui.controls import crear_controles


def _ticks():
    # Cuatro esquinas tipo "mira" de equipo medico sobre el visor.
    return html.Div([html.Span(), html.Span(), html.Span(), html.Span()], className="ticks")


def _visor(card_titulo, color_dot, meta_id, meta_inicial, graph_id, recon=False):
    # Una etapa del pipeline: cabecera + visor oscuro con el dcc.Graph dentro.
    cabecera = html.Div(
        [
            html.Span([html.Span(className="badge-dot", style={"background": color_dot}), card_titulo], className="t"),
            html.Span(meta_inicial, id=meta_id, className="m"),
        ],
        className="ct-card-h",
    )
    visor = html.Div(
        [
            _ticks(),
            dcc.Graph(
                id=graph_id,
                config={"displayModeBar": False, "responsive": True},
                style={"height": "300px"},
            ),
        ],
        className="viewer",
    )
    return html.Div([cabecera, visor], className="stage recon" if recon else "stage")


def _connector(op, desc):
    return html.Div(
        [html.Div(op, className="op"), html.Div(className="arrow"), html.Div(desc, className="desc")],
        className="connector",
    )


def _stat(clase, k, valor_id, valor_inicial, bar_id, ancho_inicial):
    return html.Div(
        [
            html.Div(k, className="k"),
            html.Div(valor_inicial, id=valor_id, className="val"),
            html.Div(html.I(id=bar_id, style={"width": ancho_inicial}), className="bar"),
        ],
        className=f"stat {clase}",
    )


def _contenido_2d():
    controles = crear_controles()

    pipeline = html.Div(
        [
            _visor("Phantom", "var(--text-soft)", "meta-phantom", "256 x 256", "graf-phantom"),
            _connector("Radon", "\u222b \u03bc dl"),
            _visor("Sinograma", "var(--hot)", "meta-sino", "90 ang.", "graf-sinograma"),
            _connector("iradon", "retroproy."),
            _visor("Reconstruccion", "var(--accent)", "meta-recon", "FBP", "graf-reconstruccion", recon=True),
        ],
        className="pipeline",
    )

    validacion = html.Div(
        [
            html.Div(
                [
                    html.Div(
                        [html.Span("Validacion de la reconstruccion", className="t"),
                         html.Span("original vs reconstruida", className="m")],
                        className="ct-card-h",
                    ),
                    html.Div(
                        [
                            _stat("rmse", "RMSE", "stat-rmse", "—", "bar-rmse", "10%"),
                            _stat("ssim", "SSIM", "stat-ssim", "—", "bar-ssim", "0%"),
                            _stat("psnr", "PSNR", "stat-psnr", "—", "bar-psnr", "0%"),
                        ],
                        className="metrics",
                    ),
                ],
                className="ct-card",
            ),
            html.Div(
                [
                    html.Div(
                        [html.Span("Perfil de corte", className="t"),
                         html.Span("fila central", className="m")],
                        className="ct-card-h",
                    ),
                    dcc.Graph(
                        id="graf-perfil",
                        config={"displayModeBar": False, "responsive": True},
                        style={"height": "150px", "padding": "6px"},
                    ),
                ],
                className="ct-card",
            ),
        ],
        className="validation",
    )

    nota = html.Div(
        [
            html.Span("\u21b3"),
            html.Span(
                ["Los visores son los heatmaps de Plotly del pipeline ",
                 html.Span("phantom \u2192 radon() \u2192 iradon()", className="ct-mono"), "."]
            ),
        ],
        className="note-foot",
    )

    return html.Div([controles, pipeline, validacion, nota])


def _placeholder(icono, titulo, texto):
    return html.Div(
        [
            html.Div(icono, className="icon"),
            html.Div(titulo, className="big"),
            html.Div(texto, className="sm"),
        ],
        className="placeholder",
    )


def _encabezado():
    brandbar = html.Div(
        [
            html.Span("Universidad de Caldas", className="org"),
            html.Span("/", className="sep"),
            html.Span("Ingenieria de Sistemas", className="org"),
            html.Span("/", className="sep"),
            html.Span("Electricidad y Magnetismo", className="org"),
            html.Span("Junio 2026", className="right"),
        ],
        className="brandbar",
    )

    titulo = html.Div(
        [
            html.Div(
                [
                    html.H1(["Simulador de Tomografia Computacional ", html.Span("CT", className="tag")]),
                    html.P("Adquisicion, reconstruccion y validacion de imagenes \u00b7 Ley de Beer-Lambert \u00b7 Transformada de Radon",
                           className="sub"),
                ]
            ),
            html.Div(
                [
                    html.Div(
                        [
                            html.Span("Tema", className="lbl"),
                            html.Div(id="swatches", className="swatches"),   # lo llena theme.js
                            html.Span(className="divider"),
                            html.Button(id="mode-toggle", className="modebtn"),
                        ],
                        className="themebar",
                    ),
                    html.Div([html.Span(className="led"), html.Span("256 x 256 \u00b7 listo", className="mono")],
                             className="status"),
                ],
                style={"display": "flex", "flexDirection": "column", "alignItems": "flex-end", "gap": "11px"},
            ),
        ],
        className="titlerow",
    )

    return html.Div([brandbar, titulo])


def crear_layout():
    return dbc.Container(
        [
            _encabezado(),

            dcc.Tabs(
                id="tabs-modo",
                value="tab-2d",
                parent_className="ct-tabs",
                className="ct-tabs",
                children=[
                    dcc.Tab(label="01  Modo 2D", value="tab-2d",
                            className="ct-tab", selected_className="ct-tab--sel",
                            children=_contenido_2d()),
                    dcc.Tab(label="02  Modo 3D", value="tab-3d",
                            className="ct-tab", selected_className="ct-tab--sel",
                            children=_placeholder("\u25c9", "Modo 3D volumetrico",
                                                  "Reconstruccion rebanada por rebanada. Objetivo 4.")),
                ],
            ),

            dcc.Store(id="store-seed", data=0),
            dcc.Store(id="store-token", data=0),
        ],
        fluid=True,
        className="ct-app",
    )
