# TEORÍA — Física de la Tomografía Computacional (CT)

> Documento de estudio del simulador. Explica **toda la física** detrás del
> proyecto y la conecta con el código, archivo por archivo y línea por línea.
> Materia: **Electricidad y Magnetismo**.

---

## Índice

1. [¿Qué es una tomografía y por qué es un problema de física?](#1-qué-es-una-tomografía)
2. [La base: Ley de Beer-Lambert y el coeficiente de atenuación μ](#2-ley-de-beer-lambert)
3. [El phantom: el mapa de μ (la "verdad")](#3-el-phantom)
4. [La adquisición: proyecciones y la Transformada de Radon](#4-la-transformada-de-radon)
5. [El sinograma: qué es y cómo se lee](#5-el-sinograma)
6. [¿Por qué se gira solo de 0° a 180°?](#6-por-qué-0-a-180)
7. [La reconstrucción: retroproyección y FBP](#7-la-reconstrucción-fbp)
8. [El Teorema del Corte Central (por qué funciona la FBP)](#8-teorema-del-corte-central)
9. [El salto a 3D: cortes axiales apilados](#9-el-salto-a-3d)
10. [Resolución axial: la distancia entre cortes](#10-resolución-axial)
11. [Validación: cuantificar la forma (Dice / IoU)](#11-validación-de-la-forma)
12. [Mapa código ↔ física](#12-mapa-código--física)
13. [Glosario](#13-glosario)

---

## 1. ¿Qué es una tomografía?

**Tomografía** = "imagen por secciones" (del griego *tomos*, corte). El objetivo es
**ver el interior de un objeto sin abrirlo**, reconstruyendo su composición a partir
de medidas tomadas *desde afuera*.

El truco está en la física: un haz de rayos X (radiación electromagnética de alta
energía) **se atenúa** al atravesar la materia. Si medimos cuánto se atenúa el haz
desde **muchos ángulos distintos**, podemos resolver matemáticamente **qué había
dentro** que causó esa atenuación. Eso es la CT.

El pipeline completo, que es el que simula este proyecto, tiene cuatro etapas:

```
   OBJETO              ADQUISICIÓN           RECONSTRUCCIÓN        VALIDACIÓN
  (mapa de μ)   →   (proyecciones/Radon)  →   (FBP / iradon)   →   (Dice/IoU)
   phantom.py         acquisition.py          reconstruction.py     metrics.py
```

---

## 2. Ley de Beer-Lambert

> **Este es el corazón físico del proyecto.** Todo lo demás se construye encima.

Cuando un haz de rayos X con intensidad inicial `I₀` atraviesa un material, **pierde
intensidad** porque el material absorbe y dispersa fotones. La **Ley de
Beer-Lambert** describe cuánto:

$$I = I_0 \, e^{-\int \mu(s)\, ds}$$

Donde:

- `I₀` = intensidad del haz **antes** de entrar al material.
- `I` = intensidad **después** de atravesarlo (lo que mide el detector).
- `μ(s)` = **coeficiente de atenuación lineal**, que depende del material en cada
  punto `s` del recorrido del rayo.
- `∫ μ(s) ds` = la integral de μ **a lo largo de la línea recta** que sigue el rayo.

### ¿Qué es físicamente μ?

El **coeficiente de atenuación lineal** (unidades: 1/longitud) mide *qué tan
fuertemente un material frena los rayos X por unidad de distancia*. Depende de:

- La **densidad** del material (más denso → más μ).
- El **número atómico** de sus elementos (metales, hueso → μ alto).

Ejemplos del mundo real: aire ≈ 0, agua/tejido blando ≈ bajo, hueso ≈ alto,
metal ≈ muy alto. En un CT médico esto se calibra en **unidades Hounsfield (HU)**.

> **En este simulador** μ es un valor adimensional de simulación: `mu_fondo` (medio
> que rodea la pieza) y `mu_pieza` (la pieza, más densa). Lo importante es el
> **contraste** entre ambos: si la pieza no es más densa que el fondo, es invisible.

### El paso clave: de la medida al "dato útil"

El detector mide `I`. Pero lo que nos interesa es la **integral de μ**. Despejándola
de Beer-Lambert (aplicando logaritmo natural):

$$\boxed{\,-\ln\!\left(\dfrac{I}{I_0}\right) = \int \mu(s)\, ds\,}$$

**Esta ecuación es la bisagra de toda la tomografía.** Dice que el logaritmo de la
atenuación medida **es exactamente la integral de μ a lo largo del rayo**. A esa
integral se le llama una **proyección**. Reúne muchas proyecciones (muchos rayos,
muchos ángulos) y tendrás suficiente información para reconstruir μ en todo el plano.

---

## 3. El phantom

**Phantom** = el objeto de prueba "ideal" cuya composición conocemos perfectamente.
Es la **verdad de referencia** (*ground truth*) contra la que luego comparamos la
reconstrucción.

📂 **Dónde vive:** `core/phantom_3d.py` (3D) y `core/phantom.py` (2D).

Un phantom **no es una foto: es un mapa físico de μ**. Cada vóxel (píxel 3D) guarda
el coeficiente de atenuación del material en ese punto:

```python
# core/phantom_3d.py:99-100
volumen = np.full((tamano, tamano, tamano), float(mu_fondo))  # todo es fondo
volumen[mascara] = float(mu_pieza)                            # se "estampa" la pieza
```

- Se crea un volumen lleno con `mu_fondo` (el medio).
- Donde la **máscara** de la forma dice `True`, se sobrescribe con `mu_pieza`.

### La forma de la pieza (geometría analítica)

📂 `shapes/generator_3d.py`. Cada forma se define con su **ecuación matemática** y
devuelve una máscara booleana (`True` = hay pieza):

- **Esfera** (`:43-47`): `(x−cx)² + (y−cy)² + (z−cz)² ≤ r²`
- **Elipsoide** (`:50-60`): `(x/a)² + (y/b)² + (z/c)² ≤ 1`
- **Cilindro** (`:63-71`): un disco en XY extruido a lo largo de Z.
- **Prisma** (`:74-82`): caja rectangular; si los lados son iguales, un cubo.
- **Toroide** (`:85-94`): una "dona" con eje de revolución en Z.
- **Aleatoria** (`:97-152`): técnica de *metaballs* (suma de gaussianas deformadas
  + ruido) para una pieza **amorfa e irregular** — justo lo que pide el enunciado.

### El modo oculto

El enunciado pide que *"la pieza esté escondida"*. Eso se logra en
`core/phantom_3d.py:84-93`: en vez de centrar la pieza, se la coloca en una
**posición aleatoria** dentro de la caja (con un margen para que no toque las
paredes). El usuario no sabe dónde está; solo la tomografía la revela.

---

## 4. La Transformada de Radon

Ahora simulamos el **escáner**: girar la fuente y el detector alrededor del objeto y,
en cada ángulo, disparar muchos rayos paralelos y medir su atenuación.

📂 **Dónde vive:** `core/acquisition.py`.

```python
# core/acquisition.py:30
angulos = np.linspace(0.0, 180.0, num_angulos, endpoint=False)
# core/acquisition.py:34
sinograma = radon(corte, theta=angulos, circle=False)
```

### ¿Qué es una proyección?

Para **un ángulo θ fijo**, lanzamos rayos paralelos que atraviesan el objeto. Cada
rayo, según Beer-Lambert (sección 2), nos da una integral de línea `∫μ dl`. El
conjunto de esas integrales para todos los rayos de ese ángulo es **una proyección**:
es como la "sombra" del objeto vista desde θ.

Matemáticamente, la **Transformada de Radon** `R` toma la función μ(x,y) y devuelve
sus proyecciones a todos los ángulos:

$$p(\theta, t) = \mathcal{R}[\mu](\theta, t) = \int_{L(\theta, t)} \mu(x, y)\, dl$$

donde `L(θ, t)` es la recta a ángulo `θ` y a distancia `t` del centro (la posición en
el detector). **Recuerda:** físicamente `p(θ, t) = −ln(I/I₀)`. La función `radon()`
de scikit-image calcula directamente esas integrales sobre el mapa de μ.

> `circle=False` indica que el objeto puede ocupar toda la imagen (no solo el círculo
> inscrito).

---

## 5. El sinograma

Si apilamos **todas las proyecciones** (una por cada ángulo) una al lado de la otra,
obtenemos una imagen 2D: el **sinograma**.

📂 Se genera en `core/acquisition.py:34` y se visualiza como un mapa de calor en la
app (los visores con colormap `"hot"`).

```
                 SINOGRAMA
        ángulo θ  →  (0°, 1°, 2°, ... 179°)
     ┌─────────────────────────────────────┐
   p │                                       │
   o │         (cada columna es una          │
   s │          proyección completa          │
   i │          a un ángulo dado)            │
   c │                                       │
   i │                                       │
   ó │                                       │
   n └─────────────────────────────────────┘
   en el detector (t)
```

- **Eje horizontal:** el ángulo de proyección θ.
- **Eje vertical:** la posición en el detector `t`.
- **Cada columna** es una proyección completa (la "sombra" a ese ángulo).
- **El brillo** de cada punto = el valor de `∫μ dl` para ese rayo.

### ¿Por qué se llama "sinograma"?

Un punto del objeto que **no esté en el centro** traza, al girar el ángulo, una curva
con forma de **sinusoide** en esta imagen (su distancia al detector varía como
`t = x·cosθ + y·senθ`). De ahí el nombre. El sinograma es **todo lo que el escáner
realmente mide**: a partir de él hay que reconstruir el objeto.

---

## 6. ¿Por qué 0° a 180°?

Notarás que los ángulos van de **0° a 180°**, no hasta 360° (`acquisition.py:30`).
La razón es física:

En geometría de **haz paralelo**, la proyección a un ángulo `θ` y la proyección a
`θ + 180°` recorren **exactamente las mismas líneas**, solo que en sentido contrario.
Como la integral `∫μ dl` no depende del sentido del recorrido, **ambas proyecciones
son idénticas**. Medir más allá de 180° sería **información redundante**.

> **Importante (aclaración del proyecto):** el slider "N.º de ángulos" controla
> *cuántas* proyecciones se toman dentro de esa media vuelta, **no el arco**. Más
> ángulos = muestreo más fino = mejor reconstrucción (in-plane), pero más cómputo.

---

## 7. La reconstrucción (FBP)

Tenemos el sinograma (lo que se mide). Ahora hay que **invertir** el proceso: a partir
de las proyecciones, recuperar el mapa de μ original. Esto es la **reconstrucción**.

📂 **Dónde vive:** `core/reconstruction.py`.

```python
# core/reconstruction.py:35-41
reconstruccion = iradon(sinograma, theta=angulos, filter_name="ramp", circle=False)
```

### Idea 1: Retroproyección (backprojection)

La forma más intuitiva de invertir: tomar cada proyección y **"untarla" de vuelta**
sobre el plano, a lo largo de la dirección en que se midió. Si sumamos las
retroproyecciones de todos los ángulos, donde había mucho material se acumulará
mucho valor, y la silueta del objeto reaparece.

**Problema:** la retroproyección simple produce una imagen **muy borrosa**. Cada
punto se "esparce" con un perfil de `1/r`, emborronando los bordes.

### Idea 2: Filtrado previo (la "F" de FBP)

La solución es **filtrar cada proyección antes de retroproyectarla**. Se aplica un
**filtro rampa** (*ramp filter*): en el dominio de frecuencias, multiplica cada
proyección por `|ω|` (realza las altas frecuencias, que son los bordes y el detalle,
y atenúa las bajas, que son las que causan el borrón).

$$\text{FBP: } \mu(x,y) = \int_0^\pi \underbrace{\big(p(\theta, \cdot) * h\big)}_{\text{proyección filtrada}}(x\cos\theta + y\sin\theta)\; d\theta$$

donde `h` es el filtro rampa. Esto es la **Retroproyección Filtrada (Filtered
Back-Projection, FBP)**, el algoritmo clásico de reconstrucción.

📂 En el código, `reconstruction.py:33` normaliza el nombre del filtro (`"ramp-filter"`
→ `"ramp"`) y `iradon()` hace el filtrado + retroproyección de un solo paso.

---

## 8. Teorema del Corte Central

*(El "por qué" matemático de la FBP — útil para impresionar en la sustentación.)*

El **Teorema del Corte Central** (*Fourier Slice Theorem*) dice:

> La **Transformada de Fourier 1D** de una proyección tomada a un ángulo `θ` es igual
> a un **corte** (una línea que pasa por el origen, a ese mismo ángulo `θ`) de la
> **Transformada de Fourier 2D** del objeto.

En palabras simples: cada proyección nos da **una rebanada** del espectro de
frecuencias del objeto. Si tenemos proyecciones desde muchos ángulos, llenamos el
plano de frecuencias 2D radio a radio, y al hacer la transformada inversa
recuperamos el objeto.

¿Y de dónde sale el **filtro rampa**? Cuando reconstruimos integrando esos cortes
radiales, las frecuencias bajas (cerca del origen) quedan **sobre-representadas**
porque los radios se juntan en el centro. El factor `|ω|` (la rampa) es exactamente
el **Jacobiano** que corrige esa densidad al pasar de coordenadas polares a
cartesianas. Por eso el filtro no es arbitrario: **cae de la matemática**.

---

## 9. El salto a 3D

> **Un volumen no se tomografía "de golpe": se trata como una pila de cortes
> transversales (axiales), y cada corte se reconstruye con el pipeline 2D.**

📂 **Dónde vive:** `core/reconstruction_3d.py`.

Esto es exactamente lo que hace un **CT real de adquisición axial**: el escáner toma
un corte transversal, avanza la camilla, toma el siguiente, y así sucesivamente.
Luego los cortes se apilan para formar el volumen.

### La convención de ejes que lo hace posible

📂 `shapes/generator_3d.py:7-12`. El volumen se indexa como `volumen[z, y, x]`:

- **eje 0 = z** → profundidad / cortes axiales.
- **eje 1 = y** → fila.
- **eje 2 = x** → columna.

La consecuencia genial: **`volumen[z]` es una imagen 2D** (un corte transversal)
**lista para pasarla por Radon**, idéntica al caso 2D. Rebanar en el eje 0 = sacar un
corte transversal.

### El bucle de reconstrucción 3D

```python
# core/reconstruction_3d.py:35-48
indices = list(range(0, n, paso))        # qué cortes reconstruir
for z in indices:
    corte = volumen[z]                                  # 1. rebanada transversal
    sinograma, angulos = generar_sinograma(corte, ...)  # 2. Radon  (sección 4)
    corte_recon = reconstruir_fbp(sinograma, ...)       # 3. FBP    (sección 7)
    reconstruccion[z:z_fin] = corte_recon               # 4. se apila en Z
```

Cada corte recorre **el mismo pipeline 2D completo** (Radon → sinograma → FBP) y
luego se coloca de vuelta en su posición Z. Apilando todos los cortes reconstruidos
se forma el **volumen reconstruido**, que la app dibuja como una **isosuperficie**
(la "cáscara" 3D de la pieza).

---

## 10. Resolución axial

Aquí hay una asimetría física **fundamental** que conviene entender bien:

- La resolución **dentro del corte (plano XY)** la da la tomografía: número de
  ángulos y muestreo del detector. Esa información sale de **Radon + FBP**.
- La resolución **a lo largo de Z (axial)** NO sale de Radon. Sale **solo de cuántos
  cortes mides**. Radon nunca "ve" el eje Z; actúa dentro de cada plano.

📂 El parámetro `paso` en `core/reconstruction_3d.py:8-15` controla esto. Es el
análogo a la **distancia entre cortes / grosor de corte** de un CT real:

- `paso = 1`: se reconstruye **cada** corte → máxima resolución axial, más lento.
- `paso > 1`: se **saltan** cortes → menos resolución axial.

### ¿Por qué se ve "escalonado" y no estirado?

Punto clave (lo discutimos durante el desarrollo): el objeto tiene una **altura fija**
(la caja, `n` vóxeles). Aumentar la distancia entre cortes significa que **caben menos
cortes en esa misma altura** — NO que el objeto se estire. *"Usar menos cortes"* y
*"más distancia entre cortes"* son **lo mismo**. El espacio que queda sin medir es,
literalmente, la parte del objeto de la que **no tienes información**.

Hay dos formas honestas de visualizarlo (switch "Unir rebanadas"):

- **Unido** (`reconstruction_3d.py:42-45`): cada corte medido se **repite** para
  llenar su rebanada (*retención de orden cero*) → el objeto se ve macizo pero
  escalonado/en bloques. Representa *"asumo que cada corte vale para toda su
  rebanada"*.
- **Separado** (`reconstruction_3d.py:46-48`): solo se guarda el plano medido, lo
  demás queda vacío → discos con huecos. Representa *"solo conozco estos planos"*.

En ambos casos, a mayor `paso`, **peor se cuantifica la forma** — que es justamente la
lección física que el enunciado quiere demostrar.

---

## 11. Validación de la forma

El enunciado pide *"comprobar que por la tomografía se logró **cuantificar su
forma**"*. La pregunta no es "¿se parecen los brillos píxel a píxel?" sino
"**¿la silueta reconstruida coincide con la real?**".

📂 **Dónde vive:** `core/metrics.py`.

El procedimiento:

1. **Binarizar** ambos volúmenes (real y reconstruido) en pieza vs fondo, usando el
   método de **Otsu** (`metrics.py`), que halla automáticamente el umbral que mejor
   separa las dos poblaciones de intensidad.
2. **Comparar las dos máscaras** con índices de solapamiento:

   - **Coeficiente de Dice:** $\dfrac{2\,|A \cap B|}{|A| + |B|}$ — 1 = solape perfecto.
   - **IoU (Intersección sobre Unión / Jaccard):** $\dfrac{|A \cap B|}{|A \cup B|}$ —
     más estricto que Dice.
   - **Error de área (%):** cuánto se desvía el tamaño reconstruido del real.

Estas métricas **sí responden a la física del experimento**: con muchos ángulos y
cortes finos, Dice/IoU se acercan a 1 (la forma se recuperó); con pocos ángulos o
cortes muy espaciados, caen (la forma se perdió).

---

## 12. Mapa código ↔ física

| Concepto físico | Dónde está en el código |
|---|---|
| Ley de Beer-Lambert (mapa de μ) | `core/phantom_3d.py:99-100` |
| Forma de la pieza (geometría) | `shapes/generator_3d.py` |
| Pieza escondida (posición aleatoria) | `core/phantom_3d.py:84-93` |
| Transformada de Radon (proyecciones) | `core/acquisition.py:34` |
| Barrido de 0° a 180° | `core/acquisition.py:30` |
| Sinograma | salida de `core/acquisition.py` |
| Retroproyección filtrada (FBP) | `core/reconstruction.py:35-41` |
| Filtro rampa | `core/reconstruction.py:33` |
| 3D = pila de cortes axiales | `core/reconstruction_3d.py:35-48` |
| Convención de ejes `volumen[z,y,x]` | `shapes/generator_3d.py:7-12` |
| Resolución axial / distancia entre cortes | `core/reconstruction_3d.py:8-15` |
| Cuantificación de la forma (Dice/IoU) | `core/metrics.py` |

---

## 13. Glosario

- **μ (coeficiente de atenuación lineal):** qué tanto frena un material a los rayos X
  por unidad de longitud. Más denso → más μ.
- **Atenuación:** pérdida de intensidad del haz al atravesar materia (Beer-Lambert).
- **Proyección:** el conjunto de integrales `∫μ dl` medidas a un ángulo dado (la
  "sombra" del objeto a ese ángulo).
- **Transformada de Radon:** la operación que convierte el objeto (μ) en todas sus
  proyecciones.
- **Sinograma:** imagen 2D que apila todas las proyecciones (posición × ángulo). Es lo
  que el escáner realmente mide.
- **Corte axial (transversal):** una rebanada 2D del volumen perpendicular al eje Z.
- **Retroproyección:** "untar" cada proyección de vuelta sobre el plano para
  reconstruir; produce imagen borrosa por sí sola.
- **FBP (Filtered Back-Projection):** retroproyección + filtro rampa = reconstrucción
  nítida. Algoritmo clásico de CT.
- **Filtro rampa:** filtro `|ω|` que compensa el borrón de la retroproyección; surge
  del Teorema del Corte Central.
- **Teorema del Corte Central:** la FT 1D de una proyección = un corte radial de la
  FT 2D del objeto. Base teórica de la FBP.
- **Resolución axial:** nivel de detalle a lo largo de Z; depende de la distancia
  entre cortes, no de Radon.
- **Dice / IoU:** índices de solapamiento entre la silueta real y la reconstruida.
- **Phantom:** objeto de prueba con μ conocido; sirve de verdad de referencia.
- **Isosuperficie:** superficie 3D que une todos los puntos con un mismo valor; se usa
  para dibujar la "cáscara" de la pieza reconstruida.
</content>
</invoke>
