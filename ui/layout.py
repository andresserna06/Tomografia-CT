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
from ui.controls_3d import crear_controles_3d


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


def _visor3d(card_titulo, color_dot, meta_id, meta_inicial, graph_id, recon=False):
    # Igual que _visor pero mas alto, para alojar la escena 3D (isosuperficie).
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
                style={"height": "400px"},
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


# Texto fijo de cada metrica (nombre completo, direccion, valor ideal y una
# explicacion en lenguaje simple). Se centraliza para que 2D y 3D sean identicos.
_METRICAS = {
    "dice": {
        "k": "DICE",
        "nombre": "Coeficiente de Dice",
        "dir": "↑ mayor es mejor",
        "ideal": "ideal: 1",
        "desc": "Solapamiento entre la silueta real y la reconstruida (1 = idénticas).",
    },
    "iou": {
        "k": "IoU",
        "nombre": "Intersección sobre unión",
        "dir": "↑ mayor es mejor",
        "ideal": "ideal: 1",
        "desc": "Área común dividida por el área total cubierta. Más estricto que Dice.",
    },
    "area": {
        "k": "ÁREA",
        "nombre": "Error de área",
        "dir": "↓ menor es mejor",
        "ideal": "ideal: 0 %",
        "desc": "Cuánto se desvía el tamaño de la pieza reconstruida frente al real.",
    },
}


def _stat(clase, valor_id, valor_inicial, bar_id, ancho_inicial, verdict_id):
    # Tarjeta explicada de una metrica: cabecera (acronimo + direccion), nombre
    # completo, valor + veredicto cualitativo, barra de calidad + valor ideal,
    # y una frase descriptiva. El valor, el veredicto y el ancho de la barra los
    # rellenan los callbacks; el resto es texto fijo tomado de _METRICAS.
    meta = _METRICAS[clase]
    return html.Div(
        [
            html.Div(
                [html.Span(meta["k"], className="k"), html.Span(meta["dir"], className="dir")],
                className="stat-head",
            ),
            html.Div(meta["nombre"], className="stat-name"),
            html.Div(
                [
                    html.Span(valor_inicial, id=valor_id, className="val"),
                    html.Span("—", id=verdict_id, className="verdict"),
                ],
                className="stat-valrow",
            ),
            html.Div(
                [
                    html.Div(html.I(id=bar_id, style={"width": ancho_inicial}), className="bar"),
                    html.Span(meta["ideal"], className="ideal"),
                ],
                className="stat-barrow",
            ),
            html.Div(meta["desc"], className="stat-desc"),
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
                        [html.Span("Cuantificacion de la forma", className="t"),
                         html.Span("silueta real vs reconstruida", className="m")],
                        className="ct-card-h",
                    ),
                    html.Div(
                        [
                            _stat("dice", "stat-dice", "—", "bar-dice", "0%", "verdict-dice"),
                            _stat("iou", "stat-iou", "—", "bar-iou", "0%", "verdict-iou"),
                            _stat("area", "stat-area", "—", "bar-area", "0%", "verdict-area"),
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


def _contenido_3d():
    controles = crear_controles_3d()

    # Pipeline 3D: phantom volumetrico -> (radon+iradon por corte) -> reconstruccion.
    pipeline = html.Div(
        [
            _visor3d("Phantom 3D", "var(--text-soft)", "meta-vol-3d", "64³ vox", "graf-phantom-3d"),
            _connector("radon × N", "corte a corte"),
            _visor3d("Reconstruccion 3D", "var(--accent)", "meta-recon-3d", "— cortes", "graf-reconstruccion-3d", recon=True),
        ],
        className="pipeline-3d",
    )

    # Validacion: metricas del volumen (fila ancha arriba) + corte axial central
    # y su sinograma (fila de visores abajo). Antes iban los tres en una sola fila
    # de 3 columnas y quedaban amontonados; ahora cada bloque respira.
    validacion = html.Div(
        [
            html.Div(
                [
                    html.Div(
                        [html.Span("Cuantificacion de la forma", className="t"),
                         html.Span("volumen real vs reconstruido", className="m")],
                        className="ct-card-h",
                    ),
                    html.Div(
                        [
                            _stat("dice", "stat-dice-3d", "—", "bar-dice-3d", "0%", "verdict-dice-3d"),
                            _stat("iou", "stat-iou-3d", "—", "bar-iou-3d", "0%", "verdict-iou-3d"),
                            _stat("area", "stat-area-3d", "—", "bar-area-3d", "0%", "verdict-area-3d"),
                        ],
                        className="metrics",
                    ),
                ],
                className="ct-card",
            ),
            html.Div(
                [
                    _visor("Corte axial", "var(--accent)", "meta-corte-3d", "z = 32", "graf-corte-3d", recon=True),
                    _visor("Sinograma del corte", "var(--hot)", "meta-sino-3d", "90 ang.", "graf-sino-3d"),
                ],
                className="vis-3d-row",
            ),
        ],
        className="validation-3d",
    )

    nota = html.Div(
        [
            html.Span("↳"),
            html.Span(
                ["El volumen se reconstruye ",
                 html.Span("corte por corte", className="ct-mono"),
                 ". La ", html.Span("distancia entre cortes", className="ct-mono"),
                 " fija la resolucion axial: a mayor paso, el objeto se ve escalonado en Z."]
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
                            children=_contenido_3d()),
                ],
            ),

            dcc.Store(id="store-seed", data=0),
            dcc.Store(id="store-token", data=0),
            # ¿La pieza 2D va en posicion aleatoria (escondida)? Se desacopla del
            # switch para poder "revelar en el sitio" sin regenerar la posicion.
            dcc.Store(id="store-pos", data=False),
            dcc.Store(id="store-seed-3d", data=0),
            dcc.Store(id="store-token-3d", data=0),
            # ¿La pieza 3D va en posicion aleatoria (escondida)? Se desacopla del
            # switch para poder "revelar en el sitio" sin regenerar la posicion.
            dcc.Store(id="store-pos-3d", data=False),
        ],
        fluid=True,
        className="ct-app",
    )
