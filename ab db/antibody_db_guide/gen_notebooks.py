#!/usr/bin/env python3
"""
gen_notebooks.py — 각 챕터의 실습 노트북(.ipynb)을 생성해요.
(BoltzGen 튜토리얼의 gen_notebooks.py 에 대응)

**노트북은 직접 손대지 말고 이 파일을 고친 뒤 `python gen_notebooks.py` 로 재생성하세요.**

설계 원칙 — 모든 실습은 "직접 생성"이 기본값이에요.
  각 절은 3단계로 짝지어져 있어요.
    1) 직접 실행    — 도구를 진짜로 돌려 결과를 `my_run/` 에 만든다
    2) 내 결과 확인 — 방금 만든 산출물을 읽어 표·그래프로 본다
    3) 레퍼런스 대조 — 저장소에 커밋된 `data/`(대조군)와 비교해 내 결과가 맞는지 확인한다
  어떤 단계를 건너뛰거나 실패해도 `resolve()` 가 `my_run/` → `data/` 순으로 폴백해서
  뒤 절이 계속 돌아가요(어느 쪽을 쓰는지 항상 출력됩니다).

실행: python gen_notebooks.py   (repo 루트에서)
"""
import json
import pathlib

ROOT = pathlib.Path(__file__).parent

# 전 셀 실행 시간 — `jupyter nbconvert --to notebook --execute` 로 **실제 측정**한 값만 적어요.
# (pip 전용 venv, CPU, 콜드 캐시 기준. 측정 환경 상세는 10_appendix 의 재현 환경 표)
# 본문(.md)의 실습 콜아웃 배지와 이 표는 항상 같은 값을 써야 해요.
RUNTIME = {
    "02_databases": "6초",
    "03_setup": "3초",
    "04_numbering": "9초",
    "05_humanness": "16초",
    "06_structure": "16초",
    "07_interface": "10초",
    "08_developability": "3초",
    "09_repertoire": "8초",
}


# ---- 셀 헬퍼 ---------------------------------------------------------------
def md(text):
    return {"cell_type": "markdown", "metadata": {}, "source": text.splitlines(keepends=True)}


def code(text):
    return {"cell_type": "code", "metadata": {}, "execution_count": None,
            "outputs": [], "source": text.splitlines(keepends=True)}


BOOTSTRAP = '''# ====== Colab/로컬 공용 부트스트랩 (모든 챕터 공통) ======
REPO_URL = "https://github.com/CONNECTS-SCV/bio-guides.git"   # 이 가이드 저장소 (fork 했다면 본인 주소로 바꾸세요)
CLONE_AS = "bio-guides"
CHAPTER  = "@CHAPTER@"
PIP_PKGS = "@PIP@"          # 이 챕터가 실제로 돌리는 도구 (pip 이름)
NEED_HMMER = @HMMERFLAG@    # ANARCI 계열은 hmmscan(HMMER) 실행파일이 필요해요 (pip 로는 안 깔려요)

import os, sys, subprocess, pathlib, shutil, importlib.util
IN_COLAB = "google.colab" in sys.modules
@HF@
def _run(cmd, quiet=False):
    """quiet=True 면 출력을 삼키고 **실패했을 때만** 보여줘요.
    apt-get 은 "(Reading database ... 5%(Reading database ... 10%" 같은 진행률을 600자 넘게 쏟아내는데,
    그게 노트북을 연 학습자가 보는 첫 화면을 덮어버려서 실패로 오해하게 만들거든요."""
    print("$", cmd)
    if not quiet:
        subprocess.run(cmd, shell=True, check=True); return
    p = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if p.returncode != 0:
        print((p.stdout or "") + (p.stderr or ""))
        raise subprocess.CalledProcessError(p.returncode, cmd)

_MARK = "antibody_viz.py"           # 이 파일이 있는 폴더가 가이드 루트

def _find_root():
    """가이드 루트를 찾습니다."""
    cwd = pathlib.Path.cwd()
    for base in (cwd, *list(cwd.parents)[:3]):
        if (base / _MARK).exists():
            return base
    # 클론 직후엔 cwd 아래만 깊이 3까지 — 위로 올라가 rglob 하면 Colab 에서 / 전체를 뒤집니다.
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
assert ROOT is not None, "repo 루트를 못 찾았습니다. 로컬이면 이 노트북을 챕터 폴더 안에서 여세요."

ADV_ROOT = ROOT.resolve()
os.chdir(ADV_ROOT / CHAPTER)        # 챕터 폴더로 이동 → data/·my_run/ 상대경로 동작
sys.path.insert(0, str(ADV_ROOT))   # antibody_viz import 보장
PY, SCRIPTS = sys.executable, ADV_ROOT / "scripts"

# --- 의존성 설치 -----------------------------------------------------------
_IMPORT = {"biopython": "Bio", "pyyaml": "yaml"}          # pip 이름 ≠ import 이름
def _have(pkg):
    mod = _IMPORT.get(pkg, pkg.split("==")[0])
    try:
        return importlib.util.find_spec(mod) is not None
    except Exception:
        return False
_APT = []                                # 필요한 시스템 패키지를 모아 apt 를 한 번만 돌립니다
@HMMER@
_miss = [p for p in PIP_PKGS.split() if not _have(p)]
if _miss:
    _run(f'"{sys.executable}" -m pip -q install ' + " ".join(_miss))
@IGFOLD@@FONT@
if _APT:
    _run("apt-get -qq update", quiet=True)   # 인덱스가 낡으면 install 이 404 로 죽습니다
    _run("DEBIAN_FRONTEND=noninteractive apt-get -qq install -y " + " ".join(_APT), quiet=True)
@PIN@BLOCK
# --- 내 산출물 폴더 & 폴백 규칙 --------------------------------------------
MYRUN = pathlib.Path("my_run"); MYRUN.mkdir(exist_ok=True)

QUIET_WARNINGS = True   # 라이브러리 내부 경고 소음을 끕니다. 다 보고 싶으면 False 로 두세요

def run_tool(args, timeout=1800):
    """도구를 서브프로세스로 실제 실행하고 출력을 셀에 그대로 보여줘요.

    igfold·biopython·transformers 는 **자기 패키지 소스 줄번호**가 찍힌
    DeprecationWarning/FutureWarning 을 실제 결과보다 길게 쏟아내요. 그게 성공 메시지를
    덮어버려 실패로 오해하게 만들어서, 기본으로 PYTHONWARNINGS=ignore 를 걸어 둡니다.
    도구가 직접 print 하는 안내·에러는 그대로 남아요(warnings 모듈만 막는 거예요)."""
    args = [str(a) for a in args]
    # 절대경로를 그대로 찍으면 한 줄이 화면을 넘겨 정작 중요한 옵션이 안 보여요.
    # /usr/bin/python3 → python, /…/scripts/x.py → scripts/x.py 로 줄여서 보여줍니다.
    def _short(s):
        if s == PY:
            return "python"
        return "scripts/" + s[len(str(SCRIPTS)) + 1:] if s.startswith(str(SCRIPTS) + os.sep) else s
    print("$", " ".join(_short(a) for a in args))
    env = {**os.environ, "PYTHONWARNINGS": "ignore"} if QUIET_WARNINGS else None
    try:
        p = subprocess.run(args, capture_output=True, text=True, timeout=timeout, env=env)
    except Exception as e:
        print(f"[실행 실패] {type(e).__name__}: {e}\\n→ 이 단계는 건너뛰고 레퍼런스(data/)로 이어갑니다")
        return False
    out = ((p.stdout or "") + (p.stderr or "")).strip()
    print(out[-3000:] if out else "(출력 없음)")
    if p.returncode != 0:
        print(f"[실패] returncode={p.returncode} → 이 단계는 건너뛰고 레퍼런스(data/)로 이어갑니다")
    return p.returncode == 0

def resolve(name):
    """내가 방금 만든 my_run/ 결과를 우선 쓰고, 없으면 커밋된 data/ 로 폴백."""
    mine, ref = MYRUN/name, pathlib.Path("data")/name
    if mine.exists():
        print(f"[내 결과]   {mine}")
        return str(mine)
    print(f"[레퍼런스] {ref}   ← my_run 산출물이 없어 커밋본으로 이어갑니다")
    return str(ref)

print("작업 폴더 :", pathlib.Path.cwd(), "| Colab:", IN_COLAB)'''


# 선택 블록 — 그 챕터가 실제로 쓰는 것만 노트북에 실린다(안 쓰는 도구 안내가 안 보이도록).
_HF_BLOCK = '''
# HF 가중치 다운로드가 멈추면 예외가 안 나 폴백이 안 걸려요 — 타임아웃으로 '실패'를 만들어 data/ 로 잇습니다.
os.environ.setdefault("HF_HUB_DOWNLOAD_TIMEOUT", "30")   # 스트림 30초 무응답 → 끊고 재시도
os.environ.setdefault("HF_HUB_ETAG_TIMEOUT", "15")
'''
_HMMER_BLOCK = '''
if shutil.which("hmmscan") is None:      # ANARCI 가 부르는 실행파일 — pip 로는 안 깔려요
    if IN_COLAB:
        _APT.append("hmmer")
    else:
        print("[!] hmmscan 이 없어요 → conda install -c bioconda hmmer  (또는 apt install hmmer)")
'''
_IGFOLD_BLOCK = '''
if importlib.util.find_spec("pkg_resources") is None:
    # setuptools 81+(2026-02) 이 pkg_resources 를 없앴는데 IgFold 의존성이 이걸 import 해요.
    _run(f'"{sys.executable}" -m pip -q install "setuptools<81"')
    importlib.invalidate_caches()
'''
_FONT_BLOCK = '''
import glob as _glob
if IN_COLAB and not _glob.glob("/usr/share/fonts/**/*Nanum*", recursive=True):
    _APT.append("fonts-nanum")           # Colab 엔 한글 폰트가 없어 라벨이 □ 로 깨집니다
'''
_PIN_BLOCK = '''
# IgFold 체크포인트에는 옛 transformers 의 토크나이저가 pickle 돼 있어, 5.x 로는 unpickle 이 실패해요.
_ver = subprocess.run([sys.executable, "-c", "import transformers;print(transformers.__version__)"],
                      capture_output=True, text=True).stdout.strip()
if not _ver.startswith("4."):
    print(f"[transformers {_ver or 'none'} → @PINVER@] IgFold 호환 버전으로 맞춥니다")
    _run(f'"{sys.executable}" -m pip -q install "transformers==@PINVER@"')
'''

def bootstrap(chapter, pip_pkgs="pandas matplotlib", hmmer=False, pin_transformers=None,
              needs_hf=False, needs_plot=None):
    """그 챕터에 필요한 블록만 골라 부트스트랩 셀을 만든다."""
    if needs_plot is None:
        needs_plot = "matplotlib" in pip_pkgs
    pin = _PIN_BLOCK.replace("@PINVER@", str(pin_transformers)) if pin_transformers else ""
    return code(BOOTSTRAP
                .replace("@CHAPTER@", chapter)
                .replace("@PIP@", pip_pkgs)
                .replace("@HMMERFLAG@", "True" if hmmer else "False")
                .replace("@HF@", _HF_BLOCK if needs_hf else "")
                .replace("@HMMER@", _HMMER_BLOCK if hmmer else "")
                .replace("@IGFOLD@", _IGFOLD_BLOCK if "igfold" in pip_pkgs else "")
                .replace("@FONT@", _FONT_BLOCK if needs_plot else "")
                .replace("@PIN@BLOCK", pin))


def header(chapter_dir, chapter_md, title, what, prev=None):
    # 앞 챕터 my_run 을 물려받는 노트북은 도입부에서 먼저 밝힌다 — 중간부터 들어온
    # 학습자가 자기도 모르게 커밋된 data/ 로 폴백된 채 진행하지 않도록.
    link = f"> **앞 랩에서 이어져요** — {prev} 의 `my_run/` 을 먼저 찾고, 없으면 커밋된 `data/` 로 대신합니다.\n" if prev else ""
    return [md(f'''# {title}

> 본문: [`{chapter_md}`]({chapter_md}) 와 **한 절씩 짝지어** 보세요.
> **전 셀 실행 {RUNTIME[chapter_dir]}** (실측 — 도구가 도는 시간만. clone·pip·apt 설치 시간은 빼고 잰 값이에요)
> 코랩 무료 런타임은 코어가 2개뿐이라 설치에 1~2분, 무거운 예측 단계는 몇 배까지 더 걸릴 수 있어요 — 정상입니다.
{link}
**이 노트북은 도구를 직접 돌립니다.** {what}
내 결과는 `my_run/` 에 쌓이고 커밋된 `data/` 는 대조군이에요 — 어느 단계가 실패해도 `resolve()` 가 `data/` 로 폴백해 뒤 절이 계속 돌아갑니다.'''),
            md('''## 0) 부트스트랩 — 저장소 클론 · 도구 설치 · 작업 폴더 이동

Colab 은 이 셀 하나로 끝나고, 로컬은 챕터 폴더 안에서 열었다면 클론 없이 진행됩니다.''')]



# ── Colab 배지 ────────────────────────────────────────────────────────────────
# GitHub 에서 노트북을 열면 이 배지를 눌러 바로 Colab 으로 넘어갈 수 있다.
COLAB_REPO   = "CONNECTS-SCV/bio-guides"
GUIDE_PREFIX = "ab db/antibody_db_guide"          # 저장소 루트 기준 이 가이드의 경로

def colab_badge_cell(rel_path):
    url = f"https://colab.research.google.com/github/{COLAB_REPO}/blob/main/{GUIDE_PREFIX}/{rel_path}".replace(" ", "%20")
    return {"cell_type": "markdown", "metadata": {},
            "source": [f"[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)]({url})\n"]}


def write_nb(path, cells):
    cells = [colab_badge_cell(str(path.relative_to(ROOT)))] + cells
    nb = {"cells": cells,
          "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python",
                                      "name": "python3"},
                       "language_info": {"name": "python"}},
          "nbformat": 4, "nbformat_minor": 5}
    path.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
    print("wrote", path.relative_to(ROOT))


# ===========================================================================
# 02 — DB explore : RCSB 에서 항체-항원 복합체 스냅샷을 직접 조회
# ===========================================================================
def nb_02():
    c = header("02_databases", "02_databases.md", "02 — 항체 DB landscape (RCSB 스냅샷 직접 조회)",
               "RCSB Search/Data API 로 항체–항원 복합체 스냅샷을 **직접 만들어** `my_run/` 에 저장해요.")
    c += [bootstrap("02_databases", pip_pkgs="pandas requests"),
          md('''## 1) 먼저 지도 — DB 성격별 분류와 확인 필드 (본문 2.1~2.6)

항체 DB 는 성격이 제각각이라 "어디서 무엇을 가져오나"부터 정해야 해요. 성격으로 나눈 여섯 유형을
세워 두고, 그중 **구조 DB** 축을 2절에서 직접 뽑아 봅니다. 아래 표의 여섯 줄이 본문 2.2~2.6 을
한 눈에 접은 것이라, 뒤 챕터에서 어느 DB 를 다시 만나는지도 마지막 열로 확인할 수 있어요.

구조 DB 를 볼 때 확인해야 할 필드 목록(본문 2.2)도 같이 만들어 둬요 — 3절에서 이 목록이
RCSB 스냅샷으로 **몇 개나 채워지는지** 세어 볼 거예요.'''),
          code('''import pandas as pd

dbs = pd.DataFrame([
    ["구조 DB",             "SAbDab / SAbDab-nano / IMGT-3Dstructure-DB", "항체 구조·항원-항체 복합체", "구조 비교·epitope/paratope", "Ch.06·07"],
    ["서열 repertoire DB",  "OAS / AIRR Data Commons / iReceptor",        "BCR·항체 대량 서열",        "naturalness·germline",      "Ch.09"],
    ["치료용 항체 DB",       "Thera-SAbDab",                              "임상·승인 항체 서열·메타",   "benchmark·developability",  "Ch.05"],
    ["질병·항원 특화 DB",    "CoV-AbDab / IEDB",                          "항원 특이 항체·epitope",     "중화항체·epitope 분석",      "Ch.07"],
    ["affinity/mutation DB","AB-Bind / SKEMPI 2.0",                      "mutation별 binding 변화",   "affinity maturation·ΔΔG",   "-"],
    ["통합 분석 시스템",     "abYsis",                                    "sequence/structure annotation", "항체-aware annotation", "-"],
], columns=["DB 유형", "대표 DB", "주요 데이터", "주 용도", "이 과정에서"])
display(dbs)

# 본문 2.2 의 SAbDab 확인 필드 → 이 스냅샷의 어느 컬럼이 그 역할을 하는지(없으면 None)
SABDAB_FIELDS = {
    "PDB ID":               "pdb_id",
    "heavy/light chain ID": "heavy_chains",
    "antigen chain ID":     "antigen_chains",
    "resolution":           "resolution_A",
    "antigen type":         "antigen_name",
    "antibody species":     None,
    "affinity value":       None,
    "bound/unbound":        None,
    "CDR sequence/length":  None,
}
print(f"\\n구조 DB 에서 확인할 필드 {len(SABDAB_FIELDS)}개 —", " · ".join(SABDAB_FIELDS))
print(f"판정 — {len(dbs)}개 유형 중 다음 절에서 직접 뽑는 것은 첫 줄의 구조 DB 축이에요.")'''),
          md('''## 2) 직접 실행 — RCSB 에서 항체-항원 복합체 스냅샷 만들기 (본문 2.2b)

SAbDab·Thera-SAbDab 웹 UI 는 스크립트로 바로 긁기 어려워요(JS 렌더링 앱이라 HTML 만 돌아옵니다).
그래서 **같은 원본인 PDB** 를 RCSB **Search API + Data API** 로 직접 조회해 "SAbDab스러운" 요약 표를 만듭니다.

```bash
python scripts/fetch_rcsb_ab_snapshot.py --rows 12 --out my_run/rcsb_ab_complexes.csv
```
- 검색 조건 — X-ray · 해상도 ≤ 2.5 Å · 단백질 entity ≥ 3 · full-text `"Fab antibody complex"`
- 정렬 — **release date 오름차순**(오래된 entry부터) → 시간이 지나도 목록이 잘 안 흔들려요
- 사슬 역할 파생 — entity 설명(`pdbx_description`)에 `HEAVY`/`LIGHT` 가 있으면 그대로,
  없으면(`"FAB NC10"` 같은 이름) 사슬 ID 가 `H*`/`L*` 인지로 추정하고,
  그것도 안 되면 **`ab_other_chains`**(= 항체는 맞는데 역할 미분류) 에 남깁니다'''),
          code('''import pathlib

run_tool([PY, SCRIPTS/"fetch_rcsb_ab_snapshot.py",
          "--rows", "12", "--out", "my_run/rcsb_ab_complexes.csv"])

snap_p = pathlib.Path("my_run/rcsb_ab_complexes.csv")
print("\\n판정 —", f"스냅샷 생성 완료 ({snap_p})" if snap_p.exists()
      else "스냅샷을 못 만들었어요(네트워크 차단 등) → 아래 절은 커밋된 data/ 로 이어갑니다")'''),
          md('''## 3) 내 결과 확인 — 스냅샷 검수 (본문 2.2b)

받아온 표를 그대로 믿으면 안 돼요. **사슬 ID·역할·항원 정체**를 코드로 훑어 손볼 곳을 골라냅니다.
본문이 말한 함정 세 가지가 이 12건 안에 실제로 들어 있어요.'''),
          code('''import pandas as pd
from collections import defaultdict

snap = pd.read_csv(resolve("rcsb_ab_complexes.csv"))

WANT = ["pdb_id", "released", "resolution_A", "heavy_chains", "light_chains",
        "ab_other_chains", "antigen_chains", "antigen_name"]
S = snap.reindex(columns=WANT).copy()          # 없는 컬럼이 있어도 죽지 않게
for col in S.columns:
    if col != "resolution_A":
        S[col] = S[col].fillna("").astype(str)
display(S)

if S["resolution_A"].notna().any():
    r = S["resolution_A"].dropna()
    print("entry %d건 | 해상도(Å) 평균 %.2f · 최고 %.2f · 최저 %.2f | 공개일 %s ~ %s"
          % (len(S), r.mean(), r.min(), r.max(), S.released.min(), S.released.max()))

def ids(v):
    return [x for x in str(v).split(";") if x]

# 함정 ① 항체 사슬 ID 는 규칙이 아니라 관례
odd = S[(S.heavy_chains != "H") | (S.light_chains != "L")]
print("\\n① H/L 관례를 안 따르는 entry:",
      ", ".join(f"{t.pdb_id}(H={t.heavy_chains or '-'}, L={t.light_chains or '-'})"
                for t in odd.itertuples()) or "없음")

# 함정 ② 항체인 건 확실한데 heavy/light 로 역할을 못 가른 사슬
unassigned = S[S.ab_other_chains != ""]
print("② 역할 미분류 항체 사슬(ab_other_chains)을 가진 entry:",
      ", ".join(f"{t.pdb_id}({t.ab_other_chains})" for t in unassigned.itertuples()) or "없음")

roles = defaultdict(lambda: defaultdict(list))
for t in S.itertuples():
    for ch in ids(t.heavy_chains):    roles[ch]["항체 heavy"].append(t.pdb_id)
    for ch in ids(t.light_chains):    roles[ch]["항체 light"].append(t.pdb_id)
    for ch in ids(t.ab_other_chains): roles[ch]["항체 역할 미분류"].append(t.pdb_id)
    for ch in ids(t.antigen_chains):  roles[ch]["항원"].append(t.pdb_id)
dual = {k: v for k, v in roles.items() if len(v) > 1}
print(f"   사슬 문자 {len(roles)}개 중 {len(dual)}개가 entry 마다 역할이 달라요.")
for ch in sorted(dual):
    print(f"     '{ch}' — " + " / ".join(f"{role} " + "·".join(sorted(set(e)))
                                         for role, e in dual[ch].items()))

# 함정 ③ full-text 검색이 물어온 노이즈
noise = S[S.antigen_name.str.upper().str.contains("T-CELL|T CELL|RECEPTOR", regex=True)]
print("③ 항원 자리에 항체가 아닌 면역수용체가 앉은 entry:",
      ", ".join(f"{t.pdb_id}({t.antigen_name})" for t in noise.itertuples()) or "없음")

review = sorted(set(odd.pdb_id) | set(unassigned.pdb_id) | set(noise.pdb_id))
print(f"\\n판정 — 눈으로 검수해야 할 entry {len(review)}/{len(S)}건 ({100*len(review)/len(S):.0f}%) — "
      + (", ".join(review) or "없음"))
print("      0건이면 그대로 써도 되고, 1건이라도 있으면 chain ID 와 항원 정체를 직접 확인해야 해요.")

have = [f for f, colname in SABDAB_FIELDS.items() if colname and colname in snap.columns]
gap  = [f for f in SABDAB_FIELDS if f not in have]
print(f"\\n1절 필드 {len(SABDAB_FIELDS)}개 중 이 스냅샷이 채우는 것 {len(have)}개 — {', '.join(have)}")
print(f"      못 채우는 {len(gap)}개 — {', '.join(gap)}")
print("      이 빈칸이 바로 SAbDab 같은 항체 전용 annotation DB 가 따로 존재하는 이유예요.")'''),
          md('''## 4) 레퍼런스 대조 — 커밋된 스냅샷과 비교 (본문 2.2b)

`data/rcsb_ab_complexes.csv` 는 **2026-07-14 에 같은 스크립트로 받아 커밋한 대조군**이에요.
PDB 는 매주 자라니까 내 결과와 100% 같지 않을 수 있어요 — 그 차이 자체가 "DB 는 살아 있다"는 관찰입니다.'''),
          code('''import pandas as pd, pathlib

ref_p, mine_p = pathlib.Path("data/rcsb_ab_complexes.csv"), pathlib.Path("my_run/rcsb_ab_complexes.csv")
if not mine_p.exists():
    print("my_run 스냅샷이 없어 대조를 건너뜁니다 — 위 3절 표는 커밋된 레퍼런스예요.")
elif not ref_p.exists():
    print("레퍼런스가 없어 대조를 건너뜁니다:", ref_p)
else:
    mine, ref = pd.read_csv(mine_p), pd.read_csv(ref_p)
    a, b = set(mine.pdb_id), set(ref.pdb_id)
    print(f"내 결과 {len(a)}개 · 레퍼런스 {len(b)}개 · 공통 {len(a & b)}개")
    print("  내 결과에만 — " + (" · ".join(sorted(a - b)) or "없음"))
    print("  레퍼런스에만 — " + (" · ".join(sorted(b - a)) or "없음"))

    key = [c for c in ["resolution_A", "heavy_chains", "light_chains",
                       "ab_other_chains", "antigen_chains"] if c in mine.columns and c in ref.columns]
    both = mine.merge(ref, on="pdb_id", suffixes=("_mine", "_ref"))
    drift = {c: both.loc[both[f"{c}_mine"].astype(str) != both[f"{c}_ref"].astype(str), "pdb_id"].tolist()
             for c in key}
    drift = {c: v for c, v in drift.items() if v}
    if drift:
        print(f"\\n공통 {len(a & b)}건 중 값이 달라진 컬럼")
        display(pd.DataFrame([
            {"컬럼": c, "달라진 entry": f"{len(v)}건",
             "어느 entry 인가": " · ".join(v[:8]) + (f" … 외 {len(v) - 8}개" if len(v) > 8 else "")}
            for c, v in drift.items()]))
    else:
        print(f"  공통 entry 는 {len(key)}개 컬럼이 전부 같아요 (완전 일치).")

    print(f"\\n판정 — 공통 {len(a & b)}건의 {len(key)}개 컬럼이 모두 같으면 재현 성공이에요.")
    print("      목록 자체가 달라진 건 오류가 아니라 PDB 가 자란 결과예요 — 스냅샷에는 항상 받은 날짜를 적으세요.")'''),
          md("> 다음 → 본문 [03. 분석 환경 구축](../03_setup/03_setup.md)")]
    write_nb(ROOT/"02_databases"/"02_db_explore.ipynb", c)


# ===========================================================================
# 03 — setup check : 도구를 실제로 한 번 돌려서 확인
# ===========================================================================
def nb_03():
    c = header("03_setup", "03_setup.md", "03 — 분석 환경 점검 (도구를 실제로 돌려 확인)",
               "import 여부만 보는 게 아니라 **ANARCI 를 실제로 한 번 돌려** numbering 이 나오는지 확인해요.")
    c += [bootstrap("03_setup", pip_pkgs="pandas anarci abnumber", hmmer=True),
          md('''## 1) 직접 실행 — 스택 점검 + ANARCI 스모크 테스트 (본문 3.5)

"설치됐다"의 진짜 기준은 **도구가 결과를 내놓는가**예요. 아래 셀은 이 챕터가 실제로 설치하는 것만
확인하고(부트스트랩의 `PIP_PKGS` 를 그대로 읽어요 — 점검 목록이 설치 목록과 어긋날 일이 없어요),
곧바로 데모 항체를 **실제로 numbering** 해서 걸린 시간까지 잽니다.'''),
          code('''import shutil, sys, time
import pandas as pd

rows, SMOKE = [], {}

def check(kind, name, ok, detail=""):
    rows.append({"kind": kind, "item": name, "ok": "O" if ok else "X", "detail": detail})
    print(("O " if ok else "X "), f"{name:12s}", detail)

print("[현재 커널 python]", sys.executable)
for pkg in PIP_PKGS.split():                       # 이 챕터가 pip 로 까는 것 그대로
    check("python", pkg, _have(pkg))
for tool in (["hmmscan", "ANARCI"] if NEED_HMMER else ["ANARCI"]):
    check("cli", tool, shutil.which(tool) is not None, shutil.which(tool) or "PATH에 없음")

# --- 스모크 테스트: 데모 항체를 실제로 numbering ---
try:
    from abnumber import Chain
    seqs, name = {}, None
    for line in open("data/demo_mab.fa"):
        line = line.strip()
        if line.startswith(">"): name = line[1:].split()[0]; seqs[name] = ""
        elif name: seqs[name] += line
    for sid, seq in seqs.items():
        t0 = time.time()
        ch = Chain(seq, scheme="imgt")
        dt = time.time() - t0
        SMOKE[sid] = {"chain_type": ch.chain_type, "cdr1_imgt": ch.cdr1_seq,
                      "cdr2_imgt": ch.cdr2_seq, "cdr3_imgt": ch.cdr3_seq,
                      "length": len(seq), "sec": round(dt, 3)}
        rows.append({"kind": "smoke", "item": sid, "ok": "O",
                     "detail": f"chain_type={ch.chain_type} cdr3={ch.cdr3_seq} ({dt:.2f}s)"})
        print(f"O  smoke        {sid} → chain_type {ch.chain_type} | CDR3 {ch.cdr3_seq} | {dt:.2f}s")
except Exception as e:
    rows.append({"kind": "smoke", "item": "abnumber/ANARCI", "ok": "X", "detail": f"{type(e).__name__}: {e}"})
    print("X  smoke        실패 —", type(e).__name__, e)
    print("   hmmscan 이 없으면 여기서 FileNotFoundError 가 나요 (본문 3.0)")
    print("   → Colab/Ubuntu: apt-get install -y hmmer   /   로컬: conda install -c bioconda hmmer")

report = pd.DataFrame(rows)
report.to_csv("my_run/setup_report.csv", index=False)
fail = int((report.ok == "X").sum())
print("\\nWrote: my_run/setup_report.csv")
print(f"판정 — 점검 {len(report)}건 중 실패 {fail}건.", "이 챕터 스택은 다 섰어요." if fail == 0
      else "실패 항목은 다음 절 표에서 조치 방법과 함께 봅니다.")'''),
          md('''## 2) 내 결과 확인 — 점검표와 numbering 속도 (본문 3.0)

본문 3.0 은 hmmscan 만 연결되면 `abnumber.Chain(seq, scheme='imgt')` 가 **0.1초 만에** 돈다고 했죠.
방금 잰 시간으로 그 기준을 직접 확인해요.'''),
          code('''import pathlib
import pandas as pd

try:
    rep, smoke, src = report, SMOKE, "셀 1 (이번 실행 결과를 메모리에서 그대로)"
except NameError:                                   # 커널을 다시 띄운 경우
    p = pathlib.Path("my_run/setup_report.csv")
    rep, smoke, src = (pd.read_csv(p), {}, str(p)) if p.exists() else (None, {}, None)

if rep is None:
    print("점검표가 없어요 — 1절 셀을 먼저 실행하세요.")
    print("(이 파일은 환경마다 값이 달라서 커밋된 대조군이 없어요. 폴백할 data/ 파일도 없습니다.)")
else:
    print("[출처]", src)
    display(rep)
    missing = rep[rep.ok == "X"]
    if missing.empty:
        print(f"판정 — 점검 {len(rep)}건 모두 통과.")
    else:
        print(f"판정 — {len(missing)}건이 미해결이에요. 아래를 먼저 해결하세요.")
        for _, r in missing.iterrows():
            print("  -", r["item"], "|", r["detail"])

if smoke:
    for sid, v in smoke.items():
        print(f"   numbering {sid:8s} {v['sec']:.2f}초 ({v['length']} aa)")
    fast = min(v["sec"] for v in smoke.values())
    print(f"판정 — 가장 빠른 호출 {fast:.2f}초 / 본문 3.0 기준 0.1초 →",
          "기준 안이에요." if fast <= 0.1
          else "기준보다 느려요. 첫 호출에 HMM 프로파일 로딩이 같이 들어간 값이면 정상이고, 두 사슬 다 느리면 hmmscan 경로를 확인하세요.")'''),
          md('''## 3) 레퍼런스 대조 — numbering 결과가 정답과 같은가 (본문 3.5)

`data/setup_expected.csv` 에는 같은 데모 항체를 ANARCI(IMGT)로 돌렸을 때 **나와야 하는 값**이 들어 있어요.
스모크 테스트 결과가 이것과 같으면 환경이 제대로 선 거예요.'''),
          code('''import pathlib
import pandas as pd

exp_p = pathlib.Path("data/setup_expected.csv")
try:
    smoke
except NameError:
    smoke = {}

if not exp_p.exists():
    print("정답지가 없어 대조를 건너뜁니다:", exp_p)
elif not smoke:
    print("스모크 테스트 결과가 없어 대조를 건너뜁니다 — 1절 셀을 먼저 실행하세요.")
else:
    exp = pd.read_csv(exp_p)
    keys = [k for k in ["chain_type", "length", "cdr1_imgt", "cdr2_imgt", "cdr3_imgt"] if k in exp.columns]
    rows, hit = [], 0
    for _, r in exp.iterrows():
        mine = smoke.get(r["id"])
        if mine is None:
            rows.append({"서열": r["id"], "판정": "X 내 결과에 이 서열이 없어요", "어긋난 항목": "-"})
            continue
        bad = [k for k in keys if str(mine.get(k)) != str(r[k])]
        hit += (not bad)
        row = {"서열": r["id"], "판정": "O 일치" if not bad else "X 불일치",
               "어긋난 항목": "-" if not bad else
               " · ".join(f"{k}: 정답지 {r[k]} → 내 결과 {mine.get(k)}" for k in bad)}
        row.update({k: r[k] for k in keys})       # 정답지 값을 그대로 옆에 세워 둡니다
        rows.append(row)
    print("정답지와 내 스모크 결과를 항목별로 맞춰 봤어요 (표의 값은 정답지 기준).")
    display(pd.DataFrame(rows))
    print(f"판정 — 정답지 {len(exp)}개 중 {hit}개 일치({len(keys)}개 항목 전수 비교).",
          "환경이 제대로 섰어요." if hit == len(exp)
          else "한 건이라도 다르면 hmmscan·ANARCI 버전을 먼저 확인하세요 — 보고서엔 도구 버전을 함께 적습니다.")'''),
          md('''## 4) 로컬 재현용 conda 환경 파일 점검 (본문 3.1~3.4)

Colab 은 노트북마다 런타임이 달라 의존성 충돌이 자연히 없지만, 로컬에서 반복 실행하려면
환경을 셋으로 나눠야 해요(`abseq`·`abstruct`·`abinterface`). 그 정의 파일이 저장소에 실제로
들어 있는지, **버전 고정이 살아 있는지** 확인합니다.'''),
          code('''import pandas as pd

EXPECT = {                                   # 파일 → 반드시 들어 있어야 하는 항목 (본문 3.2~3.4)
    "abseq.yml":       ["hmmer", "anarci", "abnumber", "sapiens"],
    "abstruct.yml":    ["igfold", "transformers==4.36.2", "anarci", "abnumber"],
    "abinterface.yml": ["freesasa", "mdanalysis", "plip"],
}
env_dir = ADV_ROOT / "environment"
rows = []
for fn, keys in EXPECT.items():
    p = env_dir / fn
    txt = p.read_text(encoding="utf-8") if p.exists() else ""
    rows.append({"파일": fn, "존재": "O" if p.exists() else "X",
                 "확인 항목": len(keys), "빠진 항목": ", ".join(k for k in keys if k not in txt) or "없음"})
envs = pd.DataFrame(rows)
display(envs)

ok = (envs["존재"] == "O").all() and (envs["빠진 항목"] == "없음").all()
print(f"판정 — 환경 파일 {len(envs)}개 중 존재 {int((envs['존재'] == 'O').sum())}개 ·",
      "필요한 항목이 전부 들어 있어요." if ok else "위 표의 '빠진 항목' 을 채워야 해요.")
print("      transformers==4.36.2 고정은 IgFold 체크포인트에 pickle 된 옛 토크나이저 때문이에요(본문 3.3).")
print("      PyMOL 은 pip·conda 어느 쪽으로도 이 목록에 못 들어가요. 대신 Ch.06·07 의 3D 는")
print("      py3Dmol 인라인 뷰어로 띄우니 Colab 에서도 내 구조를 그대로 돌려 볼 수 있어요(본문 3.0).")'''),
          md("> 다음 → 본문 [04. numbering & germline](../04_numbering/04_numbering.md)")]
    write_nb(ROOT/"03_setup"/"03_setup_check.ipynb", c)


# ===========================================================================
# 04 — numbering lab : ANARCI 를 직접 실행
# ===========================================================================
def nb_04():
    c = header("04_numbering", "04_numbering.md", "04 — numbering & germline (ANARCI 직접 실행)",
               "ANARCI 를 **직접 돌려** IMGT·Chothia numbering CSV 를 `my_run/` 에 만들고, 커밋된 결과와 대조해요.")
    c += [bootstrap("04_numbering", pip_pkgs="pandas anarci abnumber", hmmer=True),
          md('''## 1) 직접 실행 — ANARCI numbering (본문 4.1)

```bash
ANARCI -i data/demo_mab.fa -s imgt --assign_germline --csv --outfile my_run/demo_imgt
ANARCI -i data/demo_mab.fa -s chothia --csv --outfile my_run/demo_chothia
```
사슬별 CSV(`..._H.csv`, `..._KL.csv`)가 생깁니다. 각 numbering 위치가 **컬럼 하나**가 돼요.
`--assign_germline` 은 IMGT 쪽에만 붙였어요 — germline 은 scheme 과 무관하니 한 번만 받으면 됩니다.'''),
          code('''import pathlib, pandas as pd

run_tool(["ANARCI", "-i", "data/demo_mab.fa", "-s", "imgt",
          "--assign_germline", "--csv", "--outfile", "my_run/demo_imgt"])
run_tool(["ANARCI", "-i", "data/demo_mab.fa", "-s", "chothia",
          "--csv", "--outfile", "my_run/demo_chothia"])

# 위 출력에 남는 경고 한 줄은 **무해**해요. 실패로 오해하기 쉬워 여기서 짚고 갑니다.
print("\\n[경고 읽는 법] 위에 'Non IG chains cannot be numbered with the chothia scheme' 이 떴다면 정상이에요.")
print("  ANARCI 가 입력을 보기 '전에', scheme 이 imgt 가 아니면 무조건 찍는 안내예요.")
print("  실제로 빠진 사슬이 있는지는 아래 표로 확인해요.")
print("  (ANARCI 자기 소스에서 나던 SyntaxWarning 은 run_tool 이 PYTHONWARNINGS=ignore 로 눌러 뒀어요.")
print("   보고 싶으면 부트스트랩의 QUIET_WARNINGS 를 False 로 바꾸세요.)")

# 어느 서열이 어느 파일로 갔는지 눈으로 확인 — '빠진 사슬 없음' 은 여기서 판정해요.
rows = []
for p in sorted(pathlib.Path("my_run").glob("demo_*.csv")):
    try:
        d = pd.read_csv(p)
        rows.append({"파일": p.name,
                     "scheme": "imgt" if "imgt" in p.name else "chothia",
                     "사슬": "H (중쇄)" if p.name.endswith("_H.csv") else "KL (경쇄)",
                     "번호매김된 서열": " · ".join(map(str, d["Id"])) if "Id" in d.columns else "?",
                     "numbering 컬럼": d.shape[1]})
    except Exception as e:
        rows.append({"파일": p.name, "scheme": "-", "사슬": "-",
                     "번호매김된 서열": f"읽기 실패 ({type(e).__name__})", "numbering 컬럼": 0})

if rows:
    display(pd.DataFrame(rows))
    got = {r["번호매김된 서열"] for r in rows}
    print(f"판정 — CSV {len(rows)}개(imgt/chothia × H/KL)가 정상이에요. 입력 2서열이 모두 번호매김됐으면 누락 없음이에요.")
    print("       위 표의 '번호매김된 서열' 에 demo_HC 와 demo_LC 가 다 보이면 통과예요 —", " / ".join(sorted(got)))
else:
    print("판정 — my_run 에 CSV 가 하나도 없어요. hmmscan 이 없을 가능성이 커요(Ch.03 의 3.0).")
print("       실패해도 아래 절은 커밋된 data/ 로 이어갑니다.")'''),
          md('''## 2) 내 결과 확인 — germline 할당 (본문 4.2)

`--assign_germline` 이 붙여준 V/J gene 과 **어느 종의 germline인지**를 읽습니다.
어떤 사슬을 humanize 해야 하는지가 여기서 정해져요.'''),
          code('''import pandas as pd

FILES = {f: resolve(f) for f in ["demo_imgt_H.csv", "demo_imgt_KL.csv",
                                 "demo_chothia_H.csv", "demo_chothia_KL.csv"]}

def first_domain(fname):
    """ANARCI CSV 한 행 = variable domain 하나. 첫 domain 을 돌려주고, 여러 개면 알려준다."""
    d = pd.read_csv(FILES[fname])
    if len(d) > 1:
        print(f"[주의] {fname} 에 domain {len(d)}개 — scFv 처럼 한 서열에 VH·VL 이 같이 있으면 "
              f"행이 여러 개예요. 아래는 첫 domain 만 봅니다.")
    return d.iloc[0]

def val(r, *names):
    """있는 컬럼 중 먼저 나오는 값(없거나 NaN 이면 None)."""
    for n in names:
        if n in r.index and pd.notna(r[n]):
            return r[n]
    return None

def pct(x):
    return "-" if x is None else f"{float(x)*100:.0f}%"

germ = []
for label, f in [("Heavy", "demo_imgt_H.csv"), ("Light", "demo_imgt_KL.csv")]:
    r = first_domain(f)
    germ.append({"사슬": label,
                 "chain_type": val(r, "chain_type"),
                 "species": val(r, "identity_species", "hmm_species"),
                 "V gene": val(r, "v_gene"), "V identity": pct(val(r, "v_identity")),
                 "J gene": val(r, "j_gene"), "J identity": pct(val(r, "j_identity")),
                 "bit score": val(r, "score")})
g = pd.DataFrame(germ)
display(g)

nonhuman = [f"{row['사슬']}({row['V gene']}, {row['species']})"
            for _, row in g.iterrows() if str(row["species"]).lower() != "human"]
print("판정 — human germline 이 아닌 사슬:", ", ".join(nonhuman) or "없음")
print(f"      → {len(nonhuman)}개 사슬이 humanization 대상이에요." if nonhuman
      else "      → 두 사슬 다 human germline 이라 humanization 대상이 아니에요.")
print("      Ch.05 에서 Sapiens 도 같은 사슬만 '덜 사람스럽다'고 판정하는지 확인합니다.")
print("      bit score 는 HMM 프로파일 DB 버전에 따라 달라져요 — 5절에서 따로 봅니다(본문 4.2).")'''),
          md('''## 3) 내 결과 확인 — IMGT vs Chothia 를 잔기 단위로 나란히 (본문 4.3)

같은 중쇄를 두 scheme 으로 numbering 하면 CDR-H1 에 들어가는 잔기 수가 달라져요.
개수만 보면 감이 안 오니 **같은 잔기가 두 scheme 에서 각각 몇 번인지** 나란히 놓고 봅니다.'''),
          code('''import pandas as pd

def numbered(fname):
    """ANARCI CSV 한 행 → [(번호 라벨, 기본 번호, 잔기)] 를 서열 순서대로."""
    r = pd.read_csv(FILES[fname]).iloc[0]
    out = []
    for col in r.index:
        lab = str(col).strip()
        base = lab.rstrip("ABCDEFGHIJKLMNOP")          # insertion code(100A) 분리
        if base.isdigit() and str(r[col]) not in ("nan", "-", ""):
            out.append((lab, int(base), str(r[col])))
    return out

def occupied(fname, lo, hi):
    return [(lab, aa) for lab, base, aa in numbered(fname) if lo <= base <= hi]

imgt_h1 = occupied("demo_imgt_H.csv", 27, 38)
chot_h1 = occupied("demo_chothia_H.csv", 26, 32)
print(f"IMGT    CDR-H1 (27-38) — {len(imgt_h1)} 잔기  {''.join(a for _, a in imgt_h1)}")
print(f"Chothia CDR-H1 (26-32) — {len(chot_h1)} 잔기  {''.join(a for _, a in chot_h1)}")

mi, mc = numbered("demo_imgt_H.csv"), numbered("demo_chothia_H.csv")
if len(mi) != len(mc) or any(a != b for (_, _, a), (_, _, b) in zip(mi, mc)):
    print("[주의] 두 CSV 의 잔기 서열이 달라 나란히 비교를 건너뜁니다 — 같은 FASTA 로 돌렸는지 확인하세요.")
else:
    lo, hi = 24, 36                                    # CDR-H1 앞뒤로 조금 넓게
    side = pd.DataFrame([
        {"서열 위치": i, "잔기": a,
         "IMGT 번호": f"H{l1}", "Chothia 번호": f"H{l2}",
         "IMGT CDR-H1": "●" if 27 <= b1 <= 38 else "",
         "Chothia CDR-H1": "●" if 26 <= b2 <= 32 else ""}
        for i, ((l1, b1, a), (l2, b2, _)) in enumerate(zip(mi, mc), 1) if lo <= i <= hi])
    display(side)

    imgt_of_chot31 = [(l1, a) for (l1, _, a), (l2, _, _) in zip(mi, mc) if l2 == "31"]
    imgt31 = [a for l, _, a in mi if l == "31"]
    print("판정 — 같은 잔기라도 scheme 이 다르면 번호가 달라져요.")
    for l1, a in imgt_of_chot31:
        print(f"      Chothia H31 = {a}  ↔  같은 잔기의 IMGT 번호는 H{l1}")
    print("      IMGT H31 은", f"{imgt31[0]}" if imgt31 else "이 서열에서 비어 있어요(gap)",
          "— 그래서 scheme 없는 'H31' 은 어느 잔기인지 알 수 없어요.")
    print("      보고서·mutation table 에는 항상 (IMGT) 또는 (Chothia) 를 명시하세요.")'''),
          md('''## 4) 내 결과 확인 — 서열 QC 표 (본문 4.4)

numbering 은 QC 8단계 중 2~4단계예요. 지금까지 읽은 값을 한 장으로 모아 두면
Ch.05 이후 모든 챕터가 이 표를 좌표계로 씁니다.'''),
          code('''import pandas as pd

IMGT_CDR = {"CDR1 (IMGT)": (27, 38), "CDR2 (IMGT)": (56, 65), "CDR3 (IMGT)": (105, 117)}

fa, name = {}, None
for line in open("data/demo_mab.fa"):
    line = line.strip()
    if line.startswith(">"): name = line[1:].split()[0]; fa[name] = ""
    elif name: fa[name] += line

def qc_col(fname):
    r = pd.read_csv(FILES[fname]).iloc[0]
    n = len(numbered(fname))
    sid = str(val(r, "Id"))
    col = {"Chain type": val(r, "chain_type"),
           "V gene": f"{val(r, 'v_gene')} ({val(r, 'identity_species', 'hmm_species')}, {pct(val(r, 'v_identity'))})",
           "J gene": f"{val(r, 'j_gene')} ({pct(val(r, 'j_identity'))})"}
    for lab, (lo, hi) in IMGT_CDR.items():
        s = "".join(a for _, a in occupied(fname, lo, hi))
        col[lab] = f"{s} ({len(s)} aa)"
    col["Numbering 성공"] = "양호" if n else "실패"
    col["Numbering 잔기 수"] = n
    col["Sequence length"] = len(fa.get(sid, ""))
    return col

qc = pd.DataFrame({"Heavy": qc_col("demo_imgt_H.csv"), "Light": qc_col("demo_imgt_KL.csv")})
display(qc)

covered = True
for lab in qc.columns:
    n, L = qc.loc["Numbering 잔기 수", lab], qc.loc["Sequence length", lab]
    covered &= (n == L)
    print(f"      {lab}: numbering {n} / FASTA {L} 잔기 →",
          "전체를 덮었어요." if n == L else f"{L - n} 잔기가 variable domain 밖이에요(constant 영역 등).")
print("판정 —", "두 사슬 다 numbering 이 서열 전체를 덮었어요. QC 통과예요."
      if covered else "덮이지 않은 구간이 있어요 — FASTA 에 constant 영역이 섞였는지 확인하세요.")
print("      QC 8단계 중 여기까지가 1~4단계. 5~6(liability)은 Ch.08, 7(reference 비교)은 Ch.09, 8(구조)은 Ch.06 이에요.")'''),
          md('''## 5) 레퍼런스 대조 — 커밋된 ANARCI 결과와 같은가 (본문 4.2)

`data/demo_imgt_H.csv` 등은 이 저장소를 만들 때 ANARCI 로 돌려 커밋해 둔 대조군이에요.
비교는 두 갈래로 나눠서 봅니다 — **germline·numbering**(같아야 하는 것)과
**bit score·e-value**(도구/HMM 프로파일 DB 버전에 따라 달라질 수 있는 것).'''),
          code('''import pandas as pd, pathlib

SOFT = ["score", "e-value"]          # 버전에 따라 달라질 수 있는 값 (본문 4.2)

def fmt(vals):
    """대괄호·따옴표·부동소수 찌꺼기를 걷어내요 — 2.6000000000000003e-60 → 2.6e-60."""
    out = []
    for v in vals:
        try:
            x = float(v)
            out.append(f"{x:g}" if 1e-4 <= abs(x) < 1e5 else f"{x:.2e}")
        except (TypeError, ValueError):
            out.append(str(v))
    return " · ".join(out)

rows, hard_diffs = [], []
for fname in ["demo_imgt_H.csv", "demo_imgt_KL.csv",
              "demo_chothia_H.csv", "demo_chothia_KL.csv"]:
    mine_p, ref_p = pathlib.Path("my_run")/fname, pathlib.Path("data")/fname
    if not mine_p.exists() or not ref_p.exists():
        rows.append({"파일": fname,
                     "numbering 일치": "대조 건너뜀",
                     "대조한 컬럼": "-",
                     "bit score (내 결과 → 레퍼런스)": "my_run 산출물 없음" if not mine_p.exists() else "레퍼런스 없음",
                     "e-value (내 결과 → 레퍼런스)": "-"})
        continue
    mine, ref = pd.read_csv(mine_p), pd.read_csv(ref_p)
    common = [c for c in ref.columns if c in mine.columns]
    hard   = [c for c in common if c not in SOFT]          # 같아야 하는 것
    same   = mine[hard].astype(str).equals(ref[hard].astype(str))
    row = {"파일": fname,
           "numbering 일치": "O 같음" if same else "X 다름",
           "대조한 컬럼": f"{len(hard)} / 공통 {len(common)}"}
    for col in SOFT:                                        # 달라도 되는 것
        m, rf = (fmt(mine[col].tolist()), fmt(ref[col].tolist())) if col in common else ("-", "-")
        row[f"{col} (내 결과 → 레퍼런스)"] = m if m == rf else f"{m} → {rf}"
    rows.append(row)
    if not same:                                            # 진짜 문제일 때만 자세히
        for col in hard:
            if not mine[col].astype(str).equals(ref[col].astype(str)):
                hard_diffs.append((fname, col, fmt(mine[col].tolist()), fmt(ref[col].tolist())))

display(pd.DataFrame(rows))

if hard_diffs:
    print("germline·numbering 이 어긋난 자리 — 여기가 진짜 문제예요")
    for fname, col, m, rf in hard_diffs:
        print(f"  {fname} · {col} — 내 결과 {m} / 레퍼런스 {rf}")

judged = [r for r in rows if r["numbering 일치"] != "대조 건너뜀"]
ok = sum(1 for r in judged if r["numbering 일치"] == "O 같음")
if not judged:
    print("대조할 my_run 산출물이 없어요 — 1절 셀을 먼저 실행하세요.")
else:
    print(f"판정 — 대조한 {len(judged)}개 파일 중 germline·numbering 일치 {ok}개.")
    print("       위 표에서 'numbering 일치' 가 전부 O 면 통과예요.")
    print("       bit score·e-value 칸에 화살표(→)가 보여도 정상이에요 — ANARCI/HMM 프로파일 DB")
    print("       버전이 다르면 점수만 조금 달라지고 numbering 은 그대로거든요. 보고서엔 도구 버전을 함께 적으세요.")'''),
          md("> 다음 → 본문 [05. humanness & humanization](../05_humanness/05_humanness.md)")]
    write_nb(ROOT/"04_numbering"/"04_numbering_lab.ipynb", c)


# ===========================================================================
# 05 — humanness lab : Sapiens 를 직접 실행 (pip 만으로)
# ===========================================================================
def nb_05():
    c = header("05_humanness", "05_humanness.md", "05 — humanness & humanization (Sapiens 직접 실행)",
               "Sapiens 언어모델을 **직접 돌려** humanness 점수·humanized 서열을 `my_run/` 에 만들어요.")
    c += [bootstrap("05_humanness", pip_pkgs="pandas matplotlib sapiens abnumber anarci", hmmer=True),

          md('''## 1) 직접 실행 — Sapiens humanness + humanization (본문 5.1)

BioPhi CLI(`biophi sapiens`)는 **bioconda 전용**이라 Colab 에서 못 써요. 하지만 BioPhi 가 내부에서 쓰는
두 부품(`sapiens` 언어모델, `abnumber` numbering)은 **둘 다 pip 에 있어요** — 그래서 같은 알고리즘을
그대로 돌릴 수 있습니다.

```bash
python scripts/sapiens_humanize.py data/demo_mab.fa \\
    --scores-out my_run/demo_sapiens_scores.csv --fasta-out my_run/demo_humanized.fa
```
① 위치별 아미노산 확률 예측 → ② 각 위치 최대확률 아미노산으로 재구성 → ③ **원본 CDR 재이식**
(BioPhi 기본값 — scheme=kabat, cdr_definition=kabat, 1 iteration, CDR 은 humanize 하지 않음)'''),
          code('''ok = run_tool([PY, SCRIPTS/"sapiens_humanize.py", "data/demo_mab.fa",
               "--scores-out", "my_run/demo_sapiens_scores.csv",
               "--fasta-out",  "my_run/demo_humanized.fa"])
print("→ my_run/ 에 점수 CSV 와 humanized FASTA 가 생겼어요. 2절부터 이 파일을 읽습니다." if ok
      else "→ 실패했어요. 뒤 절은 커밋된 data/ 로 이어갑니다.")'''),

          md('''## 2) 내 결과 확인 — 사슬별 humanness (본문 5.2)

humanness 는 **Sapiens 가 입력 잔기에 준 확률**을 사슬 평균한 값이에요. 본문 5.2 그래프의 빨간 점선과
같은 **0.8** 을 기준선으로 씁니다.'''),
          code('''import pandas as pd
from IPython.display import display

AA20 = list("ACDEFGHIKLMNPQRSTVWY")
HUMAN_LIKE = 0.8        # 본문 5.2 그래프의 빨간 기준선

def chain_humanness(df):
    """사슬별 mean P(input residue). X·gap 처럼 20종 밖 잔기는 평균에서 뺀다."""
    cols = [a for a in AA20 if a in df.columns]          # 컬럼 교집합 — 스키마가 달라도 안 죽게
    p = [row[row["input_aa"]] if row["input_aa"] in cols else None
         for _, row in df.iterrows()]
    return df.assign(p_input=p).groupby("chain")["p_input"].mean()

scores_csv = resolve("demo_sapiens_scores.csv")
scores = pd.read_csv(scores_csv)
hum = chain_humanness(scores)

display(pd.DataFrame([{"사슬": chain, "humanness": round(v, 4),
                       "잔기 수": int((scores["chain"] == chain).sum()),
                       f"기준선 {HUMAN_LIKE}": "위 — 사람답다" if v >= HUMAN_LIKE else "아래 — 손볼 대상"}
                      for chain, v in hum.items()]))

low = [chain for chain, v in hum.items() if v < HUMAN_LIKE]
print("기준선 아래 사슬 — " + (" · ".join(low) or "없음") + " → humanize 로 손볼 대상이에요.")
print("Ch.04 에서 ANARCI 가 germline 을 판정한 사슬과 같은 쪽이 걸리는지 맞춰 보세요 "
      "(germline 할당 + 언어모델, 서로 독립인 두 도구의 합의).")'''),

          md('''## 3) 내 결과 확인 — humanness 그래프 (본문 5.2)

왼쪽 패널이 방금 찍은 사슬별 평균 humanness(빨간 점선 = 0.8), 오른쪽 패널이 원본 → humanized 변이 수예요.
두 패널을 나란히 두면 "humanness 가 낮은 사슬을 더 많이 손본다"가 눈으로 확인됩니다.'''),
          code('''from antibody_viz import humanness_overview
from IPython.display import Image, display

png = "my_run/05_humanness_overview.png"
humanized_fa = resolve("demo_humanized.fa")
humanness_overview(scores_csv, "data/demo_mab.fa", humanized_fa,
                   "Humanness — Sapiens (demo mAb, 내 실행 결과)", png)
display(Image(png))

verdict = " · ".join(f"{chain} {v:.3f} {'≥' if v >= HUMAN_LIKE else '<'} {HUMAN_LIKE}"
                     for chain, v in hum.items())
print("기준선 대비 판정 —", verdict)
print(f"→ 기준선 {HUMAN_LIKE} 아래 {len([v for v in hum if v < HUMAN_LIKE])}개 사슬 / "
      f"위 {len([v for v in hum if v >= HUMAN_LIKE])}개 사슬.")'''),

          md('''## 4) 어느 위치가 바뀌었나 — Kabat 번호와 FR/CDR 귀속 (본문 5.3 · 5.4)

본문 5.3 은 변이 **수**를, 5.4 는 **위치**를 묻습니다 — Vernier zone·CDR-supporting residue 를 건드리면
humanness 가 올라가도 결합을 잃을 수 있으니까요. `abnumber` 로 Kabat 번호를 붙여 두 질문을 한 표로 닫아요.'''),
          code('''import pandas as pd

def read_fa(path):
    d, name = {}, None
    for line in open(path):
        line = line.strip()
        if line.startswith(">"):
            name = line[1:].split()[0]; d[name] = ""
        elif name:
            d[name] += line
    return d

orig = read_fa("data/demo_mab.fa")
humanized = read_fa(humanized_fa)          # 3절이 고른 그 FASTA

try:
    from abnumber import Chain
except Exception as e:                       # abnumber 는 hmmscan 이 있어야 돌아요
    Chain = None
    print(f"[abnumber 사용 불가 — {type(e).__name__}] Kabat 번호 없이 raw 위치만 표시합니다.")
    print("→ pip install abnumber anarci 와 hmmscan(conda install -c bioconda hmmer) 후 재실행하세요.")

rows = []
for sid, o in orig.items():
    h = humanized.get(sid, "")
    if len(o) != len(h):
        print(f"{sid}: 길이가 달라(원본 {len(o)} / humanized {len(h)}) 위치 비교를 건너뜁니다.")
        continue
    labels = {}
    if Chain is not None:
        try:
            ab = Chain(o, scheme="kabat", cdr_definition="kabat")
            ct = "H" if ab.is_heavy_chain() else "L"
            off = o.find(ab.seq)             # abnumber 가 V 도메인 밖을 잘라내면 생기는 offset
            for i, pos in enumerate(ab.positions):
                labels[off + i] = (format(pos), pos.get_region().replace("CDR", f"CDR-{ct}"))
        except Exception as e:
            print(f"{sid}: numbering 실패({type(e).__name__}) → raw 위치만 표시합니다.")
    for i, (a, b) in enumerate(zip(o, h)):
        if a != b:
            num, region = labels.get(i, ("-", "-"))
            rows.append({"seq": sid, "raw_pos": i + 1, "Kabat": num,
                         "region": region, "original": a, "humanized": b})

diff = pd.DataFrame(rows, columns=["seq", "raw_pos", "Kabat", "region", "original", "humanized"])
for sid, o in orig.items():
    n = int((diff["seq"] == sid).sum()) if len(diff) else 0
    print(f"{sid}: 길이 {len(o)} · 변이 {n}개 ({n / len(o) * 100:.0f}%)")

if len(diff):
    display(diff)
    n_cdr = int(diff["region"].astype(str).str.startswith("CDR").sum())
    vc = diff["region"].value_counts()
    print("region 분포 —", " · ".join(f"{k} {v}개" for k, v in sorted(vc.items())))
    if n_cdr == 0:
        print(f"→ 변이 {len(diff)}개가 전부 framework 예요. 1절 ③ '원본 CDR 재이식'이 그대로 작동했습니다 "
              f"— 결합부위는 손대지 않았어요.")
    else:
        print(f"→ CDR 안 변이가 {n_cdr}개 있어요. 결합을 잃었을 수 있으니 본문 5.4 workflow 의 "
              f"6단계(back-mutation 후보)로 올리세요.")
else:
    print("\\n바뀐 위치가 없어요 — Sapiens 가 '고칠 필요 없다'고 본 서열이에요.")'''),

          md('''## 5) 레퍼런스 대조 — BioPhi CLI 결과와 같은가 (본문 5.1)

`data/demo_sapiens_scores.csv`·`data/demo_humanized.fa` 는 **bioconda BioPhi CLI** 로 만들어 커밋한 대조군이에요.
여기서 보는 판정 기준은 딱 두 개 — **사슬 평균 humanness 를 소수 4자리까지** 비교한 차이,
그리고 **humanized 서열이 글자 그대로 같은지** 입니다.'''),
          code('''mine_csv, mine_fa = MYRUN/"demo_sapiens_scores.csv", MYRUN/"demo_humanized.fa"

if mine_csv.exists() and mine_fa.exists():
    mine, ref = pd.read_csv(mine_csv), pd.read_csv("data/demo_sapiens_scores.csv")
    cmp = pd.DataFrame({"내 결과": chain_humanness(mine).round(4),
                        "레퍼런스(BioPhi CLI)": chain_humanness(ref).round(4)})
    cmp["차이"] = (cmp["내 결과"] - cmp["레퍼런스(BioPhi CLI)"]).abs().round(4)
    display(cmp)

    m_fa, r_fa = read_fa(mine_fa), read_fa("data/demo_humanized.fa")
    print("humanized 서열까지 글자 단위로 같은지")
    display(pd.DataFrame([{"서열": sid,
                           "판정": "O 글자까지 동일" if m_fa.get(sid) == r_fa.get(sid) else "X 다름",
                           "내 결과 길이": len(m_fa.get(sid) or ""),
                           "레퍼런스 길이": len(r_fa.get(sid) or "")} for sid in r_fa]))

    max_gap = float(cmp["차이"].max())
    same_seq = all(m_fa.get(sid) == r_fa.get(sid) for sid in r_fa)
    print(f"판정 — 사슬 평균 차이 최대 {max_gap:.4f} (소수 4자리) · humanized 서열은 "
          + ("전부 동일" if same_seq else "일부 다름"))
    if max_gap == 0.0 and same_seq:
        print("→ pip 부품 조합(sapiens + abnumber)이 bioconda CLI 를 재현했어요.")
    else:
        print("→ 차이가 남았어요. sapiens·abnumber 버전과 scheme(kabat) 설정부터 확인하세요.")
else:
    print("my_run 산출물이 없어 대조를 건너뜁니다 (1절이 실패했거나 건너뛰었어요).")'''),

          md("> 다음 → 본문 [06. 구조예측 (IgFold)](../06_structure/06_structure.md)")]
    write_nb(ROOT/"05_humanness"/"05_humanness_lab.ipynb", c)


# ===========================================================================
# 06 — structure lab : IgFold 를 직접 실행
# ===========================================================================
def nb_06():
    c = header("06_structure", "06_structure.md", "06 — 구조예측 (IgFold 직접 실행)",
               "IgFold 를 **직접 돌려** Fv 구조를 예측하고(`my_run/`), 커밋된 예측 구조와 CA-RMSD 로 대조해요.")
    c += [bootstrap("06_structure",
                    pip_pkgs="pandas matplotlib biopython igfold anarci abnumber py3Dmol gemmi",
                    hmmer=True, pin_transformers="4.36.2"),

          md('''## 1) 직접 실행 — IgFold 로 Fv 예측 (본문 6.1)

```bash
python scripts/run_igfold_demo.py --fasta data/demo_mab.fa --out my_run/demo_antibody_igfold.pdb
```
IgFold 는 항체 언어모델(AntiBERTy) + graph network 로 backbone 을 예측하고, **B-factor 컬럼에
잔기별 예측오차(Å)** 를 적어 줘요. 실행 중 나오는 함정 두 가지는 스크립트가 처리합니다.

- `torch ≥ 2.6` 의 `weights_only=True` → 체크포인트 로드 실패 → `weights_only=False` 로 감싸기
- 최신 `transformers`(5.x) → 체크포인트 unpickle 실패 → 부트스트랩이 **`transformers==4.36.2`** 로 맞춰 줌

> `RUN_IGFOLD = False` 로 두면 예측을 건너뛰고 커밋된 PDB(`data/`)로 나머지 절을 진행해요.'''),
          code('''RUN_IGFOLD = True     # False 면 예측을 건너뛰고 커밋본(data/)으로 진행

# 걸리는 시간은 코어 수에 정직하게 비례해요 — 멀티코어 CPU 9초, 코랩 무료(2 vCPU) 40~60초.
# AntiBERTy + IgFold 모델 4개를 차례로 돌리는 단계라, 1분 가까이 걸려도 실패가 아니에요.

if RUN_IGFOLD:
    run_tool([PY, SCRIPTS/"run_igfold_demo.py",
              "--fasta", "data/demo_mab.fa",
              "--out", "my_run/demo_antibody_igfold.pdb"])
else:
    print("RUN_IGFOLD=False → 예측을 건너뛰고 레퍼런스 PDB 로 진행합니다.")'''),

          md('''## 2) 내 결과 확인 — 사슬별 신뢰도와 최대오차 잔기 (본문 6.2)

본문이 "봉우리는 CDR-H3" 라고 읽으라 하니, **최대오차가 몇 번 잔기인지**까지 뽑아서 확인해요.
기준선은 본문 그래프와 같은 **1 Å** 입니다.'''),
          code('''import pandas as pd
from IPython.display import display

CONF = 1.0      # 본문 6.2 그래프의 빨간 기준선 (< 1 Å 이면 신뢰)

# 번호는 IgFold 가 do_renum=True 로 붙인 Chothia 번호(insertion code 포함).
# CDR 구간은 Kabat 정의 범위로 판정해요.
CDR_RANGES = {"H": [("CDR-H1", 31, 35), ("CDR-H2", 50, 65), ("CDR-H3", 95, 102)],
              "L": [("CDR-L1", 24, 34), ("CDR-L2", 50, 56), ("CDR-L3", 89, 97)]}

def region_of(chain, num):
    """잔기번호 → CDR 이름 또는 FR."""
    for name, lo, hi in CDR_RANGES.get(chain, []):
        if lo <= num <= hi:
            return name
    return "FR"

pdb = resolve("demo_antibody_igfold.pdb")
res, atom_names, n_atoms = {}, set(), 0
for line in open(pdb):
    if not line.startswith("ATOM"):
        continue
    n_atoms += 1
    name = line[12:16].strip()
    atom_names.add(name)
    if name == "CA":
        # (번호, insertion code, 예측오차) — 파일에 적힌 순서가 곧 서열 순서예요
        res.setdefault(line[21], []).append((int(line[22:26]), line[26].strip(), float(line[60:66])))

peaks, summary = [], []
for chain, v in sorted(res.items()):
    err = [b for _, _, b in v]
    num, ins, top = max(v, key=lambda r: r[2])
    over = [(f"{chain}{n}{i}", b, region_of(chain, n)) for n, i, b in sorted(v, key=lambda r: -r[2])
            if b > CONF]
    peaks += over
    summary.append({"사슬": chain, "잔기 수": len(v),
                    "평균 오차 (Å)": round(sum(err)/len(err), 2),
                    "최대 오차 (Å)": round(top, 2),
                    "최대인 잔기": f"{chain}{num}{ins}",
                    "그 잔기의 구간": region_of(chain, num),
                    f"{CONF:g} Å 초과": f"{len(over)}개"})

print("사슬별 요약 — 평균이 낮고 최대만 튀면 '대부분 믿을 만한데 한 loop 만 불확실' 이라는 뜻이에요.")
display(pd.DataFrame(summary))

if peaks:
    print(f"\\n{CONF:g} Å 을 넘는 잔기 {len(peaks)}개 (오차 큰 순)")
    display(pd.DataFrame([{"잔기": lbl, "예측오차 (Å)": round(b, 2), "구간": r,
                           "막대": "█" * max(1, round(b / CONF * 4))}
                          for lbl, b, r in sorted(peaks, key=lambda x: -x[1])]))

hot = sorted({r for _, _, r in peaks})
print(f"\\n판정 — {CONF:g} Å 을 넘는 잔기 {len(peaks)}개, 소속 구간 " + (" · ".join(hot) or "없음"))
if peaks and all(r != "FR" for _, _, r in peaks):
    print("→ 불확실한 곳이 CDR loop 로만 몰렸어요. framework 좌표는 쓰고 그 loop 만 교차검증하세요(본문 6.4).")
elif peaks:
    print("→ CDR 밖에도 1 Å 을 넘는 곳이 있어요. 그 구간부터 확인하세요.")
else:
    print("→ 전 구간이 1 Å 아래예요.")

print(f"\\n원자 {n_atoms}개 · 원자 종류 " + " · ".join(sorted(atom_names)))
print("스크립트가 do_refine=False 로 돌려서 side chain 이 없는 backbone(+CB) 모델이에요. "
      "side chain 원자 접촉이 필요한 분석(Ch.07 interface·Ch.08)에 이 PDB 를 그대로 넣으면 안 됩니다.")'''),

          md('''## 3) 내 결과 확인 — 신뢰도 프로파일 그래프 (본문 6.2)

잔기 번호에 **insertion code** 가 붙어 있어요(H52A·H82A~C·H100A~C). 번호를 정수로만 쓰면
H100 / H100A / H100B / H100C 가 **한 x 좌표에 겹쳐** 봉우리 폭이 뭉개집니다 — 하필 본문이
"CDR-H3 구간" 이라고 읽으라는 바로 그 자리예요. 그래서 여기서는 **사슬 안 순차 인덱스**로 그리고,
1 Å 을 넘는 점에는 실제 잔기 라벨을 달아요.'''),
          code('''import antibody_viz                    # import 만으로 한글 폰트 등록 + 팔레트 재사용
import matplotlib.pyplot as plt
from IPython.display import Image, display

png = "my_run/06_structure_confidence.png"
palette = {"H": antibody_viz.C_PURPLE, "L": antibody_viz.C_ORANGE}

fig, ax = plt.subplots(figsize=(11, 5))
for chain, v in sorted(res.items()):
    ys = [b for _, _, b in v]
    ax.plot(range(len(ys)), ys, marker="o", ms=3, lw=1.4,
            color=palette.get(chain, antibody_viz.C_TEAL),
            label=f"chain {chain} (mean {sum(ys)/len(ys):.2f} Å)")
    for k, (num, ins, b) in enumerate(v):
        if b > CONF:
            ax.annotate(f"{chain}{num}{ins}", (k, b), fontsize=7, ha="center", va="bottom")
ax.axhline(CONF, ls="--", color=antibody_viz.C_THR, lw=1.5, label=f"confident (<{CONF:g} Å)")
ax.set_title("IgFold confidence — demo mAb (Fv, 내 실행 결과)", fontsize=14, fontweight="bold")
ax.set_xlabel("Residue index (사슬 내 순서 — insertion code 포함)", fontsize=11)
ax.set_ylabel("Predicted error / B-factor (Å)", fontsize=11)
ax.grid(alpha=0.25); ax.legend(fontsize=9)
fig.tight_layout(); fig.savefig(png, dpi=150, bbox_inches="tight"); plt.close(fig)
display(Image(png))

flat = {chain: max(b for _, _, b in v) for chain, v in res.items()}
print("사슬별 최대 예측오차 —", " · ".join(f"{k} 사슬 {v:.2f} Å" for k, v in sorted(flat.items())))
print(f"→ 라벨이 달린 봉우리가 {len(peaks)}개. 나머지 잔기는 전부 {CONF:g} Å 선 아래라 "
      f"backbone 골격은 그대로 써도 됩니다.")'''),

          md('''## 4) 레퍼런스 대조 — 커밋된 예측 구조와 얼마나 같은가 (본문 6.2b)

같은 서열·같은 모델이라도 실행 환경(BLAS·스레드 수)에 따라 좌표가 소수점 단위로 흔들릴 수 있어요.
그래서 "완전 동일" 이 아니라 **CA 좌표 RMSD** 와 사슬별 예측오차 통계로 비교합니다.'''),
          code('''import pathlib

RMSD_OK = 0.01      # 이 아래면 사실상 같은 구조 (본문 6.2b 실측 0.002 Å)
mine_p = pathlib.Path("my_run/demo_antibody_igfold.pdb")

if mine_p.exists():
    import pandas as pd
    from Bio.PDB import PDBParser, Superimposer
    parser = PDBParser(QUIET=True)

    def ca(path):
        return [a for a in parser.get_structure("x", str(path)).get_atoms() if a.get_id() == "CA"]

    a, b = ca(mine_p), ca("data/demo_antibody_igfold.pdb")
    print(f"CA 원자 수 — 내 결과 {len(a)} / 레퍼런스 {len(b)}")

    # 내 예측 vs 커밋 예측을 사슬별로 나란히 — 눈으로 바로 대조되게 표로 냅니다.
    stat = {}
    for label, path in [("내 결과", mine_p), ("레퍼런스", "data/demo_antibody_igfold.pdb")]:
        d = {}
        for line in open(path):
            if line.startswith("ATOM") and line[12:16].strip() == "CA":
                d.setdefault(line[21], []).append(float(line[60:66]))
        for k, v in d.items():
            stat.setdefault(k, {})[label] = (sum(v) / len(v), max(v))
    display(pd.DataFrame([
        {"사슬": k,
         "내 결과 (평균)":   f"{s.get('내 결과',   (float('nan'),))[0]:.2f} Å",
         "레퍼런스 (평균)":  f"{s.get('레퍼런스',  (float('nan'),))[0]:.2f} Å",
         "내 결과 (최대)":   f"{s.get('내 결과',   (0, float('nan')))[1]:.2f} Å",
         "레퍼런스 (최대)":  f"{s.get('레퍼런스',  (0, float('nan')))[1]:.2f} Å"}
        for k, s in sorted(stat.items())]))

    if len(a) == len(b):
        sup = Superimposer(); sup.set_atoms(b, a)
        print(f"\\nCA-RMSD (내 예측 vs 커밋 예측) = {sup.rms:.3f} Å")
        if sup.rms < RMSD_OK:
            print(f"→ {RMSD_OK:g} Å 아래 = 사실상 같은 구조. IgFold 예측은 결정론적으로 재현됩니다.")
        else:
            print(f"→ {RMSD_OK:g} Å 를 넘었어요. transformers 버전·CPU/GPU 여부부터 맞춰 보세요.")
    else:
        print("\\nCA 개수가 달라 RMSD 를 건너뜁니다 — 입력 FASTA 가 같은지 확인하세요.")
else:
    print("my_run 예측이 없어 대조를 건너뜁니다 (RUN_IGFOLD=False 였거나 실행 실패).")'''),

          md('''## 5) 3D 구조 렌더 — 예측오차로 색칠한 인라인 뷰어 (본문 6.2)

**내가 방금 예측한 구조를 노트북 안에서 바로 돌려 봅니다.** `py3Dmol`(3Dmol.js)은 pip 로 깔리고
Colab 에서도 그대로 떠요 — 드래그로 회전, 휠로 확대됩니다.

- **cartoon 색 = 3절 그래프와 똑같은 값**인 잔기별 예측오차(B-factor).
  `roygb` 그라디언트를 `min>max` 로 뒤집어 넣어 **빨강 = 오차 큼(2 Å) → 노랑 → 초록 → 파랑 = 오차 작음(0 Å)** 이에요.
- **빨간 스틱 = 3절에서 기준선 1 Å 을 넘긴 바로 그 잔기들.** 여기서 다시 세지 않고 2절이 만든 `res`·`CONF` 를 그대로 씁니다.
- 강조는 **별도 모델로 얹어요** — `H100A`·`H100B` 처럼 insertion code 가 붙은 잔기가 선택 문법에서 새는 걸 원천 차단합니다.

> IgFold 는 `do_refine=False` 로 돌아 **backbone + CB 만** 있어요. 스틱이 짧게 보이는 건 정상입니다.'''),
          code('''import importlib.util, sys, pathlib
for _pkg in ("py3Dmol", "gemmi"):        # 부트스트랩이 이미 깔지만, 이 셀만 따로 돌릴 때 대비
    if importlib.util.find_spec(_pkg) is None:
        _run(f'"{sys.executable}" -m pip -q install {_pkg}')
import py3Dmol, gemmi

view_src = pathlib.Path(pdb)               # 2절 resolve() 가 고른 바로 그 PDB
assert view_src.exists(), f"{view_src} 가 없어요 — 1~2절을 먼저 실행하세요."
WHICH = "내 결과 (my_run/)" if view_src.parts[0] == "my_run" else "레퍼런스 (data/ 커밋본)"
print(f"[3D 뷰어] 표시 대상 = {WHICH} — {view_src}")

pdb_text = gemmi.read_structure(str(view_src)).make_pdb_string()   # PDB/CIF 무엇이든 PDB 문자열로 통일
BMAX = 2.0                                 # 색 스케일 상한(Å)

# 3절에서 CONF(=1 Å)를 넘긴 그 집합 — 하드코딩이 아니라 계산된 값 그대로
hot_keys = {(ch, n, ins) for ch, v in res.items() for n, ins, b in v if b > CONF}

def sub_pdb(text, keys):
    """(chain, resSeq, iCode) 집합에 드는 원자 줄만 뽑아 작은 PDB 를 만든다 (insertion code 안전)."""
    return "".join(L for L in text.splitlines(keepends=True)
                   if L.startswith(("ATOM", "HETATM"))
                   and (L[21], int(L[22:26]), L[26].strip()) in keys)

view = py3Dmol.view(width=820, height=560)
view.addModel(pdb_text, "pdb")
view.setStyle({"model": -1},               # model:-1 = 방금 추가한 모델
              {"cartoon": {"colorscheme": {"prop": "b", "gradient": "roygb",
                                           "min": BMAX, "max": 0.0}}})
hot_text = sub_pdb(pdb_text, hot_keys)
if hot_text:
    view.addModel(hot_text, "pdb")
    view.setStyle({"model": -1}, {"stick":  {"radius": 0.28, "color": "red"},
                                  "sphere": {"radius": 0.45, "color": "red"}})
view.setBackgroundColor("white")
view.zoomTo()
view.show()

def lab(keys):                             # H96, H97 ... 번호 순으로 (문자열 정렬이면 H100 이 H96 앞에 와요)
    return [f"{c}{n}{i}" for c, n, i in sorted(keys)]

print(f"빨갛게 강조한 잔기 {len(hot_keys)}개 — " + " · ".join(lab(hot_keys))
      + f" (원자 {len(hot_text.splitlines())}개 — 0 이면 강조가 안 그려진 것)")
missing = hot_keys - {(L[21], int(L[22:26]), L[26].strip()) for L in hot_text.splitlines()}
print("좌표에서 못 찾은 잔기 — " + (" · ".join(lab(missing)) or "없음"))
print("\\n판정 — ① 빨간 스틱이 한 loop 에 몰려 있나 ② 그 자리 cartoon 도 빨강/노랑인가 "
      "③ 3절 그래프에서 라벨이 붙은 잔기와 같은 이름인가.")
print("셋이 맞으면 2D 그래프와 3D 구조가 같은 결론을 말하는 거예요. 돌려 보면 그 loop 가 "
      "구조 바깥으로 튀어나온 끝단이라는 것도 보입니다 — CDR-H3 가 길고 자유로워 예측이 어려운 이유예요.")'''),

          md('''## 5b) (선택) PyMOL 고해상도 정지 이미지

**PyMOL 은 pip 로 설치되지 않아요**(Colab 미지원) — 위 5절 인라인 뷰어가 주 시각화이고, 이 절은 덤이에요.
로컬에 PyMOL 이 있으면 **내 예측**을 다시 렌더해 `my_run/06_structure_3d.png` 로 저장하고,
없으면 저장소에 커밋된 렌더 이미지를 **레퍼런스라고 밝히고** 보여줍니다.
커밋된 `scripts/render_06_structure.pml` 은 건드리지 않고 **경로만 바꾼 사본**을 `my_run/` 에 만들어 써요.'''),
          code('''import pathlib, shutil, subprocess
from IPython.display import Image, display

def repath_pml(src, load_path, png_path, selections=None):
    """커밋된 .pml 의 load/png 경로(필요하면 select 문)만 바꾼 사본 텍스트를 만든다."""
    out = []
    for line in pathlib.Path(src).read_text().splitlines():
        s = line.strip()
        rest = ("," + line.split(",", 1)[1]) if "," in line else ""
        if s.startswith("load "):
            line = f"load {load_path}{rest}"
        elif s.startswith("png "):
            line = f"png {png_path}{rest}"
        elif selections and s.startswith("select "):
            key = s.split(",", 1)[0].split()[1]
            if key in selections:
                line = f"select {key}, {selections[key]}"
        out.append(line)
    return "\\n".join(out) + "\\n"

committed = "06_structure_3d.png"                 # 커밋본 (덮어쓰지 않아요)
mine_png = (MYRUN/"06_structure_3d.png").resolve()
shown, origin = committed, "레퍼런스(커밋된 렌더) — 내 결과가 아닙니다"
note = "PyMOL 없음(예: Colab) → 커밋된 렌더를 표시합니다. 내 구조는 5절 뷰어에서 보세요."

if shutil.which("pymol"):
    tmp_pml = MYRUN/"render_06_structure.my_run.pml"
    tmp_pml.write_text(repath_pml(ADV_ROOT/"scripts"/"render_06_structure.pml",
                                  pathlib.Path(pdb).resolve(),      # 2절이 고른 그 PDB
                                  mine_png))
    try:
        subprocess.run(["pymol", "-cq", str(tmp_pml)], cwd=str(ADV_ROOT),
                       check=True, capture_output=True, text=True, timeout=180)
        shown, origin = str(mine_png), f"내 구조 재렌더 ({view_src})"
        note = f"PyMOL 재렌더 완료 → {mine_png}"
    except Exception as e:
        note = f"PyMOL 실행 실패({type(e).__name__}) → 커밋된 렌더를 표시합니다."

print(note)
display(Image(shown))
print(f"판정 — 표시한 이미지 = {shown}  |  출처 = {origin}")'''),

          md('''## 6) 정리 — 예측 구조를 어디까지 믿나 (본문 6.3)

- 이건 **예측 구조지 실험 구조가 아니에요.** 보고서에서 결정구조처럼 단정하면 안 됩니다.
- 방금 실측한 대로 1 Å 을 넘는 불확실성은 **CDR loop 한 곳에 몰려 있어요** — 이 loop 는
  ImmuneBuilder 등으로 교차검증하고(본문 6.4), 갈리면 후보 순위를 내려요.
- 항체 단독 구조는 **항원 결합 pose 를 보장하지 않아요** → 결합은 복합체 구조로 봅니다(Ch.07).

> 다음 → 본문 [07. interface 분석](../07_interface/07_interface.md)''')]
    write_nb(ROOT/"06_structure"/"06_structure_lab.ipynb", c)


# ===========================================================================
# 07 — interface lab : 1A14 를 직접 내려받아 contact 계산
# ===========================================================================
def nb_07():
    c = header("07_interface", "07_interface.md", "07 — 항원-항체 interface (1A14 직접 다운로드)",
               "RCSB 에서 1A14 를 **직접 내려받아** contact 을 계산하고(`my_run/`), 커밋된 결과와 대조해요.")
    c += [bootstrap("07_interface", pip_pkgs="pandas matplotlib biopython requests py3Dmol gemmi"),

          md('''## 1) 직접 실행 — 복합체 다운로드 + contact 계산 (본문 7.2)

```bash
python scripts/pdb_contacts.py --pdb 1A14 --outdir my_run/pdb                       # ① 사슬 목록 확인
python scripts/pdb_contacts.py --pdb 1A14 --chain1 H --chain2 N --cutoff 4.0 \\
    --outdir my_run/pdb --out my_run/contacts_H_N.tsv                                # ② 항원-항체
```
① 을 먼저 돌려 **사슬 ID 를 눈으로 확인**하는 게 핵심이에요 — 1A14 의 항원(neuraminidase)은 chain **N** 이에요.
`--chain2 L` 로 바꾸면 항원이 아니라 **VH–VL packing** 을 보게 됩니다(전혀 다른 분석).
네트워크가 막히면 `--fallback-cif` 로 커밋된 `data/pdb/1A14.cif` 를 씁니다(오프라인 대비).'''),
          code('''import pathlib, pandas as pd
from IPython.display import display

FALLBACK = ["--fallback-cif", "data/pdb/1A14.cif"]   # 다운로드 실패 시 커밋본 사용
CUTOFF = 4.0                                        # 본문 7.1 의 기본 cutoff

# ① 사슬 목록 먼저 — 어떤 사슬이 들어 있는지 눈으로 확인하고 나서 짝을 고릅니다.
run_tool([PY, SCRIPTS/"pdb_contacts.py", "--pdb", "1A14", "--outdir", "my_run/pdb", *FALLBACK])

# ② 짝별 contact 계산. 같은 CIF 를 재사용하니 두 번째부터는 [cache] 로 떠요.
PAIRS = [("H", "N", "항원-항체 — VH ↔ neuraminidase (본문이 보는 것)"),
         ("H", "L", "VH-VL packing — 같은 항체 내부 (대조군)")]

runs = []
for c1, c2, what in PAIRS:
    out = f"my_run/contacts_{c1}_{c2}.tsv"
    ok = run_tool([PY, SCRIPTS/"pdb_contacts.py", "--pdb", "1A14",
                   "--chain1", c1, "--chain2", c2, "--cutoff", str(CUTOFF),
                   "--outdir", "my_run/pdb", "--out", out, *FALLBACK])
    hits = [l for l in open(out)] if ok and pathlib.Path(out).exists() else []
    hits = [l for l in hits if "atom_contacts=" in l]
    runs.append({"짝": f"{c1}–{c2}", "무엇을 보는가": what, "잔기 pair": len(hits),
                 "atom contact": sum(int(l.rsplit("=", 1)[1]) for l in hits),
                 "결과 파일": out if hits else "실패 — 뒤 절은 data/ 로 이어갑니다"})

print(f"\\ncutoff {CUTOFF} Å 로 계산한 두 짝")
display(pd.DataFrame(runs))
print("H–L 이 H–N 보다 pair 가 많은 건 정상이에요 — VH-VL 은 늘 맞물려 있는 내부 packing 이라,")
print("접촉이 많다고 결합이 강한 게 아닙니다. 우리가 볼 건 H–N 쪽이에요.")'''),

          md('''## 2) 내 결과 확인 — paratope · epitope 집합과 CDR 귀속 (본문 7.3)

pair 개수만으로는 "어느 잔기가 붙었나" 를 말할 수 없어요. **paratope·epitope 잔기 집합**을 직접 뽑고,
paratope 이 정말 CDR 에 몰려 있는지 Kabat 구간으로 판정합니다.'''),
          code('''import pandas as pd
from IPython.display import display

KABAT_H = [("CDR-H1", 31, 35), ("CDR-H2", 50, 65), ("CDR-H3", 95, 102)]   # Kabat 정의

def parse_contacts(path):
    """pdb_contacts.py TSV → [(잔기1, 잔기2, atom_contacts)]. 잔기 라벨은 'ASN H:54' 꼴."""
    rows = []
    for line in open(path):
        if "atom_contacts=" not in line:
            continue
        left, n = line.rstrip().split("atom_contacts=")
        a, b = left.rstrip("\\t").split("\\t")
        rows.append((a.strip(), b.strip(), int(n)))
    return rows

def chain_of(label):
    return label.split()[-1].split(":")[0]          # 'ASN H:54' → 'H'

def resi_of(label):
    return label.split(":")[-1]                     # 'TYR H:100A' → '100A' (insertion code 포함)

def resi_key(resi):
    num = "".join(ch for ch in resi if ch.isdigit())
    return (int(num) if num else 0, "".join(ch for ch in resi if ch.isalpha()))

def load_contacts(path, left_role="paratope", right_role="epitope"):
    """역할 이름은 인자로 받고, 사슬 ID 는 파일에서 읽어 컬럼 라벨을 만든다."""
    rows = parse_contacts(path)
    c1 = chain_of(rows[0][0]) if rows else "?"
    c2 = chain_of(rows[0][1]) if rows else "?"
    return pd.DataFrame(rows, columns=[f"{left_role} ({c1})", f"{right_role} ({c2})", "atom_contacts"])

def residues(series):
    return sorted({resi_of(x) for x in series}, key=resi_key)

def cdr_of(resi):
    num = int("".join(ch for ch in resi if ch.isdigit()) or 0)
    for name, lo, hi in KABAT_H:
        if lo <= num <= hi:
            return name
    return "FR"

hn_path = resolve("contacts_H_N.tsv")
hn = load_contacts(hn_path).sort_values("atom_contacts", ascending=False).reset_index(drop=True)
pcol, ecol = hn.columns[0], hn.columns[1]
ab_chain, ag_chain = chain_of(hn[pcol].iloc[0]), chain_of(hn[ecol].iloc[0])

print(f"항원-항체 contact ({CUTOFF} Å) — {len(hn)} residue pairs · "
      f"총 {hn['atom_contacts'].sum()} atom contacts")
display(hn)                                          # 15행 전부 (잘라내지 않아요)

para, epi = residues(hn[pcol]), residues(hn[ecol])
print(f"paratope ({ab_chain}) {len(para)}개 —", " · ".join(ab_chain + r for r in para))
print(f"epitope  ({ag_chain}) {len(epi)}개 —", " · ".join(ag_chain + r for r in epi))

cdr_tab = pd.DataFrame({"paratope": [ab_chain + r for r in para],
                        "region": [cdr_of(r) for r in para],
                        "atom_contacts": [int(hn.loc[hn[pcol].map(resi_of) == r, "atom_contacts"].sum())
                                          for r in para]})
display(cdr_tab)
n_cdr = int((cdr_tab["region"] != "FR").sum())
vc = cdr_tab["region"].value_counts()
print("CDR 분포 —", " · ".join(f"{k} {v}개" for k, v in sorted(vc.items())))
if n_cdr == len(para):
    print(f"→ paratope {len(para)}개가 하나도 빠짐없이 CDR 안이에요. 이론대로 CDR 이 결합을 주도합니다.")
else:
    print(f"→ paratope {len(para)}개 중 CDR {n_cdr}개 · FR {len(para) - n_cdr}개. "
          f"FR 접촉 잔기는 humanization 때 보존 후보로 따로 표시하세요.")

hl = load_contacts(resolve("contacts_H_L.tsv"), "VH", "VL")
print(f"\\n비교) 항원 H–{ag_chain} = {len(hn)} pairs / {hn['atom_contacts'].sum()} atom contacts "
      f"vs VH–VL packing = {len(hl)} pairs / {hl['atom_contacts'].sum()} atom contacts")
print("같은 구조·같은 cutoff 인데 '무엇 대 무엇'이냐로 결과가 완전히 달라져요 — "
      "보고서에는 chain 쌍을 반드시 적으세요.")'''),

          md('''## 3) 내 결과 확인 — interface contact 그래프 (본문 7.3)

막대가 긴(원자 접촉이 많은) 잔기일수록 affinity maturation·humanization 에서 **함부로 바꾸면 안 되는
hot-spot** 이에요. 2절 표의 상위 행이 그대로 막대 위쪽에 옵니다.'''),
          code('''from antibody_viz import interface_contacts
from IPython.display import Image, display

png = "my_run/07_interface_contacts.png"
interface_contacts(hn_path,                          # 2절이 고른 그 TSV
                   f"Antibody({ab_chain})–Antigen({ag_chain}) contacts — 1A14 "
                   f"(≤{CUTOFF} Å, 내 실행 결과)", png)
display(Image(png))

top = hn.iloc[0]
print(f"가장 긴 막대 = {top[pcol]} ↔ {top[ecol]} ({top['atom_contacts']} atom contacts, "
      f"{cdr_of(resi_of(top[pcol]))})")
print(f"상위 3쌍이 전체 {hn['atom_contacts'].sum()} atom contacts 중 "
      f"{hn['atom_contacts'].head(3).sum()}개 — 접촉이 소수 잔기에 몰릴수록 그 잔기의 변이 위험이 커요.")'''),

          md('''## 4) 레퍼런스 대조 — 커밋된 contact 결과와 같은가

내가 받은 CIF 로 계산한 pair 집합이 커밋된 `data/contacts_H_N.tsv` 와 같은지 봅니다.
같으면 다운로드·파싱·거리계산이 모두 재현된 거예요.'''),
          code('''import pathlib

mine_p = pathlib.Path("my_run/contacts_H_N.tsv")
if mine_p.exists():
    mine = {(a, b): n for a, b, n in parse_contacts(mine_p)}
    ref = {(a, b): n for a, b, n in parse_contacts("data/contacts_H_N.tsv")}
    print(f"내 결과 {len(mine)} pairs / 레퍼런스 {len(ref)} pairs")

    only_mine, only_ref = sorted(set(mine) - set(ref)), sorted(set(ref) - set(mine))
    diff_n = {k: (mine[k], ref[k]) for k in set(mine) & set(ref) if mine[k] != ref[k]}
    if only_mine or only_ref or diff_n:
        display(pd.DataFrame(
            [{"pair": f"{a} ↔ {b}", "차이": "내 결과에만 있음",
              "내 결과": mine[(a, b)], "레퍼런스": "-"} for a, b in only_mine]
            + [{"pair": f"{a} ↔ {b}", "차이": "레퍼런스에만 있음",
                "내 결과": "-", "레퍼런스": ref[(a, b)]} for a, b in only_ref]
            + [{"pair": f"{a} ↔ {b}", "차이": "원자접촉 수가 다름",
                "내 결과": m, "레퍼런스": r} for (a, b), (m, r) in sorted(diff_n.items())]))
    else:
        print("어긋난 pair 없음 — 빠진 것도, 더 생긴 것도, 접촉 수가 다른 것도 0개예요.")

    if mine == ref:
        print("→ pair 집합과 접촉 수가 완전히 일치. 재현 성공이에요.")
    else:
        print("→ 차이가 있어요. 같은 PDB entry·같은 cutoff 를 썼는지, "
              "구조 버전이 갱신되지 않았는지 확인하세요.")
else:
    print("my_run contact 결과가 없어 대조를 건너뜁니다.")'''),

          md('''## 5) cutoff 를 바꾸면 얼마나 달라지나 (본문 7.1)

본문 7.1 이 말하는 대로 **4 Å 은 시작점**이에요. contact 수는 결합의 세기가 아니고,
H-bond geometry·buried surface area(BSA)·shape complementarity 는 FreeSASA·PLIP 같은
**별도 도구**의 몫입니다(본문 7.4). cutoff 를 0.5 Å 만 늘려도 결과가 얼마나 움직이는지 직접 재 봐요.'''),
          code('''CUT2 = 4.5
out2 = f"my_run/contacts_H_N_{CUT2}.tsv"
run_tool([PY, SCRIPTS/"pdb_contacts.py", "--pdb", "1A14",
          "--chain1", "H", "--chain2", ag_chain, "--cutoff", str(CUT2),
          "--outdir", "my_run/pdb", "--out", out2, *FALLBACK])

if pathlib.Path(out2).exists():
    wide = load_contacts(out2)
    e1, e2 = set(residues(hn[ecol])), set(residues(wide[wide.columns[1]]))
    p1, p2 = set(residues(hn[pcol])), set(residues(wide[wide.columns[0]]))
    n1, n2 = int(hn["atom_contacts"].sum()), int(wide["atom_contacts"].sum())
    print(f"\\ncutoff 만 {CUTOFF} → {CUT2} Å 로 바꿔서 같은 짝(H–{ag_chain})을 다시 계산했어요.")
    display(pd.DataFrame([
        {"cutoff (Å)": CUTOFF, "잔기 pair": len(hn), "atom contact": n1,
         "epitope 잔기": len(e1), "paratope 잔기": len(p1)},
        {"cutoff (Å)": CUT2, "잔기 pair": len(wide), "atom contact": n2,
         "epitope 잔기": len(e2), "paratope 잔기": len(p2)},
    ]))
    print("0.5 Å 늘렸을 때 새로 들어온 잔기")
    print("  epitope  — " + (" · ".join(sorted(e2 - e1, key=resi_key)) or "없음"))
    print("  paratope — " + (" · ".join(sorted(p2 - p1, key=resi_key)) or "없음"))
    print(f"→ 0.5 Å 차이로 pair 가 {len(hn)}→{len(wide)}, atom contact 가 {n1}→{n2} 로 움직여요.")
    print("   epitope 목록을 인용할 때는 cutoff 를 반드시 함께 적어야 비교가 성립합니다.")
else:
    print(f"{CUT2} Å 재계산 결과가 없어 이 절을 건너뜁니다.")'''),

          md('''## 6) 복합체 3D 렌더 — paratope / epitope 인라인 뷰어 (본문 7.3)

**내가 받은 그 구조를 노트북 안에서 바로 돌려 봅니다**(py3Dmol, Colab 그대로 동작).

- cartoon 색 — 항원(베이지) · 항체 H(하늘) · L(연두)
- **주황 스틱 = 2절이 계산한 paratope · 빨간 스틱 = 2절이 계산한 epitope.**
  잔기 번호를 여기 적어 두지 않고 앞 셀의 `para`·`epi` 변수를 그대로 씁니다 —
  cutoff 를 바꿔 다시 돌리면 **그림도 따라 바뀌어요**(예전 `.pml` 은 고정 selection 이라 계산 결과와 어긋났어요).
- 강조는 **별도 모델로 얹습니다** — `H100A`·`H100B` 처럼 insertion code 가 붙은 잔기가
  `resi` 선택에서 새는 걸 원천 차단하고, 아래에서 "못 찾은 잔기 0개"까지 확인합니다.

뷰어는 두 개예요 — **① 복합체 전체**(어느 사슬이 어디 붙었는지) **② 인터페이스 확대**(스틱이 맞물리는 모습).'''),
          code('''import importlib.util, sys, pathlib
for _pkg in ("py3Dmol", "gemmi"):        # 부트스트랩이 이미 깔지만, 이 셀만 따로 돌릴 때 대비
    if importlib.util.find_spec(_pkg) is None:
        _run(f'"{sys.executable}" -m pip -q install {_pkg}')
import py3Dmol, gemmi

cif = pathlib.Path(resolve("pdb/1A14.cif"))          # my_run 우선, 없으면 커밋본
assert cif.exists(), f"{cif} 가 없어요 — 1절을 먼저 실행하세요."
WHICH = "내 결과 (my_run/)" if cif.parts[0] == "my_run" else "레퍼런스 (data/ 커밋본)"
print(f"[3D 뷰어] 표시 대상 = {WHICH} — {cif}")

st = gemmi.read_structure(str(cif)); st.setup_entities()
cx = st.make_pdb_string()                            # CIF → PDB 문자열 (3Dmol.js 가 가장 안정적)

def keys_of(chain, resis):
    """['52','100A',...] → {(chain, 52, ''), (chain, 100, 'A'), ...}  insertion code 보존"""
    out = set()
    for r in resis:
        out.add((chain, int("".join(c for c in r if c.isdigit()) or 0),
                 "".join(c for c in r if c.isalpha())))
    return out

def sub_pdb(text, keys):
    return "".join(L for L in text.splitlines(keepends=True)
                   if L.startswith(("ATOM", "HETATM"))
                   and (L[21], int(L[22:26]), L[26].strip()) in keys)

para_keys, epi_keys = keys_of(ab_chain, para), keys_of(ag_chain, epi)   # 2절 계산 결과 그대로
para_pdb,  epi_pdb  = sub_pdb(cx, para_keys), sub_pdb(cx, epi_keys)
others = sorted({L[21] for L in cx.splitlines() if L.startswith("ATOM")} - {ab_chain, ag_chain})

def build(width=860, height=580):
    """복합체 cartoon + paratope/epitope 스틱. 반환값 = (view, 강조 모델 인덱스)"""
    v = py3Dmol.view(width=width, height=height)
    v.addModel(cx, "pdb")
    v.setStyle({"model": -1}, {"cartoon": {"color": "lightgrey"}})
    v.setStyle({"model": -1, "chain": ag_chain}, {"cartoon": {"color": "wheat"}})
    v.setStyle({"model": -1, "chain": ab_chain}, {"cartoon": {"color": "skyblue"}})
    for ch in others:
        v.setStyle({"model": -1, "chain": ch}, {"cartoon": {"color": "palegreen"}})
    idx, n = [], 1
    for text, scheme in ((epi_pdb, "redCarbon"), (para_pdb, "orangeCarbon")):
        if text:
            v.addModel(text, "pdb")
            v.setStyle({"model": -1}, {"stick": {"radius": 0.28, "colorscheme": scheme}})
            idx.append(n); n += 1
    v.setBackgroundColor("white")
    return v, idx

v1, hl = build()
v1.zoomTo()                                          # ① 복합체 전체
v1.show()

v2, hl2 = build(height=520)
v2.zoomTo({"model": hl2} if hl2 else {})             # ② 인터페이스 확대 (강조 모델에 맞춤)
v2.show()

print(f"사슬 색 — 항원 {ag_chain}(베이지) · 항체 {ab_chain}(하늘) · {others}(연두)")
print(f"주황 스틱 paratope {len(para)}개 — " + " · ".join(ab_chain + r for r in para))
print(f"빨간 스틱 epitope  {len(epi)}개 — " + " · ".join(ag_chain + r for r in epi))
found = {(L[21], int(L[22:26]), L[26].strip()) for L in (para_pdb + epi_pdb).splitlines()}
missing = (para_keys | epi_keys) - found
print(f"강조에 들어간 원자 = paratope {len(para_pdb.splitlines())}개 · epitope {len(epi_pdb.splitlines())}개 | "
      f"좌표에서 못 찾은 잔기 = {[f'{c}{n}{i}' for c, n, i in sorted(missing)] or '없음'}")
print("\\n판정 — ① 주황 스틱이 빨간 패치로 파고드는가 ② 빨간 잔기가 항원 표면 한 자리에 모여 있는가"
      "(모여 있으면 conformational epitope) ③ 위 목록이 2절 표의 잔기와 같은가.")'''),

          md('''## 6b) (선택) PyMOL 고해상도 정지 이미지

**PyMOL 은 pip 로 설치되지 않아요**(Colab 미지원) — 6절 인라인 뷰어가 주 시각화이고 이 절은 덤이에요.
PyMOL 이 있으면 내가 받은 CIF 로 다시 렌더해 `my_run/07_complex_3d.png` 로 저장하고,
없으면 커밋된 렌더를 **레퍼런스라고 밝히고** 보여줍니다.
커밋된 `scripts/render_07_complex.pml` 은 건드리지 않고 **경로·selection 만 바꾼 사본**을 써요.'''),
          code('''import shutil, subprocess

def repath_pml(src, load_path, png_path, selections=None):
    """커밋된 .pml 의 load/png 경로와 select 문만 바꾼 사본 텍스트를 만든다."""
    out = []
    for line in pathlib.Path(src).read_text().splitlines():
        s = line.strip()
        rest = ("," + line.split(",", 1)[1]) if "," in line else ""
        if s.startswith("load "):
            line = f"load {load_path}{rest}"
        elif s.startswith("png "):
            line = f"png {png_path}{rest}"
        elif selections and s.startswith("select "):
            key = s.split(",", 1)[0].split()[1]
            if key in selections:
                line = f"select {key}, {selections[key]}"
        out.append(line)
    return "\\n".join(out) + "\\n"

committed = "07_complex_3d.png"                   # 커밋본 (덮어쓰지 않아요)
mine_png = (MYRUN/"07_complex_3d.png").resolve()
shown, origin = committed, "레퍼런스(커밋된 렌더) — 내 계산 결과가 아닙니다"
note = "PyMOL 없음(예: Colab) → 커밋된 렌더를 표시합니다. 내 결과는 6절 뷰어에서 보세요."

if shutil.which("pymol"):
    sel = {"para": f"chain {ab_chain} and resi " + "+".join(para),
           "epi":  f"chain {ag_chain} and resi " + "+".join(epi)}
    tmp_pml = MYRUN/"render_07_complex.my_run.pml"
    tmp_pml.write_text(repath_pml(ADV_ROOT/"scripts"/"render_07_complex.pml",
                                  cif.resolve(), mine_png, selections=sel))   # 6절이 고른 그 CIF
    print("selection —", sel)
    try:
        subprocess.run(["pymol", "-cq", str(tmp_pml)], cwd=str(ADV_ROOT),
                       check=True, capture_output=True, text=True, timeout=180)
        shown, origin = str(mine_png), f"내 계산 결과로 재렌더 ({cif})"
        note = f"PyMOL 재렌더 완료 → {mine_png}"
    except Exception as e:
        note = f"PyMOL 실행 실패({type(e).__name__}) → 커밋된 렌더를 표시합니다."

print(note)
display(Image(shown))
print(f"판정 — 표시한 이미지 = {shown}  |  출처 = {origin}")'''),

          md("> 다음 → 본문 [08. developability](../08_developability/08_developability.md)")]
    write_nb(ROOT/"07_interface"/"07_interface_lab.ipynb", c)


# ===========================================================================
# 08 — developability lab : liability scan 직접 실행
# ===========================================================================
def nb_08():
    c = header("08_developability", "08_developability.md", "08 — developability (liability scan 직접 실행)",
               "`liability_scan.py` 를 **직접 돌려** 스캔 결과를 `my_run/` 에 만들고 커밋본과 대조해요.",
               prev="Ch.04 numbering")
    c += [bootstrap("08_developability", pip_pkgs="pandas matplotlib biopython"),
          md('''## 1) 직접 실행 — liability scan (본문 8.1)

```bash
python scripts/liability_scan.py data/demo_mab.fa --out my_run/liability.csv
```
motif 정규식 4종(N-glyc sequon `N-X-S/T` · deamidation `NG`·`NS` · isomerization `DG`)과
pI·GRAVY·Cys 홀짝·Met/Trp 개수를 한 번에 계산해요.
motif 컬럼에는 **hit 위치(1-based, 세미콜론 구분)** 가 들어가고, hit 이 없으면 빈 칸입니다.'''),
          code('''ok = run_tool([PY, SCRIPTS/"liability_scan.py", "data/demo_mab.fa",
               "--out", "my_run/liability.csv"])
print("→ my_run/liability.csv 가 생겼어요. 2절부터 이 파일을 읽습니다." if ok
      else "→ 실패했어요. 뒤 절은 커밋된 data/ 로 이어갑니다.")'''),
          md('''## 2) 내 결과 확인 — 물리화학·Cys·산화 지표 (본문 8.2)

**값이 하나라도 채워진 컬럼만** 표에 세웁니다. 두 사슬 모두 빈 컬럼을 그대로 보여주면
"측정했는데 0" 인지 "아예 비어 있는지"를 구분할 수 없거든요.'''),
          code('''import pandas as pd
df = pd.read_csv(resolve("liability.csv"))

PHYS  = ["id", "length", "molecular_weight", "pI", "gravy", "cysteine_count",
         "odd_cysteine_flag", "methionine_count", "tryptophan_count", "ambiguous_residues"]
MOTIF = ["N_glycosylation_NXS_T", "deamidation_NG", "deamidation_NS", "isomerization_DG"]

def filled(frame, wanted):
    """있는 컬럼 중 값이 하나라도 채워진 것만 고른다(전부 빈 컬럼은 표에서 뺀다)."""
    out = []
    for col in wanted:
        if col not in frame.columns:
            continue
        v = frame[col].astype(str).str.strip().str.lower()
        if ((v != "") & (v != "nan")).any():
            out.append(col)
    return out

def num(row, col):
    try:
        return float(row[col])
    except Exception:
        return None

shown = filled(df, PHYS)
display(df[shown])
missing = [x for x in PHYS if x not in df.columns]
empty   = [x for x in PHYS if x in df.columns and x not in shown]
if missing: print("CSV 에 없는 컬럼:", ", ".join(missing))
if empty:   print("값이 전부 비어 표에서 뺀 컬럼:", ", ".join(empty))

for _, r in df.iterrows():
    bits = []
    cys = num(r, "cysteine_count")
    if cys is not None:
        bits.append(f"Cys {int(cys)}개 " + ("짝수 → disulfide 짝맞음"
                                            if int(cys) % 2 == 0 else
                                            "홀수 → unpaired cysteine (mispairing·응집 위험)"))
    met, trp = num(r, "methionine_count"), num(r, "tryptophan_count")
    if met is not None and trp is not None:
        bits.append(f"산화 후보 Met {int(met)} + Trp {int(trp)} = {int(met) + int(trp)}개")
    pi = num(r, "pI")
    if pi is not None:
        bits.append(f"pI {pi:.2f} ({'산성' if pi < 7 else '염기성'})")
    gr = num(r, "gravy")
    if gr is not None:
        bits.append(f"GRAVY {gr:+.3f} ({'친수성' if gr < 0 else '소수성'})")
    print(f"{r.get('id', '?')}:", " | ".join(bits))

odd = int(sum(1 for _, r in df.iterrows()
              if num(r, "cysteine_count") is not None and int(num(r, "cysteine_count")) % 2 == 1))
print(f"\\n홀수 Cys 사슬 {odd}개 / 전체 {len(df)}개 — "
      + ("0개면 unpaired cysteine 위험 없음" if odd == 0
         else "1개 이상이면 mispairing·응집을 의심하고 어느 Cys 가 남는지 찾아야 해요"))
if "pI" in df.columns and len(df) > 1:
    spread = float(df["pI"].max()) - float(df["pI"].min())
    print(f"사슬 간 pI 차 {spread:.2f} — 1.0 이상이면 사슬 전하가 서로 반대쪽이라 "
          "charge symmetry(SFvCSP)를 구조 기반 도구로 따로 봐야 해요 (본문 8.3)")'''),
          md('''## 3) liability motif — 몇 건이고 CDR 안인가 (본문 8.2)

본문 8.2 요약은 **"CDR 안에 산화·glyc·불안정 motif 가 몰리면 임상으로 가기 어렵다"** 고 해요.
그래서 hit 수만 세지 않고 **위치를 IMGT 번호로 바꿔 CDR/framework 에 귀속**합니다.
번호는 Ch.04 가 만든 numbering CSV 를 그대로 재활용해요(같은 서열일 때만 — 다르면 귀속을 생략합니다).'''),
          code('''import csv, pandas as pd

ALPHA = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
IMGT_CDR = {"CDR1": (27, 38), "CDR2": (56, 65), "CDR3": (105, 117)}   # IMGT CDR 정의

def read_fasta(path):
    d, n = {}, None
    for line in open(path):
        line = line.strip()
        if line.startswith(">"): n = line[1:].split()[0]; d[n] = ""
        elif n: d[n] += line
    return d

def imgt_positions(seq_id, seq):
    """Ch.04 numbering CSV → {서열 1-based 위치: IMGT 번호}. 서열이 다르면 (None, None)."""
    for fname in ("demo_imgt_H.csv", "demo_imgt_KL.csv"):
        for sub in ("my_run", "data"):
            p = ADV_ROOT / "04_numbering" / sub / fname
            if not p.exists():
                continue
            for row in csv.DictReader(open(p)):
                if row.get("Id") != seq_id:
                    continue
                start = int(row.get("seqstart_index") or 0)
                pos, built, i = {}, [], start
                for col in row:
                    key = str(col).strip()
                    if not key[:1].isdigit():        # 'Id'·'v_gene' 등 메타 컬럼은 건너뜀
                        continue
                    v = (row[col] or "").strip()
                    if v and v != "-":               # '-' 는 IMGT 갭
                        pos[i + 1] = int(key.rstrip(ALPHA))   # '111A' → 111 (insertion code)
                        built.append(v); i += 1
                if "".join(built) == seq[start:i]:
                    return pos, str(p)
    return None, None

def region_of(imgt_no):
    for name, (lo, hi) in IMGT_CDR.items():
        if lo <= imgt_no <= hi:
            return name
    return "framework"

seqs  = read_fasta("data/demo_mab.fa")
mcols = [m for m in MOTIF if m in df.columns]
hits  = []
for _, r in df.iterrows():
    for m in mcols:
        for q in str(r[m]).split(";"):
            if q.strip().isdigit():
                hits.append((r["id"], int(q), m))

print("검사한 motif:", ", ".join(m.replace("_", " ") for m in mcols) or "(컬럼 없음)")
print(f"총 hit {len(hits)}건")

if not hits:
    print("→ motif hit 0건이라 CDR/framework 로 귀속할 대상이 없어요. "
          "스캐너가 안 도는 게 아니라 이 후보에 hit 이 없는 거예요 (5절에서 검출되는 서열로 확인합니다).")
else:
    rows, no_number = [], []
    for sid in sorted({h[0] for h in hits}):
        pos_map, src = imgt_positions(sid, seqs.get(sid, ""))
        if pos_map is None:
            no_number.append(sid)
        else:
            print(f"[{sid} 번호 출처] {src}")
        for _sid, p, m in sorted(h for h in hits if h[0] == sid):
            imgt = pos_map.get(p) if pos_map else None
            rows.append({"id": sid, "pos": p, "residues": seqs.get(sid, "")[p - 1:p + 2],
                         "motif": m, "IMGT": imgt if imgt else "-",
                         "region": region_of(imgt) if imgt else "번호 없음"})
    hit_df = pd.DataFrame(rows)
    display(hit_df)
    if no_number:
        print("Ch.04 numbering 과 서열이 달라 IMGT 귀속을 못 한 사슬:", ", ".join(no_number),
              "→ Ch.04 노트북을 같은 FASTA 로 먼저 돌리면 채워집니다")
    in_cdr = int(hit_df["region"].isin(list(IMGT_CDR)).sum())
    fr     = int((hit_df["region"] == "framework").sum())
    print(f"CDR 안 {in_cdr}건 / framework {fr}건 / 번호 없음 {len(hit_df) - in_cdr - fr}건")
    print("판정 — " + ("CDR 안 hit 은 결합 부위 자체가 화학적으로 변할 수 있어 우선 처리 대상이에요."
                     if in_cdr else
                     "CDR 안 hit 0건 — framework hit 은 제조·보관 조건에서 다시 보되 결합력 위험은 낮아요."))'''),
          md('''## 4) 내 결과 확인 — developability 개요 그래프 (본문 8.2)

2×2 패널 — 좌상 pI(주황, pH 7 기준선) · 우상 GRAVY(청록, 0 기준선) ·
좌하 Cys 개수(보라, 짝수면 짝맞음) · 우하 liability motif 누적 막대.'''),
          code('''from antibody_viz import liability_overview
from IPython.display import Image, display

png = "my_run/08_liability_overview.png"
liability_overview(resolve("liability.csv"),
                   "Developability — liability scan (demo mAb, 내 실행 결과)", png)
display(Image(png))

def panel(col, fmt):
    if col not in df.columns:
        return "(컬럼 없음)"
    out = []
    for _, r in df.iterrows():
        v = num(r, col)
        out.append(f"{r.get('id', '?')} " + (fmt.format(v) if v is not None else "-"))
    return " · ".join(out)

print("좌상 pI —",    panel("pI", "{:.2f}"))
print("우상 GRAVY —", panel("gravy", "{:+.3f}"))
print("좌하 Cys —",   panel("cysteine_count", "{:.0f}"))
if not hits:
    print(f"우하 motif 패널은 막대 없이 범례만 보여요 — 쌓을 값이 {len(hits)}건이기 때문이에요. "
          "빈 축 = 그리기 실패가 아니라 hit 0건이라는 뜻입니다.")
    print("판정 — 여러분 서열로 바꿔 돌려서 우하에 막대가 솟으면, 3절의 CDR/framework 귀속부터 확인하세요.")
else:
    print(f"우하 motif 패널 막대 높이 합 = {len(hits)}건 (사슬별로 누적).")
    print("판정 — 막대가 있는 사슬은 3절 표에서 그 hit 이 CDR 안인지부터 보세요.")'''),
          md('''## 5) 입력 robustness — 모호 잔기(X/B/Z)가 섞여도 죽는가 (본문 8.1)

본문 8.1 은 QC 입력에 `X`·`B`·`Z` 가 섞이면 Biopython `ProteinAnalysis` 가 예외로 죽는 문제를
`liability_scan.py` 가 `ambiguous_residues` 컬럼으로 분리해 해결했다고 해요.
demo 서열에는 모호 잔기가 없어 그 컬럼이 비어 있었으니, **일부러 X·B·Z 와 홀수 Cys, motif 4종을 전부 넣은
짧은 합성 서열**로 확인합니다. 위 판정 코드가 "깨끗하지 않은" 입력에서도 맞는 말을 하는지 같이 봐요.'''),
          code('''import pathlib, pandas as pd

edge_fa = pathlib.Path("my_run/edge_case.fa")
edge_fa.write_text(">edge_case\\nDIQMTQNGSCNSTDGKXBZWCVQLC\\n")   # X·B·Z + Cys 3개(홀수) + motif 4종
run_tool([PY, SCRIPTS/"liability_scan.py", str(edge_fa), "--out", "my_run/liability_edge.csv"])

edge_csv = pathlib.Path("my_run/liability_edge.csv")
if not edge_csv.exists():
    print("합성 서열 스캔 산출물이 없어요 → 위 실행 로그를 확인하세요 (biopython 설치 여부).")
else:
    edge = pd.read_csv(edge_csv)
    display(edge[filled(edge, PHYS + MOTIF)])
    r = edge.iloc[0]
    ecys = int(r["cysteine_count"])
    ehits = sum(1 for m in MOTIF if m in edge.columns
                for q in str(r[m]).split(";") if q.strip().isdigit())
    print(f"모호 잔기 {r['ambiguous_residues']} 가 섞여 있어도 예외 없이 "
          f"pI {float(r['pI']):.2f} · GRAVY {float(r['gravy']):+.3f} 가 나왔어요 (표준 20종만으로 계산).")
    print(f"Cys {ecys}개 → " + ("짝수" if ecys % 2 == 0 else "홀수 = unpaired cysteine 경고")
          + f" | motif hit {ehits}건")
    print("판정 — 같은 코드가 demo 에서는 "
          f"{len(hits)}건, 이 합성 서열에서는 {ehits}건이라고 말해요. 판정문이 입력을 따라간다는 확인이에요.")'''),
          md('''## 6) 이 스캔이 재는 축과 못 재는 축 (본문 8.1 · 8.3)

본문 8.1 은 developability 위험을 7종으로 정리했고, 본문 8.3 은 임상 분포와 비교하는 **TAP 5축**을 소개해요.
TAP 는 ABodyBuilder2 구조 + 임상 항체 분포가 필요해서 이 노트북(서열 전용)에서는 못 돌립니다.
무엇을 재고 무엇을 못 쟀는지 밝히는 것까지가 보고서예요.'''),
          code('''import pandas as pd
have = set(df.columns)

def cover(cols):
    return "O" if cols and all(x in have for x in cols) else "X"

risk = pd.DataFrame([
    ["Aggregation",       "hydrophobic patch·SAP", "gravy (사슬 평균 — patch 아님)",
     "부분" if "gravy" in have else "X"],
    ["Deamidation",       "motif regex",  "deamidation_NG, deamidation_NS",
     cover(["deamidation_NG", "deamidation_NS"])],
    ["Isomerization",     "motif regex",  "isomerization_DG",        cover(["isomerization_DG"])],
    ["Oxidation",         "Met/Trp count", "methionine_count, tryptophan_count",
     cover(["methionine_count", "tryptophan_count"])],
    ["N-glycosylation",   "N-X-S/T sequon", "N_glycosylation_NXS_T", cover(["N_glycosylation_NXS_T"])],
    ["Unpaired cysteine", "Cys 홀짝",     "cysteine_count, odd_cysteine_flag",
     cover(["cysteine_count", "odd_cysteine_flag"])],
    ["Charge/pI",         "pI 계산",      "pI",                      cover(["pI"])],
], columns=["본문 8.1 위험", "본문이 말한 스캔 방법", "이 CSV 의 컬럼", "이 노트북"])
display(risk)

tap = pd.DataFrame([
    ["CDR length",                    "부분 — 길이 자체는 Ch.04·Ch.09 에서 계산(임상 분포 대비는 못 함)"],
    ["Surface hydrophobicity (PSH)",  "X — 구조 표면 필요"],
    ["Patches of positive charge (PPC)", "X — 구조 표면 필요"],
    ["Patches of negative charge (PNC)", "X — 구조 표면 필요"],
    ["Heavy/light charge symmetry (SFvCSP)", "X — 구조 필요 (2절의 사슬 간 pI 차는 방향만 보는 신호)"],
], columns=["본문 8.3 TAP 5축", "이 노트북"])
display(tap)

full = int((risk["이 노트북"] == "O").sum())
print(f"판정 — 본문 8.1 의 7개 위험 중 {full}개는 서열만으로 확정, "
      f"{7 - full}개는 구조가 있어야 해요. TAP 5축은 0/5 — 이 노트북 결과만으로 "
      "\\"developability 통과\\"라고 쓰면 과장이에요.")
print("보완 경로 — TAP(웹) · aggregation predictor · hydrophobic/charge patch 시각화 · "
      "T-cell epitope 예측 (본문 8.3)")'''),
          md("## 7) 레퍼런스 대조 — 커밋된 스캔 결과와 같은가"),
          code('''import pandas as pd, pathlib
mine_p = pathlib.Path("my_run/liability.csv")
if not mine_p.exists():
    print("my_run 스캔 결과가 없어 대조를 건너뜁니다 → 1절 실행 로그를 확인하세요.")
else:
    mine, ref = pd.read_csv(mine_p), pd.read_csv("data/liability.csv")
    common = [x for x in ref.columns if x in mine.columns]
    only   = [x for x in mine.columns if x not in ref.columns] + \\
             [x for x in ref.columns if x not in mine.columns]
    same = len(mine) == len(ref) and mine[common].astype(str).equals(ref[common].astype(str))
    print(f"행 {len(mine)} vs {len(ref)} · 공통 컬럼 {len(common)}개 → "
          + ("모든 값이 같아요" if same else "값이 다른 컬럼이 있어요"))
    if only:
        print("한쪽에만 있는 컬럼:", ", ".join(only))
    if not same and len(mine) == len(ref):
        # 다른 컬럼만 골라 '내 결과 → 레퍼런스' 로 나란히 — 대괄호·따옴표 없이 읽히게.
        diff = []
        for col in common:
            if not mine[col].astype(str).equals(ref[col].astype(str)):
                for i in range(len(mine)):
                    m, rf = str(mine[col].iloc[i]), str(ref[col].iloc[i])
                    if m != rf:
                        diff.append({"컬럼": col, "행": i, "내 결과": m, "레퍼런스": rf})
        if diff:
            display(pd.DataFrame(diff))
    print("판정 — " + ("일치하면 같은 서열·같은 스캐너로 재현된 거예요."
                     if same else
                     "서열을 바꿔 돌렸다면 달라지는 게 정상이에요. 같은 demo 서열인데 다르면 "
                     "Biopython 버전 차이(molecular_weight·pI 반올림)를 먼저 의심하세요."))'''),
          md("> 다음 → 본문 [09. repertoire & naturalness](../09_repertoire/09_repertoire.md)")]
    write_nb(ROOT/"08_developability"/"08_dev_lab.ipynb", c)


# ===========================================================================
# 09 — repertoire lab : 실제 OAS data unit 을 직접 다운로드
# ===========================================================================
def nb_09():
    c = header("09_repertoire", "09_repertoire.md", "09 — repertoire & naturalness (OAS 직접 다운로드)",
               "**진짜 OAS data unit** 을 직접 내려받아 CDR3 길이 분포를 만들고, 후보 항체의 위치를 재요.",
               prev="Ch.04 numbering")
    c += [bootstrap("09_repertoire", pip_pkgs="pandas matplotlib anarci abnumber", hmmer=True),
          md('''## 1) 직접 실행 — OAS data unit 다운로드 + CDR3 길이 집계 (본문 9.1)

```bash
python scripts/fetch_oas_unit.py --out my_run/oas_subset.tsv.gz
python scripts/oas_cdr3_length.py my_run/oas_subset.tsv.gz --column cdr3_aa \\
    --out my_run/oas_cdr3_length_summary.csv
```
받는 unit — **Eliyahu et al. 2018 · human PBMC · heavy IgM · run ERR2843400** (productive 17,807 서열).
OAS 원본 파일은 **첫 줄이 메타데이터(JSON)** 라 그냥 읽으면 컬럼을 못 찾아요 — 스크립트가 자동 처리합니다.

> **이 unit 의 한계** (본문 9.1) — HCV 코호트 **피험자 1명(subject CI15)의 IgM 레퍼토리**예요.
> "인간 레퍼토리 일반"의 대표값이 아니라 한 사람의 한 시점 샘플입니다.
> 실전 benchmark 라면 여러 건강 도너의 여러 unit 을 합치세요(같은 스크립트에 `--url` 만 바꾸면 됩니다).'''),
          code('''ok1 = run_tool([PY, SCRIPTS/"fetch_oas_unit.py", "--out", "my_run/oas_subset.tsv.gz"])
ok2 = run_tool([PY, SCRIPTS/"oas_cdr3_length.py", resolve("oas_subset.tsv.gz"),
                "--column", "cdr3_aa", "--out", "my_run/oas_cdr3_length_summary.csv"])
print("→ 원본 unit 과 길이 집계 CSV 두 개가 my_run/ 에 생겼어요." if ok1 and ok2
      else "→ 일부가 실패했어요. 뒤 절은 커밋된 data/ 로 이어갑니다.")'''),
          md('''## 2) 내 결과 확인 — 후보의 CDR-H3 를 IMGT 로 재기 (본문 9.2)

이 unit 은 **heavy** 서열이라 비교 대상도 heavy 여야 해요. FASTA 의 첫 레코드가 중쇄라는 보장은 없으니
**전 레코드를 numbering 해서 `chain_type` 을 확인**하고 H 사슬만 분포에 얹습니다.
길이 정의도 맞춰야 해요 — OAS `cdr3_aa` 는 IMGT CDR3(105–117)예요.'''),
          code('''from abnumber import Chain
import pandas as pd
from IPython.display import display

def read_fasta(path):
    d, n = {}, None
    for line in open(path):
        line = line.strip()
        if line.startswith(">"): n = line[1:].split()[0]; d[n] = ""
        elif n: d[n] += line
    return d

seqs, chains = read_fasta("data/demo_mab.fa"), {}
for sid, seq in seqs.items():
    try:
        chains[sid] = Chain(seq, scheme="imgt")
    except Exception as e:
        print(f"{sid}: IMGT numbering 실패 — {type(e).__name__} "
              "(ANARCI 는 hmmscan 실행파일이 필요해요 — 부트스트랩 로그 확인)")
if chains:
    display(pd.DataFrame([{"서열 ID": sid, "chain_type": ch.chain_type,
                           "사슬": "중쇄 — 이 분포의 비교 대상" if ch.chain_type == "H" else "경쇄 — 여기선 제외",
                           "CDR3 (IMGT)": ch.cdr3_seq, "길이 (aa)": len(ch.cdr3_seq)}
                          for sid, ch in chains.items()]))

heavy = [(sid, ch) for sid, ch in chains.items() if ch.chain_type == "H"]
light = [(sid, ch) for sid, ch in chains.items() if ch.chain_type != "H"]
cand = cand_id = None
cdr3_by_scheme = {}

if heavy:
    cand_id, hch = heavy[0]
    cand = len(hch.cdr3_seq)
    if len(heavy) > 1:
        print("H 사슬이", len(heavy), "개예요 — 첫 번째", cand_id, "를 대표로 씁니다")
    print(f"\\n비교 대상 — {cand_id} 의 CDR-H3 {cand} aa (IMGT)")
    if light:
        print("경쇄", ", ".join(f"{s}({ch.chain_type}, CDR-L3 {len(ch.cdr3_seq)} aa)" for s, ch in light),
              "— 이 분포는 heavy 전용이라 경쇄 길이는 여기에 얹지 않아요")
    for scheme in ("imgt", "kabat", "chothia"):
        try:
            cdr3_by_scheme[scheme] = len(Chain(seqs[cand_id], scheme=scheme).cdr3_seq)
        except Exception as e:
            print(f"  {scheme} numbering 실패 — {type(e).__name__}")
    print("scheme 별 CDR-H3 길이 —",
          " · ".join(f"{k} {v} aa" for k, v in cdr3_by_scheme.items()))
    print("판정 — percentile 은 IMGT 값으로만 계산해요. "
          "OAS cdr3_aa 가 IMGT 정의라, 다른 scheme 길이를 얹으면 엉뚱한 percentile 이 나옵니다 (3절에서 실측).")
else:
    print("\\nheavy(H) 사슬을 못 찾았어요 — 이 unit 은 heavy 라 percentile 비교를 건너뜁니다.")
    print("경쇄만 있는 FASTA 라면 light data unit(예: ERR..._Light_IGKC.csv.gz)을 "
          "fetch_oas_unit.py --url 로 받아 같은 절차를 돌리세요.")'''),
          md("## 3) 내 결과 확인 — 분포 통계와 후보의 위치 (본문 9.2)"),
          code('''import pandas as pd
from IPython.display import display

s = pd.read_csv(resolve("oas_cdr3_length_summary.csv"))
need = [x for x in ("cdr3_len", "count") if x not in s.columns]
assert not need, f"집계 CSV 에 {need} 컬럼이 없어요 → oas_cdr3_length.py 를 다시 돌리세요"
s = s.sort_values("cdr3_len").reset_index(drop=True)

n    = int(s["count"].sum())
mean = float((s["cdr3_len"] * s["count"]).sum() / n)
mode = s.loc[s["count"].idxmax()]
cum  = s["count"].cumsum() / n
p05  = int(s.loc[cum >= 0.05, "cdr3_len"].iloc[0])
p95  = int(s.loc[cum >= 0.95, "cdr3_len"].iloc[0])

def pctile(length):
    """이 분포에서 length 이하가 차지하는 비율(%) — 하위 percentile."""
    return 100 * float(s.loc[s["cdr3_len"] <= length, "count"].sum()) / n

print("이 unit 의 CDR-H3 길이 분포 요약")
display(pd.DataFrame([{
    "서열 수": f"{n:,}",
    "평균 (aa)": round(mean, 2),
    "최빈 (aa)": int(mode["cdr3_len"]),
    "최빈 비율": f"{int(mode['count']):,}건 · {100*int(mode['count'])/n:.1f}%",
    "전체 범위 (aa)": f"{int(s['cdr3_len'].min())}–{int(s['cdr3_len'].max())}",
    "5–95 percentile (aa)": f"{p05}–{p95}",
}]))

tail = s[s["cdr3_len"] <= 4]
if len(tail):
    tn = int(tail["count"].sum())
    print(f"\\n왼쪽 꼬리 {int(tail['cdr3_len'].min())}–{int(tail['cdr3_len'].max())} aa 가 "
          f"{tn}건 ({100*tn/n:.2f}%) — 실제 항체보다 시퀀싱/어노테이션 노이즈로 보는 게 맞아요.")
    print("이 집계는 자르지 않고 그대로 뒀어요(최솟값이 그래서 작게 찍힙니다). "
          "자르든 남기든 어느 쪽을 골랐는지 보고서에 밝히는 게 repertoire 분석의 기본기예요.")

if cand is None:
    print("\\n후보 heavy 사슬이 없어 percentile 은 계산하지 않습니다.")
else:
    pc = pctile(cand)
    print(f"\\n후보 {cand_id} CDR-H3 {cand} aa → 하위 {pc:.1f} percentile")
    if p05 <= cand <= p95:
        print(f"판정 — {p05}–{p95} aa(5–95 percentile) 안이라 길이 측면에서는 자연 human heavy 분포의 정상 범위예요.")
    elif cand > p95:
        print(f"판정 — 95 percentile({p95} aa)보다 길어요. 긴 CDR3 는 발현·안정성·면역원성을 따로 점검하세요.")
    else:
        print(f"판정 — 5 percentile({p05} aa)보다 짧아요. 결합 표면이 좁을 수 있어 affinity·특이성과 함께 보세요.")
    d_mode = abs(cand - int(mode["cdr3_len"]))
    print(f"최빈값 {int(mode['cdr3_len'])} aa 와 {d_mode} aa 차이 · 평균 {mean:.2f} aa 와 {abs(cand-mean):.1f} aa 차이")

    if cdr3_by_scheme:
        print("\\n같은 항체를 scheme 만 바꿔 재면 percentile 이 이만큼 움직여요.")
        display(pd.DataFrame([
            {"scheme": sc, "CDR-H3 길이 (aa)": L, "하위 percentile": f"{pctile(L):.1f}",
             "IMGT 대비": "기준 (OAS 와 같은 정의)" if sc == "imgt" else f"{pctile(L) - pc:+.1f} p 이동"}
            for sc, L in cdr3_by_scheme.items()]))
        print("그래서 본문 9.2 의 주의대로 후보도 OAS 와 같은 IMGT 정의로 재야 해요.")'''),
          md("## 4) 내 결과 확인 — CDR3 분포 그래프 (본문 9.2)"),
          code('''from antibody_viz import cdr3_length_distribution
from IPython.display import Image, display

png = "my_run/09_cdr3_length.png"
cdr3_length_distribution(resolve("oas_cdr3_length_summary.csv"),
    "OAS (Eliyahu 2018, human IgM heavy) — CDR3 length distribution",
    png, highlight_len=cand,
    highlight_label=(f"{cand_id} CDR-H3" if cand_id else "candidate"))
display(Image(png))

print(f"파란 막대 = 길이별 서열 수(봉우리 {int(mode['cdr3_len'])} aa) · "
      f"빨간 점선 = 평균 {mean:.2f} aa · 오른쪽 꼬리는 {int(s['cdr3_len'].max())} aa 까지")
if cand is None:
    print("판정 — 후보 heavy 가 없어 주황 실선은 그려지지 않았어요.")
else:
    side = "왼쪽" if cand < int(mode["cdr3_len"]) else ("오른쪽" if cand > int(mode["cdr3_len"]) else "같은 칸")
    print(f"주황 실선 = 후보 {cand} aa — 봉우리의 {side}, 하위 {pctile(cand):.1f} percentile 자리예요.")
    print("판정 — " + ("주황선이 종형의 몸통 안이면 길이 naturalness 는 통과."
                     if p05 <= cand <= p95 else
                     "주황선이 꼬리 쪽이면 왜 그 길이인지 설명할 수 있어야 해요.")
          + " 단, 중앙이라고 좋은 항체라는 뜻은 아니에요 (본문 9.3).")'''),
          md('''## 5) 레퍼런스 대조 — 커밋된 OAS 서브셋과 같은가

`data/oas_subset.tsv.gz` 는 **같은 OAS data unit 을 2026-07-14 에 받아 커밋해 둔 실제 데이터**예요
(합성 데이터 아님). 내가 방금 받은 것과 집계가 같아야 정상입니다.'''),
          code('''import pandas as pd, pathlib
ref = pd.read_csv("data/oas_cdr3_length_summary.csv")
mine_p = pathlib.Path("my_run/oas_cdr3_length_summary.csv")
if not mine_p.exists():
    print("my_run 집계가 없어 대조를 건너뜁니다 → 1절 실행 로그(네트워크)를 확인하세요.")
else:
    mine = pd.read_csv(mine_p)
    common = [x for x in ref.columns if x in mine.columns]
    same = mine[common].reset_index(drop=True).equals(ref[common].reset_index(drop=True))
    print(f"내 집계 n={int(mine['count'].sum()):,} / 레퍼런스 n={int(ref['count'].sum()):,} · "
          + ("행 단위까지 완전 일치" if same else "어긋난 행이 있어요"))
    if not same:
        m = mine.merge(ref, on="cdr3_len", how="outer", suffixes=("_mine", "_ref")).fillna(0)
        print(m[m["count_mine"] != m["count_ref"]].head(10).to_string(index=False))
    print("판정 — " + ("같은 unit 을 같은 스크립트로 집계했다는 확인이에요."
                     if same else
                     "OAS 가 data unit 을 갱신했거나 --url 을 바꿔 받았다면 달라지는 게 정상이에요. "
                     "보고서에는 받은 날짜와 unit 이름을 함께 적으세요."))'''),
          md('''## 6) V/J germline usage — "목록에 없다"가 뜻하는 것 (본문 9.3)

naturalness 의 두 번째 축은 **germline usage** 예요. 내가 받은 unit 에서 어떤 IGHV/IGHJ 가 흔한지 세고,
후보의 germline 이 그 안에 있는지 봅니다. **없을 때 그 이유가 "희귀"인지 "종이 다름"인지 가르는 게 핵심**이에요.'''),
          code('''import csv, pandas as pd
from IPython.display import display

rep = pd.read_csv(resolve("oas_subset.tsv.gz"), sep="\\t")
print(f"unit 서열 {len(rep):,}개 · 컬럼 " + " · ".join(rep.columns))

usage, top_rows = {}, []
for col, label in [("v_call", "IGHV"), ("j_call", "IGHJ")]:
    if col not in rep.columns:
        print(f"[{label}] {col} 컬럼이 없어 건너뜁니다"); continue
    g = rep[col].astype(str).str.split("*").str[0]
    usage[col] = g
    for rank, (name, k) in enumerate(g.value_counts().head(5).items(), 1):
        top_rows.append({"축": f"{label} — 이 unit 에 {g.nunique()}종", "순위": rank,
                         "germline": name, "서열 수": f"{k:,}",
                         "unit 내 비율": f"{100*k/len(rep):.1f}%"})

if top_rows:
    print("\\n이 unit 에서 흔한 germline top5 — 후보의 germline 이 여기 끼는지 보는 게 목적이에요.")
    display(pd.DataFrame(top_rows))

# --- 후보의 germline — abnumber(ANARCI) 로 직접, 실패하면 Ch.04 결과로 ---------
v_gene = j_gene = species = None
if cand_id:
    try:
        hv = Chain(seqs[cand_id], scheme="imgt", assign_germline=True)
        v_gene, j_gene, species = hv.v_gene, hv.j_gene, hv.species
        print("\\n[germline 출처] abnumber/ANARCI 직접 할당")
    except Exception as e:
        print("\\nabnumber germline 할당 실패 —", type(e).__name__, "→ Ch.04 numbering CSV 로 대체합니다")
    if v_gene is None:
        for sub in ("my_run", "data"):
            p = ADV_ROOT / "04_numbering" / sub / "demo_imgt_H.csv"
            if not p.exists():
                continue
            for row in csv.DictReader(open(p)):
                if row.get("Id") == cand_id and (row.get("chain_type") or "").strip() == "H":
                    v_gene, j_gene = row.get("v_gene"), row.get("j_gene")
                    species = (row.get("identity_species") or row.get("hmm_species") or "").strip()
            if v_gene:
                print("[germline 출처]", p); break

if not v_gene:
    print("\\n후보 germline 을 못 읽어 usage 비교를 건너뜁니다 "
          "(Ch.04 노트북을 같은 FASTA 로 먼저 돌리면 채워집니다).")
elif "v_call" not in usage:
    print("\\nunit 에 v_call 이 없어 usage 비교를 건너뜁니다.")
else:
    v_fam = str(v_gene).split("*")[0]
    genes = sorted(set(usage["v_call"]))
    hit   = int((usage["v_call"] == v_fam).sum())
    print("\\n후보 heavy 의 germline 과, 그게 이 unit 안에 있는지")
    display(pd.DataFrame([
        {"항목": "V germline", "값": str(v_gene)},
        {"항목": "J germline", "값": str(j_gene)},
        {"항목": "ANARCI 가 판정한 species", "값": species or "미상"},
        {"항목": f"이 unit 에서 {v_fam} 을 쓴 서열", "값": f"{hit}건 (unit 의 IGHV {len(genes)}종 중)"},
    ]))
    if hit:
        rank = int((usage["v_call"].value_counts() > hit).sum()) + 1
        print(f"판정 — 목록 안에 있어요. usage {100*hit/len(rep):.2f}% 로 {len(genes)}종 중 {rank}위 "
              "→ 이 도너에게 흔한 germline 이에요.")
    else:
        fams = sorted({g.split("-")[0] for g in genes})
        print(f"이 unit 의 IGHV family 는 {', '.join(fams)} 뿐이고, 후보의 {v_fam.split('-')[0]} 은 그 안에 없어요.")
        if species and str(species).lower() != "human":
            print(f"판정 — 0건인 이유는 '희귀 germline' 이 아니라 종이 다르기 때문이에요. "
                  f"후보 heavy 는 {species} germline 으로 맞았고, 이 unit 은 human repertoire 라 "
                  f"{v_fam} 이라는 gene 자체가 없습니다.")
            print("판정 — 종이 다른 germline 은 human usage percentile 의 비교 대상이 아니에요. "
                  "여기서 읽을 것은 usage 순위가 아니라 humanization 이 필요하다는 사실(Ch.04·Ch.05)입니다.")
        else:
            print("판정 — 같은 종인데 0건이면 그때가 '이 unit 기준 희귀' 예요. "
                  "다만 unit 1개(도너 1명)라 희귀 판정은 여러 unit 을 합쳐서 해야 합니다.")
    if j_gene and "j_call" in usage:
        j_fam = str(j_gene).split("*")[0]
        jhit = int((usage["j_call"] == j_fam).sum())
        if jhit:
            print(f"참고) J 이름 {j_fam} 은 이 human unit 에도 {jhit:,}건 있어요 — "
                  "gene 이름은 종을 넘어 겹치니 이름이 같다고 같은 germline 은 아니에요.")

print("\\n본문 9.3 원칙 — 흔하다고 좋은 항체가 아니고, 드물다고 나쁜 후보도 아니에요. "
      "다만 '왜 드문지' 설명할 수 있어야 하고, naturalness 는 단독 판정에 쓰지 않아요.")'''),
          md('''## 7) 통합 triage — 전 챕터 결과를 한 표로 (본문 9.4)

이 가이드의 **결론 산출물**이에요. 축별로 각 챕터의 `my_run/` 을 먼저 찾고 없으면 그 챕터의 커밋본을 읽어
실측과 판정을 한 표로 모읍니다. 판정은 전부 **읽은 값으로 계산**해요 — 여러분 서열로 바꿔 돌리면 판정도 바뀝니다.
표는 `my_run/triage_summary.csv` 로도 저장돼 보고서에 그대로 붙일 수 있어요.'''),
          code('''import csv, pathlib, pandas as pd

def ch_file(chapter, name):
    """다른 챕터의 산출물 — 그 챕터 my_run/ 을 먼저, 없으면 커밋된 data/ 를 쓴다."""
    for sub in ("my_run", "data"):
        p = ADV_ROOT / chapter / sub / name
        if p.exists():
            return p, sub
    return None, None

rows = []
def add(axis, chapter, value, verdict, src):
    rows.append({"축": axis, "챕터": chapter, "실측": value, "판정": verdict, "출처": src})

# --- 04 numbering·germline -------------------------------------------------
germ, src04 = [], set()
for fn in ("demo_imgt_H.csv", "demo_imgt_KL.csv"):
    p, sub = ch_file("04_numbering", fn)
    if not p:
        continue
    src04.add(sub)
    for r in csv.DictReader(open(p)):
        germ.append((r.get("Id"), r.get("chain_type"), r.get("v_gene"),
                     (r.get("identity_species") or r.get("hmm_species") or "").strip()))
if germ:
    nonhuman = [g for g in germ if g[3] and g[3].lower() != "human"]
    add("numbering·germline", "04",
        " / ".join(f"{i}({t}) {v} [{sp or '?'}]" for i, t, v, sp in germ),
        (f"주의 — 비human germline {len(nonhuman)}개 사슬 → humanization 검토" if nonhuman
         else "양호 — 전 사슬 human germline"),
        "+".join(sorted(src04)))

# --- 05 humanness ----------------------------------------------------------
p, sub = ch_file("05_humanness", "demo_sapiens_scores.csv")
if p:
    d = pd.read_csv(p)
    if {"chain", "input_aa"} <= set(d.columns):
        aa = list("ACDEFGHIKLMNPQRSTVWY")
        d["p"] = [r[r["input_aa"]] if r["input_aa"] in aa else None for _, r in d.iterrows()]
        hum = d.groupby("chain")["p"].mean()
        val = " / ".join(f"{k} {v:.3f}" for k, v in hum.items())
        po, so = ch_file("05_humanness", "demo_mab.fa")
        ph, sh = ch_file("05_humanness", "demo_humanized.fa")
        if po and ph:
            o, h = read_fasta(po), read_fasta(ph)
            muts = {k: sum(1 for x, y in zip(o[k], h[k]) if x != y)
                    for k in o if k in h and len(o[k]) == len(h[k])}
            if muts:
                val += " · humanizing 변이 " + " / ".join(f"{k} {v}" for k, v in muts.items())
        worst = float(hum.min())
        add("humanness", "05", val,
            ("양호 — 전 사슬 0.8 이상" if worst >= 0.8 else f"주의 — 최저 {worst:.3f} (기준 0.8 미만)"),
            sub)

# --- 06 구조 신뢰도 ---------------------------------------------------------
p, sub = ch_file("06_structure", "demo_antibody_igfold.pdb")
if p:
    prof = {}
    for line in open(p):
        if line.startswith("ATOM") and line[12:16].strip() == "CA":
            prof.setdefault(line[21], []).append((int(line[22:26]), float(line[60:66])))
    if prof:
        stat = {k: (sum(b for _, b in v) / len(v), max(v, key=lambda t: t[1]))
                for k, v in sorted(prof.items())}
        val = " / ".join(f"{k} mean {m:.3f} Å, max {mx[1]:.2f} Å (res {mx[0]})"
                         for k, (m, mx) in stat.items())
        worst_mean = max(m for m, _ in stat.values())
        worst_max  = max(mx[1] for _, mx in stat.values())
        verdict = ("양호" if worst_mean < 1.0 else "주의") + f" — 사슬 평균 최대 {worst_mean:.3f} Å"
        if worst_max >= 2.0:
            verdict += f", 최대오차 {worst_max:.2f} Å 잔기(loop)는 따로 확인"
        add("구조 신뢰도", "06", val, verdict, sub)

# --- 07 interface (예시 복합체) ---------------------------------------------
p, sub = ch_file("07_interface", "contacts_H_N.tsv")
if p:
    pairs = []
    for line in open(p):
        if "atom_contacts=" in line:
            left, k = line.rstrip().split("atom_contacts=")
            a, b = left.rstrip("\\t").split("\\t")
            pairs.append((a.strip(), b.strip(), int(k)))
    if pairs:
        add("interface", "07",
            f"{len(pairs)} residue pair · paratope {len({a for a, _, _ in pairs})} · "
            f"epitope {len({b for _, b, _ in pairs})} · 원자접촉 {sum(k for *_, k in pairs)}",
            "참고 — 후보 자신의 복합체가 아니라 예시 구조(1A14) 기준이에요",
            sub)

# --- 08 developability -----------------------------------------------------
p, sub = ch_file("08_developability", "liability.csv")
if p:
    d = pd.read_csv(p)
    mcols = [x for x in ("N_glycosylation_NXS_T", "deamidation_NG",
                         "deamidation_NS", "isomerization_DG") if x in d.columns]
    tot = sum(1 for x in mcols for v in d[x] for q in str(v).split(";") if q.strip().isdigit())
    odd = int(sum(1 for v in d.get("cysteine_count", []) if int(v) % 2 == 1))
    flags = ([f"unpaired Cys {odd}사슬"] if odd else []) + ([f"motif {tot}건"] if tot else [])
    add("developability", "08", f"홀수 Cys 사슬 {odd}개 · liability motif {tot}건",
        ("양호 — 서열 liability 깨끗" if not flags else "주의 — " + ", ".join(flags)), sub)

# --- 09 naturalness --------------------------------------------------------
_cand, _pct = globals().get("cand"), globals().get("pctile")
if _cand is not None and _pct is not None:
    add("naturalness", "09",
        f"CDR-H3 {_cand} aa (IMGT) · 하위 {_pct(_cand):.1f} percentile · n={n:,}",
        (f"양호 — 5–95 percentile({p05}–{p95} aa) 안" if p05 <= _cand <= p95
         else f"주의 — 5–95 percentile({p05}–{p95} aa) 밖"),
        "이 챕터")

tri = pd.DataFrame(rows)
display(tri)
out = pathlib.Path("my_run/triage_summary.csv")
tri.to_csv(out, index=False, encoding="utf-8-sig")
print("저장:", out)

warn = [r["축"] for r in rows if str(r["판정"]).startswith("주의")]
print(f"\\n축 {len(rows)}개 중 주의 {len(warn)}개" + (" — " + ", ".join(warn) if warn else ""))
print("판정 — " + (", ".join(warn) + " 축이 남은 과제예요. 나머지 축은 기준을 통과했습니다."
                 if warn else "모든 축이 기준을 통과했어요."))
print("이 표가 보고서의 첫 페이지예요 — 축·수치·판정·출처를 한 줄씩 (본문 9.4 · Ch.10 체크리스트).")'''),
          md("> 다음 → 본문 [10. 부록](../10_appendix/10_appendix.md)")]
    write_nb(ROOT/"09_repertoire"/"09_repertoire_lab.ipynb", c)


if __name__ == "__main__":
    nb_02(); nb_03(); nb_04(); nb_05(); nb_06(); nb_07(); nb_08(); nb_09()
    print("\n모든 노트북 생성 완료.")
