"""
humanization_viz.py — 항체 humanization 결과 시각화 공용 모듈

스타일 규약:
  - parental = 회색 계열 / humanized(도구별) = 고정 색상 (도구마다 항상 같은 색)
  - 임계·기준선: 빨간 점선 + 범례
  - 굵은 suptitle / 굵은 서브플롯 타이틀, y축 그리드 alpha 0.25

데이터는 **호출자가 준다** — 이 모듈은 어떤 수치도 내장하지 않는다.
모든 함수는 pandas.DataFrame 또는 dict 리스트(rows)를 받는다.

사용:
    from humanization_viz import humanness_bars, mutation_map, nativeness_panel, liability_overview

    humanness_bars(df, "Humanness: parental vs humanized", "05_humanness.png")
    mutation_map(df, "Tool consensus by position (VH)", "06_mutation_map.png")
    nativeness_panel(df, "AbNatiV nativeness (FR / CDR)", "07_nativeness.png")
    liability_overview(df, "Developability liability motifs", "09_liability.png")
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

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
            # 단일 family 로 바꾸면 한글은 살지만 Å 같은 글리프가 깨집니다.
            # 폴백 목록으로 둬서 한글은 한글 폰트가, 나머지는 DejaVu 가 맡게 합니다.
            matplotlib.rcParams["font.family"] = "sans-serif"
            matplotlib.rcParams["font.sans-serif"] = [cand, "DejaVu Sans"]
            break
    matplotlib.rcParams["axes.unicode_minus"] = False


_use_korean_font()


# ── 색상 (도구별 고정) ────────────────────────────────────────────────
C_PARENTAL = "#8f9aa6"   # 회색 — parental (기준선)
C_SAPIENS  = "#8e44ad"   # 보라 — BioPhi/Sapiens
C_HUMATCH  = "#e8883a"   # 주황 — Humatch
C_ANTHROAB = "#1aa090"   # 청록 — AnthroAb
C_ABNATIV  = "#3477b5"   # 파랑 — AbNatiV / nativeness
C_THR      = "#e74c3c"   # 빨강 — 기준선·경고
C_CDR      = "#c0508a"   # 자홍 — CDR 영역
C_CONSENSUS = "#f1c40f"  # 금색 — 도구 합의 위치 배경
C_MISC     = "#7f8c8d"

TOOL_COLORS = {
    "parental": C_PARENTAL,
    "sapiens": C_SAPIENS, "biophi": C_SAPIENS, "biophi/sapiens": C_SAPIENS,
    "humatch": C_HUMATCH,
    "anthroab": C_ANTHROAB,
    "abnativ": C_ABNATIV,
}
_CYCLE = [C_SAPIENS, C_HUMATCH, C_ANTHROAB, C_ABNATIV, C_CDR, C_MISC]


def tool_color(name, i=0):
    """도구 이름 → 고정 색. 모르는 이름이면 순환 팔레트."""
    return TOOL_COLORS.get(str(name).strip().lower(), _CYCLE[i % len(_CYCLE)])


def _records(rows):
    """DataFrame · dict 리스트 · dict(of lists) 무엇이 와도 dict 리스트로."""
    if hasattr(rows, "to_dict"):          # pandas DataFrame
        return rows.to_dict("records")
    if isinstance(rows, dict):            # {col: [...]} 형태
        keys = list(rows)
        n = len(rows[keys[0]])
        return [{k: rows[k][i] for k in keys} for i in range(n)]
    return list(rows)


def _get(rec, *names, default=None):
    """컬럼명이 조금씩 달라도 (chain/Chain, humanized/human) 견디게."""
    for n in names:
        if n in rec and rec[n] is not None:
            return rec[n]
    return default


def _save(fig, outpath):
    fig.savefig(outpath, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return outpath


# ── 1) humanness: parental vs humanized (체인별) ──────────────────────
def humanness_bars(rows, title, outpath, ylabel="Humanness score", thr=None):
    """체인별 parental vs humanized humanness 비교 바.

    rows 컬럼: chain, parental, humanized   (예: VH / 0.694 / 0.815)
    """
    recs = _records(rows)
    chains = [str(_get(r, "chain", "Chain", default="?")) for r in recs]
    par = [float(_get(r, "parental", "Parental", default=float("nan"))) for r in recs]
    hum = [float(_get(r, "humanized", "Humanized", "humanised", default=float("nan"))) for r in recs]

    x = range(len(chains))
    w = 0.36
    fig, ax = plt.subplots(figsize=(1.9 * max(len(chains), 2) + 3, 5))
    ax.bar([i - w / 2 for i in x], par, width=w, color=C_PARENTAL,
           edgecolor="white", label="parental", zorder=3)
    ax.bar([i + w / 2 for i in x], hum, width=w, color=C_SAPIENS,
           edgecolor="white", label="humanized", zorder=3)

    for i, (p, h) in enumerate(zip(par, hum)):
        ax.annotate(f"{p:.3f}", (i - w / 2, p), ha="center", va="bottom", fontsize=9)
        ax.annotate(f"{h:.3f}", (i + w / 2, h), ha="center", va="bottom", fontsize=9,
                    fontweight="bold")
        if p == p and h == h:
            ax.annotate(f"▲ +{h - p:.3f}", (i, max(p, h)), ha="center", va="bottom",
                        fontsize=9, color=C_SAPIENS, fontweight="bold",
                        xytext=(0, 16), textcoords="offset points")

    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.set_xticks(list(x)); ax.set_xticklabels(chains, fontsize=11)
    ax.set_ylabel(ylabel, fontsize=10)
    ax.set_ylim(0, 1.0)
    ax.grid(axis="y", alpha=0.25, zorder=0)
    if thr is not None:
        ax.axhline(thr, ls="--", color=C_THR, lw=1.6, zorder=4, label=f"threshold ({thr})")
    ax.legend(fontsize=9, loc="lower right")
    fig.tight_layout()
    return _save(fig, outpath)


# ── 2) mutation map: 위치 × 도구 (합의 시각화) ────────────────────────
def mutation_map(rows, title, outpath, cdr_spans=None):
    """위치별 도구 제안 mutation 지도. 같은 위치에 같은 잔기를 제안한 도구가 많을수록
    '합의(consensus)'로 강조된다.

    rows 컬럼: position, tool, to(제안 잔기)  [+ 선택: from(parental 잔기)]
    cdr_spans: [(start, end), ...] 보호 구간을 배경 음영으로 표시(선택).
    """
    recs = _records(rows)
    if not recs:
        raise ValueError("mutation_map: rows 가 비어 있습니다")

    pos = sorted({int(_get(r, "position", "pos")) for r in recs})
    tools = list(dict.fromkeys(str(_get(r, "tool", "method")) for r in recs))
    pidx = {p: i for i, p in enumerate(pos)}
    tidx = {t: i for i, t in enumerate(tools)}

    # 위치별 제안 잔기 집합 → 모든 도구가 같은 잔기를 낸 위치 = consensus
    by_pos = {}
    for r in recs:
        by_pos.setdefault(int(_get(r, "position", "pos")), []).append(
            str(_get(r, "to", "proposed", "residue", default="?")))
    consensus = {p for p, v in by_pos.items() if len(v) == len(tools) and len(set(v)) == 1}

    fig, ax = plt.subplots(figsize=(max(7, 0.85 * len(pos) + 3), 1.1 * len(tools) + 2.6))

    for span in (cdr_spans or []):
        lo, hi = span
        xs = [pidx[p] for p in pos if lo <= p <= hi]
        if xs:
            ax.axvspan(min(xs) - 0.5, max(xs) + 0.5, color=C_CDR, alpha=0.10, zorder=0)

    for p in consensus:
        ax.axvspan(pidx[p] - 0.5, pidx[p] + 0.5, color=C_CONSENSUS, alpha=0.22, zorder=0)

    for i, t in enumerate(tools):
        color = tool_color(t, i)
        for r in recs:
            if str(_get(r, "tool", "method")) != t:
                continue
            p = int(_get(r, "position", "pos"))
            aa = str(_get(r, "to", "proposed", "residue", default="?"))
            x, y = pidx[p], tidx[t]
            hit = p in consensus
            ax.scatter([x], [y], s=430, color=color, zorder=3,
                       edgecolor=C_THR if hit else "white", linewidth=2.0 if hit else 0.8)
            ax.annotate(aa, (x, y), ha="center", va="center", fontsize=10,
                        fontweight="bold", color="white", zorder=4)

    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.set_xticks(range(len(pos)))
    ax.set_xticklabels([str(p) for p in pos], fontsize=10)
    ax.set_yticks(range(len(tools)))
    ax.set_yticklabels(tools, fontsize=10)
    ax.set_xlabel("Position (IMGT)", fontsize=10)
    ax.set_xlim(-0.6, len(pos) - 0.4)
    ax.set_ylim(-0.7, len(tools) - 0.3)
    ax.grid(axis="x", alpha=0.2, zorder=0)

    handles = [Line2D([], [], marker="o", ls="", markersize=11, markerfacecolor="white",
                      markeredgecolor=C_THR, markeredgewidth=2.0,
                      label="all-tool consensus")]
    if cdr_spans:
        handles.append(Patch(facecolor=C_CDR, alpha=0.25, label="CDR (protected)"))
    ax.legend(handles=handles, fontsize=9, loc="upper right")
    fig.tight_layout()
    return _save(fig, outpath)


# ── 3) nativeness panel: 전체 / FR / CDR 분해 ─────────────────────────
def nativeness_panel(rows, title, outpath, ylabel="AbNatiV score"):
    """서열별 nativeness를 overall · FR · CDR 로 분해해 그룹 바로 비교.

    rows 컬럼: label, overall, fr, cdr   (없는 값은 건너뜀)
    """
    recs = _records(rows)
    labels = [str(_get(r, "label", "seq", "name", default="?")) for r in recs]
    keys = [("overall", ("overall", "score", "abnativ")),
            ("FR", ("fr", "framework", "fr_score")),
            ("CDR", ("cdr", "cdr_h3", "cdr_score"))]

    series = []
    for disp, names in keys:
        vals = [_get(r, *names) for r in recs]
        if any(v is not None for v in vals):
            series.append((disp, [float(v) if v is not None else float("nan") for v in vals]))

    n, m = len(labels), len(series)
    w = 0.8 / max(m, 1)
    colors = {"overall": C_ABNATIV, "FR": C_ANTHROAB, "CDR": C_CDR}

    fig, ax = plt.subplots(figsize=(2.4 * max(n, 2) + 2, 5.2))
    for j, (disp, vals) in enumerate(series):
        xs = [i - 0.4 + w * (j + 0.5) for i in range(n)]
        ax.bar(xs, vals, width=w, color=colors.get(disp, _CYCLE[j]), edgecolor="white",
               label=disp, zorder=3)
        for x, v in zip(xs, vals):
            if v == v:
                ax.annotate(f"{v:.3f}", (x, v), ha="center", va="bottom", fontsize=8)

    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.set_xticks(range(n)); ax.set_xticklabels(labels, fontsize=10)
    ax.set_ylabel(ylabel, fontsize=10); ax.set_ylim(0, 1.05)
    ax.grid(axis="y", alpha=0.25, zorder=0)
    ax.legend(fontsize=9, loc="lower right")
    fig.tight_layout()
    return _save(fig, outpath)


# ── 4) developability: liability 모티프 개수 ──────────────────────────
def liability_overview(rows, title, outpath, ylabel="Motif count"):
    """후보별 liability 모티프 개수를 누적 바로 비교(모티프 종류별 색).

    rows 컬럼: candidate, motif, count
    """
    recs = _records(rows)
    cands = list(dict.fromkeys(str(_get(r, "candidate", "label", "name")) for r in recs))
    motifs = list(dict.fromkeys(str(_get(r, "motif", "liability", "type")) for r in recs))

    table = {c: {m: 0.0 for m in motifs} for c in cands}
    for r in recs:
        c = str(_get(r, "candidate", "label", "name"))
        m = str(_get(r, "motif", "liability", "type"))
        table[c][m] += float(_get(r, "count", "n", default=0) or 0)

    fig, ax = plt.subplots(figsize=(2.0 * max(len(cands), 2) + 3, 5))
    bottom = [0.0] * len(cands)
    for j, m in enumerate(motifs):
        vals = [table[c][m] for c in cands]
        ax.bar(cands, vals, bottom=bottom, color=_CYCLE[j % len(_CYCLE)],
               edgecolor="white", label=m, zorder=3)
        bottom = [b + v for b, v in zip(bottom, vals)]

    for i, tot in enumerate(bottom):
        ax.annotate(f"{tot:.0f}", (i, tot), ha="center", va="bottom",
                    fontsize=9, fontweight="bold")

    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.set_ylabel(ylabel, fontsize=10)
    ax.grid(axis="y", alpha=0.25, zorder=0)
    ax.legend(fontsize=9, title="motif", title_fontsize=9)
    fig.tight_layout()
    return _save(fig, outpath)
