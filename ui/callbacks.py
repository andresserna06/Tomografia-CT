# callbacks.py
# Logica reactiva del Modo 2D. Se organiza en callbacks separados para
# cumplir el requisito de eficiencia: el phantom solo se recalcula cuando
# cambia la forma o el mu, NO cuando se mueve el slider de angulos.

# --- Terceros ---
import numpy as np
import plotly.graph_objects as go
from dash import Input, Output, ctx, no_update

# --- Locales ---
from config import TAMANO_IMAGEN
from core.phantom import crear_phantom
from core.acquisition import generar_sinograma
from core.reconstruction import reconstruir_fbp


# Cache en memoria del phantom actual.
#
# Por que un cache global y no un dcc.Store con el array: el phantom es de
# 256x256 floats (~65k valores). Serializarlo a JSON y transmitirlo en cada
# movimiento del slider de angulos haria la interaccion lenta. Como la app es
# local y de un solo usuario, guardarlo en memoria del servidor es suficiente
# y mucho mas rapido. El dcc.Store "store-token" solo lleva un contador que
# avisa al callback de reconstruccion que el phantom cambio.
_CACHE = {"phantom": None, "version": 0}


def _figura_heatmap(datos, titulo: str, colorscale: str) -> go.Figure:
    # Construye un heatmap de Plotly a partir de una matriz 2D.
    fig = go.Figure(data=go.Heatmap(z=datos, colorscale=colorscale, showscale=True))
    fig.update_layout(
        title=titulo,
        margin=dict(l=10, r=10, t=40, b=10),
        height=360,
    )
    # Origen arriba (convencion de imagen).
    fig.update_yaxes(autorange="reversed")
    fig.update_xaxes(constrain="domain")
    return fig


def registrar_callbacks(app):
    # Registra todos los callbacks del Modo 2D sobre la app Dash recibida.

    # -----------------------------------------------------------------------
    # 1) Semilla aleatoria.
    #    Se renueva SOLO al cambiar la forma o al pulsar "Generar nueva pieza".
    #    Asi, mover los sliders de mu no cambia la figura (misma semilla).
    # -----------------------------------------------------------------------
    @app.callback(
        Output("store-seed", "data"),
        Input("dropdown-forma", "value"),
        Input("btn-generar", "n_clicks"),
    )
    def _nueva_semilla(_forma, _n_generar):
        return int(np.random.randint(0, 2**31 - 1))

    # -----------------------------------------------------------------------
    # 2) Phantom.
    #    Se recalcula al cambiar forma, mu_pieza, mu_fondo, modo oculto
    #    (posicion) o la semilla. Guarda el phantom en cache y publica un
    #    token (version) para disparar la reconstruccion.
    # -----------------------------------------------------------------------
    @app.callback(
        Output("store-token", "data"),
        Output("graf-phantom", "figure"),
        Input("dropdown-forma", "value"),
        Input("slider-mu-pieza", "value"),
        Input("slider-mu-fondo", "value"),
        Input("switch-oculto", "value"),
        Input("store-seed", "data"),
    )
    def _actualizar_phantom(forma, mu_pieza, mu_fondo, oculto, semilla):
        phantom = crear_phantom(
            TAMANO_IMAGEN,
            forma=forma,
            mu_fondo=mu_fondo,
            mu_pieza=mu_pieza,
            posicion_aleatoria=bool(oculto),
            semilla=semilla,
        )
        _CACHE["phantom"] = phantom
        _CACHE["version"] += 1  # el token siempre cambia -> dispara reconstruccion

        fig = _figura_heatmap(phantom, "Phantom (mu real)", "gray")
        return _CACHE["version"], fig

    # -----------------------------------------------------------------------
    # 3) Sinograma + reconstruccion.
    #    Se dispara cuando cambia el phantom (token) o el numero de angulos.
    #    Cuando solo cambian los angulos, lee el phantom del cache: NO lo
    #    regenera (cumple el requisito de eficiencia).
    # -----------------------------------------------------------------------
    @app.callback(
        Output("graf-sinograma", "figure"),
        Output("graf-reconstruccion", "figure"),
        Input("store-token", "data"),
        Input("slider-angulos", "value"),
    )
    def _actualizar_reconstruccion(_token, num_angulos):
        phantom = _CACHE["phantom"]
        if phantom is None:
            # Aun no se ha generado el phantom (primer render): no actualizar.
            return no_update, no_update

        sinograma, angulos = generar_sinograma(phantom, num_angulos)
        reconstruccion = reconstruir_fbp(sinograma, angulos)

        fig_sino = _figura_heatmap(
            sinograma, f"Sinograma ({num_angulos} ang.)", "hot"
        )
        fig_recon = _figura_heatmap(reconstruccion, "Reconstruccion FBP", "gray")
        return fig_sino, fig_recon

    # -----------------------------------------------------------------------
    # 4) Visibilidad del phantom (modo oculto).
    #    - Modo oculto OFF -> phantom visible.
    #    - Modo oculto ON  -> phantom oculto, salvo que se pulse "Revelar".
    #    - Generar nueva pieza estando en modo oculto -> se vuelve a ocultar.
    # -----------------------------------------------------------------------
    @app.callback(
        Output("graf-phantom", "style"),
        Input("switch-oculto", "value"),
        Input("btn-revelar", "n_clicks"),
        Input("btn-generar", "n_clicks"),
    )
    def _visibilidad_phantom(oculto, _n_revelar, _n_generar):
        if not oculto:
            return {"display": "block"}
        if ctx.triggered_id == "btn-revelar":
            return {"display": "block"}
        # El switch se acaba de activar o se genero una pieza nueva: ocultar.
        return {"display": "none"}
