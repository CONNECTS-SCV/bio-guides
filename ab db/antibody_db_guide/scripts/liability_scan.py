"""liability_scan.py — 항체 서열의 liability motif·물리화학 지표를 스캔한다 (Ch.08).

실행:
  python scripts/liability_scan.py 08_developability/data/demo_mab.fa \
      --out 08_developability/my_run/liability.csv     # --out 생략 시 stdout
"""
import argparse
import csv
import pathlib
import re
import sys
from Bio import SeqIO
from Bio.SeqUtils.ProtParam import ProteinAnalysis

MOTIFS = {
    "N_glycosylation_NXS_T": re.compile(r"N[^P][ST]"),
    "deamidation_NG": re.compile(r"NG"),
    "deamidation_NS": re.compile(r"NS"),
    "isomerization_DG": re.compile(r"DG"),
}

STANDARD_AA = set("ACDEFGHIKLMNPQRSTVWY")

def find_motifs(seq, pattern):
    return [m.start() + 1 for m in pattern.finditer(seq)]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("fasta")
    ap.add_argument("--out", help="CSV 저장 경로(생략 시 stdout)")
    args = ap.parse_args()

    if args.out:
        out_path = pathlib.Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        fh = out_path.open("w", newline="", encoding="utf-8")
    else:
        out_path, fh = None, sys.stdout

    writer = csv.writer(fh)
    writer.writerow([
        "id", "length", "molecular_weight", "pI", "gravy",
        "cysteine_count", "odd_cysteine_flag", "methionine_count",
        "tryptophan_count", "ambiguous_residues", *MOTIFS.keys()
    ])

    for rec in SeqIO.parse(args.fasta, "fasta"):
        seq = str(rec.seq).replace("*", "").upper()
        # X, B, Z, U, O 같은 비표준/모호 잔기는 ProteinAnalysis에서 예외를 일으키므로
        # 별도로 기록하고, 물리화학 계산은 표준 20종만으로 수행한다.
        ambiguous = sorted({aa for aa in seq if aa not in STANDARD_AA})
        clean = "".join(aa for aa in seq if aa in STANDARD_AA)
        analysis = ProteinAnalysis(clean)

        motif_hits = []
        for name, pattern in MOTIFS.items():
            positions = find_motifs(seq, pattern)
            motif_hits.append(";".join(map(str, positions)) if positions else "")

        cys = seq.count("C")
        writer.writerow([
            rec.id,
            len(seq),
            round(analysis.molecular_weight(), 2),
            round(analysis.isoelectric_point(), 2),
            round(analysis.gravy(), 3),
            cys,
            "YES" if cys % 2 == 1 else "NO",
            seq.count("M"),
            seq.count("W"),
            ";".join(ambiguous) if ambiguous else "",
            *motif_hits
        ])

    if out_path:
        fh.close()
        print("Wrote:", out_path)

if __name__ == "__main__":
    main()
