"""sapiens_humanize.py — Sapiens(BioPhi 언어모델)로 humanness 점수 + humanized 서열을 만든다 (Ch.05).

BioPhi CLI(`biophi sapiens`)는 **bioconda 전용**이라 Colab(pip)에서 못 써요. 하지만 BioPhi가
내부에서 쓰는 두 부품은 **둘 다 PyPI에 있어요**:

  · `sapiens`  — 항체 언어모델 (위치별 아미노산 확률)
  · `abnumber` — 항체 numbering / CDR 정의 (ANARCI + HMMER 사용)

BioPhi의 Sapiens humanization 알고리즘 그대로 재현합니다.
  1) 위치별 확률 행렬 예측  → 각 위치에서 확률 최대 아미노산으로 서열 재구성
  2) 원본 CDR을 다시 이식(graft)  → framework 만 사람스럽게 바꾸고 CDR은 보존
  (BioPhi 기본값: scheme=kabat, cdr_definition=kabat, iterations=1, humanize_cdrs=False)

출력 (BioPhi CLI와 같은 스키마)
  --scores-out : raw_pos,id,chain,input_aa,A..Y  (위치별 20종 확률)
  --fasta-out  : humanized FASTA

실행:
  python scripts/sapiens_humanize.py 05_humanness/data/demo_mab.fa \
      --scores-out 05_humanness/my_run/demo_sapiens_scores.csv \
      --fasta-out  05_humanness/my_run/demo_humanized.fa
"""
import argparse
import pathlib
import sys
import time

AA = list("ACDEFGHIKLMNPQRSTVWY")


def read_fasta(path):
    seqs, name = {}, None
    for line in open(path):
        line = line.strip()
        if line.startswith(">"):
            name = line[1:].split()[0]
            seqs[name] = ""
        elif name:
            seqs[name] += line
    return seqs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("fasta")
    ap.add_argument("--scores-out", default="demo_sapiens_scores.csv")
    ap.add_argument("--fasta-out", default="demo_humanized.fa")
    ap.add_argument("--iterations", type=int, default=1)
    args = ap.parse_args()

    import pandas as pd
    import sapiens
    from abnumber import Chain

    seqs = read_fasta(args.fasta)
    score_frames, humanized = [], []

    for name, seq in seqs.items():
        t0 = time.time()
        parental = Chain(seq, scheme="kabat", cdr_definition="kabat")
        chain_label = "H" if parental.is_heavy_chain() else "L"

        humanized_chain = parental.clone()
        pred = None
        for _ in range(args.iterations):
            # ① 위치별 아미노산 확률 (rows=위치, cols=20종)
            pred = sapiens.predict_scores(humanized_chain.seq, humanized_chain.chain_type)
            # ② 각 위치에서 확률이 가장 높은 아미노산 → humanized 서열
            best = "".join(pred.idxmax(axis=1).values)
            humanized_chain = parental.clone(best)
            # ③ 원본 CDR 을 다시 이식 (결합 부위는 건드리지 않기)
            humanized_chain = parental.graft_cdrs_onto(humanized_chain)

        nmut = sum(1 for a, b in zip(parental.seq, humanized_chain.seq) if a != b)
        p_input = [row[aa] for aa, (_, row) in zip(parental.seq, pred.iterrows())]
        print(f"{name}: chain={chain_label} len={len(seq)} "
              f"humanness={sum(p_input)/len(p_input):.3f} mutations={nmut} "
              f"({time.time()-t0:.1f}s)", file=sys.stderr)

        frame = pred.copy()
        frame.insert(0, "input_aa", list(parental.seq))
        frame.insert(0, "chain", chain_label)
        frame.insert(0, "id", name)
        frame.insert(0, "raw_pos", range(len(parental.seq)))
        score_frames.append(frame)
        humanized.append((name, chain_label, humanized_chain.seq))

    scores = pd.concat(score_frames, ignore_index=True)[["raw_pos", "id", "chain", "input_aa"] + AA]
    out_scores = pathlib.Path(args.scores_out)
    out_scores.parent.mkdir(parents=True, exist_ok=True)
    scores.to_csv(out_scores, index=False)

    out_fa = pathlib.Path(args.fasta_out)
    out_fa.parent.mkdir(parents=True, exist_ok=True)
    with out_fa.open("w") as fh:
        for name, chain_label, seq in humanized:
            fh.write(f">{name} V{chain_label} Sapiens {args.iterations}iter parental Kabat CDRs\n{seq}\n")

    print("Wrote:", out_scores, "and", out_fa, file=sys.stderr)


if __name__ == "__main__":
    main()
