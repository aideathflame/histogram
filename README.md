# histogram.py - Return Distribution Analysis

Visualiserar fördelningen av dagliga log-returns för en aktie och jämför med normalfördelning.

## Användning

```bash
python histogram.py TICKER       # Analysera specifik aktie
python histogram.py              # Default: ^OMXSBCAPGI
python histogram.py EQT.ST --years 5 --bins 75 --threshold 2.5
```

**Input:** `data/TICKER.csv`
**Output:** `histogram_TICKER.png`, `histogram_TICKER.txt`

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
- Skewness och kurtosis
- Lista över extrema outliers

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

| Mått | Tolkning |
|------|----------|
| **Skewness < -0.5** | Vänsterskev - fler extrema negativa returns |
| **Skewness > 0.5** | Högerskev - fler extrema positiva returns |
| **Kurtosis > 3** | Leptokurtisk - fetare svansar än normal |
| **Kurtosis < 3** | Platykurtisk - tunnare svansar än normal |

Årlig volatilitet: `σ_daily × √252`

## Annualisering av log-avkastning

Daglig log-avkastning annualiseras genom enkel multiplikation:

```
μ_annual = μ_daily × 252
```

**Varför multiplikation (inte compounding)?**

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
