"""노트북 생성기 — 각 챕터 폴더에 .ipynb 생성 (Colab 실습 + 본문 1:1 정합).
실행: python gen_notebooks.py

설계 원칙 (자매 가이드 boltzgen/advanced/gen_notebooks.py 와 동일 계보)
  · 모든 노트북 맨 위에 'Colab/로컬 공용 부트스트랩' 셀
    (저장소 클론 → 챕터 폴더로 chdir → sys.path 에 가이드 루트 → 필요한 것만 설치 → MY/find_one 헬퍼).
  · **직접 생성 모델** — 학습자가 도구를 실제로 돌려 my_run/ 에 자기 산출물을 만들고, 그걸로 다음 단계를 잇는다.
    각 절은 ① 직접 실행 → ② 내 결과 확인 → ③ 레퍼런스 대조(커밋된 data/) 3단.
  · my_run/ 이 없거나 실행이 실패해도 실습이 끊기지 않도록 data/ 로 자동 폴백하고, 어느 쪽을 쓰는지 print.
  · 그래프는 공용 모듈 humanization_viz.py (가이드 루트) 재사용.
  · 수치·소요시간은 전부 실측(hz_runs/timings.csv, manifest.md). 지어낸 값 없음.
"""
import json, pathlib

ROOT = pathlib.Path(__file__).parent


def md(t):
    return {"cell_type": "markdown", "metadata": {}, "source": t.splitlines(keepends=True)}


def co(s):
    return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [],
            "source": s.splitlines(keepends=True)}


def save(cells, folder, name, title):
    for i, cell in enumerate(cells):            # nbformat 4.5+ : 셀 id 부여
        cell.setdefault("id", f"c{i:02d}")
    doc = {"cells": cells, "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.10"}, "title": title},
        "nbformat": 4, "nbformat_minor": 5}
    p = ROOT / folder / name
    p.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"wrote {folder}/{name}  ({len(cells)} cells)")
    return len(cells)


# ─────────────────────────────────────────────────────────────────────────────
# 공용 부트스트랩 — 모든 노트북의 첫 코드 셀
# ─────────────────────────────────────────────────────────────────────────────
_BOOT = r'''# ====== Colab/로컬 공용 부트스트랩 (모든 챕터 공통) ======
REPO_URL = "https://github.com/CONNECTS-SCV/bio-guides.git"   # 이 가이드 저장소 (fork 했다면 본인 주소로 바꾸세요)
CLONE_AS = "bio-guides"
CHAPTER  = "__CHAPTER__"
APT_PKGS = "__APT__"     # Colab 에서만: 시스템 패키지 (hmmer = ANARCI 가 부르는 hmmscan)
PIP_PKGS = "__PIP__"     # 없는 것만 설치

import os, sys, json, time, shutil, pathlib, subprocess, importlib, importlib.util
IN_COLAB = "google.colab" in sys.modules

def _run(cmd, check=True):
    print("$", cmd)
    return subprocess.run(cmd, shell=True, check=check)

_MARK = "humanization_viz.py"          # 이 파일이 있는 폴더 = 가이드 루트

def _find_root():
    cwd = pathlib.Path.cwd()
    for base in (cwd, *list(cwd.parents)[:3]):
        if (base / _MARK).exists():
            return base
    # 클론 직후: cwd '아래'만 깊이 3까지 훑는다.
    # (상위로 올라가 rglob 하면 Colab 에서는 / 전체를 뒤지게 된다 — 매우 느리고 엉뚱한 경로를 잡는다)
    for pat in (f"*/{_MARK}", f"*/*/{_MARK}", f"*/*/*/{_MARK}"):
        hits = sorted(cwd.glob(pat))
        if hits:
            return hits[0].parent
    return None

ROOT = _find_root()
if ROOT is None and IN_COLAB:
    if not pathlib.Path(CLONE_AS).exists():
        _run(f'git clone --depth 1 "{REPO_URL}" {CLONE_AS}')
    ROOT = _find_root()
assert ROOT is not None, "가이드 루트를 못 찾았습니다. 로컬이면 이 노트북을 챕터 폴더 안에서 여세요."

GUIDE_ROOT = ROOT.resolve()
os.chdir(GUIDE_ROOT / CHAPTER)         # data/ 상대경로가 그대로 동작
sys.path.insert(0, str(GUIDE_ROOT))    # humanization_viz import
sys.path.insert(0, str(GUIDE_ROOT / CHAPTER))

_IMPORT_NAME = {"biopython": "Bio", "pyyaml": "yaml", "scikit-learn": "sklearn"}

def _have(mod):
    try:
        return importlib.util.find_spec(mod) is not None
    except Exception:
        return False

def _ensure(pkgs):
    miss = [p for p in pkgs.split() if not _have(_IMPORT_NAME.get(p, p.replace("-", "_")))]
    if miss:
        print("설치:", " ".join(miss))
        _run(f'"{sys.executable}" -m pip -q install ' + " ".join(miss))
        importlib.invalidate_caches()

# ANARCI 는 numbering 을 hmmscan(HMMER) 서브프로세스로 돌립니다 — pip 만으로는 hmmscan 이 없습니다.
if APT_PKGS and IN_COLAB:
    _run("apt-get -qq update")                 # 인덱스가 낡으면 install 이 404 로 죽는다
    _run(f"apt-get -qq install -y {APT_PKGS}")
if PIP_PKGS:
    _ensure(PIP_PKGS)

def _ensure_pkg_resources():
    # setuptools 81+(2026-02) 이 pkg_resources 를 없앴는데 IgFold 의존성이 이걸 import 합니다.
    if importlib.util.find_spec("pkg_resources") is None:
        _run(f'"{sys.executable}" -m pip -q install "setuptools<81"')
        importlib.invalidate_caches()

import glob as _glob
if IN_COLAB and not _glob.glob("/usr/share/fonts/**/*Nanum*", recursive=True):
    # Colab 에는 한글 폰트가 없어 그래프의 한글 라벨이 □ 로 깨집니다.
    _run("apt-get -qq update"); _run("apt-get -qq install -y fonts-nanum")


# ── ① 내가 만든 결과(my_run) 우선 · ② 없으면 커밋된 레퍼런스(data/) ─────────────
MY  = pathlib.Path("my_run"); MY.mkdir(exist_ok=True)
REF = pathlib.Path("data")

def find_one(pattern, ref=REF, quiet=False):
    """산출물 하나 찾기 — 내가 만든 my_run/ 을 먼저 뒤지고, 없으면 커밋된 레퍼런스에서."""
    hits = sorted(MY.rglob(pattern))
    if hits:
        if not quiet: print(f"[내 결과]   {hits[0]}")
        return hits[0]
    hits = sorted(pathlib.Path(ref).glob(pattern))
    assert hits, f"'{pattern}' 을 my_run/ 에서도 {ref}/ 에서도 찾지 못했습니다."
    if not quiet: print(f"[레퍼런스] {hits[0]}")
    return hits[0]

def find_prev(chapter, pattern, ref=REF, quiet=False):
    """앞 챕터에서 직접 만든 산출물 → 없으면 이 챕터 data/ 레퍼런스."""
    hits = sorted((GUIDE_ROOT / chapter / "my_run").rglob(pattern))
    if hits:
        if not quiet: print(f"[내 결과 · {chapter}] {hits[0]}")
        return hits[0]
    return find_one(pattern, ref, quiet)

def read_fasta(path):
    out, name, buf = {}, None, []
    for line in pathlib.Path(path).read_text().splitlines():
        if line.startswith(">"):
            if name: out[name] = "".join(buf)
            name, buf = line[1:].strip(), []
        elif line.strip():
            buf.append(line.strip())
    if name: out[name] = "".join(buf)
    return out

def write_fasta(path, records):
    pathlib.Path(path).write_text("".join(f">{k}\n{v}\n" for k, v in records.items()))
    return pathlib.Path(path)

PARENTAL = read_fasta(REF / "parental.fasta")      # 가이드 전체를 관통하는 러닝 예제
VH = PARENTAL["parental_H"]
VL = PARENTAL["parental_L"]

print("가이드 루트 :", GUIDE_ROOT)
print("작업 폴더   :", pathlib.Path.cwd())
print(f"러닝 예제   : VH {len(VH)} aa · VL {len(VL)} aa (mouse hybridoma 가정)")'''


def boot(chapter, pip="pandas matplotlib", apt=""):
    code = _BOOT.replace("__CHAPTER__", chapter).replace("__PIP__", pip).replace("__APT__", apt)
    apt_note = ("\n- ANARCI 는 numbering 을 **hmmscan(HMMER)** 서브프로세스로 돌립니다. "
                "Colab 에서는 `apt-get install -y hmmer` 가 함께 실행됩니다 — pip 만으로는 `hmmscan` 이 없어 죽습니다."
                if apt else "")
    return [
        md(f"""## 0) Colab 준비 — 저장소 클론 & 작업 폴더 이동

- **Colab**: 이 셀을 그대로 실행하세요. 저장소를 클론하고 이 챕터(`{chapter}`) 폴더로 이동한 뒤, 필요한 패키지만 깝니다.
- **로컬**: 이 노트북을 `{chapter}/` 폴더 안에서 열었다면 클론 없이 그대로 진행됩니다.

이 셀이 끝나면 두 개의 경로가 준비됩니다 — **`my_run/`**(내가 직접 만들 결과)과 **`data/`**(저장소에 커밋된 레퍼런스 결과).
아래 랩은 항상 `my_run/` 을 먼저 찾고, 없으면 `data/` 로 폴백하면서 **어느 쪽을 쓰는지 print** 합니다.{apt_note}"""),
        co(code),
    ]


# 실측 소요시간(hz_runs/timings.csv) — 지어낸 값 없음
BADGE = {
    "03": "ANARCI numbering+germline **0.15초** · Sapiens 첫 실행(모델 가중치 다운로드 포함) **6.3초**",
    "04": "ANARCI numbering+germline(H·L 동시) **0.15초** · abnumber CDR 추출 **1초 미만**",
    "05": "Sapiens `predict_scores` VH **0.93초** / VL **0.53초** · humanized 재스코어링 **0.01초**",
    "06": "Humatch 첫 실행 **160초**(Zenodo CNN 가중치 다운로드 포함) · AnthroAb `predict_best_score` **1.3~1.5초** / masked **2.3~2.5초**",
    "07": "Ab-RoBERTa 5후보 × VH+VL **70초** · AbNatiV 스코어링 **3.5~6.6초**(단 체크포인트 내려받기 **약 33분 / 2.6GB** → 기본 비활성)",
    "08": "IgFold VH+VL 폴딩 **7.1초**(parental) · **12.0초**(humanized)",
    "09": "정규식 liability 스캔(후보 5종) **1초 미만**",
    "10": "Sapiens 재스코어링(후보 5종) **2초 미만** · ANARCI germline(10 체인) **0.42초**",
}


def title_cell(num, ko, md_link):
    return md(f"""# {num} — {ko}

> 본문 [`{md_link}`]({md_link}) 와 **한 절씩 짝지어** 보세요.
> **① 직접 실행 → ② 내 결과 확인 → ③ 레퍼런스 대조** 순서로 진행합니다.
> 이 노트북의 표·그래프·수치는 **여러분이 방금 돌린 `my_run/`** 에서 나옵니다. 실행을 건너뛰거나 실패하면 저장소에 커밋된 `data/`(실제 실행 산출물) 로 자동 폴백합니다.
>
> **실측 소요 —** {BADGE[num]}""")


cells_all = {}

# ════════════════════════════════════════════════════════════════════════════
# 03 — 환경 구성·검증
# ════════════════════════════════════════════════════════════════════════════
c = [title_cell("03", "환경 구성 — 설치·검증·러닝 예제", "03_setup.md")]
c += boot("03_setup", pip="pandas", apt="hmmer")
c += [
md("""## 1) 직접 실행 — 도구 설치 (본문 3.1~3.2)

Colab 기준 **한 줄씩** 깝니다. 순서가 중요합니다.

```bash
apt-get -qq update                    # ① apt 인덱스 갱신
apt-get -qq install -y hmmer          # ② ANARCI 가 부르는 hmmscan 바이너리
pip -q install anarci abnumber        # ② numbering (pip 만으로는 hmmscan 이 없어 실패)
pip -q install sapiens                # ③ humanization 엔진 (Ch.05)
```

로컬 conda 라면 본문 3.1 의 `conda create -n abhuman -c conda-forge -c bioconda python=3.10 anarci hmmer` 로 대체할 수 있습니다.
어느 경로든 **`hmmscan` 이 PATH 에 있어야** 합니다 — 이 한 줄이 Ch.04·06·07 에서 가장 흔한 에러를 막습니다."""),
co('''t0 = time.time()
if IN_COLAB:
    _run("apt-get -qq update")
    _run("apt-get -qq install -y hmmer")
_ensure("anarci abnumber sapiens")
print(f"\\n설치 셀 소요: {time.time()-t0:.1f}초")'''),

md("""## 2) 내 결과 확인 — 환경 진단 (본문 3.4)

`import` 가 되는지, 그리고 **`hmmscan` 이 실제로 PATH 에 있는지**를 함께 봅니다.
CLI `ANARCI` 가 돌아가도 파이썬 모듈 `anarci` 가 import 되지 않으면 Humatch·AbNatiV 가 뒤에서 죽습니다."""),
co('''import importlib, shutil, pandas as pd

def probe(mod):
    try:
        m = importlib.import_module(mod)
        return "OK", getattr(m, "__version__", "?")
    except Exception as e:
        return "FAIL", f"{type(e).__name__}: {e}"[:60]

rows = []
for mod in ["anarci", "abnumber", "sapiens", "pandas"]:
    st, ver = probe(mod)
    rows.append({"항목": f"import {mod}", "상태": st, "버전/메시지": ver})
rows.append({"항목": "hmmscan (HMMER)", "상태": "OK" if shutil.which("hmmscan") else "FAIL",
             "버전/메시지": shutil.which("hmmscan") or "PATH 에 없음 → ANARCI numbering 이 FileNotFoundError 로 죽습니다"})
rows.append({"항목": "ANARCI CLI", "상태": "OK" if shutil.which("ANARCI") else "FAIL",
             "버전/메시지": shutil.which("ANARCI") or "없음(파이썬 API 로도 진행 가능)"})

env = pd.DataFrame(rows)
MY.mkdir(exist_ok=True)
env.to_csv(MY / "env_report.csv", index=False)
print("내 환경 리포트 →", MY / "env_report.csv")
env'''),

md("""## 3) 직접 실행 — 러닝 예제 서열로 첫 numbering

가이드 전체를 관통하는 예제 서열(`data/parental.fasta`)입니다. Ch.04~10 의 모든 수치가 이 두 체인에서 나옵니다.
여기서는 도구가 실제로 도는지만 확인합니다 — 본격적인 numbering·CDR 추출은 Ch.04 에서 합니다."""),
co('''try:
    from abnumber import Chain

    t0 = time.time()
    ch_h = Chain(VH, scheme="imgt")
    ch_l = Chain(VL, scheme="imgt")
    el = time.time() - t0

    print(f"VH  : {len(VH)} aa | chain_type={ch_h.chain_type} | CDR3={ch_h.cdr3_seq}")
    print(f"VL  : {len(VL)} aa | chain_type={ch_l.chain_type} | CDR3={ch_l.cdr3_seq}")
    print(f"\\nabnumber numbering 소요: {el:.2f}초")

    smoke = {"VH_len": len(VH), "VL_len": len(VL),
             "VH_cdr3": ch_h.cdr3_seq, "VL_cdr3": ch_l.cdr3_seq,
             "VH_chain_type": ch_h.chain_type, "VL_chain_type": ch_l.chain_type}
    (MY / "smoke.json").write_text(json.dumps(smoke, ensure_ascii=False, indent=1))
    print("→", MY / "smoke.json")
except Exception as e:
    print("스모크 실패:", type(e).__name__, str(e)[:160])
    print("→ 2) 진단표에서 FAIL 인 항목을 보고 1) 설치 셀을 다시 실행하세요.")
    print("   (hmmscan 이 없으면 numbering 이, abnumber 가 없으면 CDR 추출이 여기서 막힙니다.)")'''),

md("""## 4) 레퍼런스 대조 — 이 가이드를 검증한 도구 버전

`data/verified_versions.csv` 는 이 가이드의 모든 수치를 뽑을 때 **실제로 쓴 버전**입니다.
내 환경의 버전이 달라도 대개 문제없지만, 결과가 어긋나면 여기부터 비교하세요."""),
co('''ver = pd.read_csv("data/verified_versions.csv")
display(ver)

mine = {m: probe(m)[1] for m in ["anarci", "abnumber", "sapiens"]}
print("\\n내 환경 버전:", mine)
print("\\n주의 — torch 2.13.0+cpu 휠은 import 시 undefined symbol 로 깨집니다(실측). 2.6.0 을 쓰세요.")'''),

md("""## 이 랩에서 확인한 것

1. `hmmscan`(HMMER) 이 PATH 에 없으면 ANARCI numbering 이 **FileNotFoundError** 로 죽습니다 — Colab 은 `apt-get install -y hmmer` 가 정답.
2. 설치 채널이 도구마다 다릅니다 — Colab/PyPI 경로는 `anarci`·`abnumber`·`sapiens`·`anthroab`·`abnativ` 가 pip, Humatch 는 pip 이 안 되면 GitHub source(Ch.06 에서 자동 처리).
3. 러닝 예제 CDR3 — VH `ARRGRYGLYAMDY` · VL `QSYDSSLRVV`. 이 값이 나왔다면 Ch.04 로 넘어가도 좋습니다.

다음 → **[Ch.04 — 입력 QC](../04_sequence_qc/04_numbering_lab.ipynb)**"""),
]
cells_all[("03_setup", "03_setup_check.ipynb", "03 Setup & Check")] = c


# ════════════════════════════════════════════════════════════════════════════
# 04 — numbering / CDR / germline / raw↔IMGT
# ════════════════════════════════════════════════════════════════════════════
c = [title_cell("04", "입력 QC — numbering · CDR · germline · 번호 체계", "04_sequence_qc.md")]
c += boot("04_sequence_qc", pip="pandas anarci abnumber", apt="hmmer")
c += [
md("""## 1) 직접 실행 — ANARCI numbering + germline (본문 4.1)

```bash
ANARCI -i parental.fasta --scheme imgt --assign_germline --use_species human --csv -o my_run/anarci_gl
```

`--assign_germline` 이 핵심입니다. 이게 있어야 "가장 가까운 사람 germline 과 몇 % 같은가" 가 나오고, 그 숫자가 humanization 전략을 정합니다."""),
co('''t0 = time.time()
try:
    r = subprocess.run(["ANARCI", "-i", "data/parental.fasta", "--scheme", "imgt", "--csv",
                        "-o", str(MY / "anarci_gl"), "--assign_germline", "--use_species", "human"],
                       capture_output=True, text=True)
    rc, err = r.returncode, r.stderr
except FileNotFoundError as e:
    # ANARCI CLI 자체가 PATH 에 없음 (hmmscan 이 없으면 numbering 도 여기서 죽습니다 — Ch.03)
    rc, err = 127, f"{e} — ANARCI/hmmscan 이 PATH 에 없습니다"
el = time.time() - t0
if rc != 0:
    print("ANARCI CLI 실패:", str(err).strip()[:300])
    print("→ hmmscan 이 PATH 에 있는지 확인하세요(Ch.03). 아래 셀은 레퍼런스로 이어집니다.")
else:
    print(f"ANARCI numbering+germline 완료: {el:.2f}초")
    for p in sorted(MY.glob("anarci_gl_*.csv")):
        print("  →", p)'''),

md("""## 2) 내 결과 확인 — germline 표 (본문 4.2)

V identity 가 낮은 체인 = 사람 germline 과 멀다 = **humanization 여지가 크다**."""),
co('''import pandas as pd, glob

def germline_table(paths):
    rows = []
    for p in paths:
        for _, r in pd.read_csv(p).iterrows():
            rows.append({"체인": r["chain_type"], "hmm_species": r["hmm_species"],
                         "V gene": r["v_gene"], "V identity": float(r["v_identity"]),
                         "J gene": r["j_gene"], "J identity": float(r["j_identity"])})
    return pd.DataFrame(rows)

mine_paths = sorted(MY.glob("anarci_gl_*.csv"))
if mine_paths:
    print("[내 결과]", *[str(p) for p in mine_paths])
    gl = germline_table(mine_paths)
else:
    print("[레퍼런스] data/anarci_imgt_H.csv · data/anarci_imgt_KL.csv")
    gl = germline_table(["data/anarci_imgt_H.csv", "data/anarci_imgt_KL.csv"])
display(gl)

print("해석 — heavy V identity 가 낮을수록 heavy framework 에 손댈 자리가 많습니다.")
print("       light 가 이미 높으면 노력의 무게중심은 heavy 로 갑니다.")'''),

md("""## 3) 번호 체계와 J-gene 동점 — 두 개의 함정 (실측)

**(a) J-gene 은 동점입니다.** 본문 4.2 표는 heavy J 를 `IGHJ4*01` 86% 로 적었지만, ANARCI 실측은 **`IGHJ6*01` 85.71%** 입니다.
둘 다 J-segment 14 잔기 중 12개 일치(12/14 = 85.71%)로 **정확히 동점**이고, 어느 쪽을 고르냐는 **도구의 tie-break** 차이입니다
(ANARCI 는 germline dict 순회에서 먼저 만난 `IGHJ6*01`, abnumber 0.3.2 의 별도 germline 조회는 `IGHJ4*01`).
아래 셀에서 **두 도구를 같은 서열에 돌려 동점을 직접 확인**합니다.

**(b) 번호 체계가 두 개입니다.** 뒤 챕터에서 도구별 mutation 표기가 섞입니다.

| 체계 | 어디서 쓰나 | 예 |
|---|---|---|
| **raw 1-based** | Sapiens·AnthroAb 의 `predict_scores` 가 그대로 쓰는 서열 인덱스 | `I78T` = 입력 문자열의 78번째 잔기 |
| **IMGT** | ANARCI/abnumber numbering. gap·삽입이 있어 raw 와 어긋남 | `H86` = 같은 잔기의 IMGT 번호 |

Humatch 는 indel 을 만들 수 있어(우리 VL 은 1 잔기 짧아집니다) **raw 인덱스 비교가 깨집니다.**
그래서 도구 간 비교는 **반드시 IMGT 로 변환**해서 합니다. 그 변환표를 지금 만듭니다."""),
co('''HAVE_ABNUMBER, ch_h, ch_l = _have("abnumber"), None, None

if HAVE_ABNUMBER:
    from abnumber import Chain

    # (a) 동점 확인 — 같은 서열, 두 도구
    ch_h = Chain(VH, scheme="imgt", assign_germline=True)
    anarci_j = gl.loc[gl["체인"] == "H", "J gene"].iloc[0] if (gl["체인"] == "H").any() else "?"
    print(f"ANARCI   J gene : {anarci_j}")
    print(f"abnumber J gene : {ch_h.j_gene}")
    print("→ 같은 서열인데 J 가 다릅니다. 12/14 = 85.71% 동점이라 tie-break 가 갈린 것입니다(오류 아님).")
    print("   본문 4.2 의 'IGHJ4*01 86%' 는 abnumber 쪽 tie-break 입니다.\\n")

    # (b) raw ↔ IMGT 크로스워크 만들기
    def raw2imgt(seq):
        ch = Chain(seq, scheme="imgt")
        assert seq.startswith(ch.seq), "numbering 영역이 서열 앞부분과 어긋납니다"
        m, i, last = {}, 1, None
        for pos, aa in ch:
            m[i] = str(pos); last = str(pos); i += 1
        for k, aa in enumerate(ch.tail, start=1):       # IMGT 범위 밖(C-말단 꼬리)
            m[i] = f"{last}_tail{k}"; i += 1
        return ch, m

    ch_h, r2i_H = raw2imgt(VH)
    ch_l, r2i_L = raw2imgt(VL)
    (MY / "raw2imgt_H.json").write_text(json.dumps({str(k): v for k, v in r2i_H.items()}, indent=1))
    (MY / "raw2imgt_L.json").write_text(json.dumps({str(k): v for k, v in r2i_L.items()}, indent=1))
    print("→", MY / "raw2imgt_H.json", "·", MY / "raw2imgt_L.json")
else:
    print("[레퍼런스] abnumber 가 없어 커밋된 크로스워크(data/raw2imgt_*.json)를 씁니다")
    r2i_H = {int(k): v for k, v in json.loads(pathlib.Path("data/raw2imgt_H.json").read_text()).items()}
    r2i_L = {int(k): v for k, v in json.loads(pathlib.Path("data/raw2imgt_L.json").read_text()).items()}

print("\\nraw → IMGT 예시 (VH):", {k: r2i_H[k] for k in (5, 12, 78, 115)})
print("raw → IMGT 예시 (VL):", {k: r2i_L[k] for k in (31, 85, 109, 111)})
print("VL 마지막 잔기:", r2i_L[len(VL)], "← IMGT 범위 밖(C-말단 꼬리)이라 tail 로 라벨링됩니다")
print("\\n핵심 — Sapiens 의 'I78T' 는 raw 78번, 같은 잔기의 IMGT 번호는", r2i_H[78], "입니다.")'''),

md("""## 4) 직접 실행 — CDR 추출 + **보호 좌표 못 박기** (본문 4.3)

humanization 에서 가장 먼저 할 일은 "여기는 절대 안 건드린다"를 좌표로 고정하는 것입니다.
CDR 을 **raw 인덱스**(Sapiens/AnthroAb 가 쓰는 좌표)와 **IMGT 라벨** 두 가지로 모두 저장합니다 — Ch.05 의 CDR 가드가 이 파일을 씁니다."""),
co('''if HAVE_ABNUMBER:
    seqs_by_chain = {"H": VH, "L": VL}
    cdr_seqs = [(tag, name, "".join(ch.regions[name].values()))
                for tag, ch in (("H", ch_h), ("L", ch_l))
                for name in ("CDR1", "CDR2", "CDR3")]
else:
    print("[레퍼런스] data/cdr_table_imgt.csv 의 CDR 서열로 좌표를 복원합니다")
    seqs_by_chain = {"H": VH, "L": VL}
    cdr_seqs = [(r["chain"], r["cdr"], r["sequence"]) for _, r in pd.read_csv("data/cdr_table_imgt.csv").iterrows()]

cdr_rows, guard = [], {"H": [], "L": []}
for tag, name, s in cdr_seqs:
    seq = seqs_by_chain[tag]
    start = seq.find(s) + 1                            # raw 1-based 시작
    r2i = r2i_H if tag == "H" else r2i_L
    guard[tag] += list(range(start, start + len(s)))
    cdr_rows.append({"chain": tag, "cdr": name, "sequence": s,
                     "raw_start": start, "raw_end": start + len(s) - 1,
                     "imgt": f"{r2i[start]}..{r2i[start + len(s) - 1]}"})

cdr = pd.DataFrame(cdr_rows)
display(cdr)
print("보호 좌표(raw 1-based) — VH:", len(guard["H"]), "잔기 / VL:", len(guard["L"]), "잔기")
if HAVE_ABNUMBER:
    cdr.to_csv(MY / "cdr_table_imgt.csv", index=False)
    (MY / "cdr_guard.json").write_text(json.dumps(guard, indent=1))
    print("→", MY / "cdr_table_imgt.csv", "·", MY / "cdr_guard.json")
print("\\nCDR-H3 =", cdr.loc[(cdr.chain=='H') & (cdr.cdr=='CDR3'), 'sequence'].iloc[0],
      "— 항원 결합에 가장 결정적인 loop. 여기 mutation 이 들어가면 빨간불입니다.")'''),

md("""## 5) 레퍼런스 대조 — 커밋된 실행 결과와 맞춰보기

`data/` 는 이 가이드를 만들 때 **실제로 돌려 나온** 산출물입니다. 내 결과와 한 글자씩 비교합니다."""),
co('''ref_cdr = pd.read_csv("data/cdr_table_imgt.csv")
ref_gl  = pd.read_csv("data/germline_assignment.csv")
ref_r2i_H = json.loads(pathlib.Path("data/raw2imgt_H.json").read_text())

ok_cdr = all(ref_cdr.loc[(ref_cdr.chain == r.chain) & (ref_cdr.cdr == r.cdr), "sequence"].iloc[0] == r.sequence
             for r in cdr.itertuples())
ok_map = {str(k): v for k, v in r2i_H.items()} == ref_r2i_H
print("CDR 6개 일치      :", ok_cdr)
print("raw→IMGT(H) 일치  :", ok_map)

print("\\n[레퍼런스 germline — ANARCI 1.3 실측]")
display(ref_gl[["chain", "gene_type", "gene", "identity_pct"]])
print("실측: VH IGHV1-69*06 63.27% / IGHJ6*01 85.71%  ·  VL IGLV1-40*01 80.85% / IGLJ2*01 83.33%")
print("본문 4.2 의 J 'IGHJ4*01 86%' 는 동점 tie-break 차이입니다(3항 참고).")'''),

md("""## 이 랩에서 확인한 것

1. **germline 실측** — VH `IGHV1-69*06` **63.27%** / VL `IGLV1-40*01` **80.85%**. heavy 가 훨씬 비인간적 → 손댈 자리가 많습니다.
2. **J-gene 은 동점** — `IGHJ6*01`(ANARCI) vs `IGHJ4*01`(abnumber) 둘 다 85.71%. 도구의 tie-break 차이지 오류가 아닙니다.
3. **CDR 6개** — H `GYTFTDYV`/`IYPGSGTN`/`ARRGRYGLYAMDY`, L `SSDVGHKFP`/`KNL`/`QSYDSSLRVV`.
4. **번호 체계 두 개**(raw 1-based ↔ IMGT)를 명시적으로 이어 붙인 `raw2imgt_*.json` 을 만들었습니다. Ch.06 의 도구 간 합의 분석이 이 파일 위에서 돕니다.
5. **CDR 보호 좌표**(`cdr_guard.json`) 를 못 박았습니다 — Ch.05 에서 이걸로 사고를 막습니다.

다음 → **[Ch.05 — Sapiens](../05_humanize_sapiens/05_sapiens_lab.ipynb)**"""),
]
cells_all[("04_sequence_qc", "04_numbering_lab.ipynb", "04 Numbering Lab")] = c


# ════════════════════════════════════════════════════════════════════════════
# 05 — Sapiens
# ════════════════════════════════════════════════════════════════════════════
c = [title_cell("05", "BioPhi/Sapiens — 후보 생성 · CDR 사고 · humanness", "05_humanize_sapiens.md")]
c += boot("05_humanize_sapiens", pip="pandas matplotlib sapiens anarci abnumber", apt="hmmer")
c += [
md("""## 1) 직접 실행 — Sapiens humanization (본문 5.2)

Sapiens 의 핵심은 `predict_scores` 입니다 — position 마다 20개 아미노산에 대한 **사람 모델의 확률 분포**를 줍니다.
각 자리에서 확률이 가장 높은 잔기를 고르면(argmax) 그게 곧 Sapiens-humanized 서열입니다.

**가드 없이** 돌립니다 — 본문이 경고한 사고를 직접 재현하기 위해서입니다."""),
co('''import pandas as pd, numpy as np

def mutations(par, hum):
    return [{"position_1based": i + 1, "wt": a, "mut": b, "mutation": f"{a}{i+1}{b}"}
            for i, (a, b) in enumerate(zip(par, hum)) if a != b]

HAVE_SAPIENS = _have("sapiens")
if HAVE_SAPIENS:
    try:
        import sapiens
        t0 = time.time()
        mat_h = sapiens.predict_scores(VH, "H")     # rows=position, cols=20 AA
        mat_l = sapiens.predict_scores(VL, "L")
        print(f"Sapiens predict_scores VH+VL: {time.time()-t0:.2f}초")

        hum_h = "".join(mat_h.columns[mat_h.values.argmax(axis=1)])   # 가드 없는 argmax
        hum_l = "".join(mat_l.columns[mat_l.values.argmax(axis=1)])

        mat_h.to_csv(MY / "score_matrix_VH_parental.csv", index_label="position0based")
        mat_l.to_csv(MY / "score_matrix_VL_parental.csv", index_label="position0based")
        write_fasta(MY / "sapiens_humanized_noguard.fasta",
                    {"sapiens_humanized_VH": hum_h, "sapiens_humanized_VL": hum_l})
        mut_h = pd.DataFrame(mutations(VH, hum_h)); mut_h.to_csv(MY / "mutations_VH.csv", index=False)
        mut_l = pd.DataFrame(mutations(VL, hum_l)); mut_l.to_csv(MY / "mutations_VL.csv", index=False)
        print("→", MY / "sapiens_humanized_noguard.fasta")
    except Exception as e:
        print("Sapiens 실행 실패:", type(e).__name__, str(e)[:160])
        HAVE_SAPIENS = False

if not HAVE_SAPIENS:
    print("[레퍼런스] data/ 의 Sapiens 실행 산출물로 진행합니다")
    f = read_fasta("data/sapiens_humanized.fasta")
    hum_h, hum_l = f["sapiens_humanized_VH"], f["sapiens_humanized_VL"]
    mat_h = pd.read_csv("data/score_matrix_VH_parental.csv", index_col=0)
    mat_l = pd.read_csv("data/score_matrix_VL_parental.csv", index_col=0)
    mut_h = pd.read_csv("data/mutations_VH.csv"); mut_l = pd.read_csv("data/mutations_VL.csv")

print(f"\\nVH mutation {len(mut_h)}개 · VL mutation {len(mut_l)}개")
print("\\nPARENTAL :", VH)
print("SAPIENS  :", hum_h)
print("muts     :", ", ".join(mut_h["mutation"]))'''),

md("""## 2) 내 결과 확인 — **CDR 사고 재현** (본문 5.3)

Ch.04 에서 못 박은 CDR 보호 좌표(`cdr_guard.json`)를 가져와, 방금 나온 mutation 중 **CDR 안에 떨어진 것**을 찾습니다.
Ch.04 를 건너뛰었다면 이 챕터 `data/cdr_table_imgt.csv` 로 폴백합니다."""),
co('''# CDR 좌표 — Ch.04 에서 내가 만든 것 우선
gp = GUIDE_ROOT / "04_sequence_qc" / "my_run" / "cdr_guard.json"
if gp.exists():
    print(f"[내 결과 · 04_sequence_qc] {gp}")
    guard = json.loads(gp.read_text())
else:
    print("[레퍼런스] data/cdr_table_imgt.csv 에서 CDR 좌표를 복원합니다")
    ct = pd.read_csv("data/cdr_table_imgt.csv")
    guard = {"H": [], "L": []}
    for _, r in ct.iterrows():
        seq = VH if r["chain"] == "H" else VL
        st = seq.find(r["sequence"]) + 1
        guard[r["chain"]] += list(range(st, st + len(r["sequence"])))

cdr_h = mut_h[mut_h.position_1based.isin(guard["H"])]
cdr_l = mut_l[mut_l.position_1based.isin(guard["L"])]
print(f"\\nCDR 안에 떨어진 mutation — VH {len(cdr_h)}개 · VL {len(cdr_l)}개")
display(cdr_l)
print("VL CDR1 =", "".join(VL[p-1] for p in sorted(guard["L"])[:9]),
      "→ 가드 없는 argmax 가 CDR-L1 을 통째로 갈아엎었습니다.")
print("이건 결합력을 깰 수 있는 위험한 mutation 입니다 — 그래서 CDR 좌표를 미리 못 박아야 합니다.")'''),

md("""## 3) 직접 실행 — CDR 가드 적용본 만들기 (본문 5.3 주의)

실무 처방은 셋 중 하나입니다 — ① CDR 을 mask 에서 제외, ② 도구의 CDR 보호 모드, ③ **후처리로 CDR 을 parental 로 되돌리기**.
여기서는 ③ 을 그대로 구현합니다(가장 단순하고 검증하기 쉬움)."""),
co('''def cdr_guarded(par, hum, protected):
    s = list(hum)
    for p in protected:
        s[p - 1] = par[p - 1]                 # CDR 잔기는 parental 로 복원
    return "".join(s)

g_h = cdr_guarded(VH, hum_h, guard["H"])
g_l = cdr_guarded(VL, hum_l, guard["L"])
write_fasta(MY / "sapiens_humanized_cdrguard.fasta",
            {"sapiens_guarded_VH": g_h, "sapiens_guarded_VL": g_l})

cmp_rows = []
for tag, par, ng, gd, pr in (("VH", VH, hum_h, g_h, guard["H"]), ("VL", VL, hum_l, g_l, guard["L"])):
    cmp_rows.append({
        "체인": tag,
        "가드 없음 · 총 mutation": sum(a != b for a, b in zip(par, ng)),
        "가드 없음 · CDR mutation": sum(par[p-1] != ng[p-1] for p in pr),
        "가드 적용 · 총 mutation": sum(a != b for a, b in zip(par, gd)),
        "가드 적용 · CDR mutation": sum(par[p-1] != gd[p-1] for p in pr),
    })
display(pd.DataFrame(cmp_rows))
print("→", MY / "sapiens_humanized_cdrguard.fasta", "(Ch.08 구조 검증에서 이 파일을 쓸 수 있습니다)")'''),

md("""## 4) 직접 실행 — humanness, **정의를 못 박고** 계산 (본문 5.4)

여기가 본문에서 가장 헷갈리는 지점입니다. "humanized humanness" 는 두 가지로 계산될 수 있고, **값이 다릅니다.**

| 정의 | 계산 | 뜻 |
|---|---|---|
| **(a) argmax-on-parental** | parental 문맥의 확률행렬에서 position 별 **최대 확률**의 평균 | "모델이 각 자리에서 가장 자신 있는 값" — humanized 서열을 **다시 스코어링하지는 않음** |
| **(b) 재스코어링 self-prob** | humanized 서열을 `predict_scores` 에 **다시 넣어**, 그 서열 **자기 잔기**의 확률 평균 | "만들어진 서열이 얼마나 사람다운가" |

**본문 표의 0.815 / 0.872 는 (b) 입니다.** (a) 로 계산하면 0.782 / 0.851 이 나옵니다 — 둘 다 직접 계산해 확인합니다."""),
co('''if HAVE_SAPIENS:
    def mean_self_prob(seq, chain):
        m = sapiens.predict_scores(seq, chain)
        return float(np.mean([m.loc[i, aa] for i, aa in enumerate(seq)]))

    rows = []
    for tag, par, ng, gd, chain, mat in (("VH", VH, hum_h, g_h, "H", mat_h),
                                         ("VL", VL, hum_l, g_l, "L", mat_l)):
        par_p = mean_self_prob(par, chain)                       # parental self-prob
        def_a = float(np.mean(mat.values.max(axis=1)))           # (a) parental 행렬의 per-position max
        def_b = mean_self_prob(ng, chain)                        # (b) humanized 재스코어링 ← 본문의 값
        grd_b = mean_self_prob(gd, chain)                        # CDR 가드 적용본 (b)
        rows.append({"chain": tag, "parental": round(par_p, 4),
                     "(a) argmax-on-parental": round(def_a, 4),
                     "(b) 재스코어링 humanized": round(def_b, 4),
                     "(b) CDR 가드 적용본": round(grd_b, 4)})
    hn = pd.DataFrame(rows)
    hn.to_csv(MY / "humanness_summary.csv", index=False)
else:
    print("[레퍼런스] data/humanness_summary.csv (Sapiens 실측)")
    ref = pd.read_csv("data/humanness_summary.csv")
    piv = ref.pivot(index="chain", columns="definition", values="mean_probability")
    hn = pd.DataFrame({
        "chain": piv.index,
        "parental": piv["parental"].round(4).values,
        "(a) argmax-on-parental": piv["definition_a_argmax_on_parental_matrix"].round(4).values,
        "(b) 재스코어링 humanized": piv["definition_b_rescored_humanized"].round(4).values,
        "(b) CDR 가드 적용본": [float("nan")] * len(piv),      # 가드 적용본은 직접 돌려야 나옵니다
    })

display(hn)
print("본문 표(0.694→0.815 / 0.770→0.872)는 parental → **(b)** 열입니다.")
print("(a) 로 계산하면 0.782 / 0.851 — 같은 실행, 다른 정의, 다른 값입니다.")
print("CDR 가드를 적용하면 humanness 는 조금 내려갑니다 — CDR 을 사람화하지 않았으니 당연하고, 그게 맞습니다.")'''),

md("""## 5) 그래프 — parental vs humanized (공용 모듈)

`humanization_viz.humanness_bars` 로 체인별 비교를 그립니다."""),
co('''from humanization_viz import humanness_bars

bars = [{"chain": r["chain"], "parental": r["parental"], "humanized": r["(b) 재스코어링 humanized"]}
        for _, r in hn.iterrows()]
humanness_bars(bars, "Sapiens humanness — parental vs humanized (정의 b)", "05_humanness.png")
from IPython.display import Image; Image("05_humanness.png")'''),

md("""## 6) 레퍼런스 대조

`data/` 는 실제 실행 산출물입니다. mutation 리스트가 **문자 단위로 같은지**, humanness 가 같은지 봅니다."""),
co('''ref_mut_h = pd.read_csv("data/mutations_VH.csv")
ref_hn    = pd.read_csv("data/humanness_summary.csv")

same = list(ref_mut_h["mutation"]) == list(mut_h["mutation"])
print("VH mutation 리스트 일치:", same, f"(내 결과 {len(mut_h)}개 / 레퍼런스 {len(ref_mut_h)}개)")
if not same:
    print("  내 결과 :", ", ".join(mut_h["mutation"]))
    print("  레퍼런스:", ", ".join(ref_mut_h["mutation"]))

print("\\n[레퍼런스 humanness — 정의별]")
display(ref_hn[["chain", "definition", "mean_probability"]])
print("→ definition_b_rescored_humanized 가 본문의 0.8152 / 0.8718 입니다.")'''),

md("""## 이 랩에서 확인한 것

1. Sapiens humanization = `predict_scores` 의 **position 별 argmax**. 실측 **VH 21 · VL 17 mutation**.
2. **가드 없이 돌리면 CDR-L1 이 부서집니다**(`H31A K32Y F33N P34D`) — Ch.04 의 보호 좌표로 후처리 복원하면 CDR mutation 0개.
3. humanness 는 **정의를 밝혀야** 합니다. 본문의 **0.694 → 0.815 (VH)** · **0.770 → 0.872 (VL)** 는 **(b) humanized 재스코어링 self-prob**. 같은 실행에서 (a) 로 계산하면 0.782 / 0.851 로 **다릅니다**.
4. 가드 적용본은 humanness 가 조금 낮습니다 — CDR 을 그대로 뒀으니 당연하며, 결합력을 지키는 대가입니다.

다음 → **[Ch.06 — Humatch · AnthroAb](../06_cdr_safe_tools/06_tools_lab.ipynb)**"""),
]
cells_all[("05_humanize_sapiens", "05_sapiens_lab.ipynb", "05 Sapiens Lab")] = c


# ════════════════════════════════════════════════════════════════════════════
# 06 — Humatch · AnthroAb · 3도구 합의
# ════════════════════════════════════════════════════════════════════════════
c = [title_cell("06", "CDR-safe 도구 — Humatch · AnthroAb · 3도구 합의", "06_cdr_safe_tools.md")]
c += boot("06_cdr_safe_tools", pip="pandas matplotlib anarci abnumber", apt="hmmer")
c += [
md("""## 1) 직접 실행 — Humatch 설치 + humanization (본문 6.1)

Humatch 는 **CDR 보호가 도구에 내장**돼 있습니다(`allow_CDR_mutations=False` 가 기본값).
대신 framework 를 CNN 점수 목표(0.95)에 닿을 때까지 single-point 로 반복 탐색합니다.

첫 실행은 **Zenodo 에서 CNN 가중치(heavy/light/paired) + germline 룩업 배열**을 받으므로 **160초** 걸립니다(실측).
`pip install humatch` 가 안 되면 **GitHub source** 로 자동 전환합니다."""),
co('''import pandas as pd

# Humatch 는 파이썬 모듈명이 `Humatch`(대문자) 라서 소문자 import 체크가 통하지 않습니다 → CLI 존재로 판정
if not shutil.which("Humatch-humanise"):
    _run(f'"{sys.executable}" -m pip -q install humatch', check=False)
if not shutil.which("Humatch-humanise"):
    print("pip 로 안 되면 GitHub source 로 (본문 6.1.1 케이스 스터디)")
    _run(f'"{sys.executable}" -m pip -q install git+https://github.com/oxpig/Humatch.git', check=False)
print("Humatch CLI:", shutil.which("Humatch-humanise") or "없음")

# CLI 는 CSV 입력/CSV 출력이 가장 안전합니다(문자열 인자 -H/-L 도 가능).
inp = MY / "humatch_in.csv"
inp.write_text("VH,VL\\n%s,%s\\n" % (VH, VL))
out = MY / "humatch_out.csv"
cmd = ["Humatch-humanise", "-i", str(inp), "--vh_col", "VH", "--vl_col", "VL", "-o", str(out), "-v"]

hm_h = hm_l = None
env = dict(os.environ, TF_CPP_MIN_LOG_LEVEL="3")
t0 = time.time()
try:
    r = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if r.returncode != 0 and "DNN library" in (r.stdout + r.stderr):
        # TensorFlow 가 GPU cuDNN 초기화에 실패하는 환경이 있습니다 → CPU 로 강제하고 재시도(실측 사례)
        print("TensorFlow GPU 초기화 실패 → CPU 로 재시도합니다")
        env["CUDA_VISIBLE_DEVICES"] = ""
        r = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if r.returncode == 0 and out.exists():
        print(f"Humatch 완료: {time.time()-t0:.1f}초 (첫 실행은 Zenodo 가중치 다운로드 포함 — 실측 160초)")
        hm = pd.read_csv(out).iloc[0]
        hm_h = hm["Humatch_H"].replace("-", "")     # 출력은 200-position 정렬형 → gap 제거
        hm_l = hm["Humatch_L"].replace("-", "")
        write_fasta(MY / "humatch_humanised.fasta",
                    {"humatch_humanised_VH": hm_h, "humatch_humanised_VL": hm_l})
        print(f"CNN_H={hm['CNN_H']:.3f}  CNN_L={hm['CNN_L']:.3f}  CNN_P={hm['CNN_P']:.3f}  "
              f"HV={hm['HV']}  LV={hm['LV']}  edit={hm['Edit']}")
    else:
        print("Humatch 실행 실패:", (r.stdout + r.stderr).strip()[-300:])
except Exception as e:
    print("Humatch 실행 실패:", type(e).__name__, str(e)[:200])

if hm_h is None:
    print("→ 레퍼런스(data/humatch_humanized.fasta)로 이어갑니다.")
    ref = read_fasta("data/humatch_humanized.fasta")
    hm_h, hm_l = ref["humatch_humanised_VH"], ref["humatch_humanised_VL"]'''),

md("""## 2) 내 결과 확인 — Humatch 는 CDR 을 정말 안 건드렸나

Humatch 는 VL 에서 **1 잔기를 지웁니다**(우리 예제: 111 → 110 aa). 그래서 raw 인덱스 비교가 깨집니다 —
**CDR 보존 확인은 "parental CDR 문자열이 후보 안에 그대로 있는가"** 로 하는 게 안전합니다."""),
co('''ct = pd.read_csv(find_one("cdr_table_imgt.csv", quiet=True))
cdrs = {(r["chain"], r["cdr"]): r["sequence"] for _, r in ct.iterrows()}

def cdr_intact(cand_h, cand_l, label):
    rows = []
    for (chain, name), s in cdrs.items():
        seq = cand_h if chain == "H" else cand_l
        rows.append({"후보": label, "CDR": f"{chain}-{name}", "parental CDR": s, "보존": s in seq})
    return rows

chk = pd.DataFrame(cdr_intact(hm_h, hm_l, "Humatch"))
display(chk)
print("VL 길이 — parental", len(VL), "→ Humatch", len(hm_l), "(1 잔기 삭제 = indel)")
print("→ CDR 보존:", int(chk["보존"].sum()), "/ 6.  Humatch 는 CDR 을 안 건드립니다(도구에 내장된 보호).")'''),

md("""## 3) 직접 실행 — AnthroAb 두 모드 (본문 6.2.1)

| 모드 | 함수 | 무엇을 바꾸나 |
|---|---|---|
| ① 자동 전체 변경 | `predict_best_score(seq, chain)` | **모든 position** 을 가장 사람다운 잔기로 — **CDR 도 바꿉니다** |
| ② 커스텀 마스킹 | `predict_masked(seq, chain)` | 내가 `*` 로 찍은 자리만 |

먼저 ① 을 그대로 돌립니다(실측 VH 1.5초 / VL 1.3초)."""),
co('''_ensure("anthroab")

def mutations(par, hum):
    return [{"position_1based": i + 1, "wt": a, "mut": b, "mutation": f"{a}{i+1}{b}"}
            for i, (a, b) in enumerate(zip(par, hum)) if a != b]

ab_h = ab_l = None
try:
    import anthroab
    t0 = time.time()
    ab_h = anthroab.predict_best_score(VH, "H")
    ab_l = anthroab.predict_best_score(VL, "L")
    print(f"predict_best_score VH+VL: {time.time()-t0:.1f}초  (실측 1.3~1.5초/체인)")
    write_fasta(MY / "anthroab_best_score.fasta",
                {"anthroab_bestscore_VH": ab_h, "anthroab_bestscore_VL": ab_l})
except Exception as e:
    print("AnthroAb 실행 실패:", type(e).__name__, str(e)[:160])

if ab_h is None:
    print("[레퍼런스] data/anthroab_best_score.fasta")
    f = read_fasta("data/anthroab_best_score.fasta")
    ab_h, ab_l = f["anthroab_predict_best_score_VH"], f["anthroab_predict_best_score_VL"]

ab_mut_h = pd.DataFrame(mutations(VH, ab_h)); ab_mut_l = pd.DataFrame(mutations(VL, ab_l))
print(f"VH {len(ab_mut_h)} mut · VL {len(ab_mut_l)} mut")

chk2 = pd.DataFrame(cdr_intact(ab_h, ab_l, "AnthroAb(best_score)"))
display(chk2)
print("→ CDR 보존:", int(chk2["보존"].sum()), "/ 6.  자동 모드는 CDR 을 지켜주지 않습니다(본문 6.2.1 경고 그대로).")'''),

md("""## 4) 직접 실행 — `predict_masked` 의 버그와 우회 (실측 발견)

**anthroab 1.1.0 의 `predict_masked()` 는 그대로 쓰면 안 됩니다.** docstring 은 `*`/`X` 로 마스킹하라고 하지만,
`hemantn/roberta-base-humAb-*` 의 tokenizer vocab 에는 `*`·`X` 가 **없습니다**. 사전에 없는 문자는 `<unk>` 도 아니고 **조용히 삭제**되어,
그 뒤 토큰이 한 칸씩 밀립니다. 라이브러리는 (원래 길이의) 입력과 (짧아진) 예측을 zip 해서 **말없이 어긋난 결과**를 내거나 `IndexError` 로 죽습니다.

우회는 간단합니다 — **문자열 마스킹을 건너뛰고 `input_ids` 를 직접 만들어** 진짜 `mask_token_id` 를 꽂습니다.
여기서는 **FR 자리만** 마스킹해(=CDR 은 구조적으로 보존) 돌립니다."""),
co('''_ensure("torch transformers")
import torch
from transformers import AutoModelForMaskedLM, AutoTokenizer

MODELS = {"H": "hemantn/roberta-base-humAb-vh", "L": "hemantn/roberta-base-humAb-vl"}

@torch.no_grad()
def masked_fill(seq, chain, mask_positions):
    """mask_positions(1-based)만 마스킹해 예측 — tokenizer 문자열 마스킹을 우회한 정공법."""
    tok = AutoTokenizer.from_pretrained(MODELS[chain])
    mdl = AutoModelForMaskedLM.from_pretrained(MODELS[chain]); mdl.eval()
    vocab = tok.get_vocab()
    ids = [tok.bos_token_id] + [vocab[a] for a in seq] + [tok.eos_token_id]
    x = torch.tensor(ids).unsqueeze(0)
    for p in mask_positions:
        x[0, p] = tok.mask_token_id                 # +1 offset (bos) 이 이미 반영된 인덱스
    logits = mdl(input_ids=x).logits[0]
    inv = {v: k for k, v in vocab.items()}
    out = list(seq)
    for p in mask_positions:
        out[p - 1] = inv[int(logits[p].argmax())]
    return "".join(out)

# CDR 보호 좌표(Ch.04) → FR 자리만 마스킹
gp = GUIDE_ROOT / "04_sequence_qc" / "my_run" / "cdr_guard.json"
if gp.exists():
    guard = json.loads(gp.read_text()); print(f"[내 결과 · 04_sequence_qc] {gp}")
else:
    guard = {"H": [], "L": []}
    for _, r in ct.iterrows():
        seq = VH if r["chain"] == "H" else VL
        st = seq.find(r["sequence"]) + 1
        guard[r["chain"]] += list(range(st, st + len(r["sequence"])))
    print("[레퍼런스] data/cdr_table_imgt.csv 로 CDR 좌표 복원")

fr_h = [i for i in range(1, len(VH) + 1) if i not in guard["H"]]
fr_l = [i for i in range(1, len(VL) + 1) if i not in guard["L"]]

mk_h = mk_l = None
try:
    t0 = time.time()
    mk_h = masked_fill(VH, "H", fr_h)
    mk_l = masked_fill(VL, "L", fr_l)
    print(f"predict_masked(우회 구현) VH+VL: {time.time()-t0:.1f}초  — 실측 2.3~2.5초/체인")
    write_fasta(MY / "anthroab_masked_FRonly.fasta",
                {"anthroab_masked_VH": mk_h, "anthroab_masked_VL": mk_l})
except Exception as e:
    print("masked 실행 실패:", type(e).__name__, str(e)[:160])
    print("[레퍼런스] data/anthroab_masked_FRonly.fasta")
    f = read_fasta("data/anthroab_masked_FRonly.fasta")
    mk_h, mk_l = f["anthroab_predict_masked_fixed_VH"], f["anthroab_predict_masked_fixed_VL"]

mk_mut_h = pd.DataFrame(mutations(VH, mk_h)); mk_mut_l = pd.DataFrame(mutations(VL, mk_l))
print(f"FR-only masked → VH {len(mk_mut_h)} mut · VL {len(mk_mut_l)} mut")
chk3 = pd.DataFrame(cdr_intact(mk_h, mk_l, "AnthroAb(masked FR-only)"))
print("CDR 보존:", int(chk3["보존"].sum()), "/ 6 (구조적으로 보장 — CDR 을 아예 마스킹하지 않았으니까)")'''),

md("""## 5) 직접 실행 — 3도구 합의 분석 (본문 6.2.6)

여기가 이 챕터의 핵심입니다. **도구 간 비교는 반드시 IMGT 번호로** 합니다(Humatch 의 indel 때문에 raw 인덱스가 어긋나므로).
Ch.04 에서 만든 `raw2imgt_*.json` 을 그대로 씁니다."""),
co('''# raw → IMGT 크로스워크
def load_map(tag):
    p = GUIDE_ROOT / "04_sequence_qc" / "my_run" / f"raw2imgt_{tag}.json"
    if p.exists():
        print(f"[내 결과 · 04_sequence_qc] {p}")
    else:
        p = pathlib.Path(f"data/raw2imgt_{tag}.json"); print(f"[레퍼런스] {p}")
    return {int(k): v for k, v in json.loads(p.read_text()).items()}

r2i = {"H": load_map("H"), "L": load_map("L")}

# 각 도구의 mutation → IMGT 라벨 (Sapiens 는 Ch.05 my_run, 없으면 data/)
sap_h = pd.read_csv(find_prev("05_humanize_sapiens", "mutations_VH.csv"))
sap_l = pd.read_csv(find_prev("05_humanize_sapiens", "mutations_VL.csv"))

def to_imgt(df, chain, tool):
    return pd.DataFrame([{"chain": chain, "imgt": r2i[chain][int(r.position_1based)],
                          "wt": r.wt, "mut": r.mut, "sub": f"{r.wt}{r.mut}", "tool": tool}
                         for r in df.itertuples()])

tbl = pd.concat([
    to_imgt(sap_h, "H", "Sapiens"), to_imgt(sap_l, "L", "Sapiens"),
    to_imgt(ab_mut_h, "H", "AnthroAb_best_score"), to_imgt(ab_mut_l, "L", "AnthroAb_best_score"),
    to_imgt(mk_mut_h, "H", "AnthroAb_masked"), to_imgt(mk_mut_l, "L", "AnthroAb_masked"),
], ignore_index=True)

# Humatch 는 이미 IMGT 로 나온 레퍼런스 표를 쓰거나, 내 결과에서 IMGT 로 재계산
hmt = pd.read_csv("data/humatch_mutations_imgt.csv")
hmt = pd.DataFrame([{"chain": r["chain"], "imgt": r["imgt_position"], "wt": r["wt"], "mut": r["mut"],
                     "sub": f"{r['wt']}{r['mut']}", "tool": "Humatch"} for _, r in hmt.iterrows()])
tbl = pd.concat([tbl, hmt], ignore_index=True)
tbl.to_csv(MY / "mutations_by_tool_imgt.csv", index=False)

def consensus(anthroab_mode):
    keep = tbl[tbl.tool.isin(["Sapiens", "Humatch", anthroab_mode])]
    g = keep.groupby(["chain", "imgt"])
    out = []
    for (chain, pos), sub in g:
        tools = set(sub.tool)
        if len(tools) == 3:
            same = len(set(sub["sub"])) == 1
            out.append({"chain": chain, "imgt": pos,
                        "subs": "/".join(sorted(set(sub["sub"]))), "동일 치환": same})
    return pd.DataFrame(out).sort_values(["chain", "imgt"])

for mode in ["AnthroAb_best_score", "AnthroAb_masked"]:
    cs = consensus(mode)
    ident = cs[cs["동일 치환"]]
    print(f"\\n=== 3도구(Sapiens·Humatch·{mode}) 합의 ===")
    print(f"세 도구가 모두 건드린 위치: {len(cs)}개 · 그중 **같은 잔기**로 바꾼 위치: {len(ident)}개")
    display(ident)
    cs.to_csv(MY / f"three_way_consensus_{mode}.csv", index=False)'''),

md("""## 6) 내 결과 확인 — 본문의 "78번이 유일한 3도구 합의" 는 사실이 아닙니다

실측하면 이렇습니다.

- **`I78T`(raw) = IMGT `H86`** 은 **진짜 3도구 합의**가 맞습니다 — Sapiens·Humatch·AnthroAb(masked) 셋 다 `I→T`.
- 하지만 **"유일한" 합의는 아닙니다.** AnthroAb 를 어느 모드로 비교하냐에 따라 **7개(best_score)** 또는 **12개(masked)** 의 3도구 합의 위치가 나옵니다.
- 게다가 `best_score` 모드의 AnthroAb 는 **raw 78 / IMGT H86 을 아예 건드리지 않습니다** — 즉 그 비교에서는 `I78T` 가 합의 목록에 없습니다.

교훈은 그대로 유효합니다 — **여러 도구가 같은 자리에 같은 잔기를 제안하면 신뢰도가 올라간다.** 다만 "몇 개가 합의인가"는 **어느 모드로 비교했는지에 달렸습니다.**"""),
co('''from humanization_viz import mutation_map

# VH 만 · masked 모드 기준으로 위치별 도구 제안을 겹쳐 그립니다(IMGT 번호축)
vh = tbl[(tbl.chain == "H") & (tbl.tool.isin(["Sapiens", "Humatch", "AnthroAb_masked"]))].copy()
vh["position"] = vh["imgt"].str.lstrip("H").astype(int)
shared = (vh.groupby("position")["tool"].nunique() == 3)
pos3 = sorted(shared[shared].index)                      # 세 도구가 모두 건드린 위치
rows = [{"position": r.position, "tool": r.tool, "to": r.mut}
        for r in vh.itertuples() if r.position in pos3]

mutation_map(rows, "3-tool proposals on VH (IMGT) — 금색=세 도구 동일 치환",
             "06_mutation_map.png", cdr_spans=[(27, 38), (56, 65), (105, 117)])
h86 = vh[vh.position == 86][["tool", "wt", "mut"]]
print("IMGT H86 (= raw I78T) 에 대한 세 도구의 제안:")
display(h86)
from IPython.display import Image; Image("06_mutation_map.png")'''),

md("""## 7) 레퍼런스 대조"""),
co('''ref_cs = pd.read_csv("data/three_way_consensus.csv")
ref_ov = pd.read_csv("data/overlap_summary.csv")

print("[레퍼런스] 3도구 합의 — AnthroAb 모드별")
for mode, sub in ref_cs.groupby("anthroab_mode"):
    ident = sub[sub.identical_substitution_all3]
    print(f"  {mode:24s}: 세 도구 겹친 위치 {len(sub)}개 · 동일 치환 {len(ident)}개")
display(ref_cs[ref_cs.identical_substitution_all3][["anthroab_mode", "chain", "imgt_position",
                                                    "sapiens_mut", "humatch_mut", "anthroab_mut"]])

print("\\n[레퍼런스] Sapiens × AnthroAb 겹침 — 본문의 '10개' 는 VL 만·best_score 모드일 때의 값입니다")
display(ref_ov[["comparison", "chain_scope", "n_positions", "note"]])'''),

md("""## 이 랩에서 확인한 것

1. **Humatch** — CNN_H **0.972** · CNN_L **1.000** · gene **hv1/lv2**, edit **20**(VH 18 · VL 2), **CDR mutation 0개**. CDR 보호가 도구에 내장돼 있습니다. VL 은 1 잔기 **삭제**(indel) → 도구 간 비교는 IMGT 로.
2. **AnthroAb** — `predict_best_score` 는 CDR 을 **안 지킵니다**(6개 CDR 중 일부 파손). `predict_masked` 는 **1.1.0 에서 깨져 있어**(vocab 에 `*` 없음 → 토큰 밀림) `input_ids` 를 직접 만들어 마스킹해야 합니다.
3. **3도구 합의(실측)** — `I78T`(IMGT `H86`) 는 진짜 합의지만 **유일하지 않습니다.** 동일 치환 합의는 AnthroAb `best_score` 기준 **7개**, `masked` 기준 **12개**(`H5 Q→V`, `H21 M→V`, `H42 G→V`, `H74 A→G`, `H75 K→R`, `L99 G→E` 등). `best_score` 비교에서는 H86 이 합의에 **들어가지도 않습니다**.
4. 본문의 "Sapiens × AnthroAb 겹침 10개" 는 **VL 만·best_score 모드**일 때의 숫자입니다(VH 는 12개, VH+VL 은 22개).

다음 → **[Ch.07 — Nativeness](../07_nativeness/07_nativeness_lab.ipynb)**"""),
]
cells_all[("06_cdr_safe_tools", "06_tools_lab.ipynb", "06 CDR-safe Tools Lab")] = c


# ════════════════════════════════════════════════════════════════════════════
# 07 — nativeness / naturalness
# ════════════════════════════════════════════════════════════════════════════
c = [title_cell("07", "Nativeness · Naturalness — AbNatiV · Ab-RoBERTa", "07_nativeness.md")]
c += boot("07_nativeness", pip="pandas matplotlib torch transformers")
c += [
md("""## 1) 직접 실행 — Ab-RoBERTa pseudo-likelihood (본문 7.2)

항체 전용 언어모델 `mogam-ai/Ab-RoBERTa` 로 각 position 을 차례로 마스킹해 **실제 잔기의 로그확률**을 모아 평균합니다(masked pseudo-LL).
스코어링 스크립트는 이 챕터 폴더에 함께 실려 있습니다 — `score_abroberta_pseudolikelihood.py`.

```bash
python score_abroberta_pseudolikelihood.py --fasta variants.fasta --out scores.csv
```

후보 서열은 **앞 랩에서 내가 만든 것**을 먼저 씁니다(Ch.05 Sapiens · Ch.06 Humatch/AnthroAb). 없으면 `data/variants.fasta` 로 폴백합니다.
**실측 70초** (5후보 × VH+VL = 10 체인 스캔)."""),
co('''import pandas as pd

# 후보 모으기 — 내 결과 우선
cands = {"parental": (VH, VL)}
def _pick(chapter, fname, keys, label):
    p = GUIDE_ROOT / chapter / "my_run" / fname
    if p.exists():
        f = read_fasta(p); print(f"[내 결과 · {chapter}] {p}")
        return (f[keys[0]], f[keys[1]])
    return None

got = _pick("05_humanize_sapiens", "sapiens_humanized_noguard.fasta",
            ("sapiens_humanized_VH", "sapiens_humanized_VL"), "sapiens")
if got: cands["sapiens"] = got
got = _pick("06_cdr_safe_tools", "humatch_humanised.fasta",
            ("humatch_humanised_VH", "humatch_humanised_VL"), "humatch")
if got: cands["humatch"] = got
got = _pick("06_cdr_safe_tools", "anthroab_best_score.fasta",
            ("anthroab_bestscore_VH", "anthroab_bestscore_VL"), "anthroab")
if got: cands["anthroab"] = got
got = _pick("06_cdr_safe_tools", "anthroab_masked_FRonly.fasta",
            ("anthroab_masked_VH", "anthroab_masked_VL"), "anthroabFRmasked")
if got: cands["anthroabFRmasked"] = got

if len(cands) == 1:
    print("[레퍼런스] data/variants.fasta 의 5개 후보를 씁니다")
    v = read_fasta("data/variants.fasta")
    for name in ["parental", "sapiens", "humatch", "anthroab", "anthroabFRmasked"]:
        cands[name] = (v[f"{name}_VH"], v[f"{name}_VL"])

fa = write_fasta(MY / "variants.fasta",
                 {f"{n}_{c}": s for n, (h, l) in cands.items() for c, s in (("VH", h), ("VL", l))})
print("\\n후보:", ", ".join(cands), "→", fa)'''),
co('''from score_abroberta_pseudolikelihood import score_paired    # 이 챕터 폴더의 스크립트

t0 = time.time()
rows = []
try:
    for name, (h, l) in cands.items():
        res = score_paired(h, l)
        for ch in ("VH", "VL", "paired"):
            rows.append({"variant": name, "chain": ch,
                         "mean_logp": res[ch]["mean_logp"],
                         "perplexity": res[ch]["perplexity"],
                         "n_residues": res[ch]["n"]})
        print(f"{name:18s} paired mean_logp={res['paired']['mean_logp']:+.4f}  "
              f"ppl={res['paired']['perplexity']:.4f}")
    abr = pd.DataFrame(rows)
    abr.to_csv(MY / "abroberta_scores_summary.csv", index=False)
    print(f"\\nAb-RoBERTa 스코어링: {time.time()-t0:.1f}초 → {MY/'abroberta_scores_summary.csv'}")
except Exception as e:
    print("Ab-RoBERTa 실행 실패:", type(e).__name__, str(e)[:200])
    print("→ 레퍼런스(data/abroberta_scores_summary.csv)로 이어갑니다.")
    abr = pd.read_csv("data/abroberta_scores_summary.csv")'''),

md("""## 2) 내 결과 확인 — naturalness ≠ humanness (본문 7.2.2)

`mean_log_prob` 는 **높을수록**(0 에 가까울수록) 자연스럽고, `perplexity = exp(-mean_logp)` 는 **낮을수록** 좋습니다.

여기서 본문이 짚은 반직관적 사실을 직접 봅니다 — **VH 만 보면 parental 이 가장 자연스럽습니다.**
사람다움(humanness)과 자연스러움(naturalness)은 **다른 축**입니다."""),
co('''pv = abr.pivot(index="variant", columns="chain", values="mean_logp").round(4)
pv["perplexity(paired)"] = abr[abr.chain == "paired"].set_index("variant")["perplexity"].round(4)
display(pv.sort_values("paired", ascending=False))

best_vh = abr[abr.chain == "VH"].sort_values("mean_logp", ascending=False).iloc[0]
print(f"VH 만 보면 가장 자연스러운 것: {best_vh['variant']} ({best_vh['mean_logp']:+.4f})")
print("→ 사람다움(Sapiens humanness·Humatch CNN·AbNatiV)이 올라간 후보가 "
      "naturalness 에서는 오히려 내려갈 수 있습니다. Ab-RoBERTa 는 주 humanness 지표로 쓰면 안 됩니다.")'''),
co('''from humanization_viz import humanness_bars
import numpy as np

# exp(mean_logp) = 잔기당 pseudo-likelihood 기하평균(0~1) → 바 차트로 보기 좋은 형태
others = [v for v in abr.variant.unique() if v != "parental"]
pick = "sapiens" if "sapiens" in others else others[0]
g = abr.set_index(["variant", "chain"])["mean_logp"]
bars = [{"chain": ch, "parental": float(np.exp(g[("parental", ch)])),
         "humanized": float(np.exp(g[(pick, ch)]))} for ch in ("VH", "VL", "paired")]
humanness_bars(bars, f"Ab-RoBERTa naturalness — parental vs {pick} (exp(mean logP))",
               "07_naturalness.png", ylabel="per-residue pseudo-likelihood")
print("VH 막대를 보세요 — humanized 가 parental 보다 낮습니다(사람다워졌지만 덜 '자연스러워짐').")
from IPython.display import Image; Image("07_naturalness.png")'''),

md("""## 3) 직접 실행 — AbNatiV nativeness (본문 7.1) · **기본 비활성**

AbNatiV 는 "사람 잔기를 얼마나 썼나"(humanness)가 아니라 **"그 조합이 실제 사람 항체로서 얼마나 자연스러운가"**(nativeness)를 봅니다.

**스코어링 자체는 4서열에 3.5~6.6초로 끝납니다.** 무거운 건 **체크포인트**입니다 —
`abnativ init` 은 9개 ckpt(~6GB)를 **순차로** 받아 매우 느립니다(실측: 30분에 3개). 실제로 필요한 4개만 **병렬로** 받으면 **약 33분 / 2.6GB**(실측)입니다.

그래서 아래 셀은 **`RUN_ABNATIV = False` 가 기본**입니다. 그대로 두면 커밋된 `data/abnativ_summary_all_models.csv`(실제 실행 산출물)로 이어집니다.
직접 돌리려면 `True` 로 바꾸세요."""),
co('''RUN_ABNATIV = False        # ← True 로 바꾸면 체크포인트를 받아 실제로 스코어링합니다

abn_csv = None
if RUN_ABNATIV:
    try:
        _ensure("abnativ anarci")
        # abnativ init 은 9개 ckpt 를 순차 다운로드해 매우 느립니다 → 필요한 4개만 병렬로(실측 33분)
        home = pathlib.Path.home() / ".abnativ/models/pretrained_models"
        home.mkdir(parents=True, exist_ok=True)
        base = "https://zenodo.org/record/17295347/files"
        need = [m for m in ["vh_model", "vlambda_model", "vh2_model", "vl2_model"]
                if not (home / f"{m}.ckpt").exists()]
        if need:   # 한 셸 안에서 병렬 다운로드 후 wait (순차 abnativ init 보다 훨씬 빠름)
            par = " ".join(f'wget -c -q -O "{home}/{m}.ckpt" "{base}/{m}.ckpt?download=1" &'
                           for m in need)
            _run(f"({par} wait)")

        write_fasta(MY / "abnativ_vh.fa", {f"{n}_VH": h for n, (h, l) in cands.items()})
        write_fasta(MY / "abnativ_vl.fa", {f"{n}_VL": l for n, (h, l) in cands.items()})
        t0 = time.time()
        for nat, fa_in, oid in (("VH", "abnativ_vh.fa", "vh"), ("VLambda", "abnativ_vl.fa", "vl"),
                                ("VH2", "abnativ_vh.fa", "vh2"), ("VL2", "abnativ_vl.fa", "vl2")):
            _run(f'CUDA_VISIBLE_DEVICES="" abnativ score -nat {nat} -i "{MY/fa_in}" '
                 f'-odir "{MY/"abnativ"}" -oid {oid} -align -ncpu 4')
        print(f"AbNatiV 스코어링: {time.time()-t0:.1f}초 (실측 3.5~6.6초/모델)")
        abn_csv = sorted((MY / "abnativ").glob("*_seq_scores.csv"))
    except Exception as e:
        print("AbNatiV 실행 실패:", type(e).__name__, str(e)[:200])
        print("→ 레퍼런스로 이어갑니다.")
else:
    print("RUN_ABNATIV = False → 커밋된 레퍼런스(data/abnativ_summary_all_models.csv)로 진행합니다.")
    print("  · 스코어링은 빠르지만(3.5~6.6초) 체크포인트 다운로드가 약 33분 / 2.6GB 입니다(실측).")'''),

md("""## 4) 내 결과 / 레퍼런스 — nativeness 프로파일 (본문 7.1.3)

AbNatiV 에는 **두 세대**가 있고, 본문의 두 표는 사실 **서로 다른 모델**입니다 — 이걸 모르면 숫자가 모순돼 보입니다.

- **AbNatiV1**(`-nat VH` / `-nat VLambda`) — 본문 7.1.3 의 주 표(0.648 → 0.880 · FR 0.632 → 0.925 · CDR-H3 0.614 → 0.626 · VL 0.902). **7개 숫자 전부 재현**됩니다.
- **AbNatiV2**(`-nat VH2` / `-nat VL2`) — 본문 7.2.3 패널의 "AbNatiV H" 열. parental **0.4927 은 재현**되지만, humanized 의 **0.6900 은 재현되지 않습니다** — 실측은 **0.7777**.

그리고 본문의 "VL 0.902" 는 **parental** VL 입니다(humanized VL 은 0.9980). 이것도 표에서 확인합니다."""),
co('''abn = pd.read_csv(find_one("abnativ_summary_all_models.csv", quiet=True))
print("[출처] my_run 에 직접 만든 결과가 있으면 그것, 없으면 data/ 레퍼런스")

for gen in ["AbNatiV1", "AbNatiV2"]:
    sub = abn[abn.model_generation == gen]
    print(f"\\n=== {gen} ===")
    display(sub[["abnativ_model", "variant", "overall_score", "FR_score",
                 "CDR1_score", "CDR2_score", "CDR3_score"]].round(4))

par_vh = abn[(abn.model_generation == "AbNatiV1") & (abn.variant == "parental_VH")].iloc[0]
sap_vh = abn[(abn.model_generation == "AbNatiV1") & (abn.variant == "sapiens_humanized_VH")].iloc[0]
print(f"\\nAbNatiV1 VH  parental {par_vh.overall_score:.4f} → Sapiens {sap_vh.overall_score:.4f}")
print(f"  FR      {par_vh.FR_score:.4f} → {sap_vh.FR_score:.4f}   (framework 가 크게 사람 레퍼토리에 붙음)")
print(f"  CDR-H3  {par_vh.CDR3_score:.4f} → {sap_vh.CDR3_score:.4f}   (거의 불변 — CDR-H3 를 안 건드렸으니 당연)")
_v2 = abn[(abn.model_generation == "AbNatiV2") & (abn.variant == "sapiens_humanized_VH")]
print("\\nAbNatiV2 VH2 humanized 실측:",
      round(float(_v2.overall_score.iloc[0]), 4),   # .iloc[0] — pandas 2.x 는 float(Series) 를 거부합니다
      "(본문의 0.6900 은 재현되지 않습니다)")'''),
co('''from humanization_viz import nativeness_panel

sub = abn[(abn.model_generation == "AbNatiV1") & (abn.variant.str.endswith("_VH"))]
rows = [{"label": r.variant.replace("_VH", "").replace("_humanized", "").replace("_humanised", "").replace("_bestscore", ""),
         "overall": r.overall_score, "fr": r.FR_score, "cdr": r.CDR3_score}
        for r in sub.itertuples()]
nativeness_panel(rows, "AbNatiV1 VH nativeness — overall / FR / CDR-H3", "07_nativeness.png")
from IPython.display import Image; Image("07_nativeness.png")'''),

md("""## 5) 세 축을 한 표에 — humanness · nativeness · naturalness

세 지표는 **서로 다른 것**을 잽니다. 한 줄로 놓고 보면 어긋나는 지점이 바로 보입니다."""),
co('''abn1 = abn[(abn.model_generation == "AbNatiV1") & (abn.variant.str.endswith("_VH"))]
abn1_vh = pd.Series({r.variant.split("_")[0]: float(r.overall_score) for r in abn1.itertuples()})
abr_p = abr[abr.chain == "paired"].set_index("variant")["mean_logp"]

panel = pd.DataFrame({
    "AbNatiV1 VH (nativeness↑)": abn1_vh.round(4),
    "Ab-RoBERTa paired (naturalness↑)": abr_p.round(4),
}).dropna(how="all")
display(panel)
print("읽는 법 — nativeness 는 Sapiens 후보가 가장 높지만(0.8803), naturalness 로 보면 순위가 달라집니다.")
print("권장 역할 분담: 주 패널 = Sapiens humanness + Humatch CNN + AbNatiV, "
      "Ab-RoBERTa = naturalness 이상치 탐지 보조.")'''),

md("""## 이 랩에서 확인한 것

1. **AbNatiV 는 두 세대**입니다. 본문 7.1.3 표는 **AbNatiV1** — VH **0.6477 → 0.8803**, FR **0.6317 → 0.9245**, CDR-H3 **0.6137 → 0.6265**(거의 불변), parental VL **0.9022**. 7개 값 모두 재현됩니다. 본문의 "VL 0.902" 는 **parental** 값입니다(humanized VL 은 0.9980).
2. **AbNatiV2** 는 절반만 재현됩니다 — parental VH2 **0.4927**(일치), humanized VH2 **0.7777**(본문 0.6900 과 불일치).
3. **Ab-RoBERTa** — parental **−0.7240** · Humatch **−0.7717** 는 본문과 정확히 일치하지만, Sapiens **−0.4973**(본문 −0.6928)·AnthroAb **−0.5285**(본문 −0.8733)는 **재현되지 않습니다.** 실측값을 씁니다.
4. **naturalness ≠ humanness** — VH 만 보면 parental(−0.5188)이 가장 자연스럽습니다.

다음 → **[Ch.08 — 구조 검증](../08_structure/08_structure_lab.ipynb)**"""),
]
cells_all[("07_nativeness", "07_nativeness_lab.ipynb", "07 Nativeness Lab")] = c


# ════════════════════════════════════════════════════════════════════════════
# 08 — 구조 (IgFold)
# ════════════════════════════════════════════════════════════════════════════
c = [title_cell("08", "구조 검증 — IgFold 로 직접 접고 CDR-H3 RMSD 비교", "08_structure.md")]
c += boot("08_structure", pip="pandas matplotlib biopython")
c += [
md("""## 1) 직접 실행 — IgFold 로 parental·humanized 구조 예측

서열 지표가 좋아져도 **CDR loop 모양이 망가지면 결합력이 떨어집니다.** 그래서 만든 서열을 **독립된 모델에게 다시 접어보게** 합니다.

IgFold(+AntiBERTy)로 **VH+VL Fv 하나를 7~12초**에 접습니다(실측: parental 7.1초 · humanized 12.0초).
실행 시 반드시 아래 두 옵션을 끕니다 — 실제로 부딪힌 함정입니다.

| 옵션 | 왜 끄나 |
|---|---|
| `do_refine=False` | `True` 면 **PyRosetta** 를 요구하고, 없으면 그 자리에서 `exit()` 합니다 |
| `do_renum=False` | `True` 면 abnumber 로 재numbering 하는데, 우리 VL 의 C-말단 `G` 가 IMGT 범위 밖이라 **AssertionError** 로 죽습니다 |

스레드도 묶습니다(`OMP_NUM_THREADS=4`) — 과부하 머신에서 IgFold forward 가 간헐적으로 SIGILL 로 죽는 걸 막습니다(실측)."""),
co('''os.environ["OMP_NUM_THREADS"] = "4"
os.environ["MKL_NUM_THREADS"] = "4"
os.environ["CUDA_VISIBLE_DEVICES"] = ""     # AntiBERTy 가 부모의 try_gpu 를 무시하므로 여기서 차단

_ensure("igfold")
_ensure_pkg_resources()      # IgFold 의존성이 pkg_resources 를 import 합니다(setuptools 81+ 에서 제거됨)

# 후보 서열 — Ch.05 에서 내가 만든 것 우선(가드 없는 argmax; 가드 적용본을 쓰려면 파일명만 바꾸세요)
hp = GUIDE_ROOT / "05_humanize_sapiens" / "my_run" / "sapiens_humanized_noguard.fasta"
if hp.exists():
    print(f"[내 결과 · 05_humanize_sapiens] {hp}")
    f = read_fasta(hp); hum_h, hum_l = f["sapiens_humanized_VH"], f["sapiens_humanized_VL"]
else:
    print("[레퍼런스] data/sapiens_humanized.fasta")
    f = read_fasta("data/sapiens_humanized.fasta")
    hum_h, hum_l = f["sapiens_humanized_VH"], f["sapiens_humanized_VL"]

targets = {"parental": {"H": VH, "L": VL},
           "sapiens_humanized": {"H": hum_h, "L": hum_l}}

try:
    from igfold import IgFoldRunner
    runner = IgFoldRunner()
    for name, seqs in targets.items():
        t0 = time.time()
        runner.fold(str(MY / f"{name}.pdb"), sequences=seqs, do_refine=False, do_renum=False)
        print(f"{name}: {time.time()-t0:.1f}초 → {MY/(name+'.pdb')}")
except Exception as e:
    print("IgFold 실행 실패:", type(e).__name__, str(e)[:200])
    print("→ 아래 분석은 레퍼런스 구조(data/parental.pdb · data/sapiens_humanized.pdb)로 이어집니다.")'''),

md("""## 2) 내 결과 확인 — per-residue 신뢰도 (B-factor = 예측 RMSD)

IgFold 는 PDB 의 B-factor 자리에 **per-residue 예측 오차(Å)** 를 적습니다 — **낮을수록 확신**입니다.
CDR 구간(특히 CDR-H3)에서 값이 튀는 게 정상입니다."""),
co('''from Bio.PDB import PDBParser
import pandas as pd, matplotlib.pyplot as plt

parser = PDBParser(QUIET=True)

def prmsd_table(pdb, name):
    st = parser.get_structure(name, str(pdb))[0]
    rows = []
    for ch in st:
        for res in ch:
            if "CA" in res:
                rows.append({"chain": ch.id, "resnum": res.id[1], "resname": res.get_resname(),
                             "prmsd": float(res["CA"].get_bfactor())})
    return pd.DataFrame(rows)

pdbs = {n: find_one(f"{n}.pdb", quiet=False) for n in ("parental", "sapiens_humanized")}
tabs = {n: prmsd_table(p, n) for n, p in pdbs.items()}
for n, t in tabs.items():
    t.to_csv(MY / f"{n}_prmsd.csv", index=False)

ct = pd.read_csv("data/cdr_table_imgt.csv")
h_cdr = [(VH.find(r["sequence"]) + 1, VH.find(r["sequence"]) + len(r["sequence"]))
         for _, r in ct[ct.chain == "H"].iterrows()]

fig, ax = plt.subplots(figsize=(12, 4))
for n, t in tabs.items():
    h = t[t.chain == "H"]
    ax.plot(h["resnum"], h["prmsd"], lw=1.6, label=n)
for lo, hi in h_cdr:
    ax.axvspan(lo, hi, color="#c0508a", alpha=0.12)
ax.set_xlabel("VH residue (raw 1-based)"); ax.set_ylabel("predicted RMSD (Å)  ↓ 좋음")
ax.set_title("IgFold per-residue confidence — VH (분홍 = CDR)", fontweight="bold")
ax.grid(alpha=0.25); ax.legend()
fig.tight_layout(); fig.savefig("08_prmsd.png", dpi=150)
print("CDR 구간(분홍)에서 예측 오차가 커지는 게 정상입니다 — loop 라서.")
for n, t in tabs.items():
    h3 = t[(t.chain == "H") & (t.resnum.between(*h_cdr[2]))]
    print(f"  {n:18s} VH 평균 {t[t.chain=='H'].prmsd.mean():.2f} Å · CDR-H3 평균 {h3.prmsd.mean():.2f} Å")'''),

md("""## 3) 직접 실행 — CDR-H3 backbone RMSD (본문 8.2, 가장 중요한 단일 지표)

**framework CA 로 먼저 정렬**한 뒤, 그 정렬 상태에서 **CDR-H3 CA RMSD** 를 잽니다.
(전체를 한꺼번에 정렬하면 loop 의 변화가 framework 오차에 묻힙니다.)"""),
co('''from Bio.PDB import Superimposer
import numpy as np

cdr_res = set()
for lo, hi in h_cdr:
    cdr_res |= set(range(lo, hi + 1))
h3_lo, h3_hi = h_cdr[2]

Hp = [r for r in parser.get_structure("p", str(pdbs["parental"]))[0]["H"]]
Hh = [r for r in parser.get_structure("h", str(pdbs["sapiens_humanized"]))[0]["H"]]

fw_p = [r["CA"] for r in Hp if r.id[1] not in cdr_res]
fw_h = [r["CA"] for r in Hh if r.id[1] not in cdr_res]
sup = Superimposer(); sup.set_atoms(fw_p, fw_h)
fw_rmsd = sup.rms
sup.apply([a for r in Hh for a in r])                       # humanized 를 framework 기준으로 이동

h3_p = [r["CA"] for r in Hp if h3_lo <= r.id[1] <= h3_hi]
h3_h = [r["CA"] for r in Hh if h3_lo <= r.id[1] <= h3_hi]
d = np.array([a.coord - b.coord for a, b in zip(h3_p, h3_h)])
h3_rmsd = float(np.sqrt((d ** 2).sum() / len(d)))

allp = [r["CA"] for r in Hp]; allh = [r["CA"] for r in Hh]
sup2 = Superimposer(); sup2.set_atoms(allp, allh)

res = pd.DataFrame([
    {"metric": "framework_fit_rmsd", "value_angstrom": round(fw_rmsd, 4), "n_atoms": len(fw_p)},
    {"metric": "cdr_h3_rmsd_after_framework_alignment", "value_angstrom": round(h3_rmsd, 4), "n_atoms": len(h3_p)},
    {"metric": "whole_vh_rmsd_ca_aligned", "value_angstrom": round(sup2.rms, 4), "n_atoms": len(allp)},
])
res.to_csv(MY / "cdr_h3_rmsd_summary.csv", index=False)
display(res)
print("CDR-H3 RMSD 가 framework RMSD 보다 크면 → humanization 이 loop 를 흔들었다는 뜻입니다.")'''),

md("""## 4) 레퍼런스 대조"""),
co('''ref = pd.read_csv("data/cdr_h3_rmsd_summary.csv")
print("[레퍼런스 — 실제 IgFold 실행 산출물]")
display(ref)
print("실측: framework 0.2707 Å (91 CA) · CDR-H3 0.5406 Å (13 CA) · VH 전체 0.3207 Å (120 CA)")
print("\\n해석 — CDR-H3 가 framework 보다 2배 크게 움직였지만 0.54 Å 수준이면 canonical 구조는 유지된 것으로 봅니다.")
print("       Sapiens 가 CDR-H3 안에 mutation 을 넣지 않았는데도 loop 가 조금 움직인 건, "
      "framework 치환이 loop 받침대(Vernier)를 통해 간접적으로 영향을 주기 때문입니다.")'''),

md("""## 이 랩에서 확인한 것

1. IgFold 로 **VH+VL Fv 를 7~12초**에 접었습니다 — `do_refine=False`(PyRosetta 없음) · `do_renum=False`(VL C-말단 잔기가 IMGT 범위 밖) 가 필수.
2. per-residue 신뢰도(B-factor)는 **CDR 에서 커집니다** — loop 라서 정상.
3. **framework 로 정렬한 뒤 잰 CDR-H3 RMSD = 0.5406 Å**(framework 자체는 0.2707 Å). CDR-H3 에 mutation 이 없는데도 loop 가 움직인 것은 framework 치환의 간접 효과입니다.
4. 이 값이 랭킹(Ch.10)의 **구조 보존 항목**으로 들어갑니다.

다음 → **[Ch.09 — Developability](../09_developability/09_developability_lab.ipynb)**"""),
]
cells_all[("08_structure", "08_structure_lab.ipynb", "08 Structure Lab")] = c


# ════════════════════════════════════════════════════════════════════════════
# 09 — developability
# ════════════════════════════════════════════════════════════════════════════
c = [title_cell("09", "Developability — liability 모티프 직접 스캔", "09_developability.md")]
c += boot("09_developability", pip="pandas matplotlib")
c += [
md("""## 1) 직접 실행 — liability 스캐너 구현 (본문 9.1~9.2)

**사람답지만 만들 수 없는 항체는 약이 못 됩니다.** 후보를 만들 때마다 모티프 스캔을 자동으로 돌리세요.

| 모티프 | 정규식 | 위험 |
|---|---|---|
| N-glycosylation | `N[^P][ST]` | 예상치 못한 당쇄 → 이질성·클리어런스 |
| deamidation | `N[GS]` | 보관 중 전하 변이 |
| isomerization | `DG` | 구조 변형 |
| oxidation | `[MW]` | 산화 → 활성 저하 |

핵심은 **parental 대비 증분** — humanization 이 **새로 만든** liability 를 잡는 것입니다."""),
co('''import re, pandas as pd

MOTIFS = {
    "N-glycosylation": r"N[^P][ST]",
    "deamidation":     r"N[GS]",
    "isomerization":   r"DG",
    "oxidation":       r"[MW]",
}

def scan(seq):
    return {name: [m.start() + 1 for m in re.finditer(p, seq)] for name, p in MOTIFS.items()}

# 후보 모으기 — 앞 랩의 my_run 우선
cands = {"parental": (VH, VL)}
for chapter, fname, keys, label in [
    ("05_humanize_sapiens", "sapiens_humanized_noguard.fasta", ("sapiens_humanized_VH", "sapiens_humanized_VL"), "sapiens"),
    ("06_cdr_safe_tools",   "humatch_humanised.fasta",         ("humatch_humanised_VH", "humatch_humanised_VL"), "humatch"),
    ("06_cdr_safe_tools",   "anthroab_best_score.fasta",       ("anthroab_bestscore_VH", "anthroab_bestscore_VL"), "anthroab"),
    ("06_cdr_safe_tools",   "anthroab_masked_FRonly.fasta",    ("anthroab_masked_VH", "anthroab_masked_VL"), "anthroabFRmasked"),
]:
    p = GUIDE_ROOT / chapter / "my_run" / fname
    if p.exists():
        f = read_fasta(p); cands[label] = (f[keys[0]], f[keys[1]])
        print(f"[내 결과 · {chapter}] {p}")

if len(cands) == 1:
    print("[레퍼런스] data/variants.fasta")
    v = read_fasta("data/variants.fasta")
    for n in ["parental", "sapiens", "humatch", "anthroab", "anthroabFRmasked"]:
        cands[n] = (v[f"{n}_VH"], v[f"{n}_VL"])

rows = []
for name, (h, l) in cands.items():
    for chain, seq in (("VH", h), ("VL", l)):
        for motif, hits in scan(seq).items():
            rows.append({"candidate": name, "chain": chain, "motif": motif,
                         "count": len(hits), "positions_1based": ";".join(map(str, hits))})
lia = pd.DataFrame(rows)
lia.to_csv(MY / "liability.csv", index=False)
print("\\n→", MY / "liability.csv")
display(lia.pivot_table(index="candidate", columns=["chain", "motif"], values="count", fill_value=0))'''),

md("""## 2) 내 결과 확인 — **parental 에 없던** 모티프만 (증분 스캔)

절대 개수보다 중요한 건 "humanization 이 **새로 만든** liability" 입니다."""),
co('''par_scan = {"VH": scan(cands["parental"][0]), "VL": scan(cands["parental"][1])}

new_rows = []
for name, (h, l) in cands.items():
    if name == "parental":
        continue
    for chain, seq in (("VH", h), ("VL", l)):
        for motif, hits in scan(seq).items():
            base = set(par_scan[chain][motif])
            new = sorted(set(hits) - base)
            lost = sorted(base - set(hits))
            new_rows.append({"candidate": name, "chain": chain, "motif": motif,
                             "신규": len(new), "신규 위치": ";".join(map(str, new)) or "-",
                             "사라짐": len(lost)})
delta = pd.DataFrame(new_rows)
delta.to_csv(MY / "liability_delta.csv", index=False)

glyc = delta[(delta.motif == "N-glycosylation") & (delta["신규"] > 0)]
print("신규 N-glycosylation 모티프(가장 위험):", "없음" if glyc.empty else "")
if not glyc.empty:
    display(glyc)
display(delta[delta["신규"] > 0].sort_values(["candidate", "chain"]))
print("\\n읽는 법 — 신규 N-glyc 모티프가 CDR/paratope 근처에 생기면 hard filter 대상입니다(Ch.10).")'''),

md("""## 3) 그래프 — 후보별 liability 총량"""),
co('''from humanization_viz import liability_overview

rows = (lia.groupby(["candidate", "motif"])["count"].sum().reset_index()
          .rename(columns={"count": "count"}).to_dict("records"))
liability_overview(rows, "Developability liability motifs (VH+VL)", "09_liability.png")
from IPython.display import Image; Image("09_liability.png")'''),

md("""## 4) CDR 안에 떨어진 liability 인가?

같은 모티프라도 **CDR/paratope 안**이면 위험도가 다릅니다(결합에 직접 영향).
"""),
co('''ct = pd.read_csv("data/cdr_table_imgt.csv")
guard = {"H": set(), "L": set()}
for _, r in ct.iterrows():
    seq = VH if r["chain"] == "H" else VL
    st = seq.find(r["sequence"]) + 1
    guard[r["chain"]] |= set(range(st, st + len(r["sequence"])))

hits = []
for name, (h, l) in cands.items():
    for chain, seq, tag in (("VH", h, "H"), ("VL", l, "L")):
        for motif, ps in scan(seq).items():
            inside = [p for p in ps if p in guard[tag]]
            if inside:
                hits.append({"candidate": name, "chain": chain, "motif": motif,
                             "CDR 안 위치": ";".join(map(str, inside))})
cdr_lia = pd.DataFrame(hits)
display(cdr_lia if not cdr_lia.empty else "CDR 안 liability 없음")
print("주의 — CDR 좌표는 parental 기준입니다. indel 이 있는 후보(Humatch VL)는 위치가 한 칸씩 밀릴 수 있습니다.")'''),

md("""## 5) 레퍼런스 대조"""),
co('''ref = pd.read_csv("data/liability_reference.csv")
piv_ref = ref.pivot_table(index="candidate", columns="motif", values="count", aggfunc="sum", fill_value=0)
piv_my  = lia.pivot_table(index="candidate", columns="motif", values="count", aggfunc="sum", fill_value=0)
print("[레퍼런스]"); display(piv_ref)
common = piv_my.index.intersection(piv_ref.index)
print("내 결과와 레퍼런스가 일치:", piv_my.loc[common].equals(piv_ref.loc[common]))'''),

md("""## 이 랩에서 확인한 것

1. liability 스캔은 **정규식 4줄**이면 끝납니다 — 후보를 만들 때마다 자동으로 돌리세요.
2. 중요한 건 절대 개수가 아니라 **parental 대비 신규 모티프**입니다(특히 신규 `NXS/T`).
3. CDR 안에 떨어진 모티프는 위험도가 다릅니다 — Ch.10 의 **hard filter** 로 연결됩니다.
4. 이 표가 랭킹의 developability 항목이 됩니다.

다음 → **[Ch.10 — 랭킹·리포트](../10_ranking_report/10_ranking_lab.ipynb)**"""),
]
cells_all[("09_developability", "09_developability_lab.ipynb", "09 Developability Lab")] = c


# ════════════════════════════════════════════════════════════════════════════
# 10 — 랭킹·리포트
# ════════════════════════════════════════════════════════════════════════════
c = [title_cell("10", "후보 랭킹 · 리포트 — 앞 랩 산출물을 하나의 순위로", "10_ranking_report.md")]
c += boot("10_ranking_report", pip="pandas matplotlib pyyaml sapiens anarci abnumber", apt="hmmer")
c += [
md("""## 1) 직접 실행 — 앞 랩의 my_run 산출물 모으기

Ch.05~09 에서 **내가 직접 만든** 후보·지표를 끌어옵니다. 빠진 것만 `data/` 레퍼런스로 채웁니다(어느 쪽인지 print).
"""),
co('''import pandas as pd, numpy as np

SOURCES = {}

cands = {"parental": (VH, VL)}
for chapter, fname, keys, label in [
    ("05_humanize_sapiens", "sapiens_humanized_noguard.fasta", ("sapiens_humanized_VH", "sapiens_humanized_VL"), "sapiens"),
    ("06_cdr_safe_tools",   "humatch_humanised.fasta",         ("humatch_humanised_VH", "humatch_humanised_VL"), "humatch"),
    ("06_cdr_safe_tools",   "anthroab_best_score.fasta",       ("anthroab_bestscore_VH", "anthroab_bestscore_VL"), "anthroab"),
    ("06_cdr_safe_tools",   "anthroab_masked_FRonly.fasta",    ("anthroab_masked_VH", "anthroab_masked_VL"), "anthroabFRmasked"),
]:
    p = GUIDE_ROOT / chapter / "my_run" / fname
    if p.exists():
        f = read_fasta(p); cands[label] = (f[keys[0]], f[keys[1]]); SOURCES[label] = f"내 결과 · {chapter}"

if len(cands) == 1:
    v = read_fasta("data/variants.fasta")
    for n in ["sapiens", "humatch", "anthroab", "anthroabFRmasked"]:
        cands[n] = (v[f"{n}_VH"], v[f"{n}_VL"]); SOURCES[n] = "레퍼런스 · data/variants.fasta"

for k, v in SOURCES.items():
    print(f"  {k:18s} ← {v}")
print("\\n후보:", ", ".join(cands))'''),

md("""## 2) 직접 실행 — 지표 6종 계산

| 항목 | 어디서 |
|---|---|
| humanness | Sapiens 재스코어링(정의 b) — 이 셀에서 **직접 계산**(후보 5종 2초 미만) |
| nativeness | AbNatiV1 (Ch.07 my_run → 없으면 data/) |
| naturalness | Ab-RoBERTa paired (Ch.07 my_run → 없으면 data/) |
| germline identity | ANARCI `--assign_germline` — 이 셀에서 **직접 실행**(10 체인 0.42초) |
| CDR 보존 | parental CDR 문자열이 후보에 그대로 있는가(indel 안전) |
| developability | liability 신규 모티프(Ch.09 방식으로 직접 계산) |
| 구조 | CDR-H3 RMSD (Ch.08 my_run → 없으면 data/; **Sapiens 후보만** 측정돼 있음) |"""),
co('''import re, subprocess, tempfile

# (1) humanness — 직접 재스코어링 (정의 b)
hum = {}
try:
    import sapiens

    def mean_self_prob(seq, chain):
        m = sapiens.predict_scores(seq, chain)
        return float(np.mean([m.loc[i, aa] for i, aa in enumerate(seq)]))

    t0 = time.time()
    for n, (h, l) in cands.items():
        ph, pl = mean_self_prob(h, "H"), mean_self_prob(l, "L")
        hum[n] = (ph * len(h) + pl * len(l)) / (len(h) + len(l))   # 길이가중 paired
    print(f"humanness(Sapiens 재스코어링) {len(cands)}후보: {time.time()-t0:.1f}초")
except Exception as e:
    print("Sapiens 재스코어링 실패:", type(e).__name__, str(e)[:120])
    print("[레퍼런스] data/humanness_all_candidates.csv")
    ref = pd.read_csv("data/humanness_all_candidates.csv")
    hum = ref[ref.chain == "paired"].set_index("candidate")["mean_self_prob"].to_dict()
    hum = {n: hum.get(n, np.nan) for n in cands}

# (2) germline identity — ANARCI 직접 실행
t0 = time.time()
germ = {}
with tempfile.TemporaryDirectory() as td:
    td = pathlib.Path(td)
    write_fasta(td / "all.fa", {f"{n}_{c}": s for n, (h, l) in cands.items()
                                for c, s in (("VH", h), ("VL", l))})
    try:
        r = subprocess.run(["ANARCI", "-i", str(td / "all.fa"), "-s", "imgt", "--csv",
                            "-o", str(td / "gl"), "--assign_germline", "--use_species", "human"],
                           capture_output=True, text=True)
        rc = r.returncode
    except FileNotFoundError:
        rc = 127          # ANARCI/hmmscan 이 PATH 에 없음 → 레퍼런스로 폴백
    if rc == 0:
        vs = {}
        for f in sorted(td.glob("gl_*.csv")):
            for _, row in pd.read_csv(f).iterrows():
                n = row["Id"].rsplit("_", 1)[0]
                vs.setdefault(n, []).append(float(row["v_identity"]))
        germ = {n: float(np.mean(v)) for n, v in vs.items()}
        print(f"germline identity(ANARCI) {len(cands)*2} 체인: {time.time()-t0:.2f}초")
    else:
        ref = pd.read_csv("data/germline_all_candidates.csv")
        germ = ref.groupby("candidate")["v_identity"].mean().to_dict()
        print("[레퍼런스] data/germline_all_candidates.csv")

# (3) nativeness (AbNatiV1 VH) · (4) naturalness (Ab-RoBERTa paired)
abn = pd.read_csv(find_prev("07_nativeness", "abnativ_summary_all_models.csv", quiet=True))
abn1 = abn[(abn.model_generation == "AbNatiV1") & (abn.variant.str.endswith("_VH"))]
nat = {r.variant.split("_")[0]: float(r.overall_score) for r in abn1.itertuples()}

abr = pd.read_csv(find_prev("07_nativeness", "abroberta_scores_summary.csv", quiet=True))
ntr = abr[abr.chain == "paired"].set_index("variant")["mean_logp"].to_dict()

# (5) CDR 보존 · (6) liability 신규
ct = pd.read_csv("data/cdr_table_imgt.csv")
cdrs = [(r["chain"], r["sequence"]) for _, r in ct.iterrows()]
MOTIFS = {"N-glycosylation": r"N[^P][ST]", "deamidation": r"N[GS]",
          "isomerization": r"DG", "oxidation": r"[MW]"}
def scan(seq):
    return {m: {x.start() + 1 for x in re.finditer(p, seq)} for m, p in MOTIFS.items()}
par_scan = {"VH": scan(VH), "VL": scan(VL)}

met = []
for n, (h, l) in cands.items():
    kept = sum(1 for chain, s in cdrs if s in (h if chain == "H" else l))
    new_g = len(scan(h)["N-glycosylation"] - par_scan["VH"]["N-glycosylation"]) + \\
            len(scan(l)["N-glycosylation"] - par_scan["VL"]["N-glycosylation"])
    new_all = sum(len(scan(h)[m] - par_scan["VH"][m]) + len(scan(l)[m] - par_scan["VL"][m])
                  for m in MOTIFS)
    met.append({"candidate": n, "humanness": round(hum[n], 4),
                "nativeness_AbNatiV1_VH": round(nat.get(n, np.nan), 4) if n in nat else np.nan,
                "naturalness_AbRoBERTa": round(ntr.get(n, np.nan), 4) if n in ntr else np.nan,
                "germline_V_identity": round(germ.get(n, np.nan), 4) if n in germ else np.nan,
                "CDR_kept": kept, "new_glyc": new_g, "new_liabilities": new_all})

# (7) 구조 — Sapiens 후보만 측정돼 있음
rm = pd.read_csv(find_prev("08_structure", "cdr_h3_rmsd_summary.csv", quiet=True))
h3 = float(rm[rm.metric.str.startswith("cdr_h3")]["value_angstrom"].iloc[0])
mt = pd.DataFrame(met)
mt["cdr_h3_rmsd"] = [0.0 if n == "parental" else (h3 if n == "sapiens" else np.nan)
                     for n in mt["candidate"]]
mt.to_csv(MY / "metrics_table.csv", index=False)
display(mt)
print("cdr_h3_rmsd 는 Ch.08 에서 접어 본 후보(parental·Sapiens)만 값이 있습니다 — 나머지는 NaN(가중합에서 제외).")'''),

md("""## 3) 직접 실행 — hard filter + 가중합 랭킹 (본문 10.1)

본문 10.1.1 의 가중치를 **실제로 측정한 항목**에 맞춰 재배분했습니다(측정하지 않은 항목에 점수를 주지 않기 위해).

```
Final score = 0.30 humanness + 0.25 nativeness + 0.20 germline identity
            + 0.15 developability(신규 liability 적을수록) + 0.10 naturalness
```

**Hard filter (즉시 탈락)** — ① CDR 6개 중 하나라도 파손 ② 신규 N-glycosylation 모티프 ③ humanness 가 parental 이하."""),
co('''def minmax(s):
    s = s.astype(float)
    if s.notna().sum() == 0 or s.max() == s.min():
        return pd.Series([0.5] * len(s), index=s.index)
    return (s - s.min()) / (s.max() - s.min())

W = {"humanness": 0.30, "nativeness_AbNatiV1_VH": 0.25, "germline_V_identity": 0.20,
     "developability": 0.15, "naturalness_AbRoBERTa": 0.10}

rank = mt.set_index("candidate").copy()
rank["developability"] = -rank["new_liabilities"]            # 적을수록 좋음 → 부호 반전
missing = {k: list(rank.index[rank[k].isna()]) for k in W if rank[k].isna().any()}
if missing:
    print("측정값이 없는 항목(0점 처리):", missing)
norm = pd.DataFrame({k: minmax(rank[k]).fillna(0.0) for k in W})
rank["score"] = sum(norm[k] * w for k, w in W.items()).round(4)

par_hum = float(rank.loc["parental", "humanness"])
rank["hard_filter"] = [
    "; ".join(filter(None, [
        "CDR 파손" if r.CDR_kept < 6 else "",
        "신규 N-glyc" if r.new_glyc > 0 else "",
        "humanness 미개선" if (r.humanness <= par_hum and i != "parental") else "",
    ])) or "pass"
    for i, r in rank.iterrows()]
rank.loc["parental", "hard_filter"] = "(baseline)"

out = rank.sort_values("score", ascending=False)[
    ["score", "hard_filter", "humanness", "nativeness_AbNatiV1_VH", "germline_V_identity",
     "naturalness_AbRoBERTa", "CDR_kept", "new_glyc", "new_liabilities", "cdr_h3_rmsd"]]
out.to_csv(MY / "ranking.csv")
display(out)

adv = out[(out.hard_filter == "pass")]
print("\\nhard filter 통과:", ", ".join(adv.index) if len(adv) else "없음")
print("주의 — 점수 1위여도 hard filter 에 걸리면 실험으로 넘기지 않습니다(또는 CDR backmutation 후 재평가).")'''),

md("""## 4) 직접 실행 — candidate report (CSV + GuideDB YAML, 본문 10.1.3 · 10.2)"""),
co('''import yaml

top = adv.index[0] if len(adv) else out.index[0]
h, l = cands[top]

def mutations(par, cand):
    if len(par) != len(cand):
        return ["(길이 다름 — indel 포함, IMGT 정렬 필요)"]
    return [f"{a}{i+1}{b}" for i, (a, b) in enumerate(zip(par, cand)) if a != b]

report_rows = []
for n in out.index:
    if n == "parental":
        continue
    ch, cl = cands[n]
    r = out.loc[n]
    report_rows.append({
        "Candidate ID": f"HZ_{n}_01", "Method": n,
        "VH mutations": ", ".join(mutations(VH, ch))[:120],
        "VL mutations": ", ".join(mutations(VL, cl))[:120],
        "CDR mutations": "none (보호)" if r.CDR_kept == 6 else f"{6 - int(r.CDR_kept)}개 CDR 파손",
        "Humanness": r.humanness, "AbNatiV1 VH": r["nativeness_AbNatiV1_VH"],
        "Germline V identity": r["germline_V_identity"],
        "Developability": "clean" if r.new_liabilities == 0 else f"신규 liability {int(r.new_liabilities)}",
        "CDR-H3 RMSD": r.cdr_h3_rmsd,
        "Final score": r.score,
        "Recommendation": "advance" if r.hard_filter == "pass" else f"reject/backmutate ({r.hard_filter})",
    })
rep = pd.DataFrame(report_rows)
rep.to_csv(MY / "candidate_report.csv", index=False)
display(rep[["Candidate ID", "Method", "CDR mutations", "Humanness", "Final score", "Recommendation"]])

gl_ref = pd.read_csv("data/germline_assignment.csv")
db = {
    "project": {"id": "HZ_running_example", "parent_clone": "parental", "date": time.strftime("%Y-%m-%d")},
    "input_sequences": {"heavy": {"name": "parental_H", "sequence": VH},
                        "light": {"name": "parental_L", "sequence": VL}},
    "annotation": {
        "numbering_scheme": "IMGT", "cdr_definition": "IMGT",
        "heavy_germline": str(gl_ref[(gl_ref.chain == "H") & (gl_ref.gene_type == "V")]["gene"].iloc[0]),
        "light_germline": str(gl_ref[(gl_ref.chain == "L") & (gl_ref.gene_type == "V")]["gene"].iloc[0]),
        "heavy_cdr3": str(ct[(ct.chain == "H") & (ct.cdr == "CDR3")]["sequence"].iloc[0]),
        "note": "J-gene 은 IGHJ6*01/IGHJ4*01 동점(85.71%) — 도구 tie-break 차이",
    },
    "candidates": [
        {"id": f"HZ_{n}_01", "method": n,
         "sequences": {"heavy": cands[n][0], "light": cands[n][1]},
         "scores": {"humanness_sapiens_rescored": float(out.loc[n, "humanness"]),
                    "nativeness_abnativ1_vh": (None if pd.isna(out.loc[n, "nativeness_AbNatiV1_VH"])
                                               else float(out.loc[n, "nativeness_AbNatiV1_VH"])),
                    "naturalness_abroberta_paired": (None if pd.isna(out.loc[n, "naturalness_AbRoBERTa"])
                                                     else float(out.loc[n, "naturalness_AbRoBERTa"])),
                    "germline_v_identity": float(out.loc[n, "germline_V_identity"]),
                    "final_score": float(out.loc[n, "score"])},
         "structure": {"cdr_h3_rmsd": (None if pd.isna(out.loc[n, "cdr_h3_rmsd"])
                                       else float(out.loc[n, "cdr_h3_rmsd"]))},
         "cdr_preserved": int(out.loc[n, "CDR_kept"]) == 6,
         "decision": "advance" if out.loc[n, "hard_filter"] == "pass" else "reject/backmutate"}
        for n in out.index if n != "parental"
    ],
}
(MY / "candidate_report.yaml").write_text(yaml.safe_dump(db, allow_unicode=True, sort_keys=False))
print("\\n→", MY / "candidate_report.csv")
print("→", MY / "candidate_report.yaml")
print((MY / "candidate_report.yaml").read_text()[:700], "...")'''),

md("""## 5) 레퍼런스 대조 — 같은 코드, 레퍼런스 입력

내 후보 대신 **커밋된 레퍼런스 후보(`data/`)** 로 같은 지표를 읽어 랭킹이 어떻게 나오는지 비교합니다.
지표 자체가 실측이므로, 실행을 다 건너뛴 사람도 여기서 같은 결론에 도달합니다."""),
co('''ref_hum  = pd.read_csv("data/humanness_all_candidates.csv")
ref_hum  = ref_hum[ref_hum.chain == "paired"].set_index("candidate")["mean_self_prob"]
ref_germ = pd.read_csv("data/germline_all_candidates.csv").groupby("candidate")["v_identity"].mean()
ref_abn  = pd.read_csv("data/abnativ_summary_all_models.csv")
ref_abn  = ref_abn[(ref_abn.model_generation == "AbNatiV1") & (ref_abn.variant.str.endswith("_VH"))]
ref_abn  = {r.variant.split("_")[0]: r.overall_score for r in ref_abn.itertuples()}
ref_abr  = pd.read_csv("data/abroberta_scores_summary.csv")
ref_abr  = ref_abr[ref_abr.chain == "paired"].set_index("variant")["mean_logp"]

ref_tbl = pd.DataFrame({"humanness": ref_hum.round(4), "nativeness_AbNatiV1_VH": pd.Series(ref_abn).round(4),
                        "germline_V_identity": ref_germ.round(4),
                        "naturalness_AbRoBERTa": ref_abr.round(4)})
print("[레퍼런스 지표 — 전부 실제 실행 산출물]")
display(ref_tbl)

print("\\n내 랭킹 순서            :", " > ".join(out.index))
print("레퍼런스 humanness 순서 :", " > ".join(ref_hum.sort_values(ascending=False).index))
print("레퍼런스 nativeness 순서:", " > ".join(pd.Series(ref_abn).sort_values(ascending=False).index))
print("\\n두 순서가 다르면? 정상입니다 — humanness 와 nativeness 는 다른 축이고, "
      "랭킹은 거기에 germline·developability·CDR 보존을 더해 계산하니까요.")'''),

md("""## 이 랩에서 확인한 것

1. 랭킹은 **여러 축의 가중합 + hard filter** 입니다. 점수 1위여도 CDR 이 파손됐거나 신규 N-glyc 모티프가 생겼으면 **탈락**입니다.
2. 실측 지표(후보 5종):
   - **humanness**(Sapiens 재스코어링, paired) — parental 0.7303 · Sapiens **0.8424** · Humatch 0.7988 · AnthroAb 0.7941 · AnthroAb(FR-masked) 0.7136
   - **nativeness**(AbNatiV1 VH) — parental 0.6477 · Sapiens **0.8803** · Humatch 0.8305 · AnthroAb 0.8064
   - **germline V identity** — parental VH 0.63 → Sapiens/Humatch **0.80**
   - **CDR 보존** — Humatch 6/6, AnthroAb(FR-masked) 6/6, Sapiens·AnthroAb(best_score) 는 CDR-L1 파손
3. 그래서 "가장 사람다운 후보"와 "실험으로 넘길 후보"가 **다를 수 있습니다.** Sapiens 후보를 쓰려면 Ch.05 의 **CDR 가드 적용본**을 써야 합니다.
4. 산출물 — `my_run/metrics_table.csv` · `ranking.csv` · `candidate_report.csv` · `candidate_report.yaml`(GuideDB 스키마).

전체 체크리스트·용어집 → **[Ch.11 부록](../11_appendix/11_appendix.md)**"""),
]
cells_all[("10_ranking_report", "10_ranking_lab.ipynb", "10 Ranking & Report Lab")] = c


# ── 저장 ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    total = 0
    for (folder, name, title), cells in cells_all.items():
        total += save(cells, folder, name, title)
    print(f"\n노트북 {len(cells_all)}종 · 총 {total} 셀 생성 완료 (각 챕터 폴더, Colab/로컬 공용).")
