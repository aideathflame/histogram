import argparse
import os

import matplotlib

matplotlib.use("Agg")

from datetime import datetime, timedelta

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy.stats import gaussian_kde, jarque_bera, kurtosis, norm, skew


def parse_args():
    parser = argparse.ArgumentParser(description="Histogram of Daily Log Returns")
    parser.add_argument(
        "ticker", nargs="?", default="^OMXSBCAPGI", help="Ticker symbol (default: ^OMXSBCAPGI)"
    )
    parser.add_argument(
        "--data-dir", type=str, default="data", help="Data directory (default: data)"
    )
    parser.add_argument(
        "--years", type=int, default=3, help="Years of history to analyze (default: 3)"
    )
    parser.add_argument(
        "--bins", type=int, default=50, help="Number of histogram bins (default: 50)"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=3.0,
        help="Sigma threshold for outliers (default: 3.0)",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # Configuration
    TRADING_DAYS = 252
    HIST_COLOR = "skyblue"
    KDE_COLOR = "darkblue"
    NORMAL_FIT_COLOR = "red"
    LATEST_RETURN_COLOR = "green"
    FIG_SIZE = (12, 7)

    # Build file path
    ticker = args.ticker
    if not ticker.endswith(".csv"):
        file_path = os.path.join(args.data_dir, f"{ticker}.csv")
    else:
        file_path = os.path.join(args.data_dir, ticker)
        ticker = ticker.replace(".csv", "")

    sns.set_theme(style="whitegrid")

    # Load and prepare data
    try:
        df = pd.read_csv(file_path, parse_dates=["Date"])

        if "Close" not in df.columns or "Date" not in df.columns:
            print(f"Error: Required columns ('Close', 'Date') missing in {file_path}.")
            return

        df = df.sort_values("Date")

        # Filter to specified years
        latest_date = df["Date"].max()
        cutoff_date = latest_date - timedelta(days=args.years * 365.25)
        df = df[df["Date"] >= cutoff_date]

        if df.empty:
            print(f"Error: No data after filtering to {args.years} years.")
            return

        # Calculate log returns
        df["LogReturn"] = np.log(df["Close"] / df["Close"].shift(1))
        logreturns = df["LogReturn"].dropna()
        df = df.loc[logreturns.index]

        if logreturns.empty:
            print(f"Error: Could not calculate log returns.")
            return

        latest_logreturn = logreturns.iloc[-1]
        latest_date = df["Date"].iloc[-1]

    except FileNotFoundError:
        print(f"Error: File not found: {file_path}")
        return
    except Exception as e:
        print(f"Error loading data: {e}")
        return

    # Plot histogram
    plt.figure(figsize=FIG_SIZE)

    # Convert to percentage for display
    logreturns_pct = logreturns * 100

    ax = sns.histplot(
        logreturns_pct,
        bins=args.bins,
        kde=False,
        color=HIST_COLOR,
        edgecolor="grey",
        stat="density",
        alpha=0.7,
        label="Empirical distribution",
    )

    # Plot KDE separately for better visibility
    kde = gaussian_kde(logreturns_pct)
    x_kde = np.linspace(logreturns_pct.min(), logreturns_pct.max(), 200)
    ax.plot(x_kde, kde(x_kde), color=KDE_COLOR, lw=2.5, label="KDE")

    # Fit normal distribution (on percentage data)
    mu_pct, sigma_pct = norm.fit(logreturns_pct)
    mu, sigma = mu_pct / 100, sigma_pct / 100  # Keep original scale for stats
    xmin, xmax = plt.xlim()
    x = np.linspace(xmin, xmax, 200)
    p = norm.pdf(x, mu_pct, sigma_pct)
    plt.plot(
        x,
        p,
        color=NORMAL_FIT_COLOR,
        linestyle="--",
        linewidth=2,
        label=f"Normal ($\\mu={mu_pct:.2f}\\%, \\sigma={sigma_pct:.2f}\\%$)",
    )

    # Latest return line
    plt.axvline(
        latest_logreturn * 100,
        color=LATEST_RETURN_COLOR,
        linestyle=":",
        linewidth=2.5,
        label=f"Latest: {latest_logreturn * 100:.2f}% ({latest_date.date()})",
    )

    # Identify outliers
    threshold = args.threshold
    extreme_outliers = df[
        (logreturns > mu + threshold * sigma) | (logreturns < mu - threshold * sigma)
    ].copy()

    # Annualization
    mu_annual = mu * TRADING_DAYS
    sigma_annual = sigma * np.sqrt(TRADING_DAYS)

    # Plot formatting
    plt.title(f"Distribution of Daily Log Returns for {ticker}", fontsize=16, pad=20)
    plt.xlabel("Log Return (%)", fontsize=12)
    plt.ylabel("Density", fontsize=12)

    # Add subtitle with metadata
    plt.figtext(
        0.5,
        0.92,
        f"n={len(logreturns)} | {df['Date'].min().date()} to {df['Date'].max().date()}",
        ha="center",
        fontsize=10,
        color="grey",
    )

    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend(fontsize=10, loc="upper right")
    plt.tight_layout(rect=[0, 0, 1, 0.92])

    # Save graph
    image_filename = f"histogram_{ticker}.png"
    try:
        plt.savefig(image_filename, dpi=300)
        print(f"Graph saved: {os.path.abspath(image_filename)}")
    except Exception as e:
        print(f"Could not save image: {e}")

    plt.close()

    # Statistics
    log_kurtosis = kurtosis(logreturns, fisher=False)
    log_skewness = skew(logreturns)
    extremprocent = (len(extreme_outliers) / len(logreturns)) * 100
    theoretical_outlier_pct = 100 * (1 - norm.cdf(threshold) + norm.cdf(-threshold))

    # Fat tail multiplier
    fat_tail_mult = extremprocent / theoretical_outlier_pct if theoretical_outlier_pct > 0 else np.nan

    # Jarque-Bera normality test
    jb_stat, jb_pvalue = jarque_bera(logreturns)

    # Tail ratio: avg magnitude of negative extremes vs positive extremes
    neg_tail = logreturns[logreturns < mu - threshold * sigma]
    pos_tail = logreturns[logreturns > mu + threshold * sigma]
    if len(pos_tail) > 0 and pos_tail.abs().mean() > 0:
        tail_ratio = neg_tail.abs().mean() / pos_tail.abs().mean()
    else:
        tail_ratio = np.nan

    # Empirical vs normal tail percentiles
    empirical_1pct = np.percentile(logreturns, 1)
    empirical_5pct = np.percentile(logreturns, 5)
    normal_1pct = norm.ppf(0.01, mu, sigma)
    normal_5pct = norm.ppf(0.05, mu, sigma)

    # Generate report
    report_lines = [
        f"LOG RETURN HISTOGRAM REPORT - {ticker}",
        "=" * 50,
        f"Observations: {len(logreturns)}",
        f"Period: {df['Date'].min().date()} to {df['Date'].max().date()}",
        "",
        f"Daily mean (μ): {mu:.6f} ({mu * 100:.3f}%)",
        f"Daily std dev (σ): {sigma:.6f} ({sigma * 100:.3f}%)",
        f"Annualized mean: {mu_annual * 100:.2f}%",
        f"Annualized volatility: {sigma_annual * 100:.2f}%",
        f"Skewness: {log_skewness:.4f}",
        f"Kurtosis: {log_kurtosis:.4f}",
        "",
        "(Annualization based on 252 trading days)",
        "",
    ]

    # Interpret skewness
    if log_skewness < -0.5:
        report_lines.append(
            "Distribution is left-skewed (negative skewness) - more extreme negative returns."
        )
    elif log_skewness > 0.5:
        report_lines.append(
            "Distribution is right-skewed (positive skewness) - more extreme positive returns."
        )
    else:
        report_lines.append(
            "Distribution is approximately symmetric (skewness near 0)."
        )

    # Interpret kurtosis
    if log_kurtosis > 3:
        report_lines.append(
            "Distribution is leptokurtic (kurtosis > 3) - fatter tails than normal."
        )
    elif log_kurtosis < 3:
        report_lines.append(
            "Distribution is platykurtic (kurtosis < 3) - thinner tails than normal."
        )
    else:
        report_lines.append("Distribution has normal kurtosis (~3).")

    # Fat tails analysis
    jb_verdict = "NOT normal" if jb_pvalue < 0.05 else "Cannot reject normality"

    if np.isnan(fat_tail_mult):
        fat_tail_line = "Fat tail multiplier: N/A (no expected outliers)"
    else:
        fat_tail_line = f"Fat tail multiplier: {fat_tail_mult:.1f}x"

    report_lines.extend([
        "",
        "FAT TAILS ANALYSIS",
        "-" * 50,
        f"Jarque-Bera test: stat={jb_stat:.1f}, p={jb_pvalue:.4g} → {jb_verdict}",
        "",
        f"Extreme outliers (> ±{threshold}σ): {len(extreme_outliers)} ({extremprocent:.2f}%)",
        f"Expected under normal distribution: {theoretical_outlier_pct:.2f}%",
        fat_tail_line,
    ])

    if np.isnan(tail_ratio):
        report_lines.append("Tail ratio: N/A (insufficient positive outliers)")
    else:
        if tail_ratio > 1.2:
            tail_verdict = "downside dominates"
        elif tail_ratio > 0.8:
            tail_verdict = "roughly symmetric"
        else:
            tail_verdict = "upside dominates"
        report_lines.append(f"Tail ratio (neg/pos magnitude): {tail_ratio:.2f}x → {tail_verdict}")

    report_lines.extend([
        "",
        "EMPIRICAL vs NORMAL TAIL PERCENTILES",
        "-" * 50,
        f"  1st percentile:  empirical {empirical_1pct * 100:+.2f}%  vs  normal {normal_1pct * 100:+.2f}%",
        f"  5th percentile:  empirical {empirical_5pct * 100:+.2f}%  vs  normal {normal_5pct * 100:+.2f}%",
    ])

    if empirical_1pct < normal_1pct:
        ratio_1 = empirical_1pct / normal_1pct if normal_1pct != 0 else np.nan
        report_lines.append(f"  → Worst 1% days are {ratio_1:.1f}x worse than normal predicts")

    report_lines.extend([
        "",
        "OUTLIER DETAILS",
        "-" * 50,
    ])

    # List outliers
    extreme_outliers = extreme_outliers.sort_values(by="LogReturn", ascending=False)
    for _, row in extreme_outliers.iterrows():
        report_lines.append(f"{row['Date'].date()}: {row['LogReturn'] * 100:.2f}%")

    report_lines.append("")
    report_lines.append(f"Rapport skapad: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    # Print report to stdout
    report = "\n".join(report_lines)
    print(report)

    # Save report
    report_filename = f"histogram_{ticker}.txt"
    with open(report_filename, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\nReport saved: {report_filename}")

    # Save CSV
    csv_filename = f"histogram_{ticker}.csv"
    csv_data = {
        "Ticker": [ticker],
        "Observations": [len(logreturns)],
        "Start": [df["Date"].min().date()],
        "End": [df["Date"].max().date()],
        "Daily_Mean": [mu],
        "Daily_Std": [sigma],
        "Annual_Mean": [mu_annual],
        "Annual_Volatility": [sigma_annual],
        "Skewness": [log_skewness],
        "Kurtosis": [log_kurtosis],
        "Outliers": [len(extreme_outliers)],
        "Outlier_Pct": [extremprocent],
        "Fat_Tail_Mult": [fat_tail_mult],
        "JB_Stat": [jb_stat],
        "JB_PValue": [jb_pvalue],
        "Tail_Ratio": [tail_ratio],
        "Empirical_1Pct": [empirical_1pct],
        "Normal_1Pct": [normal_1pct],
        "Empirical_5Pct": [empirical_5pct],
        "Normal_5Pct": [normal_5pct],
    }
    pd.DataFrame(csv_data).to_csv(csv_filename, index=False)
    print(f"CSV saved: {csv_filename}")


if __name__ == "__main__":
    main()
