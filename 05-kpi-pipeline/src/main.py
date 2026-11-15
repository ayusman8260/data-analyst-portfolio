"""Run the pipeline: extract -> quality checks -> transform -> report.

    python src/main.py --data-dir data
    python src/main.py --demo          # uses synthetic sample data (for CI / smoke tests)
"""
import argparse
import logging
import sys
import tempfile

import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from extract import load_tables          # noqa: E402
from report import write_report          # noqa: E402
from transform import (DataQualityError, build_order_facts, check_quality,  # noqa: E402
                       repeat_rate, reporting_window, weekly_kpis)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("pipeline")


def run(data_dir, out_dir, as_of=None):
    tables = load_tables(data_dir)
    check_quality(tables)
    facts = build_order_facts(tables)
    all_kpis = weekly_kpis(facts)
    if as_of is not None:   # keep only weeks that END on or before the as-of date
        all_kpis = all_kpis[all_kpis.index + pd.Timedelta(days=6) <= pd.Timestamp(as_of)]
    kpis, dropped = reporting_window(all_kpis)
    if dropped:
        log.warning("Excluded %d trailing incomplete week(s) from the report", dropped)
    path = write_report(kpis, repeat_rate(tables), out_dir, dropped)
    all_kpis.to_csv(Path(out_dir) / "weekly_kpis_all.csv")
    log.info("Report written to %s", path)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default="data")
    ap.add_argument("--out-dir", default="outputs")
    ap.add_argument("--demo", action="store_true", help="use synthetic sample data")
    ap.add_argument("--as-of", default=None, help="report only on weeks ending on or before this date (YYYY-MM-DD)")
    args = ap.parse_args()
    try:
        if args.demo:
            from make_sample_data import olist
            tmp = Path(tempfile.mkdtemp())
            olist(tmp)
            run(tmp, args.out_dir, args.as_of)
        else:
            run(args.data_dir, args.out_dir, args.as_of)
    except DataQualityError as e:
        log.error("DATA QUALITY FAILURE: %s", e)
        sys.exit(1)
