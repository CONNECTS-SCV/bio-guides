"""
boltzgen_viz.py — BoltzGen 결과 시각화 모듈 (기존 튜토리얼 그래프 스타일 매칭)

스타일 규약:
  - 2x2 메트릭 개요: pTM(보라) / ipTM(주황) / RMSD(청록) 바 + 길이-수소결합 산점도(rank 색)
  - 임계선: 빨간 점선 + 범례
  - 굵은 suptitle / 굵은 서브플롯 타이틀

사용:
  from boltzgen_viz import metrics_overview, load_metrics
  df = load_metrics("path/to/final_designs_metrics_10.csv")
  metrics_overview(df, "Vanilla Protein Design Metrics Overview", "figures/05_vanilla.png")
"""
import csv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

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


# 색상 (기존 그래프에서 추출)
C_PTM   = "#8e44ad"   # 보라 (구조 신뢰도)
C_IPTM  = "#e8883a"   # 주황 (인터페이스 신뢰도)
C_RMSD  = "#1aa090"   # 청록 (구조 편차)
C_THR   = "#e74c3c"   # 임계선 빨강
C_AFF   = "#3477b5"   # 파랑 (친화도 등 보조)

# 메트릭 컬럼 표준 이름
COL = dict(rank="final_rank", ptm="design_ptm", iptm="design_to_target_iptm",
           rmsd="filter_rmsd", hb="plip_hbonds_refolded", sasa="delta_sasa_refolded",
           length="num_design", aff="affinity_pred_value")


def load_metrics(path):
    """final_designs_metrics_*.csv → rank 정렬된 dict 리스트."""
    rows = list(csv.DictReader(open(path)))
    def fnum(x):
        try: return float(x)
        except: return float("nan")
    for r in rows:
        for k in ("final_rank", COL["ptm"], COL["iptm"], COL["rmsd"], COL["hb"],
                  COL["sasa"], COL["length"], COL["aff"]):
            if k in r:
                r[k] = fnum(r[k])
    rows.sort(key=lambda r: r.get("final_rank", 1e9))
    return rows


def _bar(ax, ranks, vals, color, title, ylabel, thr=None, thr_label=None,
         lower_better=False, ylim=None):
    ax.bar(ranks, vals, color=color, edgecolor="white", width=0.7, zorder=3)
    ax.set_title(title, fontsize=12, fontweight="bold")
    ax.set_xlabel("Design Rank", fontsize=10)
    ax.set_ylabel(ylabel, fontsize=10)
    ax.set_xticks(ranks)
    ax.grid(axis="y", alpha=0.25, zorder=0)
    if ylim: ax.set_ylim(*ylim)
    if thr is not None:
        ax.axhline(thr, ls="--", color=C_THR, lw=1.6, zorder=4,
                   label=thr_label or f"threshold ({thr})")
        ax.legend(fontsize=8, loc="best")


def metrics_overview(rows, title, outpath, length_label="Designed length (aa)",
                     panel4="scatter"):
    """2x2 메트릭 개요 그림 생성 → outpath 저장.
    panel4: "scatter"(길이 vs H-bond, rank 색) | "hbonds"(H-bond 바, 길이 고정 타깃용)
            | "affinity"(예측 친화도 바, 소분자 프로토콜용)."""
    ranks = [int(r["final_rank"]) for r in rows]
    ptm  = [r.get(COL["ptm"], float("nan"))  for r in rows]
    iptm = [r.get(COL["iptm"], float("nan")) for r in rows]
    rmsd = [r.get(COL["rmsd"], float("nan")) for r in rows]
    hb   = [r.get(COL["hb"], float("nan"))   for r in rows]
    length = [r.get(COL["length"], float("nan")) for r in rows]
    aff  = [r.get(COL["aff"], float("nan"))  for r in rows]

    fig, ax = plt.subplots(2, 2, figsize=(11, 8))
    fig.suptitle(title, fontsize=15, fontweight="bold", y=0.98)

    _bar(ax[0,0], ranks, ptm, C_PTM, "pTM (Structure Confidence)", "pTM Score",
         thr=0.7, thr_label="Good threshold (0.7)", ylim=(0, 1.0))
    _bar(ax[0,1], ranks, iptm, C_IPTM, "ipTM (Interface Confidence)", "ipTM Score",
         thr=0.5, thr_label="Good threshold (0.5)", ylim=(0, 1.0))
    _bar(ax[1,0], ranks, rmsd, C_RMSD, "RMSD (Structure Deviation)", "RMSD (Angstrom)",
         thr=2.0, thr_label="Excellent (<2A)")

    if panel4 == "hbonds":
        _bar(ax[1,1], ranks, hb, "#c0508a", "H-bonds (Interface)", "H-bond Count")
    elif panel4 == "affinity":
        _bar(ax[1,1], ranks, aff, C_AFF, "Predicted Affinity (higher = stronger)",
             "affinity_pred_value")
    else:
        sc = ax[1,1].scatter(length, hb, c=ranks, cmap="viridis_r", s=180,
                             edgecolor="black", linewidth=0.8, zorder=3)
        for x, y, rk in zip(length, hb, ranks):
            ax[1,1].annotate(str(rk), (x, y), ha="center", va="center",
                             fontsize=7, fontweight="bold", color="white")
        ax[1,1].set_title("Length vs H-bonds (colored by rank)", fontsize=12, fontweight="bold")
        ax[1,1].set_xlabel(length_label, fontsize=10)
        ax[1,1].set_ylabel("H-bond Count", fontsize=10)
        ax[1,1].grid(alpha=0.25, zorder=0)
        cb = fig.colorbar(sc, ax=ax[1,1]); cb.set_label("Rank", fontsize=9)

    fig.tight_layout(rect=[0, 0, 1, 0.96])
    fig.savefig(outpath, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return outpath


def compare_bars(groups, metric_key, title, ylabel, outpath, thr=None, thr_label=None):
    """여러 실험(라벨→rows) 평균 비교 바 차트."""
    labels, means = [], []
    for label, rows in groups.items():
        vals = [r.get(metric_key, float("nan")) for r in rows]
        vals = [v for v in vals if v == v]
        labels.append(label); means.append(sum(vals)/len(vals) if vals else 0)
    fig, ax = plt.subplots(figsize=(8, 5))
    colors = [C_PTM, C_IPTM, C_RMSD, C_AFF, "#c0508a", "#7f8c8d"][:len(labels)]
    ax.bar(labels, means, color=colors, edgecolor="white", zorder=3)
    ax.set_title(title, fontsize=13, fontweight="bold")
    ax.set_ylabel(ylabel, fontsize=10); ax.grid(axis="y", alpha=0.25, zorder=0)
    if thr is not None:
        ax.axhline(thr, ls="--", color=C_THR, lw=1.6, label=thr_label or f"threshold ({thr})")
        ax.legend(fontsize=8)
    for i, v in enumerate(means):
        ax.annotate(f"{v:.3f}" if v < 10 else f"{v:.0f}", (i, v),
                    ha="center", va="bottom", fontsize=9)
    fig.tight_layout(); fig.savefig(outpath, dpi=150, bbox_inches="tight"); plt.close(fig)
    return outpath


if __name__ == "__main__":
    import sys
    rows = load_metrics(sys.argv[1])
    metrics_overview(rows, sys.argv[2], sys.argv[3])
    print("saved:", sys.argv[3], "| designs:", len(rows))
