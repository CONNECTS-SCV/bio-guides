"""pdb_contacts.py — RCSB에서 복합체를 직접 받아 사슬 간 contact 을 계산한다 (Ch.07).

  · `--pdb 1A14` 만 주면 → CIF 를 내려받고 **사슬 목록**을 찍어요(어떤 사슬이 항원인지 확인).
  · `--chain1 H --chain2 N` 을 주면 → 두 사슬 사이 cutoff 이내 residue pair 를 셉니다.
  · 네트워크가 막히면 `--fallback-cif` (저장소에 커밋해 둔 사본)로 이어서 계산해요.

실행:
  python scripts/pdb_contacts.py --pdb 1A14 --outdir 07_interface/my_run/pdb
  python scripts/pdb_contacts.py --pdb 1A14 --chain1 H --chain2 N --cutoff 4.0 \
      --outdir 07_interface/my_run/pdb --out 07_interface/my_run/contacts_H_N.tsv
"""
import argparse
import shutil
import sys
from pathlib import Path

import requests
from Bio.PDB import MMCIFParser, NeighborSearch


def get_cif(pdb_id: str, out_dir: Path, fallback: str = None) -> Path:
    """RCSB에서 CIF 다운로드. 이미 받아 뒀으면 재사용하고, 실패하면 커밋본으로 폴백."""
    pdb_id = pdb_id.upper()
    out = out_dir / f"{pdb_id}.cif"
    if out.exists():
        print(f"[cache] 이미 받아 둔 파일 사용: {out}")
        return out
    url = f"https://files.rcsb.org/download/{pdb_id}.cif"
    try:
        print(f"[download] {url}")
        r = requests.get(url, timeout=60)
        r.raise_for_status()
        out.write_text(r.text)
        print(f"[download] 완료 → {out} ({len(r.text)/1024:.0f} KB)")
        return out
    except Exception as e:
        if fallback and Path(fallback).exists():
            print(f"[네트워크 실패: {type(e).__name__}] 커밋된 사본으로 대체 → {fallback}",
                  file=sys.stderr)
            shutil.copy(fallback, out)
            return out
        raise


def residue_label(res):
    het, resseq, icode = res.id
    return f"{res.get_resname()} {res.parent.id}:{resseq}{icode.strip()}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdb", required=True, help="PDB ID, 예: 1A14")
    ap.add_argument("--chain1", help="첫 번째 사슬 ID")
    ap.add_argument("--chain2", help="두 번째 사슬 ID")
    ap.add_argument("--cutoff", type=float, default=4.0)
    ap.add_argument("--outdir", default="my_run/pdb", help="CIF 저장 폴더")
    ap.add_argument("--out", help="contact 결과 TSV 저장 경로(생략 시 stdout)")
    ap.add_argument("--fallback-cif", help="다운로드 실패 시 사용할 로컬 CIF")
    args = ap.parse_args()

    out_dir = Path(args.outdir)
    out_dir.mkdir(parents=True, exist_ok=True)

    cif_path = get_cif(args.pdb, out_dir, args.fallback_cif)
    parser = MMCIFParser(QUIET=True)
    structure = parser.get_structure(args.pdb.upper(), str(cif_path))
    model = next(structure.get_models())

    chains = {c.id: c for c in model.get_chains()}
    header = f"Chains: {', '.join(sorted(chains.keys()))}"
    print(header)

    if not args.chain1 or not args.chain2:
        print("사슬 목록만 확인했어요. contact 을 계산하려면 --chain1 --chain2 를 주세요.")
        return

    c1, c2 = chains[args.chain1], chains[args.chain2]
    atoms2 = [a for a in c2.get_atoms() if a.element != "H"]
    ns = NeighborSearch(atoms2)

    contacts = {}
    for res1 in c1.get_residues():
        for atom in (a for a in res1.get_atoms() if a.element != "H"):
            for atom2 in ns.search(atom.coord, args.cutoff, level="A"):
                key = (residue_label(res1), residue_label(atom2.get_parent()))
                contacts[key] = contacts.get(key, 0) + 1

    lines = [header, f"Residue contacts within {args.cutoff:.1f} Å"]
    lines += [f"{r1}\t{r2}\tatom_contacts={n}" for (r1, r2), n in sorted(contacts.items())]
    text = "\n".join(lines) + "\n"

    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text)
        print(f"{args.chain1}–{args.chain2}: {len(contacts)} residue pairs, "
              f"{sum(contacts.values())} atom contacts → Wrote: {out}")
    else:
        print("\n".join(lines[1:]))


if __name__ == "__main__":
    main()
