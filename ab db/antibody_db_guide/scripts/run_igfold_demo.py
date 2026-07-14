"""run_igfold_demo.py — IgFold로 항체 Fv 구조를 직접 예측한다 (Ch.06).

pip 로만 설치돼요(`pip install igfold "transformers==4.36.2"`). GPU가 있으면 쓰고,
없거나 CUDA 초기화가 실패하면 CPU로 돕니다. 실측 함정 두 가지를 코드에서 그대로 처리해요.

  ① torch ≥ 2.6 의 `weights_only=True` 기본값 → IgFold 체크포인트 로드 실패
     → `torch.load` 를 `weights_only=False` 로 감싸요 (신뢰된 패키지 가중치).
  ② transformers 5.x → 체크포인트에 pickle 된 토크나이저 클래스(Trie·BasicTokenizer)가
     사라져 unpickle 이 실패 → `transformers==4.36.2` 를 쓰세요(노트북이 자동으로 맞춰줘요).

실행:
  python scripts/run_igfold_demo.py --fasta 06_structure/data/demo_mab.fa \
      --out 06_structure/my_run/demo_antibody_igfold.pdb
"""
import argparse
import os
import pathlib
import sys
import time


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
    ap.add_argument("--fasta", default="data/demo_mab.fa",
                    help="첫 서열=heavy(H), 둘째 서열=light(L)")
    ap.add_argument("--out", default="my_run/demo_antibody_igfold.pdb")
    ap.add_argument("--cpu", action="store_true", help="GPU를 무시하고 CPU로 강제")
    args = ap.parse_args()

    if args.cpu:
        os.environ["CUDA_VISIBLE_DEVICES"] = ""

    import torch
    # ① torch >= 2.6 의 weights_only 기본값 회피
    _orig_load = torch.load
    torch.load = lambda *a, **k: _orig_load(*a, **{**k, "weights_only": False})

    import transformers
    if not transformers.__version__.startswith("4."):
        print(f"[주의] transformers {transformers.__version__} 에서는 IgFold 체크포인트 unpickle 이 "
              f"실패해요 → pip install \"transformers==4.36.2\"", file=sys.stderr)

    from igfold import IgFoldRunner

    records = list(read_fasta(args.fasta).items())
    assert len(records) >= 2, "heavy/light 두 서열이 필요해요"
    sequences = {"H": records[0][1], "L": records[1][1]}

    out = pathlib.Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    t0 = time.time()
    runner = IgFoldRunner()
    runner.fold(str(out), sequences=sequences, do_refine=False, do_renum=True)
    elapsed = time.time() - t0

    n_atoms = sum(1 for line in open(out) if line.startswith("ATOM"))
    device = "GPU" if (torch.cuda.is_available() and not args.cpu) else "CPU"
    print(f"Wrote: {out}  ({n_atoms} atoms, {device} {elapsed:.1f}s)")


if __name__ == "__main__":
    main()
