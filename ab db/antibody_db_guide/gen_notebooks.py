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
NEED_HMMER = @HMMER@        # ANARCI 계열은 HMMER 의 hmmscan 실행파일이 필요해요 (pip 로는 안 깔려요)
PIN_TRANSFORMERS = @PIN@    # IgFold 체크포인트가 요구하는 transformers 버전(없으면 None)

import os, sys, subprocess, pathlib, shutil, importlib.util
IN_COLAB = "google.colab" in sys.modules

# HuggingFace 가중치 다운로드가 '멈춘 채' 매달리는 일을 막습니다.
# (멈춤은 예외가 안 나서 폴백이 안 걸립니다 — 타임아웃을 걸어 실패로 바꿔야 data/ 로 이어집니다)
os.environ.setdefault("HF_HUB_DOWNLOAD_TIMEOUT", "30")   # 스트림 30초 무응답 → 끊고 재시도
os.environ.setdefault("HF_HUB_ETAG_TIMEOUT", "15")

def _run(cmd):
    print("$", cmd); subprocess.run(cmd, shell=True, check=True)

_MARK = "antibody_viz.py"           # 이 파일이 있는 폴더가 가이드 루트

def _find_root():
    """가이드 루트를 찾는다 — 챕터 폴더 안, 루트, 클론된 저장소 어디서 열어도 동작."""
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

if NEED_HMMER and shutil.which("hmmscan") is None:
    # ANARCI 는 내부적으로 hmmscan 을 호출해요. pip install anarci 만으로는 안 깔려요.
    if IN_COLAB:
        _run("apt-get -qq update")                       # 인덱스가 낡으면 install 이 404 로 죽는다
        _run("apt-get -qq install -y hmmer")             # ← ANARCI 가 부르는 hmmscan
    else:
        print("[!] hmmscan 이 없어요 → conda install -c bioconda hmmer  (또는 apt install hmmer)")

_miss = [p for p in PIP_PKGS.split() if not _have(p)]
if _miss:
    _run(f'"{sys.executable}" -m pip -q install ' + " ".join(_miss))

if "igfold" in PIP_PKGS and importlib.util.find_spec("pkg_resources") is None:
    # setuptools 81+(2026-02) 이 pkg_resources 를 없앴는데 IgFold 의존성이 이걸 import 해요.
    _run(f'"{sys.executable}" -m pip -q install "setuptools<81"')
    importlib.invalidate_caches()

import glob as _glob
if IN_COLAB and not _glob.glob("/usr/share/fonts/**/*Nanum*", recursive=True):
    # Colab 에는 한글 폰트가 없어 그래프의 한글 라벨이 □ 로 깨집니다.
    _run("apt-get -qq update"); _run("apt-get -qq install -y fonts-nanum")


if PIN_TRANSFORMERS:
    # IgFold 체크포인트에는 옛 transformers 의 토크나이저 객체가 pickle 돼 있어요.
    # 최신 transformers(5.x) 로는 unpickle 이 실패해서(Trie/BasicTokenizer 없음) 버전을 맞춥니다.
    _ver = subprocess.run([sys.executable, "-c",
                           "import transformers;print(transformers.__version__)"],
                          capture_output=True, text=True).stdout.strip()
    if not _ver.startswith("4."):
        print(f"[transformers {_ver or 'none'} → {PIN_TRANSFORMERS}] IgFold 체크포인트 호환 버전으로 맞춥니다")
        _run(f'"{sys.executable}" -m pip -q install "transformers=={PIN_TRANSFORMERS}"')

# --- 내 산출물 폴더 & 폴백 규칙 --------------------------------------------
MYRUN = pathlib.Path("my_run"); MYRUN.mkdir(exist_ok=True)

def run_tool(args, timeout=1800):
    """도구를 서브프로세스로 실제 실행하고 출력을 셀에 그대로 보여줘요."""
    args = [str(a) for a in args]
    print("$", " ".join(args))
    try:
        p = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
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

print("ADV_ROOT :", ADV_ROOT)
print("작업 폴더 :", pathlib.Path.cwd(), "| Colab:", IN_COLAB)'''


def bootstrap(chapter, pip_pkgs="pandas matplotlib", hmmer=False, pin_transformers=None):
    return code(BOOTSTRAP
                .replace("@CHAPTER@", chapter)
                .replace("@PIP@", pip_pkgs)
                .replace("@HMMER@", "True" if hmmer else "False")
                .replace("@PIN@", f'"{pin_transformers}"' if pin_transformers else "None"))


def header(chapter_dir, chapter_md, title, what):
    return [md(f'''# {title}

> 본문: [`{chapter_md}`]({chapter_md}) 와 **한 절씩 짝지어** 보세요.
> **전 셀 실행 {RUNTIME[chapter_dir]}** (실측)

**이 노트북은 도구를 직접 돌립니다.** {what}
각 절은 **① 직접 실행 → ② 내 결과 확인 → ③ 레퍼런스 대조** 순서예요.
내가 만든 결과는 `my_run/` 에 쌓이고, 저장소에 커밋된 `data/` 는 **대조군(레퍼런스)** 으로만 씁니다.
어느 단계를 건너뛰거나 실패해도 `resolve()` 가 `data/` 로 폴백해서 뒤 절이 계속 돌아가요.'''),
            md('''## 0) 부트스트랩 — 저장소 클론 · 도구 설치 · 작업 폴더 이동

**Colab**: 이 셀을 그대로 실행하면 클론 → 챕터 폴더 이동 → 필요한 도구 설치까지 한 번에 끝나요.
**로컬**: 챕터 폴더 안에서 열었다면 클론 없이 진행됩니다.''')]



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
    c += [bootstrap("02_databases", pip_pkgs="pandas matplotlib requests"),
          md('''## 1) 직접 실행 — RCSB에서 항체-항원 복합체 스냅샷 만들기 (본문 2.2)

SAbDab·Thera-SAbDab 웹 UI는 스크립트로 바로 긁기 어려워요(로그인·JS 렌더링). 그래서 **같은 원본인 PDB**를
RCSB **Search API + Data API**로 직접 조회해 "SAbDab스러운" 요약 표를 만듭니다.

```bash
python scripts/fetch_rcsb_ab_snapshot.py --rows 12 --out my_run/rcsb_ab_complexes.csv
```
- 검색 조건: X-ray · 해상도 ≤ 2.5 Å · 단백질 entity ≥ 3 · full-text "Fab antibody complex"
- 정렬: **release date 오름차순**(오래된 entry부터) → 시간이 지나도 목록이 잘 안 흔들려요
- entity 설명(`pdbx_description`)에서 **heavy / light / 항원 사슬 역할을 파생**합니다'''),
          code('''ok = run_tool([PY, SCRIPTS/"fetch_rcsb_ab_snapshot.py",
                "--rows", "12", "--out", "my_run/rcsb_ab_complexes.csv"])'''),
          md("## 2) 내 결과 확인 — 방금 받은 스냅샷"),
          code('''import pandas as pd
snap = pd.read_csv(resolve("rcsb_ab_complexes.csv"))
cols = ["pdb_id","released","resolution_A","heavy_chains","light_chains","antigen_chains","antigen_name"]
display(snap[cols])
print("\\n해상도(Å): 평균 %.2f / 최고 %.2f" % (snap.resolution_A.mean(), snap.resolution_A.min()))
print("항체 사슬 ID 가 H/L 이 아닌 entry:",
      snap.loc[(snap.heavy_chains != "H") | (snap.light_chains != "L"), "pdb_id"].tolist() or "없음")
print("\\n[주의] 사슬 ID 는 entry 마다 달라요 — 항원이 N일 수도, Y일 수도 있어요(Ch.07에서 직접 겪습니다).")'''),
          md('''## 3) 레퍼런스 대조 — 커밋된 스냅샷과 비교

`data/rcsb_ab_complexes.csv` 는 **2026-07-14 에 같은 스크립트로 받아 커밋한 대조군**이에요.
PDB는 매주 자라니까, 내 결과와 100% 같지 않을 수 있어요 — 그 차이 자체가 "DB는 살아 있다"는 관찰입니다.'''),
          code('''import pandas as pd, pathlib
ref = pd.read_csv("data/rcsb_ab_complexes.csv")
if pathlib.Path("my_run/rcsb_ab_complexes.csv").exists():
    mine = pd.read_csv("my_run/rcsb_ab_complexes.csv")
    a, b = set(mine.pdb_id), set(ref.pdb_id)
    print(f"내 결과 {len(a)}개 · 레퍼런스 {len(b)}개 · 공통 {len(a & b)}개")
    print("내 결과에만:", sorted(a - b) or "없음")
    print("레퍼런스에만:", sorted(b - a) or "없음")
    same = mine.merge(ref, on="pdb_id", suffixes=("_mine","_ref"))
    diff = same[same.resolution_A_mine != same.resolution_A_ref]
    print("공통 entry 중 해상도가 다른 것:", diff.pdb_id.tolist() or "없음 (완전 일치)")
else:
    print("my_run 스냅샷이 없어 대조를 건너뜁니다 (네트워크 차단 환경).")
    display(ref.head())'''),
          md("## 4) DB 성격별 지도 — 어디서 무엇을 찾나 (본문 2.1)"),
          code('''import pandas as pd
dbs = pd.DataFrame([
    ["구조 DB", "SAbDab / SAbDab-nano / IMGT-3D", "항체·복합체 구조", "구조·epitope/paratope"],
    ["서열 repertoire", "OAS / AIRR / iReceptor", "BCR 대량 서열", "naturalness·germline"],
    ["치료 항체", "Thera-SAbDab", "임상/승인 항체", "benchmark"],
    ["항원 특화", "CoV-AbDab / IEDB", "항원 특이 항체·epitope", "중화·epitope"],
    ["affinity/mutation", "AB-Bind / SKEMPI", "mutation→binding", "ΔΔG·maturation"],
], columns=["유형", "대표 DB", "주요 데이터", "주 용도"])
display(dbs)
print("SAbDab 검색 시 확인할 필드:")
for f in ["PDB ID","heavy/light chain ID","antigen chain ID","resolution","antibody species",
          "antigen type","affinity value 존재","bound/unbound","CDR sequence/length"]:
    print("  -", f)'''),
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

"설치됐다"의 진짜 기준은 **도구가 결과를 내놓는가**예요. 아래 셀은 라이브러리 import 를 확인하고,
곧바로 데모 항체를 **실제로 numbering** 해서 결과를 `my_run/setup_report.csv` 에 씁니다.'''),
          code('''import importlib.util, shutil, sys, time
import pandas as pd

rows = []
def check(kind, name, ok, detail=""):
    rows.append({"kind": kind, "item": name, "ok": "O" if ok else "X", "detail": detail})
    print(("O " if ok else "X "), f"{name:12s}", detail)

print("[현재 커널 python]", sys.executable)
for m, label in [("Bio","biopython"), ("pandas","pandas"), ("matplotlib","matplotlib"),
                 ("anarci","anarci"), ("abnumber","abnumber")]:
    check("python", label, importlib.util.find_spec(m) is not None)
for tool in ["hmmscan", "ANARCI"]:
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
        rows.append({"kind": "smoke", "item": sid, "ok": "O",
                     "detail": f"chain_type={ch.chain_type} cdr3={ch.cdr3_seq} ({time.time()-t0:.2f}s)"})
        print("O  smoke       ", sid, "→ chain_type", ch.chain_type, "| CDR3", ch.cdr3_seq)
except Exception as e:
    rows.append({"kind": "smoke", "item": "abnumber/ANARCI", "ok": "X", "detail": f"{type(e).__name__}: {e}"})
    print("X  smoke        실패:", type(e).__name__, e)
    print("   → hmmscan 이 없으면 여기서 FileNotFoundError 가 나요 (본문 3.1 참고)")

report = pd.DataFrame(rows)
report.to_csv("my_run/setup_report.csv", index=False)
print("\\nWrote: my_run/setup_report.csv")'''),
          md("## 2) 내 결과 확인 — 점검표"),
          code('''import pandas as pd
rep = pd.read_csv(resolve("setup_report.csv"))
display(rep)
missing = rep[rep.ok == "X"]
print("문제 없음 " if missing.empty else "다음 항목을 먼저 해결하세요:")
for _, r in missing.iterrows():
    print("  -", r["item"], r["detail"])'''),
          md('''## 3) 레퍼런스 대조 — numbering 결과가 정답과 같은가

`data/setup_expected.csv` 에는 같은 데모 항체를 ANARCI(IMGT)로 돌렸을 때 **나와야 하는 값**이 들어 있어요.
스모크 테스트 결과가 이것과 같으면 환경이 제대로 선 거예요.'''),
          code('''import pandas as pd
exp = pd.read_csv("data/setup_expected.csv")
display(exp)
rep = pd.read_csv("my_run/setup_report.csv")
smoke = rep[rep.kind == "smoke"].set_index("item")["detail"].to_dict()
for _, r in exp.iterrows():
    got = smoke.get(r["id"], "")
    ok = (f"chain_type={r['chain_type']}" in got) and (f"cdr3={r['cdr3_imgt']}" in got)
    print(("일치  " if ok else "불일치"), r["id"], "| 기대:", r["chain_type"], r["cdr3_imgt"], "| 내 결과:", got or "(없음)")'''),
          md("> 다음 → 본문 [04. numbering & germline](../04_numbering/04_numbering.md)")]
    write_nb(ROOT/"03_setup"/"03_setup_check.ipynb", c)


# ===========================================================================
# 04 — numbering lab : ANARCI 를 직접 실행
# ===========================================================================
def nb_04():
    c = header("04_numbering", "04_numbering.md", "04 — numbering & germline (ANARCI 직접 실행)",
               "ANARCI 를 **직접 돌려** IMGT·Chothia numbering CSV 를 `my_run/` 에 만들고, 커밋된 결과와 대조해요.")
    c += [bootstrap("04_numbering", pip_pkgs="pandas matplotlib anarci abnumber", hmmer=True),
          md('''## 1) 직접 실행 — ANARCI numbering (본문 4.1)

```bash
ANARCI -i data/demo_mab.fa -s imgt --assign_germline --csv --outfile my_run/demo_imgt
ANARCI -i data/demo_mab.fa -s chothia --csv --outfile my_run/demo_chothia
```
사슬별 CSV(`..._H.csv`, `..._KL.csv`)가 생깁니다. 각 numbering 위치가 **컬럼 하나**가 돼요.'''),
          code('''ok_imgt = run_tool(["ANARCI", "-i", "data/demo_mab.fa", "-s", "imgt",
                    "--assign_germline", "--csv", "--outfile", "my_run/demo_imgt"])
ok_chot = run_tool(["ANARCI", "-i", "data/demo_mab.fa", "-s", "chothia",
                    "--csv", "--outfile", "my_run/demo_chothia"])
import pathlib
print("\\n생성된 파일:", sorted(p.name for p in pathlib.Path("my_run").glob("*.csv")))'''),
          md("## 2) 내 결과 확인 — germline 할당 (본문 4.2)"),
          code('''import pandas as pd
for label, f in [("Heavy", "demo_imgt_H.csv"), ("Light", "demo_imgt_KL.csv")]:
    r = pd.read_csv(resolve(f)).iloc[0]
    print(f"{label:6s}: chain_type={r['chain_type']}  V={r['v_gene']} ({r['v_identity']*100:.0f}%)  "
          f"J={r['j_gene']} ({r['j_identity']*100:.0f}%)  score={r['score']}")
print("\\n[심화] Heavy V=IGHV14-4 → 마우스 germline! → Ch.05 humanization 대상")'''),
          md("## 3) 내 결과 확인 — IMGT vs Chothia CDR-H1 경계 (본문 4.3)"),
          code('''import pandas as pd
def occupied(f, lo, hi):
    r = pd.read_csv(f).iloc[0]
    cols = [c for c in r.index if str(c).strip().isdigit() and lo <= int(c) <= hi]
    return [c for c in cols if str(r[c]) not in ("nan", "-", "")]

imgt_h  = resolve("demo_imgt_H.csv")
chot_h  = resolve("demo_chothia_H.csv")
print("IMGT    CDR-H1 (27-38):", len(occupied(imgt_h, 27, 38)), "잔기")
print("Chothia CDR-H1 (26-32):", len(occupied(chot_h, 26, 32)), "잔기")
print("\\n[주의] scheme 마다 경계가 달라요 → 보고서엔 항상 scheme 명시!")

# CDR 서열도 뽑아 두면 뒤 챕터(08·09)에서 그대로 씁니다.
from abnumber import Chain
seqs, name = {}, None
for line in open("data/demo_mab.fa"):
    line = line.strip()
    if line.startswith(">"): name = line[1:].split()[0]; seqs[name] = ""
    elif name: seqs[name] += line
rows = []
for sid, seq in seqs.items():
    ch = Chain(seq, scheme="imgt")
    rows.append({"id": sid, "chain_type": ch.chain_type, "cdr1": ch.cdr1_seq,
                 "cdr2": ch.cdr2_seq, "cdr3": ch.cdr3_seq, "cdr3_len": len(ch.cdr3_seq)})
cdrs = pd.DataFrame(rows)
cdrs.to_csv("my_run/demo_cdrs.csv", index=False)
display(cdrs)'''),
          md('''## 4) 레퍼런스 대조 — 커밋된 ANARCI 결과와 같은가

`data/demo_imgt_H.csv` 는 이 저장소를 만들 때 ANARCI 로 돌려 커밋해 둔 대조군이에요.
내가 방금 만든 CSV와 **셀 단위로** 비교합니다.'''),
          code('''import pandas as pd, pathlib
def compare(fname):
    mine_p, ref_p = pathlib.Path("my_run")/fname, pathlib.Path("data")/fname
    if not mine_p.exists():
        print(f"{fname}: my_run 산출물 없음 → 대조 건너뜀"); return
    mine, ref = pd.read_csv(mine_p), pd.read_csv(ref_p)
    common = [c for c in ref.columns if c in mine.columns]
    same = mine[common].astype(str).equals(ref[common].astype(str))
    print(f"{fname}: 공통 컬럼 {len(common)}개 / 값 완전 일치 = {same}")
    if not same:
        for c in common:
            if not mine[c].astype(str).equals(ref[c].astype(str)):
                print("   차이 컬럼:", c, "| 내 결과:", mine[c].tolist(), "| 레퍼런스:", ref[c].tolist())
for f in ["demo_imgt_H.csv", "demo_imgt_KL.csv", "demo_chothia_H.csv", "demo_chothia_KL.csv"]:
    compare(f)'''),
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

BioPhi CLI(`biophi sapiens`)는 **bioconda 전용**이라 Colab 에서 못 써요. 하지만 BioPhi가 내부에서 쓰는
두 부품(`sapiens` 언어모델, `abnumber` numbering)은 **둘 다 pip 에 있어요** — 그래서 같은 알고리즘을
그대로 돌릴 수 있습니다.

```bash
python scripts/sapiens_humanize.py data/demo_mab.fa \\
    --scores-out my_run/demo_sapiens_scores.csv --fasta-out my_run/demo_humanized.fa
```
1. 위치별 아미노산 확률 예측 → 2. 각 위치 최대확률 아미노산으로 재구성 → 3. **원본 CDR 재이식**
(BioPhi 기본값: Kabat CDR 보존, 1 iteration)'''),
          code('''ok = run_tool([PY, SCRIPTS/"sapiens_humanize.py", "data/demo_mab.fa",
                "--scores-out", "my_run/demo_sapiens_scores.csv",
                "--fasta-out",  "my_run/demo_humanized.fa"])'''),
          md("## 2) 내 결과 확인 — 사슬별 humanness (본문 5.2)"),
          code('''import pandas as pd
df = pd.read_csv(resolve("demo_sapiens_scores.csv"))
aa = list("ACDEFGHIKLMNPQRSTVWY")
df["p_input"] = [row[row["input_aa"]] if row["input_aa"] in aa else None for _, row in df.iterrows()]
hum = df.groupby("chain")["p_input"].mean()
print(hum.round(3).to_string())
print("\\n[심화] Heavy 가 낮고(마우스 흔적) Light 가 높으면(사람스러움) — Ch.04 germline 결과와 일치해요.")'''),
          md("## 3) 내 결과 확인 — humanness 그래프 + 원본 vs humanized 변이 (본문 5.3)"),
          code('''from antibody_viz import humanness_overview
from IPython.display import Image
png = "my_run/05_humanness_overview.png"
humanness_overview(resolve("demo_sapiens_scores.csv"), "data/demo_mab.fa",
                   resolve("demo_humanized.fa"),
                   "Humanness — Sapiens (demo mAb, 내 실행 결과)", png)
Image(png)'''),
          md('''## 4) 레퍼런스 대조 — BioPhi CLI 결과와 같은가

`data/demo_sapiens_scores.csv`·`data/demo_humanized.fa` 는 **bioconda BioPhi CLI** 로 만들어 커밋한 대조군이에요.
pip 로 재현한 내 결과가 이것과 같은지 확인합니다(같으면 알고리즘 재현 성공).'''),
          code('''import pandas as pd, pathlib
def read_fa(p):
    d, n = {}, None
    for line in open(p):
        line = line.strip()
        if line.startswith(">"): n = line[1:].split()[0]; d[n] = ""
        elif n: d[n] += line
    return d

if pathlib.Path("my_run/demo_sapiens_scores.csv").exists():
    mine, ref = pd.read_csv("my_run/demo_sapiens_scores.csv"), pd.read_csv("data/demo_sapiens_scores.csv")
    aa = list("ACDEFGHIKLMNPQRSTVWY")
    for d in (mine, ref):
        d["p"] = [r[r["input_aa"]] for _, r in d.iterrows()]
    cmp = pd.DataFrame({"내 결과": mine.groupby("chain")["p"].mean().round(4),
                        "레퍼런스(BioPhi CLI)": ref.groupby("chain")["p"].mean().round(4)})
    cmp["차이"] = (cmp["내 결과"] - cmp["레퍼런스(BioPhi CLI)"]).abs().round(4)
    display(cmp)

    m_fa, r_fa = read_fa("my_run/demo_humanized.fa"), read_fa("data/demo_humanized.fa")
    orig = read_fa("data/demo_mab.fa")
    for sid in orig:
        nm = sum(1 for a, b in zip(orig[sid], m_fa[sid]) if a != b)
        nr = sum(1 for a, b in zip(orig[sid], r_fa[sid]) if a != b)
        print(f"{sid}: 내 humanized 변이 {nm}개 / 레퍼런스 {nr}개 | 서열 동일 = {m_fa[sid] == r_fa[sid]}")
else:
    print("my_run 산출물이 없어 대조를 건너뜁니다.")'''),
          md("> 다음 → 본문 [06. 구조예측 (IgFold)](../06_structure/06_structure.md)")]
    write_nb(ROOT/"05_humanness"/"05_humanness_lab.ipynb", c)


# ===========================================================================
# 06 — structure lab : IgFold 를 직접 실행
# ===========================================================================
def nb_06():
    c = header("06_structure", "06_structure.md", "06 — 구조예측 (IgFold 직접 실행)",
               "IgFold 를 **직접 돌려** Fv 구조를 예측하고(`my_run/`), 커밋된 예측 구조와 CA-RMSD 로 대조해요.")
    c += [bootstrap("06_structure", pip_pkgs="pandas matplotlib biopython igfold anarci abnumber",
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
          code('''RUN_IGFOLD = True     # 이 노트북에서 가장 무거운 단계(수십 초). False 면 커밋본으로 진행

if RUN_IGFOLD:
    ok = run_tool([PY, SCRIPTS/"run_igfold_demo.py",
                   "--fasta", "data/demo_mab.fa",
                   "--out", "my_run/demo_antibody_igfold.pdb"])
else:
    print("RUN_IGFOLD=False → 예측을 건너뛰고 레퍼런스 PDB 로 진행합니다.")'''),
          md("## 2) 내 결과 확인 — 사슬별 예측 신뢰도 (본문 6.2)"),
          code('''pdb = resolve("demo_antibody_igfold.pdb")
ch = {}
for line in open(pdb):
    if line.startswith("ATOM") and line[12:16].strip() == "CA":
        ch.setdefault(line[21], []).append(float(line[60:66]))
for c2, v in sorted(ch.items()):
    print(f"chain {c2}: {len(v)} res | mean err {sum(v)/len(v):.2f} Å | max {max(v):.2f} Å")
print("\\n[심화] Heavy 의 최대 예측오차 위치가 CDR-H3 예요 — 가장 다양하고 가장 불확실한 loop.")'''),
          md("## 3) 내 결과 확인 — 신뢰도 프로파일 그래프 (본문 6.2)"),
          code('''from antibody_viz import structure_confidence
from IPython.display import Image
png = "my_run/06_structure_confidence.png"
structure_confidence(resolve("demo_antibody_igfold.pdb"),
                     "IgFold confidence — demo mAb (Fv, 내 실행 결과)", png)
Image(png)'''),
          md('''## 4) 레퍼런스 대조 — 커밋된 예측 구조와 얼마나 같은가

같은 서열·같은 모델이라도 실행 환경(BLAS·스레드 수)에 따라 좌표가 소수점 단위로 흔들릴 수 있어요.
그래서 **CA 좌표 RMSD** 와 사슬별 예측오차 통계로 비교합니다. (RMSD ≈ 0 이면 재현 성공)'''),
          code('''import pathlib
mine_p = pathlib.Path("my_run/demo_antibody_igfold.pdb")
if mine_p.exists():
    from Bio.PDB import PDBParser, Superimposer
    p = PDBParser(QUIET=True)
    def ca(path):
        s = p.get_structure("x", path)
        return [a for a in s.get_atoms() if a.get_id() == "CA"]
    a, b = ca(mine_p), ca("data/demo_antibody_igfold.pdb")
    print(f"CA 원자 수 — 내 결과 {len(a)} / 레퍼런스 {len(b)}")
    if len(a) == len(b):
        sup = Superimposer(); sup.set_atoms(b, a)
        print(f"CA-RMSD (내 예측 vs 커밋 예측) = {sup.rms:.3f} Å")
    for label, path in [("내 결과", mine_p), ("레퍼런스", "data/demo_antibody_igfold.pdb")]:
        d = {}
        for line in open(path):
            if line.startswith("ATOM") and line[12:16].strip() == "CA":
                d.setdefault(line[21], []).append(float(line[60:66]))
        print(label, {k: f"mean {sum(v)/len(v):.2f} / max {max(v):.2f} Å" for k, v in sorted(d.items())})
else:
    print("my_run 예측이 없어 대조를 건너뜁니다 (RUN_IGFOLD=False 였거나 실행 실패).")'''),
          md('''## 5) 3D 구조 렌더 — 예측오차 컬러링 (본문 6.2)

색은 위 그래프와 같은 잔기별 예측오차(B-factor): **파랑=신뢰 / 빨강=불확실** → 빨간 loop 가 CDR-H3.

> **PyMOL 은 pip 로 설치되지 않아요**(Colab 미지원). 그래서 이 절만은 **저장소에 커밋된 렌더 이미지**를
> 그대로 보여줍니다. 로컬에 open-source PyMOL 이 있으면 자동으로 다시 렌더해요.'''),
          code('''import shutil, subprocess
from IPython.display import Image
png = "06_structure_3d.png"
if shutil.which("pymol"):
    try:
        subprocess.run(["pymol", "-cq", str(ADV_ROOT/"scripts"/"render_06_structure.pml")],
                       cwd=str(ADV_ROOT), check=True, capture_output=True, text=True, timeout=180)
        print("PyMOL 재렌더 완료 →", png)
    except Exception as e:
        print("PyMOL 실행 실패 → 커밋된 렌더 표시:", type(e).__name__)
else:
    print("PyMOL 없음(예: Colab) → 커밋된 렌더를 표시합니다:", png)
Image(png)'''),
          md("> 다음 → 본문 [07. interface 분석](../07_interface/07_interface.md)")]
    write_nb(ROOT/"06_structure"/"06_structure_lab.ipynb", c)


# ===========================================================================
# 07 — interface lab : 1A14 를 직접 내려받아 contact 계산
# ===========================================================================
def nb_07():
    c = header("07_interface", "07_interface.md", "07 — 항원-항체 interface (1A14 직접 다운로드)",
               "RCSB 에서 1A14 를 **직접 내려받아** contact 을 계산하고(`my_run/`), 커밋된 결과와 대조해요.")
    c += [bootstrap("07_interface", pip_pkgs="pandas matplotlib biopython requests"),
          md('''## 1) 직접 실행 — 복합체 다운로드 + contact 계산 (본문 7.2)

```bash
python scripts/pdb_contacts.py --pdb 1A14 --outdir my_run/pdb                       # ① 사슬 목록 확인
python scripts/pdb_contacts.py --pdb 1A14 --chain1 H --chain2 N --cutoff 4.0 \\
    --outdir my_run/pdb --out my_run/contacts_H_N.tsv                                # ② 항원-항체
```
① 을 먼저 돌려 **사슬 ID 를 눈으로 확인**하는 게 핵심이에요 — 1A14 의 항원(neuraminidase)은 chain **N** 이에요.
네트워크가 막히면 `--fallback-cif` 로 커밋된 `data/pdb/1A14.cif` 를 씁니다(오프라인 대비).'''),
          code('''FALLBACK = ["--fallback-cif", "data/pdb/1A14.cif"]   # 다운로드 실패 시 커밋본 사용

run_tool([PY, SCRIPTS/"pdb_contacts.py", "--pdb", "1A14", "--outdir", "my_run/pdb", *FALLBACK])
ok_hn = run_tool([PY, SCRIPTS/"pdb_contacts.py", "--pdb", "1A14",
                  "--chain1", "H", "--chain2", "N", "--cutoff", "4.0",
                  "--outdir", "my_run/pdb", "--out", "my_run/contacts_H_N.tsv", *FALLBACK])
ok_hl = run_tool([PY, SCRIPTS/"pdb_contacts.py", "--pdb", "1A14",
                  "--chain1", "H", "--chain2", "L", "--cutoff", "4.0",
                  "--outdir", "my_run/pdb", "--out", "my_run/contacts_H_L.tsv", *FALLBACK])'''),
          md("## 2) 내 결과 확인 — paratope · epitope (본문 7.3)"),
          code('''import pandas as pd
def load_contacts(path):
    rows = []
    for line in open(path):
        if "atom_contacts=" in line:
            left, n = line.rstrip().split("atom_contacts=")
            a, b = left.rstrip("\\t").split("\\t")
            rows.append((a.strip(), b.strip(), int(n)))
    return pd.DataFrame(rows, columns=["paratope (H)", "epitope (N)", "atom_contacts"])

df = load_contacts(resolve("contacts_H_N.tsv")).sort_values("atom_contacts", ascending=False)
print(f"항원-항체 contact: {len(df)} residue pairs, 총 {df['atom_contacts'].sum()} atom contacts")
display(df.head(8).reset_index(drop=True))

hl = load_contacts(resolve("contacts_H_L.tsv"))
print(f"비교) H–L (VH/VL packing): {len(hl)} residue pairs — 같은 항체인데 '무엇 대 무엇'이냐로 결과가 완전히 달라져요.")'''),
          md("## 3) 내 결과 확인 — interface contact 그래프 (본문 7.3)"),
          code('''from antibody_viz import interface_contacts
from IPython.display import Image
png = "my_run/07_interface_contacts.png"
interface_contacts(resolve("contacts_H_N.tsv"),
                   "Antibody(H)–Antigen(N) contacts — 1A14 (≤4 Å, 내 실행 결과)", png)
Image(png)'''),
          md('''## 4) 레퍼런스 대조 — 커밋된 contact 결과와 같은가'''),
          code('''import pathlib
def pairs(path):
    out = {}
    for line in open(path):
        if "atom_contacts=" in line:
            left, n = line.rstrip().split("atom_contacts=")
            a, b = left.rstrip("\\t").split("\\t")
            out[(a.strip(), b.strip())] = int(n)
    return out

if pathlib.Path("my_run/contacts_H_N.tsv").exists():
    mine, ref = pairs("my_run/contacts_H_N.tsv"), pairs("data/contacts_H_N.tsv")
    print(f"내 결과 {len(mine)} pairs / 레퍼런스 {len(ref)} pairs | 완전 일치 = {mine == ref}")
    only_mine = set(mine) - set(ref); only_ref = set(ref) - set(mine)
    if only_mine or only_ref:
        print("내 결과에만:", sorted(only_mine)); print("레퍼런스에만:", sorted(only_ref))
    print("원자접촉 수 차이:", {k: (mine[k], ref[k]) for k in set(mine) & set(ref) if mine[k] != ref[k]} or "없음")
else:
    print("my_run contact 결과가 없어 대조를 건너뜁니다.")'''),
          md('''## 5) 복합체 3D 렌더 — paratope / epitope (본문 7.3)

항원(베이지 표면) + 항체 H(하늘)/L(연두) cartoon + paratope(주황 스틱)·epitope(빨강 스틱).

> 4절과 마찬가지로 **PyMOL 은 pip 설치가 안 돼요** → 커밋된 렌더를 보여줍니다(로컬에 PyMOL 이 있으면 재렌더).'''),
          code('''import shutil, subprocess
from IPython.display import Image
png = "07_complex_3d.png"
if shutil.which("pymol"):
    try:
        subprocess.run(["pymol", "-cq", str(ADV_ROOT/"scripts"/"render_07_complex.pml")],
                       cwd=str(ADV_ROOT), check=True, capture_output=True, text=True, timeout=180)
        print("PyMOL 재렌더 완료 →", png)
    except Exception as e:
        print("PyMOL 실행 실패 → 커밋된 렌더 표시:", type(e).__name__)
else:
    print("PyMOL 없음(예: Colab) → 커밋된 렌더를 표시합니다:", png)
Image(png)'''),
          md("> 다음 → 본문 [08. developability](../08_developability/08_developability.md)")]
    write_nb(ROOT/"07_interface"/"07_interface_lab.ipynb", c)


# ===========================================================================
# 08 — developability lab : liability scan 직접 실행
# ===========================================================================
def nb_08():
    c = header("08_developability", "08_developability.md", "08 — developability (liability scan 직접 실행)",
               "`liability_scan.py` 를 **직접 돌려** 스캔 결과를 `my_run/` 에 만들고 커밋본과 대조해요.")
    c += [bootstrap("08_developability", pip_pkgs="pandas matplotlib biopython"),
          md('''## 1) 직접 실행 — liability scan (본문 8.1)

```bash
python scripts/liability_scan.py data/demo_mab.fa --out my_run/liability.csv
```
motif(N-glyc sequon·NG·NS·DG) 정규식 스캔 + pI·GRAVY·Cys 홀짝을 한 번에 계산해요.
모호 잔기(X/B/Z)가 섞여도 죽지 않게 별도 컬럼으로 뺍니다.'''),
          code('''ok = run_tool([PY, SCRIPTS/"liability_scan.py", "data/demo_mab.fa",
                "--out", "my_run/liability.csv"])'''),
          md("## 2) 내 결과 확인 — 스캔 결과 표 (본문 8.2)"),
          code('''import pandas as pd
df = pd.read_csv(resolve("liability.csv"))
cols = ["id","length","pI","gravy","cysteine_count","odd_cysteine_flag","tryptophan_count","ambiguous_residues"]
display(df[cols])
print("liability motif hits:")
for m in ["N_glycosylation_NXS_T", "deamidation_NG", "deamidation_NS", "isomerization_DG"]:
    print(f"  {m}:", df[m].fillna("").tolist())
print("\\n[심화] Cys 짝수(paired) + motif 0건 → 서열 liability 깨끗")'''),
          md("## 3) 내 결과 확인 — developability 개요 그래프 (본문 8.2)"),
          code('''from antibody_viz import liability_overview
from IPython.display import Image
png = "my_run/08_liability_overview.png"
liability_overview(resolve("liability.csv"),
                   "Developability — liability scan (demo mAb, 내 실행 결과)", png)
Image(png)'''),
          md("## 4) 레퍼런스 대조 — 커밋된 스캔 결과와 같은가"),
          code('''import pandas as pd, pathlib
if pathlib.Path("my_run/liability.csv").exists():
    mine, ref = pd.read_csv("my_run/liability.csv"), pd.read_csv("data/liability.csv")
    same = mine.astype(str).equals(ref.astype(str))
    print("값 완전 일치 =", same)
    if not same:
        for c in ref.columns:
            if not mine[c].astype(str).equals(ref[c].astype(str)):
                print("차이:", c, mine[c].tolist(), "vs", ref[c].tolist())
else:
    print("my_run 스캔 결과가 없어 대조를 건너뜁니다.")'''),
          md("> 다음 → 본문 [09. repertoire & naturalness](../09_repertoire/09_repertoire.md)")]
    write_nb(ROOT/"08_developability"/"08_dev_lab.ipynb", c)


# ===========================================================================
# 09 — repertoire lab : 실제 OAS data unit 을 직접 다운로드
# ===========================================================================
def nb_09():
    c = header("09_repertoire", "09_repertoire.md", "09 — repertoire & naturalness (OAS 직접 다운로드)",
               "**진짜 OAS data unit** 을 직접 내려받아 CDR3 길이 분포를 만들고, 후보 항체의 위치를 재요.")
    c += [bootstrap("09_repertoire", pip_pkgs="pandas matplotlib anarci abnumber", hmmer=True),
          md('''## 1) 직접 실행 — OAS data unit 다운로드 + CDR3 길이 집계 (본문 9.1)

```bash
python scripts/fetch_oas_unit.py --out my_run/oas_subset.tsv.gz
python scripts/oas_cdr3_length.py my_run/oas_subset.tsv.gz --column cdr3_aa \\
    --out my_run/oas_cdr3_length_summary.csv
```
받는 unit: **Eliyahu et al. 2018 · human PBMC · heavy IgM · run ERR2843400** (productive 17,807 서열).
OAS 원본 파일은 **첫 줄이 메타데이터(JSON)** 라 그냥 읽으면 컬럼을 못 찾아요 — 스크립트가 자동 처리합니다.'''),
          code('''ok_dl = run_tool([PY, SCRIPTS/"fetch_oas_unit.py", "--out", "my_run/oas_subset.tsv.gz"])
ok_sum = run_tool([PY, SCRIPTS/"oas_cdr3_length.py", resolve("oas_subset.tsv.gz"),
                   "--column", "cdr3_aa", "--out", "my_run/oas_cdr3_length_summary.csv"])'''),
          md("## 2) 내 결과 확인 — 분포 통계 + 후보 항체의 위치 (본문 9.2)"),
          code('''import pandas as pd
from abnumber import Chain

# 후보(demo) 항체의 CDR-H3 길이도 직접 계산해요 (IMGT 정의 = OAS cdr3_aa 와 같은 기준)
seqs, name = {}, None
for line in open("data/demo_mab.fa"):
    line = line.strip()
    if line.startswith(">"): name = line[1:].split()[0]; seqs[name] = ""
    elif name: seqs[name] += line
heavy = Chain(list(seqs.values())[0], scheme="imgt")
cand = len(heavy.cdr3_seq)
print(f"후보 항체 CDR-H3 (IMGT) = {heavy.cdr3_seq} → {cand} aa")

s = pd.read_csv(resolve("oas_cdr3_length_summary.csv"))
n = s["count"].sum()
mean = (s["cdr3_len"] * s["count"]).sum() / n
pct = 100 * s.loc[s["cdr3_len"] <= cand, "count"].sum() / n
print(f"\\nOAS: n={n:,} 서열 | 평균 CDR3 {mean:.1f} aa | 범위 {s.cdr3_len.min()}–{s.cdr3_len.max()} aa")
print(f"후보({cand} aa) 는 분포의 하위 {pct:.0f} percentile → 자연 human 분포의 한복판")'''),
          md("## 3) 내 결과 확인 — CDR3 분포 그래프 (본문 9.2)"),
          code('''from antibody_viz import cdr3_length_distribution
from IPython.display import Image
png = "my_run/09_cdr3_length.png"
cdr3_length_distribution(resolve("oas_cdr3_length_summary.csv"),
    "OAS (Eliyahu 2018, human IgM heavy) — CDR3 length distribution",
    png, highlight_len=cand, highlight_label="demo CDR-H3")
Image(png)'''),
          md('''## 4) 레퍼런스 대조 — 커밋된 OAS 서브셋과 같은가

`data/oas_subset.tsv.gz` 는 **같은 OAS data unit 을 2026-07-14 에 받아 커밋해 둔 실제 데이터**예요
(합성 데이터 아님). 내가 방금 받은 것과 집계가 같아야 정상입니다.'''),
          code('''import pandas as pd, pathlib
ref = pd.read_csv("data/oas_cdr3_length_summary.csv")
if pathlib.Path("my_run/oas_cdr3_length_summary.csv").exists():
    mine = pd.read_csv("my_run/oas_cdr3_length_summary.csv")
    same = mine.equals(ref)
    print(f"내 집계 n={mine['count'].sum():,} / 레퍼런스 n={ref['count'].sum():,} | 완전 일치 = {same}")
    if not same:
        m = mine.merge(ref, on="cdr3_len", how="outer", suffixes=("_mine","_ref")).fillna(0)
        print(m[m.count_mine != m.count_ref].head(10).to_string(index=False))
        print("(OAS 가 data unit 을 갱신하면 차이가 날 수 있어요)")
else:
    print("my_run 집계가 없어 대조를 건너뜁니다.")'''),
          md("## 5) 보너스 — 내가 받은 unit 의 V/J germline usage"),
          code('''import pandas as pd
rep = pd.read_csv(resolve("oas_subset.tsv.gz"), sep="\\t")
for col, label in [("v_call", "IGHV"), ("j_call", "IGHJ")]:
    top = rep[col].astype(str).str.split("*").str[0].value_counts().head(5)
    print(f"[{label} top5]")
    for g, n in top.items():
        print(f"   {g:12s} {n:5d}  ({100*n/len(rep):.1f}%)")
print("\\n[심화] 후보 항체의 V gene 이 이 목록에 없다면 '희귀 germline' — 왜 드문지 설명할 수 있어야 해요(9.3).")'''),
          md("> 다음 → 본문 [10. 부록](../10_appendix/10_appendix.md)")]
    write_nb(ROOT/"09_repertoire"/"09_repertoire_lab.ipynb", c)


if __name__ == "__main__":
    nb_02(); nb_03(); nb_04(); nb_05(); nb_06(); nb_07(); nb_08(); nb_09()
    print("\n모든 노트북 생성 완료.")
