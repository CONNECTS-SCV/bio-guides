"""노트북 생성기 — 각 챕터 폴더에 .ipynb 생성 (Colab 실습 + 튜토리얼 1:1 정합).
실행: python gen_notebooks.py

설계 원칙
  · 모든 노트북 맨 위에 'Colab/로컬 공용 부트스트랩' 셀(저장소 클론 + 챕터 폴더 이동 + 라이브러리).
  · 각 노트북은 해당 본문(NN_*.md)의 절을 1:1로 따라가며, 학습자가 boltzgen 을 직접 돌려 my_run/ 에
    자기 결과를 만들고 그 결과로 분석·그래프를 진행(설계를 건너뛰면 커밋된 data/ 레퍼런스로 폴백).
  · 그래프는 공용 모듈 boltzgen_viz.py (advanced/ 루트) 재사용 → sys.path 에 루트 추가.
"""
import json, pathlib
ROOT = pathlib.Path(__file__).parent

def md(t):  return {"cell_type": "markdown", "metadata": {}, "source": t.splitlines(keepends=True)}
def co(s):  return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [],
                    "source": s.splitlines(keepends=True)}

# ── Colab 배지 ────────────────────────────────────────────────────────────────
# GitHub 에서 노트북을 열면 이 배지를 눌러 바로 Colab 으로 넘어갈 수 있다.
COLAB_REPO   = "CONNECTS-SCV/bio-guides"
GUIDE_PREFIX = "boltzgen/advanced"          # 저장소 루트 기준 이 가이드의 경로

def colab_badge_cell(rel_path):
    url = f"https://colab.research.google.com/github/{COLAB_REPO}/blob/main/{GUIDE_PREFIX}/{rel_path}".replace(" ", "%20")
    return {"cell_type": "markdown", "metadata": {},
            "source": [f"[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)]({url})\n"]}


def save(cells, folder, name, title):
    cells = [colab_badge_cell(f"{folder}/{name}")] + cells
    for i, cell in enumerate(cells):          # nbformat 4.5+ : 셀 id 부여(경고 제거)
        cell.setdefault("id", f"c{i:02d}")
    doc = {"cells": cells, "metadata": {
        "kernelspec": {"display_name": "Python 3 (boltzgen_env)", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.12"}, "title": title},
        "nbformat": 4, "nbformat_minor": 5}
    p = ROOT / folder / name
    p.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    print("wrote", folder + "/" + name, "(", len(cells), "cells )")


# ─────────────────────────────────────────────────────────────────────────────
# 공용 부트스트랩 — 모든 노트북의 첫 코드 셀
#   Colab: REPO_URL 클론 → 챕터 폴더로 이동 → (선택) 라이브러리 설치
#   로컬 : 챕터 폴더 안에서 열었으면 클론 없이 그대로 진행
# ─────────────────────────────────────────────────────────────────────────────
_BOOT = r'''# ====== Colab/로컬 공용 부트스트랩 (모든 챕터 공통) ======
REPO_URL = "https://github.com/CONNECTS-SCV/bio-guides.git"   # 이 가이드 저장소 (fork 했다면 본인 주소로 바꾸세요)
CLONE_AS = "bio-guides"
CHAPTER  = "__CHAPTER__"
PIP_PKGS = "__PIP__"   # 없으면 설치할 분석 라이브러리

import os, sys, subprocess, pathlib
IN_COLAB = "google.colab" in sys.modules

# HuggingFace 가중치 다운로드가 '멈춘 채' 매달리는 일을 막습니다.
# (멈춤은 예외가 안 나서 폴백이 안 걸립니다 — 타임아웃을 걸어 실패로 바꿔야 data/ 로 이어집니다)
os.environ.setdefault("HF_HUB_DOWNLOAD_TIMEOUT", "30")   # 스트림 30초 무응답 → 끊고 재시도
os.environ.setdefault("HF_HUB_ETAG_TIMEOUT", "15")

def _run(cmd):
    print("$", cmd); subprocess.run(cmd, shell=True, check=True)

_MARK = "boltzgen_viz.py"          # 이 파일이 있는 폴더가 advanced/ 루트

def _find_root():
    """advanced/ 루트를 찾는다 — 챕터 폴더 안, 루트, 클론된 저장소 어디서 열어도 동작."""
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
assert ROOT is not None, "advanced/ 루트를 못 찾았습니다. 로컬이면 이 노트북을 챕터 폴더 안에서 여세요."

ADV_ROOT = ROOT.resolve()
os.chdir(ADV_ROOT / CHAPTER)          # 이 챕터 폴더로 이동 → data/ 상대경로가 그대로 동작
sys.path.insert(0, str(ADV_ROOT))     # boltzgen_viz import 보장
import glob as _glob
if IN_COLAB and not _glob.glob("/usr/share/fonts/**/*Nanum*", recursive=True):
    # Colab 에는 한글 폰트가 없어 그래프의 한글 라벨이 □ 로 깨집니다.
    _run("apt-get -qq update"); _run("apt-get -qq install -y fonts-nanum")


# 필요한 라이브러리 확보: import 안 되는 것만 설치(Colab 새 런타임/로컬 모두 자동 대응)
import importlib, importlib.util
_IMPORT_NAME = {"scikit-learn": "sklearn", "pillow": "PIL", "biopython": "Bio"}
def _have(mod):
    try: return importlib.util.find_spec(mod) is not None
    except Exception: return False
def _ensure(pkgs):
    miss = [p for p in pkgs.split() if not _have(_IMPORT_NAME.get(p, p))]
    if miss:
        print("필요 라이브러리 설치:", " ".join(miss))
        _run(f'"{sys.executable}" -m pip -q install ' + " ".join(miss))  # python -m pip (Ch.03 권고)
        importlib.invalidate_caches()
if PIP_PKGS:
    _ensure(PIP_PKGS)

# ── 내가 만든 결과 우선, 없으면 레퍼런스 ──────────────────────────────────────
#   MY  : 이 노트북에서 내가 직접 돌려 만든 산출물
#   REF : 저장소에 커밋된 레퍼런스 결과(대조군 · 실행을 건너뛰어도 실습이 이어지도록)
MY  = pathlib.Path("my_run")
MY.mkdir(exist_ok=True)

def find_one(pattern, ref, quiet=False):
    """산출물 하나를 찾는다 — 내가 만든 my_run/ 트리를 먼저 뒤지고, 없으면 레퍼런스 폴더에서.

    파일명 규칙이 달라도(내 실행 rank1_*.cif / 레퍼런스 rank001_*.cif,
    final_<budget>_designs / final_designs) 같은 글롭으로 잡히도록 설계했습니다.
    """
    for base in (MY/"final_ranked_designs", MY/"intermediate_designs_inverse_folded", MY):
        hits = sorted(base.glob(pattern))
        if hits:
            if not quiet: print(f"[내 결과]   {hits[0]}")
            return hits[0]
    hits = sorted(pathlib.Path(ref).glob(pattern))
    assert hits, f"{ref} 에서 '{pattern}' 을 찾지 못했습니다."
    if not quiet: print(f"[레퍼런스] {hits[0]}")
    return hits[0]

def cols_in(df, *names):
    """내 실행 결과와 레퍼런스는 컬럼 구성이 조금 다를 수 있어, 있는 컬럼만 고른다."""
    missing = [c for c in names if c not in df.columns]
    if missing:
        print("(이 실행에는 없는 컬럼 — 건너뜁니다:", ", ".join(missing) + ")")
    return [c for c in names if c in df.columns]

def inherit_run(*rel_paths):
    """앞 챕터에서 이미 설계를 돌렸다면 그 결과를 이어받는다(이 챕터에서 다시 안 돌려도 됨).

    내 my_run/ 에 결과가 있으면 그대로 쓰고, 없으면 인자로 준 순서대로 앞 챕터를 찾는다.
    아무 데도 없으면 MY 를 그대로 둬서 find_one() 이 레퍼런스로 폴백하게 한다.
    """
    global MY
    if (MY / "final_ranked_designs").exists():
        return MY
    for rel in rel_paths:
        p = pathlib.Path(rel)
        if (p / "final_ranked_designs").exists():
            print("[이어받기] 앞 챕터에서 직접 돌린 결과를 사용합니다:", p)
            MY = p
            return MY
    return MY

# 내가 만든 그림은 my_ 접두어로 저장 — 저장소에 커밋된 레퍼런스 그림을 덮어쓰지 않도록.
def my_fig(name):
    return f"my_{name}"

print("ADV_ROOT :", ADV_ROOT)
print("작업 폴더 :", pathlib.Path.cwd())'''

def boot(chapter, pip="pandas matplotlib gemmi"):
    code = _BOOT.replace("__CHAPTER__", chapter).replace("__PIP__", pip)
    return [
        md(f"""## 0) Colab 준비 — 저장소 클론 & 작업 폴더 이동

이 노트북은 **Colab과 로컬 모두**에서 동작합니다.

- **Colab**: 이 셀을 그대로 실행하세요. 저장소를 클론하고 이 챕터(`{chapter}`) 폴더로 자동 이동한 뒤, `data/` 의 실제 결과로 실습합니다.
- **로컬**: 이 노트북을 `{chapter}/` 폴더 안에서 열었다면 클론 없이 그대로 진행됩니다.

> 런타임은 **기본값 그대로** 두면 됩니다."""),
        co(code),
    ]

# 전 셀 실행 시간 — 실제로 nbconvert --execute 로 측정한 값(초).
RUNTIME = {"02": "4초", "03": "19초", "04": "5초", "05": "6초", "06": "3초",
           "07": "7초", "08": "5초", "09": "3초", "10": "3초", "11": "3초"}

# 실행 배지.
#   "none"     : 도구 실행 없이 진행 (02, 06)
#   "optional" : boltzgen 설치·검증 셀 포함 (03·04)
#   "design"   : 직접 설계 실행 셀 포함 (05, 07~11)
RUN_BADGE = {
    "none": "> 런타임 변경 없이 그대로 실행하세요.",
    "optional": "> 라이브 `boltzgen run` 셀은 NVIDIA GPU 에서 동작합니다(CPU 폴백 없음) — Colab 이면 **런타임 → T4 GPU**.\n"
                "> 그 셀을 건너뛰어도 나머지는 그대로 진행됩니다.",
    "design": "> **① 직접 설계 실행 → ② 내 결과 확인 → ③ 레퍼런스 대조** 순서로 진행합니다.\n"
              "> 설계 셀은 NVIDIA GPU 에서 동작해요 — Colab 이면 **런타임 → 런타임 유형 변경 → T4 GPU**.\n"
              "> 건너뛰어도 됩니다: 그러면 저장소에 커밋된 레퍼런스 결과로 이어집니다.",
}


# 설계 셀 실측 소요 시간 — (num_designs, budget) → 배지 문구.
# 가중치가 캐시된 상태에서 6스텝 완주 기준으로 측정한 값(부록 A8).
DESIGN_RUNTIME = {
    (4, 2): "**약 5분**(실측 307초, 최종 2개)",
    (8, 4): "**약 10분**(실측 585초, 최종 4개)",
}


def design_cells(spec, protocol, num, budget, ref_note, extra_flags="", sec=1,
                 pre_files=()):
    """'직접 설계 실행' 셀 — 학습자가 자기 결과를 my_run/ 에 만든다.
    GPU 런타임이 아니면 스스로 건너뛰고, 이후 분석은 레퍼런스로 이어진다.

    pre_files: boltzgen 레포에 커밋돼 있지 않아 실행 전에 받아와야 하는 타깃 파일
               [(레포 상대경로, 다운로드 URL), ...]
    """
    took = DESIGN_RUNTIME.get((num, budget))
    time_line = f"- 소요 시간: {took} — 가중치가 이미 캐시된 상태 기준이에요.\n" if took else ""
    pre_py = ""
    if pre_files:
        pairs = ", ".join(f'("{p}", "{u}")' for p, u in pre_files)
        pre_py = f'''
    # 이 예제의 타깃 구조는 BoltzGen 레포에 커밋돼 있지 않아 먼저 받아옵니다(있으면 건너뜀).
    import urllib.request
    for _rel, _url in [{pairs}]:
        _dst = SRC / _rel
        if _dst.exists():
            print("타깃 파일 이미 있음:", _rel)
        else:
            _dst.parent.mkdir(parents=True, exist_ok=True)
            print("타깃 파일 내려받는 중:", _rel)
            urllib.request.urlretrieve(_url, _dst)
'''
    return [
        md(f"""## {sec}) 직접 돌려보기 — 내 결과 만들기

아래 셀이 **BoltzGen 을 실제로 실행**해 `my_run/` 에 내 설계 결과를 만듭니다.
Colab 이면 **런타임 → 런타임 유형 변경 → T4 GPU** 로 바꾼 뒤 실행하세요.

- 학습용으로 `num_designs={num} --budget={budget}` 규모입니다({ref_note}).
{time_line}- 첫 실행은 모델 가중치(~6GB) 다운로드가 더해져 더 걸립니다.
- **이 셀을 건너뛰어도 됩니다** — 그러면 아래 분석이 저장소의 레퍼런스 결과로 이어집니다."""),
        co(f'''SPEC, PROTOCOL = "{spec}", "{protocol}"
NUM_DESIGNS, BUDGET = {num}, {budget}

import shutil
OUT = MY.resolve()

def _gpu():
    try:
        import torch
        return torch.cuda.is_available()
    except ImportError:
        return shutil.which("nvidia-smi") is not None

if not _gpu():
    print("GPU 런타임이 아니라 설계 실행을 건너뜁니다.")
    print("  · Colab: [런타임 → 런타임 유형 변경 → T4 GPU] 후 이 셀을 다시 실행하세요.")
    print("  · 그대로 진행해도 됩니다 — 아래 분석은 레퍼런스 결과로 이어집니다.")
else:
    SRC = ADV_ROOT / ".boltzgen_src"          # 예제 명세·타깃 CIF 가 들어 있는 BoltzGen 소스
    if not SRC.exists():
        _run(f'git clone --depth 1 https://github.com/HannesStark/boltzgen.git "{{SRC}}"')
    if not _have("boltzgen"):
        _run(f'"{{sys.executable}}" -m pip -q install -e "{{SRC}}"')
{pre_py}    try:
        _run(f'cd "{{SRC}}" && boltzgen run {{SPEC}} --output "{{OUT}}" --protocol {{PROTOCOL}} '
             f'--num_designs {{NUM_DESIGNS}} --budget {{BUDGET}}{extra_flags}')
        print("\\n내 결과 →", OUT / "final_ranked_designs")
    except Exception as e:
        # 실행이 중간에 죽어도 노트북은 계속 갑니다(완료된 스텝 산출물은 my_run/ 에 남아요).
        print("\\n설계 실행이 도중에 멈췄어요:", type(e).__name__)
        print("  · 이 셀을 그대로 다시 실행하세요 — 같은 --output 폴더의 산출물을 재사용해 이어서 끝냅니다.")
        print("    (실측: 신규 실행 763초 → 중단 후 재개 486초)")
        print("  · GPU 메모리가 부족했다면 규모를 줄여보세요: NUM_DESIGNS 를 4, BUDGET 을 2 로.")
        print("  · 그대로 두고 아래로 내려가도 됩니다 — 레퍼런스 결과로 실습이 이어집니다.")'''),
    ]


def title_cell(num, name, ko, md_link, gpu="none"):
    src = ("**여러분이 직접 돌린 결과**(`my_run/`)에서 계산합니다 — 설계 셀을 건너뛰면 저장소의 레퍼런스 결과로 이어져요."
           if gpu == "design" else
           "`data/` 의 **실제 BoltzGen 실행 결과**에서 계산합니다(임의값 아님).")
    return md(f"""# {num} — {ko}

> 본문: [`{md_link}`]({md_link}) 와 **한 절씩 짝지어** 보세요.
> 이 노트북의 표·그래프·수치는 {src}
> **분석 셀 실행 {RUNTIME[num]}.**

{RUN_BADGE[gpu]}""")


cells_all = {}

# ── 02 입력 데이터 준비 ──────────────────────────────────────────────────────
c = [title_cell("02", "02_input_data_prep", "입력 데이터 준비", "02_input_data_prep.md")]
c += boot("02_input_data_prep", pip="gemmi")
c += [
md("""## 1) 타깃 구조 다운로드 (본문 2.3)
RCSB PDB 에서 타깃 좌표를 받습니다. 예시는 PD-L1 (`7uxq`)."""),
co("""import urllib.request, pathlib
work = pathlib.Path("work"); work.mkdir(exist_ok=True)
pid = "7uxq"                                  # PD-L1
cif = work / f"{pid}.cif"
if not cif.exists():
    urllib.request.urlretrieve(f"https://files.rcsb.org/download/{pid}.cif", cif)
print("다운로드:", cif, "|", cif.stat().st_size, "bytes")"""),
md("""## 2) 체인·entity 타입 확인 (gemmi)
타깃의 체인과 폴리머 종류(단백질/DNA/RNA)를 확인해 설계 명세 작성의 근거로 삼습니다."""),
co("""import gemmi
st = gemmi.read_structure(str(cif))
print("title:", st.name)
for ch in st[0]:
    kinds = {r.name for r in ch}
    poly = ch.get_polymer()
    ptype = poly.check_polymer_type() if len(poly) else "-"
    print(f"  chain {ch.name}: {len(ch):4d} residues | type={ptype} | 첫 잔기 {ch[0].name}")"""),
md("""## 3) entity 5종 — 설계 명세의 구성요소 (본문 2.2)
BoltzGen 명세는 **무엇을 만들지(설계 대상)** 와 **무엇에 붙일지(타깃)** 를 entity 로 기술합니다."""),
co('''# (a) 설계 대상: 단백질 — 길이 범위 / 고정 길이 / 고정 서열
print("- protein: { id: B, sequence: 80..140 }     # 80~140aa 중 무작위 길이로 설계")
print("- protein: { id: B, sequence: 120 }          # 고정 120aa")
print("- protein: { id: B, sequence: MKLVAA... }     # 서열 고정(재설계/스캐폴드)")
print()
# (b) 핵산 타깃
print("- dna: { id: D, sequence: ATGCGT }")
print("- rna: { id: R, sequence: AUGCGU }")
print()
# (c) 소분자 타깃: CCD 코드 또는 SMILES
print('- ligand: { id: L, ccd: ATP }                 # PDB 화학성분 사전 3글자 코드')
print('- ligand: { id: L, smiles: "CC(=O)Oc1ccccc1C(=O)O" }   # 아스피린(CCD에 없을 때)')'''),
md("""## 4) file entity — 타깃 정제·결합부위 지정 (본문 2.4~2.5)
실제 구조 파일을 타깃으로 쓸 때의 핵심 옵션을 한 명세로 모읍니다.
- `include` 쓸 체인, `exclude` 유연한 루프/무질서 영역 제거
- `binding_types` 결합 유도 활성부위, `not_binding` 그 외 표면 억제
- `reset_res_index` 잔기번호 재정렬, `structure_groups` 가시성 그룹"""),
co('''spec = """\
entities:
  - protein: { id: B, sequence: 80..140 }       # 설계할 바인더
  - file:
      path: work/7uxq.cif
      include:       [ { chain: { id: A } } ]
      exclude:       [ { chain: { id: A, res_index: 45..55 } } ]   # 유연 루프 제거(예)
      binding_types: [ { chain: { id: A, binding: 50..70 } } ]     # 결합 유도 부위
      reset_res_index: [ { chain: { id: A } } ]
      structure_groups: "all"
"""
open("work/my_spec.yaml", "w").write(spec)
print(spec)'''),
md("""## 5) 핵산(DNA/RNA) 타깃 — 자동 인식 (본문 2.7)
CIF 안의 DNA/RNA 체인은 BoltzGen 이 자동 인식하므로, 단백질 타깃과 **동일하게** `include` 만 하면 됩니다."""),
co('''dna_spec = """\
entities:
  - protein: { id: G, sequence: 40..120 }                 # DNA 결합 단백질 설계
  - file:
      path: example/denovo_zinc_finger_against_dna/zf.cif
      include: [ { chain: { id: C1 } }, { chain: { id: B1 } } ]   # DNA 이중가닥 두 체인
      structure_groups: "all"
"""
print(dna_spec)'''),
md("""## 6) 품질 체크 — `boltzgen check` (본문 2.8)
설계 명세가 올바른지 실행 전에 검증합니다. `Total designed residues: N` 과 시각화 CIF 가 나오면 정상입니다.
*(boltzgen 이 설치돼 있고 예제 yaml 이 있을 때만 실행됩니다 — 설치는 Ch.03 참고.)*"""),
co('''import shutil, subprocess, pathlib
spec_path = "example/vanilla_protein/1g13prot.yaml"   # boltzgen 레포 예제
if shutil.which("boltzgen") and pathlib.Path(spec_path).exists():
    subprocess.run(["boltzgen", "check", spec_path])
else:
    print("건너뜀: boltzgen 미설치 또는 예제 yaml 없음.")
    print("→ Colab 라이브 실행을 원하면: !git clone https://github.com/HannesStark/boltzgen.git  후")
    print("   해당 레포에서 'boltzgen check example/vanilla_protein/1g13prot.yaml'")'''),
]
cells_all[("02_input_data_prep", "02_data_prep.ipynb", "02 Data Preparation")] = c


# ── 03 설치·검증 ────────────────────────────────────────────────────────────
c = [title_cell("03", "03_install_access", "환경 설치·검증", "03_install_access.md", gpu="optional")]
c += boot("03_install_access", pip="")     # 여기선 boltzgen 자체를 설치
c += [
md("""## 1) BoltzGen 설치 (Colab) — 본문 3.2
Colab 무료 GPU(T4 등)에서도 설치됩니다. 가중치(~6GB)는 첫 `run` 때 자동 다운로드됩니다."""),
co("""import sys
if IN_COLAB:
    _run(f'"{sys.executable}" -m pip -q install boltzgen')
    # cuequivariance 커널은 cuBLAS >= 12.5 를 요구(본문 3.3). Colab 이미지에 따라 정합 보강:
    _run(f'"{sys.executable}" -m pip -q install "nvidia-cublas-cu12>=12.5" || true')
else:
    print("로컬: 이미 설치된 boltzgen_env 등을 사용하세요 (본문 3.2).")"""),
md("""## 2) 드라이버 CUDA 상한 — `nvidia-smi` (본문 3.3)
우상단 `CUDA Version: 12.x` 가 **드라이버가 지원하는 상한**입니다."""),
co("!nvidia-smi | head -n 12"),
md("""## 3) PyTorch CUDA / GPU 인식
`torch.version.cuda` 가 드라이버 상한 이하의 12.x 이고 `cuda available: True` 면 정상."""),
co("""try:
    import torch
    print("torch:", torch.__version__, "| built cuda:", torch.version.cuda)
    print("cuda available:", torch.cuda.is_available())
    if torch.cuda.is_available():
        a = torch.randn(256, 256, device="cuda"); b = torch.randn(256, 256, device="cuda")
        print("device:", torch.cuda.get_device_name(0), "| matmul ok:", bool(torch.isfinite((a @ b).sum())))
except Exception as e:
    print("torch import/실행 실패:", repr(e)[:160])
    print("→ Colab이면 [런타임 재시작] 후 재실행, 로컬이면 본문 3.3 CUDA 정합(드라이버↔torch↔cuBLAS) 확인")"""),
md("""## 3.5) 실행 로그 미리 읽기 — 커널·배치 (본문 3.1.5)
BoltzGen은 **compute capability 8 이상**에서만 가속 커널을 켭니다(그 미만이면 자동으로 끈 채 정상 실행).
아래 셀이 내 GPU 에서 커널이 켜지는지, 어떤 diffusion 배치가 쓰일지 미리 알려줍니다."""),
co("""try:
    import torch
    if not torch.cuda.is_available():
        print("GPU 없음 → 라이브 설계(boltzgen run)는 불가합니다 (CPU 폴백 없음).")
        print("   단, 분석·해석 셀은 그대로 실습할 수 있어요(레퍼런스 결과로 이어집니다).")
    else:
        cap = torch.cuda.get_device_capability()
        vram = torch.cuda.get_device_properties(0).total_memory / 1024**3
        print(f"GPU: {torch.cuda.get_device_name(0)} | capability {cap} | VRAM {vram:.1f} GB")
        print("가속 커널:", "ON" if cap[0] >= 8 else "OFF (자동 비활성 — 정상 동작, 조금 느림)")
        print("\\n[이 GPU에서의 실행 팁]")
        print("  · --num_designs 4~30 이면 diffusion 배치가 자동으로 1 — 실습 규모엔 옵션이 필요 없어요.")
        if vram < 14:
            print("  · 100개 이상 뽑을 땐 --diffusion_batch_size 1 을 명시하세요(기본값이 10이라 메모리가 큽니다).")
        if cap[0] < 8:
            print("  · bf16 미지원 카드(T4/V100)에서 정밀도 오류가 나면: --config folding trainer.precision=32")
except Exception as e:
    print("진단 실패:", repr(e)[:160])"""),
md("""## 4) cuequivariance 가속 커널
실패 시 `undefined symbol: cublasGemmGroupedBatchedEx` → cuBLAS 12.5+ 로 보강(본문 3.3 케이스 ②).

> capability 8 미만 GPU(T4 등)는 이 커널을 **애초에 쓰지 않으므로** 이 오류가 나지 않아요. 실패해도 설계는 돌아갑니다."""),
co("""try:
    from cuequivariance_ops_torch import triangle_multiplicative_update
    print("cuequivariance kernel: OK")
except Exception as e:
    print("FAILED:", repr(e)[:160])
    print("→ pip install 'nvidia-cublas-cu12>=12.5' 후 런타임 재시작")"""),
md("## 5) BoltzGen CLI 확인"),
co("""import shutil
if shutil.which("boltzgen"):
    !boltzgen --version
    !boltzgen --help 2>&1 | sed -n '1,14p'
else:
    print("boltzgen 미설치 — 1) 셀을 먼저 실행하세요.")"""),
md("""## 6) 설계 명세 검증 + (선택) 스모크 테스트 — 본문 3.6
예제는 boltzgen 레포에 있으므로, 라이브 검증을 원하면 레포를 클론합니다."""),
co("""import shutil, pathlib
if IN_COLAB and shutil.which("boltzgen") and not pathlib.Path("boltzgen-src").exists():
    _run("git clone --depth 1 https://github.com/HannesStark/boltzgen.git boltzgen-src")
spec = "boltzgen-src/example/vanilla_protein/1g13prot.yaml"
if shutil.which("boltzgen") and pathlib.Path(spec).exists():
    !boltzgen check {spec}
    print("\\n→ 6스텝을 실제로 돌려보는 건 Ch.04 노트북에서 합니다(num_designs 4, 스모크 규모).")
else:
    print("건너뜀: boltzgen/예제 미준비. 위 1) 설치 후 다시 실행하세요.")"""),
]
cells_all[("03_install_access", "03_setup_check.ipynb", "03 Setup & Check")] = c


# ── 04 기본 사용법 ──────────────────────────────────────────────────────────
c = [title_cell("04", "04_basic_usage", "파이프라인 실행·출력 구조", "04_basic_usage.md", gpu="design")]
c += boot("04_basic_usage", pip="pandas")
c += [
md("""## 1) `boltzgen run` 명령 구조 (본문 4.1)
```
boltzgen run <명세.yaml> --output <폴더> --protocol <프로토콜> --num_designs <중간 수> --budget <최종 선별 수>
```
`protein-anything` 기준 **6스텝**: design → inverse_folding → folding → design_folding → analysis → filtering."""),
co('''run_cmd = ("boltzgen run example/vanilla_protein/1g13prot.yaml "
           "--output workbench/vanilla --protocol protein-anything "
           "--num_designs 1000 --budget 50")
print(run_cmd)
print("\\n· --num_designs : 많이 뽑을수록 좋은 '꼬리'를 만남 (테스트 4~100 → 프로덕션 1k~60k)")
print("· --budget      : 다양성까지 고려한 최종 선별 수 (보통 50~200)")
print("· --steps filtering : 무거운 단계 없이 선별만 재실행(초 단위)")'''),
] + design_cells("example/vanilla_protein/1g13prot.yaml", "protein-anything", 4, 2,
                "가장 작은 스모크 규모 — 6스텝이 전부 도는지 확인하는 게 목적", sec=2) + [
md("""## 3) 출력 구조 해부 — 내가 만든 결과로 (본문 4.6)
위에서 직접 돌렸다면 `my_run/` 이, 건너뛰었다면 Ch.05 의 레퍼런스 결과(`05_result_interpretation/data/vanilla`)가
해부 대상이 됩니다. 어느 쪽이든 **같은 파일 구조**예요 — 다만 폴더·파일 이름에 `budget` 이 박히므로
(`final_<budget>_designs/`, `final_designs_metrics_<budget>.csv`) 글롭으로 찾습니다."""),
co("""REF = "../05_result_interpretation/data/vanilla"

# steps.yaml 은 출력 루트(<out>/steps.yaml)에 생깁니다 — final_ranked_designs/ 안이 아니라.
steps = find_one("steps.yaml", REF)
print("· steps.yaml (실행된 스텝 매니페스트):")
print("   ", steps.read_text().strip().replace("\\n", "\\n    "))

# 최종 CIF: 라이브는 final_<budget>_designs/, 레퍼런스는 final_designs/ → 한 글롭으로 처리
csv = find_one("final_designs_metrics_*.csv", REF)
base = csv.parent
cifs = sorted(base.glob("final*designs/*.cif"))
print("\\n· 최종 디자인 CIF (순위별 단일 파일 — 서열+구조 포함):")
for p in cifs[:5]:
    print("   ", p.parent.name + "/" + p.name)
print("    ... 총", len(cifs), "개")

print("\\n· 메트릭 CSV:")
for f in sorted(base.glob("*metrics*.csv")):
    print(f"    {f.name:38s} ({f.stat().st_size} bytes)")"""),
md("""꼭 기억할 점(본문 4.6):
- 최종 디자인 = `final_ranked_designs/final_<budget>_designs/rankN_<name>_K.cif`
  (폴더가 아니라 **순위 붙은 단일 CIF**, 서열·구조 내장. `budget=2` 로 돌렸으면 `final_2_designs/`)
- 메트릭 = `final_designs_metrics_<budget>.csv`(최종셋) + `all_designs_metrics.csv`(전체), 한 디자인 = 한 행
- 인터페이스 분석은 **refold 기준**(최종 CIF). inverse_folded 직후 파일은 측쇄가 원점에 뭉쳐 있음."""),
co("""import pandas as pd
df = pd.read_csv(csv)
print("디자인 수:", len(df), "| 컬럼 수:", df.shape[1])
df[cols_in(df, "id", "final_rank", "design_ptm", "design_to_target_iptm",
           "filter_rmsd")].sort_values("final_rank")"""),
]
cells_all[("04_basic_usage", "04_run_pipeline.ipynb", "04 Run Pipeline")] = c


# ── 05 결과 해석·시각화 ─────────────────────────────────────────────────────
c = [title_cell("05", "05_result_interpretation", "결과 해석·시각화", "05_result_interpretation.md", gpu="design")]
c += boot("05_result_interpretation", pip="pandas matplotlib")
c += design_cells("example/vanilla_protein/1g13prot.yaml", "protein-anything", 8, 4,
                  "레퍼런스 결과는 num_designs=100")
c += [
co("""from boltzgen_viz import load_metrics, metrics_overview, compare_bars
import pandas as pd
# Ch.04 에서 스모크 실행을 했다면 그 결과를 이어받습니다(05에서 다시 안 돌려도 돼요)
inherit_run("../04_basic_usage/my_run")
CSV = str(find_one("final_designs_metrics_*.csv", "data/vanilla"))
df = pd.read_csv(CSV)
print("디자인:", len(df), "| 전체 컬럼:", df.shape[1], "(메트릭 240여 종)")"""),
md("""## 1) 핵심 메트릭 7군 (본문 5.1~5.7)
신뢰도(pTM/ipTM) · 위치오차(PAE) · 구조편차(RMSD) · 인터페이스(H-bond/ΔSASA) 를 한 표로."""),
co("""df[cols_in(df, "id", "final_rank", "design_ptm", "design_to_target_iptm",
           "min_design_to_target_pae", "filter_rmsd", "plip_hbonds_refolded",
           "delta_sasa_refolded")].sort_values("final_rank")"""),
md("""## 2) 2×2 메트릭 개요 그래프 (스타일 매칭)
pTM(보라)·ipTM(주황)·RMSD(청록) 바 + 길이↔H-bond 산점도. 임계선: pTM 0.7 / ipTM 0.5 / RMSD 2.0Å.

> 내가 만든 그림은 `my_05_vanilla_metrics.png` 로 저장돼요(본문에 실린 레퍼런스 그림을 덮어쓰지 않도록)."""),
co("""rows = load_metrics(CSV)
FIG = my_fig("05_vanilla_metrics.png")
metrics_overview(rows, "Vanilla Protein — Design Metrics Overview", FIG)
from IPython.display import Image; Image(FIG)"""),
md("""## 3) 메트릭 간 상관관계
각 메트릭이 독립적 정보를 주는지 확인 → 하나만 보지 말고 종합 판단.

> 직접 돌린 결과(4~8개)는 표본이 작아 상관계수가 불안정해요 — 경향만 보세요."""),
co("""m = df[cols_in(df, "design_ptm", "design_to_target_iptm", "filter_rmsd",
                "plip_hbonds_refolded", "delta_sasa_refolded")].astype(float)
m.corr().round(2)"""),
md("""## 4) 보조 분석 파일 (analysis 스텝 산출)
`aggregate_metrics_analyze.csv`(타깃 요약) / `per_target_metrics_analyze.csv`(타깃별)."""),
co("""import pandas as pd
for name in ["aggregate_metrics_analyze.csv", "per_target_metrics_analyze.csv"]:
    try:
        p = find_one(name, "data/vanilla")
        a = pd.read_csv(p); print(p, "→", a.shape); display(a.head(3))
    except Exception as e:
        print(name, "건너뜀:", e)"""),
md("""## 5) 해석 요점 (본문 5.8~5.10) — 내 결과의 실제 수치로

읽는 원칙(어느 결과에나 적용):

- **ipTM**(`design_to_target_iptm`)이 결합의 핵심 지표 — 가장 높은 것부터 후보로 봄.
- **RMSD**(`filter_rmsd`)는 자기일관성 — 낮을수록 "설계한 모양이 서열로 재현"됨.
- **pTM** 이 높아도 ipTM 이 낮을 수 있어 **함께** 봐야 함(둘은 다른 걸 잼).
- 순위는 `rank_*` 들을 종합한 `final_rank`. pLDDT(`complex_plddt`)는 순위의 주지표가 아님.

아래 셀이 **여러분 데이터에서** 직접 뽑아 줍니다. 본문 5.10 의 구체적 수치
(rank 5·6·8·9·10 이 ipTM 0.6 이상 등)는 **레퍼런스 실행(num_designs=100, budget=10)** 기준이라,
직접 돌린 결과(4~8개)와는 rank 번호도 값도 다릅니다 — 표본이 작으니 당연해요."""),
co("""n = len(df)
print(f"내 결과: 디자인 {n}개 (레퍼런스는 10개 — rank 번호가 다른 게 정상)\\n")
k = min(3, n)
print(f"ipTM 상위 {k}:")
print(df.nlargest(k, "design_to_target_iptm")[["final_rank","id","design_to_target_iptm"]].to_string(index=False))
print(f"\\nRMSD 최저 {k}:")
print(df.nsmallest(k, "filter_rmsd")[["final_rank","id","filter_rmsd"]].to_string(index=False))
print("\\npTM 최고:", df.loc[df.design_ptm.idxmax(), ["final_rank","id","design_ptm"]].to_dict())
print("\\nipTM 0.6 이상:", sorted(df.loc[df.design_to_target_iptm >= 0.6, "final_rank"].tolist()) or "없음")"""),
]
cells_all[("05_result_interpretation", "05_analysis_viz.ipynb", "05 Analysis & Viz")] = c


# ── 06 고급 필터링·자동화 ───────────────────────────────────────────────────
c = [title_cell("06", "06_advanced_ai", "고급 필터링·자동화", "06_advanced_ai.md")]
c += boot("06_advanced_ai", pip="pandas matplotlib")
c += [
md("""## 1) 전체 디자인 메트릭 로드 (필터링 전)
`all_designs_metrics.csv` 는 선별 전 모든 디자인. 여기에 직접 필터를 실험합니다."""),
co("""import pandas as pd
# Ch.05 또는 Ch.04 에서 직접 돌린 결과가 있으면 그걸 이어서 씁니다(먼저 찾는 쪽 우선)
inherit_run("../05_result_interpretation/my_run", "../04_basic_usage/my_run")
df = pd.read_csv(find_one("all_designs_metrics.csv", "data/vanilla"))
print("총 디자인:", len(df))
df[cols_in(df, "id", "design_ptm", "design_to_target_iptm", "filter_rmsd",
           "plip_hbonds_refolded")].head()"""),
md("""## 2) 맞춤 하드 필터 (실제 컬럼명)
ipTM>0.5 · pTM>0.7 · RMSD<2.0Å 동시 통과만 남깁니다."""),
co("""f = df[(df["design_to_target_iptm"] > 0.5) & (df["design_ptm"] > 0.7) & (df["filter_rmsd"] < 2.0)]
print("필터 통과:", len(f), "/", len(df))
f[["id", "design_to_target_iptm", "design_ptm", "filter_rmsd"]].sort_values(
    "design_to_target_iptm", ascending=False)"""),
md("""## 3) CLI 고급 필터 옵션 (본문 6.4) — pandas 실험을 그대로 명령으로
| 옵션 | 의미 |
|------|------|
| `--metrics_override k=w` | 메트릭 가중치(클수록 덜 중요) |
| `--additional_filters 'feat<2.0'` | 하드 필터 추가 |
| `--alpha 0.3` | 다양성↑(높을수록) vs 품질↑(낮을수록) |
| `--size_buckets 80-100:5` | 길이대별 할당 |"""),
co('''cli = ("boltzgen run spec.yaml --output out --steps filtering \\\\\\n"
       "  --metrics_override plip_hbonds_refolded=4 delta_sasa_refolded=2 \\\\\\n"
       "  --additional_filters 'designfolding-filter_rmsd<2.0' \\\\\\n"
       "  --alpha 0.3 --size_buckets 80-100:5 100-140:5")
print(cli)
print("\\n핵심 패턴(본문 6.2): 무거운 design~analysis 는 한 번만, filtering 은 기준 바꿔가며 여러 번(초 단위).")'''),
md("""## 4) 파라미터 스윕 골격 + 결과 비교 (본문 6.3)
설정을 바꿔가며 돌리고, 평균 ipTM 으로 비교합니다. 여기선 **필터 전/후 그룹**으로 `compare_bars` 를 시연합니다."""),
co("""import itertools
for budget, num in itertools.product([20, 50], [1000, 5000]):
    print(f"boltzgen run design.yaml --budget {budget} --num_designs {num} --output sweep/b{budget}_n{num}")"""),
co("""from boltzgen_viz import load_metrics, compare_bars
all_rows = load_metrics(str(find_one("all_designs_metrics.csv", "data/vanilla", quiet=True)))
passed   = [r for r in all_rows if r["design_to_target_iptm"] > 0.5
            and r["design_ptm"] > 0.7 and r["filter_rmsd"] < 2.0]
compare_bars({"all designs": all_rows, "hard-filtered": passed},
             "design_to_target_iptm", "Filtering Effect — mean ipTM",
             "mean ipTM", my_fig("06_filter_compare.png"), thr=0.5, thr_label="Good (0.5)")
from IPython.display import Image; Image(my_fig("06_filter_compare.png"))"""),
md("""## 5) 계층적 스크리닝 (본문 6.1)
Level1 (num_designs 1e4, budget 200) → 명세 제약 강화 → Level2 (5e3, budget 20) → 상위 5~10 실험.
**규모가 품질을 만든다** — 테스트는 작게, 프로덕션은 크게."""),
]
cells_all[("06_advanced_ai", "06_advanced_filtering.ipynb", "06 Advanced Filtering")] = c


# ── 07 펩타이드·고리형 (신규) ───────────────────────────────────────────────
c = [title_cell("07", "07_peptide_cyclic", "펩타이드·고리형(cyclotide) 실습", "07_peptide_cyclic.md", gpu="design")]
c += boot("07_peptide_cyclic", pip="pandas matplotlib gemmi")
c += design_cells("example/cyclotide/3ivq.yaml", "peptide-anything", 8, 4,
                  "레퍼런스 결과는 num_designs=100")
c += [
md("""## 1) 실행 명령 (본문 7) — `peptide-anything`
```bash
boltzgen run example/cyclotide/3ivq.yaml --output workbench/cyclotide \\
  --protocol peptide-anything --num_designs 100 --budget 10
```
펩타이드 프로토콜은 **자유 Cys 자동 금지**·**design_folding 생략(5스텝)**. 타깃은 cyclotide `3ivq`(34aa, 6 Cys, cystine knot)."""),
co("""from boltzgen_viz import load_metrics, metrics_overview
import pandas as pd
CSV = str(find_one("final_designs_metrics_*.csv", "data/cyclotide"))
df = pd.read_csv(CSV)
df[["id", "final_rank", "design_ptm", "design_to_target_iptm",
    "filter_rmsd", "plip_hbonds_refolded", "num_design"]].sort_values("final_rank")"""),
md("""## 2) 서열·시스테인 보존 검증
고리형 cyclotide 는 **34aa**, cystine knot 을 이루는 **Cys 6개**가 핵심. 실제 설계 서열에서 직접 확인합니다.
(`num_design`=28 은 재설계 영역 길이, 전체 사슬은 34aa.)"""),
co("""for _, r in df.sort_values("final_rank").head(5).iterrows():
    s = str(r["designed_chain_sequence"]); cys = [i for i, a in enumerate(s) if a == "C"]
    print(f"rank{int(r['final_rank'])} {r['id']:9s} len={len(s)} Cys={len(cys)} @ {cys}")
print("\\n→ 대부분 34aa·Cys 6개(knot). 일부는 추가 Cys 가 섞일 수 있음(생성 다양성).")"""),
md("""## 3) 메트릭 그래프 — 길이 고정형이라 4번째 패널은 H-bond 바"""),
co("""rows = load_metrics(CSV)
metrics_overview(rows, "Cyclotide (3ivq) — Design Metrics Overview",
                 my_fig("07_cyclotide_metrics.png"), panel4="hbonds")
from IPython.display import Image; Image(my_fig("07_cyclotide_metrics.png"))"""),
md("""## 4) Disulfide(이황화) 거리 확인 — 최종 CIF 에서 (gemmi)
cystine knot 이면 SG–SG 거리가 **~2.0Å** 인 쌍이 3개 보여야 합니다."""),
co("""import gemmi, itertools
top_id = df.sort_values("final_rank").iloc[0]["id"]          # 내 결과든 레퍼런스든 1위 디자인
cif = find_one(f"final*designs/*{top_id}*.cif", "data/cyclotide")
st = gemmi.read_structure(str(cif))
sg = [(ch.name, res.seqid.num, atom.pos)
      for ch in st[0] for res in ch if res.name == "CYS"
      for atom in res if atom.name == "SG"]
print(cif.name, "| SG 원자:", len(sg))
pairs = [(a, b, a[2].dist(b[2])) for a, b in itertools.combinations(sg, 2)]
for a, b, d in sorted(pairs, key=lambda x: x[2])[:4]:
    flag = "  <-- disulfide" if d < 2.5 else ""
    print(f"  CYS{a[1]}–CYS{b[1]} : {d:.2f} A{flag}")"""),
md("""## 5) 해석 요점 (본문 7)
- **ipTM** 최고는 rank 1 의 **0.508** — 작은 고리 펩타이드라 절대값은 단백질-단백질보다 낮게 나오는 편.
- **RMSD** 는 모두 ~2.3Å 이하(자기일관성 양호), rank 4 가 **1.15Å** 로 최저.
- cyclic·disulfide 제약이 지켜졌는지(2·4 셀)가 펩타이드 설계의 합격선."""),
]
cells_all[("07_peptide_cyclic", "07_peptide_lab.ipynb", "07 Peptide / Cyclic Lab")] = c


# ── 08 항체 Fab ─────────────────────────────────────────────────────────────
c = [title_cell("08", "08_antibody_fab", "항체 Fab 실습 + developability", "08_antibody_fab.md", gpu="design")]
c += boot("08_antibody_fab", pip="pandas matplotlib")
c += design_cells("example/fab_targets/pdl1.yaml", "antibody-anything", 8, 4,
                  "레퍼런스 결과는 num_designs=30",
                  # pdl1.yaml 이 참조하는 7uxq.cif 는 BoltzGen 레포에 커밋돼 있지 않음 → 먼저 받아온다
                  pre_files=[("example/fab_targets/7uxq.cif",
                              "https://files.rcsb.org/download/7uxq.cif")])
c += [
md("""## 1) 실행 명령 (본문 8) — `antibody-anything`
```bash
curl -sSL -o example/fab_targets/7uxq.cif https://files.rcsb.org/download/7uxq.cif
boltzgen run example/fab_targets/pdl1.yaml --output workbench/fab \\
  --protocol antibody-anything --num_designs 30 --budget 10
```
타깃 PD-L1(`7uxq`) + 임상 항체 14종 scaffold 의 CDR 재설계(framework 보존). 이 결과는 **사전설계 CDR → analysis/filtering 2스텝**.

> `pdl1.yaml` 은 타깃 구조로 `7uxq.cif` 를 참조하는데, 이 파일은 **BoltzGen 레포에 들어 있지 않아요** — 그래서 위 `curl` 로 RCSB 에서 먼저 받아야 합니다. 위 설계 셀은 이 다운로드를 자동으로 해 줘요(이미 있으면 건너뜀)."""),
co("""from boltzgen_viz import load_metrics, metrics_overview
import pandas as pd
CSV = str(find_one("final_designs_metrics_*.csv", "data/fab"))
df = pd.read_csv(CSV)
df[cols_in(df, "id", "final_rank", "design_ptm", "design_to_target_iptm",
           "filter_rmsd", "plip_hbonds_refolded", "num_design",
           "liability_score")].sort_values("final_rank")"""),
md("""## 2) 메트릭 그래프"""),
co("""rows = load_metrics(CSV)
FIG = my_fig("08_fab_metrics.png")
metrics_overview(rows, "Antibody Fab (PD-L1) — Design Metrics Overview", FIG)
from IPython.display import Image; Image(FIG)"""),
md("""## 3) Developability — liability 모티프 분포 (본문 8.6)
`liability_score`(낮을수록 개발성 우수) 와 위험 모티프(`*_count`)들. 항체/나노바디에서만 의미 있는 지표."""),
co("""mot = [col for col in df.columns if col.startswith("liability_") and col.endswith("_count")]
print("위험 모티프 컬럼:", [m.replace('liability_','').replace('_count','') for m in mot])
display(df[["id", "liability_score"] + mot].set_index("id"))
print("liability_score 순(낮을수록 좋음):")
print(df[["final_rank", "id", "liability_score"]].sort_values("liability_score").to_string(index=False))"""),
md("""## 4) Framework 보존 확인 (VH/VL 모두)
Fab 는 **중쇄(VH)와 경쇄(VL)** 가 섞여 나옵니다. VH 는 `EVQLVE…`/`QVQLVE…`, 경쇄(κ)는 `DIQMTQ…`/`EIVLTQ…` framework 로 시작하고,
도메인 내 **보존 Cys 2개**와 표준 말단(`…WGQGT…`(VH) / `…FGQGTKVEIK`(VL))을 유지해야 정상입니다."""),
co('''def chain_kind(s):
    """말단 J-region 모티프로 중쇄/경쇄(κ/λ) 판별 — N말단 prefix보다 견고."""
    if "WGQG" in s[-15:]:                                    # 중쇄 J: …WGQGT(L/T)VTVSS
        return "VH"
    if s.endswith(("EIK", "EIKR")) or "FGQGTK" in s[-14:]:   # κ 경쇄 J: …FGQGTKVEIK
        return "VL-κ"
    if "LTVL" in s[-7:] or "FGGGTK" in s[-14:] or "FGSGTK" in s[-14:]:  # λ 경쇄 J: …FGGGTKLTVL
        return "VL-λ"
    return "?"
for _, r in df.sort_values("final_rank").head(5).iterrows():
    s = str(r["designed_chain_sequence"])
    print(f"rank{int(r['final_rank'])} {r['id']:8s} {chain_kind(s):5s} | len={len(s)} "
          f"| Cys={s.count('C')} | {s[:11]}… …{s[-10:]}")
print("\\n→ 중쇄(VH)·경쇄(κ/λ) framework 말단 J-region + 보존 Cys 2개가 유지되면 정상(CDR만 재설계).")'''),
md("""## 5) 해석 요점 (본문 8)
- **ipTM** 최고는 rank 1·4·5 의 **0.46~0.49**. RMSD 는 rank 1·2·3 이 **<2Å** 로 우수.
- 같은 ipTM 이면 **liability_score 가 낮은**(rank 1=90) 쪽이 개발 친화적.
- num_designs=30 의 소규모 결과 — 실전은 1k+ 권장."""),
]
cells_all[("08_antibody_fab", "08_fab_lab.ipynb", "08 Antibody Fab Lab")] = c


# ── 09 나노바디 ─────────────────────────────────────────────────────────────
c = [title_cell("09", "09_nanobody", "나노바디(VHH) 실습", "09_nanobody.md", gpu="design")]
c += boot("09_nanobody", pip="pandas matplotlib")
c += design_cells("example/nanobody_against_penguinpox/penguinpox.yaml", "nanobody-anything", 8, 4,
                  "레퍼런스 결과는 num_designs=30")
c += [
md("""## 1) 실행 명령 (본문 9) — `nanobody-anything`
```bash
boltzgen run example/nanobody_against_penguinpox/penguinpox.yaml --output workbench/nanobody \\
  --protocol nanobody-anything --num_designs 30 --budget 10
```
타깃 penguinpox(`9bkq`) + 나노바디 scaffold 4종. 단일 도메인(VHH)이라 CDR3 만 다양화."""),
co("""from boltzgen_viz import load_metrics, metrics_overview
import pandas as pd
CSV = str(find_one("final_designs_metrics_*.csv", "data/nanobody"))
df = pd.read_csv(CSV)
df[["id", "final_rank", "design_ptm", "design_to_target_iptm", "filter_rmsd",
    "plip_hbonds_refolded", "num_design", "liability_score"]].sort_values("final_rank")"""),
md("""## 2) 메트릭 그래프 — CDR 외 길이가 거의 고정 → 4번째 패널은 H-bond 바"""),
co("""rows = load_metrics(CSV)
metrics_overview(rows, "Nanobody (Penguinpox) — Design Metrics Overview",
                 my_fig("09_nanobody_metrics.png"), panel4="hbonds")
from IPython.display import Image; Image(my_fig("09_nanobody_metrics.png"))"""),
md("""## 3) VHH Framework 보존 + 재설계 영역
나노바디는 **`EVQLVESGGG…`** framework 가 보존되고 `num_design`(재설계 CDR 영역 길이)만 달라집니다."""),
co("""for _, r in df.sort_values("final_rank").head(5).iterrows():
    s = str(r["designed_chain_sequence"])
    print(f"rank{int(r['final_rank'])} {r['id']:14s} fw_ok={s.startswith('EVQLVESGGG')} "
          f"| len={len(s)} | 재설계영역(num_design)={int(r['num_design'])} | {s[:18]}…")"""),
md("""## 4) 해석 요점 (본문 9.6)
- **ipTM 이 0.2 대로 낮고 RMSD 가 큰** 디자인이 보입니다(rank 2~). 이건 실패가 아니라 **소표본(num_designs=30)** 탓.
- rank 1 은 ipTM **0.252**, RMSD **1.43Å** 로 가장 균형 잡힘.
- **규모가 품질을 만든다** — 실전은 1k+ 로 키우면 ipTM 0.5+ 가 꼬리에서 나옵니다."""),
]
cells_all[("09_nanobody", "09_nanobody_lab.ipynb", "09 Nanobody Lab")] = c


# ── 10 소분자·친화도 (신규) ─────────────────────────────────────────────────
c = [title_cell("10", "10_small_molecule", "소분자 결합 + 친화도 예측 실습", "10_small_molecule.md", gpu="design")]
c += boot("10_small_molecule", pip="pandas matplotlib")
c += design_cells("example/protein_binding_small_molecule/chorismite.yaml", "protein-small_molecule", 8, 4,
                  "레퍼런스 결과는 num_designs=30")
c += [
md("""## 1) 실행 명령 (본문 10) — `protein-small_molecule`
```bash
boltzgen run example/protein_binding_small_molecule/chorismite.yaml --output workbench/sm \\
  --protocol protein-small_molecule --num_designs 3000 --budget 40
```
소분자 프로토콜은 **affinity 스텝 추가 → 7스텝**. 타깃은 chorismate 전이상태유사체(TSA). 소분자는 까다로워 디자인을 많이(3,000+) 권장."""),
co("""from boltzgen_viz import load_metrics, metrics_overview
import pandas as pd
CSV = str(find_one("final_designs_metrics_*.csv", "data/small_molecule"))
df = pd.read_csv(CSV)
df[["id", "final_rank", "design_ptm", "design_to_target_iptm", "filter_rmsd",
    "plip_hbonds_refolded", "delta_sasa_refolded",
    "affinity_pred_value", "affinity_probability_binary", "num_design"]].sort_values("final_rank")"""),
md("""## 2) 메트릭 그래프 — 4번째 패널 = 예측 친화도(affinity)"""),
co("""rows = load_metrics(CSV)
metrics_overview(rows, "Small-Molecule Binder (chorismate) — Design Metrics Overview",
                 my_fig("10_small_molecule_metrics.png"), panel4="affinity")
from IPython.display import Image; Image(my_fig("10_small_molecule_metrics.png"))"""),
md("""## 3) 친화도 랭킹 해석 (본문 10.5)
`affinity_pred_value` 는 **클수록 강한 결합 예측**, `affinity_probability_binary` 는 결합 확률.
**절대값을 프로토콜 간 비교하지 말 것** — 같은 실행 안에서의 상대 순위로만 사용."""),
co("""print("affinity_pred_value 상위 (강한 결합 예측):")
print(df.nlargest(5, "affinity_pred_value")[
    ["final_rank", "id", "affinity_pred_value", "affinity_probability_binary",
     "design_to_target_iptm"]].to_string(index=False))
print("\\nipTM 범위:", round(df.design_to_target_iptm.min(),3), "~", round(df.design_to_target_iptm.max(),3),
      "(소분자는 단백질-단백질보다 높게 나오는 경향)")"""),
md("""## 4) Pocket 품질 — 묻힘(ΔSASA)·수소결합
포켓이 소분자를 잘 감싸면 `delta_sasa_refolded`(묻힌 표면적)가 크고 RMSD 가 작습니다."""),
co("""df["_pocket"] = df["delta_sasa_refolded"].astype(float)
print(df[["final_rank","id","delta_sasa_refolded","plip_hbonds_refolded","filter_rmsd"]]
      .sort_values("delta_sasa_refolded", ascending=False).head(5).to_string(index=False))
print("\\nRMSD 최저(활성부위 재현 우수):", df.loc[df.filter_rmsd.idxmin(),
      ["final_rank","id","filter_rmsd"]].to_dict())"""),
md("""## 5) 해석 요점 (본문 10)
- **ipTM 0.72~0.84** (rank 3 의 **0.841** 최고), **RMSD 0.57~1.76Å** 로 전반적으로 우수.
- 친화도는 rank 2·9·10 의 `affinity_pred_value`(**2.39/2.49/2.71**)가 높음 → ipTM·RMSD 와 **함께** 보고 선별.
- 외부 검증(AutoDock Vina 도킹, MD)으로 교차 확인 권장."""),
]
cells_all[("10_small_molecule", "10_small_molecule_lab.ipynb", "10 Small-Molecule Lab")] = c


# ── 11 핵산(DNA/RNA) ────────────────────────────────────────────────────────
c = [title_cell("11", "11_nucleic_acid", "핵산(DNA/RNA) 결합 단백질 실습", "11_nucleic_acid.md", gpu="design")]
c += boot("11_nucleic_acid", pip="pandas matplotlib")
c += design_cells("example/denovo_zinc_finger_against_dna/zinc_finger.yaml", "protein-anything", 8, 4,
                  "레퍼런스 결과는 num_designs=30")
c += [
md("""## 1) DNA 결합 단백질 (zinc finger) — 본문 11
```bash
boltzgen run example/denovo_zinc_finger_against_dna/zinc_finger.yaml --output workbench/dna \\
  --protocol protein-anything --num_designs 30 --budget 10
```
DNA/RNA 체인은 자동 인식되어 단백질 타깃과 동일하게 다룹니다."""),
co("""from boltzgen_viz import load_metrics, metrics_overview, compare_bars
import pandas as pd
DNA_CSV = str(find_one("final_designs_metrics_*.csv", "data/dna"))
dna = pd.read_csv(DNA_CSV)
dna[["id", "final_rank", "design_ptm", "design_to_target_iptm", "filter_rmsd",
     "plip_hbonds_refolded", "num_design"]].sort_values("final_rank")"""),
md("""## 2) DNA 메트릭 그래프 — H-bond 가 매우 많음(인산 골격 정전기)"""),
co("""rows = load_metrics(DNA_CSV)
metrics_overview(rows, "DNA-binding (Zinc Finger) — Design Metrics Overview", my_fig("11_dna_metrics.png"))
from IPython.display import Image; Image(my_fig("11_dna_metrics.png"))"""),
md("""## 3) RNA 타깃 — 준비·실행은 DNA 와 동일 (본문 11.6)
RNA 체인이 든 CIF 를 받아 `include` 만 하면 됩니다.
```yaml
entities:
  - protein: { id: P, sequence: 60..120 }
  - file: { path: rna_target.cif, include: [ { chain: { id: R } } ], structure_groups: "all" }
```"""),
co("""rna = pd.read_csv("data/rna/final_designs_metrics_10.csv")
display(rna[["id", "final_rank", "design_ptm", "design_to_target_iptm", "filter_rmsd",
             "plip_hbonds_refolded", "num_design"]].sort_values("final_rank"))
rows = load_metrics("data/rna/final_designs_metrics_10.csv")
metrics_overview(rows, "RNA-binding — Design Metrics Overview", my_fig("11_rna_metrics.png"))
from IPython.display import Image; Image(my_fig("11_rna_metrics.png"))"""),
md("""## 4) DNA vs RNA — 인터페이스 H-bond 비교
이중가닥 DNA 는 인산 골격이 많아 H-bond 가 RNA(단일가닥 헤어핀)보다 훨씬 많습니다."""),
co("""dna_rows = load_metrics(DNA_CSV)
rna_rows = load_metrics("data/rna/final_designs_metrics_10.csv")
compare_bars({"DNA (zinc finger)": dna_rows, "RNA (hairpin)": rna_rows},
             "plip_hbonds_refolded", "DNA vs RNA — mean interface H-bonds",
             "mean H-bond count", my_fig("11_dna_rna_hbonds.png"))
from IPython.display import Image; Image(my_fig("11_dna_rna_hbonds.png"))"""),
md("""## 5) 해석 요점 (본문 11)
- **DNA**: H-bond 평균 **~30**(rank 3 은 42), ipTM **0.50~0.67** — 골격 정전기 결합이 핵심.
- **RNA**: H-bond 평균 **~9**(단일가닥 헤어핀), ipTM **0.29~0.45** — DNA 보다 낮음.
- 둘 다 `protein-anything` 으로 처리되며, 핵산은 별도 프로토콜이 필요 없습니다(자동 인식)."""),
]
cells_all[("11_nucleic_acid", "11_nucleic_lab.ipynb", "11 Nucleic Acid Lab")] = c


# ── 저장 ────────────────────────────────────────────────────────────────────
for (folder, name, title), cells in cells_all.items():
    save(cells, folder, name, title)

print("\n노트북", len(cells_all), "종 생성 완료 (각 챕터 폴더, Colab/로컬 공용).")
