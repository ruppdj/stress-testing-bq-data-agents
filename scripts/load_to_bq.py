"""
Load 6 NBA Parquet files into BigQuery nba_raw dataset.
Sanitizes column names that contain characters BQ rejects (%, /, .).
Supports custom project, dataset, base directory, and dry-runs.
"""

import os
import argparse
import re
import pandas as pd
from google.cloud import bigquery

# Project comes from GCP_PROJECT or --project (no baked-in default — this is
# your project). Data dir comes from NBA_DATA_DIR or --base-dir; the expected
# layout under it is documented in docs/DATA.md (the source data is not
# redistributable, so you assemble it yourself).
DEFAULT_PROJECT = os.environ.get("GCP_PROJECT")
DEFAULT_DATASET = "nba_raw"
DEFAULT_BASE_DIR = os.environ.get("NBA_DATA_DIR", "./data")


def get_tables_config(base_dir: str) -> dict:
    """Returns the absolute paths for the 6 source parquet files."""
    return {
        "player_advanced": os.path.join(base_dir, "nba-playoff-predictor/data/raw/bball_ref/player_stats/player_advanced_all.parquet"),
        "player_pergame":  os.path.join(base_dir, "nba-playoff-predictor/data/raw/bball_ref/player_stats/player_pergame_all.parquet"),
        "team_advanced":   os.path.join(base_dir, "nba-playoff-predictor/data/raw/bball_ref/team_stats/team_advanced_all.parquet"),
        "team_game_logs":  os.path.join(base_dir, "nba-playoff-predictor/data/raw/nba_api/team_game_logs/team_game_logs_all.parquet"),
        "playoff_series":  os.path.join(base_dir, "nba-playoff-predictor/data/raw/bball_ref/playoff_series/playoff_series_all.parquet"),
        "trade_impact":    os.path.join(base_dir, "nba-trade-impact/data/processed/trade_dataset.parquet"),
    }


def repair_text(value):
    """Repair UTF-8-read-as-Latin-1 mojibake (e.g. 'DraÅ¾en' → 'Dražen').

    Only strings whose Latin-1 bytes form valid UTF-8 are rewritten; clean
    strings (including correctly-accented ones) fail the round-trip and come
    back unchanged.
    """
    if not isinstance(value, str):
        return value
    try:
        return value.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return value


def sanitize_col(name: str) -> str:
    s = name.lower()
    s = s.replace('%', '_pct')
    s = s.replace('/', '_per_')
    s = s.replace('.', '')
    s = re.sub(r'[ \-]', '_', s)
    s = re.sub(r'[^a-z0-9_]', '', s)
    s = re.sub(r'_+', '_', s)
    s = s.strip('_')
    if s and s[0].isdigit():
        digit_map = {'2': 'two', '3': 'three'}
        prefix = digit_map.get(s[0], 'n')
        s = f"{prefix}_{s[1:]}"
    return s


def load_table(client: bigquery.Client, project: str, dataset: str, table_name: str, path: str,
               text_repair: bool = True) -> None:
    print(f"\n--- {table_name} ---")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Source file not found at: {path}")

    df = pd.read_parquet(path)
    print(f"  Read {len(df):,} rows x {len(df.columns)} cols from {path.split('/')[-1]}")

    original_cols = list(df.columns)
    df.columns = [sanitize_col(c) for c in df.columns]

    renamed = {o: n for o, n in zip(original_cols, df.columns) if o != n}
    if renamed:
        print(f"  Renamed {len(renamed)} columns:")
        for orig, new in renamed.items():
            print(f"    {orig!r:20s} → {new!r}")

    # Drop duplicate column names (keep first); can arise when two source columns
    # differ only in case (e.g. Team_ID and TEAM_ID both → team_id).
    dupes = df.columns[df.columns.duplicated()].tolist()
    if dupes:
        print(f"  Dropping {len(dupes)} duplicate column(s) after rename: {dupes}")
        df = df.loc[:, ~df.columns.duplicated()]

    if text_repair:
        for col in df.columns[df.dtypes == object]:
            fixed = df[col].map(repair_text)
            changed = df[col].notna() & (fixed != df[col])
            if changed.any():
                print(f"  Repaired mojibake in {col!r}: {int(changed.sum()):,} cells "
                      f"({fixed[changed].nunique()} distinct values)")
                df[col] = fixed

    dest = f"{project}.{dataset}.{table_name}"
    job_config = bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE")
    job = client.load_table_from_dataframe(df, dest, job_config=job_config)
    job.result()

    bq_table = client.get_table(dest)
    print(f"  Loaded → {dest} ({bq_table.num_rows:,} rows)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Load NBA Parquet files into BigQuery nba_raw dataset.")
    parser.add_argument("--project", default=DEFAULT_PROJECT,
                        help="GCP project ID (or set GCP_PROJECT)")
    parser.add_argument("--dataset", default=DEFAULT_DATASET, help="Target BigQuery dataset name")
    parser.add_argument("--base-dir", default=DEFAULT_BASE_DIR, help="Base directory containing raw data folders")
    parser.add_argument("--dry-run", action="store_true", help="Print resolved paths and configurations without running load")
    parser.add_argument("--no-text-repair", action="store_true",
                        help="Skip mojibake repair and load source bytes verbatim "
                             "(reproduces the pre-2026-07-03 ground-zero state, frozen in nba_raw_ground_zero)")
    args = parser.parse_args()

    project = args.project
    if not project:
        raise SystemExit("No GCP project set. Pass --project or set GCP_PROJECT.")
    dataset = args.dataset
    base_dir = os.path.expanduser(args.base_dir)
    tables = get_tables_config(base_dir)

    print(f"Configuration:")
    print(f"  GCP Project: {project}")
    print(f"  Dataset:     {dataset}")
    print(f"  Base Dir:    {base_dir}")
    print(f"  Dry Run:     {args.dry_run}")
    print(f"  Text repair: {not args.no_text_repair}\n")

    if args.dry_run:
        print("Resolved table paths:")
        for table_name, path in tables.items():
            print(f"  {table_name:<20s} -> {path}")
        return

    client = bigquery.Client(project=project)

    for table_name, path in tables.items():
        load_table(client, project, dataset, table_name, path,
                   text_repair=not args.no_text_repair)

    print("\n=== Done. Row count summary ===")
    for table_name in tables:
        dest = f"{project}.{dataset}.{table_name}"
        t = client.get_table(dest)
        print(f"  {table_name:<20s} {t.num_rows:>8,} rows")


if __name__ == "__main__":
    main()
