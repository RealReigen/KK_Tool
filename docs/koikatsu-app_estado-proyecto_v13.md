# Proyecto: KK_Tool — gestión/edición masiva de cards de Koikatsu (KK)
### Documento de estado v13 (acumulativo y depurado; código KK_Tool v0.5.4)

Sirve para que otro chat/IA pueda continuar sin repetir trabajo. Cada versión nueva debe incluir TODO lo vigente de esta más lo nuevo (no solo el delta). Marcas: ✅ verificado con datos/código reales · 🟡 hipótesis o aproximación sin verificar · ❓ pendiente.

**Novedades desde la v7 (detalle en el Historial, sección 8):** v0.4.2 donar + convertir a futa en una acción · v0.4.3 reseteo de huesos genitales · v0.5.0 buscador, orden y filtros por atributos · v0.5.1/v0.5.2 tamaño del pene compensado por la altura (hueso + slider) · v0.5.3 pestaña «Reparar pene (futas)» · v0.5.4 «Female → Futa» con casillas (checklist). El problema de las animaciones H rotas tras convertir a futa está **resuelto en lo que depende de la app**; lo que queda (algo de clipping) ocurre también con las cards por defecto.

**Descubrimientos clave (lo más valioso de este proyecto; detalle en la sección 3):**
1. Una futa = `sex=0` + 4 entradas de plugins en `KKEx` (`IsTrap`, uncensor, `Bulge`, `MaleHeightEnabled`).
2. El **pene hereda la escala del cuerpo**: la raíz del pene en ABMX es el hueso `cm_J_dan100_00`; la altura total vive en `cf_n_height` (también en cards male) y en el **slider 0 de altura**.
3. **Modelo medido: escala del cuerpo = 0.9 + 0.2 × slider de altura** (±10 % entre 0 y 1). El slider admite valores fuera de 0..1 (p. ej. −0.7307) y siguen escalando.
4. Una card male de fábrica **no tiene entrada ABMX ni uncensor**: «tamaño perfecto» = ningún hueso tocado. En ABMX **un hueso ausente = valores por defecto**.
5. Causa real del síntoma «la female anima en el aire»: futas bajas ⇒ pene encogido. Compensando el pene con `referencia / altura_total` las escenas H mejoran claramente (confirmado por el usuario); el clipping restante es un límite del juego (también con cards por defecto).
6. Los huesos `cf_d_kokan`/`cf_j_kokan` modificados en una female deforman el pene al convertirla (se resetean).

---

## 0. Cómo arrancar un chat nuevo
1. Dirígete al usuario como **"goat"** al principio de cada mensaje (canario anti-degradación, regla 4).
2. Pide: este `.md` + el zip del código (`KK_Tool_v0_5_4.zip`) **o, si el repositorio de GitHub es público, su URL** (el sandbox llega a github.com: `git clone` y leer solo los módulos necesarios, para gastar menos tokens) y, si hay que probar, una card female, una futa y las cards de referencia (sección 3, «Cards de referencia»).
3. `pip install kkloader send2trash pillow --break-system-packages` (si da `403 host_not_allowed`, es bloqueo de red de ese chat: avisar al usuario).
4. Probar la GUI en el sandbox: `apt-get install -y python3-tk xvfb imagemagick`; `xvfb-run -a -s "-screen 0 1250x760x24" python3 script.py`; captura con `import -window root /tmp/x.png`. Los scripts de prueba deben usar `App(Settings(ruta_temporal))` para no ensuciar el `settings.json` real.
5. `/bin/sh` del sandbox no expande llaves ni admite `<( )`; usar `bash -c`.
6. **No hay suite de tests guardada** en el zip: los scripts de prueba usados hasta ahora vivían en `/tmp` y se pierden. Si se hacen cambios, reconstruir pruebas con las cards de referencia (sección 7 propone guardarlas en `tests/`).
7. Al editar código con `str.replace` desde Python, **usar `assert old in texto`** antes de reemplazar: un reemplazo silencioso que no coincide dejó una función sin actualizar (v0.5.2) y solo se vio al ejecutar.

## 1. Usuario y reglas de trabajo
- Edita muchas cards de Koikatsu; entiende el dominio (mods, sliders, bonemods) pero **no programa**: él dirige, la IA ejecuta. Habla español, responder en español. Windows, proyecto en `C:\Games\KK_Tool`, ejecuta con `python -m kk_tool` (`abrir_programa.bat`). Quiere interfaz gráfica.
- Juega con **Better Repack + HF Patch + kPlug**. En la escena H (Free H) tiene clipping y animaciones «en el aire» también con las cards por defecto.
- Intentos anteriores acabaron en "un desastre" que se rompía con cualquier cambio: **modularidad ante todo**.
- **Cómo pedirle experimentos:** pasos numerados, cortos y concretos («abre X, cambia solo Y, guarda con otro nombre, súbela»). Una petición abstracta («necesito medir…») no la entendió; cuando se le dio una receta, él mismo diseñó y midió bien (midió el pene en Paint con la misma cámara).

Reglas (mantener siempre):
1. Código limpio y modular: una función = un módulo; no mezclar todo en un archivo grande.
2. Iteración incremental: verificar que lo nuevo no rompe lo anterior.
3. Al llegar al 90 % de créditos (o si lo pide), generar un `.md` como este, acumulativo.
4. Canario: empezar **cada** mensaje con "goat".
5. Ser honesto sobre lo verificado vs. lo supuesto (✅ / 🟡 / ❓). Si una prueba no ejercita lo que se quiere probar (como la v0.5.1 con una card de altura por slider), decirlo.
6. Al entregar archivos de prueba, decir exactamente qué campos se cambiaron y cuáles no.
7. Los originales del usuario **nunca se modifican**; probar siempre sobre copias. Las herramientas nuevas escriben **copias** (carpeta de salida) y no sobrescriben.
8. Entregar el proyecto como `.zip` (carpeta `KK_Tool`) que se descomprime encima de la instalación; **sin `settings.json`** (no pisarlo), sin `__pycache__`, sin archivos sueltos. Solo el `.md` más reciente en `docs/`.

## 2. Qué hace el proyecto
App Python (tkinter) para trabajar en masa con cards de **Koikatsu original (KK)** (no Party/Sunshine). Las cards del usuario vienen de KK Sunshine convertidas a KK, con mods (zipmods de ropa, headmods, bodymods, uncensor, bonemods…).

Pestañas implementadas:
1. **Leer datos:** lista de cards (nombre, sexo, tipo female/male/futa, plugins, altura, fecha, pene efectivo, categorías de altura/pecho…), visor de portada, papelera, columnas/divisores redimensionables, **búsqueda/orden/filtros (sección 5)**.
2. **Female → Futa:** (lista con **casillas ☐/☑**, v0.5.4: marcar es independiente de la selección del visor; se convierten las marcadas, incluidas las ocultas por un filtro) convierte cards female a futa (male + `IsTrap`) de forma atómica, resetea huesos genitales y fija el tamaño del pene. Salida en `<salida>/male/`, **repitiendo la estructura de subcarpetas de la entrada**.
3. **Donante → Receptores:** crea copias de las receptoras con el cuerpo de una card donante (3 modos), opcionalmente convirtiéndolas a futa. Renombra la card y estampa una franja gris en la portada.
4. **Reparar pene (futas):** corrige el tamaño del pene de futas YA hechas (copias en `<salida>/reparadas/`).

Herramientas comunes: carpetas por pestaña (botón «Carpetas…», recuerdan en `settings.json`), «Actualizar», «Enviar a papelera» (Supr), registro con log en `<salida>/log.txt`. Los lotes usan hilo + cola; un fallo no detiene el lote.

Fuera de alcance por ahora: ropa/accesorios (`Coordinate`), detección de mods faltantes, clipping de las escenas H (límite del juego).
Visión de uso: apuntar la app directamente a `chara/female` y `chara/male` del juego; más pestañas con distribuciones distintas (el visor `CardPreview` debe seguir siendo reutilizable).

## 3. Datos técnicos importantes ✅

### Librería y formato
- Base: **`kkloader`** (v0.1.24). Todo el trabajo es sobre los datos serializados tras el `IEND` del PNG; Python puro. Dependencias de la app: `kkloader`, `send2trash`, `pillow` (franja de portada); `instalar.bat` las instala.
- Bloques de la card: `Custom` (cara/cuerpo/pelo; `shapeValueBody` tiene 44 sliders, índice 0 = altura), `Coordinate`, `Parameter`, `Status`, `KKEx` (datos de plugins BepInEx). La portada es el PNG inicial (≈252×352).
- Uso básico:
  ```python
  from kkloader import KoikatuCharaData
  from kkloader.KoikatuCharaData import KKEx
  KKEx.LZ4_UNPACK = True          # ANTES de .load()
  k = KoikatuCharaData.load("card.png"); k["Parameter"]["nickname"] = "X"; k.save("out.png")
  ```
- Avisos de API: `.prettify()` imprime y devuelve `None`. **`k["Parameter"]` admite `p["campo"]` pero NO `.get()`** (usar helper `_get` de `readers/summary.py`). `k["KKEx"].data` sí es un dict normal. `Parameter.sex`: 1 = female, 0 = male. `k.blocks` no existe.
- **`KKEx.LZ4_UNPACK = True`** hace que `boneData` (ABMX), `breastphysicscontroller.DynamicBoneParameter` y `marco.authordata.Authors` salgan como listas Python (se recomprimen al guardar). Cada hueso: `[nombre, [[escala_xyz, largo, offset_pos_xyz, offset_rot_xyz]], grupo]` (grupo = 1 en todos los vistos).
- `KKEx.data`: clave = GUID del plugin, valor `[version_int, {campo: valor}]`. **Si un plugin no se usa, su clave no existe**: activarlo = crear la entrada entera (verificado). La entrada ABMX (`KKABMPlugin.ABMData`) es `[2, {"boneData": [...]}]`.
- Re-guardar no da archivos idénticos byte a byte (LZ4 recomprimido distinto), pero sí **lógicamente idénticos**. Criterio de validación: igualdad lógica tras recargar. El juego/maker abre bien las cards guardadas por la app.
- **Los sliders se guardan como float de 32 bits**: −0.7307 se lee como −0.730677…; al comparar valores, redondear (a 4 decimales). Una card puede pesar mucho (Gwen 18,8 MB; Baek Ji Min 4,2 MB): cada lectura abre la card entera.

### Futa / trap
El flag futa **no** está en `Parameter`; está en `KKEx`. Una futa = `sex=0` + estas entradas:

| Plugin (clave en `KKEx.data`) | Valor en la futa de referencia |
|---|---|
| `marco.becometrap` | `[1, {"IsTrap": True, "IdleAnimation": None}]` — el check "is futa" del juego |
| `com.deathweasel.bepinex.uncensorselector` | `[2, {"BodyGUID": "bp.sac_clit2", "PenisGUID": "BP_SoS", "BallsGUID": None, "DisplayPenis": True, "DisplayBalls": False}]` |
| `Bulge` | `[1, {"EnableBulge": 2, "BulgeSize": 0.5}]` — **2 = desactivado** |
| `kokaiinum.KKExpandMaleMaker` | `[1, {"MaleHeightEnabled": True}]` |

- El uncensor guarda el **GUID interno**, no el texto del desplegable (Body "[Female] BP Clit 2 Game" = `bp.sac_clit2`; Penis "BP SoS" = `BP_SoS`). Un GUID mal escrito no da error al guardar, pero el juego no encuentra el mod.
- **Decisión de diseño:** la app solo soporta la vía **male (`sex=0`) + `IsTrap`**, guardada como male. El usuario hace TODAS sus futas convirtiendo cards female.
- **Decisiones cerradas:** `Bulge` **siempre desactivado (`EnableBulge = 2`)**, creando la entrada si falta; `DisplayBalls` **siempre `False`**. Es lo que hace el preset.
- **Conversión atómica** (`editors/futa.py::apply_futa`, preset `futa_bp_sos` en `config/presets.json`): aplica todo a la vez y **no toca sliders ni otros plugins** (verificado: los otros 24 plugins de Gwen quedaron idénticos; coincide campo a campo con la futa de referencia). Solo toca de los huesos ABMX los genitales (reseteo) y el del pene (tamaño). Tras guardar, la app relee y comprueba que queda como `futa`, que el pene tiene el tamaño de referencia, que no quedan huesos genitales y que la altura (slider + hueso) coincide con la anterior; lo anota en el log. `apply_futa` devuelve `(huesos_reseteados, texto_pene)`.
- **Detección** (`readers/summary.py::classify`): indicadores `IsTrap`, `PenisGUID is not None`, `DisplayPenis`. `sex=0` y los tres → `futa`; alguno pero no todos (o `sex=1` con alguno) → `futa incompleta`; ninguno → `male`/`female`. Las `futa` completas se omiten en la conversión; las incompletas se completan.

### Genitales: huesos de la entrepierna (v0.4.3) ✅
El pene sale aplastado/deformado cuando los huesos de la entrepierna de la female vienen modificados. Verificado con una card real (Yuan Zhu, `KK_378199.png`): `cf_d_kokan` escala [0.661, 1.411, 1.0] y `cf_j_kokan` [0.468, 1.194, 0.855] (`kokan` = entrepierna; el pene del uncensor cuelga de ahí). **Solución:** `apply_futa` quita de `boneData` los huesos de `reset_huesos` del preset (hoy: `cf_d_kokan`, `cf_j_kokan` ✅ confirmados en la card; `cf_d_ana`, `cf_j_ana` 🟡 nombres por conocimiento general, no vistos en ninguna card — si no existen no pasa nada). El resto de huesos y sliders no se toca. La **donación** sustituye los huesos `CUERPO`, que incluyen `kokan` del donante (female): si la receptora acaba con `sex=0`, tras donar se vuelven a resetear (`verify_donation` lo tiene en cuenta con `drop_bones`). A una receptora que sigue female **no** se le toca nada. Para desactivarlo: `"reset_huesos": []` en `presets.json`.
- Importante: este reseteo **no** era la causa del síntoma de las animaciones en el aire (eso fue el tamaño del pene, siguiente apartado). Sigue siendo válido para la deformación.

### Tamaño del pene (v0.5.1 → v0.5.3) ✅ medido; resultado confirmado por el usuario en el juego
**Síntoma:** tras convertir a futa, en escenas H a veces un personaje queda muy lejos del otro y la female anima en el aire. **Causa:** el pene cuelga del cuerpo y hereda su escala; un cuerpo pequeño ⇒ pene corto, y las animaciones están hechas para el tamaño de la male de referencia.

**Datos medidos (en este orden se descubrieron):**
1. Card male de muestra (Kashiwagi Sousuke, `Koikatu_M_20261003001216400…png`, slider 0.6): **sin entrada ABMX ni uncensor**, sin ningún dato de tamaño de pene en `Custom` ni `Parameter` → su tamaño «perfecto» es el de fábrica a esa altura; no hay un número que copiar.
2. Copia editada por el usuario en el maker (`small_Kashiwagi_Sousuke.png`: altura total a la mitad + pene ×2): solo aparece la entrada ABMX con **`cf_n_height = [0.5, 0.5, 0.5]`** (altura total; el hueso conserva el nombre `cf_` en una card male) y **`cm_J_dan100_00 = [2.0, 2.0, 2.0]`** (raíz del pene, largo 1.0, offsets 0, grupo 1). Ningún slider cambió.
3. El **slider de altura (`shapeValueBody[0]`) también escala el pene**: el usuario midió en pantalla (misma cámara y distancia, Paint) el pene de una misma card (Baek Ji Min) con slider 0.6 y −0.7307: **largo 75 vs 55 px, ancho 20 vs 15 px** → ratio 0.73–0.75 (error ±1–2 px). Las dos cards solo difieren en el slider 0.
4. Modelo ajustado: **`escala_cuerpo = 0.9 + 0.2 × slider`** (slider 0 → 0.9, 0.5 → 1.0, 1 → 1.1, −0.7307 → 0.754). Predice 0.739 (medido 0.733 largo / 0.75 ancho). 🟡 Sale de **una sola pareja de alturas** más el supuesto de que 0.5 es neutro; la linealidad en otros valores no está comprobada.

**Solución** (`editors/penis_size.py`):
- `altura_total = (hueso cf_n_height, media xyz; 1.0 si no hay) × escala_slider(slider 0)`.
- Escala del hueso del pene = `tamaño_referencia / altura_total` (xyz iguales); **referencia por defecto = pene de la male de muestra = escala_slider(0.6) = 1.02** (`presets.json → pene.tamano_referencia: null` = usar esa; se puede fijar un número; `compensar_altura: false` desactiva todo).
- Si la altura ya es la de referencia no se escribe nada (y no se crea la entrada ABMX); si el resultado es 1.0 se **quita** el hueso (ausente = por defecto). Idempotente. Sobrescribe cualquier escala de pene previa (es lo pedido).
- Ejemplos: slider −0.7307 → pene ×1.353 · slider 0 → ×1.133 · slider 0.6 → nada · slider 1.0 → ×0.927 · hueso 0.5 + slider 0.6 → ×2.0 (exacto lo que hizo el usuario a mano).
- Config en `config/medidas.json` (`altura_slider.base/pendiente`, `referencia_slider` 0.6, `pene_ok` [0.95, 1.05]), leída por `readers/measures.py` (con valores de fábrica si el JSON falta o está roto).

**Dónde se aplica:** `apply_futa` (conversión) y la donación: tras donar a una receptora que acaba `sex=0`, si hubo que convertirla a futa o el modo copia la altura (`"ALTURA"` en `huesos`: modo `total`), se recalcula con la altura FINAL; `sinaltura`/`pechos` sobre una futa que ya lo era no tocan el pene. Verificación tras guardar: `verify_penis_size` (tolerancia 0.01); `verify_donation(..., ignore_bones=(PENIS_BONE,))` excluye ese hueso de la comparación y se comprueba aparte.

**Detección:** `summarize()` da `pene_escala`, `pene_efectivo` (= hueso del pene × hueso de altura × escala del slider; 1.0 = male con slider 0.5 y sin huesos) y `pene_estado` (`corto` < 0.95 ≤ `ok` ≤ 1.05 < `largo`; None en female). Columna «Pene (efectivo)» en Leer datos y Reparar, y atributo/filtro `pene` (origen `campo` + `numero`). Con la referencia 1.02: slider 0.6 → 1.02 (ok); slider −0.7307 → 0.75 (corto).

**Reparar futas ya hechas (v0.5.3):** pestaña `gui/tabs/repair_tab.py` + `batch/repair.py::repair_cards` + `editors/penis_size.py::needs_repair`. Solo actúa sobre `tipo == 'futa'` con tamaño efectivo fuera de referencia (> 0.01); omite female/male/futa incompleta (esas, en «Female → Futa») y las ya correctas. Copias en `<salida>/reparadas/<subcarpetas de la entrada>/` con `_free_name`; originales intactos (comprobado por hash). Verificación tras guardar: `verify_penis_size` + `verify_repair` (sexo, nombre, `Custom.body` campo a campo, cara, todos los plugins salvo ABMX, resto de huesos ABMX, sigue siendo futa; se comprobó que detecta un slider o un plugin cambiado). Botón «Seleccionar las que lo necesitan» (sobre las filas visibles). `gui/tabs/out_mixin.py` (`OutDirMixin`) comparte la carpeta de salida con «Female → Futa».

**Pruebas y resultado:**
- ✅ Con las cards reales (Sousuke ×2, Baek Ji Min a 0.6 y −0.7307): fórmula, guardar/recargar, columna y filtro; pipelines `convert_cards`, `donate_cards` (total y sinaltura, + futa) y `repair_cards` sobre cards derivadas de ellas (3 reparadas, 4 omitidas, 0 problemas; 2ª pasada = todo omitido).
- ✅ **Confirmado por el usuario en el juego (v0.5.2):** las escenas H van «bastante mejor». El error que queda (algo de clipping entre partes del cuerpo y animación en el aire, p. ej. el pene se sale o choca con las manos de la female) **es igual de grande con las cards male y female por defecto de Koikatsu** → límite de las animaciones del juego, no de la conversión. Meta cumplida: las futas se comportan como las de fábrica.
- 🟡 Reparar no se ha probado con la biblioteca real del usuario; ni la conversión con cards female reales tras la v0.5.2 más allá de lo que él probó en el juego.
- Historia de errores: la v0.5.1 solo contaba el hueso de altura y **no hizo nada en una card con altura solo por slider** (Baek Ji Min a −0.7307); por eso se midió el slider y salió la v0.5.2.

**Limitaciones:** (1) linealidad slider → escala sin comprobar con una tercera altura (si se mide otra y no encaja, cambiar `base`/`pendiente` en `medidas.json`); (2) escala de altura del hueso no uniforme → se usa la media de xyz; (3) sliders de pelvis/piernas fuera de rango (en Baek Ji Min los índices 14, 17 y 26 valen ≈ −0.14, −0.10 y 1.12) podrían desplazar la pelvis y no se tocan; (4) el valor 1.02 de referencia depende del modelo (si cambia `medidas.json`, cambia solo).

### Altura
- Puede vivir en dos sitios: slider `shapeValueBody[0]` y escala del hueso ABMX `cf_n_height`; **ambos escalan el cuerpo entero (pene incluido)** (ver «Tamaño del pene»). En la futa de referencia (オトギ) la altura real viene del hueso (slider neutro 0.5, hueso 0.9097); en Gwen y en Baek Ji Min viene solo del slider (0.30 y −0.7307). El slider admite valores fuera de 0..1 (el usuario usa un plugin que amplía el rango).
- Requisito del usuario: al convertir a male la altura se conserva. La app no toca slider ni hueso de altura y pone `MaleHeightEnabled = True`.
- 🟡 Hipótesis: `MaleHeightEnabled` es la marca "guardada con KKExpandMaleMaker activo"; sin ella el plugin (modo compatibilidad) ignora alturas no estándar en male y las reinicia. No verificado (no se pudo leer el código del plugin).
- ❓ Falta probar en el juego una futa **alta** (las bajas ya funcionan con la compensación).
- Las animaciones H se rompían si el male se desviaba mucho de la altura por defecto: ya compensado en el pene; no hay rangos publicados para la posición de la pelvis. Idea pendiente: límites min/máx configurables que solo avisen.

### Cards de referencia
- **Gwen Tennyson:** female, 84 huesos, slider altura 0.30, sin `cf_n_height`; en la original `DisplayBalls` era True.
- **天神山 オトギ:** futa final (md5 `436ef9a3fc0af32df63cd4281eca2c61`), altura slider 0.50 / hueso `cf_n_height` 0.9097.
- **Yuan Zhu (`KK_378199.png`):** female con `cf_d_kokan`/`cf_j_kokan` deformados (origen del reseteo genital).
- **Kashiwagi Sousuke (`Koikatu_M_20261003001216400…png`):** male de fábrica, slider 0.6, sin ABMX ni uncensor; **define el tamaño de pene de referencia**. `small_Kashiwagi_Sousuke.png`: copia con altura 0.5 (hueso) + pene ×2.
- **Baek Ji Min (`altura60.png` / `altura-73.png`, mismo personaje futa):** solo difieren en el slider de altura (0.6 vs −0.7307); base de la calibración del modelo; `98570336_p12.png` es la misma card. Tiene `kokaiinum.KKExpandMaleMaker` y sliders 14/17/26 fuera de rango.

## 4. Donante → Receptores (✅ funciona en el PC del usuario)
Petición: una card con buena ropa y cabeza pero mal cuerpo → copia de la receptora con el cuerpo del donante. Un donante, varias receptoras (casillas ☐/☑).

**Modos** (perfiles en `config/donaciones.json`; a futuro el usuario quiere añadir donaciones por partes, p. ej. piernas: se añaden como perfiles, no como código):
- `total` (etiqueta «total», archivo `_total`): sliders 0 y 4-43, huesos ALTURA/PECHO/CUERPO (solo `cf_`), campos `bustSoftness/bustWeight/areolaSize`, plugin `breastphysicscontroller`, `BodyGUID`. Pone `MaleHeightEnabled=True` en receptoras male. **Copia la altura del donante** (slider 0 y hueso).
- `sinaltura` («sin altura», `_sinaltura`): como total conservando la altura de la receptora (slider 0 y hueso `cf_n_height`).
- `pechos` («pechos», `_pechos`): solo sliders 4-13, 20 huesos de pecho, campos y plugin de física. No toca `BodyGUID`.
- Mapa de sliders: 0 altura · 1-3 cabeza/cuello (nunca se copian) · 4-13 pecho · 14-43 resto del cuerpo.
- Se **sustituye, no se mezcla**: huesos de esas categorías que la receptora tenía y el donante no, se borran (en ABMX un hueso ausente = sin modificar). Los `cm_` (pene) no se tocan por las categorías (el hueso del pene lo recalcula `penis_size` cuando toca). Cara, cabeza, cuello, piel, sexo y plugins de futa de la receptora no cambian; las futas siguen siendo futas. Solo female/futa (una male nativa se rechaza). `BodyGUID`: fijo `bp.sac_clit2` o el del donante (selector en la ventana).
- Limitación conocida (sin solución automática): una cabeza pensada para otro cuerpo queda desproporcionada; se arregla a mano.

**Donar + futa en una acción (v0.4.2):** casilla «Convertir también a futa» en la pestaña (se recuerda) y `--futa` en consola. `donate_cards(..., make_futa=True)`: por cada receptora, 1º `apply_futa`, 2º `apply_donor`, 3º recálculo del pene con la altura final. Female / futa incompleta → se convierten; futa completa → solo reciben el cuerpo; male nativa → omitida. Salida siempre en `<donante>/male/`. La verificación compara con "la receptora ya convertida a futa" y exige que la card guardada quede como `futa`. Probado con cards simuladas/derivadas (3 modos, sin fallos de verificación); **no con cards female reales**.

**Nombre (v0.4.1):** `Nombre original [modo: Donante]`, p. ej. `Gwen Tennyson [total: Otogi]`, `… [sin altura: Otogi]`, `… [pechos: Otogi]`. Formato en `nombre_sufijo` del JSON (`{modo}` = `etiqueta` del modo, `{donante}`); se escribe en `firstname` (o `lastname` si no hay). Si la card ya tenía etiqueta (incluida la antigua `[cuerpo: X]`) se **reemplaza**, nunca se apila: `base_name()` quita la etiqueta final.
**Salida** (decisión cerrada: no respeta subcarpetas de la entrada, porque cada donante ya tiene su propia carpeta): `<salida>/<nombre del donante>/female|male/<personaje original>_<modo>.png` (por defecto `salida_donaciones/`; `_1`, `_2`… si existe). El archivo no lleva la etiqueta del nombre.
**Franja de portada** (`editors/cover_text.py`, Pillow): abajo, gris (90,90,90), texto blanco `Cuerpo: {donante}`, alto 9 % de la portada; todo editable en `portada` del JSON (fuentes probadas: Yu Gothic, Meiryo, MS Gothic, Noto CJK, Arial, DejaVu).
**Marca oculta:** entrada `kktool.donor` en `KKEx` con donante, modo y fecha; la columna «Cuerpo de» y el visor la leen para reconocer cards donadas.
**Verificación:** tras guardar se relee y se comprueban sliders, campos, huesos, plugins, `BodyGUID`, sexo/tipo, piel, cara, nombre, franja y tamaño del pene.
Consola: `python -m kk_tool donate <donante.png> <receptora|carpeta> [...] --modo total|sinaltura|pechos [--salida carpeta] [--body-guid fijo|donante] [--sin-portada] [--futa]`; `python -m kk_tool summary <ruta>` imprime el resumen de una card.

## 5. Buscar, ordenar y filtrar (v0.5.0)
Petición: en las listas de cards, buscador por nombre; ordenar por nombre de archivo (como Windows), nombre de card, fecha de Windows…; y filtrar por atributos de la card (altas/bajas, pechos grandes/pequeños) **con combinaciones**; código preparado para ampliar.

**Comportamiento (✅ probado con GUI real bajo xvfb, con cards simuladas y luego reales; 🟡 no con la biblioteca completa del usuario):**
- Todos los `CardPanel` (las 3 pestañas de lista y los dos paneles de Donante → Receptores) llevan una `FilterBar`: **Buscar** (palabras sueltas = AND; sin mayúsculas ni tildes latinas; el japonés no se altera; busca en archivo, nombre, nickname y donante), **Ordenar** (desplegable + ▲/▼ + clic en cabecera con flecha; se recuerda en `tabs.<key>.sort`), **Filtros** (una fila de casillas por atributo; dentro de una fila = O, entre filas = Y; sin casillas = no filtra; el botón muestra cuántas filas filtran; «Limpiar»). Abiertos por defecto en las pestañas de lista, plegados en los paneles de Donante (`tabs.<key>.filters_open`).
- Orden base: orden de carga, **nombre de archivo (orden natural tipo Windows: card2 < card10)**, nombre de la card, fecha de modificación, fecha de creación (en Windows `ctime` = creación), tamaño, nº de plugins, donante; más una por atributo; más «Columna: X» para columnas sin orden propio. Las filas sin valor (p. ej. card ilegible) van siempre al final.
- Las filas filtradas se **ocultan con `Treeview.detach`** (no se borran): conservan iid, casillas y vuelven al limpiar. En Donante → Receptores `checked_paths()` devuelve **también las marcadas ocultas** y la etiqueta avisa «N ocultas por el filtro, también se incluyen». «Marcar todas» solo marca las visibles.
- «Leer datos» muestra fecha de modificación, pene efectivo y una columna por atributo (`alta (+0.20)` = categoría y puntuación). La ficha del visor añade «altura: alta · pecho: grande».

**Atributos = datos, no código** (`config/atributos.json`, con `_ayuda`): añadir un bloque crea solo su grupo de filtro, su opción de orden y su columna en «Leer datos». Dos orígenes: `campo` (valor de un campo del resumen, con `numero` opcional para ordenar por un campo numérico) y `puntuacion` (suma de `peso·(medida − neutro)`; categoría por `cortes` con `hasta` crecientes). Medidas: `slider:N` (índice de `shapeValueBody`) o `hueso:NOMBRE:x|y|z` (escala ABMX; hueso ausente = neutro). Un JSON mal escrito no rompe la app: avisa en el registro y desactiva los atributos.
- **Definiciones actuales:** `tipo` = campo `tipo`; `pene` = campo `pene_estado` + número `pene_efectivo` (corto/ok/largo, ✅ calibrado, sección 3); `altura` = (slider 0 − 0.5) + (escala y de `cf_n_height` − 1.0), cortes baja < −0.08 ≤ media < +0.08 ≤ alta (🟡 orientativo; suma slider + hueso es una aproximación para ordenar con un solo número, y **no** usa la escala 0.2 del slider medida después); `pecho` = slider 4 − 0.5, cortes pequeño < −0.12 ≤ medio < +0.12 ≤ grande (🟡 orientativo).
- 🟡 **Sin verificar:** que el slider **4** sea el *tamaño* de pecho (solo se sabe que 4-13 son pecho). Comprobarlo: en «Leer datos» ordenar por «Pecho (puntuación)» y mirar las portadas de los extremos; si no coincide, cambiar `slider:4` en el JSON (sin tocar código). Altura y pecho también pueden venir de **huesos de bonemods** (cf_*bust*): se añadirían como un término más en el JSON.

**Piezas de código (tocar solo una para ampliar):** `core/listquery.py` (Entry, FilterState, `matches`, SortOption, `sort_options`; nuevo criterio de orden = una línea en `_BASE_SORTS`), `readers/attributes.py`, `readers/fileinfo.py`, `batch/scan.py::read_card_summary`, `gui/widgets/filter_bar.py`, `card_panel.py::apply_view`. `summarize()` es puro y devuelve también `sliders` (44 valores) y `bones_scale` (`{hueso: [x,y,z]}`).

## 6. Código — KK_Tool v0.5.4
```
KK_Tool/
├── instalar.bat / abrir_programa.bat / LEEME.txt
├── settings.json                 # lo crea la app; NO va en el zip
├── docs/                         # solo el .md más reciente
├── cards_entrada/ · salida/male/ · salida/reparadas/ (+log.txt) · salida_donaciones/   # los crea el usuario/la app
└── kk_tool/
    ├── __main__.py               # sin args -> ventana; "summary <ruta>"; "donate …"
    ├── config/  presets.json (futa + pene) · donaciones.json (modos, nombre, portada) · atributos.json (atributos filtrables) · medidas.json (altura por slider, referencia del pene)
    ├── core/    card_io.py (ÚNICO sitio que toca kkloader; save_card se niega a sobrescribir el original)
    │            cover.py (lee la portada PNG sin cargar la card) · settings.py (settings.json atómico)
    │            listquery.py (buscar/filtrar/ordenar: lógica pura, sin GUI)
    ├── readers/ summary.py (summarize(), classify(); solo lectura) · measures.py · attributes.py · fileinfo.py
    ├── editors/ futa.py · donor.py · cover_text.py · penis_size.py   # modifican la card en memoria, no tocan archivos
    ├── batch/   scan.py (+ read_card_summary) · convert.py (female→futa) · donate.py · repair.py (reparar pene)   # orquestan, guardan, releen, log
    └── gui/     app.py · tabs/ (base.py CardListTab, read_tab, futa_tab, donor_tab, repair_tab, out_mixin.py; registro TABS en __init__)
                 widgets/ (card_panel.py CardPanel, filter_bar.py FilterBar, worker.py Worker, preview.py CardPreview, folders_dialog.py)
```
Reglas de diseño (mantener): `editors/` nunca toca archivos; `batch/` orquesta y escribe; `gui/` solo interfaz. **Función nueva = archivo nuevo** (editor, batch si es masiva, pestaña registrada en `TABS`). Una pestaña = subclase de `CardListTab` con `key` única, `checkable = True` si la lista debe llevar casillas (como `FutaTab`; usa `panel.checked_paths()`), `title`, `columns` y ganchos `build_toolbar/update_buttons/default_folders`. El trabajo pesado va en `Worker` (hilo) y se comunica por cola con `post(fn, …)`; los hilos nunca tocan widgets. Los números del juego (alturas, referencias) van en JSON de `config/`, no en el código.

**Subcarpetas (v0.4.1):** `convert_cards(paths, out_root, preset, log, roots)` y `repair_cards(...)`; `roots` = carpetas de entrada de la pestaña. `relative_parent()` calcula la subcarpeta de cada card respecto a la carpeta de entrada que la contiene (la más profunda si hay anidadas): `entrada/A/B/x.png` → `salida/male/A/B/x.png`. No se incluye el nombre de la carpeta raíz. Si dos raíces producen la misma ruta relativa, el segundo archivo recibe `_1`, `_2`… (nunca se sobrescribe). Sin `roots` todo va plano.

`settings.json` guarda: `tabs.<key>.folders / out_dir / col_widths / layout / sort / filters_open`, `window.size`, `window.tab` (claves: `leer`, `futa`, `reparar`, `donar`, `donar_donante`, `donar_receptoras`).

### Problemas ya encontrados (no repetir)
- Un `.bat` de "arrastrar carpeta" se cerraba al instante (causa desconocida): descartado; si algo falla al abrir, ejecutar `python -m kk_tool` desde consola.
- Windows + nombres japoneses: escribir archivos desde Python con `encoding="utf-8"`; los `.bat` usan `PYTHONUTF8=1`.
- Tkinter: conservar la referencia a `PhotoImage` (`self._img`).
- Sliders float32 (comparar con redondeo) y reemplazos de texto sin `assert` (sección 0).
- Una prueba que no ejercita el caso real no valida nada: la v0.5.1 «pasó» sus pruebas y falló con una card de altura solo por slider.

## 7. Pendiente
- ❓ Confirmar la **linealidad slider → escala** con una tercera altura (slider 0 o 1, mismo método de medida) y ajustar `config/medidas.json` si no encaja.
- ❓ Probar en el juego una futa **alta**; y que «Reparar pene» funcione con la biblioteca real del usuario.
- ❓ Probar con cards reales el nombre `[modo: Donante]`, las subcarpetas en female → futa y donar + futa.
- ❓ Verificar que el slider 4 es el tamaño de pecho (sección 5) y, si hay bonemods de pecho, añadir sus huesos como término.
- Confirmar que `DisplayPenis` es el interruptor real (visto True en la futa, False en Gwen).
- Avisos de altura fuera de rango (límites configurables) y de sliders de pelvis/piernas fuera de rango.
- Guardar una **suite de tests** en `tests/` (con las cards de referencia o versiones derivadas) para que los próximos chats no empiecen de cero.
- Rendimiento con carpetas grandes: sin caché de lectura; si se hace lento, guardar resúmenes por ruta + fecha + tamaño y releer solo lo nuevo/modificado.
- Filtros: rangos numéricos libres (altura entre X e Y), editar los cortes desde la ventana, filtro por plugin presente/ausente, filtro «cards donadas», guardar combinaciones con nombre.
- Ideas sin confirmar (el usuario dice que hay "más cosas", de tipo funciones nuevas): renombrar en masa, ajuste de sliders/bonemods, salida `female/` en la conversión, donaciones por partes (piernas…).
- Fuera de alcance salvo que el usuario lo pida: el clipping/animaciones en el aire que quedan en la escena H (también con cards por defecto; juega con Better Repack + HF Patch + kPlug).

## 8. Historial
- **v1–v2:** punto de partida; `kkloader` instalado; mecanismo LZ4 resuelto; flag futa localizado; altura y `KKExpandMaleMaker`; decisión de la vía male.
- **v3:** futas siempre desde female; `EnableBulge=2` = desactivado; `BodyGUID` `bp.sac_clit2`; formato de archivo y ExtType 99 documentados.
- **v4:** prueba de escritura (igualdad lógica); código v0.1 → v0.3 (core, readers, editors/futa, batch, GUI con pestañas, visor, memoria).
- **v5:** v0.3.2 (papelera, tamaños redimensionables); diseño de Donante → Receptores.
- **v6:** v0.4.0: motor de donación (3 modos, verificado con 15 cards reales), nombre `[cuerpo: Donante]`, franja de portada, pestaña con dos paneles, `CardPanel`/`Worker`.
- **v7:** documento depurado; v0.4.1: nombre `Nombre [modo: Donante]`, subcarpetas en female → futa, `Bulge`/`DisplayBalls` cerrados (siempre 2 / siempre False); franja y pestaña confirmadas por el usuario.
- **v7 + v0.4.2:** donar + futa en una sola acción.
- **v7 + v0.4.3:** reseteo de huesos genitales al convertir a futa y al donar a futa/male.
- **v8 + v0.5.0:** buscador, orden y filtros por atributos en las listas (sección 5).
- **v9 + v0.5.1:** pene compensado por la altura (solo hueso) al convertir/donar; columna y filtro «Pene». No hizo nada en una card con altura por slider. Se analizó la male de muestra (sin ABMX) y la copia editada (hueso del pene `cm_J_dan100_00`).
- **v10 + v0.5.2:** la compensación cuenta el slider de altura (medido por el usuario: slider 0.6 vs −0.7307 → pene 0.73–0.75); `config/medidas.json`. El usuario confirma en el juego que va «bastante mejor» y que el clipping restante también está en las cards por defecto.
- **v11 + v0.5.3:** pestaña «Reparar pene (futas)» (copias nuevas verificadas); `OutDirMixin`.
- **v12 (sin cambios de código, v0.5.3):** documento reorganizado y consolidado: descubrimientos clave arriba, secciones renumeradas, cards de referencia, entorno de juego del usuario, lecciones de proceso, pendientes depurados.
- **v13 + v0.5.4:** «Female → Futa» pasa a checklist (`CardListTab.checkable`, botones Marcar todas / Ninguna / Marcar las seleccionadas, contador de marcadas). Probado con GUI real bajo xvfb y filas simuladas: ver la portada de otra fila no desmarca. «Reparar pene» sigue con selección normal (pendiente si se quiere igual).
- **v13 + repositorio:** el proyecto se lleva a GitHub con GitHub Desktop (el usuario tiene el plan gratuito de Claude, sin Claude Code). Se añaden `.gitignore` (excluye `settings.json`, cards, `salida*`, `*.png`), `.gitattributes` (`.bat` en CRLF), `README.md` y `CHANGELOG.md`. Flujo: la IA entrega el zip, el usuario lo descomprime encima y hace «Commit» + «Push».
- **Idioma (decisión del usuario):** todo lo que se ve en GitHub (descripción, `README.md`, `CHANGELOG.md`, mensajes de commit) va en **inglés**; `README.es.md` es la versión en español. `LEEME.txt` y `docs/` siguen en español. A muy largo plazo: selector de idioma en la app (interfaz hoy solo en español).
