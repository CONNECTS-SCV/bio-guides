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
_BOOT = r'''REPO_URL = "https://github.com/CONNECTS-SCV/bio-guides.git"   # fork 했다면 본인 주소로 바꾸세요
CLONE_AS = "bio-guides"
CHAPTER  = "__CHAPTER__"
PIP_PKGS = "__PIP__"   # 없으면 설치할 분석 라이브러리

import os, sys, subprocess, pathlib
IN_COLAB = "google.colab" in sys.modules

# HF 가중치 다운로드가 멈춘 채 매달리지 않도록 타임아웃을 겁니다.
os.environ.setdefault("HF_HUB_DOWNLOAD_TIMEOUT", "30")   # 스트림 30초 무응답 → 끊고 재시도
os.environ.setdefault("HF_HUB_ETAG_TIMEOUT", "15")

def _run(cmd):
    print("$", cmd); subprocess.run(cmd, shell=True, check=True)

_MARK = "boltzgen_viz.py"          # 이 파일이 있는 폴더가 advanced/ 루트

def _find_root():
    """advanced/ 루트를 찾습니다."""
    cwd = pathlib.Path.cwd()
    for base in (cwd, *list(cwd.parents)[:3]):
        if (base / _MARK).exists():
            return base
    for pat in (f"*/{_MARK}", f"*/*/{_MARK}", f"*/*/*/{_MARK}"):   # 클론 직후: cwd 아래로만 깊이 3까지
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

# import 안 되는 패키지만 설치합니다.
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

# 내 결과는 my_run/ 에 쌓이고, 없으면 커밋된 레퍼런스로 폴백합니다.
MY  = pathlib.Path("my_run")
MY.mkdir(exist_ok=True)

def find_one(pattern, ref, quiet=False):
    """my_run/ 에서 먼저 찾고, 없으면 레퍼런스 폴더에서 찾습니다."""
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
    """앞 챕터에서 돌린 설계 결과를 이어받습니다(없으면 레퍼런스로 폴백)."""
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

# 레퍼런스 그림을 덮어쓰지 않도록 my_ 접두어.
def my_fig(name):
    return f"my_{name}"

print("작업 폴더 :", pathlib.Path.cwd())'''

def boot(chapter, pip="pandas matplotlib gemmi"):
    code = _BOOT.replace("__CHAPTER__", chapter).replace("__PIP__", pip)
    return [
        md(f"""## 0) 준비 — 저장소 클론 & 작업 폴더 이동

이 셀이 저장소를 클론하고 `{chapter}/` 로 이동합니다. 로컬에서 `{chapter}/` 안에 열었다면 클론 없이 진행돼요."""),
        co(code),
    ]

# 실행 배지.
#   "none"     : 도구 실행 없이 진행 (06)
#   "optional" : boltzgen 설치·검증 셀 포함 (02·03)
#   "design"   : 직접 설계 실행 셀 포함 (04·05, 07~11)
RUN_BADGE = {
    "none": "",
    "optional": "> GPU 진단 셀은 NVIDIA GPU 에서만 의미가 있어요 — Colab 이면 **런타임 → T4 GPU**. 없어도 나머지는 그대로 진행됩니다.",
    "design": "> **① 직접 설계 실행 → ② 내 결과 확인 → ③ 레퍼런스 대조** 순서로 갑니다. "
              "설계 셀은 NVIDIA GPU 전용이에요(CPU 폴백 없음) — Colab 이면 **런타임 → 런타임 유형 변경 → T4 GPU**.",
}


# 설계 셀 실측 소요 시간 — (num_designs, budget) → 배지 문구.
# 부록 A8 의 재현 환경(24GB GPU / CUDA 12.4)에서 가중치 캐시 상태로 측정. 스텝 수는 프로토콜마다 다르다
# (protein-anything 6 · peptide/antibody/nanobody 5 · protein-small_molecule 7).
# T4 는 가속 커널이 꺼지고(capability 7.5) 칩도 느려 이보다 더 걸린다 — T4 실측치는 없다.
DESIGN_RUNTIME = {
    (4, 2): "실측 **307초**(최종 2개)",
    (8, 4): "실측 **585초**(최종 4개)",
}


def design_cells(spec, protocol, num, budget, ref_note, extra_flags="", sec=1,
                 pre_files=()):
    """'직접 설계 실행' 셀 — 학습자가 자기 결과를 my_run/ 에 만든다.
    GPU 런타임이 아니면 스스로 건너뛰고, 이후 분석은 레퍼런스로 이어진다.

    pre_files: boltzgen 레포에 커밋돼 있지 않아 실행 전에 받아와야 하는 타깃 파일
               [(레포 상대경로, 다운로드 URL), ...]
    """
    took = DESIGN_RUNTIME.get((num, budget))
    time_line = (f"- 소요 시간 {took} — **24GB GPU · 가중치 캐시** 기준이에요. "
                 f"Colab T4 는 가속 커널이 꺼져 더 걸리고(T4 실측치 없음), 첫 실행은 가중치 ~6GB 다운로드가 더 붙어요.\n"
                 if took else "")
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

- 학습용 규모 `num_designs={num} --budget={budget}` ({ref_note})
{time_line}- 건너뛰면 아래 분석이 커밋된 레퍼런스 결과로 이어집니다."""),
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
    print("GPU 런타임이 아니라 설계 실행을 건너뜁니다 — 아래 분석은 레퍼런스 결과로 이어집니다.")
    print("  · 직접 돌리려면 Colab [런타임 → 런타임 유형 변경 → T4 GPU] 후 이 셀을 다시 실행하세요.")
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
        print("\\n설계 실행이 도중에 멈췄어요 —", type(e).__name__)
        print("  · 이 셀을 다시 실행하면 같은 --output 산출물을 재사용해 이어서 끝냅니다(실측 763초 → 재개 486초).")
        print("  · GPU 메모리가 부족했다면 NUM_DESIGNS 4, BUDGET 2 로 줄이세요.")'''),
    ]


def title_cell(num, name, ko, md_link, gpu="none"):
    src = {"design": "> 이 노트북의 표·그래프·수치는 **여러분이 직접 돌린 결과**(`my_run/`)에서 계산합니다.\n",
           "optional": "", "none": ""}[gpu]
    badge = RUN_BADGE[gpu]
    return md(f"""# {num} — {ko}

> 본문 [`{md_link}`]({md_link}) 와 **한 절씩 짝지어** 보세요.
{src}{badge}""" if badge else f"""# {num} — {ko}

> 본문 [`{md_link}`]({md_link}) 와 **한 절씩 짝지어** 보세요.
{src}""")


cells_all = {}

# ── 02 입력 데이터 준비 ──────────────────────────────────────────────────────
# ── ch02 교체 블록 ───────────────────────────────────────────────────────────
# gen_notebooks.py 의 "## 02 입력 데이터 준비" 블록(c = [title_cell("02", ...)] ~
# cells_all[("02_input_data_prep", ...)] = c)을 이 파일 내용으로 그대로 갈아끼운다.
#
# [고친 사실 오류]
#  · `binding: 50..70` / `exclude: 45..55` — 7uxq 근거 없는 숫자였음.
#    → 결합부위는 이 구조에 이미 붙어 있는 펩타이드(체인 C) 5Å 접촉 잔기에서 계산,
#      exclude 는 실측으로 찾은 C말단 His-태그 구간(파일번호 140..144)으로 교체.
#      (실측 확인: 접촉 res_index 38,40..42,44..50,52,59..60,62,97,99..101,105..107)
#  · 명세의 `res_index`/`binding` 은 체인 첫 잔기를 1로 세는 순번(=CIF label_seq)이라
#    파일에 찍힌 잔기 번호(7uxq 체인 A 는 18..144)와 다름 → 두 번호를 나란히 출력해 근거를 보임.
#    (boltzgen 0.3.2 소스 parse_range + `boltzgen check` 실측으로 확인)
#  · 설계 체인 id 를 `B` 로 쓰면 파일의 체인 B 와 충돌 → 파일에 없는 ID 를 코드로 골라 씀.
#  · `path` 는 YAML 위치 기준 상대경로(본문 2.8) → work/my_spec.yaml 안에서는 `7uxq.cif`.
#    (기존 `work/7uxq.cif` 였다면 work/work/… 로 풀려 check 가 실패)
#
# [채운 커버리지]
#  · 본문 2.6 서열·위상학 심화(시스테인 패턴 3C8C6C5C3C1C2 · cyclic · constraints.bond ·
#    secondary_structure · residue_constraints) 셀 신설 + Ch.07 연결.
#  · 본문 2.8 을 끝까지 — 내가 쓴 work/my_spec.yaml 을 `boltzgen check` 로 검증(레포 예제 검증도 유지).
#  · 본문 2.8 체크리스트 4행("결합부위 번호가 실제 타깃에 존재하나")을 실습으로 이행(좌표 있는 res_index 대조).
#
# [줄인 군더더기]
#  · 죽은 변수 `kinds` 삭제. entity 5종 print() 9회 → 삼중따옴표 한 덩어리.
#  · "PyMOL 불필요" 3회 → 1회(제목에만). 3D 뷰어 도입부 4줄 → 2줄.
#  · 셀 동작 예고("아래 셀이 ~합니다") 제거. 절 번호는 0)→1)…→9) 로 중복 없이.
# ─────────────────────────────────────────────────────────────────────────────

c = [title_cell("02", "02_input_data_prep", "입력 데이터 준비", "02_input_data_prep.md")]
c += boot("02_input_data_prep", pip="gemmi")
c += [
md("""## 1) 타깃 구조 받기 (본문 2.3)

설계는 "무엇에 붙일지"부터 정해집니다. 면역항암 표적 PD-L1 의 결정구조 `7uxq` 를 RCSB 에서 받아
이 챕터 내내 같은 재료로 씁니다."""),
co("""import urllib.request, pathlib
work = pathlib.Path("work"); work.mkdir(exist_ok=True)
PDB_ID = "7uxq"                                # PD-L1
cif = work / f"{PDB_ID}.cif"
if not cif.exists():
    urllib.request.urlretrieve(f"https://files.rcsb.org/download/{PDB_ID}.cif", cif)
print("타깃 구조", cif, "|", cif.stat().st_size, "bytes")
print("수십 KB 이상이면 정상이고, 몇 백 bytes 면 PDB ID 오타로 오류 페이지를 받은 거예요.")"""),

md("""## 2) 파일 안을 먼저 들여다보기 — 체인과 잔기 번호 (본문 2.4)

받은 파일을 그대로 넣지 않아요. **어떤 체인이 들어 있고 잔기 번호가 어디부터 어디까지인지**를 봐야
`include`·`exclude`·`binding` 에 적을 숫자가 정해집니다.

번호는 두 가지가 나옵니다. 파일에 찍힌 잔기 번호와, 명세가 쓰는 `res_index`(체인의 첫 잔기를 1로 세는 순번)예요.
둘이 다를 수 있으니 나란히 확인합니다."""),
co("""import gemmi
st = gemmi.read_structure(str(cif)); st.setup_entities()
model = st[0]
CHAIN_IDS = [ch.name for ch in model]
print("구조", st.name, "| 체인", ", ".join(CHAIN_IDS))
print()
print("체인  폴리머  종류        파일 잔기번호   명세 res_index   서열(앞·뒤)")
for ch in model:
    poly = ch.get_polymer()
    if not len(poly):
        continue
    kind = str(poly.check_polymer_type()).split(".")[-1]
    seq = gemmi.one_letter_code([r.name for r in poly])
    shown = seq if len(seq) <= 30 else seq[:14] + "…" + seq[-14:]
    print(f"  {ch.name:<4}{len(poly):>5}  {kind:<11}"
          f"{poly[0].seqid.num:>6}..{poly[-1].seqid.num:<8}"
          f"{poly[0].label_seq:>4}..{poly[-1].label_seq:<10}{shown}")"""),

md("""## 3) 이 체인들을 명세 문법으로 — entity 5종 (본문 2.2)

긴 체인 두 벌(A·B)이 PD-L1 본체이고, 짧은 체인 두 벌(C·D)은 그 표면에 붙은 채로 결정화된 펩타이드예요.
이걸 명세로 옮기려면 entity 문법이 필요합니다. BoltzGen 이 다루는 entity 는 5종이고,
**만들 것**(`protein`·`dna`·`rna`·`ligand`)과 **붙일 것**(`file`)으로 나뉘어요."""),
co('''print("""# 만들 것 — 설계 대상
- protein: { id: B, sequence: 80..140 }      # 80~140aa 중 무작위 길이로 설계
- protein: { id: B, sequence: 120 }          # 고정 120aa
- protein: { id: B, sequence: MKLVAA... }    # 서열 고정(재설계/스캐폴드)

# 붙일 것 — 타깃 entity
- dna: { id: D, sequence: ATGCGT }
- rna: { id: R, sequence: AUGCGU }
- ligand: { id: L, ccd: ATP }                                  # PDB 화학성분 사전 3글자 코드
- ligand: { id: L, smiles: "CC(=O)Oc1ccccc1C(=O)O" }           # 아스피린(CCD 에 없을 때)
- file:   { path: target.cif, include: [ { chain: { id: A } } ] }

# res_index 범위 표기 — include / exclude / binding 공통
  45..55        45번부터 55번까지
  ..10          처음부터 10번까지
  185..         185번부터 끝까지
  10,29,33,40..48   개별 + 범위 혼합""")'''),

md("""## 4) 결합부위를 데이터에서 뽑기 (본문 2.5)

본문이 말한 세 단서 중 가장 확실한 건 **이미 붙어 있는 것**이에요.
7uxq 는 PD-L1(체인 A) 표면에 18잔기 펩타이드(체인 C)가 붙은 상태로 풀린 구조라,
C 로부터 5Å 안에 있는 A 의 잔기가 곧 실험으로 검증된 결합부위입니다.

명세에 적을 값은 `res_index` 쪽이므로, 접촉 잔기를 찾은 뒤 **그 번호가 좌표 있는 잔기를 가리키는지**까지
확인합니다(본문 2.8 체크리스트 "결합부위 잔기 번호")."""),
co("""TARGET, PROBE, CUTOFF = "A", "C", 5.0          # A = PD-L1 타깃, C = 이미 붙어 있는 펩타이드
chains = {ch.name: ch.get_polymer() for ch in model}
tgt, prb = chains[TARGET], chains[PROBE]

probe_pos = [a.pos for r in prb for a in r]
contact = [r for r in tgt if any(a.pos.dist(p) <= CUTOFF for a in r for p in probe_pos)]

def to_range(nums):
    \"\"\"연속 구간은 a..b, 단독은 a 로 묶어 BoltzGen 범위 문법 문자열을 만듭니다.\"\"\"
    out, i = [], 0
    while i < len(nums):
        j = i
        while j + 1 < len(nums) and nums[j + 1] == nums[j] + 1:
            j += 1
        out.append(f"{nums[i]}..{nums[j]}" if j > i else str(nums[i]))
        i = j + 1
    return ",".join(out)

BINDING = to_range(sorted(r.label_seq for r in contact))
print(f"체인 {PROBE} 에서 {CUTOFF:g}Å 안에 있는 체인 {TARGET} 잔기 {len(contact)}개")
print("  파일 잔기번호 ", to_range(sorted(r.seqid.num for r in contact)))
print("  명세 res_index", BINDING)

RESOLVED = {r.label_seq for r in tgt}
used = sorted({int(x) for tok in BINDING.split(",") for x in tok.split("..") if x})
bad = [n for n in used if n not in RESOLVED]
print()
print(f"좌표가 있는 res_index 범위 {min(RESOLVED)}..{max(RESOLVED)}")
print("검증 통과 — 명세에 적을 번호가 모두 실제 잔기를 가리켜요." if not bad
      else f"확인 필요 — 좌표 없는 번호 {bad} 는 빼세요.")"""),

md("""## 5) 뺄 것을 빼고 명세로 쓰기 (본문 2.4)

붙일 자리는 정했으니 이제 **뺄 것**입니다. 2)의 서열 끝을 보면 `...HHHHH` — 정제용 His-태그예요.
생물학적 타깃이 아니고 구조도 흔들리니 `exclude` 로 뺍니다. 끝까지 자르는 거라 `N..` 표기가 딱 맞아요.

남은 함정 둘도 여기서 막습니다. 설계 체인 `id` 는 **파일에 없는 문자**로 골라 충돌을 피하고,
`path` 는 **YAML 파일 위치 기준** 상대경로라 `work/my_spec.yaml` 안에서는 `7uxq.cif` 로 씁니다(본문 2.8)."""),
co('''tail = list(tgt)
k = len(tail)
while k > 0 and tail[k - 1].name == "HIS":      # C말단 His-태그 구간을 뒤에서부터 찾습니다
    k -= 1
assert k < len(tail), "C말단 His-태그가 없어요 — 뺄 구간을 직접 정해 exclude 에 적으세요."
TAG_FROM = tail[k].label_seq
print(f"C말단 His-태그 {len(tail) - k}잔기 → 파일 번호 {tail[k].seqid.num}.. / res_index {TAG_FROM}.. 를 제거")

DESIGN_ID = next(x for x in "ZYXWV" if x not in CHAIN_IDS)
print(f"설계 체인 id = {DESIGN_ID} (파일이 이미 쓰는 {','.join(CHAIN_IDS)} 와 겹치지 않음)")

spec = f"""entities:
  - protein: {{ id: {DESIGN_ID}, sequence: 80..140 }}       # 설계할 바인더
  - file:
      path: {PDB_ID}.cif
      include:       [ {{ chain: {{ id: {TARGET} }} }} ]
      exclude:       [ {{ chain: {{ id: {TARGET}, res_index: {TAG_FROM}.. }} }} ]
      binding_types: [ {{ chain: {{ id: {TARGET}, binding: "{BINDING}" }} }} ]
      reset_res_index: [ {{ chain: {{ id: {TARGET} }} }} ]
      structure_groups: "all"
"""
MY_SPEC = work / "my_spec.yaml"
MY_SPEC.write_text(spec, encoding="utf-8")
print()
print(spec)'''),

md("""## 6) 서열 칸으로 위상학까지 적기 (본문 2.6)

여기까지가 "타깃에 자유롭게 붙이기"예요. 그런데 설계 단백질의 `sequence` 칸은 길이만 적는 자리가 아니라
**어디에 Cys 를 박고, 고리로 닫고, 어느 구간을 helix 로 둘지**까지 적는 자리입니다.
고리형 펩타이드는 Ch.07 에서 이 표기 그대로 실제 설계를 돌립니다."""),
co('''print("""- protein:
    id: B
    sequence: 3C8C6C5C3C1C2     # 디자인 3잔기 + Cys + 8잔기 + Cys + ... = 34잔기, Cys 6개
    cyclic: true                # 머리-꼬리 고리화
    secondary_structure:
        helix: 5..15            # 5~15번을 helix 로
        sheet: 20..28           # 20~28번을 sheet 로
    residue_constraints:
      - { position: 1, allowed: A }         # 1번은 Ala 만
      - { position: 3..5, disallowed: CM }  # 3~5번은 Cys/Met 금지
constraints:
  - bond: { atom1: [B, 4, SG], atom2: [B, 26, SG] }    # Cys4-Cys26 이황화
  - bond: { atom1: [B, 13, SG], atom2: [B, 30, SG] }
  - bond: { atom1: [B, 20, SG], atom2: [B, 32, SG] }""")
print()
print("Cys 6개 → 이황화 3쌍(cystine knot). bond 는 [체인, 잔기번호, 원자이름] 형식이고 SG 는 Cys 의 황 원자예요.")'''),

md("""## 7) 핵산 타깃 — 따로 할 일이 없어요 (본문 2.7)

DNA·RNA 타깃도 4)~5)와 완전히 같은 방식입니다. BoltzGen 이 CIF 안의 잔기 코드를 보고
단백질·DNA·RNA 를 자동 구분하니, 핵산 체인을 그냥 `include` 하면 돼요."""),
co('''print("""entities:
  - protein: { id: G, sequence: 40..120 }                # DNA 결합 단백질 설계
  - file:
      path: example/denovo_zinc_finger_against_dna/zf.cif
      include: [ { chain: { id: C1 } }, { chain: { id: B1 } } ]   # DNA 이중가닥 두 체인
      structure_groups: "all"
""")'''),

md("""## 8) 돌리기 전 검증 — `boltzgen check` (본문 2.8)

5)에서 쓴 `work/my_spec.yaml` 이 실제로 통과하는지 확인합니다. 체인 ID·잔기 번호·상대경로 중 하나라도
어긋나면 여기서 바로 오류가 나요. 비교 기준으로 레포 예제(`1g13prot.yaml`)도 같이 검사합니다.
`check` 는 GPU 가 필요 없어 CPU 런타임에서도 돌아갑니다(설치 상세는 Ch.03)."""),
co('''import shutil, subprocess, sys

if not shutil.which("boltzgen"):
    _run(f'"{sys.executable}" -m pip -q install boltzgen')

SRC = ADV_ROOT / ".boltzgen_src"          # 예제 명세는 pip 패키지에 없고 소스 레포에만 있습니다
if not SRC.exists():
    _run(f'git clone --depth 1 https://github.com/HannesStark/boltzgen.git "{SRC}"')

def check(spec):
    """boltzgen check 를 돌리고 결과를 이 셀 출력으로 가져옵니다."""
    r = subprocess.run(["boltzgen", "check", str(spec)], capture_output=True, text=True)
    print(r.stdout.strip() if r.returncode == 0 else r.stderr.strip()[-700:])

if shutil.which("boltzgen"):
    print("=== 내가 쓴 명세 ===")
    check(MY_SPEC)
    print("=== 레포 예제 ===")
    check(SRC / "example/vanilla_protein/1g13prot.yaml")
    print()
    print("두 명세 모두 sequence 를 80..140 으로 뒀으니, Total designed residues 가 그 범위 안이면 정상이에요.")
    print("매 실행마다 값이 달라지는 것도 정상이고요. 오류가 나면 체인 ID·res_index·path 를 다시 보세요.")
else:
    print("boltzgen 설치가 아직 안 됐어요. 이 셀을 한 번 더 실행하면 설치 완료 후 검증까지 이어집니다.")'''),

md("""## 9) 명세를 3D 로 확인 — PyMOL 불필요 (본문 2.8)

`check` 가 남긴 `my_spec.cif` 를 그대로 띄웁니다. 마우스로 회전·확대하면서
**타깃이 맞는지, 잘라낸 자리가 의도대로인지**를 눈으로 확인하세요(N말단 파랑 → C말단 빨강)."""),
co('''import importlib.util, pathlib
if importlib.util.find_spec("py3Dmol") is None:
    _run(f'"{sys.executable}" -m pip -q install py3Dmol')
import py3Dmol, gemmi

viz = next((p for p in (pathlib.Path("my_spec.cif"), pathlib.Path("1g13prot.cif")) if p.exists()), None)
assert viz is not None, "시각화 CIF 가 없어요 — 위 8) 셀을 먼저 실행하세요."
print("띄울 구조", viz)

pdb = gemmi.read_structure(str(viz)).make_pdb_string()   # 3Dmol.js 는 PDB 를 가장 안정적으로 읽어요
view = py3Dmol.view(width=760, height=540)
view.addModel(pdb, "pdb")
view.setStyle({"cartoon": {"color": "spectrum"}})
view.setBackgroundColor("white")
view.zoomTo()
view.show()'''),

md("""### 정리

타깃 구조를 받아 체인·잔기 번호를 실측하고, 결합부위를 데이터에서 뽑고, 태그를 잘라내고,
`boltzgen check` 로 통과시킨 `work/my_spec.yaml` 하나가 이 챕터의 결과물이에요.
이제 이 명세를 실제로 돌릴 환경이 필요합니다 — Ch.03 에서 설치와 GPU·CUDA 정합을 맞춥니다."""),
]
cells_all[("02_input_data_prep", "02_data_prep.ipynb", "02 Data Preparation")] = c


# ── 03 설치·검증 ────────────────────────────────────────────────────────────
# ── ch03 교체 블록 ───────────────────────────────────────────────────────────
# gen_notebooks.py 의 "## 03 설치·검증" 블록(c = [title_cell("03", ...)] ~
# cells_all[("03_install_access", ...)] = c)을 이 파일 내용으로 그대로 갈아끼운다.
#
# [고친 사실 오류]
#  · "기본값이 10이라 메모리가 큽니다" → 본문 3.1.5 는 `num_designs` 100 미만이면 1,
#    100 이상이면 10 으로 자동 결정. 100 분기표를 코드로 출력하도록 교체.
#  · `if vram < 14` (근거 없는 14GB 임계값) 삭제 → 판정 기준을 num_designs 100 분기로.
#  · `--config folding trainer.precision=32` 는 Ch.03 본문에 없음 → 부록 A6 인용으로 정정.
#  · 셀 제목 "+ (선택) 스모크 테스트" — 그 코드가 없으므로 제목에서 제거.
#  · 클론 위치를 `boltzgen-src`(챕터 폴더) → Ch.02 와 같은 `ADV_ROOT/".boltzgen_src"` 로 통일
#    (같은 레포를 두 번 클론하지 않음).
#
# [채운 커버리지]
#  · 본문 3.3 체크리스트 5행 — `python -m pip show nvidia-cublas-cu12` 로 버전 출력 + `>= 12.5` 판정 셀 신설.
#  · 본문 3.4 — `boltzgen download`, `--cache`/`--models_token`/`--force_download`,
#    캐시 경로 `~/.cache/huggingface/` 점검 셀 신설.
#  · 절 순서를 본문 3.3 체크리스트 5행 순서(nvidia-smi → torch.version.cuda → is_available →
#    커널 → cuBLAS)에 맞추고, 이어서 3.1.5 → 3.4 → 3.6 으로 진행.
#
# [줄인 군더더기]
#  · "런타임 → T4 GPU" 안내 2회 → 0회(타이틀 배지가 이미 1회 안내).
#  · 이 노트북에 없는 셀·폴더 안내 삭제(설계 셀·레퍼런스 결과 폴백 문구 — 03 에는 data/ 가 없음).
#  · 절 번호 `1) 2) 3) 3.5) 4) 5) 6)` → `1)~9)` 로 중복·변칙 없이. GPU 장치 정보 출력은 3) 한 곳으로 모음.
# ─────────────────────────────────────────────────────────────────────────────

c = [title_cell("03", "03_install_access", "환경 설치·검증", "03_install_access.md", gpu="optional")]
c += boot("03_install_access", pip="")     # 여기선 boltzgen 자체를 설치
c += [
md("""## 1) BoltzGen 설치 (본문 3.2)

설치 자체는 한 줄이에요. 진짜 관문은 그다음 CUDA 정합이고, 2)부터 그걸 한 층씩 확인합니다.
가중치(~6GB)는 아직 받지 않고, 첫 `boltzgen run` 때 자동으로 내려받아요."""),
co('''import sys
if IN_COLAB:
    _run(f'"{sys.executable}" -m pip -q install boltzgen')
    # cuequivariance 커널은 cuBLAS >= 12.5 를 요구(본문 3.3) — Colab 이미지에 따라 정합을 보강합니다.
    _run(f'"{sys.executable}" -m pip -q install "nvidia-cublas-cu12>=12.5" || true')
else:
    print("로컬은 conda 로 만든 boltzgen_env 를 활성화한 뒤 이 노트북을 여세요 (본문 3.2).")'''),

md("""## 2) 1층 — 드라이버가 지원하는 CUDA 상한 (본문 3.3)

맞춰야 할 층은 넷이에요. **드라이버 ↔ PyTorch ↔ cuequivariance ↔ cuBLAS**.
맨 아래부터 봅니다. `nvidia-smi` 우상단 `CUDA Version: 12.x` 가 드라이버가 지원하는 **상한**이고,
위층의 CUDA 는 이 값을 넘으면 안 돼요."""),
co('''import shutil, subprocess
if shutil.which("nvidia-smi"):
    out = subprocess.run(["nvidia-smi"], capture_output=True, text=True).stdout
    for line in out.splitlines()[:12]:
        print(line)
else:
    print("nvidia-smi 가 없어요 — 지금은 CPU 런타임입니다.")
    print("  · 아래 GPU 항목은 비어서 나오고, 설치·CLI·명세 검증은 그대로 진행됩니다.")'''),

md("""## 3) 2층 — PyTorch 의 CUDA 빌드와 GPU 인식 (본문 3.3)

`torch.version.cuda` 가 2)의 상한 이하 12.x 이고 `cuda available` 이 True 면 통과예요.
major 가 어긋나면(예: 드라이버 12.4 에 torch cu130) `driver too old` 로 GPU 를 아예 못 봅니다.
여기서 읽은 GPU 이름·capability·VRAM 은 뒤 셀에서도 그대로 씁니다."""),
co('''CAP, VRAM = None, None
try:
    import torch
    print("torch", torch.__version__, "| built cuda", torch.version.cuda)
    print("cuda available", torch.cuda.is_available())
    if torch.cuda.is_available():
        CAP = torch.cuda.get_device_capability()
        VRAM = torch.cuda.get_device_properties(0).total_memory / 1024**3
        a = torch.randn(256, 256, device="cuda"); b = torch.randn(256, 256, device="cuda")
        print(f"device {torch.cuda.get_device_name(0)} | capability {CAP} | VRAM {VRAM:.1f} GB")
        print("matmul 검산", bool(torch.isfinite((a @ b).sum())))
except Exception as e:
    print("torch import/실행 실패 —", repr(e)[:160])
    print("  → Colab 이면 런타임 재시작 후 재실행, 로컬이면 드라이버 상한에 맞는 빌드로 재설치")
    print("     python -m pip install 'torch==2.6.0' --index-url https://download.pytorch.org/whl/cu124"
          " --extra-index-url https://pypi.org/simple")'''),

md("""## 4) 3층 — cuequivariance 가속 커널 (본문 3.3)

torch 가 GPU 를 봐도 여기서 한 번 더 막힐 수 있어요. import 가 되면 통과입니다.

> capability 8 미만 GPU(T4 등)는 이 커널을 **애초에 쓰지 않아** 실패해도 설계는 그대로 돌아가요."""),
co('''try:
    from cuequivariance_ops_torch import triangle_multiplicative_update
    print("cuequivariance kernel OK")
except Exception as e:
    print("FAILED —", repr(e)[:160])
    print("  → undefined symbol: cublasGemmGroupedBatchedEx 라면 cuBLAS 문제예요. 5) 셀에서 버전을 봅니다.")'''),

md("""## 5) 4층 — cuBLAS 버전 (본문 3.3)

4)의 커널이 요구하는 함수 `cublasGemmGroupedBatchedEx` 는 **cuBLAS 12.5 이상**에서 추가됐어요.
torch 가 12.4 를 번들로 들고 오면 커널 로딩만 실패합니다. cuBLAS 는 12.x 안에서 하위 호환이라
이것만 올려도 torch 는 그대로 돌아가요."""),
co('''import subprocess, sys
out = subprocess.run([sys.executable, "-m", "pip", "show", "nvidia-cublas-cu12"],
                     capture_output=True, text=True).stdout
ver = next((l.split(":", 1)[1].strip() for l in out.splitlines() if l.startswith("Version:")), None)
print("nvidia-cublas-cu12", ver or "(설치 안 됨)")

if ver and tuple(int(x) for x in ver.split(".")[:2]) >= (12, 5):
    print("판정 통과 — 12.5 이상")
elif ver:
    print("판정 미달 — 12.5 미만이라 4)의 커널이 실패해요.")
    print("  → python -m pip install 'nvidia-cublas-cu12==12.9.2.10' 후 런타임 재시작")
else:
    print("판정 보류 — GPU 로 설계할 계획이면 미리 넣어두세요.")
    print("  → python -m pip install 'nvidia-cublas-cu12>=12.5'")'''),

md("""## 6) 실행 로그를 미리 읽어두기 — 커널과 배치 (본문 3.1.5)

네 층이 맞았으면 이제 `boltzgen run` 로그예요. 딱 두 줄만 알면 실행을 통제할 수 있어요.

```
Using kernels: False [device capability: (7, 5)]
Using diffusion batch size: 1
```

첫 줄은 4)에서 본 가속 커널이 켜졌는지, 둘째 줄은 유일하게 신경 쓸 메모리 레버예요.
`--diffusion_batch_size` 를 지정하지 않으면 `num_designs` 가 **100 미만이면 1, 100 이상이면 10** 으로
자동 결정됩니다. 즉 99 → 100 으로 늘리는 순간이 분기점이에요.

> 가장 무거운 folding 단계는 내부적으로 `batch_size: 1` 고정이라, 디자인을 몇 개 뽑든
> GPU 에 한 번에 올라가는 복합체는 하나예요."""),
co('''for n in (4, 30, 99, 100, 1000):
    print(f"  --num_designs {n:>5}  →  diffusion 배치 자동값 {1 if n < 100 else 10}")
print()
if CAP is None:
    print("GPU 가 없어 지금은 표만 읽고 갑니다 — 실습 예제는 전부 num_designs 4~30 이라 배치는 1이에요.")
else:
    print("가속 커널", "ON" if CAP[0] >= 8 else "OFF (capability 8 미만 — 자동 비활성, 정상 동작하고 조금 느림)")
    print(f"이 GPU 의 VRAM {VRAM:.1f} GB — 실습 규모(num_designs 4~30)는 배치가 1이라 옵션이 필요 없어요.")
    print("100개 이상 뽑을 때 메모리가 빠듯하면 --diffusion_batch_size 1 을 명시하세요.")
    print("CUDA out of memory 가 뜨면 배치를 줄이고, 그래도 안 되면 num_designs 를 쪼개 돌린 뒤 boltzgen merge 로 합칩니다.")
    if CAP[0] < 8:
        print("bf16 네이티브 미지원 카드(T4/V100)에서 정밀도 오류가 나면 --config folding trainer.precision=32 (부록 A6)")'''),

md("""## 7) 모델 가중치와 캐시 (본문 3.4)

가중치는 첫 실행 때 HuggingFace Hub 에서 자동으로 받아요. 약 6GB 이고 한 번 받으면
`~/.cache/huggingface/` 에 남아 재사용됩니다. 지금 무엇이 받아져 있는지부터 봅니다."""),
co('''import os, pathlib
cache = pathlib.Path(os.environ.get("HF_HOME", pathlib.Path.home() / ".cache" / "huggingface"))
print("캐시 경로", cache, "| 존재", cache.exists())
if cache.exists():
    hits = [p for p in cache.rglob("*")                       # snapshots/ 만 봐야 blob 중복이 안 잡혀요
            if p.is_file() and "snapshots" in p.parts and "boltz" in str(p).lower()]
    used = sum(p.stat().st_size for p in hits) / 1024**3
    print(f"BoltzGen 관련 캐시 파일 {len(hits)}개 | {used:.2f} GB")
    for p in sorted(hits, key=lambda x: -x.stat().st_size)[:6]:
        print(f"    {p.name:34s}{p.stat().st_size / 1024**2:8.1f} MB")
print()
print("미리 받아두려면 boltzgen download")
print("  --cache <DIR>       모델 캐시 위치 지정 (기본 ~/.cache)")
print("  --models_token <T>  HuggingFace 토큰 (rate limit 완화·빠른 다운로드)")
print("  --force_download    재다운로드")
print()
print("전부 받으면 백본 2종·역접힘·구조검증 체크포인트에 보조 데이터까지 약 6GB 예요.")
print("지금 비어 있어도 정상이고, 다운로드가 느리거나 실패하면 --models_token 이나 --force_download 를 쓰세요.")'''),

md("""## 8) CLI 확인 (본문 3.6)

여기부터는 설치 자체의 마무리 점검이에요. 버전과 서브커맨드가 뜨면 실행 파일이 제대로 깔린 겁니다."""),
co('''import shutil, subprocess
if shutil.which("boltzgen"):
    print(subprocess.run(["boltzgen", "--version"], capture_output=True, text=True).stdout.strip())
    helptext = subprocess.run(["boltzgen", "--help"], capture_output=True, text=True).stdout
    for line in helptext.splitlines()[:14]:
        print(line)
    print()
    print("run / configure / execute / download / check / merge 가 보이면 정상이에요.")
else:
    print("boltzgen 이 아직 없어요 — 1) 셀을 먼저 실행하세요.")'''),

md("""## 9) 설계 명세 검증 (본문 3.6)

마지막은 가벼운 엔드투엔드 확인이에요. `boltzgen check` 는 명세를 읽고 타깃 구조까지 파싱하므로,
여기까지 통과하면 설치·의존성·데이터 경로가 모두 살아 있다는 뜻입니다. GPU 는 필요 없어요."""),
co('''import shutil, subprocess, pathlib
SRC = ADV_ROOT / ".boltzgen_src"          # Ch.02 에서 이미 받았다면 그대로 재사용합니다
if shutil.which("boltzgen") and not SRC.exists():
    _run(f'git clone --depth 1 https://github.com/HannesStark/boltzgen.git "{SRC}"')

spec = SRC / "example/vanilla_protein/1g13prot.yaml"
if shutil.which("boltzgen") and spec.exists():
    r = subprocess.run(["boltzgen", "check", str(spec)], capture_output=True, text=True)
    print(r.stdout.strip() if r.returncode == 0 else r.stderr.strip()[-700:])
    print()
    print("이 예제는 sequence 가 80..140 이라 Total designed residues 가 그 범위 안이면 통과예요.")
    print("매 실행마다 값이 달라지는 것도 정상입니다.")
else:
    print("boltzgen 또는 예제 명세가 아직 없어요 — 1) 셀을 실행한 뒤 다시 오세요.")'''),

md("""### 정리

드라이버 → torch → 커널 → cuBLAS 네 층을 순서대로 통과시키고, 가중치 캐시와 CLI, 명세 검증까지 확인했어요.
설치에서 막히는 대부분은 이 순서로 짚으면 어느 층이 어긋났는지 바로 드러납니다.
이제 실제로 6스텝을 끝까지 돌릴 차례예요 — Ch.04 에서 `num_designs 4`, `budget 2` 규모로 파이프라인을 완주합니다."""),
]
cells_all[("03_install_access", "03_setup_check.ipynb", "03 Setup & Check")] = c


# ── 04 기본 사용법 ──────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────
# gen_notebooks.py 의 04 블록 교체본
#
# [고친 사실 오류]
#   · "--budget 보통 50~200" → 본문에 없는 수치. 본문 4.3 의 실제 기준(다양성 선별 수)과
#     본문 4.7 실행 예시(peptide 30 · small_molecule 40 · protein 50)로 교체.
#   · --num_designs 도 본문 4.3 표(4~100 / 1,000~5,000 / 10,000~60,000)를 그대로 반영.
#
# [채운 커버리지]
#   · 본문 4.8 — 실행 중 무엇을 보며 기다리나. `Pipeline step k of N` /
#     `completed successfully in Xs` / `Traceback` 로그 패턴 + nvidia-smi 실시간 판정.
#     (5분짜리 설계 셀 '앞'에 배치해서, 기다리는 동안 볼 것을 먼저 정하도록 함)
#   · 본문 4.4 — --steps 부분 실행 7종(affinity 포함) + "무거운 건 한 번, filtering 은 여러 번".
#   · 본문 4.5 — `--config <스텝> 키=값` 문법과 실행제어 옵션 7종을
#     "언제 쓰나" 열을 붙인 실습형으로. VRAM 부족·bf16 미지원 조합 명령도 제시.
#   · 본문 4.2 — steps.yaml 을 읽어 6스텝 ↔ 산출물 폴더를 실제로 매핑.
#   · 본문 4.6 — 출력 트리를 존재 여부 체크 + rglob 실측 나열로 확장
#     (config/ · intermediate_designs/ · refold_cif/ · refold_design_cif/ 포함).
#
# [줄인 군더더기]
#   · 죽은 주석 `# 최종 CIF: 라이브는 ... → 한 글롭으로 처리`(마크다운과 중복) 삭제.
#   · "어느 쪽이든 같은 파일 구조" 중복 안내를 한 번으로 축약.
#   · 문장 끝 콜론 제거(마크다운·print 출력문 모두).
#
# [구조]
#   절 번호 1) 2) → design_cells(sec=3) → 4) … 8) 로 중복 없이 이어짐.
#   모든 제목에 실재하는 (본문 N.M) 앵커. DataFrame 선택은 전부 cols_in().
# ─────────────────────────────────────────────────────────────────────────────

c = [title_cell("04", "04_basic_usage", "파이프라인 실행·출력 구조", "04_basic_usage.md", gpu="design")]
c += boot("04_basic_usage", pip="pandas")
c += [
md("""## 1) `boltzgen run` 명령 구조 — 두 숫자가 전부를 좌우해요 (본문 4.1·4.3)

```
boltzgen run <명세.yaml> --output <폴더> --protocol <프로토콜> --num_designs <중간 수> --budget <최종 선별 수>
```

`--protocol` 이 내부 설정을 통째로 정합니다. `protein-anything` 이면 **6스텝** —
design → inverse_folding → folding → design_folding → analysis → filtering.

나머지 둘, `--num_designs` 와 `--budget` 이 품질과 실행 시간을 가장 크게 좌우해요. 기준부터 잡고 갑니다."""),
co('''run_cmd = ("boltzgen run example/vanilla_protein/1g13prot.yaml "
           "--output workbench/vanilla --protocol protein-anything "
           "--num_designs 1000 --budget 50")
print(run_cmd)

print("\\n--num_designs — 표본을 많이 뽑을수록 좋은 꼬리를 만납니다 (본문 4.3)")
for case, rec in [("빠른 테스트 · 환경 검증", "4 ~ 100"),
                  ("일반 설계",              "1,000 ~ 5,000"),
                  ("어려운 타깃 · 복잡한 제약", "10,000 ~ 60,000")]:
    print(f"   {case:22s} → {rec}")
print("   시간·계산이 비례해 늘어나요. 작게 테스트한 뒤 크게 프로덕션으로 갑니다.")

print("\\n--budget — 점수 상위 N개가 아니라, 서로 다른 전략까지 골라 담는 최종 후보 수 (본문 4.3)")
for proto, b in [("peptide-anything", 30), ("protein-small_molecule", 40), ("protein-anything", 50)]:
    print(f"   {proto:24s} --budget {b}")
print("   본문 4.7 실행 예시의 값이에요. 1~3등이 거의 같은 서열이면 하나가 실패할 때 셋 다 실패하니,")
print("   다양성을 섞는 게 실험 성공 확률을 높이는 보험입니다.")

print("\\n아래 실습은 이 표의 맨 윗줄, num_designs 4 · budget 2 스모크 규모로 갑니다.")'''),

md("""## 2) 실행 중 무엇을 보며 기다리나 (본문 4.8)

다음 셀은 **5분 동안 로그만 쏟아냅니다.** 무엇을 보며 기다릴지 먼저 정해두면
"멈춘 건지 도는 건지"로 헷갈리지 않아요."""),
co('''import shutil, subprocess

print("로그에서 이 세 줄만 쫓으면 됩니다 (본문 4.8)")
print("   Pipeline step k of N                    ← k 번째 스텝 시작")
print("   Step ... completed successfully in Xs   ← 그 스텝 정상 종료")
print("   Traceback                               ← 여기서 멈췄다면 위로 스크롤해 원인 확인")
print("   k 가 1 → 2 → 3 으로 올라가면 정상. 같은 k 에서 오래 머무르면 그 스텝이 무거운 거예요.")

print("\\n터미널에서 돌릴 때 (본문 4.8)")
print("   watch -n 1 nvidia-smi                       # 다른 터미널에서 GPU 사용량")
print("   boltzgen run ... > run.log 2>&1 &")
print("   tail -f run.log                             # 로그 추적")

print("\\n지금 이 런타임의 GPU 상태")
if shutil.which("nvidia-smi"):
    q = "name,memory.used,memory.total,utilization.gpu"
    out = subprocess.run(["nvidia-smi", f"--query-gpu={q}", "--format=csv,noheader"],
                         capture_output=True, text=True).stdout.strip()
    print("  ", out.replace("\\n", "\\n   "))
    print("   설계가 돌면 memory.used 가 수 GB 로 올라가고 utilization 이 높게 유지돼요.")
    print("   0 % 에서 오래 머물면 가중치(~6GB) 를 내려받는 중일 수 있습니다.")
else:
    print("   nvidia-smi 없음 → CPU 런타임이라 아래 설계 셀은 스스로 건너뜁니다.")
    print("   직접 돌리려면 [런타임 → 런타임 유형 변경 → T4 GPU] 로 바꾸세요.")'''),
] + design_cells("example/vanilla_protein/1g13prot.yaml", "protein-anything", 4, 2,
                 "가장 작은 스모크 규모 — 6스텝이 전부 도는지 확인하는 게 목적", sec=3) + [

md("""## 4) 방금 돌아간 스텝을 `steps.yaml` 로 되짚기 (본문 4.2)

로그는 지나갔으니 이제 산출물 쪽에서 확인해요. **어떤 스텝이 실제로 실행됐는지는 출력 루트의 `steps.yaml`** 에
그대로 적혀 있고, 스텝마다 결과를 놓는 폴더가 정해져 있습니다.

설계를 건너뛰었다면 Ch.05 의 레퍼런스 결과(`05_result_interpretation/data/vanilla`)가 해부 대상이 됩니다 —
`--output` 폴더 구조는 어느 쪽이든 같아요."""),
co('''import re
REF = "../05_result_interpretation/data/vanilla"

steps    = find_one("steps.yaml", REF)
OUT_ROOT = steps.parent                       # steps.yaml 이 있는 곳 = --output 루트
names    = re.findall(r"-\\s*name:\\s*(\\S+)", steps.read_text())

WHAT = {
    "design":          ("타깃에 맞는 백본 생성",  "intermediate_designs/"),
    "inverse_folding": ("백본에 서열 채우기",    "intermediate_designs_inverse_folded/"),
    "folding":         ("바인더+타깃 재접힘",    "intermediate_designs_inverse_folded/refold_cif/"),
    "design_folding":  ("바인더 단독 재접힘",    "intermediate_designs_inverse_folded/refold_design_cif/"),
    "affinity":        ("소분자 친화도 예측",    "intermediate_designs_inverse_folded/"),
    "analysis":        ("메트릭 계산",          "intermediate_designs_inverse_folded/*_metrics_analyze.csv"),
    "filtering":       ("하드필터 + 다양성 선별", "final_ranked_designs/"),
}

print("출력 루트   :", OUT_ROOT)
print("실행된 스텝 :", len(names), "개\\n")
for i, nm in enumerate(names, 1):
    what, out = WHAT.get(nm, ("-", "-"))
    print(f"  [{i}] {nm:16s} {what:14s} → {out}")

print("\\nprotein-anything 은 6스텝이에요. 펩타이드·나노바디·항체는 design_folding 이 빠져 5스텝,")
print("소분자는 affinity 가 붙어 7스텝으로 늘어납니다 (본문 4.2·4.7).")'''),

md("""## 5) 출력 트리 실제로 열어보기 (본문 4.6)

스텝마다 폴더가 정해져 있다고 했으니, 그 폴더가 진짜 생겼는지 확인할 차례예요.
본문 4.6 의 트리를 그대로 체크리스트로 만들어 **있음/없음**을 표시하고, 이어서 안에 뭐가 들었는지 셉니다."""),
co('''from collections import Counter

EXPECT = [
    ("config/",                                              "스텝별 설정 yaml (configure 단계 산출)"),
    ("steps.yaml",                                           "실행된 스텝 매니페스트"),
    ("intermediate_designs/",                                "[design] 백본 cif + 메타데이터 npz"),
    ("intermediate_designs_inverse_folded/",                 "[inverse_folding] 서열이 채워진 cif"),
    ("intermediate_designs_inverse_folded/refold_cif/",      "[folding] 재접힘 복합체 — 분석의 진짜 입력"),
    ("intermediate_designs_inverse_folded/refold_design_cif/", "[design_folding] 바인더 단독 재접힘"),
    ("final_ranked_designs/",                                "[filtering] 최종셋 · 메트릭 CSV · results_overview.pdf"),
]
print("본문 4.6 트리 대조\\n")
for rel, note in EXPECT:
    p = OUT_ROOT / rel.rstrip("/")
    if p.is_dir():
        print(f"  [O] {rel:56s} {sum(1 for _ in p.glob('*')):5d}개  {note}")
    elif p.is_file():
        print(f"  [O] {rel:56s} {p.stat().st_size:5d}B  {note}")
    else:
        print(f"  [ ] {rel:56s}    -    {note}")

print("\\n실제로 들어 있는 것 (하위 폴더별 파일 수·확장자)\\n")
seen = {}
for f in OUT_ROOT.rglob("*"):
    if f.is_file():
        key = f.parent.relative_to(OUT_ROOT).as_posix() or "."
        seen.setdefault(key, []).append(f.suffix or "(확장자없음)")
for key in sorted(seen):
    ext = ", ".join(f"{e} {n}" for e, n in Counter(seen[key]).most_common(4))
    print(f"  {key + '/':56s} {len(seen[key]):5d}개  {ext}")

print("\\n빈 칸은 저장소에 커밋하지 않은 중간 산출물이에요(용량 문제) — 레퍼런스에는 최종 산출물만 평평하게 담겨 있어요.")
print("직접 돌린 my_run/ 에는 위 일곱 줄이 모두 생깁니다.")'''),

md("""## 6) 최종 산출물 — 순위 붙은 CIF 와 메트릭 CSV (본문 4.6)

트리에서 `final_ranked_designs/` 를 확인했으니, 그 안의 최종 결과물을 직접 엽니다.
폴더·파일 이름에 `budget` 이 박히므로(`final_<budget>_designs/`, `final_designs_metrics_<budget>.csv`)
글롭으로 찾아요."""),
co('''import pandas as pd

csv  = find_one("final_designs_metrics_*.csv", REF)
base = csv.parent
cifs = sorted(base.glob("final*designs/*.cif"))

print("최종 디자인 CIF — 순위 붙은 단일 파일 (서열·구조 내장)")
for p in cifs[:5]:
    print("   ", p.parent.name + "/" + p.name)
print("    ... 총", len(cifs), "개")

print("\\n메트릭 CSV")
for f in sorted(base.glob("*metrics*.csv")):
    print(f"    {f.name:38s} ({f.stat().st_size} bytes)")

df = pd.read_csv(csv)
print("\\n최종셋 디자인", len(df), "개 | 컬럼", df.shape[1], "개 — 한 디자인이 한 행이에요")
df[cols_in(df, "id", "final_rank", "design_ptm", "design_to_target_iptm",
           "filter_rmsd")].sort_values("final_rank")'''),

md("""판정 — `final_rank` 가 1부터 `budget` 까지 빠짐없이 있고 pTM·ipTM·RMSD 가 비어 있지 않으면
6스텝이 정상 완주한 거예요. 한 스텝이 죽어 CSV 가 안 나왔다면 **같은 `--output` 으로 같은 명령을 다시** 실행하세요 —
이미 만들어진 산출물을 재사용해 이어서 끝냅니다(본문 4.7).

기억해 둘 것 두 가지(본문 4.6).
- 인터페이스 분석·시각화는 **`refold_cif/` 또는 최종 CIF 기준**. inverse_folded 직후 파일은 측쇄가 원점에 뭉쳐 있어요.
- `all_designs_metrics.csv` 는 선별 **전** 전체, `final_designs_metrics_<budget>.csv` 는 선별 **후** 최종셋이에요."""),

md("""## 7) 다시 돌릴 때 — `--steps` 부분 실행 (본문 4.4)

방금 표를 보고 "선별 기준을 바꿔 다시 뽑고 싶다"는 생각이 들었다면, 전체를 처음부터 돌릴 필요가 없어요."""),
co('''spec_path = globals().get("SPEC", "spec.yaml")

print("사용 가능한 스텝 7종 (본문 4.4)")
print("   design · inverse_folding · design_folding · folding · affinity · analysis · filtering")
print("   affinity 는 소분자 프로토콜에서만 붙습니다 (본문 4.7 · Ch.10).")

print("\\n# 앞 절반만 — 백본과 서열까지")
print(f"boltzgen run {spec_path} --output out --steps design inverse_folding")
print("\\n# 분석이 끝난 결과에서 선별만 다시 — 몇 초면 끝납니다")
print(f'boltzgen run {spec_path} --output "{OUT_ROOT}" --steps filtering --budget 3')

print("\\n핵심 패턴 — 무거운 design~analysis 는 한 번만, filtering 은 기준을 바꿔가며 여러 번 (본문 4.4).")
print("바꿔볼 기준은 --budget, --metrics_override, --additional_filters 예요. 실험은 Ch.06 에서 이어갑니다.")'''),

md("""## 8) 스텝 안까지 조절 — `--config` 와 실행 제어 옵션 (본문 4.5)

규모를 키우면 이번엔 자원이 문제가 돼요. 스텝 내부 설정은 `--config <스텝명> 키=값` 으로 덮어씁니다."""),
co('''print("--config <스텝명> 키=값 — 그 스텝의 내부 설정만 덮어씁니다 (본문 4.5)")
print("boltzgen run spec.yaml --output out --config folding num_workers=4 trainer.devices=2")

print("\\n자주 쓰는 실행 제어 옵션 (본문 4.5)")
opts = [
    ("--devices N",                    "사용할 GPU 수",            "여러 장으로 나눠 돌릴 때"),
    ("--num_workers N",                "데이터로더 워커 수",        "CPU 는 노는데 GPU 가 굶을 때"),
    ("--use_kernels auto|true|false",  "CUDA 가속 커널 (기본 auto)", "커널 로딩 오류를 우회할 때 (Ch.03)"),
    ("--reuse",                        "기존 결과 재사용",          "같은 폴더에 디자인을 더 얹을 때"),
    ("--diffusion_batch_size N",       "디자인 배치 크기",          "VRAM 이 모자라면 1 로"),
    ("--inverse_fold_num_sequences N", "백본당 서열 수",           "백본은 두고 서열만 더 볼 때"),
    ("--inverse_fold_avoid 'KEC'",     "특정 잔기 금지",           "Cys 등을 피한 설계가 필요할 때"),
]
for opt, mean, when in opts:
    print(f"   {opt:32s} {mean:20s} | {when}")

print("\\n실습 규모에서 바로 쓰는 조합")
print("   # VRAM 이 좁은 카드(T4 등)에서 100개 이상 뽑을 때")
print("   boltzgen run spec.yaml --output out --num_designs 100 --budget 10 --diffusion_batch_size 1")
print("   # bf16 미지원 카드에서 정밀도 오류가 날 때 (Ch.03)")
print("   boltzgen run spec.yaml --output out --config folding trainer.precision=32")'''),

md("""### 이 챕터에서 확인한 것

`--num_designs`·`--budget` 의 기준을 잡고, 스모크 규모로 6스텝을 완주시켜 `steps.yaml` 부터
`final_ranked_designs/` 까지 출력 트리를 직접 열어봤어요. 다시 돌릴 땐 `--steps` 로 필요한 스텝만,
자원이 모자라면 `--config` 로 스텝 안까지 조절하면 됩니다.

이제 손에 남은 건 `final_designs_metrics_<budget>.csv` 한 장이에요. 그 안의 200여 개 컬럼이 무엇을 재고
**순위가 어떻게 정해지는지**는 Ch.05 에서 데이터로 확인합니다."""),
]
cells_all[("04_basic_usage", "04_run_pipeline.ipynb", "04 Run Pipeline")] = c


# ── 05 결과 해석·시각화 ─────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────
# gen_notebooks.py 의 05 블록 교체본
#
# [고친 사실 오류 · 과대표기]
#   · 절 제목 "핵심 메트릭 7군 (본문 5.1~5.7)" → 실제 표가 덮는 범위인 (본문 5.2~5.4) 로 축소.
#     개발성·친화도·다양성/신규성은 프로토콜·옵션에 따라만 생성된다는 한 줄로 Ch.08·10 에 연결.
#   · `complex_plddt` 는 이 결과 CSV 에 실재하지 않음 → 있다고 쓰지 않고 cols_in 으로 방어
#     (없으면 헬퍼가 "건너뜁니다" 를 스스로 출력).
#   · 컬럼 수를 "240여 종" 이라 단정하지 않고 df.shape[1] 실측을 출력.
#
# [채운 커버리지]
#   · 본문 5.8 핵심 — rank_* 6개 + max_rank + secondary_rank 를 표로 보여
#     "왜 pTM 1등이 최종 1등이 아닌가" 를 데이터로 증명(레퍼런스 CSV 219~226열).
#     max_rank = 여섯 순위의 최댓값, secondary_rank = max_rank 의 dense 순위임을
#     노트북이 직접 대조해 일치 개수를 출력(레퍼런스에서 10/10, 전체 풀 100/100).
#   · 선별 전 전체 풀(all_designs_metrics.csv)에서 ipTM 최고 디자인이 최종셋 밖으로 밀린 사실을 확인.
#   · analysis 산출 CSV vs filtering 산출 CSV 컬럼 차분 → filtering 이 rank_*/pass_* 를 덧붙인다는 것.
#   · `plip_saltbridge_refolded` 를 메트릭 표와 상관행렬에 추가(본문 5.4 의 3대 인터페이스 지표).
#   · `designfolding-filter_rmsd`(본문 5.3) 추가 + "복합체에선 멀쩡한데 단독으로 접으면 무너지는" 판정.
#   · 본문 5.9 Filter(budget, use_affinity, refolding_rmsd_threshold, alpha, …) 커버
#     + 기준을 2.5 로 조였을 때 후보가 몇 개 남는지 실제로 계산.
#
# [줄인 군더더기 · 구조]
#   · 미사용 import compare_bars 삭제, import pandas as pd 중복 제거(로드 셀 1회).
#   · design_cells(..., sec=1) 을 명시해 "## 1)" 중복 해소 — 이후 챕터 절은 2) 부터 이어짐.
#   · 마크다운 없이 떠 있던 로드 코드 셀에 제목·맥락 부여.
#   · 문장 끝 콜론 제거(마크다운·print 출력문 모두).
# ─────────────────────────────────────────────────────────────────────────────

c = [title_cell("05", "05_result_interpretation", "결과 해석·시각화", "05_result_interpretation.md", gpu="design")]
c += boot("05_result_interpretation", pip="pandas matplotlib")
c += design_cells("example/vanilla_protein/1g13prot.yaml", "protein-anything", 8, 4,
                  "레퍼런스 결과는 num_designs=100", sec=1)
c += [
md("""## 2) 결과 CSV 열기 — 컬럼이 몇 개인지부터 (본문 5.1)

Ch.04 에서 스모크 실행을 했다면 그 결과를 그대로 이어받습니다(05 에서 다시 안 돌려도 돼요).
한 디자인이 한 행, 컬럼은 수백 개예요. 이 많은 걸 다 볼 필요는 없고 실제로 자주 보는 건 10여 개뿐입니다."""),
co('''from boltzgen_viz import load_metrics, metrics_overview
import pandas as pd

inherit_run("../04_basic_usage/my_run")
CSV = str(find_one("final_designs_metrics_*.csv", "data/vanilla"))
df  = pd.read_csv(CSV)
print("최종 선별 디자인", len(df), "개 | 컬럼", df.shape[1], "개")'''),

md("""## 3) 자주 보는 메트릭 한 표로 (본문 5.2~5.4)

신뢰도(pTM·ipTM) · 위치오차(PAE) · 구조편차(RMSD 두 종류) · 인터페이스(H-bond·염다리·ΔSASA)를 나란히 놓습니다.
읽는 기준은 pTM 0.7 이상 양호, ipTM 0.5 이상이면 결합 가능성 양호, PAE 5Å 미만, `filter_rmsd` 2Å 미만 우수예요.

개발성(본문 5.5)·친화도(본문 5.6)·다양성/신규성(본문 5.7)은 프로토콜과 실행 옵션에 따라만 생성돼요 —
항체는 Ch.08, 소분자는 Ch.10 에서 다룹니다."""),
co('''view = df[cols_in(df, "id", "final_rank", "design_ptm", "design_to_target_iptm", "complex_plddt",
                  "min_design_to_target_pae", "filter_rmsd", "designfolding-filter_rmsd",
                  "plip_hbonds_refolded", "plip_saltbridge_refolded",
                  "delta_sasa_refolded")].sort_values("final_rank")
display(view)

if {"filter_rmsd", "designfolding-filter_rmsd"} <= set(df.columns):
    solo = df[(df["filter_rmsd"] < 2.0) & (df["designfolding-filter_rmsd"] >= 5.0)]
    print(f"복합체 RMSD 는 2A 미만인데 단독 재접힘 RMSD 가 5A 이상인 디자인 {len(solo)}/{len(df)}개")
    print("  타깃이 있어야만 그 모양이 유지된다는 신호예요 (본문 5.3).")'''),

md("""## 4) 표를 그림 한 장으로 (본문 5.10)

숫자 열 개 열을 눈으로 훑는 대신 2×2 개요로 봅니다.
pTM(보라)·ipTM(주황)·RMSD(청록) 바 + 길이↔H-bond 산점도, 임계선은 pTM 0.7 / ipTM 0.5 / RMSD 2.0Å.

> 내가 만든 그림은 `my_05_vanilla_metrics.png` 로 저장돼요(본문에 실린 레퍼런스 그림을 덮어쓰지 않도록)."""),
co('''rows = load_metrics(CSV)
FIG  = my_fig("05_vanilla_metrics.png")
metrics_overview(rows, "Vanilla Protein — Design Metrics Overview", FIG)
from IPython.display import Image; Image(FIG)'''),

md("""## 5) 지표끼리 겹치나 — 상관관계 (본문 5.10)

그림에서 "구조는 대체로 괜찮은데 인터페이스에서 갈린다"가 보였다면, 그 인터페이스 지표들이
서로 같은 말을 반복하는 건 아닌지 확인할 차례예요. 상관이 낮을수록 각자 다른 정보를 준다는 뜻입니다.

> 직접 돌린 결과(4~8개)는 표본이 작아 상관계수가 불안정해요 — 방향만 보세요."""),
co('''m  = df[cols_in(df, "design_ptm", "design_to_target_iptm", "filter_rmsd",
                 "plip_hbonds_refolded", "plip_saltbridge_refolded",
                 "delta_sasa_refolded", "num_design")].astype(float)
cm = m.corr().round(2)

if {"design_ptm", "design_to_target_iptm"} <= set(cm.columns):
    print("pTM ↔ ipTM 상관", cm.loc["design_ptm", "design_to_target_iptm"],
          "— 0 에 가깝거나 음수면 서로 다른 걸 재고 있다는 뜻이라 둘을 함께 봐야 해요 (본문 5.2)")
if {"plip_hbonds_refolded", "delta_sasa_refolded"} <= set(cm.columns):
    print("H-bond ↔ ΔSASA 상관", cm.loc["plip_hbonds_refolded", "delta_sasa_refolded"],
          "— 클수록 두 지표가 같은 얘기를 반복한다는 뜻이에요")
print("\\n판정 — 절댓값이 0.8 을 넘는 쌍은 둘 중 하나만 봐도 되고,")
print("0 근처인 쌍은 반드시 함께 봐야 해요. 그래서 순위도 한 지표로 매기지 않습니다.")
cm'''),

md("""## 6) 이 순위 컬럼들은 어디서 왔나 (본문 4.2·5.8)

표에 `final_rank` 가 있는데, 정작 메트릭을 계산한 **analysis 스텝**의 CSV 에는 없어요.
순위는 그 다음 **filtering 스텝**이 붙입니다. 두 CSV 의 컬럼을 차분하면 무엇이 덧붙었는지 그대로 보여요."""),
co('''POOL = find_one("all_designs_metrics.csv", "data/vanilla")
pool = pd.read_csv(POOL)

agg = None
try:
    agg = pd.read_csv(find_one("aggregate_metrics_analyze.csv", "data/vanilla"))
except Exception as e:
    print("aggregate_metrics_analyze.csv 를 못 찾았습니다 —", type(e).__name__)

print("\\n선별 전 전체 풀", len(pool), "개 | 컬럼", pool.shape[1], "개")
if agg is not None:
    added = [col for col in pool.columns if col not in agg.columns]
    print("analysis 산출", agg.shape[1], "컬럼 → filtering 이", len(added), "개를 덧붙임")
    for kind, pre in [("하드필터 통과 여부", "pass_"), ("메트릭별 순위", "rank_"), ("종합", "")]:
        got = [a for a in added if a.startswith(pre)] if pre else \\
              [a for a in added if a in ("final_rank", "max_rank", "secondary_rank", "quality_score")]
        if got:
            print(f"   {kind:16s}", ", ".join(got[:6]) + (" ..." if len(got) > 6 else ""))

try:
    per = pd.read_csv(find_one("per_target_metrics_analyze.csv", "data/vanilla"))
    print("\\nper_target_metrics_analyze.csv — 타깃 1개가 1행인 요약", per.shape)
except Exception as e:
    print("\\nper_target_metrics_analyze.csv 건너뜀 —", type(e).__name__)'''),

md("""## 7) 왜 pTM 1등이 최종 1등이 아닐까 (본문 5.8)

가장 자주 나오는 질문이에요. 답은 방금 본 `rank_*` 여섯 개에 있습니다.
BoltzGen 은 한 메트릭으로 줄세우지 않고, 여섯 지표를 각각 순위화한 뒤

```
rank_design_to_target_iptm · rank_design_ptm · rank_neg_min_design_to_target_pae
rank_plip_hbonds_refolded · rank_plip_saltbridge_refolded · rank_delta_sasa_refolded
        ↓
   max_rank → secondary_rank → final_rank
```

로 종합해요. 아래 표에서 각 디자인의 여섯 순위와 그 결과를 나란히 봅니다."""),
co('''RANKS = cols_in(df, "rank_design_to_target_iptm", "rank_design_ptm",
                "rank_neg_min_design_to_target_pae", "rank_plip_hbonds_refolded",
                "rank_plip_saltbridge_refolded", "rank_delta_sasa_refolded")
s = df.sort_values("final_rank")

if not RANKS:
    print("이 실행 CSV 에는 rank_* 컬럼이 없어 이 절은 건너뜁니다.")
else:
    tbl = s[cols_in(s, "final_rank", "id") + RANKS + cols_in(s, "max_rank", "secondary_rank")]
    display(tbl.rename(columns={col: col.replace("rank_", "") for col in RANKS}).set_index("final_rank"))

    if "max_rank" in s.columns:
        ok = int((s[RANKS].max(axis=1) == s["max_rank"]).sum())
        print(f"max_rank = 여섯 순위 중 가장 나쁜 값 — {ok}/{len(s)} 행에서 일치")
    if {"max_rank", "secondary_rank"} <= set(s.columns):
        ok2 = int((s["max_rank"].rank(method="dense").astype(int) == s["secondary_rank"]).sum())
        print(f"secondary_rank = max_rank 를 동점끼리 묶어 다시 매긴 순위 — {ok2}/{len(s)} 행에서 일치")

    worst = s[RANKS].idxmax(axis=1).str.replace("rank_", "", regex=False)
    print("\\n각 디자인의 발목을 잡은 지표")
    for rk, wid, w in zip(s["final_rank"], s["id"], worst):
        print(f"   {int(rk):3d}위 {wid:14s} ← {w}")'''),

md("""위 표에서 **한 지표만 1등인 디자인은 위로 못 올라온다**는 게 보여요.
가장 나쁜 순위 하나(`max_rank`)가 그 디자인의 자리를 정하니까요. 아래 셀이 그걸 이름과 숫자로 확인합니다."""),
co('''if RANKS and {"design_ptm", "design_to_target_iptm"} <= set(s.columns):
    tp = s.loc[s["design_ptm"].idxmax()]
    ti = s.loc[s["design_to_target_iptm"].idxmax()]
    top = s.iloc[0]
    print(f"pTM  최고 {tp['design_ptm']:.3f}  ({tp['id']}) → 최종 {int(tp['final_rank'])}위")
    print(f"ipTM 최고 {ti['design_to_target_iptm']:.3f}  ({ti['id']}) → 최종 {int(ti['final_rank'])}위")
    if "max_rank" in s.columns:
        print(f"최종  1위 {top['id']} — 여섯 지표 중 최악이 {top['max_rank']}위로 가장 얕음")
    print("\\n판정 — 한 지표만 특출난 디자인보다 여섯이 고르게 좋은 디자인이 올라와요.")
    print("실험 후보를 고를 때도 ipTM 하나로 줄세우지 말고 표의 여섯 열을 함께 보세요 (본문 5.8).")'''),

md("""## 8) 최종셋 밖으로 밀린 디자인 (본문 5.8)

지금까지 본 건 `budget` 개로 이미 걸러진 최종셋이에요. 선별 **전** 전체 풀에서
ipTM 이 가장 높았던 디자인이 어디로 갔는지 보면, 다양성 선택까지 포함한 선별의 성격이 드러납니다."""),
co('''cand = cols_in(pool, "id", "final_rank", "design_to_target_iptm", "design_ptm",
               "filter_rmsd", "designfolding-filter_rmsd", "num_filters_passed")
top3 = pool.nlargest(3, "design_to_target_iptm")[cand]
print("전체 풀에서 ipTM 상위 3")
print(top3.to_string(index=False))

inside = set(df["id"])
print(f"\\n최종셋(budget {len(df)}) 포함 여부")
for _, r in top3.iterrows():
    print(f"   {r['id']:14s} {'최종셋 안' if r['id'] in inside else '최종셋 밖'}")

print("\\nipTM 만 보고 골랐다면 맨 윗줄을 1순위로 뽑았을 거예요.")
print("표의 나머지 열(RMSD·통과한 필터 수)까지 보면 왜 그 디자인이 위로 못 갔는지 읽힙니다.")'''),

md("""## 9) 기준을 바꿔 다시 선별하기 (본문 5.9)

순위가 어떻게 만들어지는지 알았으니, 이제 기준을 내 목적에 맞게 바꿀 수 있어요.
BoltzGen 레포의 공식 노트북 `filter.ipynb` 가 하드 필터 → 품질 순위 → 다양성 선택 → 시각화를 한 번에 해 줍니다.

```python
Filter(
    design_dir=..., outdir=..., budget=5,
    use_affinity=False,            # 소분자면 True
    refolding_rmsd_threshold=2.5,  # RMSD 하드 필터
    alpha=0.1,                     # 품질 ↔ 다양성 (기본값은 작아요 — 펩타이드 0.01, 그 외 0.001)
    metrics_override={...},        # 메트릭별 중요도
    additional_filters=[...],      # 추가 하드 필터
)
```

같은 일을 CLI 로 하면 `boltzgen run ... --steps filtering` 이에요(Ch.04 7절). 필터링은 몇 초라 여러 번 돌릴 수 있습니다.
기준 하나만 조여도 후보가 얼마나 줄어드는지 지금 데이터로 세어 봅니다."""),
co('''THR = 2.5
if "filter_rmsd" in df.columns:
    keep = df[df["filter_rmsd"] < THR]
    print(f"refolding_rmsd_threshold={THR} → {len(keep)}/{len(df)} 생존")
    if "designfolding-filter_rmsd" in keep.columns:
        keep2 = keep[keep["designfolding-filter_rmsd"] < THR]
        print(f"additional_filters 로 'designfolding-filter_rmsd<{THR}' 까지 걸면 {len(keep2)}/{len(df)} 생존")
        print("   남는 id", ", ".join(keep2["id"].tolist()) or "없음")
    print("\\n기준을 하나 더 얹었을 뿐인데 후보 수가 달라져요. 어떤 기준을 쓸지가 곧 어떤 실험을 할지예요.")
else:
    print("filter_rmsd 컬럼이 없어 이 실습은 건너뜁니다.")'''),

md("""### 이 챕터에서 확인한 것

메트릭 표와 2×2 그림으로 "구조는 대체로 괜찮고 인터페이스에서 갈린다"를 보고,
`rank_*` → `max_rank` → `secondary_rank` → `final_rank` 조립 과정을 데이터로 따라가
**한 지표 1등이 최종 1등이 아닌 이유**를 확인했어요. 마지막엔 기준을 2.5Å 로 조여 후보가 줄어드는 것도 봤고요.

그 "기준 바꾸기"를 명령 한 줄로 반복하는 게 실전 워크플로우입니다 —
하드 필터·가중치·다양성(`--alpha`)·길이 버킷까지 직접 만져보는 건 Ch.06 에서 이어갑니다."""),
]
cells_all[("05_result_interpretation", "05_analysis_viz.ipynb", "05 Analysis & Viz")] = c


# ── 06 고급 필터링·자동화 ───────────────────────────────────────────────────
# ── ch06.py — gen_notebooks.py 의 06 블록 전체 교체본 ─────────────────────────
#
# 변경 요약
#
# [사실 오류 정정]
#  · "규모가 품질을 만든다 — 테스트는 작게, 프로덕션은 크게" 삭제. 06 본문에 없고 6.1 논지와 반대여서,
#    본문 6.1 의 실제 원리("Level 이 올라갈수록 num_designs 는 줄이고 제약은 강화")로 교체.
#  · 필터 노브 설명에서 alpha 방향을 본문 6.4 문구대로 정정(0=품질만, 1=다양성만).
#
# [커버리지 보강 — 데이터로 재계산한 실측만 사용]
#  · 본문 6.4 부등호 방향(`<` = 이 값 이하만 통과)을 최우선 절로 신설. `ALA_fraction < 0.3` 이
#    내장 `pass_ALA_fraction_filter` 와 100/100 완전히 일치함을 노트북이 직접 검증(실측 확인).
#    본문의 `design_ALA` ↔ CSV 컬럼 `ALA_fraction` 대응을 명시.
#  · `--filter_biased`(기본 true) 절 신설 — 조성 5종(ALA/GLY/GLU/LEU/VAL) 내장 판정 컬럼 사용.
#    실측: ALA_fraction ≥ 0.3 이 24/100, 그 24개 평균 pTM 0.381 vs 나머지 76개 0.660.
#    (GLY 등 나머지 임계값은 레퍼런스 실행과 현재 소스가 달라 수치를 단정하지 않고 내장 판정 컬럼을 씀)
#  · `--size_buckets` 를 실데이터로 시연 — num_design 80-100 구간 40개 중 메트릭 통과 8개,
#    100-140 구간 60개 중 1개(길이 쏠림이 실제로 일어남).
#  · `--metrics_override`·`--alpha` 를 포함한 filtering 명령 한 줄 조립.
#  · 본문 6.3 스윕 셀에 `boltzgen merge <dir1> <dir2> ... --output <merged>` 반영(부록 12 확인 문법).
#  · 본문 6.5(커스텀 scaffold YAML 5요소)·6.6(체크포인트/스케줄 표)·6.7(교차검증 순서)·
#    6.8(적용 흐름) 절 신설.
#  · Ch.05 최종 10개와의 연결 — 100개 중 9개 필터를 모두 통과한 3개가 Ch.05 rank 1~3(실측).
#
# [군더더기 축소]
#  · ".head() 를 쓰지 않습니다" 3중복(마크다운 2줄 + 코드 주석) → 마크다운 1문장으로.
#  · 모든 DataFrame 컬럼 선택을 cols_in() 경유로 교체(직접 인덱싱 제거).
#  · 절 번호 1)~10) 중복 없이 연속, 모든 제목에 실재하는 (본문 N.M) 앵커.

# ── 06 고급 필터링·자동화 ───────────────────────────────────────────────────
c = [title_cell("06", "06_advanced_ai", "고급 필터링·자동화", "06_advanced_ai.md")]
c += boot("06_advanced_ai", pip="pandas matplotlib")
c += [
md("""## 1) 선별 전 전체를 펼치기 (본문 6.2)

Ch.05 에서 본 최종 10개는 여기 있는 디자인들에서 걸러진 결과예요. 생성(design~analysis)은 무겁고
선별(filtering)은 몇 초면 끝나니, 한 번 만든 `all_designs_metrics.csv` 위에서 기준만 바꿔가며 실험합니다.

아래 표는 앞부분 미리보기가 아니라 전체 행이에요 — Colab 은 표 아래 페이지 컨트롤로 넘겨 보고,
주피터는 앞뒤만 잘라 `N rows × M columns` 로 표시합니다."""),
co("""import pandas as pd
# Ch.05 또는 Ch.04 에서 직접 돌린 결과가 있으면 그걸 이어서 씁니다(먼저 찾는 쪽 우선)
inherit_run("../05_result_interpretation/my_run", "../04_basic_usage/my_run")
df = pd.read_csv(find_one("all_designs_metrics.csv", "data/vanilla"))
print("선별 전 디자인", len(df), "개 | 컬럼", df.shape[1], "종")
if "pass_filters" in df.columns:
    print("내장 필터를 전부 통과한 디자인", int(df["pass_filters"].astype(bool).sum()), "개")
df[cols_in(df, "id", "design_ptm", "design_to_target_iptm", "filter_rmsd",
           "plip_hbonds_refolded", "num_filters_passed", "pass_filters")]"""),
md("""## 2) 부등호는 통과 조건이다 (본문 6.4)

방금 표의 `pass_*` 는 BoltzGen 이 스스로 매긴 판정이에요. 레퍼런스 100개에서는 이 판정을 전부 통과한 게
3개뿐인데, 그 셋이 Ch.05 최종 순위의 1~3위였어요. 이제 그 판정을 내가 직접 쓰려면
`--additional_filters 'feature<threshold'` 를 쓰는데, 여기서 부등호를 거꾸로 읽는 실수가 잦아요.

- `<` 는 이 값 이하만 통과 (작을수록 좋은 지표)
- `>` 는 이 값 이상만 통과 (클수록 좋은 지표)

그래서 Ala 가 너무 많은 디자인을 버리고 싶으면 `design_ALA<0.3` 이 맞아요. `design_ALA>0.3` 이라고 쓰면
정반대로 Ala 가 30% 넘는 것만 남습니다. 본문의 `design_ALA` 는 CSV 에서 `ALA_fraction` 컬럼으로 나오니,
내장 판정 `pass_ALA_fraction_filter` 와 직접 계산한 `ALA_fraction < 0.3` 이 같은지부터 맞춰 보죠."""),
co("""ALA_T = 0.3                                   # 내장 Ala-rich 배제 임계값
keep = df["ALA_fraction"] < ALA_T              # 'design_ALA<0.3' 이 남기는 쪽
drop = ~keep
print(f"전체 {len(df)}개 | 'ALA_fraction<0.3' 통과 {int(keep.sum())}개 | 탈락(Ala-rich) {int(drop.sum())}개")
if "pass_ALA_fraction_filter" in df.columns:
    agree = int((keep == df["pass_ALA_fraction_filter"].astype(bool)).sum())
    print(f"내장 pass_ALA_fraction_filter 와 일치 {agree}/{len(df)}")

print("\\n부등호를 'ALA_fraction>0.3' 으로 뒤집으면 남는 건 바로 이쪽 (버리려던 것만 남음)")
print(df.loc[drop, cols_in(df, "id", "ALA_fraction", "design_ptm", "design_to_target_iptm")]
        .sort_values("ALA_fraction", ascending=False).head(5).to_string(index=False))"""),
md("""## 3) `--filter_biased` — 조성 이상치를 기본으로 거른다 (본문 6.4)

방금 본 Ala-rich 배제는 사실 기본으로 켜져 있어요(`--filter_biased`, 기본 true).
생성 모델은 종종 ALA·GLY·GLU·LEU·VAL 을 몰아 넣은 "치트성" 서열을 만드는데, 이 다섯 잔기의 비율을
각각 보고 넘치면 탈락 표시를 남깁니다. 정말 버릴 만한 것들인지 pTM 으로 확인해 보죠."""),
co("""comp = cols_in(df, "pass_ALA_fraction_filter", "pass_GLY_fraction_filter",
               "pass_GLU_fraction_filter", "pass_LEU_fraction_filter", "pass_VAL_fraction_filter")
comp_ok = df[comp].astype(bool).all(axis=1)
print(f"조성 필터 {len(comp)}종을 모두 통과 {int(comp_ok.sum())}/{len(df)}")
for name in comp:
    print(f"  {name:34s} 탈락 {int((~df[name].astype(bool)).sum()):3d}개")

rich = df["ALA_fraction"] >= ALA_T
print(f"\\nAla-rich {int(rich.sum())}개 평균 pTM {df.loc[rich, 'design_ptm'].mean():.3f}"
      f" | 나머지 {int((~rich).sum())}개 평균 pTM {df.loc[~rich, 'design_ptm'].mean():.3f}")"""),
md("""## 4) 메트릭 필터 위에 조성 필터를 겹치기 (본문 6.4)

레퍼런스 100개에서는 Ala-rich 24개의 평균 pTM 이 **0.381**, 나머지 76개가 **0.660** 이었어요.
조성만 보고도 걸러지는 게 이만큼 있다는 뜻이니, 결합·구조 메트릭으로 먼저 좁힌 뒤 조성 필터를 얹어 봅니다."""),
co("""m = (df["design_to_target_iptm"] > 0.5) & (df["design_ptm"] > 0.7) & (df["filter_rmsd"] < 2.0)
mc = m & comp_ok
print(f"메트릭 필터만 (ipTM>0.5, pTM>0.7, RMSD<2.0) {int(m.sum())}/{len(df)}")
print(f"조성 필터까지 겹치면 {int(mc.sum())}/{len(df)} — 조성 때문에 추가 탈락 {int((m & ~mc).sum())}개")

sel = df.loc[m, cols_in(df, "id", "design_to_target_iptm", "design_ptm", "filter_rmsd",
                        "ALA_fraction", "GLY_fraction", "num_design")].copy()
sel["comp_pass"] = comp_ok[m].values
sel.sort_values("design_to_target_iptm", ascending=False)"""),
co("""from boltzgen_viz import load_metrics, compare_bars
rows = load_metrics(str(find_one("all_designs_metrics.csv", "data/vanilla", quiet=True)))
g_metric = [r for r in rows if r["design_to_target_iptm"] > 0.5
            and r["design_ptm"] > 0.7 and r["filter_rmsd"] < 2.0]
g_both = [r for r in g_metric if float(r.get("ALA_fraction", 0)) < ALA_T]
FIG = my_fig("06_filter_compare.png")
compare_bars({"all designs": rows, "+ metric": g_metric, "+ composition": g_both},
             "design_to_target_iptm", "Filtering Effect — mean ipTM",
             "mean ipTM", FIG, thr=0.5, thr_label="Good (0.5)")
from IPython.display import Image; Image(FIG)"""),
md("""## 5) 남은 세 노브 — 크기·다양성·가중치 (본문 6.4)

필터를 통과한 것만 모으면 길이가 한쪽으로 쏠릴 수 있어요. `--size_buckets` 는 길이 구간마다 최대 몇 개를
뽑을지 못 박아 다양한 크기를 확보합니다. 방금 통과한 디자인들이 실제로 쏠렸는지부터 보죠."""),
co("""for lo, hi in [(80, 100), (100, 140)]:
    inb = (df["num_design"] >= lo) & (df["num_design"] < hi)
    print(f"길이 {lo}-{hi} : 전체 {int(inb.sum()):3d}개 중 메트릭 통과 {int((inb & m).sum())}개")
print("\\n한 구간에 쏠렸다면 --size_buckets 로 구간별 상한을 걸어 반대쪽 크기도 남깁니다.")"""),
md("""나머지 둘(`--metrics_override`·`--alpha`)은 걸러내는 게 아니라 순위 자체를 바꿔요. 네 노브를 한 번에 정리하면 이렇습니다.

| 옵션 | 의미 |
|------|------|
| `--metrics_override k=w` | 메트릭별 가중치. 값이 클수록 그 메트릭을 덜 중요하게(down-weight) 봅니다 |
| `--alpha 0~1` | 0 이면 품질만, 1 이면 다양성만. 비슷한 서열이 상위를 덮을 때 올립니다 |
| `--size_buckets 80-100:5` | 길이 구간별 선발 상한 |
| `--filter_biased true` | 조성 이상치 배제(기본값 true) |

지금까지 pandas 로 실험한 걸 그대로 명령으로 옮기면 이렇게 돼요."""),
co("""cmd = [
    "boltzgen run spec.yaml --output out --steps filtering",
    "  --metrics_override plip_hbonds_refolded=4 delta_sasa_refolded=2",
    "  --additional_filters 'design_ALA<0.3' 'design_GLY<0.2' 'designfolding-filter_rmsd<2.0'",
    "  --size_buckets 80-100:5 100-140:5",
    "  --alpha 0.3 --filter_biased true",
]
print(" \\\\\\n".join(cmd))
print("\\n생성(design~analysis)은 한 번, filtering 은 기준을 바꿔가며 여러 번 — 이게 본문 6.2 의 핵심 패턴이에요.")"""),
md("""## 6) 계층적 스크리닝 — 한 판이 아니라 라운드로 (본문 6.1)

지금까지 한 건 "한 번 만든 결과를 여러 기준으로 다시 걸러 보기"였어요. 실전에서는 이 걸러내기를 라운드로 쌓습니다.

```
Level 1  넓고 얕게 — boltzgen run spec.yaml --num_designs 10000 --budget 200 --output L1
             ↓ 상위 후보에서 어느 결합 전략이 되는지 파악 → YAML 제약 보강(결합부위 좁히기 등)
Level 2  좁고 깊게 — boltzgen run spec_refined.yaml --num_designs 5000 --budget 20 --output L2
             ↓
Level 3  최종 검증 — 실험 가능한 top 5~10
```

핵심은 Level 이 올라갈수록 `num_designs` 는 줄이고 제약은 강화한다는 거예요. Level 1 에서 방향을 잡고
Level 2 에서 그 방향만 집중 탐색하니, 비용은 줄고 품질은 올라갑니다."""),
md("""## 7) 라운드를 손으로 돌리지 않기 — 스윕과 merge (본문 6.3)

Level 1 의 운영점(`num_designs` × `budget`)을 감으로 정하지 말고 스윕으로 찾습니다.
GPU 가 하나면 동시 실행은 메모리 경합·OOM 을 부르니 순차로 돌리고, 큰 작업은 `--num_designs` 를 쪼개
여러 번 돌린 뒤 `boltzgen merge` 로 합치는 게 정석이에요(메모리 안정성 + 중단 복구)."""),
co("""import itertools
outs = []
for budget, num in itertools.product([20, 50, 100], [1000, 5000]):
    out = f"sweep/b{budget}_n{num}"
    outs.append(out)
    print(f"boltzgen run design.yaml --protocol protein-anything --output {out} "
          f"--num_designs {num} --budget {budget}")
print("\\nboltzgen merge " + " ".join(outs) + " --output sweep/merged")
print("\\n각 실행의 final_ranked_designs/final_designs_metrics_<budget>.csv 를 pandas 로 모아")
print("groupby(['num_designs','budget'])['design_to_target_iptm'].mean() 으로 운영점을 고릅니다.")"""),
md("""## 8) 커스텀 scaffold — 내 골격 위에 결합부위만 재설계 (본문 6.5)

Level 2 의 "제약 강화"를 가장 강하게 거는 방법이 scaffold 예요. 항체·나노바디뿐 아니라 내가 가진
검증된 단백질 골격을 그대로 두고 결합부위만 다시 설계합니다. scaffold YAML 은 다섯 요소로 이뤄져요.

```yaml
# my_scaffold.yaml
path: my_protein.cif
include:
  - chain: { id: A }
design:                       # 재설계할 영역
  - chain: { id: A, res_index: 26..34,52..59,98..118 }
not_design:                   # 절대 고정 (구조 핵심·기능 잔기)
  - chain: { id: A, res_index: 1..25,35..51,60..97,119.. }
structure_groups:
  - group: { id: A, visibility: 2 }                                   # 골격 구조 유지
  - group: { id: A, visibility: 0, res_index: 26..34,52..59,98..118 } # 결합부위는 자유
design_insertions:            # 결합부위 길이 가변 (loop 연장)
  - insertion: { id: A, res_index: 26, num_residues: 1..5 }
reset_res_index:
  - chain: { id: A }
```

타깃 YAML 에서는 파일로 불러오기만 하면 돼요.

```yaml
entities:
  - file: { path: target.cif, include: [ { chain: { id: B } } ] }
  - file: { path: my_scaffold.yaml }   # 여러 개 나열하면 BoltzGen 이 최적을 선택
```

여러 scaffold 를 동시에 주면 각 골격으로 설계를 시도하고 자동으로 최적을 골라요.
CDR3 길이가 다른 scaffold 를 섞으면(짧은 것=평평한 epitope, 긴 것=깊은 pocket) 다양한 타깃 형태에 대응합니다.
Ch.08(Fab)·Ch.09(나노바디) 실습이 바로 이 전략이에요."""),
md("""## 9) 모델 자체를 바꾸기 (본문 6.6)

scaffold 로도 부족할 때 손대는 마지막 층이에요. 표준 워크플로우로 안 될 때만 쓰세요.

| 옵션 | 용도 |
|------|------|
| `--design_checkpoints A.ckpt B.ckpt` | 백본 생성 체크포인트 교체(기본 diverse+adherence) |
| `--inverse_fold_checkpoint C.ckpt` | 역접힘 모델 교체(fine-tune 한 가중치 등) |
| `--folding_checkpoint D.ckpt` | 검증(Boltz-2) 체크포인트 교체 |
| `--affinity_checkpoint E.ckpt` | 친화도 예측기 교체 |
| `--step_scale`, `--noise_scale` | 확산 스케줄 고정(탐색 보수성 조절) |

특정 단백질군(막단백질·효소 패밀리 등)에 대해 역접힘 모델을 자체 데이터로 fine-tune 한 뒤
`--inverse_fold_checkpoint` 로 끼워 넣으면 그 도메인에 특화된 서열 설계가 가능해요."""),
md("""## 10) 교차 검증과 적용 흐름 (본문 6.7·6.8)

여기까지가 BoltzGen 안에서 할 수 있는 전부예요. 신뢰도를 더 올리려면 다른 가정을 쓰는 도구로 다시 걸러야 합니다.
권장 순서는 이렇습니다.

```
BoltzGen(생성·1차 검증)
  → liability / humanness (서열 필터, Ch.08·09)
  → 분자도킹 · MD (물리 검증)
  → 실험
```

- AutoDock Vina — 소분자 결합을 독립적으로 재도킹해 친화도 교차 검증
  (`vina --receptor protein.pdbqt --ligand ligand.pdbqt --out docked.pdbqt`)
- PyMOL — 인터페이스 잔기·수소결합·이황화 거리 시각 검증(`refold_cif` 사용)
- ESM / 서열 분석 — 면역원성·발현성·humanness 예측
- MD 시뮬레이션(GROMACS 등) — 상위 후보의 결합 안정성을 동역학으로 검증

각 단계가 서로 다른 가정으로 거르니, 통과한 후보의 신뢰도가 곱으로 올라가요.
실전 신약 후보 발굴은 이 전부를 한 줄로 꿴 모습이에요.

```
타깃 선정·구조 확보(Ch.02) → 결합부위 전략 수립
   → Level 1 광역 스크리닝(num_designs 10k+)
   → 필터로 좁히기(6.4) → Level 2 집중 재설계 → top 10~50
   → 도킹/MD 교차검증(6.7) → 합성·실험 검증
   → 실험 결과로 필터 기준 개선 → 다음 라운드
```

이 챕터에서 확인한 건 두 가지예요. 부등호 방향 하나로 남는 집합이 정반대가 된다는 것, 그리고
메트릭·조성·크기 필터를 겹칠수록 후보 수는 줄지만 평균 품질은 올라간다는 것. 다음 Part B 부터는
이 선별 기술을 타깃 타입별 실전 설계에 적용해요 — 첫 주자는 고리형 펩타이드입니다."""),
]
cells_all[("06_advanced_ai", "06_advanced_filtering.ipynb", "06 Advanced Filtering")] = c


# ── 07 펩타이드·고리형 (신규) ───────────────────────────────────────────────
# ── ch07.py — gen_notebooks.py 의 07 블록 전체 교체본 ─────────────────────────
#
# 변경 요약 (모든 수치는 data/cyclotide 의 CSV·CIF 를 직접 읽어 재계산)
#
# [사실 오류 정정]
#  · "대부분 34aa·Cys 6개" 삭제 → 실측은 길이 34aa 10/10, Cys 정확히 6개는 3/10(나머지 7~10개).
#    대신 데이터에서 진짜로 100% 지켜진 것을 셉니다 — 명세가 못 박은 Cys 6자리(4/13/20/26/30/32)
#    보존이 최종 10/10, 선별 전 100개에서도 100/100.
#  · "타깃은 cyclotide 3ivq(34aa, 6 Cys, knot)" 삭제 → 34aa·Cys·knot 은 설계물의 성질.
#    결과 CIF 실측은 설계 사슬 34잔기 + 타깃 사슬 140잔기 (= 본문 7.2 의 174 토큰).
#  · "작은 고리 펩타이드라 절대값은 단백질-단백질보다 낮다" 삭제(07 본문에 근거 없음)
#    → 본문 7.8 의 실제 판정 원리(ipTM·pTM·PAE 가 함께 순위를 좌우)로 교체.
#  · RMSD "~2.3Å 이하" → 실측 최댓값 2.33Å(rank 10), 최저 1.15Å(rank 4)을 코드가 계산해 출력.
#  · 인용 (본문 7) → 실재 절 번호 (본문 7.2/7.3/7.4/7.5/7.6/7.7/7.8/7.9).
#  · 결과 CIF 의 설계 사슬 라벨은 A, 타깃이 B — 명세의 chain B 와 반대라 사슬 하드코딩을 제거하고
#    designed_chain_sequence 와 일치하는 사슬(없으면 최단 사슬)을 찾도록 바꿈.
#
# [커버리지 보강]
#  · 입력 YAML 절 신설 — `cyclic: true`, `constraints.bond` `atom1: [B, 4, SG]` 형식,
#    시스테인 패턴 3C8C6C5C3C1C2 → 34잔기·Cys 6개 (본문 7.3·7.4·7.5).
#  · 고리화를 실제로 검증 — gemmi 로 N말단 N ↔ C말단 C 거리 측정. rank001 실측 1.31Å(펩타이드 결합).
#  · 이황화 셀에 판정 기준 2종 부착 — 이상 SG–SG 2.0~2.1Å(본문 7.4)와 Cys 간격 권장 3~15잔기.
#    고리라 반대 방향 경로가 더 짧을 수 있어 간격을 고리 기준으로 계산.
#    rank001 실측 SG–SG: Cys4–26 1.77Å, Cys20–32 1.85Å, Cys13–30 1.98Å.
#  · 이 실행이 실제로 밟은 스텝을 steps.yaml 에서 읽어 출력(단계 수를 문장으로 단정하지 않음).
#  · 본문 7.6(secondary_structure)·7.7(binding_types)·7.9(실험 경로·후보 3축) 절 신설.
#  · 본문 7.8 의 "H-bond 수만으론 순위가 안 정해진다"(rank 3 이 H-bond 10개 최다인데 3위) 반영.
#
# [구조·군더더기]
#  · design_cells(..., sec=1) 명시 → `## 1)` 중복 해소, 이후 절을 2)~10) 으로 연속.
#  · 모든 DataFrame 컬럼 선택을 cols_in() 경유로 교체.

# ── 07 펩타이드·고리형 ──────────────────────────────────────────────────────
c = [title_cell("07", "07_peptide_cyclic", "펩타이드·고리형(cyclotide) 실습", "07_peptide_cyclic.md", gpu="design")]
c += boot("07_peptide_cyclic", pip="pandas matplotlib gemmi")
c += design_cells("example/cyclotide/3ivq.yaml", "peptide-anything", 8, 4,
                  "레퍼런스 결과는 num_designs=100", sec=1)
c += [
md("""## 2) 방금 그 명령이 요구한 것 — 입력 명세 (본문 7.3·7.4·7.5)

`example/cyclotide/3ivq.yaml` 은 짧지만 제약이 세 겹으로 걸려 있어요. 뒤에서 결과를 검증할 때 기준이 되니
먼저 읽고 갑니다.

```yaml
entities:
  - protein:
      id: B
      sequence: 3C8C6C5C3C1C2   # 3개+C+8개+C+6개+C+5개+C+3개+C+1개+C+2개 = 34잔기, Cys 6개
      cyclic: true              # 머리-꼬리 펩타이드 결합 자동 생성
  - file:
      path: 3ivq.cif
      include: [ { chain: { id: A } } ]
      structure_groups: "all"
constraints:
  - bond: { atom1: [B, 4, SG],  atom2: [B, 26, SG] }   # [체인, 잔기번호, 원자이름]
  - bond: { atom1: [B, 13, SG], atom2: [B, 30, SG] }
  - bond: { atom1: [B, 20, SG], atom2: [B, 32, SG] }
```

- `cyclic: true` — N말단과 C말단 사이에 펩타이드 결합이 자동으로 생겨요. 끝이 없으니 분해효소가 물 자리가 없죠.
- `constraints.bond` — 시스테인 6개를 3쌍으로 묶어 이황화(-S-S-)를 만듭니다. 이상 거리는 약 2.0~2.1Å 이에요.
- 서열 패턴 `3C8C6C5C3C1C2` — Cys 자리를 4·13·20·26·30·32 로 못 박고 나머지 28자리만 AI 가 채웁니다.

이 셋이 겹쳐야 cystine knot 이 완성돼요. 그러니 검증할 것도 셋이에요 — 서열, 고리, 이황화."""),
md("""## 3) 이 실행이 실제로 밟은 스텝 (본문 7.2)

`peptide-anything` 은 inverse folding 단계에서 자유 시스테인을 억제해요 — 자유 Cys 가 엉뚱한 이황화나
응집을 만들기 때문이에요. 우리가 `constraints` 로 지정한 Cys 는 그와 별개로 배치되고요.
실제로 어떤 스텝이 돌았는지는 출력 폴더의 `steps.yaml` 에 그대로 적혀 있습니다."""),
co("""import pathlib
steps = pathlib.Path(find_one("steps.yaml", "data/cyclotide"))
print(steps.read_text().strip())"""),
md("""## 4) 최종 10개 메트릭 (본문 7.8)

스텝을 다 밟고 나온 결과예요. `num_tokens` 가 복합체 전체 크기(설계 펩타이드 + 타깃),
`num_design` 이 AI 가 실제로 채운 자리 수입니다."""),
co("""from boltzgen_viz import load_metrics, metrics_overview
import pandas as pd
CSV = str(find_one("final_designs_metrics_*.csv", "data/cyclotide"))
df = pd.read_csv(CSV)
print("최종 디자인", len(df), "개")
df[cols_in(df, "id", "final_rank", "design_ptm", "design_to_target_iptm",
           "min_design_to_target_pae", "filter_rmsd", "plip_hbonds_refolded",
           "num_design", "num_tokens")].sort_values("final_rank")"""),
md("""## 5) 메트릭 개요 그래프 (본문 7.8)

길이가 34aa 로 고정된 설계라 네 번째 패널은 길이 산점도 대신 H-bond 막대를 씁니다."""),
co("""rows = load_metrics(CSV)
FIG = my_fig("07_cyclotide_metrics.png")
metrics_overview(rows, "Cyclotide (3ivq) — Design Metrics Overview", FIG, panel4="hbonds")
from IPython.display import Image; Image(FIG)"""),
md("""## 6) 검증 ① 서열 — 제약 자리가 살아남았나 (본문 7.5)

그래프는 "얼마나 좋은가"를 보여줄 뿐, "요구한 대로 만들어졌는가"는 답하지 않아요. 먼저 서열부터 봅니다.
길이가 34aa 인지, 그리고 명세가 Cys 로 못 박은 4·13·20·26·30·32 자리가 그대로인지 세어 보죠.
(`num_design`=28 은 34자리에서 Cys 6자리를 뺀, AI 가 채운 자리 수예요.)"""),
co("""from collections import Counter
SEQ_LEN   = 34                                 # 3+1+8+1+6+1+5+1+3+1+1+1+2
CYS_SITES = [4, 13, 20, 26, 30, 32]            # 명세가 Cys 로 고정한 자리
d = df.sort_values("final_rank")
n_len = n_sites = 0
for _, r in d.iterrows():
    s = str(r["designed_chain_sequence"])
    pos = [i + 1 for i, a in enumerate(s) if a == "C"]
    kept = all(p in pos for p in CYS_SITES)
    n_len += int(len(s) == SEQ_LEN)
    n_sites += int(kept)
    mark = "" if kept else "   <-- 제약 자리 누락"
    print(f"rank{int(r['final_rank']):>2} {str(r['id']):9s} len={len(s):3d} Cys={len(pos):2d} @ {pos}{mark}")
print(f"\\n길이 {SEQ_LEN}aa {n_len}/{len(d)} | 제약 Cys 6자리 전부 보존 {n_sites}/{len(d)}")
print("Cys 총개수 분포", dict(sorted(Counter(str(x).count("C")
                                        for x in d["designed_chain_sequence"]).items())))"""),
md("""합격선은 길이와 제약 자리예요. 6자리가 전부 살아 있으면 이황화 3쌍을 만들 재료가 갖춰진 거고,
그 밖의 자리에 Cys 가 더 붙은 건 생성 다양성이라 그 자체로는 탈락 사유가 아니에요.
다만 짝 없는 Cys 는 응집 위험이니, 실제로 어느 쌍이 결합했는지는 8절에서 거리로 확인합니다."""),
md("""## 7) 검증 ② 구조 — 고리가 닫혔나 (본문 7.3)

`cyclic: true` 가 지켜졌다면 N말단의 N 과 C말단의 C 가 펩타이드 결합 거리(약 1.3Å)만큼 붙어 있어야 해요.
최종 CIF 를 gemmi 로 열어 직접 잽니다. 출력 CIF 의 사슬 라벨은 명세와 다를 수 있어서,
라벨 대신 설계 서열과 일치하는 사슬을 찾습니다."""),
co("""import gemmi
top = df.sort_values("final_rank").iloc[0]
cif = find_one(f"final*designs/*{top['id']}*.cif", "data/cyclotide")
model = gemmi.read_structure(str(cif))[0]

want = str(top["designed_chain_sequence"])
def chain_seq(ch):
    return gemmi.one_letter_code([r.name for r in ch]).upper()
hit = [ch for ch in model if chain_seq(ch) == want]
design = hit[0] if hit else min(model, key=lambda ch: len(ch))   # 폴백은 가장 짧은 사슬
res = list(design)

print(cif.name, "| 사슬 구성", {ch.name: len(ch) for ch in model})
print(f"설계 사슬 = {design.name} ({len(res)}잔기), 나머지가 타깃")

n_at, c_at = res[0].find_atom("N", "*"), res[-1].find_atom("C", "*")
if n_at is None or c_at is None:
    print("\\n말단 백본 원자가 없어 고리화 판정을 건너뜁니다.")
else:
    d_nc = n_at.pos.dist(c_at.pos)
    verdict = "펩타이드 결합 = 고리 닫힘" if d_nc < 1.6 else "떨어져 있음 = 선형"
    print(f"\\nN말단 N ↔ C말단 C 거리 {d_nc:.2f} A → {verdict}")"""),
md("""## 8) 검증 ③ 구조 — 이황화 3쌍이 맺혔나 (본문 7.4)

고리가 닫혔으면 이제 매듭이에요. 같은 사슬 안 모든 Cys 쌍의 SG–SG 거리를 재서
이상값 2.0~2.1Å 근처인 쌍을 찾습니다. 서열상 두 Cys 사이 간격도 함께 봐요 — 권장은 3~15잔기인데,
고리형이라 반대 방향으로 도는 경로가 더 짧으면 그쪽을 씁니다."""),
co("""import itertools
sg = [(r.seqid.num, r.sole_atom("SG").pos) for r in res
      if r.name == "CYS" and r.find_atom("SG", "*") is not None]
L = len(res)
pairs = sorted(((a[0], b[0], a[1].dist(b[1])) for a, b in itertools.combinations(sg, 2)),
               key=lambda x: x[2])
bonded = [p for p in pairs if p[2] < 2.5]
print(f"SG 원자 {len(sg)}개 | 이상 SG-SG 거리 2.0~2.1 A")
for i, j, dist in bonded + [p for p in pairs if p[2] >= 2.5][:2]:
    step = abs(j - i)
    gap  = min(step - 1, L - step - 1)          # 고리 기준 최단 간격(사이에 낀 잔기 수)
    if dist < 2.5:
        note = "권장 3~15 안" if 3 <= gap <= 15 else "권장 범위 밖"
        print(f"  CYS{i:>3}-CYS{j:<3} {dist:5.2f} A  이황화 | 사이 잔기 {gap:2d} ({note})")
    else:
        print(f"  CYS{i:>3}-CYS{j:<3} {dist:5.2f} A  결합 아님")
print(f"\\n이황화 {len(bonded)}쌍 형성 — 명세가 요구한 건 Cys4-26, 13-30, 20-32 세 쌍이에요.")"""),
md("""판정은 거리로 합니다. 2.0~2.1Å 근처면 결합, 8Å처럼 크게 벌어졌으면 안 닫힌 거예요.
그때 손볼 곳은 구조가 아니라 서열 패턴이에요 — 두 Cys 를 서열상 더 가깝게(`5C20C5` → `5C10C5`) 좁히면
닫힐 확률이 올라갑니다. 간격 3~15잔기는 그 설계 단계의 권장 범위이지, 이미 닫힌 결합의 합격선은 아니에요.

제약 3쌍이 모두 2.5Å 미만으로 나왔다면 cystine knot 이 완성된 겁니다."""),
md("""## 9) 더 좁히고 싶을 때 — 2차구조와 결합부위 (본문 7.6·7.7)

여기까지가 기본 제약이고, 결과가 마음에 안 들면 두 가지를 더 걸 수 있어요.

2차구조를 강제하려면 `secondary_structure` 를 씁니다. 평평한 결합면에는 sheet, 깊은 groove 에는 helix 가
유리해요. sheet 는 최소 3~4잔기 이상이어야 형성되고, 너무 짧게 지정하면 loop 로 끝나요.

```yaml
- protein:
    id: B
    sequence: 1C11..16C1
    secondary_structure:
        sheet: 1,3..11          # 이 잔기들을 beta-sheet 로
```

붙을 자리를 지정하려면 타깃 쪽에 `binding_types` 를 겁니다.

```yaml
- file:
    path: target.cif
    include: [ { chain: { id: A } } ]
    binding_types:
      - chain: { id: A, binding: 343,344,251 }
    structure_groups: "all"
```

둘 다 선택 기능이라 굳이 강제하지 않아도 AI 가 알아서 최적화해요 — 특정 구조나 자리가 꼭 필요할 때만 쓰세요.
`binding_types` 를 걸었다면 결과 CSV 의 인터페이스 접촉 잔기를 확인해 지정한 자리에 실제로 붙었는지 검증하고요."""),
md("""## 10) 종합 판정과 실험 후보 (본문 7.8·7.9)

제약이 다 지켜졌다면 이제 순위를 읽을 차례예요. 읽는 원칙은 셋입니다.

- ipTM·pTM·PAE 가 함께 순위를 좌우해요. 어느 하나만 보고 고르지 않습니다.
- RMSD 는 자기일관성 — 낮을수록 "설계한 모양이 서열로 재현"된 거예요.
- H-bond 수는 순위를 결정하지 않아요. 레퍼런스에서는 H-bond 가 10개로 가장 많은 rank 3 이 최종 3위였어요.

실험 후보는 하나만 고르지 말고 성격이 다른 셋을 함께 보내는 게 정석이에요(본문 7.9)."""),
co("""d = df.sort_values("final_rank")
pick = [("결합력(ipTM 최고)",     d["design_to_target_iptm"].idxmax()),
        ("구조 안정성(pTM 최고)", d["design_ptm"].idxmax()),
        ("자기일관성(RMSD 최저)", d["filter_rmsd"].idxmin())]
for label, idx in pick:
    r = d.loc[idx]
    print(f"rank{int(r['final_rank']):>2} {str(r['id']):9s} "
          f"ipTM {r['design_to_target_iptm']:.3f} | pTM {r['design_ptm']:.3f} "
          f"| RMSD {r['filter_rmsd']:.2f} A   <- {label}")
hb = d.loc[d["plip_hbonds_refolded"].idxmax()]
print(f"\\nRMSD 최댓값 {d['filter_rmsd'].max():.2f} A"
      f" | H-bond 최다는 rank {int(hb['final_rank'])} ({int(hb['plip_hbonds_refolded'])}개)")"""),
md("""34잔기짜리 작은 펩타이드라 SPPS(고상 펩타이드 합성)로 만들 수 있어요. 실험 경로는 이렇습니다.

1. SPPS 로 선형 펩타이드 합성 (약 2주)
2. Native chemical ligation 으로 고리화
3. Oxidative folding 으로 이황화 3쌍 형성
4. Mass spec + NMR 로 구조 검증
5. SPR 로 결합 친화도 측정

이 챕터에서 확인한 건 "메트릭보다 제약 준수가 먼저"라는 순서예요. 서열(6절)·고리(7절)·이황화(8절)가
모두 통과한 뒤에야 ipTM 순위가 의미를 가집니다. 다음 Ch.08 에서는 제약이 훨씬 많은 항체 Fab 을 다뤄요 —
거기서는 재설계 영역(CDR)만 바뀌고 framework 는 그대로여야 한다는 새 합격선이 붙습니다."""),
]
cells_all[("07_peptide_cyclic", "07_peptide_lab.ipynb", "07 Peptide / Cyclic Lab")] = c


# ── 08 항체 Fab ─────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────
# 08 항체 Fab — gen_notebooks.py 의 08 블록 교체본
#
# [고친 사실 오류]
#  · "사전설계 CDR → analysis/filtering 2스텝" 단정 삭제 → steps.yaml 을 읽어 실제 스텝을 출력
#    (커밋 레퍼런스는 analysis·filtering 2스텝인 재개 산출물, 내 my_run/ 은 5스텝이 그대로 보임)
#  · 경쇄 예시 `EIVLTQ` 삭제 — 실측 N말단은 DIQMTQ·DIVMTQ(κ)·ESVLTQ(λ) (상위 5개 기준)
#  · framework 셀이 designed_chain_sequence 하나(= full_sequence_1)만 읽어 VH/VL 중 한쪽만 표시하던 것을
#    full_sequence_1·full_sequence_2 두 사슬 순회로 수정 (제목 "VH/VL 모두"와 실제 동작 일치)
#  · 실전 규모 "1k+" → 본문 8.7 "수천 개"
#  · liability 모티프·"낮을수록 좋음" 인용 (본문 8.6) → (본문 8.5)
#  · 모티프별 개수를 liability_*_count 로 표시하던 것 수정 — 이 실행에서 8종 _count 는 전부 0 이고
#    실제 검출은 liability_violations_summary 문자열에 담김(실측 확인)
#  · `## 1)` 중복 해소 — design_cells(sec=1) 명시 + 이후 2)~8) 연속 번호
#
# [채운 커버리지]
#  · antibody-anything 정의(Cys 자동 금지 + design_folding 생략) — 이미 세고 있던 Cys 수를 규칙에 연결
#    (재설계 구간 Cys 0 = 금지 규칙 / 사슬당 Cys 2 = framework 보존 이황화쌍)
#  · scaffold YAML 3요소(design / not_design / design_insertions) — 본문 8.4
#  · framework 이상 시 not_design 확대 조치 — 본문 8.6
#  · num_design 48~60aa 해석 + 두 사슬 재설계 길이 합과 대조 — 본문 8.7
#  · 실험 후보 3축(ipTM 높음 + RMSD 낮음 + liability_score 낮음) 교집합 — 본문 8.7
#
# [줄인 군더더기]
#  · 7uxq.cif 다운로드 안내 2회 → 1회, "건너뛰어도 됩니다" 계열 문구 제거
#  · 모든 마크다운 제목에 실재 절 앵커(8.3~8.7) 부여, 문장 끝 콜론 제거(print 출력 포함)
#
# [데이터로 재확인한 수치] data/fab/final_designs_metrics_10.csv (10행 207열), steps.yaml
#  · ipTM 상위 rank4 0.486 / rank5 0.482 / rank1 0.463, RMSD <2Å = rank1·2·3
#  · num_design 48~60 이고 매 행에서 len(designed_sequence_1)+len(designed_sequence_2) 와 정확히 일치
#  · 20개 사슬 전부 Cys 2개, 재설계 구간(designed_sequence_1/2) Cys 0개
#  · liability_score 최저 rank1=90, 3축 상위 3개 교집합 = pdl1_05(rank 1) 단 하나
# ─────────────────────────────────────────────────────────────────────────────

# ── 08 항체 Fab ─────────────────────────────────────────────────────────────
c = [title_cell("08", "08_antibody_fab", "항체 Fab 실습 + developability", "08_antibody_fab.md", gpu="design")]
c += boot("08_antibody_fab", pip="pandas matplotlib")
c += design_cells("example/fab_targets/pdl1.yaml", "antibody-anything", 8, 4,
                  "레퍼런스 결과는 num_designs=30", sec=1,
                  # pdl1.yaml 이 참조하는 7uxq.cif 는 BoltzGen 레포에 커밋돼 있지 않음 → 먼저 받아온다
                  pre_files=[("example/fab_targets/7uxq.cif",
                              "https://files.rcsb.org/download/7uxq.cif")])
c += [
md("""## 2) 무엇이 실제로 돌았나 — `steps.yaml` (본문 8.3)

`antibody-anything` 은 `protein-anything` 과 스텝 구성부터 달라요.

- **inverse folding 에서 Cys 자동 금지** — CDR 에 자유 시스테인이 생기면 도메인 안의 이황화 짝이 어긋나요.
- **design_folding 생략** — CDR 은 framework·타깃에 의존적이라 단독 폴딩이 무의미해요.
- 최대 소수성 패치 미계산.

레퍼런스를 만든 명령은 이거예요. 타깃 `7uxq.cif` 는 BoltzGen 레포에 없어서 먼저 받아야 하고, 위 설계 셀이 그 다운로드까지 해 둡니다.

```bash
curl -sSL -o example/fab_targets/7uxq.cif https://files.rcsb.org/download/7uxq.cif
boltzgen run example/fab_targets/pdl1.yaml --output workbench/fab \\
  --protocol antibody-anything --num_designs 30 --budget 10
```

스텝 구성은 외우지 말고, 실행이 출력 폴더에 남긴 `steps.yaml` 에서 그대로 읽어요."""),
co('''steps_file = find_one("steps.yaml", "data/fab")
names = [ln.split(":", 1)[1].strip()
         for ln in steps_file.read_text().splitlines()
         if ln.strip().startswith("- name:")]

print("이 출력 폴더에서 실행된 스텝", len(names), "개")
for i, n in enumerate(names, 1):
    print(f"  {i}. {n}")
print()
print("design_folding 포함 —", "예" if "design_folding" in names else "아니오 (antibody-anything 은 이 스텝을 생략)")
print("이 목록은 '이 출력 폴더에서 실제로 돈 스텝'이에요 — 앞 스텝 산출물을 재사용해 이어 돌리면 그만큼만 남습니다.")'''),
md("""## 3) 결과 표 — 무엇을 보나 (본문 8.6)

돌아간 스텝이 남긴 건 메트릭 CSV 한 장이에요. 본문 8.6 이 꼽는 다섯 가지를 한 줄에 모아 봅니다 —
`design_to_target_iptm`(PD-L1 결합), `design_ptm`·`filter_rmsd`(구조·자기일관성),
`num_design`(재설계 CDR 길이), `liability_score`(개발성)."""),
co('''from boltzgen_viz import load_metrics, metrics_overview
import pandas as pd

CSV = str(find_one("final_designs_metrics_*.csv", "data/fab"))
df = pd.read_csv(CSV).sort_values("final_rank").reset_index(drop=True)
print("디자인", len(df), "개 | 전체 컬럼", df.shape[1], "종")
df[cols_in(df, "final_rank", "id", "design_ptm", "design_to_target_iptm",
           "filter_rmsd", "plip_hbonds_refolded", "num_design", "liability_score")]'''),
md("""## 4) 메트릭 그래프 — 순위와 함께 보기 (본문 8.7)

표의 숫자가 순위를 따라 어떻게 움직이는지는 그림이 빨라요. pTM(보라)·ipTM(주황)·RMSD(청록) 바에
길이–H-bond 산점도가 붙습니다. 레퍼런스 그림(`08_fab_metrics.png`)을 덮지 않도록 `my_` 접두어로 저장돼요."""),
co('''rows = load_metrics(CSV)
FIG = my_fig("08_fab_metrics.png")
metrics_overview(rows, "Antibody Fab (PD-L1) — Design Metrics Overview", FIG)
from IPython.display import Image; Image(FIG)'''),
md("""## 5) 재설계된 곳은 CDR 뿐인가 — `num_design` 과 자유 Cys (본문 8.4·8.7)

레퍼런스에서는 ipTM 이 rank 4(0.486)·rank 5(0.482)·rank 1(0.463) 순으로 높고, RMSD 는 rank 1·2·3 이 2Å 미만이었어요.
그런데 이 숫자는 **CDR 만 바뀌었을 때**만 의미가 있어요 — framework 까지 흔들렸다면 scaffold 설계가 아니니까요.

각 scaffold YAML 이 세 요소로 "어디를 건드릴지"를 못 박아요(본문 8.4).

```yaml
# adalimumab.6cr1.yaml (요약)
design:            [ { chain: { id: H, res_index: 27..38,56..65,99..110 } } ]        # CDR 재설계
not_design:        [ { chain: { id: H, res_index: 1..26,39..55,66..98,111.. } } ]    # framework 고정
design_insertions: [ { insertion: { id: H, res_index: 99, num_residues: 1..12 } } ]  # CDR3 길이 가변
```

`num_design` 은 이렇게 열어 준 구간의 총 길이예요(본문 8.7의 48~60aa). Fab 는 사슬이 둘이니
`designed_sequence_1`·`designed_sequence_2` 길이를 각각 세서 합이 `num_design` 과 맞는지, 그리고
그 구간에 **자유 Cys 가 하나도 없는지** 확인합니다."""),
co('''des_cols = cols_in(df, "designed_sequence_1", "designed_sequence_2") or cols_in(df, "designed_sequence")
has_nd = "num_design" in df.columns

for _, r in df.head(5).iterrows():
    parts = [str(r[col]) for col in des_cols]
    lens = "+".join(str(len(p)) for p in parts)
    nd = f"num_design={int(r['num_design']):3d} | " if has_nd else ""
    print(f"rank{int(r['final_rank'])} {r['id']:8s} {nd}사슬별 재설계 {lens} = {sum(len(p) for p in parts):3d} "
          f"| 재설계 구간 Cys={sum(p.count('C') for p in parts)}")

print()
if has_nd:
    print("재설계 영역 길이 범위", int(df["num_design"].min()), "~", int(df["num_design"].max()), "aa")
    print("→ 사슬별 합이 num_design 과 같으면 설계가 CDR 구간 밖으로 새지 않은 거예요.")
print("→ 재설계 구간 Cys 가 0 이면 antibody-anything 의 Cys 자동 금지가 지켜진 겁니다 (본문 8.3).")'''),
md("""## 6) Developability — liability (본문 8.5)

CDR 은 규칙대로 만들어졌어요. 다음 질문은 **약이 될 수 있는가**예요. ipTM 이 좋아도 Met 산화·Asp 절단·소수성 패치가
몰려 있으면 발현·정제·보관에서 무너지거든요. 종합 지표 `liability_score` 는 **낮을수록** 개발하기 쉬운 후보고요(본문 8.5).

모티프별 검출 내역은 `liability_*_count` 가 아니라 `liability_violations_summary` 문자열에 들어 있어요
(`ProtTrypx7(pos18-105,sev10); MetOx(pos4,sev5); …` 형태)."""),
co('''import collections

score_cols = cols_in(df, "final_rank", "id", "liability_score", "liability_num_violations",
                     "liability_high_severity_violations", "liability_medium_severity_violations")
tbl = df[score_cols]
if "liability_score" in tbl.columns:
    tbl = tbl.sort_values("liability_score")
print("liability_score 낮은 순 (낮을수록 개발성 우수)")
print(tbl.to_string(index=False))

if "liability_violations_summary" in df.columns:
    tot = collections.Counter()
    for summary in df["liability_violations_summary"].astype(str):
        for item in summary.split(";"):
            head = item.strip().split("(", 1)[0]
            if not head:
                continue
            name, mult = head, 1
            if "x" in head:
                stem, _, tail = head.rpartition("x")
                if tail.isdigit():
                    name, mult = stem, int(tail)
            tot[name] += mult
    print()
    print("최종셋 전체에서 검출된 위험 모티프 (합계)")
    for name, n in tot.most_common():
        print(f"  {name:12s} {n}")

print()
print("→ 같은 ipTM 대라면 liability_score 가 낮은 쪽이 임상으로 갈 확률이 높아요.")'''),
md("""## 7) Framework 보존 — VH·VL 두 사슬 모두 (본문 8.6)

개발성까지 봤으니 마지막은 "그래프팅이 정상이었나"예요. Fab 는 한 디자인이 **두 사슬**이라 메트릭 CSV 도
`full_sequence_1`·`full_sequence_2` 두 칸에 나눠 담아요. 한 칸만 읽으면 중쇄와 경쇄 중 하나를 통째로 놓칩니다.

- 중쇄(VH) — `EVQLVE…`·`QVQLQE…` 로 시작해 J-region `…WGQGTLVTVSS` 로 끝나요.
- 경쇄 κ — `DIQMTQ…`·`DIVMTQ…` → `…FGQGTKVEIK`
- 경쇄 λ — `ESVLTQ…` → `…FGGGTKLTVL`

그리고 도메인 안의 **보존 Cys 2개**(framework 이황화쌍)는 사슬마다 그대로 남아야 해요."""),
co('''import collections

def chain_kind(s):
    """말단 J-region 모티프로 중쇄/경쇄(κ/λ) 판별 — N말단 prefix 보다 견고."""
    if "WGQG" in s[-15:] or "WGRG" in s[-15:]:                # 중쇄 J: …WGQGT(L/T/M)VTVSS
        return "VH"
    if s.endswith(("EIK", "EIKR")) or "FGQGTK" in s[-14:]:    # κ 경쇄 J: …FGQGTKVEIK
        return "VL-k"
    if "LTVL" in s[-7:] or "FGGGTK" in s[-14:] or "FGSGTK" in s[-14:]:   # λ 경쇄 J: …FGGGTKLTVL
        return "VL-l"
    return "?"

chain_cols = cols_in(df, "full_sequence_1", "full_sequence_2") or cols_in(df, "designed_chain_sequence")

for _, r in df.head(5).iterrows():
    for col in chain_cols:
        s = str(r[col])
        print(f"rank{int(r['final_rank'])} {r['id']:8s} {chain_kind(s):5s} len={len(s):4d} "
              f"Cys={s.count('C')} | {s[:6]}… …{s[-11:]}")

kinds = collections.Counter(chain_kind(str(r[col])) for _, r in df.iterrows() for col in chain_cols)
print()
print("사슬 종류 분포", dict(kinds))
print("→ 한 디자인에서 VH 와 VL 이 하나씩 잡히고 사슬당 Cys 가 2개면 CDR 만 바뀐 정상 그래프팅이에요.")
print("→ framework 가 많이 변했으면 scaffold YAML 의 not_design 범위를 넓혀 더 고정하세요 (본문 8.6).")'''),
md("""## 8) 어떤 후보를 실험으로 보낼까 (본문 8.7)

결합(ipTM)·구조(RMSD)·개발성(liability_score) 세 축은 서로 다른 후보를 가리켜요.
세 축 상위 3개를 각각 뽑아 **교집합에 남는 후보**가 균형 잡힌 후보예요."""),
co('''axes = [("결합  ipTM 높음", "design_to_target_iptm", False),
        ("구조  RMSD 낮음", "filter_rmsd", True),
        ("개발성 liability_score 낮음", "liability_score", True)]

picks = []
for label, col, asc in axes:
    if col not in df.columns:
        continue
    top3 = df.sort_values(col, ascending=asc).head(3)
    picks.append(set(top3["id"]))
    shown = ", ".join(f"{i}({v:.3f})" if isinstance(v, float) else f"{i}({v})"
                      for i, v in zip(top3["id"], top3[col]))
    print(f"{label:26s} {shown}")

both = set.intersection(*picks) if picks else set()
print()
if both:
    print("세 축을 모두 만족하는 후보 —", ", ".join(sorted(both)))
    print("→ 이 후보부터 발현·SPR 로 검증하세요.")
else:
    print("세 축을 모두 만족하는 후보 없음 — 표본이 작아 세 조건이 한 디자인으로 모이지 않았어요.")
    print("→ num_designs 를 키워 꼬리를 더 뽑아야 합니다.")'''),
md("""### 이 챕터에서 확인한 것 (본문 8.7)

- 실행 스텝은 문장이 아니라 `steps.yaml` 이 사실이고, `antibody-anything` 은 design_folding 을 쓰지 않아요.
- 재설계는 CDR 구간(48~60aa) 안에 갇혀 있고 그 안에 자유 Cys 가 없어요 — 프로토콜의 Cys 금지가 실제로 걸린 증거예요.
- VH·VL 두 사슬의 framework 말단과 보존 Cys 2개가 모두 살아 있어 정상 그래프팅이에요.
- num_designs 30 은 데모 규모예요. 실전 항체 캠페인은 **수천 개**까지 올려, 결합·구조·개발성을 동시에 만족하는
  희귀한 후보를 꼬리에서 건집니다(본문 8.7).

다음 Ch.09 는 같은 그래프팅을 **사슬 하나(VHH)** 로 할 때 무엇이 쉬워지고 무엇이 어려워지는지 봐요."""),
]
cells_all[("08_antibody_fab", "08_fab_lab.ipynb", "08 Antibody Fab Lab")] = c


# ── 09 나노바디 ─────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────
# 09 나노바디 — gen_notebooks.py 의 09 블록 교체본
#
# [고친 사실 오류]
#  · scaffold "4종" → **5종**(7eow·7xl0·gontivimab·isecarosmab·sonelokimab, 본문 9.3)
#  · "CDR3 만 다양화" → CDR1/2/3 **모두 재설계**(design res_index 26..34,52..59,98..118),
#    CDR3 는 design_insertions(1..14)로 **길이까지** 가변 (본문 9.3)
#  · "CDR 외 길이가 거의 고정" 삭제 — 실측 num_design 24~44aa 로 흩어짐(본문 9.6 의 28~44 는 상위 5개)
#  · 실전 규모 "1k+" → 본문 9.6 의 **2,000~10,000**
#  · 컬럼 하드코딩 인덱싱(df[[...]]) → 전부 `cols_in(df, ...)` (학습자 my_run/ 에서 KeyError 나던 것)
#  · `## 1)` 중복 해소 — design_cells(sec=1) 명시 + 이후 2)~8) 연속 번호
#
# [채운 커버리지 — 08 과의 비대칭 해소]
#  · liability 셀 전체 신설(08 과 동일 구조) — 본문 9.4 의 4대 지표 중 하나, 9.7 실험 후보 3축의 한 축
#  · Cys 검증(사슬당 보존 Cys 2개) — nanobody-anything = antibody-anything 동일 설정(Cys 금지)
#  · C말단 framework 검증 `…WGQGTQVTVSS` 추가(기존엔 N말단 10-mer startswith 만)
#  · steps.yaml 을 읽어 실제 스텝 출력(레퍼런스는 design→inverse_folding→folding→analysis→filtering 5스텝)
#  · 본문 9.4 "흔한 오해" — CDR3 길이·Framework Identity·Humanness Score 는 출력 컬럼이 아님.
#    num_design 을 CDR3 길이로 오독하지 말라는 경고 + CDR3 를 서열에서 직접 세는 코드
#  · 실험 후보 3축(ipTM 높음 + liability_score 낮음 + RMSD 낮음) 교집합 — 본문 9.7
#
# [본문 9.5 심화 관련 처리]
#  · 노트북은 서열에서 직접 N말단 15-mer 를 비교해 **실측만** 출력(본문을 반박하는 문구 없음).
#    실측: rank2 = EVQLVESGGG**V**VQPG(L11V), rank4 = EVQLVESGGGLVQ**A**G(P14A), 나머지 8개는 완전 일치.
#
# [데이터로 재확인한 수치] data/nanobody/final_designs_metrics_10.csv (10행 203열), steps.yaml(5스텝)
#  · num_design 24~44 (상위 5개는 28~44), 사슬 길이 120~134aa, 전 디자인 Cys 2개
#  · 서열에서 센 CDR3 길이 12~21aa — num_design 과 명백히 다른 수
#  · C말단 11-mer: WGQGTQVTVSS 3개 / WGQGTLVTVSS 6개 / WGRGTQVTVSS 1개 (전부 …VTVSS 로 끝남)
#  · liability_score 150(rank4) ~ 205(rank6), rank1=175. 3축 상위 3개 교집합 = 없음(소표본)
#  · liability_*_count 8종은 전부 0 — 실제 검출은 liability_violations_summary 문자열
# ─────────────────────────────────────────────────────────────────────────────

# ── 09 나노바디 ─────────────────────────────────────────────────────────────
c = [title_cell("09", "09_nanobody", "나노바디(VHH) 실습", "09_nanobody.md", gpu="design")]
c += boot("09_nanobody", pip="pandas matplotlib")
c += design_cells("example/nanobody_against_penguinpox/penguinpox.yaml", "nanobody-anything", 8, 4,
                  "레퍼런스 결과는 num_designs=30", sec=1)
c += [
md("""## 2) 무엇이 실제로 돌았나 — `steps.yaml` (본문 9.2)

`nanobody-anything` 은 `antibody-anything` 과 **내부 설정이 같아요** — inverse folding 에서 Cys 자동 금지,
design_folding 생략. Ch.08 에서 본 규칙이 사슬 하나짜리 VHH 에도 그대로 걸립니다.

레퍼런스를 만든 명령은 이거예요. 타깃은 penguinpox 단백질(`9bkq` B 체인)이고 복합체는 317~340 토큰이에요.

```bash
boltzgen run example/nanobody_against_penguinpox/penguinpox.yaml --output workbench/nanobody \\
  --protocol nanobody-anything --num_designs 30 --budget 10
```"""),
co('''steps_file = find_one("steps.yaml", "data/nanobody")
names = [ln.split(":", 1)[1].strip()
         for ln in steps_file.read_text().splitlines()
         if ln.strip().startswith("- name:")]

print("이 출력 폴더에서 실행된 스텝", len(names), "개")
for i, n in enumerate(names, 1):
    print(f"  {i}. {n}")
print()
print("design_folding 포함 —", "예" if "design_folding" in names else "아니오 (nanobody-anything 은 이 스텝을 생략)")
print("이 목록은 '이 출력 폴더에서 실제로 돈 스텝'이에요 — 앞 스텝 산출물을 재사용해 이어 돌리면 그만큼만 남습니다.")'''),
md("""## 3) 결과 표 — 무엇을 보나 (본문 9.4)

나노바디도 항체와 같은 메트릭군을 봐요 — `design_to_target_iptm`(타깃 결합, 순위를 좌우),
`design_ptm`·`filter_rmsd`(구조·자기일관성), `num_design`(재설계 CDR 영역 길이), `liability_*`(개발성)."""),
co('''from boltzgen_viz import load_metrics, metrics_overview
import pandas as pd

CSV = str(find_one("final_designs_metrics_*.csv", "data/nanobody"))
df = pd.read_csv(CSV).sort_values("final_rank").reset_index(drop=True)
print("디자인", len(df), "개 | 전체 컬럼", df.shape[1], "종")
df[cols_in(df, "final_rank", "id", "design_ptm", "design_to_target_iptm",
           "filter_rmsd", "plip_hbonds_refolded", "num_design", "liability_score")]'''),
md("""## 4) 메트릭 그래프 — 순위와 함께 보기 (본문 9.6)

네 번째 패널은 순위별 인터페이스 H-bond 개수예요 — 결합면이 실제로 몇 개의 수소결합으로 잡혔는지
pTM·ipTM·RMSD 바와 나란히 봅니다."""),
co('''rows = load_metrics(CSV)
FIG = my_fig("09_nanobody_metrics.png")
metrics_overview(rows, "Nanobody (Penguinpox) — Design Metrics Overview", FIG, panel4="hbonds")
from IPython.display import Image; Image(FIG)'''),
md("""## 5) 어디를 재설계했나 — scaffold 5종과 `num_design` (본문 9.3·9.4)

레퍼런스에서는 rank 1 이 ipTM 0.252·RMSD 1.43Å 로 유일하게 두 축을 함께 만족했어요. 그 차이가 어디서 나왔는지
보려면 **무엇을 열어 뒀는지**부터 알아야 해요.

penguinpox 예제는 나노바디 scaffold **5종**을 함께 줍니다 — `7eow`(caplacizumab)·`7xl0`(vobarilizumab)·
`gontivimab`·`isecarosmab`·`sonelokimab`. 각 YAML 은 CDR1·CDR2·CDR3 를 **모두** `design` 으로 열고,
CDR3 는 `design_insertions` 로 길이까지 가변으로 둬요.

```yaml
# 7eow.yaml (caplacizumab, 요약)
design:            [ { chain: { id: B, res_index: 26..34,52..59,98..118 } } ]        # CDR1·CDR2·CDR3 모두 재설계
design_insertions: [ { insertion: { id: B, res_index: 98, num_residues: 1..14 } } ]  # CDR3 길이 가변
structure_groups:  # 골격은 visibility 2 로 유지, CDR 구간만 visibility 0 으로 자유
```

그래서 `num_design` 은 **CDR1+CDR2+CDR3 를 합친 재설계 구간 길이**예요.
흔한 오해가 여기서 나와요 — "CDR3 길이"는 BoltzGen 출력 컬럼이 **아니고**(Framework Identity·Humanness Score 도
마찬가지), CDR3 는 서열에서 직접 세야 해요(본문 9.4). 보존 Cys 다음부터 J-region(`WG?G…`) 직전까지가 CDR3 입니다."""),
co('''def j_region_start(s, window=25):
    """VHH J-region(WG?GT…) 시작 위치 — 못 찾으면 -1."""
    base = max(len(s) - window, 0)
    tail, hit = s[base:], -1
    for i in range(len(tail) - 3):
        if tail[i] == "W" and tail[i + 1] == "G" and tail[i + 3] == "G":
            hit = base + i
    return hit

def cdr3_of(s):
    """보존 Cys 3잔기 뒤 ~ J-region 직전 = CDR3 (Kabat 관례 근사)."""
    cys = [i for i, a in enumerate(s) if a == "C"]
    j = j_region_start(s)
    return s[cys[-1] + 3: j] if len(cys) >= 2 and j > 0 else ""

SEQ = (cols_in(df, "designed_chain_sequence", "sequence") or [None])[0]
has_nd = "num_design" in df.columns

lens = []
for _, r in df.iterrows():
    s = str(r[SEQ])
    cdr3 = cdr3_of(s)
    lens.append(len(cdr3))
    nd = f"num_design={int(r['num_design']):3d} | " if has_nd else ""
    print(f"rank{int(r['final_rank'])} {r['id']:14s} len={len(s):4d} | {nd}"
          f"CDR3={len(cdr3):2d}aa {cdr3}")

print()
if has_nd:
    print("num_design 범위", int(df["num_design"].min()), "~", int(df["num_design"].max()),
          "aa (CDR1+CDR2+CDR3 합계)")
print("서열에서 센 CDR3 길이 범위", min(lens), "~", max(lens), "aa")
print("→ 두 수가 다르면 정상이에요. num_design 을 CDR3 길이로 읽으면 안 됩니다 (본문 9.4).")'''),
md("""## 6) Developability — liability (본문 9.4)

CDR 이 얼마나 다양해졌는지 봤으니, 이제 그 서열이 **시약·약으로 버티는가**를 봐요. 나노바디도 산화·절단·응집 위험이
낮아야 대장균 발현부터 보관까지 문제가 없어요. 종합 지표 `liability_score` 는 **낮을수록** 개발하기 쉬운 후보고요.

모티프별 검출 내역은 `liability_*_count` 가 아니라 `liability_violations_summary` 문자열에 들어 있어요
(`ProtTrypx10(pos…); MetOx(pos…,sev5); …` 형태)."""),
co('''import collections

score_cols = cols_in(df, "final_rank", "id", "liability_score", "liability_num_violations",
                     "liability_high_severity_violations", "liability_medium_severity_violations")
tbl = df[score_cols]
if "liability_score" in tbl.columns:
    tbl = tbl.sort_values("liability_score")
print("liability_score 낮은 순 (낮을수록 개발성 우수)")
print(tbl.to_string(index=False))

if "liability_violations_summary" in df.columns:
    tot = collections.Counter()
    for summary in df["liability_violations_summary"].astype(str):
        for item in summary.split(";"):
            head = item.strip().split("(", 1)[0]
            if not head:
                continue
            name, mult = head, 1
            if "x" in head:
                stem, _, tail = head.rpartition("x")
                if tail.isdigit():
                    name, mult = stem, int(tail)
            tot[name] += mult
    print()
    print("최종셋 전체에서 검출된 위험 모티프 (합계)")
    for name, n in tot.most_common():
        print(f"  {name:12s} {n}")

print()
print("→ ipTM 1위가 liability 1위는 아니에요. 두 순위가 어긋나는 지점이 8) 절의 선별 문제로 이어집니다.")'''),
md("""## 7) Framework 보존 — N말단·C말단 양쪽 (본문 9.5)

개발성까지 봤으니 마지막 확인은 "CDR 만 바뀐 게 맞나"예요. VHH framework 는 매우 보존적이라
앞은 `EVQLVESGGGLVQPG…` 로 시작하고 뒤는 `…WGQGTQVTVSS` 로 끝나요(본문 9.5).
앞만 보면 뒤쪽 J-region 이 무너진 디자인을 놓치니 두 끝을 모두 봅니다.

그리고 `nanobody-anything` 은 Cys 를 자동 금지하니, 사슬에 남는 Cys 는 framework 의 **보존 이황화쌍 2개**뿐이어야 해요."""),
co('''FW_N, FW_C = "EVQLVESGGGLVQPG", "WGQGTQVTVSS"

def diffs(seg, ref):
    """기준 모티프와 다른 자리를 '기준자리번호실제' 로."""
    return [f"{ref[i]}{i + 1}{seg[i]}" for i in range(min(len(seg), len(ref))) if seg[i] != ref[i]]

n_exact = c_exact = j_ok = cys_ok = 0
for _, r in df.iterrows():
    s = str(r[SEQ])
    head, tail = s[:len(FW_N)], s[-len(FW_C):]
    dn, dc = diffs(head, FW_N), diffs(tail, FW_C)
    n_exact += not dn
    c_exact += not dc
    j_ok += tail[:2] == "WG" and tail[3] == "G" and s.endswith("VTVSS")   # J-region 골격
    cys_ok += s.count("C") == 2
    print(f"rank{int(r['final_rank'])} {r['id']:14s} Cys={s.count('C')} "
          f"| N {head} {'일치' if not dn else '치환 ' + ','.join(dn)} "
          f"| C {tail} {'일치' if not dc else '치환 ' + ','.join(dc)}")

n = len(df)
print()
print(f"N말단 {FW_N} 완전 일치 {n_exact}/{n} · C말단 {FW_C} 완전 일치 {c_exact}/{n}")
print(f"J-region 골격(WG?GT…VTVSS) 유지 {j_ok}/{n} · 보존 Cys 2개 {cys_ok}/{n}")
print("→ J-region 골격이 살아 있고 Cys 가 2개면 CDR 만 바뀐 정상 그래프팅이에요 (자리 한두 개 치환은 같은 계열).")
print("  두 끝이 통째로 무너졌으면 scaffold YAML 의 not_design 범위를 넓혀 더 고정하세요 (본문 9.5).")'''),
md("""## 8) 어떤 후보를 실험으로 보낼까 (본문 9.6·9.7)

나노바디는 대장균 발현·His-tag 정제가 쉬워서 후보를 실험으로 빨리 넘길 수 있어요(본문 9.7).
그래서 선별이 곧 실험 비용이에요 — **ipTM 최고(결합) + liability_score 낮음(개발성) + RMSD 낮음(구조)**,
세 축 상위 3개의 교집합을 봅니다."""),
co('''axes = [("결합  ipTM 높음", "design_to_target_iptm", False),
        ("구조  RMSD 낮음", "filter_rmsd", True),
        ("개발성 liability_score 낮음", "liability_score", True)]

picks = []
for label, col, asc in axes:
    if col not in df.columns:
        continue
    top3 = df.sort_values(col, ascending=asc).head(3)
    picks.append(set(top3["id"]))
    shown = ", ".join(f"{i}({v:.3f})" if isinstance(v, float) else f"{i}({v})"
                      for i, v in zip(top3["id"], top3[col]))
    print(f"{label:26s} {shown}")

both = set.intersection(*picks) if picks else set()
print()
if both:
    print("세 축을 모두 만족하는 후보 —", ", ".join(sorted(both)))
    print("→ 이 후보부터 대장균 발현·SPR/BLI 로 검증하세요.")
else:
    print("세 축을 모두 만족하는 후보 없음 — 세 조건이 한 디자인으로 모이지 않았어요.")
    print("→ 표본을 키워 꼬리를 더 뽑아야 합니다 (본문 9.6).")'''),
md("""### 이 챕터에서 확인한 것 (본문 9.6)

- `nanobody-anything` 은 `antibody-anything` 과 같은 설정이고, `steps.yaml` 에 design_folding 이 없어요.
- scaffold 5종이 CDR1·CDR2·CDR3 를 모두 열어 두고 CDR3 는 길이까지 바꿔요. `num_design` 은 그 합계지
  CDR3 길이가 아니에요 — CDR3 는 서열에서 직접 셌어요.
- framework 는 N·C 양 끝이 기준 모티프와 거의 같고 Cys 는 2개뿐 — 정상 그래프팅이에요.
- ipTM 이 0.2 대에 머물고 RMSD 가 큰 디자인이 섞여 있는 건 실패가 아니라 **소표본(num_designs=30)** 탓이에요.
  penguinpox 는 어려운 타깃이라 실전이라면 `num_designs` 를 **2,000~10,000** 으로 올려야 ipTM 0.5+ 후보가
  꼬리에서 나와요(본문 9.6).

다음 Ch.10 은 상대가 단백질이 아니라 **소분자**일 때 파이프라인이 어떻게 달라지는지 봐요."""),
]
cells_all[("09_nanobody", "09_nanobody_lab.ipynb", "09 Nanobody Lab")] = c


# ── 10 소분자·친화도 (신규) ─────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────
# ch10.py — gen_notebooks.py 의 10_small_molecule 블록 교체본
#
# 변경 요약
#  [사실 오류 정정]
#   · "포켓이 잘 감싸면 ΔSASA 가 크고 RMSD 가 작다" 삭제 — 데이터가 반증
#     (레퍼런스 rank2 ΔSASA 361.7/RMSD 0.79 vs rank1 345.1/RMSD 1.76).
#     ΔSASA·H-bond(포켓 묻힘)와 RMSD(자기일관성)를 서로 다른 축으로 분리해 각각 판정.
#   · 실행 명령 규모를 로드하는 레퍼런스와 일치시킴 — 본문 10.3 의 `--num_designs 30 --budget 10`.
#     프로덕션 `--num_designs 3000 --budget 40` 은 별도 줄로 구분.
#   · 상위 후보 추천의 범위를 명시 — "최종 10개 전체 기준"(본문 10.6 표는 상위 5개 기준).
#   · ipTM/RMSD/affinity 범위를 최종 10개 실측으로 재계산
#     (ipTM 0.723~0.841, RMSD 0.574~1.764Å, affinity_pred_value 1.09~2.71,
#      ΔSASA 252.2~361.7Å², H-bond 1~9).
#  [커버리지 보강]
#   · 본문 10.2 `ccd:` vs `smiles:` 입력 2방식 — 결과 CIF 의 HETATM 으로 리간드 코드·원자 수 확인.
#   · 본문 10.3 리간드 토큰화 — num_prot_tokens + num_lig_atoms = num_tokens 를 CSV 로 실증
#     (실측 140~160 + 16 = 156~176, 10/10 성립).
#   · 본문 10.3 주의 — affinity 컬럼은 protein-small_molecule 프로토콜에서만.
#     산출물 steps.yaml 을 읽어 7스텝·affinity 포함을 출력으로 확인.
#   · 본문 10.5 보조 컬럼 affinity_probability_binary1/2·affinity_pred_value1/2 와
#     랭킹에 실제로 쓰이는 rank_affinity_probability_binary1 추가.
#   · 본문 10.4 plip_saltbridge_refolded 를 포켓 지표에 포함.
#  [구조 결함 수정]
#   · design_cells(sec=1) 명시 → `## 1)` 중복 제거, 절 번호 0~8 연속.
#   · 모든 DataFrame 컬럼 선택을 cols_in(df, ...) 로 — affinity 6종 부재 시에도 안 끊김.
#   · 모든 마크다운 제목에 실재 앵커 (본문 10.2~10.7) 부여(기존 "(본문 10)" 제거).
#  [군더더기 축소]
#   · 죽은 코드 df["_pocket"] 삭제.
#   · 셀마다 반복되던 프로토콜 재설명 제거, 각 절은 앞 출력을 받아 다음을 여는 구성으로.
# ─────────────────────────────────────────────────────────────────────────────

c = [title_cell("10", "10_small_molecule", "소분자 결합 + 친화도 예측 실습", "10_small_molecule.md", gpu="design")]
c += boot("10_small_molecule", pip="pandas matplotlib")
c += design_cells("example/protein_binding_small_molecule/chorismite.yaml", "protein-small_molecule", 8, 4,
                  "레퍼런스 결과는 num_designs=30", sec=1)
c += [
md("""## 2) 리간드를 어떻게 적어 넣나 — CCD vs SMILES (본문 10.2)

방금 돌린 명세에서 타깃 자리를 차지한 건 `ligand` 한 줄이에요. 소분자는 두 가지로 적습니다.

```yaml
# 방법 1 — CCD 코드(PDB 화학성분 사전). 결정구조에 이미 등장한 분자
- ligand: { id: B, ccd: TSA }

# 방법 2 — SMILES. 표준 코드가 없는 신약 후보 등
- ligand: { id: B, smiles: "C1CNC[C@@H]1OC2=C(...)..." }
```

`chorismite.yaml` 은 첫 번째 방식이고 `TSA` 는 chorismate 전이상태 유사체예요. RCSB 에서 코드가 검색되면 `ccd`, 안 나오면 `smiles` 나 `.sdf` 로 넣습니다. 무엇이 실제로 들어갔는지는 결과 구조 파일이 알려줘요."""),
co('''cif = find_one("final*designs/*.cif", "data/small_molecule")
het = [l.split() for l in pathlib.Path(cif).read_text().splitlines() if l.startswith("HETATM")]
codes = sorted({f[5] for f in het})
print("결과 구조에 들어 있는 비폴리머 코드", codes)
for code in codes:
    names = [f[3] for f in het if f[5] == code]
    print(f"  {code} — 원자 {len(names)}개 | {' '.join(names)}")'''),
md("""리간드는 **수소를 뺀 heavy atom 목록**으로 들어가요. TSA 는 16개고, 이 16이 바로 다음 절의 토큰 계산에 그대로 나타납니다."""),

md("""## 3) `protein-small_molecule` — affinity 스텝이 붙은 프로토콜 (본문 10.3)

리간드가 정해졌으면 프로토콜을 고를 차례예요. 소분자 전용 프로토콜에는 다른 프로토콜에 없는 **affinity 스텝**이 하나 더 있어요.

```bash
# 아래 분석이 쓰는 레퍼런스를 만든 명령
boltzgen run example/protein_binding_small_molecule/chorismite.yaml --output workbench/sm \\
  --protocol protein-small_molecule --num_designs 30 --budget 10

# 프로덕션 규모 — 소분자는 결합면이 좁아 후보를 크게 잡습니다(수 시간~수십 시간)
boltzgen run example/protein_binding_small_molecule/chorismite.yaml --output workbench/sm \\
  --protocol protein-small_molecule --num_designs 3000 --budget 40
```

디자인당 affinity 예측에만 ~17초가 더 붙어요. 그리고 **친화도 예측은 이 프로토콜에서만** 나옵니다 — 다른 프로토콜로 돌리면 `affinity_*` 컬럼이 아예 생기지 않아요. 스텝 구성은 산출물의 `steps.yaml` 에 그대로 남습니다."""),
co('''steps_txt = pathlib.Path(find_one("steps.yaml", "data/small_molecule")).read_text()
step_names = [l.split("name:")[1].strip() for l in steps_txt.splitlines() if "name:" in l]
print(f"스텝 {len(step_names)}개 —", " → ".join(step_names))
print("affinity 스텝 있음 — 아래 7절의 친화도 분석이 그대로 이어집니다." if "affinity" in step_names
      else "affinity 스텝 없음 — 이 산출물에는 affinity_* 컬럼이 없어 7절을 건너뛰게 됩니다.")'''),

md("""## 4) 복합체 토큰 세기 — 폴리머는 잔기, 소분자는 원자 (본문 10.3)

7스텝이 확인됐으니 이제 이 복합체가 모델에 얼마나 큰 입력인지 봅니다. BoltzGen 이 세는 단위는 **토큰**이에요. 폴리머는 **잔기당 1토큰**, 소분자는 **원자당 1토큰**이라 `num_prot_tokens + num_lig_atoms = num_tokens` 가 딱 맞아떨어져야 해요."""),
co('''from boltzgen_viz import load_metrics, metrics_overview
import pandas as pd
CSV = str(find_one("final_designs_metrics_*.csv", "data/small_molecule"))
df = pd.read_csv(CSV).sort_values("final_rank")

tok = cols_in(df, "final_rank", "id", "num_prot_tokens", "num_lig_atoms", "num_tokens")
display(df[tok])
if {"num_prot_tokens", "num_lig_atoms", "num_tokens"} <= set(df.columns):
    ok = int((df.num_prot_tokens + df.num_lig_atoms == df.num_tokens).sum())
    print(f"num_prot_tokens + num_lig_atoms = num_tokens 성립 {ok}/{len(df)}")
    print(f"단백질 {int(df.num_prot_tokens.min())}~{int(df.num_prot_tokens.max())}잔기"
          f" + 리간드 {int(df.num_lig_atoms.iloc[0])}원자"
          f" = 복합체 {int(df.num_tokens.min())}~{int(df.num_tokens.max())}토큰")'''),
md("""단백질 길이는 명세의 `sequence: 140..180` 안에서 실행마다 달라지고, 리간드 16은 고정이에요. GPU 메모리는 이 토큰 수에 좌우되니 OOM 이 나면 `sequence` 상한이나 `--num_designs` 를 줄이세요."""),

md("""## 5) 최종 선별셋 — 한 표, 한 그림 (본문 10.6)

입력이 확인됐으니 결과를 봅니다. 4번째 패널이 다른 챕터의 산점도 대신 **예측 친화도 바**로 바뀌는 게 이 프로토콜의 표식이에요."""),
co('''df[cols_in(df, "id", "final_rank", "design_ptm", "design_to_target_iptm", "filter_rmsd",
           "plip_hbonds_refolded", "delta_sasa_refolded",
           "affinity_pred_value", "affinity_probability_binary", "num_design")]'''),
co('''rows = load_metrics(CSV)
FIG = my_fig("10_small_molecule_metrics.png")
metrics_overview(rows, "Small-Molecule Binder (chorismate) — Design Metrics Overview",
                 FIG, panel4="affinity")
from IPython.display import Image; Image(FIG)'''),
md("""레퍼런스(num_designs=30) 기준으로 ipTM 0.723~0.841, RMSD 0.57~1.76Å 이 나와요. 소분자처럼 작고 조밀한 인터페이스는 ipTM 이 높게 나오는 경향이 있으니 **단백질-단백질 ipTM 과 절대값을 비교하지 마세요**(Ch.05). 같은 실행 안에서의 상대 순위로만 씁니다."""),

md("""## 6) 포켓 품질 — 얼마나 묻히고, 몇 개나 붙잡나 (본문 10.4)

ipTM·RMSD 는 "구조를 믿을 수 있나"까지만 말해줘요. 소분자가 실제로 주머니에 묻혔는지는 따로 봐야 합니다. `delta_sasa_refolded`(묻힌 표면적, Å²)·`plip_hbonds_refolded`(수소결합)·`plip_saltbridge_refolded`(염다리)가 그 지표예요."""),
co('''pk = cols_in(df, "final_rank", "id", "delta_sasa_refolded", "plip_hbonds_refolded",
             "plip_saltbridge_refolded", "filter_rmsd")
sub = df[pk].sort_values("delta_sasa_refolded", ascending=False) if "delta_sasa_refolded" in df.columns else df[pk]
print(sub.to_string(index=False))
if {"delta_sasa_refolded", "filter_rmsd"} <= set(df.columns):
    a = df.loc[df.delta_sasa_refolded.idxmax()]
    b = df.loc[df.filter_rmsd.idxmin()]
    print(f"\\nΔSASA 최대  rank{int(a.final_rank)} {a.id} — {a.delta_sasa_refolded:.1f} A^2, RMSD {a.filter_rmsd:.2f} A")
    print(f"RMSD 최저   rank{int(b.final_rank)} {b.id} — {b.delta_sasa_refolded:.1f} A^2, RMSD {b.filter_rmsd:.2f} A")'''),
md("""ΔSASA 가 가장 큰 디자인과 RMSD 가 가장 낮은 디자인은 서로 다른 후보로 나옵니다. 묻힘(ΔSASA·H-bond·염다리)은 **포켓이 소분자를 얼마나 감싸는가**, RMSD 는 **그 구조를 설계 서열이 재현하는가** — 서로 다른 축이라 하나로 다른 하나를 대신할 수 없어요.

판정은 각각 따로 하고 둘 다 만족하는 후보를 고릅니다. 레퍼런스 기준 ΔSASA 252~362Å², H-bond 1~9개, 염다리는 전부 0이라 이 포켓의 결합은 묻힘과 수소결합이 담당해요. ΔSASA 가 유독 작은 디자인은 리간드가 표면에 얹혀 있다는 뜻이니 후보에서 빼세요."""),

md("""## 7) 친화도 컬럼 6종과 랭킹 (본문 10.5)

포켓이 잘 감싼다고 결합이 센 건 아니에요. 결합 세기는 affinity 스텝이 따로 예측해 줍니다.

| 컬럼 | 의미 |
|------|------|
| `affinity_pred_value` | 예측 결합 친화도(회귀값, 클수록 강한 결합) |
| `affinity_probability_binary` | "결합한다" 이진 확률 |
| `affinity_pred_value1`, `_value2` | 보조 회귀값 |
| `affinity_probability_binary1`, `_binary2` | 보조 이진 분류 확률 |
| `rank_affinity_probability_binary1` | 최종 랭킹에 들어가는 친화도 순위 |"""),
co('''aff = cols_in(df, "final_rank", "id", "affinity_pred_value", "affinity_probability_binary",
              "affinity_pred_value1", "affinity_pred_value2",
              "affinity_probability_binary1", "affinity_probability_binary2",
              "rank_affinity_probability_binary1")
display(df[aff])
if "affinity_pred_value" in df.columns:
    k = min(3, len(df))
    print(f"최종 {len(df)}개 전체 기준 affinity_pred_value 상위 {k}")
    print(df.nlargest(k, "affinity_pred_value")[
        cols_in(df, "final_rank", "id", "affinity_pred_value", "affinity_probability_binary",
                "design_to_target_iptm", "filter_rmsd")].to_string(index=False))
if "rank_affinity_probability_binary1" in df.columns:
    t = df.nsmallest(1, "rank_affinity_probability_binary1").iloc[0]
    print(f"\\n친화도 순위 1위는 {t.id}(final_rank {int(t.final_rank)}) — 최종 순위는 여러 rank_* 의 종합이에요.")'''),
md("""친화도로 뽑은 상위와 `final_rank` 상위는 일치하지 않아요. **최종 10개 전체**를 기준으로 보면 `affinity_pred_value` 는 rank 10·9·2 가 높고(2.71/2.49/2.39), 본문 10.6 표처럼 **상위 5개 안에서만** 보면 rank 2·3(2.39/2.34)이 가장 높습니다 — 어느 범위에서 고른 추천인지 늘 같이 말해야 해요.

판정 기준. 친화도는 **절대값이 아니라 같은 실행 안의 상대 순위**로 씁니다. 구조 지표(ipTM·RMSD)와 친화도가 함께 상위인 후보를 실험 후보로 올리고, 그 후보는 AutoDock Vina 재도킹·MD 로 독립 검증하세요(Ch.06.7).

```bash
vina --receptor protein.pdbqt --ligand ligand.pdbqt --out docked.pdbqt
```"""),

md("""## 8) 이 챕터에서 확인한 것 (본문 10.6~10.7)

리간드를 `ccd`/`smiles` 로 적어 넣고(2절), affinity 스텝이 붙은 7스텝 프로토콜로 돌려(3절), 복합체가 단백질 잔기 + 리간드 원자로 토큰화되는 것을 확인했어요(4절). 결과는 구조 신뢰도(5절)·포켓 묻힘(6절)·예측 친화도(7절) **세 축을 따로** 읽고, 셋이 함께 상위인 후보만 실험으로 넘깁니다.

다음 챕터의 타깃은 단백질도 소분자도 아닌 **핵산**이에요. 리간드처럼 원자로 세지 않고 폴리머로 다루면서도, 온통 음전하인 골격 때문에 인터페이스 지표가 지금까지와 전혀 다른 값을 냅니다."""),
]
cells_all[("10_small_molecule", "10_small_molecule_lab.ipynb", "10 Small-Molecule Lab")] = c


# ── 11 핵산(DNA/RNA) ────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────
# ch11.py — gen_notebooks.py 의 11_nucleic_acid 블록 교체본
#
# 변경 요약
#  [사실 오류 정정]
#   · DNA ipTM 상한 0.67 을 경고 없이 인용하던 것을 수정. 그 상한은 RMSD 11.59/11.69Å 로
#     자기일관성이 무너진 rank 10(zinc_finger_28, ipTM 0.670)·rank 9(zinc_finger_29, 0.635)
#     에서 나옴. 본문 11.5 의 판정 원칙("순위만 보지 말고 RMSD 를 따로 확인")을 절 하나로 편성.
#     자기일관성이 확보된 상위 8개 기준 ipTM 은 0.503~0.588.
#   · RNA ipTM 범위를 실측으로 정정 — 0.293~0.451(기존 "0.29~0.45" 유지 확인),
#     H-bond 평균 DNA 30.8 / RNA 9.3 을 노트북이 직접 재계산해 출력.
#  [커버리지 보강]
#   · 본문 11.3 핵산 자동 인식 — 결과 CIF 의 _entity_poly 타입(polypeptide/polydeoxyribonucleotide/
#     polyribonucleotide)으로 자동 분류를 확인하고, 가장 단순한 사례 vanilla_protein.yaml 을 연결.
#   · 본문 11.4 고급 입력 기능 전부 — exclude·design_insertions(3~8잔기)·structure_groups
#     visibility 0·design/not_design·reset_res_index. 범위 문자열을 펼쳐 잔기 수를 계산하고
#     CSV 와 대조(실측: 200 − 33(exclude) = 167, not_design 72 고정, 재설계 95 + 삽입 3~8
#     = num_design 98~103, 단백질 170~175 = num_prot_tokens).
#   · Zn 배위 4잔기 고정을 별도 절로 — zf.cif 6개 site 24잔기(Cys 2.2~2.4Å, His 2.0~2.2Å)가
#     전부 not_design 안에 있고, 설계 서열의 Cys 가 10개 디자인 모두 정확히 12개.
#   · RNA 타깃 정체 명시 — 1URN 의 U1 snRNA 헤어핀 20 nt 단일 체인 R.
#     num_tokens − num_prot_tokens = 20 으로 실증하고 CIF 에서 서열을 직접 출력.
#  [구조 결함 수정]
#   · design_cells(sec=1) 명시 → `## 1)` 중복 제거, 절 번호 0~9 연속.
#   · 모든 DataFrame 컬럼 선택을 cols_in(df, ...) 로.
#   · 반복되던 "data/rna/final_designs_metrics_10.csv" 3회를 RNA_CSV 변수로(DNA_CSV 와 대칭).
#   · 모든 마크다운 제목에 실재 앵커 (본문 11.3~11.7) 부여(기존 "(본문 11)" 제거).
#  [군더더기 축소]
#   · 각 절이 앞 셀 출력을 받아 다음을 여는 구성으로 재배치, 판정 기준으로 마감.
# ─────────────────────────────────────────────────────────────────────────────

c = [title_cell("11", "11_nucleic_acid", "핵산(DNA/RNA) 결합 단백질 실습", "11_nucleic_acid.md", gpu="design")]
c += boot("11_nucleic_acid", pip="pandas matplotlib")
c += design_cells("example/denovo_zinc_finger_against_dna/zinc_finger.yaml", "protein-anything", 8, 4,
                  "레퍼런스 결과는 num_designs=30", sec=1)
c += [
md("""## 2) 핵산 타깃은 따로 선언하지 않는다 (본문 11.3)

방금 명령의 `--protocol` 은 `protein-anything` 이었어요. DNA 전용 프로토콜을 쓰지 않은 이유는, BoltzGen 이 CIF 의 잔기 코드(CCD)를 보고 **DNA·RNA 를 스스로 구분**하기 때문이에요. 그래서 가장 단순한 de novo DNA 바인더 명세(`denovo_zinc_finger_against_dna/vanilla_protein.yaml`)는 설계할 단백질 한 줄과 DNA 두 가닥을 `include` 하는 게 전부예요.

```yaml
entities:
  - protein: { id: G, sequence: 40..120 }   # DNA 에 붙을 새 단백질
  - file:
      path: zf.cif
      include:
        - chain: { id: C1 }   # DNA 가닥 1 — DNA 로 자동 인식
        - chain: { id: B1 }   # DNA 가닥 2
```

자동 분류의 결과는 산출물 CIF 의 `_entity_poly` 에 그대로 적혀 나와요."""),
co('''KIND = {"polypeptide(L)": "단백질", "polydeoxyribonucleotide": "DNA",
        "polyribonucleotide": "RNA"}
cif = find_one("final*designs/*.cif", "data/dna")
lines = pathlib.Path(cif).read_text().splitlines()
for l in lines:
    for key, ko in KIND.items():
        if key in l and l.split()[1] == key:
            seq = l.split()[-1]
            print(f"{ko:4s} {len(seq):4d} 잔기 | {seq[:44]}{'…' if len(seq) > 44 else ''}")
zn = [l for l in lines if l.startswith("HETATM") and l.split()[5] == "ZN"]
print(f"Zn 이온 {len(zn)}개 (비폴리머라 원자 단위로 셉니다)")'''),
md("""단백질 1사슬 + DNA 2가닥(각 36 nt) + Zn 6개가 한 복합체예요. 단백질을 뺀 타깃 쪽 토큰은 36+36+6 = 78 이고, 이 숫자는 뒤에서 CSV 의 `num_tokens − num_prot_tokens` 로 다시 만납니다."""),

md("""## 3) zinc_finger.yaml — 고급 입력 기능 총동원 (본문 11.4)

앞 절의 `vanilla_protein.yaml` 이 "빈 종이에 새로 그리기"라면, 이번에 돌린 `zinc_finger.yaml` 은 "기존 zinc finger 를 뜯어고치기"예요. BoltzGen 에서 가장 복잡한 명세 중 하나고, Ch.02 의 고급 기능이 거의 다 나옵니다.

```yaml
entities:
  - file:
      path: zf.cif
      include: "all"                    # 전체 포함 후
      exclude:                          # 불필요한 구간 제외
        - chain: { id: A1, res_index: ..10,63..69,185.. }
      design_insertions:                # finger 사이 linker 삽입
        - insertion: { id: A1, res_index: 63, num_residues: 3..8 }
      structure_groups:                 # 구조를 숨겨 자유 재설계
        - group: { visibility: 0, id: "all" }
      design:                           # 재설계할 영역
        - chain: { id: A1, res_index: 11..184 }
      not_design:                       # Zn 배위 잔기 등 고정
        - chain: { id: A1, res_index: 11..20,29,33,39..48,57,61,72..81,90,94,100..109,118,122,129..138,147,151,157..166,175,179 }
      reset_res_index:                  # 번호 정리
        - chain: { id: A1 }
```

| 기능 | 무엇을 하나 | 왜 |
|------|------------|----|
| `exclude` | N/C 말단·특정 구간 제거 | 시스템 경량화 |
| `design_insertions` | finger 사이 linker 3~8잔기 삽입 | DNA 인식에 필요한 유연성 |
| `structure_groups: visibility 0` | 구조 숨김 → 자유 재설계 | 타깃 DNA 마다 최적 구조가 다름 |
| `design` / `not_design` | 재설계 영역 vs 고정 영역 | 기능 필수 잔기 보호 |
| `reset_res_index` | 잔기 번호 연속 정리 | exclude·insertion 후 정돈 |

말로만 보면 감이 안 오니 범위 문자열을 실제로 펼쳐 세어 보고, 그 결과가 결과 CSV 의 길이와 맞는지 대조해요."""),
co('''from boltzgen_viz import load_metrics, metrics_overview, compare_bars
import pandas as pd
DNA_CSV = str(find_one("final_designs_metrics_*.csv", "data/dna"))
dna = pd.read_csv(DNA_CSV).sort_values("final_rank")

CHAIN_LEN = 200          # zf.cif 의 A1 사슬 잔기 수
def expand(spec, lo=1, hi=CHAIN_LEN):
    """'..10,63..69,185..' 같은 res_index 표기를 잔기 번호 집합으로 펼친다."""
    out = set()
    for part in spec.split(","):
        if ".." in part:
            a, b = part.split("..")
            out |= set(range(int(a) if a else lo, (int(b) if b else hi) + 1))
        else:
            out.add(int(part))
    return out

EXCLUDE    = expand("..10,63..69,185..")
DESIGN     = expand("11..184")
NOT_DESIGN = expand("11..20,29,33,39..48,57,61,72..81,90,94,100..109,118,122,"
                    "129..138,147,151,157..166,175,179")
INSERTION  = (3, 8)

kept       = set(range(1, CHAIN_LEN + 1)) - EXCLUDE
fixed      = NOT_DESIGN & kept
designable = (DESIGN & kept) - NOT_DESIGN
print(f"원본 A1 {CHAIN_LEN}잔기 → exclude {len(EXCLUDE)}잔기 제거 → 남는 사슬 {len(kept)}잔기")
print(f"그중 not_design 으로 고정 {len(fixed)}잔기, 재설계 가능 {len(designable)}잔기")
print(f"+ design_insertions {INSERTION[0]}~{INSERTION[1]}잔기")
print(f"→ 예상 num_design {len(designable) + INSERTION[0]}~{len(designable) + INSERTION[1]},"
      f" 단백질 길이 {len(kept) + INSERTION[0]}~{len(kept) + INSERTION[1]}")
if {"num_design", "num_prot_tokens", "num_tokens"} <= set(dna.columns):
    print(f"\\nCSV 실측 num_design {int(dna.num_design.min())}~{int(dna.num_design.max())},"
          f" num_prot_tokens {int(dna.num_prot_tokens.min())}~{int(dna.num_prot_tokens.max())}")
    print("고정 잔기 수(num_prot_tokens − num_design)",
          sorted((dna.num_prot_tokens - dna.num_design).unique()))
    print("타깃 토큰 수(num_tokens − num_prot_tokens)",
          sorted((dna.num_tokens - dna.num_prot_tokens).unique()))'''),
md("""명세에서 계산한 숫자와 결과 CSV 가 그대로 맞아요. 길이가 실행마다 달라지는 건 `design_insertions` 의 3~8잔기 때문이고, 모든 디자인에서 고정 잔기 수가 72로 일정한 게 `not_design` 이 작동했다는 증거예요.

여기서 안 맞는다면 `exclude`/`design`/`not_design` 범위가 겹치거나 빠진 것이니 명세부터 다시 보세요."""),

md("""## 4) Zn 배위 잔기가 정말 지켜졌나 (본문 11.4)

72잔기를 왜 고정했는지가 이 챕터의 핵심이에요. zinc finger 는 `Cys-X2-Cys-X12-His-X3-His` 로 Zn²⁺ 을 붙잡는데, **이 4잔기 중 하나만 바뀌어도 Zn 이 안 붙고 finger 가 무너져요.** `zf.cif` 에는 이런 site 가 6벌 있고(2.0~2.4Å 배위), 그 24잔기가 전부 `not_design` 안에 들어 있는지 확인합니다."""),
co('''ZN_SITES = [(13, 16, 29, 33), (41, 44, 57, 61), (74, 77, 90, 94),
            (102, 105, 118, 122), (131, 134, 147, 151), (159, 162, 175, 179)]
for i, site in enumerate(ZN_SITES, 1):
    inside = all(r in NOT_DESIGN for r in site)
    print(f"finger {i} — Cys{site[0]},Cys{site[1]} His{site[2]},His{site[3]}"
          f" | not_design 고정 {inside}")
print(f"\\nZn 배위 잔기 {sum(len(s) for s in ZN_SITES)}개 중 고정된 것",
      sum(1 for s in ZN_SITES for r in s if r in NOT_DESIGN))

if "designed_chain_sequence" in dna.columns:
    print("\\n설계 서열의 Cys 개수 (6 finger x 2 = 12 이면 그대로 보존)")
    for _, r in dna.head(5).iterrows():
        s = str(r["designed_chain_sequence"])
        print(f"  rank{int(r['final_rank'])} {r['id']:15s} len={len(s):4d} Cys={s.count('C'):3d}"
              f" His={s.count('H'):3d}")'''),
md("""Cys 가 정확히 12개면 배위 잔기가 보존되고 새 Cys 도 안 섞인 정상 상태예요. 12보다 적으면 `not_design` 범위가 잘못된 것이고, 많으면 재설계 영역에서 자유 Cys 가 생긴 것이니 후보에서 빼거나 범위를 넓혀 다시 돌리세요. His 는 배위 12개에 재설계 영역에서 더 생길 수 있어 12개 이상이 정상이에요.

효소의 catalytic triad, 이황화 Cys, 금속 결합 부위처럼 **기능에 필수인 잔기**는 어느 타깃에서든 이렇게 고정합니다."""),

md("""## 5) DNA 결합 결과 — H-bond 가 자릿수부터 다르다 (본문 11.5)

명세가 의도대로 지켜졌으니 이제 성능을 봅니다. DNA 결합에서 가장 먼저 눈에 띄는 건 인터페이스 수소결합 개수예요."""),
co('''dna[cols_in(dna, "id", "final_rank", "design_ptm", "design_to_target_iptm", "filter_rmsd",
             "plip_hbonds_refolded", "num_design")]'''),
co('''rows = load_metrics(DNA_CSV)
FIG = my_fig("11_dna_metrics.png")
metrics_overview(rows, "DNA-binding (Zinc Finger) — Design Metrics Overview", FIG)
from IPython.display import Image; Image(FIG)'''),
md("""레퍼런스(num_designs=30) 기준 H-bond 는 20~42개, 평균 30.8개예요. 단백질-단백질 결합이 보통 한 자릿수인 것과 비교하면 차원이 다르죠 — 인산 골격의 음전하를 Arg/Lys 가 줄줄이 따라가며 붙잡기 때문이에요(본문 11.2). pTM 0.50~0.60 으로 다소 낮은 건 zinc finger 가 작고 복잡한 도메인이라 그래요."""),

md("""## 6) ipTM 상한만 보면 안 되는 이유 (본문 11.5)

레퍼런스 그래프에서 ipTM 막대는 최고 0.67 까지 올라가요. 나노바디(Ch.09)나 항체(Ch.08)보다 높아서 "DNA 는 붙이기 쉽구나" 하고 넘어가기 쉬운데, **그 상한이 어느 디자인에서 나왔는지**를 반드시 같이 봐야 합니다."""),
co('''chk = cols_in(dna, "final_rank", "id", "design_to_target_iptm", "filter_rmsd",
              "plip_hbonds_refolded")
sub = dna[chk].sort_values("design_to_target_iptm", ascending=False) if "design_to_target_iptm" in dna.columns else dna[chk]
print(sub.to_string(index=False))
if {"design_to_target_iptm", "filter_rmsd"} <= set(dna.columns):
    good = dna[dna.filter_rmsd < 3.0]
    bad  = dna[dna.filter_rmsd >= 3.0]
    print(f"\\nRMSD 3A 미만 {len(good)}개 — ipTM {good.design_to_target_iptm.min():.3f}"
          f"~{good.design_to_target_iptm.max():.3f}, RMSD {good.filter_rmsd.min():.2f}"
          f"~{good.filter_rmsd.max():.2f}A")
    if len(bad):
        print(f"RMSD 3A 이상 {len(bad)}개 — ipTM {bad.design_to_target_iptm.min():.3f}"
              f"~{bad.design_to_target_iptm.max():.3f}, RMSD {bad.filter_rmsd.min():.2f}"
              f"~{bad.filter_rmsd.max():.2f}A")
        print("  " + ", ".join(f"rank{int(r.final_rank)} {r.id}" for _, r in bad.iterrows()))'''),
md("""레퍼런스에서 ipTM 최고 0.670·0.635 는 rank 10(`zinc_finger_28`)·rank 9(`zinc_finger_29`)의 값이고, 이 둘은 RMSD 가 11.6Å 대로 **자기일관성이 무너진** 디자인이에요. RMSD 필터를 통과하지 못했는데도 다른 지표가 좋아 최종 10위 안에 올라온 사례죠. 자기일관성이 확보된 상위 8개만 보면 ipTM 은 0.503~0.588 이에요.

판정 기준. **최종 선별셋에 들었다는 것이 모든 지표가 좋다는 뜻은 아니에요.** 실험 후보를 고를 땐 순위만 보지 말고 RMSD 같은 자기일관성 지표를 따로 확인하고, RMSD 가 큰 디자인은 ipTM 이 아무리 높아도 제외하세요."""),

md("""## 7) RNA 타깃 — 1URN 의 U1 snRNA 헤어핀 (본문 11.6)

DNA 를 했으니 RNA 로 넘어가요. 방법은 완전히 동일해요 — RNA 가 든 CIF 를 `include` 하면 2절에서 본 자동 인식이 그대로 작동합니다. 다만 이번엔 구조를 숨기지 않고(`structure_groups: "all"`) 타깃 구조를 그대로 보여줘요.

```yaml
entities:
  - protein: { id: P, sequence: 60..120 }   # RNA 에 붙을 단백질
  - file:
      path: rna_target.cif
      include:
        - chain: { id: R }    # RNA 가닥 — RNA 로 자동 인식
      structure_groups: "all"
```

커밋된 `data/rna` 는 **1URN 의 U1 snRNA 헤어핀(20 nt)** 을 RNA 만 깨끗이 추출해 단일 체인 R 로 만든 타깃에 `protein-anything`, num_designs 30, budget 10 으로 돌린 결과예요. 이 절부터는 여러분의 `my_run/`(DNA) 대신 이 레퍼런스를 씁니다."""),
co('''RNA_CSV = "data/rna/final_designs_metrics_10.csv"
rna = pd.read_csv(RNA_CSV).sort_values("final_rank")

rna_cif = sorted(pathlib.Path("data/rna/final_designs").glob("*.cif"))
if rna_cif:
    for l in pathlib.Path(rna_cif[0]).read_text().splitlines():
        if "polyribonucleotide" in l and l.split()[1] == "polyribonucleotide":
            seq = l.split()[-1]
            print(f"타깃 RNA {len(seq)} nt | {seq}")
if {"num_tokens", "num_prot_tokens", "num_resolved_tokens"} <= set(rna.columns):
    print("타깃 토큰 수(num_tokens − num_prot_tokens)",
          sorted((rna.num_tokens - rna.num_prot_tokens).unique()))
    print("좌표가 풀리지 않은 토큰(num_tokens − num_resolved_tokens)",
          sorted((rna.num_tokens - rna.num_resolved_tokens).unique()))
display(rna[cols_in(rna, "id", "final_rank", "design_ptm", "design_to_target_iptm",
                    "filter_rmsd", "plip_hbonds_refolded", "num_design")])'''),
co('''rows = load_metrics(RNA_CSV)
FIG = my_fig("11_rna_metrics.png")
metrics_overview(rows, "RNA-binding (U1 snRNA hairpin) — Design Metrics Overview", FIG)
from IPython.display import Image; Image(FIG)'''),
md("""타깃 토큰이 20으로 일정해 헤어핀 20 nt 단일 가닥이 그대로 들어간 걸 확인할 수 있어요(그중 3개는 좌표가 풀리지 않아 결과 구조에는 17 nt 만 그려져요). ipTM 0.293~0.451, pTM 0.441~0.652, RMSD 2.16~2.47Å 로 RMSD 는 10개 모두 양호해요 — 6절 같은 자기일관성 붕괴는 없습니다."""),

md("""## 8) DNA vs RNA — 같은 방법, 다른 인터페이스 (본문 11.6)

두 실행을 나란히 놓으면 타깃의 물리적 차이가 인터페이스 지표로 드러나요."""),
co('''dna_rows = load_metrics(DNA_CSV)
rna_rows = load_metrics(RNA_CSV)
FIG = my_fig("11_dna_rna_hbonds.png")
compare_bars({"DNA (zinc finger)": dna_rows, "RNA (hairpin)": rna_rows},
             "plip_hbonds_refolded", "DNA vs RNA — mean interface H-bonds",
             "mean H-bond count", FIG)
for tag, d in (("DNA", dna), ("RNA", rna)):
    if {"plip_hbonds_refolded", "design_to_target_iptm"} <= set(d.columns):
        print(f"{tag} — H-bond 평균 {d.plip_hbonds_refolded.mean():.1f}"
              f" (범위 {int(d.plip_hbonds_refolded.min())}~{int(d.plip_hbonds_refolded.max())})"
              f" | ipTM {d.design_to_target_iptm.min():.3f}~{d.design_to_target_iptm.max():.3f}")
    if {"ARG_fraction", "LYS_fraction"} <= set(d.columns):
        print(f"     양전하 잔기 비율(Arg+Lys) 평균 {(d.ARG_fraction + d.LYS_fraction).mean():.3f}")
from IPython.display import Image; Image(FIG)'''),
md("""H-bond 평균은 DNA 30.8 대 RNA 9.3 이에요. 둘 다 인산 골격이 음전하지만 타깃이 36+36 nt 이중나선이냐 20 nt 단일가닥 헤어핀이냐에 따라 접촉면이 이만큼 차이나요. 설계 서열의 Arg+Lys 비율도 DNA 쪽이 훨씬 높게 나오는데, 음전하 골격을 따라가는 정전기 결합이 실제로 서열에 반영됐다는 뜻이에요.

다만 H-bond 수가 곧 결합 품질은 아니에요. DNA 결합에서 진짜 중요한 건 **염기 서열 특이성**이고, 이건 총 개수보다 인터페이스의 기하·위치에 달려 있어요. H-bond 가 많은 후보 중 결합부위가 의도한 염기에 놓이는지를 PyMOL 로 확인하고, 비슷한 서열에 오프타깃으로 붙지 않는지 비교하세요."""),

md("""## 9) 이 챕터에서 확인한 것 (본문 11.7)

핵산 타깃은 CIF 에 있으면 자동 인식되어 별도 프로토콜이 필요 없고(2절), 대신 **명세로 무엇을 고정할지**가 설계의 승부처였어요. `exclude`·`design_insertions`·`visibility 0`·`design`/`not_design`·`reset_res_index` 로 재설계 범위를 짜고(3절), Zn 배위 24잔기를 고정해 finger 가 무너지지 않게 했죠(4절). 결과는 DNA 가 H-bond·ipTM 모두 높지만 순위 상단에 자기일관성이 깨진 디자인이 섞일 수 있고(6절), RNA 는 접촉면이 작아 지표가 전반적으로 낮게 나왔어요(7·8절).

이걸로 Part B 의 타깃별 실습을 모두 마쳤어요. 단백질·펩타이드·항체·나노바디·소분자·핵산 어느 타깃이든 **명세로 제약을 걸고 → 실행하고 → 여러 지표를 따로 확인해 후보를 고르는** 흐름은 같습니다. 이제 여러분의 타깃으로 같은 흐름을 돌려보세요."""),
]
cells_all[("11_nucleic_acid", "11_nucleic_lab.ipynb", "11 Nucleic Acid Lab")] = c


# ── 저장 ────────────────────────────────────────────────────────────────────
for (folder, name, title), cells in cells_all.items():
    save(cells, folder, name, title)

print("\n노트북", len(cells_all), "종 생성 완료 (각 챕터 폴더, Colab/로컬 공용).")
