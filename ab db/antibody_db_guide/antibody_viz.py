"""
antibody_viz.py — 항체 DB·분석 가이드 공용 시각화 모듈

BoltzGen 튜토리얼의 boltzgen_viz.py 와 같은 역할이에요. 모든 챕터 노트북이
repo 루트를 sys.path 에 추가해 이 모듈을 import 하고, 각 챕터 data/ 의
**실제 분석 결과**(임의값 아님)로 표준화된 그림을 그려요.

스타일 규약(BoltzGen 스타일 매칭):
  - 색: liability=보라, charge/pI=주황, hydropathy=청록, 보조=파랑, 임계선=빨강 점선
  - 굵은 suptitle / 굵은 서브플롯 타이틀, dpi=150, grid alpha 0.25

사용:
  import sys; sys.path.insert(0, "<repo_root>")
  from antibody_viz import liability_overview, cdr3_length_distribution, interface_contacts
"""
import csv
import gzip
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def _use_korean_font():
    """한글 라벨이 □ 로 깨지지 않게 — 시스템의 한글 폰트를 찾아 matplotlib 에 등록한다.
    (matplotlib 기본 DejaVu Sans 에는 한글 글리프가 없다. Colab 은 부트스트랩이 fonts-nanum 을 깐다.)"""
    import glob
    from matplotlib import font_manager as fm
    for path in (glob.glob("/usr/share/fonts/**/*Nanum*", recursive=True)
                 + glob.glob("/usr/share/fonts/**/NotoSansCJK*", recursive=True)):
        try:
            fm.fontManager.addfont(path)
        except Exception:
            pass
    have = {f.name for f in fm.fontManager.ttflist}
    for cand in ("NanumGothic", "NanumBarunGothic", "Noto Sans CJK KR",
                 "Noto Sans CJK JP", "Noto Sans KR", "Malgun Gothic", "AppleGothic"):
        if cand in have:
            # font.family 를 '리스트' 로 줘야 matplotlib 이 글리프 단위 폴백을 한다.
            # "sans-serif" + font.sans-serif 조합으로는 폴백이 안 걸려 Å(U+00C5) 가 □ 로 깨진다
            # (NanumGothic 에 U+00C5 글리프가 없음). 한글은 한글 폰트, 나머지는 DejaVu 가 맡는다.
            matplotlib.rcParams["font.family"] = [cand, "DejaVu Sans"]
            matplotlib.rcParams["font.sans-serif"] = [cand, "DejaVu Sans"]
            break
    matplotlib.rcParams["axes.unicode_minus"] = False


_use_korean_font()


# 색상 (boltzgen_viz 와 동일 팔레트)
C_PURPLE = "#8e44ad"   # liability / 구조
C_ORANGE = "#e8883a"   # charge / interface
C_TEAL   = "#1aa090"   # hydropathy / RMSD
C_BLUE   = "#3477b5"   # 보조 (length 등)
C_THR    = "#e74c3c"   # 임계선 빨강
C_PINK   = "#c0508a"   # H-bond 등


def _read_csv(path):
    return list(csv.DictReader(open(path)))


def _f(x):
    try:
        return float(x)
    except Exception:
        return float("nan")


# ---------------------------------------------------------------------------
# 1) Developability — liability_scan.py 결과 (08_developability)
# ---------------------------------------------------------------------------
def liability_overview(csv_path, title, outpath):
    """liability_scan.py CSV → 사슬별 물리화학 + liability 모티프 개요(2x2)."""
    rows = _read_csv(csv_path)
    ids = [r["id"] for r in rows]
    pI = [_f(r.get("pI")) for r in rows]
    gravy = [_f(r.get("gravy")) for r in rows]
    cys = [_f(r.get("cysteine_count")) for r in rows]
    # 모티프 hit 수(세미콜론 구분 위치 문자열 → 개수)
    motif_cols = [c for c in rows[0] if c in
                  ("N_glycosylation_NXS_T", "deamidation_NG", "deamidation_NS", "isomerization_DG")]
    motif_counts = {m: [len([p for p in (r.get(m) or "").split(";") if p]) for r in rows]
                    for m in motif_cols}

    fig, ax = plt.subplots(2, 2, figsize=(11, 8))
    fig.suptitle(title, fontsize=15, fontweight="bold", y=0.98)
    x = range(len(ids))

    ax[0, 0].bar(x, pI, color=C_ORANGE, edgecolor="white", zorder=3)
    ax[0, 0].axhline(7.0, ls="--", color=C_THR, lw=1.5, label="pH 7.0")
    ax[0, 0].set_title("Isoelectric point (pI)", fontweight="bold")
    ax[0, 0].set_ylabel("pI"); ax[0, 0].legend(fontsize=8)

    ax[0, 1].bar(x, gravy, color=C_TEAL, edgecolor="white", zorder=3)
    ax[0, 1].axhline(0.0, ls="--", color=C_THR, lw=1.5, label="neutral (0)")
    ax[0, 1].set_title("Hydropathy (GRAVY)", fontweight="bold")
    ax[0, 1].set_ylabel("GRAVY"); ax[0, 1].legend(fontsize=8)

    ax[1, 0].bar(x, cys, color=C_PURPLE, edgecolor="white", zorder=3)
    ax[1, 0].set_title("Cysteine count (even = paired)", fontweight="bold")
    ax[1, 0].set_ylabel("# Cys")

    bottoms = [0] * len(ids)
    palette = [C_PURPLE, C_ORANGE, C_TEAL, C_PINK]
    for i, (m, vals) in enumerate(motif_counts.items()):
        ax[1, 1].bar(x, vals, bottom=bottoms, label=m.replace("_", " "),
                     color=palette[i % len(palette)], edgecolor="white", zorder=3)
        bottoms = [b + v for b, v in zip(bottoms, vals)]
    ax[1, 1].set_title("Liability motif hits (stacked)", fontweight="bold")
    ax[1, 1].set_ylabel("# motif sites"); ax[1, 1].legend(fontsize=7)

    for a in ax.flat:
        a.set_xticks(list(x)); a.set_xticklabels(ids, fontsize=9)
        a.grid(axis="y", alpha=0.25, zorder=0)
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    fig.savefig(outpath, dpi=150, bbox_inches="tight"); plt.close(fig)
    return outpath


# ---------------------------------------------------------------------------
# 2) Repertoire — oas_cdr3_length.py 결과 (09_repertoire)
# ---------------------------------------------------------------------------
def cdr3_length_distribution(summary_csv, title, outpath, highlight_len=None,
                             highlight_label="candidate"):
    """oas_cdr3_length_summary.csv (cdr3_len,count) → 분포 막대 + 후보 위치 강조."""
    rows = _read_csv(summary_csv)
    lens = [int(_f(r["cdr3_len"])) for r in rows]
    cnt = [int(_f(r["count"])) for r in rows]
    total = sum(cnt)
    mean = sum(l * c for l, c in zip(lens, cnt)) / total if total else 0

    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.bar(lens, cnt, color=C_BLUE, edgecolor="white", width=0.85, zorder=3)
    ax.axvline(mean, ls="--", color=C_THR, lw=1.6, label=f"mean = {mean:.1f} aa")
    if highlight_len is not None:
        ax.axvline(highlight_len, ls="-", color=C_ORANGE, lw=2.4,
                   label=f"{highlight_label} = {highlight_len} aa")
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.set_xlabel("CDR3 length (aa)", fontsize=11)
    ax.set_ylabel(f"Count (n = {total})", fontsize=11)
    ax.grid(axis="y", alpha=0.25, zorder=0); ax.legend(fontsize=9)
    fig.tight_layout(); fig.savefig(outpath, dpi=150, bbox_inches="tight"); plt.close(fig)
    return outpath


# ---------------------------------------------------------------------------
# 3) Interface — pdb_contacts.py 결과 (07_interface)
# ---------------------------------------------------------------------------
def _parse_contacts(tsv_path):
    """pdb_contacts.py stdout(tsv) → [(ab_res, partner_res, atom_contacts), ...]."""
    out = []
    for line in open(tsv_path):
        line = line.rstrip("\n")
        if "\tatom_contacts=" not in line:
            continue
        left, n = line.split("atom_contacts=")
        a, b = left.rstrip("\t").split("\t")
        out.append((a.strip(), b.strip(), int(n)))
    return out


def interface_contacts(tsv_path, title, outpath, top=15):
    """contact tsv → 원자접촉 많은 residue pair 상위 막대."""
    rows = _parse_contacts(tsv_path)
    rows.sort(key=lambda r: r[2], reverse=True)
    rows = rows[:top]
    labels = [f"{a}\n↔ {b}" for a, b, _ in rows]
    vals = [n for _, _, n in rows]

    fig, ax = plt.subplots(figsize=(11, 6))
    ax.barh(range(len(rows)), vals, color=C_ORANGE, edgecolor="white", zorder=3)
    ax.set_yticks(range(len(rows))); ax.set_yticklabels(labels, fontsize=8)
    ax.invert_yaxis()
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.set_xlabel("Atom contacts (≤ cutoff)", fontsize=11)
    ax.grid(axis="x", alpha=0.25, zorder=0)
    fig.tight_layout(); fig.savefig(outpath, dpi=150, bbox_inches="tight"); plt.close(fig)
    return outpath


# ---------------------------------------------------------------------------
# 4) Structure prediction confidence — IgFold PDB (06_structure)
# ---------------------------------------------------------------------------
def structure_confidence(pdb_path, title, outpath):
    """IgFold PDB의 CA B-factor(잔기별 예측오차, Å) → 사슬별 신뢰도 프로파일.
    IgFold는 예측 RMSD(낮을수록 신뢰↑)를 B-factor 컬럼에 기록해요(CDR loop에서 큰 경향)."""
    chains = {}
    for line in open(pdb_path):
        if not line.startswith("ATOM") or line[12:16].strip() != "CA":
            continue
        ch = line[21]
        resseq = int(line[22:26])
        bfac = float(line[60:66])
        chains.setdefault(ch, []).append((resseq, bfac))

    fig, ax = plt.subplots(figsize=(11, 5))
    palette = {"H": C_PURPLE, "L": C_ORANGE}
    for i, (ch, vals) in enumerate(sorted(chains.items())):
        vals.sort()
        xs = [v[0] for v in vals]; ys = [v[1] for v in vals]
        ax.plot(xs, ys, marker="o", ms=3, lw=1.4,
                color=palette.get(ch, [C_TEAL, C_BLUE, C_PINK][i % 3]),
                label=f"chain {ch} (mean {sum(ys)/len(ys):.2f} Å)")
    ax.axhline(1.0, ls="--", color=C_THR, lw=1.5, label="confident (<1 Å)")
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.set_xlabel("Residue number", fontsize=11)
    ax.set_ylabel("Predicted error / B-factor (Å)", fontsize=11)
    ax.grid(alpha=0.25, zorder=0); ax.legend(fontsize=9)
    fig.tight_layout(); fig.savefig(outpath, dpi=150, bbox_inches="tight"); plt.close(fig)
    return outpath


# ---------------------------------------------------------------------------
# 5) Humanness — BioPhi/Sapiens 결과 (05_humanness)
# ---------------------------------------------------------------------------
def _read_fasta(path):
    d, name = {}, None
    for line in open(path):
        line = line.strip()
        if line.startswith(">"):
            name = line[1:].split()[0]; d[name] = ""
        elif name:
            d[name] += line
    return d


def humanness_overview(scores_csv, orig_fa, hum_fa, title, outpath):
    """Sapiens score 행렬 + 원본/humanized FASTA → 사슬별 humanness + 변이수 비교."""
    # 사슬별 입력 잔기 평균확률 = humanness proxy
    rows = _read_csv(scores_csv)
    hum_by_chain = {}
    for r in rows:
        ch = r["chain"]; aa = r["input_aa"]
        if aa in r:
            hum_by_chain.setdefault(ch, []).append(_f(r[aa]))
    chains = sorted(hum_by_chain)
    humanness = [sum(hum_by_chain[c]) / len(hum_by_chain[c]) for c in chains]

    orig = _read_fasta(orig_fa); hum = _read_fasta(hum_fa)
    o_list, h_list = list(orig.values()), list(hum.values())
    nmut = []
    for i, c in enumerate(chains):
        o, h = o_list[i], h_list[i]
        nmut.append(sum(1 for a, b in zip(o, h) if a != b) if len(o) == len(h) else 0)

    fig, ax = plt.subplots(1, 2, figsize=(11, 4.6))
    fig.suptitle(title, fontsize=14, fontweight="bold", y=1.0)
    x = range(len(chains))
    ax[0].bar(x, humanness, color=C_PURPLE, edgecolor="white", zorder=3)
    ax[0].axhline(0.8, ls="--", color=C_THR, lw=1.5, label="human-like (~0.8)")
    ax[0].set_title("Sapiens humanness (mean)", fontweight="bold")
    ax[0].set_ylabel("mean P(input residue)"); ax[0].set_ylim(0, 1); ax[0].legend(fontsize=8)
    ax[1].bar(x, nmut, color=C_ORANGE, edgecolor="white", zorder=3)
    ax[1].set_title("Humanizing mutations (orig → humanized)", fontweight="bold")
    ax[1].set_ylabel("# substitutions")
    for a in ax:
        a.set_xticks(list(x)); a.set_xticklabels([f"chain {c}" for c in chains])
        a.grid(axis="y", alpha=0.25, zorder=0)
    fig.tight_layout(); fig.savefig(outpath, dpi=150, bbox_inches="tight"); plt.close(fig)
    return outpath


if __name__ == "__main__":
    import sys
    print("antibody_viz: liability_overview / cdr3_length_distribution / "
          "interface_contacts / structure_confidence / humanness_overview")
    if len(sys.argv) > 1:
        print("self-test on:", sys.argv[1])
