# histogram.py - Return Distribution Analysis

Visualiserar fördelningen av dagliga log-returns för en aktie och jämför med normalfördelning.

## Användning

```bash
python histogram.py TICKER       # Analysera specifik aktie
python histogram.py              # Default: ^OMXSBCAPGI
python histogram.py EQT.ST --years 5 --bins 75 --threshold 2.5
```

**Input:** `data/TICKER.csv`
**Output:** `histogram_TICKER.png`, `histogram_TICKER.txt`, `histogram_TICKER.csv`

## Konfiguration

| Parameter | Default | Beskrivning |
|-----------|---------|-------------|
| `ticker` | ^OMXSBCAPGI | Aktie att analysera |
| `--years` | 3 | År av historik |
| `--bins` | 50 | Antal staplar i histogrammet |
| `--threshold` | 3.0 | Sigma-gräns för outliers |
| `--data-dir` | data | Datakatalog |

## Output

**PNG-graf visar:**
- Histogram (ljusblå) - empirisk fördelning
- KDE-kurva (mörkblå) - utjämnad faktisk fördelning
- Normalfördelning (röd streckad) - teoretisk referens
- Senaste return (grön linje)

**TXT-rapport innehåller:**
- Daglig och årlig μ (medelvärde) och σ (volatilitet)
- Skewness och kurtosis med tolkning
- Jarque-Bera normalitetstest
- Fat tail multiplier (empiriska / teoretiska outliers)
- Tail ratio (asymmetri i extremsvansar)
- Empiriska vs normala percentiler (1:a, 5:e)
- Lista över extrema outliers med datum

**CSV-rapport** (`histogram_TICKER.csv`) — en rad, maskinläsbar:

| Kolumn | Beskrivning |
|--------|-------------|
| `Ticker` | Aktiesymbol |
| `Observations` | Antal dagliga returns |
| `Start`, `End` | Periodens start- och slutdatum |
| `Daily_Mean`, `Daily_Std` | μ och σ för dagliga log-returns |
| `Annual_Mean`, `Annual_Volatility` | Annualiserade värden (×252 resp. ×√252) |
| `Skewness`, `Kurtosis` | Pearson-kurtosis (normal = 3) |
| `Outliers`, `Outlier_Pct` | Antal och andel utanför ±threshold·σ |
| `Fat_Tail_Mult` | Empiriska outliers / teoretiska under normal |
| `JB_Stat`, `JB_PValue` | Jarque-Bera testresultat |
| `Tail_Ratio` | Genomsnittlig magnitud neg-svans / pos-svans |
| `Empirical_1Pct`, `Normal_1Pct` | 1:a percentilen empiriskt vs teoretiskt |
| `Empirical_5Pct`, `Normal_5Pct` | 5:e percentilen empiriskt vs teoretiskt |

## Tolkning

| Kurva | Beskrivning |
|-------|-------------|
| **KDE** | Faktisk fördelning - icke-parametrisk, fångar asymmetri och feta svansar |
| **Normal** | Teoretisk referens - antar klockkurva med samma μ och σ |

**Typiska observationer:**
- KDE-topp högre och smalare än normal → leptokurtisk (feta svansar)
- Extrema rörelser förekommer oftare än normalfördelningen förutspår
- Därför underskattar normalfördelningen svansrisken

## Statistik

Tröskelvärdena nedan är heuristiker — inte hårda gränser.

| Mått | Tolkning |
|------|----------|
| **Skewness < -0.5** | Vänsterskev - fler extrema negativa returns |
| **Skewness > 0.5** | Högerskev - fler extrema positiva returns |
| **Kurtosis > 3** | Leptokurtisk - fetare svansar än normal |
| **Kurtosis < 3** | Platykurtisk - tunnare svansar än normal |

Scriptet använder **Pearson-kurtosis** (`fisher=False`), där normal = 3.
Scipy:s default är excess kurtosis där normal = 0 — blanda inte ihop.

Årlig volatilitet: `σ_daily × √252`

### Jarque-Bera

Kombinerar skewness + kurtosis i ett normalitetstest.

- **p < 0.05** → avvisa normalfördelning (datat är inte normalt)
- **p ≥ 0.05** → kan inte avvisa normalitet

För svenska aktier med 3+ år data avvisas normalitet nästan alltid — frågan är hur grov approximationen är.

### Fat Tail Multiplier

`empiriska outliers / teoretiskt förväntade under normal`

- **1.0x** → svansarna matchar normalfördelningen
- **3x** → tre gånger fler ±3σ-dagar än normal förutspår
- **>5x** → kraftigt leptokurtisk, normal är dålig modell för svansrisk

Vid threshold = 3.0σ är teoretisk frekvens ~0.27%. Empiriskt brukar aktier ligga 3-10x över.

### Tail Ratio

`mean(|neg-svans|) / mean(|pos-svans|)` — jämför magnitud i extremerna.

- **> 1.2** → nedsidan dominerar (asymmetrisk crash-risk)
- **0.8 - 1.2** → ungefär symmetrisk
- **< 0.8** → uppsidan dominerar (ovanligt)

## Annualisering av log-avkastning

Daglig log-avkastning annualiseras genom enkel multiplikation:

```
μ_annual = μ_daily × 252
```

**Varför `μ × 252` istället för `(1+μ)^252 - 1`?**

Log-avkastning är **additiv** över tid. Om dagliga log-returns är r₁, r₂, r₃... så är total log-avkastning = r₁ + r₂ + r₃ + ...

Detta skiljer sig från enkel procentuell avkastning som är multiplikativ.

**Exempel:**
- Daglig log-avkastning: 0.165%
- Annualiserad: 0.165% × 252 = 41.6%

**Konvertering till faktisk prisförändring:**

Log-avkastning och faktisk prisförändring är inte samma sak:

```
Faktisk avkastning = e^(log_return) - 1
```

Så 41.6% årlig log-avkastning motsvarar `e^0.416 - 1 = 51.6%` faktisk prisökning.

## Exempel-output (TXT-utdrag)

```
LOG RETURN HISTOGRAM REPORT - EQT.ST
==================================================
Observations: 754
Period: 2023-05-19 to 2026-05-19

Daily mean (μ): 0.000823 (0.082%)
Daily std dev (σ): 0.022451 (2.245%)
Annualized mean: 20.74%
Annualized volatility: 35.64%
Skewness: -0.3214
Kurtosis: 6.2103

FAT TAILS ANALYSIS
--------------------------------------------------
Jarque-Bera test: stat=342.1, p=1.2e-75  → NOT normal

Extreme outliers (> ±3.0σ): 8 (1.06%)
Expected under normal distribution: 0.27%
Fat tail multiplier: 3.9x
Tail ratio (neg/pos magnitude): 1.34x  → downside dominates

EMPIRICAL vs NORMAL TAIL PERCENTILES
--------------------------------------------------
  1st percentile:  empirical -6.82%  vs  normal -5.14%
  5th percentile:  empirical -3.51%  vs  normal -3.61%
  → Worst 1% days are 1.3x worse than normal predicts
```
