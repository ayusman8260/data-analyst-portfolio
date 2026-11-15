"""Run every query in ./sql against olist.db, print results and save CSVs to ./outputs."""
import sqlite3
import sys
from pathlib import Path
import pandas as pd

def main(db="olist.db"):
    con = sqlite3.connect(db)
    Path("outputs").mkdir(exist_ok=True)
    for f in sorted(Path("sql").glob("q*.sql")):
        df = pd.read_sql_query(f.read_text(), con)
        df.to_csv(Path("outputs") / f"{f.stem}.csv", index=False)
        print(f"\n=== {f.stem} ===")
        print(df.head(10).to_string(index=False))
    con.close()

if __name__ == "__main__":
    main(*sys.argv[1:2])
