"""oas_cdr3_length.py — OAS 서열 표에서 CDR3 길이 분포를 집계한다 (Ch.09).

OAS 원본 data unit(csv.gz)은 **첫 줄이 메타데이터(JSON 한 줄)**, 둘째 줄이 헤더예요.
그래서 그대로 읽으면 컬럼을 못 찾습니다 — 이 스크립트가 자동으로 감지해 건너뜁니다.
`fetch_oas_unit.py` 가 만든 슬림 TSV.gz 도 그대로 받습니다.

실행:
  python scripts/oas_cdr3_length.py 09_repertoire/my_run/oas_subset.tsv.gz \
      --column cdr3_aa --out 09_repertoire/my_run/oas_cdr3_length_summary.csv
"""
import argparse
import gzip
import io

import pandas as pd


def read_table(path):
    """OAS 메타데이터 첫 줄을 자동 감지해 건너뛰고 표를 읽는다."""
    path = str(path)
    opener = gzip.open if path.endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8", errors="replace") as fh:
        text = fh.read()

    first = text.split("\n", 1)[0]
    skip = 1 if first.lstrip().startswith(('"{', "{")) else 0
    if skip:
        print("[OAS] 첫 줄이 메타데이터라 건너뜁니다:", first[:90] + " ...")

    sep = "\t" if ".tsv" in path else ","
    return pd.read_csv(io.StringIO(text), sep=sep, skiprows=skip, low_memory=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("table", help="OAS CSV/TSV(.gz)")
    ap.add_argument("--column", default=None, help="CDR3 아미노산 컬럼명")
    ap.add_argument("--out", default="cdr3_length_summary.csv")
    args = ap.parse_args()

    df = read_table(args.table)

    candidates = [args.column, "cdr3_aa", "CDR3_aa", "cdr3", "junction_aa"]
    col = next((c for c in candidates if c and c in df.columns), None)
    if col is None:
        raise SystemExit(f"CDR3 컬럼을 못 찾았어요. 컬럼: {list(df.columns)[:30]}")

    df = df[df[col].notna()].copy()
    df["cdr3_len"] = df[col].astype(str).str.len()

    summary = (df.groupby("cdr3_len").size().reset_index(name="count")
                 .sort_values("cdr3_len"))
    summary.to_csv(args.out, index=False)

    n = int(summary["count"].sum())
    mean = float((summary["cdr3_len"] * summary["count"]).sum() / n)
    print(f"n={n:,} 서열 | 평균 CDR3 {mean:.2f} aa | "
          f"범위 {summary.cdr3_len.min()}–{summary.cdr3_len.max()} aa")
    print("Wrote:", args.out)


if __name__ == "__main__":
    main()
