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
from dash import Input, Output, State, ctx, no_update

# --- Locales ---
from config import TAMANO_VOLUMEN
from core.phantom_3d import crear_phantom_3d
from core.reconstruction_3d import reconstruir_volumen
from core.acquisition import generar_sinograma, proyeccion_en_angulo
from core.metrics import cuantificar_forma, clasificar_metrica


# Extendemos el caché para guardar también la reconstrucción actual
_CACHE_3D = {"volumen": None, "reconstruccion": None, "version": 0}

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
    n = volumen.shape[0]
    trazas = []

    if mostrar_pieza:
        # 1. Creamos las mallas de coordenadas planas en el orden correcto
        zz, yy, xx = np.mgrid[0:n, 0:n, 0:n]
        
        # Aplanamos las matrices para Plotly
        x_flat = xx.flatten()
        y_flat = yy.flatten()
        z_flat = zz.flatten()
        v_flat = volumen.flatten()
        
        iso = _nivel_iso(volumen)
        
        # 2. TRAZA VISUAL: La Isosuperficie (Se queda igual, pero desactivamos su hover problemático)
        trazas.append(
            go.Isosurface(
                x=x_flat, y=y_flat, z=z_flat,
                value=v_flat,
                isomin=iso, isomax=float(volumen.max()),
                surface_count=1,
                colorscale=[[0, color], [1, color]],
                showscale=False,
                opacity=0.9,
                caps=dict(x_show=False, y_show=False, z_show=False),
                hoverinfo="skip",  # Dejamos que la colisión la maneje el Scatter3d
            )
        )
        
        # 3. [NUEVO] COLCHÓN DE CLICS: Traza oculta de alta sensibilidad
        # Filtramos para colocar puntos interactivos únicamente donde la pieza es sólida
        mascara_solida = v_flat >= iso
        
        trazas.append(
            go.Scatter3d(
                x=x_flat[mascara_solida],
                y=y_flat[mascara_solida],
                z=z_flat[mascara_solida],
                mode="markers",
                marker=dict(
                    size=14,              # ¡Marcadores gigantes para que sea imposible fallar el disparo!
                    opacity=0.0,          # Completamente invisibles al ojo humano
                    color=color
                ),
                # Guardamos la Z real en el hover text para el callback de clic
                text=[f"{z}" for z in z_flat[mascara_solida]],
                hoverinfo="text",
                hoverlabel=dict(
                    bgcolor="rgba(30, 41, 59, 0.85)",
                    font_size=13,
                    font_color="white"
                ),
                showlegend=False
            )
        )

    # Caja contenedora (wireframe)
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


def _figura_corte_con_haz(corte, angulo_grados) -> go.Figure:
    # Heatmap del corte (mapa de mu) con la DIRECCION DEL HAZ superpuesta: varias
    # lineas paralelas a 'angulo_grados' que representan los rayos que atraviesan
    # la pieza desde ese angulo. Es la "vista de adquisicion" para ese angulo.
    fig = go.Figure(data=go.Heatmap(z=corte, colorscale="gray", showscale=False))
    n = corte.shape[0]
    c = (n - 1) / 2.0
    th = np.radians(angulo_grados)
    # Direccion a lo largo del rayo y direccion perpendicular (separa los rayos).
    # A th=0 los rayos son verticales (radon integra por columnas) y rotan con th.
    dx, dy = np.sin(th), np.cos(th)
    px, py = np.cos(th), -np.sin(th)
    largo = n  # suficiente para cruzar toda la imagen
    xs, ys = [], []
    for off in np.linspace(-0.42 * n, 0.42 * n, 7):
        x0, y0 = c + off * px - largo * dx, c + off * py - largo * dy
        x1, y1 = c + off * px + largo * dx, c + off * py + largo * dy
        xs += [x0, x1, None]
        ys += [y0, y1, None]
    fig.add_trace(go.Scatter(
        x=xs, y=ys, mode="lines",
        line=dict(color="#36b6d6", width=1.5),
        opacity=0.85, hoverinfo="skip", showlegend=False,
    ))
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", autosize=True,
    )
    # y invertido (rango [n-1, 0]) para mostrar la imagen como los demas visores.
    fig.update_xaxes(visible=False, range=[0, n - 1], constrain="domain")
    fig.update_yaxes(visible=False, range=[n - 1, 0], scaleanchor="x")
    return fig


def _figura_sombra_1d(sombra) -> go.Figure:
    # Perfil 1D de la "sombra": la proyeccion (integral de linea) en un solo
    # angulo. Es una columna del sinograma vista como curva.
    x = np.arange(len(sombra))
    fig = go.Figure(go.Scatter(
        x=x, y=sombra, mode="lines", fill="tozeroy",
        line=dict(color="#e0a64a", width=2),
        fillcolor="rgba(224,166,74,0.15)", hoverinfo="skip",
    ))
    fig.update_layout(
        margin=dict(l=0, r=0, t=8, b=0),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False, autosize=True,
    )
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
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

    # 1b) Posicion de la pieza (aleatoria = escondida). Se desacopla del switch
    #     para lograr "revelar en el sitio":
    #       - Activar el switch (ON)  -> posicion ALEATORIA: arranca el reto.
    #       - Apagar el switch (OFF)  -> NO se toca la posicion (no_update): la
    #         pieza ya esta donde estaba, solo cambia su visibilidad. Asi se
    #         revela exactamente en su sitio real, sin volver al centro.
    #       - Generar nueva / cambiar forma -> la posicion sigue al switch actual.
    @app.callback(
        Output("store-pos-3d", "data"),
        Input("switch-oculto-3d", "value"),
        Input("btn-generar-3d", "n_clicks"),
        Input("dropdown-forma-3d", "value"),
    )
    def _posicion_pieza_3d(oculto, _n_generar, _forma):
        if ctx.triggered_id == "switch-oculto-3d":
            # ON -> aleatoria; OFF -> conservar (revelar en su sitio).
            return True if oculto else no_update
        # Generar nueva o cambiar forma: respeta el estado actual del switch.
        return bool(oculto)

    # 2) Volumen: se recalcula al cambiar forma, mu, posicion o semilla. Lo cachea
    #    en el servidor y publica un token para disparar la reconstruccion. NO emite
    #    la figura del phantom aqui: de eso se encarga el callback 3 (visibilidad).
    @app.callback(
        Output("store-token-3d", "data"),
        Input("dropdown-forma-3d", "value"),
        Input("slider-mu-pieza-3d", "value"),
        Input("slider-mu-fondo-3d", "value"),
        Input("store-pos-3d", "data"),
        Input("store-seed-3d", "data"),
    )
    def _actualizar_volumen(forma, mu_pieza, mu_fondo, pos_aleatoria, semilla):
        volumen = crear_phantom_3d(
            TAMANO_VOLUMEN, forma=forma, mu_fondo=mu_fondo, mu_pieza=mu_pieza,
            posicion_aleatoria=bool(pos_aleatoria), semilla=semilla,
        )
        _CACHE_3D["volumen"] = volumen
        _CACHE_3D["version"] += 1
        return _CACHE_3D["version"]

    # 3) Figura del phantom 3D. El SWITCH controla solo la visibilidad:
    #       ON  -> muestra solo la caja (pieza escondida en su posicion aleatoria).
    #       OFF -> revela la pieza. Como el volumen NO se regenero al apagar
    #              (callback 1b devolvio no_update), la pieza aparece en su sitio real.
    @app.callback(
        Output("graf-phantom-3d", "figure"),
        Output("meta-vol-3d", "children"),
        Input("store-token-3d", "data"),
        Input("switch-oculto-3d", "value"),
    )
    def _figura_phantom_3d(_token, oculto):
        volumen = _CACHE_3D["volumen"]
        if volumen is None:
            return no_update, no_update

        mostrar = not bool(oculto)

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
        Output("stat-dice-3d", "children"),
        Output("stat-iou-3d", "children"),
        Output("stat-area-3d", "children"),
        Output("bar-dice-3d", "style"),
        Output("bar-iou-3d", "style"),
        Output("bar-area-3d", "style"),
        Output("verdict-dice-3d", "children"),
        Output("verdict-dice-3d", "className"),
        Output("verdict-iou-3d", "children"),
        Output("verdict-iou-3d", "className"),
        Output("verdict-area-3d", "children"),
        Output("verdict-area-3d", "className"),
        Output("meta-recon-3d", "children"),
        Output("meta-corte-3d", "children"),
        Output("meta-sino-3d", "children"),
        # Al recalcular todo, la seleccion de corte vuelve al central.
        Output("store-z-3d", "data"),
        Input("store-token-3d", "data"),
        Input("slider-angulos-3d", "value"),
        Input("slider-paso", "value"),
        Input("switch-unir-3d", "value"),
    )
    def _actualizar_reconstruccion_3d(_token, num_angulos, paso, unir_cortes):
        volumen = _CACHE_3D["volumen"]
        if volumen is None:
            return (no_update,) * 19

        n = volumen.shape[0]

        # Reconstruccion corte por corte con el paso indicado.
        reconstruccion, indices = reconstruir_volumen(volumen, num_angulos, paso, unir_cortes=unir_cortes)
        
        # [NUEVO] Guardamos el volumen reconstruido en el caché global para usarlo en los clics
        _CACHE_3D["reconstruccion"] = reconstruccion

        # Por defecto, al recalcular todo, mostramos el corte axial central z = n/2
        z_centro = n // 2
        corte_recon = reconstruccion[z_centro]
        sinograma, _ = generar_sinograma(volumen[z_centro], num_angulos)

        fig_recon = _figura_volumen(reconstruccion, _COLOR_RECON, mostrar_pieza=True)
        fig_corte = _figura_heatmap(corte_recon, "gray")
        fig_sino = _figura_heatmap(sinograma, "hot")

        # Cuantificacion de la forma sobre TODO el volumen (solapamiento 3D de
        # las siluetas, no intensidades).
        m = cuantificar_forma(volumen, reconstruccion)
        dice_txt = f"{m['dice']:.2f}"
        iou_txt = f"{m['iou']:.2f}"
        area_txt = f"{m['area']:.0f}%"

        # Veredicto cualitativo (Buena/Aceptable/Pobre) + clase de color por metrica.
        dice_lbl, dice_cls = clasificar_metrica("dice", m["dice"])
        iou_lbl, iou_cls = clasificar_metrica("iou", m["iou"])
        area_lbl, area_cls = clasificar_metrica("area", m["area"])

        # Anchos de las barras (0-100%, lleno = mejor). El error de area se invierte.
        w_dice = max(4, min(100, m["dice"] * 100))
        w_iou = max(4, min(100, m["iou"] * 100))
        w_area = max(4, min(100, (1 - min(m["area"], 50.0) / 50.0) * 100))

        return (
            fig_recon, fig_corte, fig_sino,
            dice_txt, iou_txt, area_txt,
            {"width": f"{w_dice:.0f}%"},
            {"width": f"{w_iou:.0f}%"},
            {"width": f"{w_area:.0f}%"},
            dice_lbl, f"verdict {dice_cls}",
            iou_lbl, f"verdict {iou_cls}",
            area_lbl, f"verdict {area_cls}",
            f"{len(indices)} cortes",
            f"z = {z_centro}",
            f"{num_angulos} ang.",
            z_centro,
        )

    # 5) Interaccion: clic en el volumen 3D selecciona una rebanada axial. Muestra
    #    ese corte reconstruido, SU sinograma (sobre el volumen original) y guarda
    #    el indice en store-z-3d para que la vista de sombras use el mismo corte.
    @app.callback(
        Output("graf-corte-3d", "figure", allow_duplicate=True),
        Output("meta-corte-3d", "children", allow_duplicate=True),
        Output("graf-sino-3d", "figure", allow_duplicate=True),
        Output("meta-sino-3d", "children", allow_duplicate=True),
        Output("store-z-3d", "data", allow_duplicate=True),
        Input("graf-reconstruccion-3d", "clickData"),
        State("slider-angulos-3d", "value"),
        prevent_initial_call=True,
    )
    def _mostrar_corte_por_clic(clickData, num_angulos):
        # Si no hay interaccion valida o el cache esta vacio, no actualizamos.
        if not clickData or _CACHE_3D["reconstruccion"] is None or _CACHE_3D["volumen"] is None:
            return (no_update,) * 5

        try:
            # Punto de interseccion 3D capturado por Plotly.
            punto = clickData["points"][0]
            z_clicado = punto.get("z", None)
            if z_clicado is None:
                return (no_update,) * 5

            # Coordenada continua -> indice entero del corte, acotado a [0, n-1].
            z_index = int(round(z_clicado))
            n = _CACHE_3D["reconstruccion"].shape[0]
            z_index = max(0, min(z_index, n - 1))

            # Corte reconstruido seleccionado.
            corte_seleccionado = _CACHE_3D["reconstruccion"][z_index]
            fig_corte = _figura_heatmap(corte_seleccionado, "gray")

            # Sinograma del corte SELECCIONADO (sobre el volumen original: es lo
            # que el escaner mediria en esa rebanada).
            sinograma, _ = generar_sinograma(_CACHE_3D["volumen"][z_index], num_angulos)
            fig_sino = _figura_heatmap(sinograma, "hot")

            return (
                fig_corte, f"z = {z_index} (Seleccionado)",
                fig_sino, f"{num_angulos} ang. · z = {z_index}",
                z_index,
            )

        except Exception:
            return (no_update,) * 5

    # 6) Vista de adquisicion: para el corte seleccionado (o el central), dibuja el
    #    corte con la direccion del haz y la "sombra" (proyeccion 1D) del angulo
    #    elegido. Asi se ve como cada angulo aporta una columna al sinograma.
    @app.callback(
        Output("graf-corte-haz-3d", "figure"),
        Output("graf-sombra-3d", "figure"),
        Output("meta-sombra-3d", "children"),
        Output("meta-sombra-perfil-3d", "children"),
        Input("slider-angulo-sombra-3d", "value"),
        Input("store-z-3d", "data"),
        Input("store-token-3d", "data"),
    )
    def _sombra_por_angulo(angulo, z_sel, _token):
        volumen = _CACHE_3D["volumen"]
        if volumen is None:
            return no_update, no_update, no_update, no_update

        n = volumen.shape[0]
        z = n // 2 if z_sel is None else max(0, min(int(z_sel), n - 1))
        corte = volumen[z]  # corte ORIGINAL: es el que proyecta la sombra

        fig_haz = _figura_corte_con_haz(corte, angulo)
        sombra = proyeccion_en_angulo(corte, angulo)
        fig_sombra = _figura_sombra_1d(sombra)

        return (
            fig_haz, fig_sombra,
            f"θ = {angulo}° · z = {z}",
            f"θ = {angulo}° · {len(sombra)} detectores",
        )