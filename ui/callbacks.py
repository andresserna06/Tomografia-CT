# callbacks.py
# Logica reactiva del Modo 2D.
# Cambios respecto a la version original:
#   - Las figuras usan un tema OSCURO sin ejes para verse como visores.
#   - El callback de reconstruccion ademas calcula RMSE/SSIM/PSNR (metricas)
#     y dibuja el perfil de corte (fila central original vs reconstruida).
# La estructura eficiente se mantiene: el phantom solo se recalcula cuando
# cambia la forma o el mu, NO al mover el slider de angulos.

# --- Terceros ---
import numpy as np
import plotly.graph_objects as go
from dash import Input, Output, ctx, no_update

# --- Locales ---
from config import TAMANO_IMAGEN
from core.phantom import crear_phantom
from core.acquisition import generar_sinograma
from core.reconstruction import reconstruir_fbp
from core.metrics import calcular_metricas


_CACHE = {"phantom": None, "version": 0}


# ---------------------------------------------------------------------------
# Helpers de presentacion
# ---------------------------------------------------------------------------
def _figura_visor(datos, colorscale: str) -> go.Figure:
    # Heatmap "limpio": fondo transparente, sin ejes ni barra de color.
    # Asi encaja dentro del visor oscuro (.viewer) del CSS.
    fig = go.Figure(data=go.Heatmap(z=datos, colorscale=colorscale, showscale=False))
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        autosize=True,
    )
    fig.update_xaxes(visible=False, constrain="domain")
    fig.update_yaxes(visible=False, autorange="reversed", scaleanchor="x")
    return fig


def _figura_perfil(original, reconstruida) -> go.Figure:
    # Perfil 1D: la fila central de la imagen original vs la reconstruida.
    fila = original.shape[0] // 2
    x = np.arange(original.shape[1])
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=original[fila], mode="lines",
                             line=dict(color="#9aa4b4", width=2), name="original"))
    fig.add_trace(go.Scatter(x=x, y=reconstruida[fila], mode="lines",
                             line=dict(color="#36b6d6", width=2), name="reconstruida"))
    fig.update_layout(
        margin=dict(l=0, r=0, t=4, b=0),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False, autosize=True,
    )
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return fig


def registrar_callbacks(app):

    # 1) Semilla aleatoria: se renueva al cambiar la forma o al "Generar nueva".
    @app.callback(
        Output("store-seed", "data"),
        Input("dropdown-forma", "value"),
        Input("btn-generar", "n_clicks"),
    )
    def _nueva_semilla(_forma, _n_generar):
        return int(np.random.randint(0, 2**31 - 1))

    # 2) Phantom: se recalcula al cambiar forma, mu o semilla. Lo cachea y
    #    publica un token para disparar la reconstruccion.
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
            TAMANO_IMAGEN, forma=forma, mu_fondo=mu_fondo, mu_pieza=mu_pieza,
            posicion_aleatoria=bool(oculto), semilla=semilla,
        )
        _CACHE["phantom"] = phantom
        _CACHE["version"] += 1
        return _CACHE["version"], _figura_visor(phantom, "gray")

    # 3) Sinograma + reconstruccion + metricas + perfil.
    #    Se dispara al cambiar el phantom (token) o el numero de angulos.
    @app.callback(
        Output("graf-sinograma", "figure"),
        Output("graf-reconstruccion", "figure"),
        Output("graf-perfil", "figure"),
        Output("stat-rmse", "children"),
        Output("stat-ssim", "children"),
        Output("stat-psnr", "children"),
        Output("bar-rmse", "style"),
        Output("bar-ssim", "style"),
        Output("bar-psnr", "style"),
        Output("meta-sino", "children"),
        Input("store-token", "data"),
        Input("slider-angulos", "value"),
    )
    def _actualizar_reconstruccion(_token, num_angulos):
        phantom = _CACHE["phantom"]
        if phantom is None:
            return (no_update,) * 10

        sinograma, angulos = generar_sinograma(phantom, num_angulos)
        reconstruccion = reconstruir_fbp(sinograma, angulos)

        fig_sino = _figura_visor(sinograma, "hot")
        fig_recon = _figura_visor(reconstruccion, "gray")
        fig_perfil = _figura_perfil(phantom, reconstruccion)

        m = calcular_metricas(phantom, reconstruccion)
        rmse_txt = f"{m['rmse']:.3f}"
        ssim_txt = f"{m['ssim']:.2f}"
        psnr_txt = f"{m['psnr']:.1f}"

        # Anchos de las barras (0-100%). RMSE: menor es mejor -> se invierte.
        w_rmse = max(4, min(100, (1 - min(m["rmse"], 0.3) / 0.3) * 100))
        w_ssim = max(0, min(100, m["ssim"] * 100))
        w_psnr = max(0, min(100, m["psnr"] / 40 * 100))

        return (
            fig_sino, fig_recon, fig_perfil,
            rmse_txt, ssim_txt, psnr_txt,
            {"width": f"{w_rmse:.0f}%"},
            {"width": f"{w_ssim:.0f}%"},
            {"width": f"{w_psnr:.0f}%"},
            f"{num_angulos} ang.",
        )

    # 4) Visibilidad del phantom (modo oculto).
    @app.callback(
        Output("graf-phantom", "style"),
        Input("switch-oculto", "value"),
        Input("btn-revelar", "n_clicks"),
        Input("btn-generar", "n_clicks"),
    )
    def _visibilidad_phantom(oculto, _n_revelar, _n_generar):
        base = {"height": "300px"}
        if not oculto:
            return {**base, "display": "block"}
        if ctx.triggered_id == "btn-revelar":
            return {**base, "display": "block"}
        return {**base, "display": "none"}
