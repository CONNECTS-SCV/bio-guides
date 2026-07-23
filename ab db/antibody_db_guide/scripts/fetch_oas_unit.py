"""fetch_oas_unit.py — OAS(Observed Antibody Space) data unit을 직접 내려받는다 (Ch.09).

OAS는 data unit 단위(study/run/사슬/isotype)로 gzip CSV를 공개해요. 파일 **첫 줄은
메타데이터(JSON 한 줄)**, 둘째 줄이 진짜 헤더예요 — 그래서 `skiprows=1`이 필요합니다.

기본 unit (이 과정의 레퍼런스와 동일):
  Eliyahu et al. 2018 · human PBMC unsorted B cells · heavy chain IgM · run ERR2843400
  → productive 17,807 서열

출력: locus / v_call / j_call / cdr3_aa 만 남긴 슬림 TSV.gz (원본 97컬럼은 너무 커요)

실행:
  python scripts/fetch_oas_unit.py --out 09_repertoire/my_run/oas_subset.tsv.gz
"""
import argparse
import gzip
import io
import json
import pathlib
import sys
import urllib.request

DEFAULT_URL = ("https://opig.stats.ox.ac.uk/webapps/ngsdb/unpaired/"
               "Eliyahu_2018/csv/ERR2843400_Heavy_IGHM.csv.gz")
KEEP = ["locus", "v_call", "j_call", "cdr3_aa"]


def download(url):
    req = urllib.request.Request(url, headers={"User-Agent": "antibody-db-guide/1.0"})
    with urllib.request.urlopen(req, timeout=180) as r:
        return r.read()


def main():
    import pandas as pd

    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default=DEFAULT_URL, help="OAS unpaired data unit URL(.csv.gz)")
    ap.add_argument("--out", default="oas_subset.tsv.gz")
    args = ap.parse_args()

    raw = download(args.url)
    text = gzip.decompress(raw).decode("utf-8", errors="replace")

    # 1) 첫 줄 = OAS 메타데이터(JSON) — 출처를 그대로 찍어줘요
    meta_line = text.split("\n", 1)[0].strip()
    try:
        meta = json.loads(meta_line.strip('"').replace('""', '"'))
        # dict 를 그대로 찍으면 따옴표·중괄호가 섞여 한 줄로 흘러가요. 한 항목 한 줄로 세워 둡니다.
        LABEL = {"Species": "종", "BSource": "채취 조직", "BType": "B세포 종류",
                 "Disease": "질환/코호트", "Chain": "사슬", "Isotype": "isotype",
                 "Author": "출처 논문", "Link": "DOI"}
        print("[OAS metadata] 이 unit 이 어디서 온 데이터인지", file=sys.stderr)
        for k, ko in LABEL.items():
            if k in meta:
                print(f"    {ko:<12s} {meta.get(k)}", file=sys.stderr)
    except Exception:
        print("[OAS metadata] 파싱 실패(무시하고 진행)", file=sys.stderr)

    # 2) 둘째 줄부터가 표 (skiprows=1)
    df = pd.read_csv(io.StringIO(text), skiprows=1, low_memory=False)
    df = df[df["cdr3_aa"].notna()]
    slim = df[[c for c in KEEP if c in df.columns]].copy()

    out = pathlib.Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    slim.to_csv(out, sep="\t", index=False, compression="gzip")
    print(f"Wrote: {out}  ({len(slim):,} sequences, {out.stat().st_size/1024:.0f} KB)",
          file=sys.stderr)


if __name__ == "__main__":
    main()
