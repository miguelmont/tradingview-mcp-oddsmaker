# MNQ Analysis Workflow — Design Spec

**Fecha:** 2026-04-21
**Autor:** miguelmont (+ Claude brainstorming)
**Estado:** Diseño aprobado — pendiente de plan de implementación

## 1. Contexto y objetivo

Construir un workflow reutilizable que analice el estado actual del mercado MNQ (Micro Nasdaq futures) según la estrategia personal del usuario — basada en sesiones ICT (Asia/London/NY), Session VWAP con desviaciones estándar, Weekly/Monthly AVWAP para bias HTF, Big Beluga CHoCH para estructura, Time Cycles (TTP) para liquidez temporal, y SMT entre MNQ y ES.

El workflow se invoca desde Claude Code como slash command `/analizar [MNQ|ES|NQ]` y produce un reporte dual: TL;DR corto para decisión rápida + reporte detallado estructurado. El reporte evalúa la activación de tres setups de la estrategia y emite un veredicto accionable.

**Instrumentos principales:** MNQ (ejecución) y ES (para SMT).
**Limitación conocida:** El chart actual muestra `CME_MINI:NQ1!`. La lógica se aplica igual; los niveles de liquidez son equivalentes entre NQ y MNQ.

## 2. Arquitectura

### 2.1 Layout físico

Dos chart tabs en TradingView Desktop, cada uno con layout vertical `2v`:

```
┌─────── Tab 1: "MNQ Analysis" ────────┐    ┌─────── Tab 2: "ES Analysis" ─────────┐
│  Pane 0: MNQ 1h    (HTF bias)        │    │  Pane 0: ES 1h    (HTF bias)         │
├──────────────────────────────────────┤    ├──────────────────────────────────────┤
│  Pane 1: MNQ 1min  (ejecución)       │    │  Pane 1: ES 1min  (ejecución)        │
└──────────────────────────────────────┘    └──────────────────────────────────────┘
```

Los tabs se crean una vez y se reutilizan en invocaciones siguientes. Los indicadores cargados en el chart del usuario (VWAP Auto Anchored x3, Choch Pattern Levels [BigBeluga], Sessions [LuxAlgo], Time Cycles (TTP), Daily Ranges Dividers, ICT First Presented FVG) deben estar visibles en ambos tabs.

### 2.2 Flujo de ejecución del slash command

```
/analizar [MNQ|ES|NQ]
 │
 ├─ 1. Leer docs/mi-estrategia.md (fuente de verdad: reglas + thresholds)
 │
 ├─ 2. Preparar tabs:
 │      tab_list                       → ¿existen los 2 tabs?
 │      tab_new / tab_switch           → crear/activar
 │      pane_set_layout "2v"           → split vertical
 │      pane_set_symbol + timeframe    → MNQ 60 | MNQ 1 ; ES 60 | ES 1
 │
 ├─ 3. Lectura de datos MNQ (tab 1):
 │      quote_get
 │      chart_get_state (x pane)
 │      data_get_study_values          → VWAPs, KAMA ER
 │      data_get_pine_lines            → niveles SVWAP ±SD, PDH/PDL/PWH/PWL
 │      data_get_pine_labels           → textos con precio
 │      data_get_pine_boxes            → time cycles, FVG
 │      data_get_pine_tables           → delta Big Beluga si expone
 │      data_get_ohlcv summary=true    → contexto OHLCV reciente
 │
 ├─ 4. Lectura de datos ES (tab 2, mínimo necesario para SMT):
 │      data_get_pine_boxes            → time cycles de ES
 │      quote_get
 │      data_get_ohlcv summary=true    → referencia sesión
 │
 ├─ 5. Motor de análisis:
 │      - Calcular bias HTF (§3.1)
 │      - Clasificar estado LTF (§3.2)
 │      - Detectar SMT vía time-cycle boxes (§3.3)
 │      - Detectar sweep TBL o SMT equivalente (§3.9)
 │      - Clasificar AMD por sesión (§3.10)
 │      - Evaluar los 3 setups (§3.4, 3.5, 3.6)
 │      - Computar veredicto + grade (§3.7)
 │
 └─ 6. Renderizar reporte (TL;DR + detalle)
```

### 2.3 Archivos producidos

| Archivo | Propósito |
|---|---|
| `docs/mi-estrategia.md` | Estrategia formalizada: reglas SI/ENTONCES + thresholds. Fuente de verdad que el slash command lee en cada invocación. |
| `.claude/commands/analizar.md` | Slash command. Contiene las instrucciones para Claude: qué tools llamar, en qué orden, cómo renderizar el reporte. |
| `docs/superpowers/specs/2026-04-21-mnq-analisis-workflow-design.md` | Este spec de diseño. |

## 3. Reglas de análisis (contenido de `docs/mi-estrategia.md`)

### 3.1 Bias HTF (leído en MNQ 1h)

```
BULLISH    ⟺  precio > Weekly AVWAP   ∧  precio > Monthly AVWAP
BEARISH    ⟺  precio < Weekly AVWAP   ∧  precio < Monthly AVWAP
NEUTRAL+   ⟺  precio > Weekly AVWAP   ∧  precio < Monthly AVWAP
            (jerarquía weekly → sesgo alcista débil)
NEUTRAL-   ⟺  precio < Weekly AVWAP   ∧  precio > Monthly AVWAP
            (jerarquía weekly → sesgo bajista débil)
```

**Identificación de los 3 VWAP Auto Anchored** (el chart tiene tres; hay que saber cuál es cuál):
- Inspeccionar inputs de cada estudio (anchor time) — el anchor es el único input distintivo.
- Weekly = anchor al inicio de la semana (lunes 00:00 exchange time o equivalente).
- Monthly = anchor al primer día del mes.
- Session = anchor a 18:00 NY del día previo (inicio del trading day de futuros).
- Si la inspección es ambigua en la primera invocación, el slash command pregunta al usuario para etiquetar y persiste el mapeo.

**Grade y tradeabilidad por bias:**
```
grade = A+   ⟺  bias ∈ {BULLISH, BEARISH}
               → los 3 setups disponibles

grade = A-   ⟺  bias ∈ {NEUTRAL+, NEUTRAL-}
               → Setup 3 ELIMINADO (HTF no claramente definido)
               → Setup 1 y Setup 2 disponibles usando jerarquía weekly como "HTF efectivo"
               → reporte marca: "⚠️ HTF no claramente definido — riesgo mayor"
```

**Regla de "dirección HTF efectiva"** (la que usan los setups para orientarse, incluso en neutral):
```
dirección HTF efectiva = BULL   si  bias ∈ {BULLISH, NEUTRAL+}
                       = BEAR   si  bias ∈ {BEARISH, NEUTRAL-}
```
En neutral la dirección efectiva proviene de la jerarquía weekly. Setup 3 (contra-HTF) nunca usa esta regla — siempre exige bias ∈ {BULLISH, BEARISH}.

**Condición global (KAMA sobre pendiente del SVWAP):**
```
TRADEABLE   ⟺  KAMA_ER(SVWAP_slope, period=14) ≥ 0.30
NO-TRADE    ⟺  KAMA_ER(SVWAP_slope, period=14) <  0.30   (SVWAP flat, sin edge)
```

### 3.2 Estado LTF (leído en MNQ 1min)

```
Distancia = (precio − SVWAP) / SVWAP_sd

EN-BANDA            ⟺  |Distancia| ≤ 0.5
CERCA-BANDA         ⟺  0.5 < |Distancia| ≤ 1.0
SOBREEXT-ALCISTA    ⟺  Distancia > 1.0
SOBREEXT-BAJISTA    ⟺  Distancia < -1.0
```

### 3.3 SMT (MNQ vs ES) vía Time Cycles boxes

**Fuente**: `data_get_pine_boxes study_filter:"Time Cycles"` leído en ambos tabs.

**Cajas comparadas** (jerarquía de peso, mayor a menor):
```
SESSION box      ← peso mayor
90min box
30min box
10min box        ← peso menor
```

**Detección por nivel `n`:**
```
SMT-BEARISH (n)   ⟺  MNQ.current_n.high > MNQ.prev_n.high   (MNQ hizo HH)
                     ∧ ES.current_n.high  ≤ ES.prev_n.high    (ES no confirmó)

SMT-BULLISH (n)   ⟺  MNQ.current_n.low  < MNQ.prev_n.low    (MNQ hizo LL)
                     ∧ ES.current_n.low   ≥ ES.prev_n.low     (ES no confirmó)

SIN-SMT (n)       ⟺  ambos confirmaron o ambos neutrales
```

**Agregación:**
```
SMT final = { nivel : dirección }   para todos los niveles que disparen
peso_total = Σ pesos_niveles_confirmando
```

### 3.4 Setup 1 — NY Continuation

```
ACTIVA ⟺ todos los siguientes:
  ├─ bias HTF ∈ {BULLISH, BEARISH, NEUTRAL+, NEUTRAL-}   (cualquiera — si neutral → A-)
  ├─ Distancia LTF ∈ {EN-BANDA, CERCA-BANDA}
  ├─ sweep TBL reciente (≤10 bars 1min) — directo o vía SMT (§3.9)
  ├─ Big Beluga CHoCH en dirección del bias HTF (≤5 bars tras el sweep)
  ├─ condición global = TRADEABLE
  └─ hora ∈ sesión NY (09:30–16:00 NY)   (ideal; fuera de NY → señal débil)

ENTRY:   al cierre del bar del CHoCH
STOP:    swing extremo que originó el CHoCH
TARGET:  liquidez intradía  o  PDH/PDL  o  PWH/PWL
RR:      mínimo 2.0  (default RRSetup1 = 2.0)
```

### 3.5 Setup 2 — NY Reversal pro-HTF

```
ACTIVA ⟺ todos los siguientes:
  ├─ bias HTF ∈ {BULLISH, BEARISH, NEUTRAL+, NEUTRAL-}   (si neutral → A-)
  ├─ Distancia LTF |SDs| > 1.0 EN DIRECCIÓN OPUESTA al bias HTF
  │    (ej: HTF bullish + precio <-1 SD del SVWAP)
  ├─ sweep TBL reciente EN LA DIRECCIÓN DE LA SOBREEXTENSIÓN (≤10 bars)
  ├─ Big Beluga CHoCH en dirección HTF (contra la sobreextensión)
  ├─ SMT confirmando pro-HTF (opcional pero boost)
  ├─ condición global = TRADEABLE
  └─ hora ∈ sesión NY

ENTRY:   al cierre del bar del CHoCH
STOP:    extremo del sweep (margen ≤2 ticks)
TARGET:  SVWAP (primario) · +1 SD en dirección HTF (secundario) · PDH/PWH si alineado
RR:      mínimo 3.0  (default RRSetup2 = 3.0)

BOOST:   si SMT presente → sizing RiskPctBoost (1.5%)
```

### 3.6 Setup 3 — NY Reversal contra-HTF (mean reversion de sobreextensión pro-HTF)

```
ACTIVA ⟺ todos los siguientes:
  ├─ bias HTF ∈ {BULLISH, BEARISH}   (Setup 3 NO activa en neutral)
  ├─ Distancia LTF |SDs| > 1.0 EN LA MISMA DIRECCIÓN que bias HTF
  │    (ej: HTF bullish + precio >+1 SD del SVWAP)
  ├─ sweep TBL reciente EN LA MISMA DIRECCIÓN (ej: sweep PDH si bull)
  ├─ Big Beluga CHoCH contra HTF
  ├─ SMT confirmando contra-HTF (IDEAL — este es el setup donde SMT aporta más)
  ├─ condición global = TRADEABLE
  └─ hora ∈ sesión NY

ENTRY:   al cierre del bar del CHoCH
STOP:    extremo del sweep
TARGET:  SVWAP únicamente (mean reversion pequeño, NO más allá)
RR:      mínimo 1.5  (default RRSetup3 = 1.5)

NOTA:    sin SMT confirmando, este setup baja a "ESPERA" por default — demasiado riesgo para ir contra HTF sin divergencia.
```

### 3.7 Veredicto final

```
EJECUTAR SETUP N (A+)   ⟺  checks ✅ del setup
                           ∧ bias ∈ {BULLISH, BEARISH}
                           ∧ TRADEABLE
                           ∧ en NY

EJECUTAR SETUP N (A-)   ⟺  checks ✅ del setup
                           ∧ bias ∈ {NEUTRAL+, NEUTRAL-}
                           ∧ Setup ∈ {1, 2}   (Setup 3 jamás en neutral)
                           ∧ TRADEABLE
                           ∧ en NY
                           → reporte anota: "A- · HTF weekly-only · risk mayor"

ESPERAR                 ⟺  algunos checks parciales — el reporte lista qué falta

NO-TRADE                ⟺  NO-TRADE por KAMA ER flat
                           ∨ fuera de NY session (salvo flag `--off-hours`)
```

### 3.8 Sizing (de tu doc, sin cambios)

```
RiskPctBase    = 1.0%    (setups sin boost)
RiskPctBoost   = 1.5%    (setups con SMT confirmando u otra confluencia fuerte)
MaxDDPct       = 15.0%   (kill switch — drawdown peak-to-trough)
```

### 3.9 Sweep de liquidez (TBL — Time Based Liquidity)

**Fuente primaria**: `data_get_pine_boxes study_filter:"Time Cycles"` (mismo indicador usado para SMT).

**Detección directa en MNQ:**
```
Sweep directo (n)    ⟺  en las últimas ≤10 barras 1min:
                        ∃ caja de TC nivel n  tal que:
                          bar.high > caja.high ∧ bar.close < caja.high   (sweep bajista)
                          ∨
                          bar.low  < caja.low  ∧ bar.close > caja.low    (sweep alcista)
```

**Detección vía SMT (ES "tomó" la liquidez que MNQ no confirmó):**
```
Sweep vía SMT (n)    ⟺  Sweep directo en ES al nivel n
                        ∧ MNQ NO hizo sweep al nivel n
                        ∧ SMT-BEARISH(n) o SMT-BULLISH(n) confirmado
```

**Regla de satisfacción para setups:**
```
"sweep TBL reciente"  ⟺  ∃ Sweep directo (cualquier n)
                         ∨ ∃ Sweep vía SMT (cualquier n)
```

**Convenciones de reporte:**
- Si hay sweep directo en MNQ → peso = el peso del nivel `n` de la caja barrida.
- Si hay sweep vía SMT → el setup se marca automáticamente con **boost de sizing** (RiskPctBoost).
- Si hay ambos (directo en MNQ + SMT) → `confluence_score = máximo`, highest conviction.
- Orden esperado en el timing: `sweep → CHoCH en dirección opuesta`. Si CHoCH ocurre antes que el sweep o sin sweep, el setup degrada a "ESPERA".

### 3.10 AMD phase por sesión

**Concepto**: cada sesión (Asia / London / NY) pasa por fases de acumulación / manipulación / distribución / expansión. El estado actual de cada sesión ayuda a predecir el comportamiento de NY.

**Detección por sesión** (dentro de la ventana horaria NY time):
```
CONSOLIDATED   ⟺  (session_high − session_low) < 0.6 × ATR(14, daily)
                   rango apretado durante toda la sesión

MANIPULATED    ⟺  la sesión hizo sweep de {prev_session_high, prev_session_low}
                   y cerró del lado opuesto (retracement > 50% del rango de la sesión)

EXPANDED       ⟺  |close − open| > 0.4 × ATR(14, daily)
                   ∧ movimiento direccional claro (no round-trip)

Combos secuenciales:
  CONSOLIDATED → MANIPULATED                      (consolidó, luego fakeout al final)
  CONSOLIDATED → MANIPULATED → EXPANDED            (AMD completo)
  EXPANDED (no manipulación previa)                (se fue directo)
```

**Ventanas horarias (NY time):**
- Asia: 18:00 – 03:00
- London: 03:00 – 09:30
- NY: 09:30 – 16:00

**Narrativa predictiva (lookup en `mi-estrategia.md`):**

| Asia | London | Sesgo NY esperado |
|---|---|---|
| CONSOLIDATED | CONSOLIDATED | Expansión esperada en NY (dirección según HTF) |
| CONSOLIDATED → MANIPULATED | EXPANDED | Continuación — la manipulación asiática ya se corrigió en Londres |
| EXPANDED alcista | EXPANDED bajista | Alta probabilidad de NY Reversal (Setup 2 hacia HTF) |
| EXPANDED | CONSOLIDATED | NY probablemente extenderá la dirección de Asia |
| CONSOLIDATED | CONSOLIDATED → MANIPULATED | NY tiende a expandir en dirección opuesta al sweep |

## 4. Estructura del reporte

### 4.1 TL;DR (primer bloque, ~150-250 palabras)

Formato fijo, siempre las mismas 6 líneas:

```
🕐 {timestamp NY} · Sesión: {Asia|London|NY} ({estado})

🎯 Bias HTF ({symbol} 1h):       {BULLISH|BEARISH|NEUTRAL+|NEUTRAL-}   · razón corta
📍 Posición LTF ({symbol} 1m):   {±N.N SD}   · {EN-BANDA|CERCA-BANDA|SOBREEXT-ALCISTA|SOBREEXT-BAJISTA}
🔀 SMT MNQ vs ES:                {AUSENTE|BEARISH|BULLISH}   · qué nivel confirma
🧭 Setup activo:                 {SETUP N ACTIVO|ESPERA|NO-TRADE}   · razón corta · grade A+/A-

⚠️ Warnings: {lista corta o vacío}
💡 Próxima acción: {qué observar o esperar concretamente}
```

### 4.2 Reporte detallado (segundo bloque, ~800-1200 palabras)

Secciones fijas en este orden:

1. **Contexto HTF** (precio vs Weekly/Monthly AVWAP, pendiente, sesión activa)
2. **Estado LTF** (SVWAP con pendiente/KAMA ER, distancia en SDs, bandas)
3. **Big Beluga CHoCH/MSS** (último CHoCH reciente, delta volumen si expuesto)
4. **Time Cycles (TTP)** (ciclo activo, cuándo termina, contexto)
5. **AMD por sesión** (tabla Asia/London/NY + narrativa predictiva)
6. **SMT (MNQ vs ES)** (tabla por nivel de caja + peso total + implicación)
7. **Evaluación de los 3 setups** (check-by-check con ✅/⏳/❌ y detalles)
8. **Liquidez clave cercana** (tabla ordenada por precio, radio ±2%)
9. **Veredicto final + checklist de ejecución**
10. **Screenshot** (opcional, si pasan `--screenshot`)

Ejemplos concretos de render en la sección §Apéndice A.

### 4.3 Flags del slash command

| Flag | Efecto |
|---|---|
| `--screenshot` | Añade `capture_screenshot region:"full"` al final del reporte |
| `--off-hours` | Permite veredicto incluso fuera de sesión NY (marca setups con warning) |
| `--smt-visual` (futuro) | Alterna a layout 2x2 en un solo tab para confirmación visual del SMT |
| `--verbose` | Pasa `verbose: true` a los tools Pine para ver raw data / IDs |

## 5. Tools MCP usadas

| Tool | Uso |
|---|---|
| `tab_list`, `tab_new`, `tab_switch` | gestión de los 2 tabs MNQ y ES |
| `pane_set_layout`, `pane_set_symbol`, `pane_focus` | setup del split 2v |
| `chart_get_state` | confirmar símbolo/TF por pane |
| `quote_get` | precio + OHLC + volumen actual |
| `data_get_study_values` | valores numéricos de VWAPs |
| `data_get_pine_lines` | niveles horizontales (SVWAP bands, daily/weekly ranges) |
| `data_get_pine_labels` | textos con precio (PDH, etc.) |
| `data_get_pine_boxes` | time cycles boxes (para SMT y TBL sweeps) |
| `data_get_pine_tables` | delta Big Beluga si expone tabla |
| `data_get_ohlcv` (summary) | contexto precio reciente |
| `capture_screenshot` | opcional, si `--screenshot` |
| `tv_health_check` | pre-flight antes de todo |

## 6. Criterios de éxito

El workflow se considera funcional cuando:

1. `/analizar` ejecuta end-to-end en ≤15 segundos con tabs ya creados.
2. El TL;DR se puede leer en ≤10 segundos y comunica bias + setup activo + próxima acción.
3. El reporte detallado evalúa explícitamente los 3 setups y justifica cada ✅/⏳/❌.
4. Detección SMT vía time-cycle boxes funciona y reporta por nivel (session/90/30/10).
5. El sweep detection usa TBL (Time Cycles) como fuente única, incluyendo la equivalencia vía SMT.
6. Grade A+/A- se asigna correctamente según bias HTF.
7. El reporte usa los nombres de indicadores actuales del chart (`data_get_pine_*` con `study_filter`).

## 7. Decisiones deferidas (no bloquean v1)

- **Alerts automáticos**: fuera de scope v1. Futuro: combinar con `alert_create` para avisar cuando un setup cambie de ESPERA a ACTIVO.
- **Logging histórico**: no se guardan los reportes. Futuro: append a `logs/analisis-YYYY-MM-DD.md` para review posterior.
- **Backtesting**: fuera de scope v1. El doc del usuario menciona protocolo de validación (WFA, Monte Carlo); eso requiere infra separada.
- **Modo `--smt-visual` (2x2 un solo tab)**: fuera de scope v1. Decidido en brainstorming diferir a v2.
- **Identificación automática de los 3 VWAP Auto Anchored**: v1 pide confirmación al usuario la primera vez y persiste mapping. v2 podría inspeccionar anchors programáticamente.
- **Notificación fuera de NY**: v1 marca warning si fuera de NY; el flag `--off-hours` permite forzar análisis completo.

## 8. Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| Los 3 "VWAP Auto Anchored" son indistinguibles por nombre | Mapear por anchor time en primera ejecución; pedir confirmación al usuario; persistir mapping en `mi-estrategia.md`. |
| Pine boxes del indicador Time Cycles no exponen metadata de nivel (session/90/30/10) | Inferir el nivel por duración de la caja; si falla, pedir al usuario que apunte mediante `study_filter` + nombre exacto. |
| Big Beluga CHoCH no expone dirección vía API | Inferir dirección del CHoCH por posición del label vs swing previo. |
| KAMA_ER sobre SVWAP slope no existe como indicador cargado | Calcular en Claude mediante OHLCV de `data_get_ohlcv` y SVWAP de `data_get_study_values`. Alternativa: cargar indicador Pine custom. |
| Latencia de los 2 tabs + lecturas duplicadas | Paralelizar lecturas MNQ/ES con `data_get_*` en una sola iteración. Minimizar calls en tab ES (solo boxes + quote). |
| ES no tiene los mismos indicadores cargados que MNQ | En setup inicial del tab ES, clonar los indicadores necesarios (solo Time Cycles requerido para SMT). |

## Apéndice A — Ejemplos de render

### A.1 TL;DR ejemplo

```
🕐 2026-04-21 15:47 NY · Sesión: NY (Cash Open +17min)

🎯 Bias HTF (MNQ 1h):       BULLISH   · +Weekly AVWAP, +Monthly AVWAP
📍 Posición LTF (MNQ 1m):   +0.6 SD   · CERCA-BANDA
🔀 SMT MNQ vs ES:           BEARISH   · 90m + 30m boxes confirmando
🧭 Setup activo:            ESPERA    · Setup 3 armándose (contra-HTF) · grade A+

⚠️ Warnings: SMT bearish contra bias bullish — conflicto de sesgo
💡 Próxima acción: esperar sweep MNQ del 30m box high + CHoCH bearish → confirma Setup 3
```

### A.2 Evaluación de setup (detalle)

```
SETUP 3 — NY Reversal contra-HTF          RESULTADO: ESPERA (grade A+)
┌──────────────────────────────────────────────────────────┬─────┐
│ HTF bullish (o bearish)                                  │ ✅  │  (BULLISH)
│ Distancia LTF > 1.0 SD en dirección HTF                  │ ⏳  │  (+0.6 SD, falta)
│ Sweep TBL en dirección HTF                               │ ❌  │  (sin sweep detectado)
│ Big Beluga CHoCH contra HTF                              │ ❌  │  (último CHoCH fue bullish)
│ SMT confirmando contra-HTF                               │ ✅  │  (BEARISH en 90m + 30m)
│ TRADEABLE (KAMA ER ≥ 0.30)                              │ ✅  │  (ER=0.38)
└──────────────────────────────────────────────────────────┴─────┘

Condiciones faltantes: precio llegar a +1 SD + sweep del 30m box + CHoCH bearish.
Si todas se cumplen en próximas barras → SETUP 3 ACTIVO con SMT boost.
```