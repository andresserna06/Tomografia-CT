# callbacks_3d.py
# Logica reactiva del Modo 3D.
# Cambios respecto a la version 2D:
#   - Se implementa go.Volume para renderizar el Phantom y la Reconstruccion.
#   - El sinograma muestra unicamente el corte transversal central (Z/2) en 2D.
#   - El perfil de corte extrae la fila central de la rebanada Z central.
#   - Se asume un tamano de volumen menor (ej. 128) para mantener rendimiento.

# --- Terceros ---
import numpy as np
import plotly.graph_objects as go
from dash import Input, Output, State, ctx, no_update

# --- Locales ---
# Nota: Configurar TAMANO_VOLUMEN = 128 en config.py
from config import TAMANO_IMAGEN 
from core.phantom import crear_phantom_3d
# Asumimos que tienes/creaste una version 3D de la adquisicion
from core.acquisition import generar_sinograma_3d 
from core.reconstruction import reconstruir_fbp_3d
from core.metrics import calcular_metricas


_CACHE = {"phantom": None, "version": 0}


# ---------------------------------------------------------------------------
# Helpers de presentacion
# ---------------------------------------------------------------------------

def _figura_visor_2d(datos, colorscale: str) -> go.Figure:
    # Heatmap 2D clasico (utilizado para el sinograma central)
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


def _figura_visor_3d(vol, colorscale: str) -> go.Figure:
    z, y, x = np.mgrid[0:vol.shape[0], 0:vol.shape[1], 0:vol.shape[2]]
    
    # [CAMBIO Visual 1]
    # Antes: umbral_min = np.min(vol) + 0.05
    # Ahora: Bajamos el umbral mínimo drásticamente.
    # Al poner un isomin muy bajo (ej: 0.1), Plotly dibujará una superficie
    # alrededor de la simulación de fondo (tu contenedor, que es mu=0.4).
    isomin_contenedor = 0.1 
    
    fig = go.Figure(data=go.Volume(
        x=x.flatten(), y=y.flatten(), z=z.flatten(),
        value=vol.flatten(),
        # [MODIFICADO] Bajamos el mínimo para ver el contenedor (la "caja")
        isomin=isomin_contenedor,
        isomax=np.max(vol),
        # [CAMBIO Visual 2]
        # Antes: opacity=0.15
        # Ahora: Subimos opacidad para que el contenedor tenga "sustancia",
        # pero Plotly Volume dibujará capas translúcidas para ver el interior.
        opacity=0.4,
        # [CAMBIO Visual 3]
        # Antes: surface_count=6
        # Ahora: Subimos el número de capas superficiales. Esto define mejor
        # las diferentes densidades (la pared de la caja vs la esfera).
        surface_count=15, # Esto puede aumentar un poco el tiempo de render
        colorscale=colorscale,
        showscale=False
    ))
    
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        scene=dict(
            xaxis=dict(visible=False, showbackground=False),
            yaxis=dict(visible=False, showbackground=False),
            zaxis=dict(visible=False, showbackground=False),
            bgcolor="rgba(0,0,0,0)",
            # [NUEVO] Forzamos a que el aspecto sea un cubo que llene el espacio
            aspectmode='cube',
            # [MODIFICADO] Acercamos la cámara (zoom in). 
            # Antes estaba en 1.5, al bajarlo a 1.2 (o 1.1) se verá más grande.
            camera=dict(eye=dict(x=1.2, y=1.2, z=1.2)) 
        ),
        autosize=True,
    )
    return fig


def _figura_perfil_3d(original, reconstruida) -> go.Figure:
    # Perfil 1D: la fila central de la REBANADA central en Z.
    z_mid = original.shape[0] // 2
    y_mid = original.shape[1] // 2
    x = np.arange(original.shape[2])
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=original[z_mid, y_mid, :], mode="lines",
                             line=dict(color="#9aa4b4", width=2), name="original"))
    fig.add_trace(go.Scatter(x=x, y=reconstruida[z_mid, y_mid, :], mode="lines",
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

    # 1) Semilla aleatoria
    @app.callback(
        Output("store-seed", "data"),
        Input("dropdown-forma", "value"),
        Input("btn-generar", "n_clicks"),
    )
    def _nueva_semilla(_forma, _n_generar):
        return int(np.random.randint(0, 2**31 - 1))

    # 2) Phantom 3D: Generacion volumetrica pesada cacheada
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
        # En 3D se sugiere TAMANO_VOLUMEN = 128 (en vez de 256)
        TAMANO_VOLUMEN = 128 
        phantom = crear_phantom_3d(
            tamano=TAMANO_VOLUMEN, forma=forma, mu_fondo=mu_fondo, 
            mu_pieza=mu_pieza, posicion_aleatoria=bool(oculto), semilla=semilla,
        )
        _CACHE["phantom"] = phantom
        _CACHE["version"] += 1
        
        # colorscale "Blues" o "Viridis" suele verse mejor en volumenes 3D que "gray"
        return _CACHE["version"], _figura_visor_3d(phantom, "Blues")

    # 3) Sinograma + reconstruccion 3D + metricas + perfil.
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
        # Opcional: Input("slider-step-z", "value") para controlar la resolucion Z
    )
    def _actualizar_reconstruccion(_token, num_angulos, step_z=2):
        phantom = _CACHE["phantom"]
        if phantom is None:
            return (no_update,) * 10

        # Adquisicion y reconstruccion volumetrica
        sinograma_3d, angulos = generar_sinograma_3d(phantom, num_angulos)
        reconstruccion_3d = reconstruir_fbp_3d(sinograma_3d, angulos, step_z=step_z)

        # Para el sinograma, extraemos solo el corte central para visualizar en 2D
        z_mid = sinograma_3d.shape[0] // 2
        fig_sino = _figura_visor_2d(sinograma_3d[z_mid, :, :], "hot")
        
        # Renderizamos la reconstruccion volumetrica
        fig_recon = _figura_visor_3d(reconstruccion_3d, "gray")
        fig_perfil = _figura_perfil_3d(phantom, reconstruccion_3d)

        # Las metricas (skimage.metrics) calculan automaticamente en N-dimensiones
        m = calcular_metricas(phantom, reconstruccion_3d)
        
        rmse_txt = f"{m['rmse']:.3f}"
        ssim_txt = f"{m['ssim']:.2f}"
        psnr_txt = f"{m['psnr']:.1f}"

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
        # En 3D quiza necesites mas altura para que el cubo no se vea aplastado
        base = {"height": "400px", "width": "100%"} 
        if not oculto:
            return {**base, "display": "block"}
        if ctx.triggered_id == "btn-revelar":
            return {**base, "display": "block"}
        return {**base, "display": "none"}