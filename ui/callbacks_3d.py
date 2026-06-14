# callbacks_3d.py
# Logica reactiva del Modo 3D (Objetivo 4).
# Misma estrategia de eficiencia que en 2D: el volumen se cachea en memoria del
# servidor (_CACHE_3D) y un dcc.Store con un contador/token avisa al callback de
# reconstruccion. Asi, mover SOLO los sliders de angulos o de paso de cortes NO
# regenera el volumen (que es lo costoso de construir), y mover los sliders de mu
# no cambia la figura (misma semilla -> misma pieza).

# --- Terceros ---
import numpy as np
import plotly.graph_objects as go
from dash import Input, Output, ctx, no_update

# --- Locales ---
from config import TAMANO_VOLUMEN
from core.phantom_3d import crear_phantom_3d
from core.reconstruction_3d import reconstruir_volumen
from core.acquisition import generar_sinograma
from core.metrics import calcular_metricas


_CACHE_3D = {"volumen": None, "version": 0}

# Colores (coherentes con el perfil de corte del Modo 2D).
_COLOR_PIEZA = "#9aa4b4"   # phantom original (gris suave)
_COLOR_RECON = "#36b6d6"   # reconstruccion (acento)
_COLOR_CAJA = "#4a5364"    # aristas de la caja contenedora


# ---------------------------------------------------------------------------
# Helpers de presentacion
# ---------------------------------------------------------------------------
def _aristas_caja(n):
    # Devuelve las 12 aristas del cubo [0, n]^3 como tres listas (x, y, z) para
    # una sola traza Scatter3d. Se separan los segmentos con None para que Plotly
    # no una aristas que no son contiguas.
    aristas = [
        # Base inferior (z = 0)
        ((0, 0, 0), (n, 0, 0)), ((n, 0, 0), (n, n, 0)),
        ((n, n, 0), (0, n, 0)), ((0, n, 0), (0, 0, 0)),
        # Base superior (z = n)
        ((0, 0, n), (n, 0, n)), ((n, 0, n), (n, n, n)),
        ((n, n, n), (0, n, n)), ((0, n, n), (0, 0, n)),
        # Aristas verticales
        ((0, 0, 0), (0, 0, n)), ((n, 0, 0), (n, 0, n)),
        ((n, n, 0), (n, n, n)), ((0, n, 0), (0, n, n)),
    ]
    xs, ys, zs = [], [], []
    for p0, p1 in aristas:
        xs += [p0[0], p1[0], None]
        ys += [p0[1], p1[1], None]
        zs += [p0[2], p1[2], None]
    return xs, ys, zs


def _nivel_iso(volumen):
    # Nivel de la isosuperficie: punto medio entre el "fondo" y la "pieza",
    # estimados con percentiles robustos para que picos/artefactos de la FBP no
    # desplacen el umbral y oculten la pieza.
    lo = float(np.percentile(volumen, 5))
    hi = float(np.percentile(volumen, 99))
    return lo + 0.5 * (hi - lo)


def _figura_volumen(volumen, color, mostrar_pieza=True) -> go.Figure:
    # Renderiza el volumen como una isosuperficie dentro de la caja contenedora.
    # La caja (aristas) se dibuja SIEMPRE; la pieza solo si mostrar_pieza=True
    # (en el modo oculto la pieza se esconde y queda visible solo la caja).
    n = volumen.shape[0]
    trazas = []

    if mostrar_pieza:
        # Mallas de coordenadas en el MISMO orden de ejes que el volumen
        # (eje 0 = z, eje 1 = y, eje 2 = x), para que cada valor case con su
        # posicion al aplanar.
        zz, yy, xx = np.mgrid[0:n, 0:n, 0:n]
        iso = _nivel_iso(volumen)
        trazas.append(
            go.Isosurface(
                x=xx.flatten(), y=yy.flatten(), z=zz.flatten(),
                value=volumen.flatten(),
                isomin=iso, isomax=float(volumen.max()),
                surface_count=1,
                colorscale=[[0, color], [1, color]],
                showscale=False,
                opacity=0.9,
                caps=dict(x_show=False, y_show=False, z_show=False),
            )
        )

    # Caja contenedora (wireframe).
    cx, cy, cz = _aristas_caja(n)
    trazas.append(
        go.Scatter3d(
            x=cx, y=cy, z=cz, mode="lines",
            line=dict(color=_COLOR_CAJA, width=2),
            hoverinfo="skip", showlegend=False,
        )
    )

    fig = go.Figure(data=trazas)
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        scene=dict(
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            zaxis=dict(visible=False),
            bgcolor="rgba(0,0,0,0)",
            aspectmode="cube",
            camera=dict(eye=dict(x=1.5, y=1.5, z=1.1)),
        ),
    )
    return fig


def _figura_heatmap(datos, colorscale) -> go.Figure:
    # Heatmap "limpio" para los visores 2D (corte axial y sinograma), igual estilo
    # que el Modo 2D: sin ejes, fondo transparente.
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


# ---------------------------------------------------------------------------
# Registro de callbacks
# ---------------------------------------------------------------------------
def registrar_callbacks_3d(app):

    # 1) Semilla aleatoria: se renueva al cambiar la forma o al "Generar nueva".
    @app.callback(
        Output("store-seed-3d", "data"),
        Input("dropdown-forma-3d", "value"),
        Input("btn-generar-3d", "n_clicks"),
    )
    def _nueva_semilla_3d(_forma, _n_generar):
        return int(np.random.randint(0, 2**31 - 1))

    # 2) Volumen: se recalcula al cambiar forma, mu o semilla. Lo cachea en el
    #    servidor y publica un token para disparar la reconstruccion. NO emite la
    #    figura del phantom aqui: de eso se encarga el callback 3 (visibilidad).
    @app.callback(
        Output("store-token-3d", "data"),
        Input("dropdown-forma-3d", "value"),
        Input("slider-mu-pieza-3d", "value"),
        Input("slider-mu-fondo-3d", "value"),
        Input("switch-oculto-3d", "value"),
        Input("store-seed-3d", "data"),
    )
    def _actualizar_volumen(forma, mu_pieza, mu_fondo, oculto, semilla):
        volumen = crear_phantom_3d(
            TAMANO_VOLUMEN, forma=forma, mu_fondo=mu_fondo, mu_pieza=mu_pieza,
            posicion_aleatoria=bool(oculto), semilla=semilla,
        )
        _CACHE_3D["volumen"] = volumen
        _CACHE_3D["version"] += 1
        return _CACHE_3D["version"]

    # 3) Figura del phantom 3D + modo oculto. Construye la isosuperficie desde el
    #    volumen cacheado. En modo oculto se muestra solo la caja; "Revelar"
    #    destapa la pieza. Misma logica de disparo que el modo oculto 2D.
    @app.callback(
        Output("graf-phantom-3d", "figure"),
        Output("meta-vol-3d", "children"),
        Input("store-token-3d", "data"),
        Input("switch-oculto-3d", "value"),
        Input("btn-revelar-3d", "n_clicks"),
        Input("btn-generar-3d", "n_clicks"),
    )
    def _figura_phantom_3d(_token, oculto, _n_revelar, _n_generar):
        volumen = _CACHE_3D["volumen"]
        if volumen is None:
            return no_update, no_update

        # En modo oculto la pieza queda escondida, salvo que se acabe de pulsar
        # "Revelar".
        mostrar = True
        if oculto:
            mostrar = ctx.triggered_id == "btn-revelar-3d"

        n = volumen.shape[0]
        fig = _figura_volumen(volumen, _COLOR_PIEZA, mostrar_pieza=mostrar)
        return fig, f"{n}³ vox"

    # 4) Reconstruccion volumetrica + corte axial + sinograma + metricas.
    #    Se dispara al cambiar el volumen (token), el numero de angulos o el paso
    #    entre cortes. La reconstruccion SIEMPRE muestra la pieza (es la respuesta
    #    del modo oculto).
    @app.callback(
        Output("graf-reconstruccion-3d", "figure"),
        Output("graf-corte-3d", "figure"),
        Output("graf-sino-3d", "figure"),
        Output("stat-rmse-3d", "children"),
        Output("stat-ssim-3d", "children"),
        Output("stat-psnr-3d", "children"),
        Output("bar-rmse-3d", "style"),
        Output("bar-ssim-3d", "style"),
        Output("bar-psnr-3d", "style"),
        Output("meta-recon-3d", "children"),
        Output("meta-corte-3d", "children"),
        Output("meta-sino-3d", "children"),
        Input("store-token-3d", "data"),
        Input("slider-angulos-3d", "value"),
        Input("slider-paso", "value"),
    )
    def _actualizar_reconstruccion_3d(_token, num_angulos, paso):
        volumen = _CACHE_3D["volumen"]
        if volumen is None:
            return (no_update,) * 12

        n = volumen.shape[0]

        # Reconstruccion corte por corte con el paso indicado.
        reconstruccion, indices = reconstruir_volumen(volumen, num_angulos, paso)

        # Corte axial central (la rebanada reconstruida en z = n/2) y el sinograma
        # de ese mismo corte original, para visualizar el pipeline 2D subyacente.
        z_centro = n // 2
        corte_recon = reconstruccion[z_centro]
        sinograma, _ = generar_sinograma(volumen[z_centro], num_angulos)

        fig_recon = _figura_volumen(reconstruccion, _COLOR_RECON, mostrar_pieza=True)
        fig_corte = _figura_heatmap(corte_recon, "gray")
        fig_sino = _figura_heatmap(sinograma, "hot")

        # Metricas sobre TODO el volumen: asi el paso entre cortes (resolucion
        # axial) tambien impacta la calidad medida, no solo la del plano.
        m = calcular_metricas(volumen, reconstruccion)
        rmse_txt = f"{m['rmse']:.3f}"
        ssim_txt = f"{m['ssim']:.2f}"
        psnr_txt = f"{m['psnr']:.1f}"

        # Anchos de las barras (0-100%). RMSE: menor es mejor -> se invierte.
        w_rmse = max(4, min(100, (1 - min(m["rmse"], 0.3) / 0.3) * 100))
        w_ssim = max(0, min(100, m["ssim"] * 100))
        w_psnr = max(0, min(100, m["psnr"] / 40 * 100))

        return (
            fig_recon, fig_corte, fig_sino,
            rmse_txt, ssim_txt, psnr_txt,
            {"width": f"{w_rmse:.0f}%"},
            {"width": f"{w_ssim:.0f}%"},
            {"width": f"{w_psnr:.0f}%"},
            f"{len(indices)} cortes",
            f"z = {z_centro}",
            f"{num_angulos} ang.",
        )
