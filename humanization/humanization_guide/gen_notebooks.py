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



# ── Colab 배지 ────────────────────────────────────────────────────────────────
# GitHub 에서 노트북을 열면 이 배지를 눌러 바로 Colab 으로 넘어갈 수 있다.
COLAB_REPO   = "CONNECTS-SCV/bio-guides"
GUIDE_PREFIX = "humanization/humanization_guide"          # 저장소 루트 기준 이 가이드의 경로

def colab_badge_cell(rel_path):
    url = f"https://colab.research.google.com/github/{COLAB_REPO}/blob/main/{GUIDE_PREFIX}/{rel_path}".replace(" ", "%20")
    return {"cell_type": "markdown", "metadata": {},
            "source": [f"[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)]({url})\n"]}


def save(cells, folder, name, title):
    cells = [colab_badge_cell(f"{folder}/{name}")] + cells
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

# HuggingFace 가중치 다운로드가 '멈춘 채' 매달리는 일을 막아요.
# (멈춤은 예외가 안 나서 폴백이 안 걸려요 — 타임아웃을 걸어 실패로 바꿔야 data/ 로 이어져요)
os.environ.setdefault("HF_HUB_DOWNLOAD_TIMEOUT", "30")   # 스트림 30초 무응답 → 끊고 재시도
os.environ.setdefault("HF_HUB_ETAG_TIMEOUT", "15")

def _run(cmd, check=True, timeout=None, quiet=False):
    # timeout 을 꼭 주세요 — 네트워크가 '멈춘 채' 매달리면 예외가 안 나서 data/ 폴백이 안 걸립니다.
    """quiet=True 면 출력을 삼키고 **실패했을 때만** 보여줘요.
    apt-get 은 "(Reading database ... 5%(Reading database ... 10%" 같은 진행률을 600자 넘게 쏟아내는데,
    그게 노트북을 연 학습자가 보는 첫 화면을 덮어버려서 실패로 오해하게 만들거든요."""
    print("$", cmd)
    if not quiet:
        return subprocess.run(cmd, shell=True, check=check, timeout=timeout)
    p = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
    if p.returncode != 0:
        print((p.stdout or "") + (p.stderr or ""))
        if check:
            raise subprocess.CalledProcessError(p.returncode, cmd)
    return p

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
assert ROOT is not None, "가이드 루트를 못 찾았어요. 로컬이면 이 노트북을 챕터 폴더 안에서 여세요."

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

_APT = APT_PKGS.split() if (APT_PKGS and IN_COLAB) else []   # 모아서 apt 를 한 번만 돌립니다
if PIP_PKGS:
    _ensure(PIP_PKGS)

def _ensure_pkg_resources():
    # setuptools 81+(2026-02) 이 pkg_resources 를 없앴는데 IgFold 의존성이 이걸 import 합니다.
    if importlib.util.find_spec("pkg_resources") is None:
        _run(f'"{sys.executable}" -m pip -q install "setuptools<81"')
        importlib.invalidate_caches()

import glob as _glob
if IN_COLAB and not _glob.glob("/usr/share/fonts/**/*Nanum*", recursive=True):
    _APT.append("fonts-nanum")             # Colab 엔 한글 폰트가 없어 라벨이 □ 로 깨져요

if _APT:                                   # apt 인덱스 갱신은 한 번만 (ANARCI 는 hmmscan 이 필요해요)
    _run("apt-get -qq update", timeout=600, quiet=True)
    _run("DEBIAN_FRONTEND=noninteractive apt-get -qq install -y " + " ".join(_APT), timeout=900, quiet=True)


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
    assert hits, f"'{pattern}' 을 my_run/ 에서도 {ref}/ 에서도 찾지 못했어요."
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
    apt_note = ("\n- ANARCI 는 numbering 을 **hmmscan(HMMER)** 서브프로세스로 돌려요. "
                "Colab 에서는 `apt-get install -y hmmer` 가 함께 실행돼요 — pip 만으로는 `hmmscan` 이 없어 죽어요."
                if apt else "")
    return [
        md(f"""## 0) Colab 준비 — 저장소 클론 & 작업 폴더 이동

이 셀이 저장소를 클론하고 `{chapter}/` 로 이동해 필요한 패키지만 깝니다(로컬에서 `{chapter}/` 안에 열었다면 클론 생략).
끝나면 **`my_run/`**(내가 만들 결과)과 **`data/`**(커밋된 레퍼런스)가 준비돼요 — 랩은 `my_run/` 을 먼저 찾고 없으면 `data/` 로 폴백하며 어느 쪽을 썼는지 매번 print 합니다.{apt_note}"""),
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


def title_cell(num, ko, md_link, prev=None):
    # 앞 챕터 my_run 을 물려받는 노트북은 도입부에서 먼저 밝힌다 — 중간부터 들어온
    # 학습자가 자기도 모르게 커밋된 data/ 로 폴백된 채 진행하지 않도록.
    link = f"\n> **앞 랩에서 이어져요** — {prev} 의 `my_run/` 을 먼저 찾고, 없으면 커밋된 `data/` 로 대신합니다." if prev else ""
    return md(f"""# {num} — {ko}

> 본문 [`{md_link}`]({md_link}) 와 **한 절씩 짝지어** 보세요.
> **실측 소요 —** {BADGE[num]}{link}""")


cells_all = {}

# ════════════════════════════════════════════════════════════════════════════
# 03 — 환경 구성·검증
# ════════════════════════════════════════════════════════════════════════════
c = [title_cell("03", "환경 구성 — 설치·검증·러닝 예제", "03_setup.md")]
c += boot("03_setup", pip="pandas", apt="hmmer")
c += [
md("""## 1) 직접 실행 — 도구 설치 (본문 3.1~3.2)

설치 채널이 도구마다 달라요. **BioPhi 는 bioconda 전용**(PyPI 에 없음), **Humatch 는 GitHub source**, Sapiens·AnthroAb·AbNatiV 는 PyPI 예요.
채널 지도 전체는 4) 의 표(`data/verified_versions.csv` 의 `install` 컬럼)에서 한 번에 봅니다.

로컬 conda 라면 본문 3.1 의 한 줄로 바닥을 깔 수 있어요.

```bash
conda create -n abhuman -c conda-forge -c bioconda python=3.10 anarci hmmer -y
conda activate abhuman
ANARCI --help
```

이 노트북이 이 챕터에서 실제로 하는 일은 넷이에요 — **① `anarci`·`abnumber`·`sapiens` 설치 → ② import 진단 → ③ 예제 서열 numbering → ④ 검증 버전 대조**.
`hmmscan`(HMMER) 은 위 부트스트랩 셀의 apt 단계에서 이미 깔렸어요. 설치가 실패해도 랩은 멈추지 않아요 — 2) 진단표가 무엇이 빠졌는지 짚어 줍니다."""),
co('''t0 = time.time()
try:
    _ensure("anarci abnumber sapiens")          # 이미 있으면 건너뜁니다
    print(f"설치 셀 소요 {time.time()-t0:.1f}초")
except Exception as e:
    print("설치 실패:", type(e).__name__, str(e)[:200])
    print("→ 여기서 멈추지 마세요. 2) 진단표에서 FAIL 인 줄만 골라 그 줄의 설치 명령을 다시 돌리면 돼요.")

print("hmmscan :", shutil.which("hmmscan") or "PATH 에 없음 → ANARCI numbering 이 FileNotFoundError 로 죽어요")'''),

md("""## 2) 내 결과 확인 — 환경 진단 (본문 3.3·3.4)

본문 3.4 의 검증 네 줄(`ANARCI --help` · `import sapiens` · `import anthroab` · `import anarci`)을 파이썬에서 한 번에 확인해요.
마지막 줄이 특히 중요해요. CLI `ANARCI` 가 잘 돌아도 **파이썬 모듈 `anarci` 가 import 되지 않는** 상태가 있거든요.
본문 3.3 대로 `anarci` 는 **ANARCI 자신 · Humatch 의 정렬 · AbNatiV 의 `-align`** 세 곳이 공통으로 import 해요 — env 를 나눌 거면 **각 env 에 넣어야** 합니다."""),
co('''import pandas as pd

def probe(mod):
    try:
        m = importlib.import_module(mod)
        return "OK", getattr(m, "__version__", "?")
    except Exception as e:
        return "FAIL", f"{type(e).__name__}: {e}"[:60]

CHECKS = [("anarci",   "필수", "ANARCI 자신 · Humatch 정렬 · AbNatiV -align 이 공통 import (본문 3.3)"),
          ("abnumber", "필수", "CDR/region 추출 (Ch.04)"),
          ("sapiens",  "필수", "humanization 엔진 (Ch.05)"),
          ("anthroab", "나중", "본문 3.4 의 검증 4줄 중 하나 — 설치는 Ch.06 에서 해도 돼요")]

rows = []
for mod, when, why in CHECKS:
    st, ver = probe(mod)
    rows.append({"항목": f"import {mod}", "언제": when, "상태": st, "버전/메시지": ver, "쓰는 곳": why})
rows.append({"항목": "hmmscan (HMMER)", "언제": "필수",
             "상태": "OK" if shutil.which("hmmscan") else "FAIL",
             "버전/메시지": shutil.which("hmmscan") or "PATH 에 없음",
             "쓰는 곳": "ANARCI 가 numbering 을 이 서브프로세스로 돌려요"})
rows.append({"항목": "ANARCI CLI", "언제": "권장",
             "상태": "OK" if shutil.which("ANARCI") else "FAIL",
             "버전/메시지": shutil.which("ANARCI") or "없음",
             "쓰는 곳": "Ch.04 의 --assign_germline (파이썬 API 로도 진행 가능)"})

env = pd.DataFrame(rows)
display(env)

bad = [r["항목"] for r in rows if r["언제"] == "필수" and r["상태"] == "FAIL"]
if bad:
    print("필수 항목 실패 —", ", ".join(bad))
    print("→ import 실패는 1) 셀 재실행, hmmscan 실패는 Colab 이면 apt-get install -y hmmer 로 해결돼요.")
else:
    print("필수 4줄(anarci · abnumber · sapiens · hmmscan) 전부 OK — 3) 으로 넘어가도 좋아요.")
print("'나중' 인 항목은 지금 FAIL 이어도 정상이에요 — 해당 챕터에서 설치합니다.")'''),

md("""## 3) 직접 실행 — 러닝 예제 서열로 첫 numbering

가이드 전체를 관통하는 예제 서열(`data/parental.fasta`)이에요. Ch.04~10 의 모든 수치가 이 두 체인에서 나옵니다.
여기서는 **numbering 경로가 실제로 도는지**만 확인해요 — CDR 표·germline 할당은 Ch.04 에서 제대로 합니다."""),
co('''try:
    from abnumber import Chain

    t0 = time.time()
    ch_h = Chain(VH, scheme="imgt")
    ch_l = Chain(VL, scheme="imgt")
    el = time.time() - t0

    print(f"VH  : {len(VH)} aa | chain_type={ch_h.chain_type} | CDR3={ch_h.cdr3_seq}")
    print(f"VL  : {len(VL)} aa | chain_type={ch_l.chain_type} | CDR3={ch_l.cdr3_seq}")
    print(f"abnumber numbering(2 체인) 소요 {el:.2f}초")

    ok = (ch_h.chain_type == "H") and (ch_l.chain_type in ("K", "L")) and bool(ch_h.cdr3_seq) and bool(ch_l.cdr3_seq)
    print("판정 —", "chain_type H/L 이 제대로 붙고 CDR3 두 개가 나왔어요. numbering 경로(hmmscan 포함) 정상이에요."
          if ok else "chain_type 이나 CDR3 가 비었어요. 2) 진단표의 FAIL 줄부터 해결하세요.")
except Exception as e:
    print("numbering 실패:", type(e).__name__, str(e)[:160])
    print("→ 2) 진단표에서 FAIL 인 항목을 보고 1) 설치 셀을 다시 실행하세요.")
    print("   hmmscan 이 없으면 numbering 이, abnumber 가 없으면 CDR 추출이 여기서 막혀요.")'''),

md("""## 4) 레퍼런스 대조 — 이 가이드를 검증한 도구 9종 (본문 3.2)

`data/verified_versions.csv` 는 이 가이드의 모든 수치를 뽑을 때 **실제로 쓴 버전과 설치 채널**이에요.
버전이 달라도 대개 문제없지만, 뒤 챕터의 결과가 어긋나면 여기부터 비교하세요."""),
co('''ver = pd.read_csv(find_one("verified_versions.csv"))

IMPORT_OF = {"ANARCI": "anarci", "Humatch": "humatch"}       # 표기 ≠ import 이름
WHERE     = {"ANARCI": "Ch.04·06·07", "abnumber": "Ch.04", "sapiens": "Ch.05",
             "Humatch": "Ch.06", "anthroab": "Ch.06", "abnativ": "Ch.07",
             "igfold": "Ch.08", "transformers": "Ch.07", "torch": "Ch.07·08"}
LIGHT     = {"anarci", "abnumber", "sapiens", "anthroab"}    # 버전 확인을 위해 import 해도 싼 것들

from importlib.metadata import version as _dist_version

def installed_version(mod):
    for nm in (mod, mod.lower(), mod.upper()):
        try:
            return _dist_version(nm)
        except Exception:
            pass
    if not _have(mod):
        return None
    if mod in LIGHT:
        try:
            return getattr(importlib.import_module(mod), "__version__", "설치됨")
        except Exception:
            return "설치됨(버전 미상)"
    return "설치됨"

rows = []
for _, r in ver.iterrows():
    tool = str(r["tool"])
    mod  = IMPORT_OF.get(tool, tool.lower())
    got  = installed_version(mod)
    rows.append({"도구": tool, "검증 버전": r["version"], "내 버전": got or "미설치",
                 "상태": "미설치" if got is None else ("일치" if str(got) == str(r["version"]) else "다름"),
                 "설치 채널": r["install"], "쓰는 곳": WHERE.get(tool, "-")})
vt = pd.DataFrame(rows)
display(vt)

need = vt[vt["도구"].isin(["ANARCI", "abnumber", "sapiens"])]
miss = list(need.loc[need["상태"] == "미설치", "도구"])
print("이 챕터 필수 3종 —", "전부 설치됨" if not miss else "빠짐 " + ", ".join(miss))
print(f"나머지 {len(vt) - len(need)}종은 쓰는 챕터에서 설치돼요 — 지금 '미설치' 여도 정상이에요.")

trow = vt[vt["도구"] == "torch"]
if len(trow):
    want, got = str(trow["검증 버전"].iloc[0]), str(trow["내 버전"].iloc[0])
    note = str(ver.loc[ver["tool"] == "torch", "note"].iloc[0])
    if got == "미설치":
        print(f"torch — 아직 없어요. Ch.07·08 에서 검증 버전 {want} 로 깔면 돼요.")
    elif got == want:
        print(f"torch {got} — 검증 버전과 같아요.")
    else:
        print(f"torch {got} ≠ 검증 {want} — {note}")'''),

md("""## 이 랩에서 확인한 것

1. `hmmscan`(HMMER) 이 PATH 에 없으면 ANARCI numbering 이 **FileNotFoundError** 로 죽어요 — Colab 은 `apt-get install -y hmmer` 가 정답.
2. **`import anarci` 는 세 곳(ANARCI·Humatch·AbNatiV `-align`)이 공통으로 쓰는 관문**이에요. env 를 나누면 각 env 에 넣으세요.
3. 설치 채널은 도구마다 달라요 — BioPhi 는 **bioconda 전용**, Humatch 는 **GitHub source**, Sapiens·AnthroAb·AbNatiV 는 **PyPI**. 4) 의 `설치 채널` 컬럼이 9종 전체 지도예요.
4. 러닝 예제 CDR3 — VH `ARRGRYGLYAMDY` · VL `QSYDSSLRVV`. 이 값이 나왔다면 Ch.04 로 넘어가도 좋아요.

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

`--assign_germline` 이 핵심이에요. 이게 있어야 "가장 가까운 사람 germline 과 몇 % 같은가" 가 나오고, 그 숫자가 humanization 전략을 정해요."""),
co('''t0 = time.time()
try:
    r = subprocess.run(["ANARCI", "-i", "data/parental.fasta", "--scheme", "imgt", "--csv",
                        "-o", str(MY / "anarci_gl"), "--assign_germline", "--use_species", "human"],
                       capture_output=True, text=True, timeout=300)
    rc, err = r.returncode, r.stderr
except FileNotFoundError as e:
    # ANARCI CLI 자체가 PATH 에 없음 (hmmscan 이 없으면 numbering 도 여기서 죽어요 — Ch.03)
    rc, err = 127, f"{e} — ANARCI/hmmscan 이 PATH 에 없어요"
except subprocess.TimeoutExpired:
    rc, err = 124, "300초를 넘겨 끊었어요"
el = time.time() - t0

gl_paths = sorted(MY.glob("anarci_gl_*.csv"))
if rc == 0 and gl_paths:
    print(f"ANARCI numbering+germline {el:.2f}초 · CSV {len(gl_paths)}개")
    for p in gl_paths:
        print("  →", p)
    print("판정 — 체인별 CSV(H · KL)가 생겼으면 numbering 과 germline 할당이 모두 끝난 거예요.")
else:
    print("ANARCI CLI 실패:", str(err).strip()[:300])
    print("→ hmmscan 이 PATH 에 있는지 확인하세요(Ch.03). 이 랩은 커밋된 실행 산출물로 이어집니다.")
    gl_paths = [pathlib.Path("data/anarci_imgt_H.csv"), pathlib.Path("data/anarci_imgt_KL.csv")]
    print("[레퍼런스]", " · ".join(str(p) for p in gl_paths))'''),

md("""## 2) 내 결과 확인 — germline 표와 종 판정 (본문 4.2)

진짜 정보는 germline 컬럼에 있어요. V identity 가 낮은 체인 = 사람 germline 과 멀다 = **humanization 여지가 크다**."""),
co('''import pandas as pd

def _cell(row, name):
    return row[name] if (name in row.index and pd.notna(row[name])) else None

def germline_table(paths):
    """ANARCI --csv 결과에서 체인·종·V/J germline 만 뽑는다. germline 컬럼이 없으면 (표, True)."""
    rows, missing = [], False
    for p in paths:
        for _, r in pd.read_csv(p).iterrows():
            vg, vi = _cell(r, "v_gene"), _cell(r, "v_identity")
            jg, ji = _cell(r, "j_gene"), _cell(r, "j_identity")
            if vg is None or vi is None:
                missing = True
            rows.append({"체인": _cell(r, "chain_type") or "?",
                         "hmm_species": _cell(r, "hmm_species") or "?",
                         "V gene": vg or "—", "V identity": float(vi) if vi is not None else float("nan"),
                         "J gene": jg or "—", "J identity": float(ji) if ji is not None else float("nan")})
    return pd.DataFrame(rows), missing

gl, no_germline = germline_table(gl_paths)
if no_germline:
    print("germline 컬럼이 없어요 — 1) 셀에 --assign_germline --use_species human 을 붙여 다시 실행하세요.")
    print("[레퍼런스] data/anarci_imgt_H.csv · data/anarci_imgt_KL.csv 로 이어갑니다")
    gl, _ = germline_table(["data/anarci_imgt_H.csv", "data/anarci_imgt_KL.csv"])
display(gl)

hv = gl.loc[gl["체인"] == "H", "V identity"]
lv = gl.loc[gl["체인"].isin(["K", "L"]), "V identity"]
if len(hv) and len(lv):
    h, l = float(hv.iloc[0]), float(lv.iloc[0])
    print(f"V identity — heavy {h:.0%} / light {l:.0%}. 낮은 쪽인 "
          f"{'heavy' if h < l else 'light'} 에 손댈 자리가 많아요. 노력의 무게중심을 여기에 둡니다.")

# HMM 종 순위 — 어느 종 프로파일이 이겼는지, 그리고 그 차이가 믿을 만한지
cur, hits = None, {}
for ln in pathlib.Path(find_one("anarci_hits.txt")).read_text().splitlines():
    f = ln.split()
    if not f:
        continue
    if f[0] == "NAME":
        cur = f[1]; hits[cur] = []
    elif cur and len(f) >= 5 and f[0][-2:] in ("_H", "_L", "_K"):
        hits[cur].append((f[0], float(f[2])))
for name, hs in hits.items():
    if len(hs) >= 2:
        gap = hs[0][1] - hs[1][1]
        verdict = "종 판정 근거로 쓸 만해요" if gap >= 10 else "사실상 동률이라 종 판정 근거로는 약해요"
        print(f"{name} HMM 1위 {hs[0][0]} {hs[0][1]} · 2위 {hs[1][0]} {hs[1][1]} (차 {gap:.1f}) — {verdict}")'''),

md("""## 3) 같은 서열, 다른 J 유전자 — 동점을 직접 재계산 (본문 4.2)

ANARCI 와 abnumber 는 같은 서열에 **서로 다른 J 유전자**를 답해요. 어느 쪽이 틀린 게 아니라 동점이에요.
말로 넘기지 말고 확인해요 — ANARCI 패키지 안에 IMGT 정렬된 사람 germline 세트가 들어 있으니,
**1) 에서 나온 IMGT 번호열을 그 세트 전체와 대조**하면 몇 개가 동률인지 그대로 보입니다.
(여기서 만드는 numbering 은 이 노트북 전체가 재사용해요 — 체인당 딱 한 번만 돌려요.)"""),
co('''HAVE_ABNUMBER, chains, abn_j = _have("abnumber"), {}, "—"
if HAVE_ABNUMBER:
    try:
        from abnumber import Chain
        t0 = time.time()
        chains["H"] = Chain(VH, scheme="imgt", assign_germline=True)
        chains["L"] = Chain(VL, scheme="imgt", assign_germline=True)
        abn_j = chains["H"].j_gene
        print(f"abnumber numbering(H·L, germline 포함) {time.time()-t0:.2f}초")
    except Exception as e:
        HAVE_ABNUMBER = False
        print("abnumber 실패:", type(e).__name__, str(e)[:120])
        print("→ 5)·6) 은 커밋된 크로스워크/CDR 표로 이어져요.")

anarci_j = gl.loc[gl["체인"] == "H", "J gene"].iloc[0] if (gl["체인"] == "H").any() else "?"
anarci_v = gl.loc[gl["체인"] == "H", "V gene"].iloc[0] if (gl["체인"] == "H").any() else "?"
print("ANARCI J gene  :", anarci_j)
print("abnumber J gene:", abn_j)

# ── IMGT 번호열 하나를 뽑아 germline 세트 전체와 대조 ──────────────────────────
def imgt_row(paths, want="H"):
    for p in paths:
        d = pd.read_csv(p)
        sel = d[d["chain_type"] == want] if "chain_type" in d.columns else d
        if len(sel):
            cols = sorted([c for c in d.columns if str(c).isdigit()], key=int)
            return [str(sel.iloc[0][c]) for c in cols]
    return None

par_imgt = imgt_row(gl_paths, "H")
try:
    from anarci import germlines
    HAVE_GLSET = par_imgt is not None
except Exception as e:
    HAVE_GLSET = False
    print("anarci germline 세트를 못 읽었어요:", type(e).__name__, str(e)[:100])

def identity_scan(region):
    """parental H 의 IMGT 번호열 vs 사람 germline(V 또는 J) 전체 — gap 을 뺀 위치에서 % identity."""
    out = []
    for allele, gseq in germlines.all_germlines[region]["H"]["human"].items():
        pairs = [(a, b) for a, b in zip(gseq, par_imgt) if a != "-" and b != "-"]
        if not pairs:
            continue
        m = sum(a == b for a, b in pairs)
        out.append({"allele": allele, "일치": m, "정렬길이": len(pairs), "identity": m / len(pairs)})
    df = pd.DataFrame(out)
    return df.sort_values(["identity", "allele"], ascending=[False, True]).reset_index(drop=True)

def top_tie(df):
    return df[df["identity"] >= df["identity"].max() - 1e-9]

if HAVE_GLSET:
    tie_j = top_tie(identity_scan("J"))
    display(tie_j)
    r0 = tie_j.iloc[0]
    print(f"J 최고 동률 {len(tie_j)}개 — {int(r0['일치'])}/{int(r0['정렬길이'])} = {r0['identity']:.2%}")
    picked = [x for x in (anarci_j, abn_j) if isinstance(x, str) and x not in ("—", "?")]
    inside = [x for x in picked if x in set(tie_j["allele"])]
    print(f"두 도구가 고른 {len(picked)}개 중 {len(inside)}개가 이 동률 목록 안 — "
          "어느 쪽이 먼저 나오냐는 tie-break(참조 세트·순회 순서) 문제예요.")
print("판정 — J 절편은 14 잔기라 동점이 흔해요. backmutation 판단의 근거는 V 로 잡고, J 는 참고로만 봅니다.")'''),

md("""## 4) 레퍼런스 대조 — IgBLAST 로 V 유전자 교차검증 (본문 4.4)

ANARCI 의 germline 추정이 맞는지 두 번째 도구로 확인하면 더 든든해요. 진입장벽은 **germline DB 를 직접 마련해야** 한다는 점인데,
본문의 트릭이 여기서 통해요 — **ANARCI 패키지 안의 사람 germline 을 FASTA 로 뽑아** DB 재료로 씁니다(외부 다운로드 없음).

```bash
conda install -c bioconda igblast -y
makeigblastdb -in human_IGHV.fasta -dbtype prot -out db/human_gl_V
igblastp -query parental_H.fasta -germline_db_V db/human_gl_V -organism human -outfmt 7
```

`igblastp` 가 없어도 괜찮아요. 같은 germline 세트로 **% identity 를 직접 계산**해 같은 대조를 합니다."""),
co('''fa = None
if HAVE_GLSET:
    ref_v = germlines.all_germlines["V"]["H"]["human"]
    fa = MY / "human_IGHV.fasta"
    fa.write_text("".join(f">{a}\\n{str(s).replace('-', '').replace('.', '')}\\n" for a, s in ref_v.items()))
    print(f"human IGHV allele {len(ref_v)}개 → {fa}")

igb, mkdb = shutil.which("igblastp"), shutil.which("makeigblastdb")
if fa and igb and mkdb:
    db = MY / "db"; db.mkdir(exist_ok=True)
    q = MY / "parental_H.fasta"; q.write_text(f">parental_H\\n{VH}\\n")
    try:
        subprocess.run(f'makeigblastdb -in "{fa}" -dbtype prot -out "{db}/human_gl_V"',
                       shell=True, capture_output=True, text=True, timeout=300)
        r = subprocess.run(f'igblastp -query "{q}" -germline_db_V "{db}/human_gl_V" -organism human -outfmt 7',
                           shell=True, capture_output=True, text=True, timeout=300)
        rows = [ln.split("\\t") for ln in r.stdout.splitlines() if ln.startswith("V\\t")]
        for h in rows[:3]:
            print("  igblastp hit —", " ".join(h[1:5]), "(query · subject · %identity · 정렬길이)")
        if not rows:
            print("  igblastp 가 V 히트를 내지 않았어요:", (r.stderr or "").strip()[:200])
    except Exception as e:
        print("igblastp 실행 실패:", type(e).__name__, str(e)[:160])
else:
    print("igblastp/makeigblastdb 가 없어요 — conda install -c bioconda igblast 로 깔면 이 셀이 실제 BLAST 까지 돌려요.")

if HAVE_GLSET:
    tie_v = top_tie(identity_scan("V"))
    display(tie_v)
    r0 = tie_v.iloc[0]
    print(f"V 최고 동률 {len(tie_v)}개 — {int(r0['일치'])}/{int(r0['정렬길이'])} = {r0['identity']:.2%}")
    fams = sorted({str(a).split("-")[0].split("*")[0] for a in tie_v["allele"]})
    print("동률 allele 의 계열 —", ", ".join(fams), "· ANARCI 가 고른", anarci_v,
          "가 이 목록 안" if anarci_v in set(tie_v["allele"]) else "는 이 목록 밖")
    print(f"판정 — 계열이 {len(fams)}개면 정렬 방식이 다른 두 경로가 같은 곳을 가리킨 거예요. "
          "유전자 이름이 한 끗 달라도 subgroup 과 identity 가 같으면 결론은 하나예요.")
print("참고 — igblastp 는 단백질 모드라 J·junction 은 다루지 않아요. V gene 과 % identity 확인이 주 용도예요.")'''),

md("""## 5) 번호 체계가 두 개예요 — raw ↔ IMGT 크로스워크

뒤 챕터에서 도구별 mutation 표기가 섞여요.

| 체계 | 어디서 쓰나 | 예 |
|---|---|---|
| **raw 1-based** | Sapiens·AnthroAb 의 `predict_scores` 가 그대로 쓰는 서열 인덱스 | `I78T` = 입력 문자열의 78번째 잔기 |
| **IMGT** | ANARCI/abnumber numbering. gap·삽입이 있어 raw 와 어긋남 | `H86` = 같은 잔기의 IMGT 번호 |

Humatch 는 indel 을 만들 수 있어(우리 VL 은 1 잔기 짧아져요) **raw 인덱스 비교가 깨져요.** 그래서 도구 간 비교는 **반드시 IMGT 로 변환**해서 합니다."""),
co('''def raw2imgt(seq, ch):
    """raw 1-based 인덱스 → IMGT 라벨. numbering 밖(C-말단 꼬리)은 tail 로 표시."""
    assert seq.startswith(ch.seq), "numbering 영역이 서열 앞부분과 어긋나요 — 입력 서열을 확인하세요"
    m, pos_raw, last = {}, {}, None
    for i, (pos, aa) in enumerate(ch, start=1):
        m[i] = str(pos); pos_raw[pos] = i; last = str(pos)
    for k in range(1, len(ch.tail) + 1):
        m[len(ch.seq) + k] = f"{last}_tail{k}"
    return m, pos_raw

r2i, raw_of = {}, {}
if HAVE_ABNUMBER:
    for tag, seq in (("H", VH), ("L", VL)):
        r2i[tag], raw_of[tag] = raw2imgt(seq, chains[tag])
        (MY / f"raw2imgt_{tag}.json").write_text(
            json.dumps({str(k): v for k, v in r2i[tag].items()}, indent=1))
    print("→", MY / "raw2imgt_H.json", "·", MY / "raw2imgt_L.json")
else:
    for tag in ("H", "L"):
        p = find_one(f"raw2imgt_{tag}.json")
        r2i[tag] = {int(k): v for k, v in json.loads(pathlib.Path(p).read_text()).items()}

def _cross(chain, picks):        # 대괄호·중괄호 없이 "raw 78 → H86" 꼴로 읽히게
    return " · ".join(f"raw {k} → {r2i[chain][k]}" for k in picks if k in r2i[chain])
print("raw → IMGT (VH) —", _cross("H", (5, 12, 78, 115)))
print("raw → IMGT (VL) —", _cross("L", (31, 85, 109, 111)))
last_l = max(r2i["L"])
print(f"VL 마지막 잔기 raw {last_l} → {r2i['L'][last_l]} — IMGT 범위 밖이라 tail 로 라벨링돼요")
print("판정 — Sapiens 가 'I78T' 라고 하면 raw 78번이고, 같은 잔기의 IMGT 번호는",
      r2i["H"].get(78), "이에요. Ch.06 의 도구 간 합의는 이 변환을 거쳐야 성립해요.")'''),

md("""## 6) 직접 실행 — CDR 추출 + **보호 좌표 못 박기** (본문 4.3)

humanization 에서 가장 먼저 할 일은 "여기는 절대 안 건드린다"를 좌표로 고정하는 것이에요.
CDR 을 **raw 인덱스**(Sapiens/AnthroAb 가 쓰는 좌표)와 **IMGT 라벨** 두 가지로 저장하고, 본문 4.3 의 IMGT 규격창(**CDR1 27–38 · CDR2 56–65 · CDR3 105–117**) 안에 들어오는지까지 봅니다.
Ch.05 의 CDR 가드가 여기서 나온 파일을 그대로 씁니다."""),
co('''IMGT_WINDOW = {"CDR1": (27, 38), "CDR2": (56, 65), "CDR3": (105, 117)}   # 본문 4.3

def imgt_num(label):
    d = "".join(x for x in str(label) if x.isdigit())
    return int(d) if d else None

cdr_rows = []
if HAVE_ABNUMBER:
    for tag in ("H", "L"):
        ch = chains[tag]
        for name in ("CDR1", "CDR2", "CDR3"):
            if name not in ch.regions:
                continue
            reg = ch.regions[name]
            pos = list(reg.keys())
            raws = [raw_of[tag][p] for p in pos]
            cdr_rows.append({"chain": tag, "cdr": name, "sequence": "".join(reg.values()),
                             "raw_start": min(raws), "raw_end": max(raws),
                             "imgt": f"{pos[0]}..{pos[-1]}"})
else:
    print("[레퍼런스] data/cdr_table_imgt.csv 의 CDR 서열로 좌표를 복원해요")
    for _, r in pd.read_csv("data/cdr_table_imgt.csv").iterrows():
        tag, s = r["chain"], r["sequence"]
        st = (VH if tag == "H" else VL).find(s)
        if st < 0:
            print(f"  {tag}-{r['cdr']} 를 parental 에서 못 찾아 건너뜁니다(입력 서열이 레퍼런스와 다르면 생겨요)")
            continue
        cdr_rows.append({"chain": tag, "cdr": r["cdr"], "sequence": s,
                         "raw_start": st + 1, "raw_end": st + len(s),
                         "imgt": f"{r2i[tag].get(st + 1)}..{r2i[tag].get(st + len(s))}"})

guard = {"H": [], "L": []}
for row in cdr_rows:
    guard[row["chain"]] += list(range(row["raw_start"], row["raw_end"] + 1))
    lo, hi = IMGT_WINDOW[row["cdr"]]
    a, b = imgt_num(row["imgt"].split("..")[0]), imgt_num(row["imgt"].split("..")[-1])
    row["IMGT 규격창"] = f"{lo}–{hi}"
    row["규격 안"] = bool(a is not None and b is not None and lo <= a and b <= hi)

cdr = pd.DataFrame(cdr_rows)
if not len(cdr):
    print("CDR 좌표를 하나도 만들지 못했어요 — 3) 에서 abnumber 가 실패했고 레퍼런스 복원도 안 됐어요.")
else:
    display(cdr)
    if HAVE_ABNUMBER:
        cdr.to_csv(MY / "cdr_table_imgt.csv", index=False)
        (MY / "cdr_guard.json").write_text(json.dumps(guard, indent=1))
        print("→", MY / "cdr_table_imgt.csv", "·", MY / "cdr_guard.json")

    print("보호 좌표(raw 1-based) — VH", len(guard["H"]), "잔기 · VL", len(guard["L"]), "잔기")
    print(f"IMGT 규격창 안에 들어온 CDR {int(cdr['규격 안'].sum())}/{len(cdr)}개")
    h3 = cdr[(cdr["chain"] == "H") & (cdr["cdr"] == "CDR3")]
    if len(h3):
        print("판정 — CDR-H3 =", h3["sequence"].iloc[0],
              "· 항원 결합에 가장 결정적인 loop 예요. 여기 mutation 이 들어가면 빨간불이에요.")'''),

md("""## 7) 레퍼런스 대조 — 커밋된 실행 결과와 맞춰보기

`data/` 는 이 가이드를 만들 때 **실제로 돌려 나온** 산출물이에요. 내 결과와 한 글자씩 비교해요."""),
co('''ref_cdr   = pd.read_csv("data/cdr_table_imgt.csv")
ref_gl    = pd.read_csv("data/germline_assignment.csv")
ref_r2i_H = json.loads(pathlib.Path("data/raw2imgt_H.json").read_text())

got  = {(r.chain, r.cdr): r.sequence for r in cdr.itertuples()}
want = {(r.chain, r.cdr): r.sequence for r in ref_cdr.itertuples()}
common = sorted(set(got) & set(want))
print(f"CDR {len(common)}개 일치", all(got[k] == want[k] for k in common))
print("raw→IMGT(H) 일치", {str(k): v for k, v in r2i["H"].items()} == ref_r2i_H)
if not HAVE_ABNUMBER:
    print("(지금은 커밋된 레퍼런스로 좌표를 복원한 상태라 위 두 줄은 data/ 를 data/ 와 비교한 셈이에요.)")

rows = []
for _, r in ref_gl.iterrows():
    sel = gl[gl["체인"] == r["chain"]]
    col = f"{r['gene_type']} gene"
    mine_gene = str(sel[col].iloc[0]) if (len(sel) and col in gl.columns) else "—"
    mine_id   = float(sel[f"{r['gene_type']} identity"].iloc[0]) if (len(sel) and f"{r['gene_type']} identity" in gl.columns) else float("nan")
    rows.append({"체인": r["chain"], "종류": r["gene_type"],
                 "레퍼런스": f"{r['gene']} {r['identity_pct']}%",
                 "내 결과": f"{mine_gene} {mine_id:.1%}",
                 "같은 유전자": bool(mine_gene == r["gene"])})
chk = pd.DataFrame(rows)
display(chk)
print(f"같은 유전자 {int(chk['같은 유전자'].sum())}/{len(chk)}줄. "
      "ANARCI CSV 의 identity 는 소수 둘째 자리에서 반올림돼 있어 germline_assignment.csv 의 63.27% 가 0.63 으로 보여요.")
print("판정 — V 유전자가 두 줄 다 맞으면 입력 QC 통과예요. J 는 3) 에서 본 대로 동률이라 갈릴 수 있어요.")'''),

md("""## 이 랩에서 확인한 것

1. **germline 실측** — VH `IGHV1-69*06` **63.27%** / VL `IGLV1-40*01` **80.85%**. heavy 가 훨씬 비인간적이라 손댈 자리가 많아요.
2. **J 유전자는 동률** — 사람 germline 세트를 직접 훑으면 J 최고점이 **12/14 = 85.71%** 로 여러 allele 에 걸쳐 있어요. ANARCI 의 `IGHJ6*01` 과 abnumber 의 `IGHJ4*01` 이 모두 그 안이라 tie-break 만 갈립니다. 판단 근거는 V 로 잡아요.
3. **IgBLAST 교차검증** — ANARCI 패키지의 germline 을 FASTA 로 뽑아 DB 를 만들면 외부 다운로드 없이 재현돼요. top hit 은 `IGHV1-8*01`·`IGHV1-69*08` **63.27%** 로 ANARCI 와 **같은 IGHV1 계열·같은 identity** 예요. `igblastp` 는 J·junction 을 다루지 않아요.
4. **CDR 6개** — H `GYTFTDYV`/`IYPGSGTN`/`ARRGRYGLYAMDY`, L `SSDVGHKFP`/`KNL`/`QSYDSSLRVV`. 여섯 개 모두 IMGT 규격창(27–38 · 56–65 · 105–117) 안이에요.
5. **번호 체계 두 개**(raw 1-based ↔ IMGT)를 이어 붙인 `raw2imgt_*.json` 을 만들었어요. Ch.06 의 도구 간 합의 분석이 이 파일 위에서 돕니다.
6. **CDR 보호 좌표**(`cdr_guard.json`, VH 29 · VL 22 잔기)를 못 박았어요 — Ch.05 에서 이걸로 사고를 막아요.

다음 → **[Ch.05 — Sapiens](../05_humanize_sapiens/05_sapiens_lab.ipynb)**"""),
]
cells_all[("04_sequence_qc", "04_numbering_lab.ipynb", "04 Numbering Lab")] = c


# ════════════════════════════════════════════════════════════════════════════
# 05 — Sapiens
# ════════════════════════════════════════════════════════════════════════════
c = [title_cell("05", "BioPhi/Sapiens — 후보 생성 · CDR 사고 · humanness", "05_humanize_sapiens.md",
                prev="Ch.04 numbering")]
c += boot("05_humanize_sapiens", pip="pandas matplotlib sapiens")
c += [
md("""## 1) 직접 실행 — 설치 함정을 넘고 Sapiens 돌리기 (본문 5.1~5.2)

첫 줄에서 막히는 분이 많아요. `pip install biophi` 는 이렇게 죽어요.

```
ERROR: Could not find a version that satisfies the requirement biophi (from versions: none)
```

BioPhi 는 **bioconda 전용**(v1.0.11) 이라 PyPI 에 아예 없어요. 반면 사람화를 실제로 담당하는 엔진 **Sapiens 는 PyPI 에 따로**(`sapiens` 1.1.0) 올라와 있어요. 후보 서열만 빨리 뽑을 거면 이쪽이 제일 빠른 길이고, 0) 부트스트랩이 깐 것도 이거예요.

```bash
conda install -c bioconda biophi     # 전체(웹·CLI 포함) — PyPI 아님
python -m pip install sapiens        # humanization 엔진만
```

핵심 함수는 `predict_scores` 하나예요 — position 마다 20개 아미노산에 대한 **사람 모델의 확률 분포**를 주고, 각 자리에서 확률이 가장 높은 잔기를 이어 붙이면(**argmax**) 그게 Sapiens-humanized 서열이에요. 모델 가중치는 첫 실행 때 HuggingFace 에서 받아와요.

**가드 없이** 돌립니다 — 본문이 경고한 사고를 직접 재현하려고요."""),
co('''import pandas as pd, numpy as np

def mutations(par, hum):
    """길이가 같은 두 서열의 치환 목록 (raw 1-based)."""
    return [{"position_1based": i + 1, "wt": a, "mut": b, "mutation": f"{a}{i+1}{b}"}
            for i, (a, b) in enumerate(zip(par, hum)) if a != b]

RAN_SAPIENS, mat_h, mat_l = False, None, None
# 부트스트랩이 HF_HUB_DOWNLOAD_TIMEOUT=30 을 걸어 '멈춤'을 실패로 바꿔 뒀어요.
# 여기서는 두 번까지 재시도하고, 그래도 안 되면 커밋된 실행 산출물(data/)로 이어가요.
for _attempt in (1, 2):
    if not _have("sapiens"):
        print("sapiens 모듈이 없어요 — python -m pip install sapiens 로 깔면 이 셀이 실제로 돌아요.")
        break
    try:
        import sapiens
        t0 = time.time()
        mat_h = sapiens.predict_scores(VH, "H")          # rows=position, cols=20 AA
        mat_l = sapiens.predict_scores(VL, "L")
        hum_h = "".join(mat_h.columns[mat_h.values.argmax(axis=1)])   # 가드 없는 argmax
        hum_l = "".join(mat_l.columns[mat_l.values.argmax(axis=1)])
        print(f"Sapiens predict_scores VH+VL {time.time()-t0:.2f}초")
        mat_h.to_csv(MY / "score_matrix_VH_parental.csv", index_label="position0based")
        mat_l.to_csv(MY / "score_matrix_VL_parental.csv", index_label="position0based")
        write_fasta(MY / "sapiens_humanized_noguard.fasta",
                    {"sapiens_humanized_VH": hum_h, "sapiens_humanized_VL": hum_l})
        RAN_SAPIENS = True
        break
    except Exception as e:
        print(f"Sapiens 실행 실패({_attempt}/2)", type(e).__name__, str(e)[:160])
        if _attempt == 1:
            print("  · HuggingFace 다운로드 지연일 수 있어 5초 뒤 다시 시도해요")
            time.sleep(5)

if not RAN_SAPIENS:
    f = read_fasta(REF / "sapiens_humanized.fasta")
    hum_h, hum_l = f["sapiens_humanized_VH"], f["sapiens_humanized_VL"]
    mat_h = pd.read_csv(REF / "score_matrix_VH_parental.csv", index_col=0)
    mat_l = pd.read_csv(REF / "score_matrix_VL_parental.csv", index_col=0)
SRC = "내 실행(my_run/)" if RAN_SAPIENS else "레퍼런스(data/)"

# mutation 은 어느 경로든 **서열에서 직접 다시** 셉니다 — 6) 의 대조가 진짜 대조가 되도록.
mut_h = pd.DataFrame(mutations(VH, hum_h))
mut_l = pd.DataFrame(mutations(VL, hum_l))
if RAN_SAPIENS:
    mut_h.to_csv(MY / "mutations_VH.csv", index=False)
    mut_l.to_csv(MY / "mutations_VL.csv", index=False)
    print("→", MY / "sapiens_humanized_noguard.fasta", "· mutations_VH.csv · mutations_VL.csv")

for tag, par, hum, mut in (("VH", VH, hum_h, mut_h), ("VL", VL, hum_l, mut_l)):
    print(f"\\n[{tag}] PARENTAL {par}")
    print(f"[{tag}] SAPIENS  {hum}")
    print(f"[{tag}] muts     {', '.join(mut['mutation'])}")

print("\\n서열 출처 —", SRC)
print(f"판정 — VH {len(mut_h)}/{len(VH)} 자리가 바뀌어 parental 대비 identity {1-len(mut_h)/len(VH):.1%}, "
      f"VL 은 {len(mut_l)}/{len(VL)} 로 {1-len(mut_l)/len(VL):.1%} 예요. "
      "네 줄짜리 argmax 가 서열을 이만큼 갈아엎었어요 — 어디를 갈아엎었는지는 다음 절에서 봅니다.")'''),

md("""## 2) 내 결과 확인 — CDR 이 어떻게 됐나 (본문 5.3)

`argmax` 는 **CDR 인지 framework 인지 구분하지 않아요.** 모델은 "사람 항체에서 이 자리에 뭐가 자주 오는가"만 알지, "이 항체가 무엇에 붙어야 하는가"는 모르니까요.

그러니 개수만 세면 안 되고 **자리**를 봐야 해요. Ch.04 에서 못 박은 CDR 좌표를 가져와 6개 CDR 을 하나씩 before → after 로 펼쳐 봅니다. Ch.04 를 건너뛰었다면 이 챕터 `data/cdr_table_imgt.csv` 로 폴백해요 — 이 노트북은 항상 내 결과를 먼저 찾고, 없으면 커밋된 레퍼런스로 이어가요."""),
co('''ct = pd.read_csv(find_prev("04_sequence_qc", "cdr_table_imgt.csv"))
have_raw = {"raw_start", "raw_end"}.issubset(ct.columns)     # Ch.04 my_run 표에만 있는 좌표 컬럼

cdr_rows, guard, hits_all = [], {"H": [], "L": []}, {"H": [], "L": []}
for _, r in ct.iterrows():
    chain = r["chain"]
    par, hum = (VH, hum_h) if chain == "H" else (VL, hum_l)
    if have_raw and pd.notna(r["raw_start"]):
        st, en = int(r["raw_start"]), int(r["raw_end"])
    else:
        st = par.find(r["sequence"]) + 1          # 못 찾으면 0 이 되니 바로 아래에서 걸러요
        en = st + len(r["sequence"]) - 1
    if st < 1 or en > min(len(par), len(hum)):
        print(f"  {chain}-{r['cdr']} 좌표를 못 잡아 건너뜁니다(입력 서열이 레퍼런스와 다르면 생겨요)")
        continue
    rng = list(range(st, en + 1))
    hits = [f"{par[p-1]}{p}{hum[p-1]}" for p in rng if par[p-1] != hum[p-1]]
    guard[chain] += rng
    hits_all[chain] += hits
    cdr_rows.append({"CDR": f"{chain}-{r['cdr']}", "raw 좌표": f"{st}..{en}",
                     "parental": "".join(par[p-1] for p in rng),
                     "Sapiens":  "".join(hum[p-1] for p in rng),
                     "변이": ", ".join(hits) or "—", "파손": bool(hits)})

cdr = pd.DataFrame(cdr_rows)
display(cdr)

gp = GUIDE_ROOT / "04_sequence_qc" / "my_run" / "cdr_guard.json"
if gp.exists():
    prev = json.loads(gp.read_text())
    ok = all(sorted(set(prev.get(k, []))) == sorted(set(guard[k])) for k in ("H", "L"))
    print("Ch.04 cdr_guard.json 좌표와 일치 —", ok)

n_mut = len(mut_h) + len(mut_l)
n_cdr = len(hits_all["H"]) + len(hits_all["L"])
broken = cdr[cdr["파손"]]
print(f"\\nCDR 안에 떨어진 변이 — VH {len(hits_all['H'])}개 · VL {len(hits_all['L'])}개 "
      f"(전체 {n_mut}개 중 {n_cdr}개, {n_cdr/n_mut:.0%})")
print(f"바뀐 CDR {len(broken)}/{len(cdr)}개 —", ", ".join(broken["CDR"]) or "없음")
h3 = cdr[cdr["CDR"] == "H-CDR3"]
if len(h3):
    r3 = h3.iloc[0]
    print(f"CDR-H3   {r3['parental']} → {r3['Sapiens']}   ({r3['변이']})")
    print("판정 — Ch.04 가 '여기 변이가 들어가면 빨간불' 이라고 못 박은 그 loop 예요. " +
          ("항원과 직접 만나는 자리가 바뀌었으니 사람다움과 별개로 결합력을 반드시 확인해야 해요."
           if r3["파손"] else "여기는 그대로 보존됐어요."))
print("그래서 실무에서는 셋 중 하나를 꼭 해요 — ① CDR 좌표를 argmax 대상에서 제외, "
      "② 도구의 CDR 보호 모드, ③ 후처리로 CDR 을 parental 로 되돌리기.")'''),

md("""## 3) 직접 실행 — CDR 가드 적용본 만들기 (본문 5.3 주의)

셋 중 **③ 후처리 복원**을 그대로 구현해요. 가장 단순하고, 검증하기도 제일 쉬워요 — CDR 좌표의 잔기를 parental 로 되돌리기만 하면 되니까요."""),
co('''def cdr_guarded(par, hum, protected):
    """protected(raw 1-based) 자리의 잔기를 parental 로 되돌린 서열."""
    s = list(hum)
    for p in protected:
        s[p - 1] = par[p - 1]
    return "".join(s)

g_h = cdr_guarded(VH, hum_h, guard["H"])
g_l = cdr_guarded(VL, hum_l, guard["L"])
write_fasta(MY / "sapiens_humanized_cdrguard.fasta",
            {"sapiens_guarded_VH": g_h, "sapiens_guarded_VL": g_l})

cmp_rows = []
for tag, par, ng, gd, pr in (("VH", VH, hum_h, g_h, guard["H"]), ("VL", VL, hum_l, g_l, guard["L"])):
    cmp_rows.append({"체인": tag, "보호 좌표": len(pr),
                     "가드 없음 · 총 변이": sum(a != b for a, b in zip(par, ng)),
                     "가드 없음 · CDR 변이": sum(par[p-1] != ng[p-1] for p in pr),
                     "가드 적용 · 총 변이": sum(a != b for a, b in zip(par, gd)),
                     "가드 적용 · CDR 변이": sum(par[p-1] != gd[p-1] for p in pr)})
cg = pd.DataFrame(cmp_rows)
display(cg)

left = int(cg["가드 적용 · CDR 변이"].sum())
print("→", MY / "sapiens_humanized_cdrguard.fasta")
print(f"판정 — 가드 적용 뒤 CDR 변이 {left}개. " +
      ("0 이면 CDR 은 parental 그대로이고, framework 치환만 남아요."
       if left == 0 else "0 이 아니면 보호 좌표가 서열과 어긋난 거예요 — Ch.04 의 CDR 표부터 다시 보세요.") +
      f" 총 변이는 VH {int(cg.loc[0, '가드 없음 · 총 변이'])}→{int(cg.loc[0, '가드 적용 · 총 변이'])}, "
      f"VL {int(cg.loc[1, '가드 없음 · 총 변이'])}→{int(cg.loc[1, '가드 적용 · 총 변이'])} 로 줄어요.")'''),

md("""## 4) humanness — **정의를 못 박고** 계산 (본문 5.4)

변이를 21개 넣었다고 사람다워졌다는 보장은 없어요. 숫자로 확인해야죠. 그런데 "humanized 의 humanness" 는 계산법이 두 가지고 **값이 서로 달라요.**

| 정의 | 계산 방식 | 이 실행에서 |
|---|---|---:|
| **(a) argmax-on-parental** | parental 문맥 행렬의 position 별 **최대 확률** 평균 — humanized 서열을 다시 스코어링하진 않아요 | 0.782 / 0.851 |
| **(b) 재스코어링 self-prob** | humanized 서열을 `predict_scores` 에 **다시 넣어** 그 서열 **자기 잔기**의 확률 평균 | **0.815 / 0.872** |

본문 표·그림의 값은 **(b)** 예요. 둘 다 직접 계산해서 눈으로 확인해요."""),
co('''def mean_self_prob(mat, seq):
    """확률행렬(rows=position, cols=20 AA)에서 서열 자기 잔기 확률의 평균."""
    return float(np.mean([mat.iloc[i][aa] for i, aa in enumerate(seq)]))

rows, HAVE_GUARD_COL = [], RAN_SAPIENS
for tag, par, ng, gd, chain, mat in (("VH", VH, hum_h, g_h, "H", mat_h),
                                     ("VL", VL, hum_l, g_l, "L", mat_l)):
    row = {"chain": tag,
           "parental": round(mean_self_prob(mat, par), 4),                     # parental self-prob
           "(a) argmax-on-parental": round(float(np.mean(mat.values.max(axis=1))), 4)}
    if RAN_SAPIENS:
        row["(b) 재스코어링 humanized"] = round(mean_self_prob(sapiens.predict_scores(ng, chain), ng), 4)
        row["(b) CDR 가드 적용본"]      = round(mean_self_prob(sapiens.predict_scores(gd, chain), gd), 4)
    else:
        # 커밋된 재스코어링 행렬이 있어 (b) 는 그대로 계산돼요. 가드 적용본은 그 서열을
        # predict_scores 에 다시 넣어야 나오는 값이라, 실행 없이는 열을 만들지 않아요.
        rs = pd.read_csv(REF / f"score_matrix_{tag}_humanized_rescored.csv", index_col=0)
        row["(b) 재스코어링 humanized"] = round(mean_self_prob(rs, ng), 4)
    rows.append(row)

hn = pd.DataFrame(rows)
if RAN_SAPIENS:
    hn.to_csv(MY / "humanness_summary.csv", index=False)
display(hn)

if not HAVE_GUARD_COL:
    print("CDR 가드 적용본 열은 비워 두지 않고 아예 만들지 않았어요 — 그 서열을 predict_scores 에 "
          "다시 넣어야 나오는 값이라, 1) 셀에서 Sapiens 가 실제로 돌면 그때 생겨요.")

for _, r in hn.iterrows():
    line = (f"{r['chain']}  parental {r['parental']:.3f} → (b) {r['(b) 재스코어링 humanized']:.3f} "
            f"(▲ +{r['(b) 재스코어링 humanized'] - r['parental']:.3f})  ·  "
            f"(a) {r['(a) argmax-on-parental']:.3f} · (a)↔(b) 차 "
            f"{abs(r['(b) 재스코어링 humanized'] - r['(a) argmax-on-parental']):.3f}")
    if HAVE_GUARD_COL:
        line += (f"  ·  가드 적용본 {r['(b) CDR 가드 적용본']:.3f} "
                 f"(▼ {r['(b) 재스코어링 humanized'] - r['(b) CDR 가드 적용본']:.3f})")
    print(line)

print("판정 — 같은 실행인데 (a) 와 (b) 가 다른 건 어느 하나가 틀려서가 아니라 재는 대상이 달라서예요. "
      "humanness 를 보고할 때 정의를 반드시 밝혀야 하는 이유예요.")
if HAVE_GUARD_COL:
    drop = (hn["(b) 재스코어링 humanized"] - hn["(b) CDR 가드 적용본"]).max()
    print(f"가드 적용본은 (b) 보다 최대 {drop:.3f} 낮아요 — CDR 을 사람화하지 않았으니 당연하고, "
          "그게 결합력을 지키는 대가예요.")
print("이 값은 Sapiens 모델의 확률이지 OASis 점수가 아니에요 — OASis 는 서열을 9-mer 로 쪼개 "
      "OAS DB 에서 얼마나 자주 관찰되는지로 매기는 별개 지표이고 DB 다운로드가 필요해요(본문 5.4 심화).")'''),

md("""## 5) 그래프 — parental vs humanized (본문 5.4)

본문 그림과 같은 막대를 공용 모듈 `humanization_viz.humanness_bars` 로 그려요. 저장 위치는 `my_run/` 이에요 — 챕터 폴더의 `05_humanness.png` 는 본문이 인용하는 커밋 파일이라 건드리지 않아요."""),
co('''from humanization_viz import humanness_bars
from IPython.display import Image, display

bars = [{"chain": r["chain"], "parental": r["parental"],
         "humanized": r["(b) 재스코어링 humanized"]} for _, r in hn.iterrows()]
png = humanness_bars(bars, "Sapiens humanness — parental vs humanized (정의 b)",
                     MY / "05_humanness.png")
display(Image(str(png)))

pv = {r["chain"]: (r["parental"], r["(b) 재스코어링 humanized"]) for _, r in hn.iterrows()}
low  = min(pv, key=lambda k: pv[k][0])
gain = {k: v[1] - v[0] for k, v in pv.items()}
big  = max(gain, key=gain.get)
print(f"출발점이 낮은 쪽은 {low} ({pv[low][0]:.3f}), 상승폭이 큰 쪽은 {big} (+{gain[big]:.3f}) 이에요.")

glp = GUIDE_ROOT / "04_sequence_qc" / "data" / "germline_assignment.csv"
if glp.exists():
    gv = pd.read_csv(glp)
    gv = gv[gv["gene_type"] == "V"].set_index("chain")["identity_pct"]
    if {"H", "L"}.issubset(gv.index):
        gl_low = "VH" if gv["H"] < gv["L"] else "VL"
        print(f"Ch.04 의 V germline identity 는 VH {gv['H']:.2f}% · VL {gv['L']:.2f}% 로 낮은 쪽이 {gl_low} 였어요.")
        print("판정 — 두 지표가 " + ("같은" if gl_low == low else "다른") +
              " 체인을 가리켜요. " + ("germline 거리와 Sapiens 확률이 같은 결론을 주면 그 판단은 믿고 갑니다."
                                    if gl_low == low else "두 지표가 갈리면 어느 축으로 우선순위를 매길지 먼저 정하세요."))
else:
    print("판정 — 출발점이 낮은 체인이 더 크게 오르는 게 정상이에요. 이미 사람다운 체인은 올릴 여지가 적어요.")'''),

md("""## 6) 레퍼런스 대조

`data/` 는 이 가이드를 만들 때 **실제로 돌려 나온** 산출물이에요. 변이 목록이 문자 단위로 같은지, humanness 가 정의별로 같은지 맞춰 봅니다."""),
co('''for tag, mine in (("VH", mut_h), ("VL", mut_l)):
    ref = pd.read_csv(REF / f"mutations_{tag}.csv")
    a, b = list(mine["mutation"]), list(ref["mutation"])
    print(f"{tag} — 내 계산 {len(a)}개 / 레퍼런스 {len(b)}개 · 목록 일치 {a == b}")
    if a != b:
        print("   내 계산에만 :", ", ".join(sorted(set(a) - set(b))) or "—")
        print("   레퍼런스에만:", ", ".join(sorted(set(b) - set(a))) or "—")
print("(서열 출처는", SRC + " 이고, 변이 목록은 그 서열에서 다시 세어 data/mutations_*.csv 와 맞춘 거예요.)")

ref_hn = pd.read_csv(REF / "humanness_summary.csv")
DEF_KEY = {"parental": "parental",
           "(a) argmax-on-parental": "definition_a_argmax_on_parental_matrix",
           "(b) 재스코어링 humanized": "definition_b_rescored_humanized"}
rows = []
for _, r in hn.iterrows():
    for col, key in DEF_KEY.items():
        if col not in hn.columns:
            continue
        sel = ref_hn[(ref_hn["chain"] == r["chain"]) & (ref_hn["definition"] == key)]
        if not len(sel):
            print(f"  레퍼런스에 {r['chain']} / {key} 행이 없어 이 줄은 건너뜁니다")
            continue
        v, w = float(r[col]), float(sel["mean_probability"].iloc[0])
        rows.append({"chain": r["chain"], "정의": col, "내 결과": round(v, 4),
                     "레퍼런스": round(w, 4), "차": round(abs(v - w), 4)})
chk = pd.DataFrame(rows)
display(chk)
mx = float(chk["차"].max())
print(f"판정 — 정의별 최대 차이 {mx:.4f}. " +
      ("1e-3 아래면 같은 실행을 그대로 재현한 거예요." if mx < 1e-3 else
       "1e-3 을 넘으면 모델 버전이나 입력 서열이 다른 거예요 — sapiens 버전부터 확인하세요."))'''),

md("""## 이 랩에서 확인한 것

1. **설치** — BioPhi 는 **bioconda**(v1.0.11), Sapiens 는 **PyPI `sapiens`**(1.1.0). `pip install biophi` 는 실패해요.
2. **Sapiens humanization = `predict_scores` 의 position 별 argmax.** 실측 **VH 21 변이 · VL 17 변이**(identity 82.5% / 84.7%).
3. **argmax 는 CDR 을 구분하지 않아요** — 6개 CDR 중 **5개**가 바뀌었어요. `H-CDR2`(Y52N·N58T), `H-CDR3`(L104D·Y109V), `L-CDR1`(H31A·K32Y·F33N·P34D), `L-CDR2`(K52G·L54S), `L-CDR3`(R98S). 전체 38개 변이 중 **11개가 CDR 안**이에요.
4. **CDR-H3 `ARRGRYGLYAMDY` → `ARRGRYGDYAMDV`** — Ch.04 가 빨간불이라고 못 박은 loop 에 변이 2개가 들어갔어요. 후처리 복원(`sapiens_humanized_cdrguard.fasta`)을 거치면 CDR 변이 **0개**, 총 변이는 VH 21→17 · VL 17→10 이에요.
5. **humanness 는 정의를 밝혀야** 해요. **(b) 재스코어링** 기준 VH **0.694 → 0.815** · VL **0.770 → 0.872**, 같은 실행을 **(a)** 로 계산하면 **0.782 / 0.851** 이에요. 가드 적용본은 (b) 보다 조금 낮고, 그게 결합력을 지키는 대가예요.
6. 이 값은 Sapiens 모델 확률이지 **OASis 가 아니에요.** OASis 는 9-mer 를 OAS DB 와 대조하는 별개 지표예요.
7. 산출물 — `my_run/sapiens_humanized_noguard.fasta` · `sapiens_humanized_cdrguard.fasta` · `mutations_VH.csv` · `mutations_VL.csv` · `humanness_summary.csv` · `05_humanness.png`. Ch.06~Ch.10 이 이 파일들을 그대로 씁니다.

다음 → **[Ch.06 — Humatch · AnthroAb](../06_cdr_safe_tools/06_tools_lab.ipynb)**"""),
]
cells_all[("05_humanize_sapiens", "05_sapiens_lab.ipynb", "05 Sapiens Lab")] = c


# ════════════════════════════════════════════════════════════════════════════
# 06 — Humatch · AnthroAb · 3도구 합의
# ════════════════════════════════════════════════════════════════════════════
c = [title_cell("06", "CDR-safe 도구 — Humatch · AnthroAb · 3도구 합의", "06_cdr_safe_tools.md",
                prev="Ch.04 numbering")]
c += boot("06_cdr_safe_tools", pip="pandas matplotlib anarci abnumber", apt="hmmer")
c += [
md("""## 1) 직접 실행 — Humatch 설치 + humanization (본문 6.1.1~6.1.2)

Ch.05 의 Sapiens 는 가드 없이 돌리자 CDR 을 건드렸어요. Humatch 는 그 걱정을 도구 안으로 가져간 쪽이에요 —
**CDR 보호가 기본값**(`allow_CDR_mutations=False`)이고, framework 만 CNN 점수 목표에 닿을 때까지 single-point 로 반복 탐색해요.

`pip install humatch` 가 안 되면 **GitHub source** 로 자동 전환해요(본문 6.1.1 의 첫 번째 함정).
첫 실행은 Zenodo 에서 CNN 가중치(heavy/light/paired)와 germline 룩업 배열을 받으므로 **160초** 걸려요(실측).
다운로드가 멈추면 예외가 안 나서 폴백도 안 걸리니, **600초 타임아웃**을 걸어 멈춤을 실패로 바꿔 둡니다."""),
co('''import pandas as pd

# Humatch 는 파이썬 모듈명이 `Humatch`(대문자) 라서 소문자 import 체크가 통하지 않아요 → CLI 존재로 판정
if not shutil.which("Humatch-humanise"):
    _run(f'"{sys.executable}" -m pip -q install humatch', check=False)
if not shutil.which("Humatch-humanise"):
    print("pip 실패 → GitHub source 로 재시도해요")
    _run(f'"{sys.executable}" -m pip -q install git+https://github.com/oxpig/Humatch.git', check=False)
print("Humatch CLI:", shutil.which("Humatch-humanise") or "없음")

# CLI 는 CSV 입력/CSV 출력이 가장 안전해요(문자열 인자 -H/-L 도 가능).
inp = MY / "humatch_in.csv"
inp.write_text("VH,VL\\n%s,%s\\n" % (VH, VL))
out = MY / "humatch_out.csv"
cmd = ["Humatch-humanise", "-i", str(inp), "--vh_col", "VH", "--vl_col", "VL", "-o", str(out), "-v"]

hm_h = hm_l = hm_row = None
env = dict(os.environ, TF_CPP_MIN_LOG_LEVEL="3")
t0 = time.time()
try:
    r = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=600)
    if r.returncode != 0 and "DNN library" in (r.stdout + r.stderr):
        # TensorFlow 가 GPU cuDNN 초기화에 실패하는 환경이 있어요 → CPU 로 강제하고 재시도(실측 사례)
        print("TensorFlow GPU 초기화 실패 → CPU 로 재시도해요")
        env["CUDA_VISIBLE_DEVICES"] = ""
        r = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=600)
    if r.returncode == 0 and out.exists():
        print(f"Humatch 완료 {time.time()-t0:.1f}초 (첫 실행은 Zenodo 가중치 다운로드 포함 — 실측 160초)")
        hm_row = pd.read_csv(out).iloc[0]
        hm_h = hm_row["Humatch_H"].replace("-", "")     # 출력은 200-position 정렬형 → gap 제거
        hm_l = hm_row["Humatch_L"].replace("-", "")
        write_fasta(MY / "humatch_humanised.fasta",
                    {"humatch_humanised_VH": hm_h, "humatch_humanised_VL": hm_l})
    else:
        print("Humatch 실행 실패:", (r.stdout + r.stderr).strip()[-300:])
except subprocess.TimeoutExpired:
    print("Humatch 600초 초과 — Zenodo 다운로드가 멈춘 것 같아요. 셀을 다시 실행하면 받다 만 곳부터 이어받아요.")
except Exception as e:
    print("Humatch 실행 실패:", type(e).__name__, str(e)[:200])

if hm_h is None or hm_l is None:
    ref = read_fasta(REF / "humatch_humanized.fasta")
    hm_h, hm_l = ref["humatch_humanised_VH"], ref["humatch_humanised_VL"]
    print("[레퍼런스]", REF / "humatch_humanized.fasta")

print(f"parental VH {len(VH)} aa · VL {len(VL)} aa  →  Humatch VH {len(hm_h)} aa · VL {len(hm_l)} aa")'''),

md("""## 2) 내 결과 확인 — config 가 약속한 것과 결과가 맞나 (본문 6.1.3~6.1.4)

Humatch 는 실행 로그에 **자기가 무엇을 지킬지 config 로 먼저 선언**해요. 그 선언과 실제 산출물을 맞춰 보는 게 이 절의 일이에요.

그런데 raw 인덱스로 비교하면 안 돼요 — Humatch 는 우리 예제의 **VL 에서 1 잔기를 지워요**(111 → 110 aa).
그래서 CDR 보존 확인은 **"parental CDR 문자열이 후보 안에 그대로 있는가"** 로 합니다(indel 에 안전한 방법)."""),
co('''cfg = pd.read_csv(find_one("humatch_scores.csv")).set_index("metric")["value"]
if hm_row is not None:
    cnn_h, cnn_l, cnn_p = float(hm_row["CNN_H"]), float(hm_row["CNN_L"]), float(hm_row["CNN_P"])
    hv, lv, edit = hm_row["HV"], hm_row["LV"], int(hm_row["Edit"])
else:
    cnn_h, cnn_l, cnn_p = float(cfg["CNN_H"]), float(cfg["CNN_L"]), float(cfg["CNN_P"])
    hv, lv, edit = cfg["HV_gene"], cfg["LV_gene"], int(cfg["edit_total"])

tgt = float(cfg["CNN_target_score"])
display(pd.DataFrame([
    {"config 항목": "allow_CDR_mutations", "값": cfg["allow_CDR_mutations"], "뜻": "CDR 은 기본 보호"},
    {"config 항목": "GL_target_score", "값": cfg["GL_target_score"], "뜻": "germline-likeness 매칭 목표"},
    {"config 항목": "CNN_target_score", "값": cfg["CNN_target_score"], "뜻": "이 점수에 닿을 때까지 framework 탐색"},
    {"config 항목": "CDR_mutations_observed", "값": cfg["CDR_mutations_observed"], "뜻": "실행 결과 CDR 에 들어간 변이 수"},
]))
print(f"gene {hv}/{lv} · edit {edit} · CNN  H {cnn_h:.3f} / L {cnn_l:.3f} / paired {cnn_p:.3f}")
print(f"→ CNN 목표 {tgt:.2f} 도달 —",
      "H " + ("OK" if cnn_h >= tgt else f"미달({cnn_h:.3f})"),
      "· L " + ("OK" if cnn_l >= tgt else f"미달({cnn_l:.3f})"))

ct = pd.read_csv(find_prev("04_sequence_qc", "cdr_table_imgt.csv", quiet=True))
cdrs = {(r["chain"], r["cdr"]): r["sequence"] for _, r in ct.iterrows()}

def cdr_intact(cand_h, cand_l, label):
    rows = []
    for (chain, name), s in cdrs.items():
        seq = cand_h if chain == "H" else cand_l
        rows.append({"후보": label, "CDR": f"{chain}-{name}", "parental CDR": s, "보존": s in seq})
    return rows

chk = pd.DataFrame(cdr_intact(hm_h, hm_l, "Humatch"))
display(chk)
print(f"→ CDR 보존 {int(chk['보존'].sum())} / {len(chk)}.  VL 길이 {len(VL)} → {len(hm_l)}(1 잔기 삭제 = indel).")
print("   config 가 선언한 CDR 보호가 산출물에서도 지켜졌는지가 판정 기준이에요 — 6/6 이면 통과.")'''),

md("""## 3) 직접 실행 — AnthroAb 자동 모드 (본문 6.2.1)

| 모드 | 함수 | 무엇을 바꾸나 |
|---|---|---|
| ① 자동 전체 변경 | `predict_best_score(seq, chain)` | **모든 position** 을 가장 사람다운 잔기로 — **CDR 도 바꿔요** |
| ② 커스텀 마스킹 | `predict_masked(seq, chain)` | 내가 `*` 로 찍은 자리만 |

①을 그대로 돌려 봐요(실측 VH 1.5초 / VL 1.3초). 같은 CDR 보존 검사를 그대로 통과시켜 Humatch 와 나란히 놓습니다."""),
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
    print(f"predict_best_score VH+VL {time.time()-t0:.1f}초 (실측 1.3~1.5초/체인)")
    write_fasta(MY / "anthroab_best_score.fasta",
                {"anthroab_bestscore_VH": ab_h, "anthroab_bestscore_VL": ab_l})
except Exception as e:
    print("AnthroAb 실행 실패:", type(e).__name__, str(e)[:160])

if ab_h is None or ab_l is None:
    f = read_fasta(REF / "anthroab_best_score.fasta")
    ab_h, ab_l = f["anthroab_predict_best_score_VH"], f["anthroab_predict_best_score_VL"]
    print("[레퍼런스]", REF / "anthroab_best_score.fasta")

ab_mut_h = pd.DataFrame(mutations(VH, ab_h)); ab_mut_l = pd.DataFrame(mutations(VL, ab_l))
chk2 = pd.DataFrame(cdr_intact(ab_h, ab_l, "AnthroAb(best_score)"))
display(chk2)
print(f"VH {len(ab_mut_h)} mut · VL {len(ab_mut_l)} mut · CDR 보존 {int(chk2['보존'].sum())} / {len(chk2)}")
broken = [r["CDR"] for _, r in chk2.iterrows() if not r["보존"]]
print("→ 파손된 CDR:", ", ".join(broken) if broken else "없음",
      "— 자동 모드는 CDR 을 지켜 주지 않아요(본문 6.2.1 경고 그대로).")'''),

md("""## 4) 직접 실행 — `predict_masked` 의 버그와 우회 (실측 발견)

**anthroab 1.1.0 의 `predict_masked()` 는 그대로 쓰면 안 됩니다.** docstring 은 `*`/`X` 로 마스킹하라고 하지만,
`hemantn/roberta-base-humAb-*` 의 tokenizer vocab 에는 `*`·`X` 가 **없어요**. 사전에 없는 문자는 `<unk>` 도 아니고 **조용히 삭제**되어
그 뒤 토큰이 한 칸씩 밀려요. 라이브러리는 (원래 길이의) 입력과 (짧아진) 예측을 zip 해서 **말없이 어긋난 결과**를 내거나 `IndexError` 로 죽어요.

우회는 간단해요 — 문자열 마스킹을 건너뛰고 **`input_ids` 를 직접 만들어** 진짜 `mask_token_id` 를 꽂습니다.

여기서 마스킹 대상은 **FR 전체**예요. 본문 6.2.5 의 masking 등급표(FWR exposed ✅ / buried ⚠️ / Vernier 🔸 / interface ⚠️ / CDR ⛔)를
**의도적으로 무시한 최대 마스킹**이고, CDR 보호만 지킨 상한선 실험이에요. 실무 기본값은 등급표대로 **FWR exposed 만** 찍는 쪽입니다."""),
co('''_ensure("torch transformers")

MODELS = {"H": "hemantn/roberta-base-humAb-vh", "L": "hemantn/roberta-base-humAb-vl"}
_LOADED = {}

def _load(chain):
    """체인당 한 번만 로드(가중치 164MB — 매 호출 로드하면 그만큼 매번 기다려요)."""
    if chain not in _LOADED:
        from transformers import AutoModelForMaskedLM, AutoTokenizer
        tok = AutoTokenizer.from_pretrained(MODELS[chain])
        mdl = AutoModelForMaskedLM.from_pretrained(MODELS[chain]); mdl.eval()
        _LOADED[chain] = (tok, mdl)
    return _LOADED[chain]

def masked_fill(seq, chain, mask_positions):
    """mask_positions(1-based)만 마스킹해 예측 — tokenizer 문자열 마스킹을 우회한 정공법.
    (import 를 함수 안에 둬요 — torch/transformers 가 어긋난 환경에서도 셀이 통째로 죽지 않게)"""
    import torch
    tok, mdl = _load(chain)
    vocab = tok.get_vocab()
    ids = [tok.bos_token_id] + [vocab[a] for a in seq] + [tok.eos_token_id]
    x = torch.tensor(ids).unsqueeze(0)
    for p in mask_positions:
        x[0, p] = tok.mask_token_id                 # +1 offset (bos) 이 이미 반영된 인덱스
    with torch.no_grad():
        logits = mdl(input_ids=x).logits[0]
    inv = {v: k for k, v in vocab.items()}
    outs = list(seq)
    for p in mask_positions:
        outs[p - 1] = inv[int(logits[p].argmax())]
    return "".join(outs)

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
    print("CDR 좌표를 CDR 표에서 복원했어요")

fr_h = [i for i in range(1, len(VH) + 1) if i not in guard["H"]]
fr_l = [i for i in range(1, len(VL) + 1) if i not in guard["L"]]
print(f"마스킹 비율 — VH {len(fr_h)}/{len(VH)} · VL {len(fr_l)}/{len(VL)} (CDR 은 0)")

mk_h = mk_l = None
try:
    t0 = time.time()
    mk_h = masked_fill(VH, "H", fr_h)
    mk_l = masked_fill(VL, "L", fr_l)
    print(f"predict_masked(우회 구현) VH+VL {time.time()-t0:.1f}초 — 실측 2.3~2.5초/체인")
    write_fasta(MY / "anthroab_masked_FRonly.fasta",
                {"anthroab_masked_VH": mk_h, "anthroab_masked_VL": mk_l})
except Exception as e:
    print("masked 실행 실패:", type(e).__name__, str(e)[:160])

if mk_h is None or mk_l is None:
    f = read_fasta(REF / "anthroab_masked_FRonly.fasta")
    mk_h, mk_l = f["anthroab_predict_masked_fixed_VH"], f["anthroab_predict_masked_fixed_VL"]
    print("[레퍼런스]", REF / "anthroab_masked_FRonly.fasta")

mk_mut_h = pd.DataFrame(mutations(VH, mk_h)); mk_mut_l = pd.DataFrame(mutations(VL, mk_l))
chk3 = pd.DataFrame(cdr_intact(mk_h, mk_l, "AnthroAb(masked FR-only)"))
print(f"FR-only masked → VH {len(mk_mut_h)} mut · VL {len(mk_mut_l)} mut · "
      f"CDR 보존 {int(chk3['보존'].sum())} / {len(chk3)} (마스킹하지 않았으니 구조적으로 보장)")

if "H" in _LOADED:   # 본문 6.3.2 — 덩치를 로드한 모델에서 그대로 확인
    _cfg, _mdl = _LOADED["H"][1].config, _LOADED["H"][1]
    print(f"AnthroAb VH 모델 — {_cfg.num_hidden_layers}층 · hidden {_cfg.hidden_size} · "
          f"파라미터 {sum(p.numel() for p in _mdl.parameters())/1e6:.1f}M")
    print("   Sapiens(4층 · hidden 128 · 약 0.5M) 와 같은 API 를 쓰지만 덩치가 다른 모델이에요.")'''),

md("""## 5) 직접 실행 — 3도구 합의 (본문 6.2.6)

여기가 이 챕터의 핵심이에요. **도구 간 비교는 반드시 IMGT 번호로** 합니다(Humatch 의 indel 때문에 raw 인덱스가 어긋나므로).
Ch.04 에서 만든 `raw2imgt_*.json` 을 그대로 씁니다.

세는 방법을 두 가지로 나눠요. **세 도구가 모두 건드린 위치**와, 그중 **똑같은 잔기로 바꾼 위치(동일 치환)** 는 다른 숫자예요."""),
co('''def load_map(tag):
    p = GUIDE_ROOT / "04_sequence_qc" / "my_run" / f"raw2imgt_{tag}.json"
    if p.exists():
        print(f"[내 결과 · 04_sequence_qc] {p}")
    else:
        p = REF / f"raw2imgt_{tag}.json"; print(f"[레퍼런스] {p}")
    return {int(k): v for k, v in json.loads(p.read_text()).items()}

r2i = {"H": load_map("H"), "L": load_map("L")}

def to_imgt(df, chain, tool):
    return pd.DataFrame([{"chain": chain, "imgt": r2i[chain][int(r.position_1based)],
                          "wt": r.wt, "mut": r.mut, "sub": f"{r.wt}{r.mut}", "tool": tool}
                         for r in df.itertuples()] or None)

sap_h = pd.read_csv(find_prev("05_humanize_sapiens", "mutations_VH.csv", quiet=True))
sap_l = pd.read_csv(find_prev("05_humanize_sapiens", "mutations_VL.csv", quiet=True))

# Humatch — 내 결과에서 IMGT 로 재계산. 단 indel 이 난 체인은 raw 인덱스가 통째로 밀려
# 자리별 비교 자체가 성립하지 않아요 → 그 체인만 커밋된 IMGT 표를 씁니다(어느 쪽인지 아래에 출력).
hm_parts, hm_src = [], {}
ref_hmt = pd.read_csv(REF / "humatch_mutations_imgt.csv")
for chain, par_seq, cand_seq in (("H", VH, hm_h), ("L", VL, hm_l)):
    if len(par_seq) == len(cand_seq):
        hm_parts.append(to_imgt(pd.DataFrame(mutations(par_seq, cand_seq)), chain, "Humatch"))
        hm_src[chain] = "내 결과에서 재계산"
    else:
        sub = ref_hmt[ref_hmt.chain == chain]
        hm_parts.append(pd.DataFrame([{"chain": chain, "imgt": r.imgt_position, "wt": r.wt, "mut": r.mut,
                                       "sub": f"{r.wt}{r.mut}", "tool": "Humatch"} for r in sub.itertuples()]))
        hm_src[chain] = f"레퍼런스 IMGT 표(indel {len(par_seq)}→{len(cand_seq)} aa 라 raw 비교 불가)"
print("Humatch mutation 출처 —", " · ".join(f"{k}: {v}" for k, v in hm_src.items()))

tbl = pd.concat([
    to_imgt(sap_h, "H", "Sapiens"), to_imgt(sap_l, "L", "Sapiens"),
    to_imgt(ab_mut_h, "H", "AnthroAb_best_score"), to_imgt(ab_mut_l, "L", "AnthroAb_best_score"),
    to_imgt(mk_mut_h, "H", "AnthroAb_masked"), to_imgt(mk_mut_l, "L", "AnthroAb_masked"),
] + hm_parts, ignore_index=True)
tbl.to_csv(MY / "mutations_by_tool_imgt.csv", index=False)

def consensus(anthroab_mode):
    keep = tbl[tbl.tool.isin(["Sapiens", "Humatch", anthroab_mode])]
    out = []
    for (chain, pos), sub in keep.groupby(["chain", "imgt"]):
        if len(set(sub.tool)) == 3:
            out.append({"chain": chain, "imgt": pos, "subs": "/".join(sorted(set(sub["sub"]))),
                        "동일 치환": len(set(sub["sub"])) == 1})
    return pd.DataFrame(out).sort_values(["chain", "imgt"])

cons, counts = {}, {}
for mode in ["AnthroAb_best_score", "AnthroAb_masked"]:
    cs = consensus(mode)
    ident = cs[cs["동일 치환"]]
    cons[mode], counts[mode] = cs, (len(cs), len(ident))
    cs.to_csv(MY / f"three_way_consensus_{mode}.csv", index=False)
    print(f"\\n=== Sapiens · Humatch · {mode} ===")
    print(f"세 도구가 모두 건드린 위치 {len(cs)}개 · 그중 동일 치환 {len(ident)}개")
    display(cs)
    split = cs[~cs["동일 치환"]]
    if len(split):
        print("   갈린 자리:", ", ".join(f"{r.imgt} {r.subs}" for r in split.itertuples()))'''),

md("""## 6) 내 결과 확인 — 합의 개수는 **어느 모드로 비교했느냐**에 달려 있어요

같은 세 도구인데 AnthroAb 를 `best_score` 로 놓느냐 `masked` 로 놓느냐에 따라 합의 목록이 바뀌어요.
그래서 합의를 인용할 때는 **개수만이 아니라 모드까지** 함께 적어야 해요.

지도는 `masked` 모드 기준으로 그려요. 금색 배경 + 빨간 테두리가 **세 도구 동일 치환**입니다."""),
co('''from humanization_viz import mutation_map
from IPython.display import Image, display

vh = tbl[(tbl.chain == "H") & (tbl.tool.isin(["Sapiens", "Humatch", "AnthroAb_masked"]))].copy()
vh = vh[vh["imgt"].str[1:].str.isdigit()]           # 'L127_tail1' 처럼 IMGT 범위 밖 라벨은 제외
vh["position"] = vh["imgt"].str[1:].astype(int)
pos3 = sorted(p for p, n in vh.groupby("position")["tool"].nunique().items() if n == 3)
rows = [{"position": r.position, "tool": r.tool, "to": r.mut}
        for r in vh.itertuples() if r.position in pos3]

# CDR 보호 구간도 데이터에서 — CDR 표(raw) → IMGT 경계로 변환
cdr_spans = []
for _, r in ct[ct.chain == "H"].iterrows():
    st = VH.find(r["sequence"]) + 1
    lo, hi = r2i["H"][st], r2i["H"][st + len(r["sequence"]) - 1]
    cdr_spans.append((int(lo[1:]), int(hi[1:])))
in_cdr = [p for p in pos3 if any(lo <= p <= hi for lo, hi in cdr_spans)]

png = mutation_map(rows, "3-tool proposals on VH (IMGT) — 금색 = 세 도구 동일 치환",
                   MY / "06_mutation_map.png",
                   cdr_spans=cdr_spans if in_cdr else None)   # 그릴 게 없으면 범례도 띄우지 않아요
print("CDR(IMGT) 구간:", ", ".join(f"H{lo}~H{hi}" for lo, hi in cdr_spans))
print(f"세 도구가 함께 건드린 VH 위치 {len(pos3)}개 중 CDR 안 {len(in_cdr)}개 — 합의는 전부 framework 에서 났어요.")
display(Image(str(png)))

h86 = vh[vh.position == 86][["tool", "wt", "mut"]]
n_touch, n_same = counts["AnthroAb_masked"]
if len(h86):
    print("\\nIMGT H86 (= raw I78T) 에 대한 세 도구의 제안")
    display(h86)
    agreed = len(h86) == 3 and len(set(h86["mut"])) == 1
    print(f"판정 — masked 모드 합의 {n_same}/{n_touch}. H86 은 "
          + (f"세 도구가 모두 {h86.iloc[0]['wt']}→{h86.iloc[0]['mut']} 로 모인 자리라 backmutation 우선순위에서 가장 뒤로 밀 수 있어요."
             if agreed else "세 도구가 갈린 자리라 합의로 세지 않아요."))
else:
    print(f"\\n판정 — masked 모드 합의 {n_same}/{n_touch}. 이 서열에서는 H86 을 세 도구가 함께 건드리지 않았어요.")
split = cons["AnthroAb_masked"]
split = split[~split["동일 치환"]]
if len(split):
    print("        제안 잔기가 갈린 자리(" + ", ".join(split["imgt"]) + ")는 합의로 세지 않아요.")'''),

md("""## 7) 레퍼런스 대조"""),
co('''# keep_default_na=False — 치환 표기 'NA'(Asn→Ala)가 결측(NaN)으로 읽히는 것을 막아요
ref_cs = pd.read_csv(REF / "three_way_consensus.csv", keep_default_na=False)
MODE_KEY = {"AnthroAb_best_score": "best_score_full_argmax", "AnthroAb_masked": "masked_FR_only"}
REF_CMP  = {"AnthroAb_best_score": "Sapiens x AnthroAb_best_score",
            "AnthroAb_masked": "Sapiens x AnthroAb_masked_FRonly"}

for mode, key in MODE_KEY.items():
    sub = ref_cs[ref_cs.anthroab_mode == key]
    ref_pair = (len(sub), int(sub.identical_substitution_all3.sum()))
    my_pair = counts[mode]
    print(f"{key:24s} 레퍼런스 건드린 위치 {ref_pair[0]:2d} · 동일 치환 {ref_pair[1]:2d}   "
          f"내 결과 {my_pair[0]:2d} · {my_pair[1]:2d}  → {'일치' if ref_pair == my_pair else '차이'}")

display(ref_cs[ref_cs.identical_substitution_all3][["anthroab_mode", "chain", "imgt_position",
                                                    "sapiens_mut", "humatch_mut", "anthroab_mut"]])

# Sapiens × AnthroAb 겹침 — 내 표에서 직접 세고 레퍼런스와 맞춰요
# (overlap_summary.csv 의 note 컬럼은 6행 중 4행이 비어 있어 표에서 뺐어요)
ov_rows = []
for mode in ["AnthroAb_best_score", "AnthroAb_masked"]:
    for scope, sel in (("VH only", tbl.chain == "H"), ("VL only", tbl.chain == "L"),
                       ("VH+VL combined", tbl.chain.notna())):
        s = tbl[sel]
        ov_rows.append({"comparison": REF_CMP[mode], "chain_scope": scope,
                        "겹친 위치(내 결과)": len(set(s[s.tool == "Sapiens"].imgt)
                                              & set(s[s.tool == mode].imgt))})
ref_ov = pd.read_csv(REF / "overlap_summary.csv").rename(columns={"n_positions": "겹친 위치(레퍼런스)"})
ov = pd.DataFrame(ov_rows).merge(ref_ov[["comparison", "chain_scope", "겹친 위치(레퍼런스)"]],
                                 on=["comparison", "chain_scope"], how="left")
display(ov)
lo, hi = int(ov["겹친 위치(내 결과)"].min()), int(ov["겹친 위치(내 결과)"].max())
print(f"판정 — 같은 두 도구인데 겹침이 {lo}~{hi} 로 흔들려요. "
      "체인 범위와 AnthroAb 모드를 함께 적지 않은 겹침 숫자는 재현되지 않아요.")'''),

md("""## 이 랩에서 확인한 것

1. **Humatch** — config 가 `allow_CDR_mutations=False`·CNN 목표 **0.95**·GL 목표 **0.4** 를 선언하고, 산출물이 그대로 따라와요(CNN_H **0.972** · CNN_L **1.000** · gene **hv1/lv2** · edit **20** · CDR 변경 **0개**). VL 은 1 잔기 **삭제**(indel) 라 도구 간 비교는 IMGT 로.
2. **AnthroAb** — `predict_best_score` 는 CDR 을 **안 지켜요**. `predict_masked` 는 1.1.0 에서 깨져 있어(vocab 에 `*` 없음 → 토큰 밀림) `input_ids` 를 직접 만들어야 하고, 여기서는 본문 6.2.5 등급표를 무시한 **FR 전체 마스킹**으로 상한선을 봤어요.
3. **3도구 합의(실측)** — `best_score` 기준 건드린 위치 **7 · 동일 치환 7**, `masked` 기준 건드린 위치 **12 · 동일 치환 10**. 차이는 H45(`R→A` vs `R→P`)·H68(`N→A` vs `N→P`) 두 자리예요.
4. `I78T`(IMGT **H86**)는 `masked` 비교에서 세 도구가 모두 `I→T` 로 모인 자리이고, `best_score` 비교에서는 AnthroAb 가 이 자리를 아예 건드리지 않아 목록에 없어요. **합의 개수는 모드와 함께 적어야** 재현돼요.
5. 모델 덩치도 축이 달라요 — AnthroAb VH 는 **12층 · hidden 768 · 약 85M** 파라미터로, 같은 API 의 Sapiens(4층 · 128 · 약 0.5M) 와는 다른 체급이에요.

다음 → **[Ch.07 — Nativeness](../07_nativeness/07_nativeness_lab.ipynb)**"""),
]
cells_all[("06_cdr_safe_tools", "06_tools_lab.ipynb", "06 CDR-safe Tools Lab")] = c


# ════════════════════════════════════════════════════════════════════════════
# 07 — nativeness / naturalness
# ════════════════════════════════════════════════════════════════════════════
c = [title_cell("07", "Nativeness · Naturalness — AbNatiV · Ab-RoBERTa", "07_nativeness.md",
                prev="Ch.04 · Ch.05 · Ch.06")]
c += boot("07_nativeness", pip="pandas matplotlib torch transformers")
c += [
md("""## 1) 직접 실행 — Ab-RoBERTa pseudo-likelihood (본문 7.2.1)

항체 전용 언어모델 `mogam-ai/Ab-RoBERTa` 로 각 position 을 차례로 `<mask>` 로 가리고, **그 자리에 있던 진짜 잔기의 로그확률**을 모아 평균해요(masked pseudo-log-likelihood). 결과 CSV 는 `variant · chain · mean_logp · perplexity · n_residues` 다섯 컬럼이에요.

- `mean_logp` — 마스킹한 자리의 평균 로그확률. **높을수록** 자연스러움
- `perplexity = exp(-mean_logp)` — 같은 값을 뒤집어 본 것. **낮을수록** 좋음
- `chain` — `VH` · `VL` 각각과, 둘을 **길이가중 평균**한 `paired`. 비교는 `paired` 로 해요

스코어링 스크립트는 이 챕터 폴더에 함께 실려 있어요 — `score_abroberta_pseudolikelihood.py`.

```bash
python score_abroberta_pseudolikelihood.py --fasta variants.fasta --out scores.csv
```

후보는 **앞 랩에서 내가 만든 것**을 먼저 씁니다(Ch.05 Sapiens · Ch.06 Humatch/AnthroAb). 빠진 후보만 `data/variants.fasta` 로 채워요 —
이 노트북의 모든 표는 `my_run/` 을 먼저 찾고 없으면 `data/` 로 폴백하며, 어느 쪽을 썼는지 그때그때 print 합니다."""),
co('''import pandas as pd

PREV = [
    ("05_humanize_sapiens", "sapiens_humanized_noguard.fasta", ("sapiens_humanized_VH", "sapiens_humanized_VL"), "sapiens"),
    ("06_cdr_safe_tools",   "humatch_humanised.fasta",         ("humatch_humanised_VH", "humatch_humanised_VL"), "humatch"),
    ("06_cdr_safe_tools",   "anthroab_best_score.fasta",       ("anthroab_bestscore_VH", "anthroab_bestscore_VL"), "anthroab"),
    ("06_cdr_safe_tools",   "anthroab_masked_FRonly.fasta",    ("anthroab_masked_VH", "anthroab_masked_VL"), "anthroabFRmasked"),
]

cands, SRC = {"parental": (VH, VL)}, {"parental": "data/parental.fasta"}
for chapter, fname, keys, label in PREV:
    p = GUIDE_ROOT / chapter / "my_run" / fname
    if p.exists():
        f = read_fasta(p)
        if keys[0] in f and keys[1] in f:
            cands[label], SRC[label] = (f[keys[0]], f[keys[1]]), f"내 결과 · {chapter}/my_run/{fname}"

need = [lab for *_, lab in PREV if lab not in cands]      # 빠진 후보만 레퍼런스로 채워요
if need:
    vp = find_one("variants.fasta", quiet=True)
    v = read_fasta(vp)
    for lab in need:
        cands[lab], SRC[lab] = (v[f"{lab}_VH"], v[f"{lab}_VL"]), f"레퍼런스 · {vp}"

for k in cands:
    print(f"  {k:18s} VH {len(cands[k][0]):3d} aa · VL {len(cands[k][1]):3d} aa  ← {SRC[k]}")

fa = write_fasta(MY / "variants.fasta",
                 {f"{n}_{ch}": s for n, (h, l) in cands.items() for ch, s in (("VH", h), ("VL", l))})
print(f"\\n후보 {len(cands)}종 →", fa)'''),
co('''t0, rows, abr = time.time(), [], None
try:
    # import 도 try 안에 둬요 — torch/transformers 가 어긋나면 여기서 끊고 레퍼런스로 이어가야
    # 뒤 셀들이 연쇄로 죽지 않아요.
    from score_abroberta_pseudolikelihood import score_paired
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
    print(f"\\nAb-RoBERTa 스코어링 {time.time()-t0:.1f}초 (실측 70초 · 5후보 × VH+VL) →",
          MY / "abroberta_scores_summary.csv")
except Exception as e:
    print("Ab-RoBERTa 실행 실패:", type(e).__name__, str(e)[:200])
    print("모델 다운로드가 막힌 거라면 셀을 다시 실행하면 이어받아요. 지금은 레퍼런스로 진행해요.")

if abr is None:
    abr = pd.read_csv(find_one("abroberta_scores_summary.csv"))

rank = abr[abr.chain == "paired"].sort_values("mean_logp", ascending=False)
print("\\npaired 순위(자연스러운 순) —",
      " > ".join(f"{r.variant} {r.mean_logp:+.4f}" for r in rank.itertuples()))'''),

md("""## 2) 내 결과 확인 — perplexity 로 자르기 (본문 7.2.2)

`paired` 는 VH·VL 을 길이로 가중한 값이라 체인 하나가 무너져도 절반쯤 희석돼요. 그래서 **체인별 값을 먼저 펼쳐 놓고** paired 를 봐요.

판정은 절대값이 아니라 **parental 대비 배수**로 합니다. 항체마다 서열 자체의 난이도가 달라서, 같은 파이프라인 안의 parental 이 가장 정직한 기준선이거든요."""),
co('''def keep_cols(df, wanted):
    """있는 컬럼만 골라내요 — 하드코딩한 목록을 그대로 넘기면 KeyError 로 죽어요."""
    return [x for x in wanted if x in df.columns]

pv  = abr.pivot_table(index="variant", columns="chain", values="mean_logp")
ppl = abr[abr.chain == "paired"].set_index("variant")["perplexity"]
order = [n for n in cands if n in pv.index] or list(pv.index)

tbl = pv.reindex(order)[keep_cols(pv, ["VH", "VL", "paired"])].round(4)
tbl["perplexity(paired)"] = ppl.reindex(order).round(4)
display(tbl)

vh = pv["VH"].dropna().sort_values(ascending=False)
print(f"VH 만 보면 가장 자연스러운 후보는 {vh.index[0]} ({vh.iloc[0]:+.4f}) 이에요.")
if vh.index[0] == "parental":
    print("사람다움을 올린 편집이 VH 의 자연스러움은 깎았어요 — humanness 와 naturalness 는 다른 축이에요.")

base = float(ppl["parental"]) if "parental" in ppl.index else float(ppl.median())
print(f"\\n기준선 parental paired perplexity {base:.4f} · 이번 실행의 paired 범위 "
      f"{ppl.min():.4f}~{ppl.max():.4f}")
print("컷오프 — 1.0배 이하 통과 · 1.0~2.0배 주의 · 2.0배 이상이면 서열이 무너진 신호로 봐요.")
warn = []
for n in order:
    r = float(ppl[n]) / base
    v_ = "통과" if r <= 1.0 else ("주의" if r < 2.0 else "★경고")
    if r >= 2.0:
        warn.append(n)
    print(f"  {n:18s} ppl {float(ppl[n]):.4f} · parental 대비 {r:.2f}배 → {v_}")
print("\\n판정 —", ("2.0배를 넘긴 후보 " + ", ".join(warn) + " 는 naturalness 축에서 먼저 걸러요."
                  if warn else "2.0배를 넘긴 후보가 없어 naturalness 축에서 즉시 탈락하는 후보는 없어요."))'''),
co('''from humanization_viz import humanness_bars
from IPython.display import Image, display
import numpy as np

# exp(mean_logp) = 잔기당 pseudo-likelihood 기하평균(0~1) → 막대로 보기 좋은 형태
others = [v for v in pv.index if v != "parental"]
pick = "sapiens" if "sapiens" in others else others[0]
CH = keep_cols(pv, ["VH", "VL", "paired"])
bars = [{"chain": ch, "parental": float(np.exp(pv.loc["parental", ch])),
         "humanized": float(np.exp(pv.loc[pick, ch]))} for ch in CH]
png = humanness_bars(bars, f"Ab-RoBERTa naturalness — parental vs {pick} (exp(mean logP))",
                     MY / "07_naturalness.png", ylabel="per-residue pseudo-likelihood")
display(Image(str(png)))

up   = [ch for ch in CH if pv.loc[pick, ch] > pv.loc["parental", ch]]
down = [ch for ch in CH if pv.loc[pick, ch] <= pv.loc["parental", ch]]
print(f"판정 — {pick} 는 {', '.join(up) or '없음'} 에서 parental 보다 자연스러워졌고, "
      f"{', '.join(down) or '없음'} 에서는 내려갔어요.")
print("체인 하나만 내려가도 paired 는 올라갈 수 있어요. naturalness 는 paired 만 보지 말고 체인별로 확인하세요.")'''),

md("""## 3) 직접 실행 — AbNatiV nativeness (본문 7.1.1~7.1.2) · **기본 비활성**

AbNatiV 는 "사람 잔기를 얼마나 썼나"(humanness)가 아니라 **"그 조합이 실제 사람 항체로서 얼마나 자연스러운가"**(nativeness)를 봐요.

설치는 한 줄인데 **두 번 막혀요.**

```bash
conda create -n abnativ -c conda-forge python=3.10 -y && conda activate abnativ
python -m pip install abnativ            # abnativ 2.0.8 (ImmuneBuilder 동반)
abnativ init                             # 함정① 체크포인트(모델당 약 1GB) — 안 받으면 score 가 FileNotFoundError: .../pretrained_models/vh_model.ckpt
conda install -c bioconda -c conda-forge anarci hmmer -y   # 함정② -align 이 anarci 를 import (Humatch 와 같은 에러)
```

옵션 두 개도 짚고 가요 — **`-align`** 은 ANARCI 로 번호를 매겨 FR·CDR 구간을 나눠 주고(그래서 anarci·hmmscan 이 필요), **`-mean`** 은 잔기별 점수를 서열당 한 값으로 접어 줘요. 이 분해 덕분에 overall 뿐 아니라 FR·CDR 을 따로 볼 수 있어요.

**스코어링 자체는 4서열에 3.5~6.6초로 끝나요.** 무거운 건 체크포인트예요 — `abnativ init` 은 9개 ckpt(~6GB)를 **순차로** 받아 매우 느리고(실측 30분에 3개), 실제로 쓰는 4개만 **병렬로** 받아도 **약 33분 / 2.6GB**(실측)예요.

그래서 아래 셀은 **`RUN_ABNATIV = False` 가 기본**입니다. `True` 로 바꾸면 받은 결과를 `my_run/abnativ_summary_all_models.csv` 로 합쳐 두고, 다음 절이 그걸 먼저 집어요."""),
co('''import re

RUN_ABNATIV = False        # ← True 로 바꾸면 체크포인트를 받아 실제로 스코어링해요

# (nat 이름, 입력 fasta, oid, ckpt 파일명)
ABN_MODELS = [("VH", "abnativ_vh.fa", "vh", "vh_model"), ("VLambda", "abnativ_vl.fa", "vl", "vlambda_model"),
              ("VH2", "abnativ_vh.fa", "vh2", "vh2_model"), ("VL2", "abnativ_vl.fa", "vl2", "vl2_model")]

def abnativ_merge(outdir):
    """abnativ 가 남긴 *_seq_scores.csv 들을 summary 한 장으로. 모델·세대는 파일명이 아니라
    컬럼 이름('AbNatiV VH2 Score')에서 읽어요 — oid 를 어떻게 주든 안 깨지게."""
    out = []
    for p in sorted(pathlib.Path(outdir).glob("*_seq_scores.csv")):
        d = pd.read_csv(p)
        hit = [re.match(r"AbNatiV (\\w+) Score$", x) for x in d.columns]
        m = next((h.group(1) for h in hit if h), None)
        if m is None:
            continue
        for rec in d.to_dict("records"):
            out.append({"model_generation": "AbNatiV2" if m.endswith("2") else "AbNatiV1",
                        "abnativ_model": m, "variant": rec.get("seq_id"),
                        "overall_score": rec.get(f"AbNatiV {m} Score"),
                        "FR_score":   rec.get(f"AbNatiV FR-{m} Score"),
                        "CDR1_score": rec.get(f"AbNatiV CDR1-{m} Score"),
                        "CDR2_score": rec.get(f"AbNatiV CDR2-{m} Score"),
                        "CDR3_score": rec.get(f"AbNatiV CDR3-{m} Score")})
    return pd.DataFrame(out)

if RUN_ABNATIV:
    try:
        _ensure("abnativ anarci")
        if IN_COLAB and not shutil.which("hmmscan"):
            _run("apt-get -qq install -y hmmer", check=False)      # -align → anarci → hmmscan
        home = pathlib.Path.home() / ".abnativ/models/pretrained_models"
        home.mkdir(parents=True, exist_ok=True)
        base_url = "https://zenodo.org/record/17295347/files"
        need = [ck for *_, ck in ABN_MODELS if not (home / f"{ck}.ckpt").exists()]
        if need:   # 순차 abnativ init 대신 필요한 것만 병렬로. 멈춤은 예외가 안 나니 타임아웃·재시도 필수
            par = " ".join(f'wget -c -q --timeout=30 --tries=3 -O "{home}/{ck}.ckpt" '
                           f'"{base_url}/{ck}.ckpt?download=1" &' for ck in need)
            _run(f"({par} wait)", check=False)
            miss = [ck for ck in need if not (home / f"{ck}.ckpt").exists()]
            assert not miss, f"체크포인트를 못 받았어요 {miss} — 셀을 다시 실행하면 -c 로 이어받아요."

        write_fasta(MY / "abnativ_vh.fa", {f"{n}_VH": h for n, (h, l) in cands.items()})
        write_fasta(MY / "abnativ_vl.fa", {f"{n}_VL": l for n, (h, l) in cands.items()})
        t0 = time.time()
        for nat, fa_in, oid, _ck in ABN_MODELS:
            _run(f'CUDA_VISIBLE_DEVICES="" abnativ score -nat {nat} -i "{MY/fa_in}" '
                 f'-odir "{MY/"abnativ"}" -oid {oid} -align -ncpu 4')
        print(f"AbNatiV 스코어링 {time.time()-t0:.1f}초 (실측 3.5~6.6초/모델)")

        merged = abnativ_merge(MY / "abnativ")
        if len(merged):
            merged.to_csv(MY / "abnativ_summary_all_models.csv", index=False)
            print(f"세대 {merged.model_generation.nunique()}종 · {len(merged)}행 합쳤어요 →",
                  MY / "abnativ_summary_all_models.csv")
        else:
            print("*_seq_scores.csv 를 못 찾았어요 — 다음 절은 커밋된 레퍼런스로 이어가요.")
    except Exception as e:
        print("AbNatiV 실행 실패:", type(e).__name__, str(e)[:200])
        print("다음 절은 커밋된 레퍼런스로 이어가요.")
else:
    print("RUN_ABNATIV = False → 커밋된 레퍼런스로 진행해요.")
    print("스코어링은 3.5~6.6초로 빠르지만 체크포인트가 약 33분 / 2.6GB 예요(실측).")'''),

md("""## 4) 내 결과 / 레퍼런스 — 두 세대를 나란히 (본문 7.1.3 · 7.2.3)

AbNatiV 에는 **세대가 둘**이고, 본문의 두 표는 서로 다른 모델이에요. 세대를 섞으면 같은 후보인데 숫자가 모순돼 보여요.

| 세대 | 옵션 | 본문 |
|---|---|---|
| AbNatiV1 | `-nat VH` / `-nat VLambda` | 7.1.3 표 |
| AbNatiV2 | `-nat VH2` / `-nat VL2` | 7.2.3 표의 AbNatiV2 열 |

두 세대를 **같은 후보 집합으로 나란히** 그려서, 무엇이 세대 차이이고 무엇이 후보 차이인지 갈라 봐요."""),
co('''abn = pd.read_csv(find_one("abnativ_summary_all_models.csv"))

SCORES = ["overall_score", "FR_score", "CDR1_score", "CDR2_score", "CDR3_score"]

def cand_of(v):
    """'sapiens_humanized_VH' · 'sapiens_VH' 어느 표기든 후보 키로."""
    s = re.sub(r"_(VH|VL)$", "", str(v))
    return s if s in cands else s.split("_")[0]

abn["candidate"] = abn.variant.map(cand_of)
abn["chain"] = abn.variant.map(lambda v: "VH" if str(v).endswith("_VH") else "VL")

for gen, sub in abn.groupby("model_generation"):
    print(f"=== {gen} ===")
    display(sub[keep_cols(sub, ["abnativ_model", "variant"] + SCORES)].round(4).reset_index(drop=True))

def val(gen, chain, cand, col):
    s = abn[(abn.model_generation == gen) & (abn.chain == chain) & (abn.candidate == cand)]
    return float(s.iloc[0][col]) if len(s) else float("nan")

ref_cand = "sapiens" if "sapiens" in set(abn.candidate) else sorted(set(abn.candidate) - {"parental"})[0]
print(f"\\nAbNatiV1 VH  parental → {ref_cand}")
deltas = {}
for col, lab in (("overall_score", "overall"), ("FR_score", "FR    "), ("CDR3_score", "CDR-H3")):
    a, b = val("AbNatiV1", "VH", "parental", col), val("AbNatiV1", "VH", ref_cand, col)
    deltas[lab.strip()] = b - a
    print(f"  {lab}  {a:.4f} → {b:.4f}  (Δ {b-a:+.4f})")
vl_par, vl_ref = val("AbNatiV1", "VL", "parental", "overall_score"), val("AbNatiV1", "VL", ref_cand, "overall_score")
print(f"AbNatiV1 VL(lambda) parental {vl_par:.4f} → {ref_cand} {vl_ref:.4f}")
print(f"판정 — overall 상승분 {deltas['overall']:+.4f} 중 FR 이 {deltas['FR']:+.4f}, CDR-H3 가 {deltas['CDR-H3']:+.4f} 예요. "
      + ("상승이 FR 에 몰린 'framework 만 사람화' 프로파일이에요." if deltas["FR"] > deltas["CDR-H3"]
         else "상승이 FR 밖에서도 나왔어요 — CDR 쪽 변화를 서열로 확인하세요."))
print(f"VL 은 parental 이 이미 {vl_par:.4f} 라 올릴 여지가 {1-vl_par:.4f} 밖에 없어요.")

neg = abn[(abn[keep_cols(abn, SCORES)] < 0).any(axis=1)]
if len(neg):
    print(f"\\nAbNatiV2 는 CDR 점수가 음수로 내려가요 — 음수가 든 행 {len(neg)}개 · 최소값 "
          f"{abn[keep_cols(abn, SCORES)].min().min():.4f}")
    display(neg[keep_cols(neg, ["model_generation", "variant", "CDR1_score", "CDR2_score", "CDR3_score"])].round(4))
    print("짧은 CDR 은 정렬 구간이 좁아 세대마다 스케일이 크게 달라져요. **세대 간 비교는 overall 열로만** 하세요.")'''),
co('''# CDR-H3 에 실제로 변이가 들어갔는지는 점수가 아니라 서열로 확인해요
ct = pd.read_csv(find_prev("04_sequence_qc", "cdr_table_imgt.csv",
                           ref=GUIDE_ROOT / "04_sequence_qc" / "data", quiet=True))
h3 = ct[(ct.chain == "H") & (ct.cdr == "CDR3")].iloc[0]["sequence"]
st = VH.find(h3) + 1
assert st > 0, "CDR-H3 를 parental VH 에서 못 찾았어요 — cdr_table 과 parental.fasta 가 어긋나요."
en = st + len(h3) - 1

SEQ_COL = f"CDR-H3 (raw {st}~{en})"
par_h3 = val("AbNatiV1", "VH", "parental", "CDR3_score")
recs = [{"후보": "parental", SEQ_COL: h3, "변이": "-", "n_mut": 0, "AbNatiV1 CDR-H3": par_h3}]
for name, (h, l) in cands.items():
    if name == "parental" or len(h) != len(VH):
        continue
    muts = [f"{a}{i+1}{b}" for i, (a, b) in enumerate(zip(VH, h)) if a != b and st <= i + 1 <= en]
    recs.append({"후보": name, SEQ_COL: h[st-1:en], "변이": ", ".join(muts) or "-", "n_mut": len(muts),
                 "AbNatiV1 CDR-H3": val("AbNatiV1", "VH", name, "CDR3_score")})
h3tbl = pd.DataFrame(recs)
display(h3tbl.round(4))

moved = h3tbl[(h3tbl["n_mut"] > 0) & h3tbl["AbNatiV1 CDR-H3"].notna()]
for _, r in moved.iterrows():
    print(f"{r['후보']:18s} CDR-H3 변이 {int(r['n_mut'])}개 ({r['변이']}) · "
          f"점수 {par_h3:.4f} → {r['AbNatiV1 CDR-H3']:.4f} (Δ {r['AbNatiV1 CDR-H3']-par_h3:+.4f})")
if len(moved):
    big = float((moved["AbNatiV1 CDR-H3"] - par_h3).abs().max())
    print(f"\\n판정 — CDR-H3 에 변이가 들어간 후보가 {len(moved)}개인데 점수 변화는 최대 {big:.4f} 예요.")
else:
    print("\\n판정 — 이 후보 집합에서는 CDR-H3 에 들어간 변이가 없어요.")
print("CDR 점수가 평평하다고 해서 CDR 을 안 건드렸다는 뜻이 아니에요. 변이 여부는 반드시 서열로 확인하세요.")
print("구조가 실제로 얼마나 움직였는지는 Ch.08 의 CDR-H3 RMSD 로 따로 봐요.")'''),
co('''from humanization_viz import nativeness_panel
from IPython.display import Image, display

pngs, ranks = [], {}
for gen in [g for g in ["AbNatiV1", "AbNatiV2"] if g in set(abn.model_generation)]:
    sub = abn[(abn.model_generation == gen) & (abn.chain == "VH")]
    rows = [{"label": r.candidate, "overall": r.overall_score, "fr": r.FR_score,
             # 음수 CDR 은 그리지 않아요 — 패널 y축이 0~1.05 라 잘려서 0 처럼 보여요
             "cdr": r.CDR3_score if r.CDR3_score == r.CDR3_score and r.CDR3_score >= 0 else None}
            for r in sub.itertuples()]
    p = nativeness_panel(rows, f"{gen} VH nativeness — overall / FR / CDR-H3",
                         MY / f"07_nativeness_{gen.lower()}.png")
    pngs.append(p)
    ranks[gen] = list(sub.sort_values("overall_score", ascending=False).candidate)

for p in pngs:
    display(Image(str(p)))
for gen, o in ranks.items():
    print(f"{gen} VH overall 순위 —", " > ".join(o))
if len(ranks) == 2:
    a, b = ranks["AbNatiV1"], ranks["AbNatiV2"]
    print("판정 — 두 세대의 1위는 " + ("같지만" if a[0] == b[0] else "다르고") +
          (" 나머지 순위가 뒤집혀요." if a != b else " 순위도 같아요."))
    print("세대가 다르면 값의 스케일도 순위도 달라져요. AbNatiV 점수는 **세대 표기와 함께** 인용하세요.")'''),

md("""## 5) 세 축을 한 표에 — humanness · nativeness · naturalness (본문 7.2.3)

셋은 서로 다른 것을 재요.

| 축 | 지표 | 무엇을 보나 |
|---|---|---|
| humanness | Humatch CNN (H/L) | 사람 germline 계열로 분류되나 |
| nativeness | AbNatiV2 (VH2/VL2) | 자연 사람 레퍼토리에 들어맞나 |
| naturalness | Ab-RoBERTa paired | 언어모델이 이 서열을 자연스럽다고 보나 |

Humatch CNN 은 **자기 산출물에만 붙는 자체 점수**라 다른 후보 칸은 비어요(본문 7.2.3 표와 같아요). OASis 백분위는 수십 GB OAS DB 가 필요해 이 환경에서 재현할 수 없어 뺐고, 그 자리는 Ch.05 Sapiens 확률로 봐요."""),
co('''# humanness — 내 Humatch 실행 결과가 있으면 그것, 없으면 커밋된 config 표
hm_out = GUIDE_ROOT / "06_cdr_safe_tools" / "my_run" / "humatch_out.csv"
if hm_out.exists():
    r0 = pd.read_csv(hm_out).iloc[0]
    cnn_h, cnn_l = float(r0["CNN_H"]), float(r0["CNN_L"])
    print(f"[내 결과 · 06_cdr_safe_tools] {hm_out}")
else:
    cfg = pd.read_csv(find_prev("06_cdr_safe_tools", "humatch_scores.csv",
                                ref=GUIDE_ROOT / "06_cdr_safe_tools" / "data")).set_index("metric")["value"]
    cnn_h, cnn_l = float(cfg["CNN_H"]), float(cfg["CNN_L"])

# CNN 이 안 붙는 후보의 humanness 는 Ch.05 Sapiens 확률로 봐요(본문 7.2.3 이 OASis 를 뺀 자리)
try:
    hs = pd.read_csv(find_prev("05_humanize_sapiens", "humanness_summary.csv",
                               ref=GUIDE_ROOT / "05_humanize_sapiens" / "data", quiet=True))
    hs = hs.set_index(["chain", "definition"])["mean_probability"]
    for chn in ("VH", "VL"):
        print(f"Sapiens humanness (Ch.05) {chn} — parental {hs[(chn, 'parental')]:.4f} → "
              f"humanized {hs[(chn, 'definition_b_rescored_humanized')]:.4f}")
except Exception as e:
    print("Ch.05 humanness 표를 못 읽었어요:", type(e).__name__, str(e)[:120])

abn2 = abn[abn.model_generation == "AbNatiV2"].pivot_table(index="candidate", columns="chain",
                                                           values="overall_score")
def gen_col(df, name):
    """세대나 체인이 통째로 빠져도 KeyError 로 죽지 않게."""
    return df[name] if name in getattr(df, "columns", []) else pd.Series(dtype=float)

abr_p = abr[abr.chain == "paired"].copy()
abr_p["candidate"] = abr_p.variant.map(cand_of)
abr_p = abr_p.set_index("candidate")["mean_logp"]

idx = [n for n in cands if n in abr_p.index]
panel = pd.DataFrame({
    "Humatch CNN H/L (humanness↑)": ["%.3f / %.3f" % (cnn_h, cnn_l) if n == "humatch" else "—" for n in idx],
    "AbNatiV2 VH (nativeness↑)": [gen_col(abn2, "VH").get(n, float("nan")) for n in idx],
    "AbNatiV2 VL (nativeness↑)": [gen_col(abn2, "VL").get(n, float("nan")) for n in idx],
    "Ab-RoBERTa paired (naturalness↑)": [abr_p.get(n, float("nan")) for n in idx],
}, index=idx).round(4)

nat_cols = keep_cols(panel, ["AbNatiV2 VH (nativeness↑)", "AbNatiV2 VL (nativeness↑)"])
drop = [n for n in panel.index if panel.loc[n, nat_cols].isna().any()]
if drop:
    print("AbNatiV 점수가 없는 후보는 표에서 뺐어요 —", ", ".join(drop),
          "(AbNatiV 를 이 후보까지 돌리면 채워져요)")
panel = panel.drop(index=drop)
display(panel)

if "parental" in panel.index and len(panel) > 1:
    nat, natu = panel[nat_cols[0]], panel["Ab-RoBERTa paired (naturalness↑)"]
    b_nat, b_natu = float(nat["parental"]), float(natu["parental"])
    outliers = [n for n in panel.index
                if n != "parental" and float(nat[n]) > b_nat and float(natu[n]) < b_natu]
    print(f"\\n이상치 규칙 — parental 대비 nativeness 는 올랐는데(> {b_nat:.4f}) "
          f"naturalness 는 내려간(< {b_natu:.4f}) 후보")
    for n in outliers:
        print(f"  ★ {n}  nativeness {float(nat[n])-b_nat:+.4f} · naturalness {float(natu[n])-b_natu:+.4f}")
    print("판정 —", (", ".join(outliers) + " 가 이상치예요. 주 패널(Humatch CNN + AbNatiV2)은 통과시키지만 "
                    "Ab-RoBERTa 가 붙잡는 후보라, 실험 전에 한 번 더 들여다볼 자리예요."
                    if outliers else "주 패널과 Ab-RoBERTa 가 같은 방향을 가리켜 걸러낼 이상치가 없어요."))
else:
    print("\\n비교할 후보가 부족해요 — AbNatiV 를 후보 전체에 돌리면 이상치 판정이 켜져요.")
print("역할 분담 — 주 human-likeness 패널은 Humatch CNN + AbNatiV2, Ab-RoBERTa 는 이상치 탐지 보조예요.")'''),

md("""## 이 랩에서 확인한 것

1. **AbNatiV 는 세대를 구분해 적어요.** AbNatiV1 VH **0.6477 → 0.8803**(FR **0.6317 → 0.9245**), VL(lambda) parental **0.9022**. 같은 후보를 AbNatiV2 로 재면 VH **0.4927 → 0.7777** 로 스케일이 통째로 달라요.
2. **CDR-H3 점수가 평평해도 CDR 이 그대로인 건 아니에요.** Sapiens 후보는 CDR-H3 에 **L104D · Y109V 2개**를 넣었는데도 AbNatiV1 CDR-H3 는 **0.6137 → 0.6265**(Δ +0.0127) 로 거의 안 움직였어요. AnthroAb 도 **Y102S · Y109V 2개**에 Δ +0.0834 뿐이에요. 변이 여부는 **서열로** 확인하세요.
3. **AbNatiV2 의 CDR 점수는 음수가 나와요**(실측 최소 **−0.2564**). 구간이 짧을수록 세대별 스케일 차가 커지니 **세대 간 비교는 overall 열로만** 하세요.
4. **naturalness ≠ humanness** — VH 만 보면 parental(**−0.5188**)이 가장 자연스러워요. paired perplexity 는 **1.6444~4.1467** 범위이고 parental **2.0627** 이 기준선이에요. **2.0배**(FR-masked 후보)를 넘기면 서열이 무너진 신호예요.
5. **세 축을 한 표에** 놓으면 어긋나는 후보가 보여요 — humanness(Humatch CNN **0.972 / 1.000**)·nativeness(AbNatiV2)는 올랐는데 naturalness 만 내려간 후보가 Ab-RoBERTa 가 잡아내는 이상치예요.
6. 산출물 — `my_run/abroberta_scores_summary.csv` · `abnativ_summary_all_models.csv`(직접 실행 시) · `07_naturalness.png` · `07_nativeness_abnativ1.png` · `07_nativeness_abnativ2.png`.

다음 → **[Ch.08 — 구조 검증](../08_structure/08_structure_lab.ipynb)**"""),
]
cells_all[("07_nativeness", "07_nativeness_lab.ipynb", "07 Nativeness Lab")] = c


# ════════════════════════════════════════════════════════════════════════════
# 08 — 구조 (IgFold)
# ════════════════════════════════════════════════════════════════════════════
c = [title_cell("08", "구조 검증 — IgFold 로 직접 접고 6개 CDR RMSD 비교", "08_structure.md",
                prev="Ch.05 Sapiens 결과")]
c += boot("08_structure", pip="pandas matplotlib biopython py3Dmol gemmi")
c += [
md("""## 1) 직접 실행 — parental·humanized 를 다시 접기 (본문 8.1)

서열 지표가 전부 좋아져도 **CDR loop 모양이 망가지면 결합력은 사라져요.** 그래서 서열을 만든 도구(Sapiens)가 아니라 **그 사정을 전혀 모르는 모델**에게 다시 접게 해요. 만드는 쪽과 검증하는 쪽을 분리하는 거예요.

IgFold(+AntiBERTy)는 VH+VL Fv 하나를 CPU 로 접어요. 기본값으로 부르면 두 번 죽으니 아래 두 옵션을 꺼요.

| 옵션 | 왜 끄나 |
|---|---|
| `do_refine=False` | `True` 면 **PyRosetta** 를 요구하고, 없으면 그 자리에서 `exit()` 합니다 |
| `do_renum=False` | `True` 면 abnumber 로 재numbering 하는데, 우리 VL 의 C-말단 `G` 가 IMGT 범위 밖이라 **AssertionError** 로 죽어요 |

스레드도 묶어요(`OMP_NUM_THREADS=4`) — 과부하 머신에서 IgFold forward 가 간헐적으로 SIGILL 로 죽는 걸 막아요(실측)."""),
co('''os.environ["OMP_NUM_THREADS"] = "4"
os.environ["MKL_NUM_THREADS"] = "4"
os.environ["CUDA_VISIBLE_DEVICES"] = ""     # AntiBERTy 가 부모의 try_gpu 를 무시하므로 여기서 차단

_ensure("igfold")
_ensure_pkg_resources()      # IgFold 의존성이 pkg_resources 를 import 합니다(setuptools 81+ 에서 제거됨)

# 후보 서열 — Ch.05 에서 내가 만든 가드 없는 argmax 결과 우선(가드 적용본을 쓰려면 파일명만 바꾸세요)
hp = GUIDE_ROOT / "05_humanize_sapiens" / "my_run" / "sapiens_humanized_noguard.fasta"
if hp.exists():
    print(f"[내 결과 · 05_humanize_sapiens] {hp}")
else:
    hp = find_one("sapiens_humanized.fasta")      # 출처 라벨은 find_one 이 찍어요
f = read_fasta(hp)
hum_h, hum_l = f["sapiens_humanized_VH"], f["sapiens_humanized_VL"]

targets = {"parental": {"H": VH, "L": VL},
           "sapiens_humanized": {"H": hum_h, "L": hum_l}}

mine = {}
try:
    from igfold import IgFoldRunner
    t0 = time.time(); runner = IgFoldRunner(); load_s = time.time() - t0
    for name, seqs in targets.items():
        t0 = time.time()
        runner.fold(str(MY / f"{name}.pdb"), sequences=seqs, do_refine=False, do_renum=False)
        mine[name] = time.time() - t0
        (MY / f"{name}_timing.json").write_text(json.dumps(
            {"load_time_sec": load_s, "fold_time_sec": mine[name], "prmsd_available": True}, indent=2))
        print(f"{name}: {mine[name]:.1f}초 → {MY / (name + '.pdb')}")
except Exception as e:
    print("IgFold 실행 실패:", type(e).__name__, str(e)[:200])
    print("→ 아래 분석은 레퍼런스 구조(data/parental.pdb · data/sapiens_humanized.pdb)로 그대로 이어져요.")

ref_t = {n: json.loads((REF / f"{n}_timing.json").read_text())["fold_time_sec"] for n in targets}
print("\\n레퍼런스 실측 폴딩 —", " · ".join(f"{n} {v:.4f}초" for n, v in ref_t.items()))
if mine:
    print("내 폴딩       —", " · ".join(f"{n} {v:.1f}초" for n, v in mine.items()))'''),
co('''import pandas as pd

display(pd.DataFrame([
    {"도구": "IgFold (+AntiBERTy)", "역할": "항체 Fv 구조 예측", "이 랩": "실행 — 이 챕터의 모든 수치"},
    {"도구": "ABodyBuilder3",       "역할": "항체 Fv 구조 예측", "이 랩": "미실행 — GPU·모델 가중치"},
    {"도구": "ImmuneBuilder",       "역할": "항체 Fv 구조 예측", "이 랩": "미실행 — GPU·모델 가중치"},
    {"도구": "AntiFold",            "역할": "inverse folding · residue tolerance", "이 랩": "미실행 — GPU"},
]))
print("아래 pRMSD·RMSD 는 전부 IgFold 한 도구에서 나온 값이에요.")
print("예측기가 바뀌면 절대값도 바뀌니, 다른 도구가 낸 수치와 나란히 놓고 비교하지 마세요.")
print("본문 8.3 의 AntiFold backmutation 우선순위도 이 환경에서는 돌리지 않았어요 — 명령 템플릿과 판정 기준만 있어요.")'''),

md("""## 2) 내 결과 확인 — 잔기별 예측 오차 (본문 8.2)

IgFold 는 PDB 의 B-factor 자리에 **잔기별 예측 오차(Å)** 를 적어요 — **낮을수록 확신**이에요. 겹쳐 보기 전에, 모델이 스스로 "여기는 자신 없다"고 말하는 자리부터 봐요.

그림은 `my_run/` 에 저장해요. 본문이 인용하는 `08_prmsd.png` 는 그대로 둡니다."""),
co('''import humanization_viz          # import 만으로 한글 폰트가 등록돼요(안 하면 제목·축이 □ 로 깨져요)
import matplotlib.pyplot as plt
from Bio.PDB import PDBParser
from IPython.display import Image, display

parser = PDBParser(QUIET=True)

def pick(df, *names):
    """산출물마다 컬럼명이 달라요(prmsd ↔ prmsd_ca_rmsd_angstrom_bfactor) — 있는 쪽을 골라요."""
    for n in names:
        if n in df.columns:
            return n
    raise KeyError(f"{names} 중 아무 컬럼도 없어요 — 실제 컬럼은 {list(df.columns)} 예요.")

def prmsd_table(pdb, name):
    """PDB → 잔기별 CA B-factor(= 예측 RMSD) 표. pos = 체인 안 1-based 번호."""
    rows = []
    for ch in parser.get_structure(name, str(pdb))[0]:
        i = 0
        for res in ch:
            if "CA" in res:
                i += 1
                rows.append({"chain": ch.id, "resnum": res.id[1], "pos": i,
                             "resname": res.get_resname(), "prmsd": float(res["CA"].get_bfactor())})
    return pd.DataFrame(rows)

pdbs = {n: find_one(f"{n}.pdb") for n in ("parental", "sapiens_humanized")}
tabs = {n: prmsd_table(p, n) for n, p in pdbs.items()}
for n, t in tabs.items():
    t.to_csv(MY / f"{n}_prmsd.csv", index=False)
    assert pick(t, "prmsd", "prmsd_ca_rmsd_angstrom_bfactor")

# CDR 좌표 — Ch.04 에서 만든 표 우선, 없으면 이 챕터 data/ (경로를 하드코딩하지 않아요)
ct = pd.read_csv(find_prev("04_sequence_qc", "cdr_table_imgt.csv", quiet=True))
CDR = {}
for _, r in ct.iterrows():
    seq = VH if r["chain"] == "H" else VL
    st = seq.find(r["sequence"]) + 1
    assert st > 0, f"CDR {r['chain']}-{r['cdr']} 를 parental 서열에서 못 찾았어요 — CDR 표와 parental.fasta 가 어긋나요."
    CDR[(r["chain"], r["cdr"])] = (st, st + len(r["sequence"]) - 1)
print("CDR 구간(체인 안 1-based) —", " · ".join(f"{c}-{n} {lo}~{hi}" for (c, n), (lo, hi) in CDR.items()))

fig, axes = plt.subplots(2, 1, figsize=(12, 7))
for ax, chain in zip(axes, ("H", "L")):
    for n, t in tabs.items():
        s = t[t.chain == chain]
        ax.plot(s["pos"], s[pick(s, "prmsd", "prmsd_ca_rmsd_angstrom_bfactor")], lw=1.6, label=n)
    for (c, nm), (lo, hi) in CDR.items():
        if c == chain:
            ax.axvspan(lo, hi, color="#c0508a", alpha=0.12)
    ax.set_ylabel("예측 RMSD (Å) ↓ 좋음")
    ax.set_title(f"IgFold 잔기별 예측 오차 — V{chain} (분홍 = CDR)", fontweight="bold")
    ax.grid(alpha=0.25); ax.legend()
axes[1].set_xlabel("체인 안 잔기 번호 (1-based)")
fig.tight_layout()
png = MY / "08_prmsd.png"; fig.savefig(png, dpi=150); plt.close(fig)
display(Image(str(png)))

cdr_pos = {ch: {i for (c, nm), (lo, hi) in CDR.items() if c == ch for i in range(lo, hi + 1)}
           for ch in ("H", "L")}
for n, t in tabs.items():
    col = pick(t, "prmsd", "prmsd_ca_rmsd_angstrom_bfactor")
    for chain in ("H", "L"):
        s = t[t.chain == chain]
        inc = s["pos"].isin(cdr_pos[chain])
        cdr_m, fr_m = s[inc][col].mean(), s[~inc][col].mean()
        print(f"  {n:18s} V{chain}  전체 {s[col].mean():.3f} Å · CDR {cdr_m:.3f} · framework {fr_m:.3f}"
              f"  → CDR 이 framework 의 {cdr_m / fr_m:.1f}배")
print("\\n판정 — CDR 이 framework 보다 크게 나오는 게 정상이에요(loop 라서 원래 흔들려요).")
print("두 구조가 같은 패턴이면 예측 품질이 비슷하다는 뜻이라, 다음 절의 RMSD 를 서로 비교해도 돼요.")'''),

md("""## 3) 직접 실행 — framework 로 정렬한 뒤 CDR 별 RMSD (본문 8.2)

재는 순서가 중요해요. **framework CA 로 먼저 정렬**하고, 그 상태에서 CDR 만 RMSD 를 재요. 전체를 한꺼번에 정렬하면 loop 의 변화가 framework 오차에 묻혀 버려요.

짝은 **자리 번호**로 지어요. Sapiens 는 자리마다 잔기를 바꿔 쓸 뿐 넣거나 빼지 않아서, parental 의 i 번째와 humanized 의 i 번째가 곧 같은 자리거든요(Ch.05 의 `F101V` 같은 표기가 바로 이 번호예요). 길이가 달라지는 후보(Humatch 처럼 indel 이 난 경우)에서만 서열 정렬로 짝을 찾고, 짝이 없는 자리는 표에서 빠져요.

본문 8.2 표가 요구하는 건 CDR-H3 하나가 아니라 **6개 CDR 전부**예요."""),
co('''import difflib, numpy as np
from Bio.SeqUtils import seq1
from Bio.PDB import Superimposer

def ca_res(pdb, chain):
    """한 체인에서 CA 를 가진 잔기 목록(파일 순서 = 서열 순서)."""
    return [r for r in parser.get_structure("s", str(pdb))[0][chain] if "CA" in r]

def pair_index(a, b):
    """0-based 잔기 인덱스를 1:1 로 짝지어요.

    길이가 같으면 **자리끼리 그대로** 짝지어요 — Sapiens argmax 는 자리별 치환이라 indel 이 없고,
    Ch.05 의 mutation 표(F101V 처럼 자리 번호로 적힌 것)와 짝이 어긋나면 안 되거든요.
    (치환이 몰린 구간을 서열 정렬에 맡기면 '한 칸 밀린 삽입'으로 읽혀 엉뚱한 잔기끼리 재게 돼요.)
    길이가 다른 후보(Humatch 처럼 indel 이 난 경우)에서만 정렬로 짝을 찾고, 짝 없는 자리는 빠져요."""
    if len(a) == len(b):
        return {i: i for i in range(len(a))}
    m = {}
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if op in ("equal", "replace"):
            for k in range(min(i2 - i1, j2 - j1)):
                m[i1 + k] = j1 + k
    return m

rows, head, notes, ALIGN = [], {}, [], {}      # ALIGN = 4절 3D 겹쳐보기가 그대로 재사용할 정렬 결과
for chain in ("H", "L"):
    P, Hm = ca_res(pdbs["parental"], chain), ca_res(pdbs["sapiens_humanized"], chain)
    # 서열은 FASTA 가 아니라 접힌 구조에서 직접 읽어요 — 폴백으로 구조만 레퍼런스가 되어도 어긋나지 않아요
    a = seq1("".join(r.get_resname() for r in P))
    b = seq1("".join(r.get_resname() for r in Hm))
    if a != (VH if chain == "H" else VL):
        notes.append(f"V{chain} — 접힌 parental 구조의 서열이 parental.fasta 와 달라요. 구조 쪽 서열을 기준으로 쟀어요.")
    pair = pair_index(a, b)
    spans = {nm: (lo, hi) for (c, nm), (lo, hi) in CDR.items() if c == chain}
    in_cdr = {i for lo, hi in spans.values() for i in range(lo - 1, hi)}
    fw = [i for i in sorted(pair) if i not in in_cdr]
    assert len(fw) > 20, f"V{chain} framework 짝이 {len(fw)}개뿐이에요 — CDR 표가 이 서열의 것이 맞는지 확인하세요."

    sup = Superimposer()
    sup.set_atoms([P[i]["CA"] for i in fw], [Hm[pair[i]]["CA"] for i in fw])
    sup.apply([at for r in Hm for at in r])          # humanized 를 framework 기준으로 옮겨 놓고 CDR 을 재요
    ALIGN[chain] = {"sup": sup, "pair": pair, "fw": fw, "spans": spans}   # 4절이 이 정렬을 그대로 씁니다

    def rmsd(idx):
        d = np.array([P[i]["CA"].coord - Hm[pair[i]]["CA"].coord for i in idx])
        return float(np.sqrt((d ** 2).sum() / len(d)))

    def muts(idx):
        return [f"{a[i]}{i + 1}{b[pair[i]]}" for i in idx if a[i] != b[pair[i]]]

    rows.append({"부위": f"V{chain} framework", "정렬 기준": "이 체인 framework",
                 "RMSD (Å)": round(sup.rms, 4), "CA": len(fw), "변이": len(muts(fw)), "변이 목록": "-"})
    for nm, (lo, hi) in spans.items():
        idx = [i for i in range(lo - 1, hi) if i in pair]
        m = muts(idx)
        rows.append({"부위": f"{chain}-{nm}", "정렬 기준": "이 체인 framework",
                     "RMSD (Å)": round(rmsd(idx), 4), "CA": len(idx),
                     "변이": len(m), "변이 목록": " ".join(m) or "-"})
    both = sorted(pair)
    s2 = Superimposer()
    s2.set_atoms([P[i]["CA"] for i in both], [Hm[pair[i]]["CA"] for i in both])
    rows.append({"부위": f"V{chain} 전체", "정렬 기준": "자체 CA 정렬",
                 "RMSD (Å)": round(s2.rms, 4), "CA": len(both), "변이": len(muts(both)), "변이 목록": "-"})
    head[chain] = {"fw": (round(sup.rms, 4), len(fw)), "whole": (round(s2.rms, 4), len(both))}
    if len(pair) < len(a):
        notes.append(f"V{chain} — {len(a)} aa 중 {len(pair)} 자리만 짝지어졌어요"
                     f" (짝 없는 parental 자리 {[i + 1 for i in range(len(a)) if i not in pair]}"
                     f" · humanized 자리 {[j + 1 for j in range(len(b)) if j not in set(pair.values())]}).")

tab = pd.DataFrame(rows)
tab.to_csv(MY / "cdr_rmsd_all.csv", index=False)
display(tab)
for s in notes:
    print(s)
print("→", MY / "cdr_rmsd_all.csv")'''),
co('''h3 = tab[tab["부위"] == "H-CDR3"].iloc[0]
h3v, (fwv, fwn) = float(h3["RMSD (Å)"]), head["H"]["fw"]
whv, whn = head["H"]["whole"]

res = pd.DataFrame([
    {"metric": "framework_fit_rmsd", "value_angstrom": fwv, "n_atoms": fwn},
    {"metric": "cdr_h3_rmsd_after_framework_alignment", "value_angstrom": h3v, "n_atoms": int(h3["CA"])},
    {"metric": "whole_vh_rmsd_ca_aligned", "value_angstrom": whv, "n_atoms": whn},
])
res.to_csv(MY / "cdr_h3_rmsd_summary.csv", index=False)   # Ch.10 이 이 파일의 cdr_h3 행을 읽어요
display(res)

cdrs = tab[tab["부위"].str.contains("-CDR")]
over = cdrs[cdrs["RMSD (Å)"] >= 1.0]
worst = cdrs.loc[cdrs["RMSD (Å)"].idxmax()]
most  = cdrs.loc[cdrs["변이"].idxmax()]
print(f"CDR-H3 {h3v:.4f} Å 는 VH framework {fwv:.4f} Å 의 {h3v / fwv:.1f}배예요 — 그래도 절대값은 1.0 Å 아래예요.")
print(f"관찰 — CDR-H3 에 변이 {int(h3['변이'])}개({h3['변이 목록']})가 들어갔는데도 backbone 은 {h3v:.4f} Å 만 움직였어요.")
print("1.0 Å 이상 움직인 CDR —",
      ", ".join(f"{r['부위']} {r['RMSD (Å)']:.4f} Å(변이 {int(r['변이'])}개)" for _, r in over.iterrows()) or "없음")
print(f"가장 크게 움직인 CDR 은 {worst['부위']} ({worst['RMSD (Å)']:.4f} Å · 변이 {int(worst['변이'])}개), "
      f"변이가 가장 많은 CDR 은 {most['부위']} (변이 {int(most['변이'])}개 · {most['RMSD (Å)']:.4f} Å) 이에요.")
print("판정 — 변이 개수 순서와 움직인 정도의 순서가 달라요. 서열만 보고 '몇 개 안 바꿨으니 안전'이라 말할 수 없다는 뜻이라,")
print("       이렇게 접어서 재는 단계가 따로 필요해요. 1.0 Å 을 넘긴 CDR 은 backmutation 검토 대상으로 올려요.")'''),

md("""## 4) 겹쳐 보기 — 0.5406 Å 이 어디서 나왔는지 3D 로 (본문 8.2)

표의 숫자만으로는 **어디가** 움직였는지 알 수 없어요. 그래서 3절이 쓴 **VH framework 정렬을 그대로 재사용해** 두 구조를 겹쳐 놓고 봐요. 여기서 정렬을 새로 하면 안 돼요 — 기준틀이 달라지면 그림과 표가 서로 다른 이야기를 하게 되거든요.

- **파랑 = parental · 주황 = sapiens_humanized**(3절 `Superimposer` 로 옮겨 놓은 좌표)
- **진하고 굵은 구간 = CDR-H3**. 라벨 붙은 굵은 stick = 3절이 CDR-H3 안에서 찾아낸 **변이 잔기**(번호를 적어 넣지 않고 계산 결과에서 가져와요)
- 뷰어는 드래그로 돌리고 휠로 확대해요. 첫 뷰어는 Fv 전체, 두 번째는 CDR-H3 확대예요."""),
co('''_ensure("py3Dmol gemmi")
from Bio.PDB import PDBIO

try:                       # 뷰어가 없어도 좌표 파일·판정은 그대로 만들어요(설치 실패로 절이 통째로 죽지 않게)
    import py3Dmol
    HAVE_3D = True
except Exception as e:
    HAVE_3D = False
    print("py3Dmol 을 못 불러왔어요:", type(e).__name__, str(e)[:120])
    print("→ 3D 뷰어만 건너뛰고 나머지는 그대로 진행해요. `pip install py3Dmol` 뒤 셀을 다시 실행하면 그림이 나와요.")

# (1) 좌표 — 3절의 VH framework Superimposer 를 humanized 구조 '전체' 에 그대로 적용해요.
#     CDR-H3 RMSD 를 잰 바로 그 기준틀이라, 눈으로 보는 벌어짐과 표의 숫자가 같은 정렬 위에 있어요.
par_st = parser.get_structure("parental", str(pdbs["parental"]))
hum_st = parser.get_structure("humanized", str(pdbs["sapiens_humanized"]))
ALIGN["H"]["sup"].apply(list(hum_st.get_atoms()))

io, ovl = PDBIO(), {}
for tag, st in (("parental", par_st), ("humanized_aligned", hum_st)):
    io.set_structure(st)
    p = MY / f"overlay_{tag}.pdb"
    io.save(str(p))
    ovl[tag] = p

def pdb_text(p):
    """3Dmol.js 는 PDB 문자열이 가장 안정적이라 gemmi 로 한 번 통과시켜요(없으면 원문 그대로)."""
    try:
        import gemmi
        return gemmi.read_structure(str(p)).make_pdb_string()
    except Exception:
        return pathlib.Path(p).read_text()

def origin(p):
    return "내 결과 (my_run/)" if MY.resolve() in pathlib.Path(p).resolve().parents else "레퍼런스 (data/)"

print("[구조 출처] parental          ←", pdbs["parental"], "·", origin(pdbs["parental"]))
print("[구조 출처] sapiens_humanized ←", pdbs["sapiens_humanized"], "·", origin(pdbs["sapiens_humanized"]))
print("[정렬]      VH framework", f"{ALIGN['H']['sup'].rms:.4f} Å ({len(ALIGN['H']['fw'])} CA) — 3절과 같은 변환")

# (2) 강조할 잔기 — 앞 절이 계산한 CDR 구간·변이 목록에서 가져와요(잔기 번호 하드코딩 없음)
h3_lo, h3_hi = CDR[("H", "CDR3")]
pair_h = ALIGN["H"]["pair"]
par_i  = list(range(h3_lo - 1, h3_hi))                    # parental 체인 안 0-based
hum_i  = [pair_h[i] for i in par_i if i in pair_h]

def resi(name, chain, idxs):
    """체인 안 0-based 인덱스 → 그 PDB 파일의 실제 residue 번호."""
    s = tabs[name]
    s = s[s.chain == chain]
    m = dict(zip(s["pos"].astype(int), s["resnum"].astype(int)))
    return [int(m[i + 1]) for i in idxs if (i + 1) in m]

h3_par, h3_hum = resi("parental", "H", par_i), resi("sapiens_humanized", "H", hum_i)

mut_txt  = str(tab[tab["부위"] == "H-CDR3"].iloc[0]["변이 목록"]).strip()
mut_list = [] if mut_txt in ("-", "", "nan") else mut_txt.split()
mut_i    = [int("".join(ch for ch in m if ch.isdigit())) - 1 for m in mut_list]
mut_par  = resi("parental", "H", mut_i)
mut_hum  = resi("sapiens_humanized", "H", [pair_h[i] for i in mut_i if i in pair_h])
assert h3_par and h3_hum, "CDR-H3 잔기 번호를 못 찾았어요 — CDR 표가 이 구조의 것인지 확인하세요."

PAR_C, HUM_C = "#5b84c4", "#e07b39"

def overlay(zoom_sel=None, w=760, h=520):
    v = py3Dmol.view(width=w, height=h)
    v.addModel(pdb_text(ovl["parental"]), "pdb")             # model 0 = parental
    v.addModel(pdb_text(ovl["humanized_aligned"]), "pdb")    # model 1 = humanized (정렬된 좌표)
    v.setStyle({"model": 0}, {"cartoon": {"color": PAR_C, "opacity": 0.85}})
    v.setStyle({"model": 1}, {"cartoon": {"color": HUM_C, "opacity": 0.85}})
    v.addStyle({"model": 0, "chain": "H", "resi": h3_par},    # CDR-H3 = 굵은 cartoon + stick
               {"cartoon": {"color": "#123a72", "thickness": 1.0},
                "stick": {"colorscheme": "blueCarbon", "radius": 0.14}})
    v.addStyle({"model": 1, "chain": "H", "resi": h3_hum},
               {"cartoon": {"color": "#a02c0f", "thickness": 1.0},
                "stick": {"colorscheme": "redCarbon", "radius": 0.14}})
    if mut_par:                                              # CDR-H3 안의 변이 = 더 굵은 stick + 라벨
        v.addStyle({"model": 0, "chain": "H", "resi": mut_par},
                   {"stick": {"colorscheme": "cyanCarbon", "radius": 0.30}})
        v.addStyle({"model": 1, "chain": "H", "resi": mut_hum},
                   {"stick": {"colorscheme": "magentaCarbon", "radius": 0.30}})
        v.addResLabels({"model": 1, "chain": "H", "resi": mut_hum},
                       {"fontSize": 11, "fontColor": "black",
                        "backgroundColor": "white", "backgroundOpacity": 0.75})
    v.setBackgroundColor("white")
    if zoom_sel:
        v.zoomTo(zoom_sel); v.zoom(0.7)
    else:
        v.zoomTo()
    return v

print(f"\\nCDR-H3 residue — parental {h3_par[0]}~{h3_par[-1]} ({len(h3_par)}개) · humanized {h3_hum[0]}~{h3_hum[-1]} ({len(h3_hum)}개)")
print(f"CDR-H3 안 변이 {len(mut_list)}개 —", " · ".join(mut_list) or "없음")
print("→", ovl["parental"], "·", ovl["humanized_aligned"])
if HAVE_3D:
    overlay().show()                                             # ① Fv 전체
    overlay({"model": 0, "chain": "H", "resi": h3_par}).show()    # ② CDR-H3 확대'''),
co('''print(f"판정 — framework 는 {fwv:.4f} Å 라 두 cartoon 이 사실상 포개져요. 눈에 띄게 벌어지는 곳은 굵게 칠한 CDR-H3 이고,")
print(f"       그 벌어짐이 표의 {h3v:.4f} Å 예요. VH 전체는 {whv:.4f} Å 인데, 이건 loop 의 변화가 나머지 잔기에 희석된 값이에요.")
print(f"       라벨 붙은 {len(mut_list)}개({' · '.join(mut_list) or '없음'})가 CDR-H3 에 들어간 변이예요 —")
print("       곁사슬은 바뀌었는데 backbone cartoon 은 거의 같은 자리에 있어요. 그래서 '변이가 있다 = 구조가 망가졌다' 가 아니에요.")
if HAVE_3D:
    print("       그림이 안 보이면 py3Dmol 이 아니라 브라우저 쪽 문제예요 — Colab 이면 셀을 한 번 다시 실행해 보세요.")'''),

md("""## 5) 레퍼런스 대조 (본문 8.2)

`data/cdr_h3_rmsd_summary.csv` 는 이 가이드를 만들 때 같은 방식으로 뽑은 산출물이에요. 다만 **metric 이름이 노트북과 조금 달라요**(`whole_vh_rmsd_ca_aligned` ↔ `whole_vh_rmsd_all_atoms_aligned`). 이름 전체가 아니라 **앞부분만** 맞춰서 비교해요."""),
co('''ref = pd.read_csv(REF / "cdr_h3_rmsd_summary.csv")
STEMS = ("framework_fit", "cdr_h3", "whole_vh")

def stem(m):
    return next((s for s in STEMS if str(m).startswith(s)), str(m))

cmp_ = (res.assign(stem=res.metric.map(stem))
           .merge(ref.assign(stem=ref.metric.map(stem)), on="stem", suffixes=("_my", "_ref")))
cmp_["차이 (Å)"] = (cmp_.value_angstrom_my - cmp_.value_angstrom_ref).round(4)
display(cmp_[["stem", "value_angstrom_my", "n_atoms_my", "metric_ref", "value_angstrom_ref", "n_atoms_ref", "차이 (Å)"]])

print("레퍼런스 실측 — framework 0.2707 Å (91 CA) · CDR-H3 0.5406 Å (13 CA) · VH 전체 0.3207 Å (120 CA)")
same = bool((cmp_["차이 (Å)"].abs() < 0.005).all() and (cmp_.n_atoms_my == cmp_.n_atoms_ref).all())
if same:
    print("판정 — 세 지표가 레퍼런스와 같아요. 실행을 건너뛴 사람도 같은 표에 도달하니 아래 결론은 어느 쪽으로 읽어도 같아요.")
else:
    print("판정 — 값이 어긋나요. 내가 접은 구조나 Ch.05 후보 서열이 레퍼런스와 다르면 정상이에요.")
    print("       CA 개수까지 다르면 CDR 표가 이 서열의 것인지 먼저 확인하세요.")

print(f"\\nCh.10 으로 넘어가는 값은 CDR-H3 RMSD {h3v:.4f} Å **하나**예요 — 나머지 표는 그 값을 해석하기 위한 맥락이에요.")
print("Ch.10 은 이 파일의 cdr_h3 행만 읽어 가고, 구조를 접어 본 후보(parental·Sapiens)에만 값이 붙어요.")
print("1.0 Å 아래라는 건 '통과'가 아니라 '구조 축에서 경고가 없다' 는 뜻이에요 — 결합력은 구조 하나로 정해지지 않아요.")'''),

md("""## 이 랩에서 확인한 것

1. IgFold 로 VH+VL Fv 를 접었어요 — 실측 **7.0859초**(parental) · **11.9880초**(humanized). `do_refine=False`(PyRosetta 없음) · `do_renum=False`(VL C-말단 잔기가 IMGT 범위 밖) 가 필수예요.
2. 잔기별 예측 오차(B-factor)는 **CDR 이 framework 의 1.4~2.1배** — loop 라서 정상이고, 두 구조가 같은 패턴이면 서로 비교해도 됩니다.
3. framework 정렬 후 **CDR-H3 = 0.5406 Å**(framework 0.2707 Å · **2.0배**, VH 전체 0.3207 Å). CDR-H3 에 변이 **2개(L104D·Y109V)** 가 들어갔는데도 이만큼만 움직였어요.
4. 6개 CDR 중 가장 크게 움직인 건 **L-CDR3 (2.5792 Å)** 인데 변이는 **1개**(R98S)뿐이에요. 반대로 변이가 4개인 L-CDR1 은 **0.6678 Å**. **변이 개수로 구조 변화를 예측할 수 없어요.**
5. 경쇄는 **framework 정렬 오차 자체가 1.2748 Å**(89 CA)로 중쇄(0.2707 Å · 91 CA)보다 훨씬 커요. VL 쪽 CDR 값은 이 바닥 위에서 읽어야 하고, C-말단 꼬리처럼 흔들리는 구간이 정렬을 끌고 갔는지 함께 봐야 해요.
6. ABodyBuilder3·ImmuneBuilder·AntiFold 는 **이 환경에서 미실행** — 여기 수치는 전부 IgFold 하나에서 나왔어요.
7. 3D 로 겹쳐 보면 **framework 는 포개지고 CDR-H3 만 벌어져요** — 표의 `0.2707 vs 0.5406` 이 그림 그대로예요. 겹치는 좌표는 새로 정렬한 게 아니라 3절 `Superimposer` 를 재사용한 것이라, 그림과 표가 같은 기준틀 위에 있어요.
8. 산출물 — `my_run/{parental,sapiens_humanized}.pdb` · `*_prmsd.csv` · `cdr_rmsd_all.csv` · `cdr_h3_rmsd_summary.csv` · `08_prmsd.png` · `overlay_{parental,humanized_aligned}.pdb`.

다음 → **[Ch.09 — Developability](../09_developability/09_developability_lab.ipynb)**"""),
]
cells_all[("08_structure", "08_structure_lab.ipynb", "08 Structure Lab")] = c


# ════════════════════════════════════════════════════════════════════════════
# 09 — developability
# ════════════════════════════════════════════════════════════════════════════
c = [title_cell("09", "Developability — liability 모티프 직접 스캔", "09_developability.md",
                prev="Ch.04 numbering")]
c += boot("09_developability", pip="pandas matplotlib")
c += [
md("""## 1) 직접 실행 — 서열 한 줄로 잡히는 liability (본문 9.1)

liability 는 한 종류가 아니에요. **서열만으로 스캔되는 것**과 **구조가 있어야 잡히는 것**으로 갈려요. 이 절은 앞쪽만 다뤄요.

| 서열로 잡히는 것 | 방법 | 위험 |
|---|---|---|
| N-glycosylation | `N[^P][ST]` | 예상치 못한 당쇄 → 이질성·클리어런스 |
| deamidation | `N[GS]` | 보관 중 전하 변이 |
| isomerization | `DG` | 구조 변형 |
| oxidation | `[MW]` | 산화 → 활성 저하 |
| unpaired Cys | Cys 개수의 홀짝 | 미스폴딩·이량체 |

`NXS/T` 의 X 가 P 면 당쇄가 안 붙어요 — 정규식이 `N[^P][ST]` 인 이유예요.
SAP·charge patch 는 Ch.08 의 예측 구조가 있어야 하니 5절에서 따로 봐요."""),
co('''import re, json, difflib, pandas as pd

MOTIFS = {
    "N-glycosylation": r"N[^P][ST]",   # NXS/T (X != P)
    "deamidation":     r"N[GS]",
    "isomerization":   r"DG",
    "oxidation":       r"[MW]",
}

def scan(seq):
    """서열 → {모티프: [1-based 위치, ...]}"""
    return {name: [m.start() + 1 for m in re.finditer(p, seq)] for name, p in MOTIFS.items()}

PREV = [
    ("05_humanize_sapiens", "sapiens_humanized_noguard.fasta", ("sapiens_humanized_VH", "sapiens_humanized_VL"), "sapiens"),
    ("06_cdr_safe_tools",   "humatch_humanised.fasta",         ("humatch_humanised_VH", "humatch_humanised_VL"), "humatch"),
    ("06_cdr_safe_tools",   "anthroab_best_score.fasta",       ("anthroab_bestscore_VH", "anthroab_bestscore_VL"), "anthroab"),
    ("06_cdr_safe_tools",   "anthroab_masked_FRonly.fasta",    ("anthroab_masked_VH", "anthroab_masked_VL"), "anthroabFRmasked"),
]

cands, SRC = {"parental": (VH, VL)}, {"parental": "data/parental.fasta"}
for chapter, fname, keys, label in PREV:
    p = GUIDE_ROOT / chapter / "my_run" / fname
    if p.exists():
        f = read_fasta(p)
        cands[label], SRC[label] = (f[keys[0]], f[keys[1]]), f"내 결과 · {chapter}/my_run/{fname}"

need = [lab for *_, lab in PREV if lab not in cands]          # 빠진 후보만 레퍼런스로 채워요
if need:
    vp = find_one("variants.fasta", quiet=True)
    v = read_fasta(vp)
    for lab in need:
        cands[lab], SRC[lab] = (v[f"{lab}_VH"], v[f"{lab}_VL"]), f"레퍼런스 · {vp}"

for k in cands:
    print(f"  {k:18s} ← {SRC[k]}")

# unpaired Cys — 개수가 홀수면 짝 없는 시스테인이 남아요
print()
odd = []
for name, (h, l) in cands.items():
    nh, nl = h.count("C"), l.count("C")
    if nh % 2 or nl % 2:
        odd.append(name)
    print(f"  {name:18s} Cys VH {nh}개 · VL {nl}개 · {'짝 맞음' if not (nh % 2 or nl % 2) else '★홀수 — unpaired Cys'}")
print(f"\\nunpaired Cys 판정 — 홀수 후보 {len(odd)}개"
      + ("" if odd else ". 전부 짝이 맞아 미스폴딩·이량체 위험은 이 축에서 걸리지 않아요."))'''),

md("""## 2) 내 결과 확인 — 후보별 모티프 총량 (본문 9.2)

8개(체인 2 × 모티프 4) 조합을 다 늘어놓으면 **후보 전부 0인 칸**이 섞여요. 0만 있는 칸은 정보가 아니라 잡음이라서 표에서 빼고, 어떤 칸을 뺐는지만 알려요."""),
co('''rows = []
for name, (h, l) in cands.items():
    for chain, seq in (("VH", h), ("VL", l)):
        for motif, hits in scan(seq).items():
            rows.append({"candidate": name, "chain": chain, "motif": motif,
                         "count": len(hits), "positions_1based": ";".join(map(str, hits))})
lia = pd.DataFrame(rows)
lia.to_csv(MY / "liability.csv", index=False)
print("→", MY / "liability.csv")

piv = lia.pivot_table(index="candidate", columns=["chain", "motif"], values="count",
                      aggfunc="sum", fill_value=0)
piv = piv.reindex(list(cands))
zero = [col for col in piv.columns if piv[col].sum() == 0]
print("후보 전부 0건이라 뺀 칸:", ", ".join(f"{a} {b}" for a, b in zero) if zero else "없음")
display(piv.drop(columns=zero))

tot = lia.groupby("candidate")["count"].sum().reindex(list(cands))
ox  = lia[lia.motif == "oxidation"].groupby("candidate")["count"].sum().reindex(list(cands)).fillna(0)
print()
for name in cands:
    print(f"  {name:18s} 총 {int(tot[name]):2d}건 · 그중 oxidation {int(ox[name]):2d}건 ({ox[name]/tot[name]*100:.0f}%)")
print(f"\\n판정 — oxidation 비중이 {ox.div(tot).min()*100:.0f}~{ox.div(tot).max()*100:.0f}% 로 전 후보가 비슷해요.")
print("Met/Trp 은 어느 항체 서열에나 흔해서 총량으로는 후보가 갈리지 않아요.")
print("갈라지는 축은 총량이 아니라 parental 대비 신규 모티프예요 (3절).")'''),
co('''from humanization_viz import liability_overview
from IPython.display import Image, display

png = liability_overview(lia.groupby(["candidate", "motif"], sort=False)["count"].sum().reset_index(),
                         "Developability liability motifs (VH+VL)", str(MY / "09_liability.png"))
display(Image(str(png)))
worst = tot.idxmax()
print(f"막대 높이 판정 — 가장 높은 후보는 {worst} ({int(tot[worst])}건), 가장 낮은 후보는 "
      f"{tot.idxmin()} ({int(tot.min())}건). parental 은 {int(tot['parental'])}건이에요.")
print("총량이 parental 보다 크게 늘어난 후보가 developability 축의 1차 경고 대상이에요.")'''),

md("""## 3) 증분 스캔 — parental 에 없던 자리만 (본문 9.2)

원래 있던 모티프는 parental 항체가 이미 견디던 자리예요. 진짜 위험은 humanization 이 **새로 심은 자리**예요.
그중에서도 신규 `NXS/T` 가 제일 위험해요 — 예상치 못한 당쇄는 이질성·클리어런스로 바로 이어지거든요."""),
co('''par_scan = {"VH": scan(cands["parental"][0]), "VL": scan(cands["parental"][1])}

new_rows = []
for name, (h, l) in cands.items():
    if name == "parental":
        continue
    for chain, seq in (("VH", h), ("VL", l)):
        for motif, hits in scan(seq).items():
            base = set(par_scan[chain][motif])
            new, lost = sorted(set(hits) - base), sorted(base - set(hits))
            new_rows.append({"candidate": name, "chain": chain, "motif": motif,
                             "신규": len(new), "신규 위치": ";".join(map(str, new)) or "-",
                             "사라짐": len(lost)})
delta = pd.DataFrame(new_rows)
delta.to_csv(MY / "liability_delta.csv", index=False)

display(delta[delta["신규"] > 0].sort_values(["candidate", "chain"]).reset_index(drop=True))

new_tot = delta.groupby("candidate")["신규"].sum().reindex([n for n in cands if n != "parental"])
glyc = delta[(delta.motif == "N-glycosylation") & (delta["신규"] > 0)]
print()
for name, v_ in new_tot.items():
    print(f"  {name:18s} 신규 {int(v_):2d}건")
print(f"\\n신규 N-glycosylation 모티프 — 총 {int(glyc['신규'].sum())}건", end="")
if glyc.empty:
    print(". 이 축에서는 아무도 걸리지 않았어요.")
else:
    print(" ·", ", ".join(f"{r.candidate} {r.chain} {r['신규 위치']}" for _, r in glyc.iterrows()))
    print("판정 — 신규 NXS/T 가 있는 후보는 Ch.10 의 hard filter 대상이에요(즉시 탈락 또는 backmutation 검토).")
print(f"신규가 가장 많은 후보는 {new_tot.idxmax()} ({int(new_tot.max())}건), 가장 적은 후보는 "
      f"{new_tot.idxmin()} ({int(new_tot.min())}건) 이에요.")'''),

md("""## 4) CDR 안에 떨어졌나 — 좌표를 IMGT 로 다시 매핑 (본문 9.2)

같은 모티프라도 **CDR 안**이면 결합에 직접 영향을 줘서 위험도가 달라요.
그런데 CDR 좌표는 parental raw 번호 기준이고, **indel 이 있는 후보는 raw 번호가 밀려요.**
그래서 Ch.04 가 만든 `raw2imgt_*.json` 으로 parental 좌표를 **IMGT 라벨**로 바꾸고, 후보 좌표도 같은 라벨로 옮긴 뒤에 비교해요."""),
co('''def load_r2i(tag):
    p = find_prev("04_sequence_qc", f"raw2imgt_{tag}.json",
                  ref=GUIDE_ROOT / "04_sequence_qc" / "data", quiet=True)
    return {int(k): v for k, v in json.loads(pathlib.Path(p).read_text()).items()}

r2i = {"H": load_r2i("H"), "L": load_r2i("L")}
print("raw → IMGT 크로스워크 — VH", len(r2i["H"]), "자리 · VL", len(r2i["L"]), "자리")

# parental raw CDR 구간 → IMGT 라벨 집합 (여기가 '보호 좌표'의 기준면)
ct = pd.read_csv(find_one("cdr_table_imgt.csv", quiet=True))
guard = {"H": {}, "L": {}}
for _, r in ct.iterrows():
    seq = VH if r["chain"] == "H" else VL
    st = seq.find(r["sequence"]) + 1
    assert st > 0, f"CDR {r['cdr']} 를 parental 서열에서 못 찾았어요 — cdr_table 과 parental.fasta 가 어긋나요."
    for p in range(st, st + len(r["sequence"])):
        guard[r["chain"]][r2i[r["chain"]][p]] = f"{r['chain']}-{r['cdr']}"

def cand2imgt(par, cand, tag):
    """후보 raw 위치 → IMGT 라벨. 길이가 같으면 1:1, 다르면(indel) 정렬로 이어 붙여요."""
    if len(par) == len(cand):
        return {i + 1: r2i[tag][i + 1] for i in range(len(cand))}
    m = {}
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, par, cand, autojunk=False).get_opcodes():
        if op in ("equal", "replace"):
            for k in range(min(i2 - i1, j2 - j1)):
                m[j1 + k + 1] = r2i[tag][i1 + k + 1]
    return m

hits, shifted = [], []
for name, (h, l) in cands.items():
    for chain, seq, tag in (("VH", h, "H"), ("VL", l, "L")):
        par = VH if tag == "H" else VL
        m = cand2imgt(par, seq, tag)
        if len(par) != len(seq):
            moved = [p for p, lab in m.items() if r2i[tag].get(p) != lab]
            shifted.append((name, chain, len(par), len(seq), len(m), len(moved)))
        for motif, ps in scan(seq).items():
            for p in ps:
                lab = m.get(p)
                if lab in guard[tag]:
                    hits.append({"candidate": name, "chain": chain, "motif": motif,
                                 "raw": p, "IMGT": lab, "구간": guard[tag][lab]})

cdr_lia = pd.DataFrame(hits)
display(cdr_lia if not cdr_lia.empty else "CDR 안 liability 없음")

for name, chain, lp, lc, nmap, nmoved in shifted:
    print(f"재매핑 — {name} {chain} 은 길이 {lp}→{lc} 라 정렬로 이어 붙였어요 "
          f"(잇힌 자리 {nmap}개 · 그중 raw 번호가 실제로 밀린 자리 {nmoved}개).")
if not shifted:
    print("재매핑 — indel 있는 후보가 없어 raw 번호가 그대로 IMGT 로 이어졌어요.")

par_cdr = set(map(tuple, cdr_lia[cdr_lia.candidate == "parental"][["chain", "motif", "IMGT"]].values)) if not cdr_lia.empty else set()
new_in_cdr = [r for _, r in cdr_lia.iterrows()
              if r.candidate != "parental" and (r.chain, r.motif, r.IMGT) not in par_cdr] if not cdr_lia.empty else []
print(f"\\n판정 — CDR 안 모티프 {len(cdr_lia)}건 중 parental 에 없던 신규는 {len(new_in_cdr)}건이에요.")
for r in new_in_cdr:
    print(f"  ★ {r.candidate} {r['구간']} {r.IMGT} 에 신규 {r.motif}")
print("parental 부터 갖고 있던 자리는 이미 견디던 자리라 우선순위가 낮고, 신규만 backmutation 후보로 올려요.")'''),

md("""## 5) 구조가 있어야 잡히는 것 — SAP · charge patch · TAP (본문 9.1 심화 · 9.3)

여기까지가 서열 스캔이에요. 응집·점도·클리어런스로 이어지는 지표는 **Ch.08 의 예측 구조 위에서** 돌아가요."""),
co('''struct_based = pd.DataFrame([
    {"지표": "SAP (Spatial Aggregation Propensity)", "필요한 입력": "예측 구조 + 표면 노출·소수성", "이 랩": "미실행"},
    {"지표": "charge patch / pI 비대칭",             "필요한 입력": "예측 구조 + 표면 전하 분포",   "이 랩": "미실행"},
    {"지표": "TAP (Therapeutic Antibody Profiler)",  "필요한 입력": "예측 구조 + 임상단계 항체 분포", "이 랩": "미실행 · 웹 전용"},
])
display(struct_based)
print("세 지표는 예측 구조의 품질을 그대로 물려받아요.")
print("그래서 절대 기준선으로 자르지 말고, 같은 파이프라인으로 뽑은 후보끼리 상대 비교로 읽어요.")
print("반대로 1~4절의 정규식 스캔은 구조 품질과 무관해서 절대값으로 읽어도 됩니다 — 이 차이가 두 축을 나눠 쓰는 이유예요.")'''),

md("""## 6) 레퍼런스 대조 (본문 9.2)

`data/liability_reference.csv` 는 이 가이드를 만들 때 같은 정규식으로 뽑은 산출물이에요. 개수뿐 아니라 **위치 문자열까지** 맞춰 봐요."""),
co('''ref = pd.read_csv(find_one("liability_reference.csv", quiet=True)).fillna({"positions_1based": ""})
cmp_ = lia.merge(ref, on=["candidate", "chain", "motif"], suffixes=("_my", "_ref"))
ok_cnt = bool((cmp_.count_my == cmp_.count_ref).all())
ok_pos = bool((cmp_.positions_1based_my == cmp_.positions_1based_ref).all())
print(f"대조한 행 {len(cmp_)}개 · 개수 일치 {ok_cnt} · 위치 일치 {ok_pos}")

ref_tot = ref.groupby("candidate")["count"].sum().reindex(list(cands))
print("\\n[레퍼런스 총량]")
for name in cands:
    print(f"  {name:18s} {int(ref_tot[name]):2d}건")
ref_pos = {(r.candidate, r.chain): set(str(r.positions_1based).split(";")) - {""}
           for r in ref[ref.motif == "N-glycosylation"].itertuples()}
ref_new_glyc = sorted({cnd for (cnd, chain) in ref_pos if cnd != "parental"
                       and ref_pos[(cnd, chain)] - ref_pos[("parental", chain)]})
print("레퍼런스에서 신규 N-glyc 를 만든 후보 —", ", ".join(ref_new_glyc) or "없음")

if ok_cnt and ok_pos:
    print("\\n판정 — 커밋된 레퍼런스가 variants.fasta 에서 정규식만으로 완전히 재현돼요.")
    print("실행을 건너뛴 사람도 같은 표에 도달하니, 아래 결론은 내 결과·레퍼런스 어느 쪽으로 읽어도 같아요.")
else:
    print("\\n판정 — 개수나 위치가 어긋나요. 내 후보 서열이 레퍼런스와 다른 경우(직접 만든 my_run)라면 정상이에요.")
    display(cmp_[(cmp_.count_my != cmp_.count_ref) | (cmp_.positions_1based_my != cmp_.positions_1based_ref)])'''),

md("""## 이 랩에서 확인한 것

1. 서열 liability 스캔은 **정규식 4줄 + Cys 홀짝 1줄**이면 끝나요 — 후보를 만들 때마다 자동으로 돌리세요.
2. 총량은 후보를 못 갈라요. **oxidation(Met/Trp)이 총량의 83~100%** 를 차지하는데, Met·Trp 은 어느 서열에나 흔하거든요.
3. 갈라지는 축은 **parental 대비 신규 모티프**예요 — 특히 신규 `NXS/T` 는 Ch.10 의 **hard filter** 로 직행해요.
4. CDR 귀속은 **IMGT 라벨로 다시 매핑한 뒤** 판단해요. raw 번호는 indel 후보에서 밀려요.
5. SAP·charge patch·TAP 는 예측 구조 위에서 돌고, **후보 간 상대 비교**로 읽어요.
6. 산출물 — `my_run/liability.csv` · `liability_delta.csv` · `09_liability.png`.

다음 → **[Ch.10 — 랭킹·리포트](../10_ranking_report/10_ranking_lab.ipynb)**"""),
]
cells_all[("09_developability", "09_developability_lab.ipynb", "09 Developability Lab")] = c


# ════════════════════════════════════════════════════════════════════════════
# 10 — 랭킹·리포트
# ════════════════════════════════════════════════════════════════════════════
c = [title_cell("10", "후보 랭킹 · 리포트 — 앞 랩 산출물을 하나의 순위로", "10_ranking_report.md",
                prev="Ch.05~Ch.09")]
c += boot("10_ranking_report", pip="pandas matplotlib pyyaml sapiens anarci abnumber", apt="hmmer")
c += [
md("""## 1) 직접 실행 — 앞 랩 산출물 모으기 (본문 10.2)

후보 하나를 고르려면 Ch.05~09 가 만든 조각이 **한자리에** 있어야 해요. 본문 10.2 가 프로젝트를 문서가 아니라 DB 로 굴리라고 하는 이유가 이거예요 — 3개월 뒤에 "이 점수가 어디서 나왔더라" 를 다시 묻지 않으려고요.

그래서 이 랩의 첫 규칙은 **모든 값에 출처를 붙이는 것**이에요. 내가 직접 만든 `my_run/` 이 있으면 그걸 쓰고, 없는 것만 커밋된 `data/` 로 채워요. 아래 출력의 왼쪽이 후보, 오른쪽이 그 후보가 어디서 왔는지예요."""),
co('''import re, difflib, subprocess, tempfile
import pandas as pd, numpy as np

PREV = [
    ("05_humanize_sapiens", "sapiens_humanized_noguard.fasta", ("sapiens_humanized_VH", "sapiens_humanized_VL"), "sapiens"),
    ("06_cdr_safe_tools",   "humatch_humanised.fasta",         ("humatch_humanised_VH", "humatch_humanised_VL"), "humatch"),
    ("06_cdr_safe_tools",   "anthroab_best_score.fasta",       ("anthroab_bestscore_VH", "anthroab_bestscore_VL"), "anthroab"),
    ("06_cdr_safe_tools",   "anthroab_masked_FRonly.fasta",    ("anthroab_masked_VH", "anthroab_masked_VL"), "anthroabFRmasked"),
]

cands, SRC = {"parental": (VH, VL)}, {"parental": "data/parental.fasta"}
for chapter, fname, keys, label in PREV:
    p = GUIDE_ROOT / chapter / "my_run" / fname
    if p.exists():
        f = read_fasta(p)
        cands[label], SRC[label] = (f[keys[0]], f[keys[1]]), f"내 결과 · {chapter}/my_run/{fname}"

need = [lab for *_, lab in PREV if lab not in cands]      # 빠진 후보만 레퍼런스로 채워요
if need:
    vp = find_one("variants.fasta", quiet=True)
    v = read_fasta(vp)
    for lab in need:
        cands[lab], SRC[lab] = (v[f"{lab}_VH"], v[f"{lab}_VL"]), f"레퍼런스 · {vp}"

for k in cands:
    print(f"  {k:18s} ← {SRC[k]}")
print(f"\\n후보 {len(cands)}종 · VH/VL 길이", ", ".join(f"{k} {len(h)}/{len(l)}" for k, (h, l) in cands.items()))
print("길이가 parental(120/111)과 다른 후보는 indel 이 들어간 거라 위치 번호를 그대로 비교하면 안 돼요 (2절에서 처리).")'''),

md("""## 2) 직접 실행 — 랭킹에 쓸 지표 계산 (본문 10.1.1)

본문 10.1.1 이 요구하는 축은 6개예요. 이 랩이 각 축을 무엇으로 채우는지 먼저 못 박아요.

| 본문 10.1.1 축 | 이 랩의 측정값 | 어디서 |
|---|---|---|
| Humanness | Sapiens 재스코어링 paired (정의 b) | 이 셀에서 직접 계산 (후보 5종 2초 미만) |
| Nativeness | AbNatiV1 VH `overall_score` | Ch.07 산출물 → 없으면 `data/` |
| CDR/structure 보존 | CDR-H3 backbone RMSD (Å) | Ch.08 산출물 → 없으면 `data/` |
| Developability | parental 대비 **신규** liability 모티프 수 | 이 셀에서 Ch.09 방식으로 계산 |
| Germline 일관성 | ANARCI V identity **VH·VL 평균** | 이 셀에서 직접 실행 (10 체인 0.42초) |
| 전문가 수동 review | 사람 판단 — 노트북이 만들 수 없어요 | 결측으로 둬요 (3절) |

Ab-RoBERTa naturalness 도 함께 읽지만 **가중합에는 넣지 않아요.** Ch.07 에서 확인했듯 사람다움과 자연스러움은 다른 축이고, Ab-RoBERTa 는 주 humanness 지표가 아니라 이상치 탐지 보조라서요 — 표에는 참고 열로만 둡니다.

germline 은 **VH·VL 평균**으로 통일해요. VH 만 보면 parental 이 0.63 이지만 VL 은 0.81 이라, 한쪽만 쓰면 경쇄를 거의 안 건드린 후보가 부당하게 낮게 나와요."""),
co('''# (1) humanness — Sapiens 재스코어링(정의 b), paired 는 길이가중 평균
hum, hum_src = {}, ""
try:
    import sapiens

    def mean_self_prob(seq, chain):
        m = sapiens.predict_scores(seq, chain)
        return float(np.mean([m.loc[i, aa] for i, aa in enumerate(seq)]))

    t0 = time.time()
    for n, (h, l) in cands.items():
        ph, pl = mean_self_prob(h, "H"), mean_self_prob(l, "L")
        hum[n] = (ph * len(h) + pl * len(l)) / (len(h) + len(l))
    hum_src = f"직접 계산 · Sapiens 재스코어링 {time.time()-t0:.1f}초"
except Exception as e:
    hp = find_one("humanness_all_candidates.csv", quiet=True)
    ref = pd.read_csv(hp)
    ref = ref[ref.chain == "paired"].set_index("candidate")["mean_self_prob"]
    hum = {n: float(ref[n]) if n in ref.index else np.nan for n in cands}
    hum_src = f"레퍼런스 · {hp} (Sapiens 실패 — {type(e).__name__})"

# (2) germline V identity — ANARCI 직접 실행, VH·VL 따로 받아 평균
gvh, gvl, germ_src = {}, {}, ""
t0 = time.time()
with tempfile.TemporaryDirectory() as td:
    td = pathlib.Path(td)
    write_fasta(td / "all.fa", {f"{n}__{c}": s for n, (h, l) in cands.items()
                                for c, s in (("VH", h), ("VL", l))})
    try:
        r = subprocess.run(["ANARCI", "-i", str(td / "all.fa"), "-s", "imgt", "--csv",
                            "-o", str(td / "gl"), "--assign_germline", "--use_species", "human"],
                           capture_output=True, text=True, timeout=600)   # 멈춘 채 매달리지 않게
        rc = r.returncode
    except (FileNotFoundError, subprocess.TimeoutExpired):
        rc = 127                       # ANARCI/hmmscan 이 없거나 600초 초과 → 레퍼런스로
    got = {}
    if rc == 0:
        for f in sorted(td.glob("gl_*.csv")):
            df = pd.read_csv(f)
            if "v_identity" not in df.columns:
                continue               # ANARCI 판올림으로 컬럼명이 바뀌면 레퍼런스로 넘어가요
            for _, row in df.iterrows():
                n, ch = str(row["Id"]).split("__")
                got[(n, ch)] = float(row["v_identity"])
    if len(got) == 2 * len(cands):
        gvh = {n: got[(n, "VH")] for n in cands}
        gvl = {n: got[(n, "VL")] for n in cands}
        germ_src = f"직접 실행 · ANARCI --assign_germline {len(got)} 체인 {time.time()-t0:.2f}초"
    else:
        gp = find_one("germline_all_candidates.csv", quiet=True)
        g = pd.read_csv(gp)
        gvh = {n: float(g[(g.candidate == n) & (g.chain == "VH")]["v_identity"].iloc[0]) for n in cands if (g.candidate == n).any()}
        gvl = {n: float(g[(g.candidate == n) & (g.chain == "VL")]["v_identity"].iloc[0]) for n in cands if (g.candidate == n).any()}
        germ_src = f"레퍼런스 · {gp}"

# (3) nativeness — Ch.07 의 AbNatiV 셀은 체크포인트 33분/2.6GB 때문에 기본 비활성이고,
#     켜도 결과가 모델별 abnativ/*_seq_scores.csv 로 흩어져 이 챕터가 읽는 합본 형식이 아니에요.
abn_dir = GUIDE_ROOT / "07_nativeness" / "my_run"
abn_merged = sorted(abn_dir.rglob("abnativ_summary_all_models.csv"))
abn_raw = sorted(abn_dir.glob("abnativ/*_seq_scores.csv"))
if abn_merged:
    abn_path, abn_src = abn_merged[0], f"내 결과 · {abn_merged[0]}"
else:
    abn_path = find_one("abnativ_summary_all_models.csv", quiet=True)
    abn_src = f"레퍼런스 · {abn_path}"
    if abn_raw:
        abn_src += f" (Ch.07 의 raw 산출물 {len(abn_raw)}개는 모델별로 나뉜 형식이라 합본으로 못 읽어요)"
abn = pd.read_csv(abn_path)
a1 = abn[(abn.model_generation == "AbNatiV1") & (abn.variant.str.endswith("_VH"))]
nat = {str(r.variant).split("_")[0]: float(r.overall_score) for r in a1.itertuples()}

# (4) naturalness — 참고 열
abr_path = find_prev("07_nativeness", "abroberta_scores_summary.csv", quiet=True)
abr = pd.read_csv(abr_path)
ntr = abr[abr.chain == "paired"].set_index("variant")["mean_logp"].to_dict()

# (5) CDR 보존 · (6) liability 신규 — Ch.04 CDR 표, Ch.09 정규식
ct_path = find_prev("04_sequence_qc", "cdr_table_imgt.csv", quiet=True)
ct = pd.read_csv(ct_path)
CDR_H3 = str(ct[(ct.chain == "H") & (ct.cdr == "CDR3")]["sequence"].iloc[0])
MOTIFS = {"N-glycosylation": r"N[^P][ST]", "deamidation": r"N[GS]",
          "isomerization": r"DG", "oxidation": r"[MW]"}

def scan(seq):
    """서열 → {모티프: 1-based 위치 집합}"""
    return {m: {x.start() + 1 for x in re.finditer(p, seq)} for m, p in MOTIFS.items()}

par_scan = {"VH": scan(VH), "VL": scan(VL)}

# (7) 구조 — Ch.08 이 접은 후보만 값이 있어요
rm_path = find_prev("08_structure", "cdr_h3_rmsd_summary.csv", quiet=True)
rm = pd.read_csv(rm_path)
h3_rmsd = float(rm[rm.metric.str.startswith("cdr_h3")]["value_angstrom"].iloc[0])
fw_rmsd = float(rm[rm.metric.str.startswith("framework")]["value_angstrom"].iloc[0])

rows = []
for n, (h, l) in cands.items():
    lost = [f"{r['chain']}-{r['cdr']}" for _, r in ct.iterrows()
            if str(r["sequence"]) not in (h if r["chain"] == "H" else l)]
    new_g = len(scan(h)["N-glycosylation"] - par_scan["VH"]["N-glycosylation"]) \\
          + len(scan(l)["N-glycosylation"] - par_scan["VL"]["N-glycosylation"])
    new_all = sum(len(scan(h)[m] - par_scan["VH"][m]) + len(scan(l)[m] - par_scan["VL"][m])
                  for m in MOTIFS)
    rows.append({"candidate": n,
                 "humanness": round(hum.get(n, np.nan), 4),
                 "nativeness_AbNatiV1_VH": round(nat[n], 4) if n in nat else np.nan,
                 "germline_V_VH": gvh.get(n, np.nan), "germline_V_VL": gvl.get(n, np.nan),
                 "germline_V_mean": round(np.mean([gvh[n], gvl[n]]), 4) if n in gvh and n in gvl else np.nan,
                 "CDR_kept": 6 - len(lost), "CDR_lost": ";".join(lost) or "-",
                 "CDR_H3_kept": CDR_H3 in h,
                 "new_glyc": new_g, "new_liabilities": new_all,
                 "naturalness_AbRoBERTa": round(ntr[n], 4) if n in ntr else np.nan,
                 "cdr_h3_rmsd": 0.0 if n == "parental" else (h3_rmsd if n == "sapiens" else np.nan)})

mt = pd.DataFrame(rows).set_index("candidate")
mt.to_csv(MY / "metrics_table.csv")
print("[출처]")
print("  humanness  ←", hum_src)
print("  germline   ←", germ_src)
print("  nativeness ←", abn_src)
print("  naturalness ←", abr_path)
print("  CDR 표     ←", ct_path)
print("  구조 RMSD  ←", rm_path)
print("→", MY / "metrics_table.csv")
display(mt)

nan_ax = {k: list(mt.index[mt[k].isna()]) for k in
          ("nativeness_AbNatiV1_VH", "cdr_h3_rmsd", "germline_V_mean", "humanness")
          if mt[k].isna().any()}
print()
for k, v in nan_ax.items():
    print(f"  결측 — {k}: {', '.join(v)}")
print(f"판정 — 5후보 × 6축 중 실제로 채워진 칸은 {int(mt[['humanness','nativeness_AbNatiV1_VH','germline_V_mean','new_liabilities','cdr_h3_rmsd']].notna().sum().sum())}/25 개예요.")
print("빈 칸은 '나쁨' 이 아니라 '측정 안 함' 이에요. 3절에서 이 둘을 다르게 다뤄요.")'''),

md("""## 3) 직접 실행 — 가중합 랭킹과 결측 처리 (본문 10.1.1 · 10.2)

가중치는 본문 10.1.1 값을 그대로 씁니다.

```
Final score = 0.25 humanness + 0.20 nativeness + 0.20 CDR/structure 보존
            + 0.15 developability + 0.10 germline 일관성 + 0.10 전문가 review
```

문제는 **빈 칸**이에요. 본문 10.2 가 못 박듯 `null` 은 0 이 아니에요 — "측정 안 함" 과 "나쁨" 은 다른 상태고, 빈 칸을 0 으로 메우면 그 축의 가중치를 **통째로 감점**으로 바꿔요. 그래서 결측 축은 **분모에서 빼고**, 남은 축으로 가중치를 다시 100% 가 되게 나눠요.

```
score = Σ(w_k · norm_k) / Σ(w_k)     ← 둘 다 '값이 있는 축' 에 대해서만
```

축을 0~1 로 접는 방법도 축마다 달라요.

| 축 | 접는 법 | 왜 |
|---|---|---|
| humanness · nativeness · germline | 후보 5종 min-max | 상대 비교용 점수라 절대 기준선이 없어요 |
| CDR/structure 보존 | `1 − RMSD / 2 Å` (0~1 clip) | RMSD 는 절대 스케일이 있어요. 측정값이 parental·Sapiens 둘뿐이라 min-max 를 쓰면 0/1 플래그가 돼요 |
| developability | `(최대 − 신규건수) / 최대` | 신규 0건이 곧 만점이라 0 에 앵커를 걸어요 |
| 전문가 review | 접지 않아요 | 사람 판단이라 이 노트북이 채울 수 없어요 → 전 후보 결측 |"""),
co('''W = {"humanness": 0.25, "nativeness": 0.20, "structure": 0.20,
     "developability": 0.15, "germline": 0.10, "expert_review": 0.10}

def minmax(s):
    """값 있는 칸만 0~1 로. 전부 같으면 0.5, 결측은 결측 그대로 둬요."""
    s = s.astype(float)
    ok = s.notna()
    if ok.sum() == 0 or s[ok].max() == s[ok].min():
        return s.where(~ok, 0.5)
    return (s - s[ok].min()) / (s[ok].max() - s[ok].min())

def build_norm(tbl):
    nm = pd.DataFrame(index=tbl.index)
    nm["humanness"]  = minmax(tbl["humanness"])
    nm["nativeness"] = minmax(tbl["nativeness_AbNatiV1_VH"])
    nm["germline"]   = minmax(tbl["germline_V_mean"])
    nm["structure"]  = (1 - tbl["cdr_h3_rmsd"].astype(float) / 2.0).clip(0, 1)
    mx = float(tbl["new_liabilities"].max())
    nm["developability"] = 1.0 if mx == 0 else (mx - tbl["new_liabilities"]) / mx
    nm["expert_review"] = np.nan          # 사람 판단 — 결측으로 남겨요
    return nm[list(W)]

def weighted_score(nm):
    num = sum((nm[k] * w).fillna(0.0) for k, w in W.items())
    den = sum(nm[k].notna() * w for k, w in W.items())
    return (num / den).round(4), den.round(2), (num / sum(W.values())).round(4)

norm = build_norm(mt)
score, used_w, score_if_zero = weighted_score(norm)

rank = mt.copy()
rank["score"] = score
rank["used_weight"] = used_w
rank["missing_axes"] = [", ".join(k for k in W if pd.isna(norm.loc[i, k])) for i in norm.index]
out = rank.sort_values("score", ascending=False)
display(out[["score", "used_weight", "missing_axes", "humanness", "nativeness_AbNatiV1_VH",
             "germline_V_mean", "new_liabilities", "cdr_h3_rmsd"]])

print("[정규화 후 축별 점수 — 빈 칸이 결측]")
display(norm.round(3))

print("[결측을 0 으로 메웠다면]")
delta = (score - score_if_zero).round(4)
for n in out.index:
    print(f"  {n:18s} 재정규화 {score[n]:.4f} · 0 대입 {score_if_zero[n]:.4f} · 차이 {delta[n]:+.4f}"
          f"  (사용 가중치 {used_w[n]:.2f}/1.00)")
gap = float(out["score"].iloc[0] - out["score"].iloc[1])
worst = delta.drop(index=out.index[0]).idxmax()
print(f"\\n판정 — 0 대입은 결측이 많은 후보를 최대 {delta.max():.4f} 깎아요({worst} 가 가장 크게 손해).")
if delta.max() > gap:
    print(f"이 감점폭은 1·2위 격차 {gap:.4f} 보다 커요 — 0 으로 메웠다면 순위가 뒤집혔을 크기예요.")
else:
    print(f"이번엔 1·2위 격차 {gap:.4f} 보다 작아 순서는 유지되지만, 점수는 근거 없이 낮아져요.")
print("측정하지 않은 축 때문에 후보가 떨어지면 그건 후보의 문제가 아니라 데이터의 구멍이에요 — 채워서 다시 재요.")
low = out.index[out["used_weight"] < 0.7]
print("사용 가중치 0.70 미만(근거가 얇아 점수를 그대로 믿기 어려운 후보) —",
      ", ".join(low) if len(low) else "없음")'''),

md("""## 4) 직접 실행 — hard filter (본문 10.1.2)

가중합은 **치명적 결함을 묻어요.** CDR-H3 가 깨져 결합이 사라진 후보도 humanness 가 높으면 총점 1위에 오를 수 있거든요. 그래서 점수와 **별개로** 무조건 걸리는 선을 둬요.

본문 10.1.2 의 항목은 7개인데, 이 랩의 환경에서 **실제로 잴 수 있는 건 그중 일부**예요. 못 재는 항목을 조용히 빼면 "통과" 가 실제보다 후해지니까, 무엇을 재고 무엇을 못 재는지 먼저 표로 박아요."""),
co('''FILTERS = pd.DataFrame([
    {"본문 10.1.2 항목": "CDR-H3 핵심 residue 변경", "이 랩": "측정",
     "근거": "Ch.04 CDR 표의 CDR-H3 문자열이 후보 VH 에 그대로 있는지"},
    {"본문 10.1.2 항목": "알려진 paratope residue 변경", "이 랩": "못 잼",
     "근거": "이 프로젝트에 paratope 목록이 없어요 (본문 10.2 YAML 도 known_paratope_residues: [])"},
    {"본문 10.1.2 항목": "VH/VL interface core residue 변경", "이 랩": "못 잼",
     "근거": "interface core 잔기 정의와 접촉 분석을 이 가이드에서 돌리지 않았어요"},
    {"본문 10.1.2 항목": "CDR 구조 RMSD 급증", "이 랩": "부분",
     "근거": f"Ch.08 이 접은 후보만 값이 있어요 (기준 1.0 Å · framework 자체는 {fw_rmsd:.4f} Å)"},
    {"본문 10.1.2 항목": "CDR/paratope 신규 N-glycosylation", "이 랩": "측정",
     "근거": "Ch.09 정규식 N[^P][ST] · 사슬 전체 기준 (CDR 국한 판정은 Ch.09 4절)"},
    {"본문 10.1.2 항목": "severe hydrophobic/charge patch 증가", "이 랩": "못 잼",
     "근거": "구조 기반 SAP·charge patch 미실행 (Ch.09 5절에서 미실행으로 정리)"},
    {"본문 10.1.2 항목": "AbNatiV/OASis 가 parental 대비 미개선", "이 랩": "측정",
     "근거": "AbNatiV1 VH overall_score 를 parental 과 비교. 값이 없는 후보는 Sapiens humanness 로 대신 재고 표에 표기"},
])
display(FILTERS)

par_nat = nat.get("parental", np.nan)
par_hum = float(mt.loc["parental", "humanness"])
RMSD_CUT = 1.0

flags, basis = {}, {}
for n in mt.index:
    r = mt.loc[n]
    f = []
    if not bool(r["CDR_H3_kept"]):
        f.append("CDR-H3 변경")
    if int(r["CDR_kept"]) < 6:
        f.append(f"CDR 파손 {6 - int(r['CDR_kept'])}개({r['CDR_lost']})")
    if int(r["new_glyc"]) > 0:
        f.append(f"신규 N-glyc {int(r['new_glyc'])}건")
    if pd.notna(r["cdr_h3_rmsd"]) and float(r["cdr_h3_rmsd"]) >= RMSD_CUT:
        f.append(f"CDR-H3 RMSD {float(r['cdr_h3_rmsd']):.3f} Å ≥ {RMSD_CUT} Å")
    if n in nat and pd.notna(par_nat):
        basis[n] = "AbNatiV1 VH"
        if float(r["nativeness_AbNatiV1_VH"]) <= par_nat:
            f.append("nativeness 미개선")
    else:
        basis[n] = "Sapiens humanness(AbNatiV 결측 대체)"
        if float(r["humanness"]) <= par_hum:
            f.append("humanness 미개선 · AbNatiV 결측 대체 판정")
    flags[n] = "; ".join(f) or "pass"
flags["parental"] = "(baseline)"

out["hard_filter"] = [flags[n] for n in out.index]
out["filter_basis"] = [basis[n] for n in out.index]
out[["score", "used_weight", "missing_axes", "hard_filter", "filter_basis", "humanness",
     "nativeness_AbNatiV1_VH", "germline_V_mean", "new_liabilities", "cdr_h3_rmsd",
     "CDR_kept", "CDR_lost", "naturalness_AbRoBERTa"]].to_csv(MY / "ranking.csv")
display(out[["score", "hard_filter", "filter_basis", "CDR_kept", "CDR_lost", "new_glyc", "cdr_h3_rmsd"]])
print("→", MY / "ranking.csv")

adv = out[out.hard_filter == "pass"]
print("hard filter 통과 —", ", ".join(adv.index) if len(adv) else "없음")
top = out.index[0]
if top != "parental" and flags[top] != "pass":
    print(f"판정 — 점수 1위는 {top}({out.loc[top, 'score']:.4f}) 인데 hard filter 에 걸려요 [{flags[top]}].")
    print("가중합이 왜 결론이 될 수 없는지가 여기서 드러나요 — 점수는 평균이고, 결합은 평균으로 안 붙어요.")
if len(adv):
    pick = adv.index[0]
    print(f"실험으로 넘길 후보는 {pick} 예요 (통과 후보 중 점수 최상위 {out.loc[pick, 'score']:.4f}).")
else:
    print("통과 후보가 없으면 backmutation 을 걸어 다시 돌려요 — 걸린 항목을 되돌리는 게 다음 라운드의 목표예요.")
print(f"단, 못 잰 항목이 {int((FILTERS['이 랩'] == '못 잼').sum())}종 남아 있어요. "
      "'pass' 는 '이 랩이 잰 범위에서 통과' 라는 뜻이지 무결이 아니에요.")'''),

md("""## 5) 그림 — 최종 순위와 축별 기여 (본문 10.1.1 · 10.2)

표만 보면 "왜 이 후보가 1위인지" 가 안 보여요. 점수를 **축별로 쪼개 쌓은 막대**로 그리면, 어느 축이 그 후보를 밀어 올렸는지가 한눈에 들어와요.

여기서 제일 조심할 게 **결측**이에요. 빈 칸을 0 으로 그리면 "재지 않은 축" 이 "0 점인 축" 처럼 보여서, 3절에서 재정규화로 바로잡은 걸 그림이 도로 망가뜨려요. 그래서 그림도 두 가지를 분리해요.

| 그림 요소 | 뜻 |
|---|---|
| 색칠된 구간 | 실제로 측정한 축의 기여 `w × 정규화값` |
| **빗금 구간** | 결측 축을 분모에서 빼서 되돌아온 몫 = `재정규화 점수 − 0 대입 점수`. **0 으로 메웠다면 사라지는 부분** |
| 오른쪽 격자 | 후보 × 축 커버리지. 빗금 + `미측정` 이 결측 칸이에요 |
| 빨간 후보 이름 | hard filter 에 걸린 후보(4절 결과) |"""),
co('''import humanization_viz          # import 만으로 한글 폰트가 등록돼요(안 하면 제목·축이 □ 로 깨져요)
import matplotlib.pyplot as plt
from IPython.display import Image, display

AX_COLOR = {"humanness": "#3f6fb5", "nativeness": "#5aa2c9", "structure": "#7bbf6a",
            "developability": "#e0a63c", "germline": "#c1666b", "expert_review": "#9b8ec4"}
AX_LABEL = {k: f"{k} ({W[k]:.2f})" for k in W}

ordr = list(out.index)[::-1]                 # 아래→위 = 꼴찌→1위 (막대는 위가 1위로 보이게)
yy   = np.arange(len(ordr))

fig, (axL, axR) = plt.subplots(1, 2, figsize=(13.6, 0.95 * len(ordr) + 2.8),
                               gridspec_kw={"width_ratios": [2.3, 1.15]})

left = np.zeros(len(ordr))
for k in W:                                   # ① 측정한 축만 쌓아요 — 결측은 아예 안 그려요(0 으로 안 메움)
    v = np.array([0.0 if pd.isna(norm.loc[n, k]) else float(norm.loc[n, k]) * W[k] for n in ordr])
    axL.barh(yy, v, left=left, height=0.62, color=AX_COLOR[k],
             edgecolor="white", linewidth=0.7, label=AX_LABEL[k])
    left += v

# ② 결측 축을 분모에서 뺀 덕분에 되돌아온 몫 — 0 대입이면 사라지는 부분이라 빗금으로 따로 그려요
boost = np.array([float(score[n] - score_if_zero[n]) for n in ordr])
axL.barh(yy, boost, left=left, height=0.62, color="#f4f4f4", edgecolor="#8c8c8c",
         hatch="///", linewidth=0.9, label="결측 축 재정규화 몫 (0 대입이면 사라짐)")

for i, n in enumerate(ordr):
    axL.text(float(score[n]) + 0.012, yy[i], f"{score[n]:.4f}", va="center", ha="left",
             fontsize=10, fontweight="bold")

hf = out["hard_filter"].to_dict()
axL.set_yticks(yy)
axL.set_yticklabels([f"{n}\\n(사용 가중치 {used_w[n]:.2f})" for n in ordr], fontsize=9)
for t, n in zip(axL.get_yticklabels(), ordr):
    if hf.get(n) not in ("pass", "(baseline)"):
        t.set_color("#b03030")                # hard filter 탈락 = 빨간 이름
axL.set_xlim(0, max(0.9, float(score.max()) + 0.16))
axL.set_xlabel("final score = Σ(w · 정규화값) / Σ(측정된 w)")
axL.set_title("최종 순위 — 축별 기여 누적 (빨간 이름 = hard filter 탈락)", fontweight="bold")
axL.grid(axis="x", alpha=0.25); axL.set_axisbelow(True)
axL.legend(fontsize=8, loc="lower right", framealpha=0.95)

AXES = list(W)                                # ③ 커버리지 격자 — 어느 후보의 어느 축이 비었는지
for i, n in enumerate(ordr):
    for j, k in enumerate(AXES):
        v = norm.loc[n, k]
        if pd.isna(v):
            axR.add_patch(plt.Rectangle((j - 0.46, i - 0.40), 0.92, 0.80, facecolor="#f4f4f4",
                                        edgecolor="#8c8c8c", hatch="///", linewidth=0.9))
            axR.text(j, i, "미측정", ha="center", va="center", fontsize=7.5, color="#555555",
                     bbox={"facecolor": "white", "edgecolor": "none", "pad": 1.2})
        else:
            axR.add_patch(plt.Rectangle((j - 0.46, i - 0.40), 0.92, 0.80, facecolor=AX_COLOR[k],
                                        alpha=0.22 + 0.66 * float(v), edgecolor="white", linewidth=0.9))
            axR.text(j, i, f"{float(v):.2f}", ha="center", va="center", fontsize=8.5, color="#101010")
axR.set_xlim(-0.5, len(AXES) - 0.5); axR.set_ylim(-0.6, len(ordr) - 0.4)
axR.set_xticks(range(len(AXES))); axR.set_xticklabels(AXES, fontsize=8, rotation=30, ha="right")
axR.set_yticks(yy); axR.set_yticklabels(ordr, fontsize=9)
axR.set_title("축 커버리지 — 빗금 = 측정 안 함 (0 점이 아님)", fontweight="bold")
for s in ("top", "right", "left", "bottom"):
    axR.spines[s].set_visible(False)
axR.tick_params(length=0)

fig.tight_layout()
png = MY / "10_ranking.png"; fig.savefig(png, dpi=150, bbox_inches="tight")
display(Image(str(png)))          # 저장만 하면 셀에 안 보여요 — 반드시 표시까지
plt.close(fig)
print("→", png)'''),
co('''miss = {n: [k for k in W if pd.isna(norm.loc[n, k])] for n in out.index}
for n in out.index:
    print(f"  {n:18s} score {score[n]:.4f} = 측정분 {score_if_zero[n]:.4f} + 재정규화분 {score[n]-score_if_zero[n]:.4f}"
          f"  · 결측 {', '.join(miss[n]) or '없음'}")
mostmiss = max(miss, key=lambda n: len(miss[n]))
gainv    = {n: float(score[n] - score_if_zero[n]) for n in out.index}
bigg     = max(gainv, key=gainv.get)
print(f"\\n판정 — 빗금은 '0 점' 이 아니라 '재지 않은 축' 이에요. 축이 가장 많이 빈 후보는 {mostmiss}"
      f" ({len(miss[mostmiss])}축 결측 · 사용 가중치 {used_w[mostmiss]:.2f}) 라, 오른쪽 격자의 빗금 칸이 제일 많아요.")
print(f"       빗금 막대가 가장 넓은 후보는 {bigg} ({gainv[bigg]:.4f}) — 0 으로 메웠다면 이만큼이 그대로 감점이 됐을 몫이에요.")
print("       색칠 구간이 0 인 칸(격자 0.00)은 '재긴 쟀는데 후보 중 꼴찌' 라는 뜻이라 빗금과 전혀 다른 상태예요 — 둘을 같은 색으로 그리면 안 돼요.")
print("       빗금이 넓을수록 점수의 근거가 얇다는 뜻이라, 순위를 그대로 믿지 말고 그 축부터 채워야 해요.")
print("       빨간 이름은 점수와 무관하게 hard filter 에 걸린 후보예요 — 막대가 길어도 실험으로 넘기지 않아요.")'''),

md("""## 6) 직접 실행 — candidate report · GuideDB (본문 10.1.3 · 10.2)

후보 하나를 실험 담당자에게 넘기는 최소 단위가 본문 10.1.3 의 한 장짜리 표예요. 마지막 줄은 반드시 **advance / backmutate / reject** 중 하나로 끝나야 해요.

같은 내용을 본문 10.2 의 GuideDB YAML 로도 떨어뜨려요. 두 형식의 차이는 하나예요 — CSV 는 사람이 읽고, YAML 은 다음 라운드가 읽어요. 그래서 YAML 에서는 측정하지 않은 값을 **`null` 그대로** 남겨요."""),
co('''import yaml

def mutations(par, cand):
    """parental raw 1-based 치환 목록. 길이가 다르면(indel) 정렬로 이어 붙여 세요."""
    if len(par) == len(cand):
        return [f"{a}{i+1}{b}" for i, (a, b) in enumerate(zip(par, cand)) if a != b], 0
    muts, indel = [], 0
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, par, cand, autojunk=False).get_opcodes():
        if op == "replace":
            for k in range(min(i2 - i1, j2 - j1)):
                muts.append(f"{par[i1+k]}{i1+k+1}{cand[j1+k]}")
        if op in ("replace", "insert", "delete"):
            indel += abs((i2 - i1) - (j2 - j1))
    return muts, indel

report_rows = []
for n in out.index:
    if n == "parental":
        continue
    ch, cl = cands[n]
    mh, ih = mutations(VH, ch)
    ml, il = mutations(VL, cl)
    r = out.loc[n]
    report_rows.append({
        "Candidate ID": f"HZ_{n}_01", "Method": n,
        "VH mutations": f"{len(mh)}개" + (f" +indel {ih}" if ih else "") + " — " + ", ".join(mh[:6]) + ("…" if len(mh) > 6 else ""),
        "VL mutations": f"{len(ml)}개" + (f" +indel {il}" if il else "") + " — " + ", ".join(ml[:6]) + ("…" if len(ml) > 6 else ""),
        "CDR mutations": "none (6/6 보존)" if int(r.CDR_kept) == 6 else f"{6-int(r.CDR_kept)}개 파손 — {r.CDR_lost}",
        "Humanness (paired)": r.humanness,
        "AbNatiV1 VH": r["nativeness_AbNatiV1_VH"],
        "Germline V (VH·VL 평균)": r["germline_V_mean"],
        "Structure": "미측정" if pd.isna(r.cdr_h3_rmsd) else f"CDR-H3 RMSD {float(r.cdr_h3_rmsd):.4f} Å",
        "Developability": "clean" if int(r.new_liabilities) == 0 else f"신규 liability {int(r.new_liabilities)}건(N-glyc {int(r.new_glyc)})",
        "Final score": r.score, "Used weight": r.used_weight,
        "Recommendation": "advance" if r.hard_filter == "pass" else f"reject/backmutate ({r.hard_filter})",
    })
rep = pd.DataFrame(report_rows)
rep.to_csv(MY / "candidate_report.csv", index=False)
display(rep[["Candidate ID", "CDR mutations", "Humanness (paired)", "Final score", "Used weight", "Recommendation"]])

gl = pd.read_csv(find_one("germline_assignment.csv", quiet=True))
def gene_of(chain, gtype):
    q = gl[(gl.chain == chain) & (gl.gene_type == gtype)]
    return (str(q["gene"].iloc[0]), float(q["identity_pct"].iloc[0])) if len(q) else ("unknown", float("nan"))
hv, hv_id = gene_of("H", "V")
lv, lv_id = gene_of("L", "V")
hj, hj_id = gene_of("H", "J")

def nn(x):
    """측정 안 한 값은 0 이 아니라 null 로 — 본문 10.2 의 규칙."""
    return None if pd.isna(x) else float(x)

db = {
    "project": {"id": "HZ_running_example", "parent_clone": "parental",
                "date": time.strftime("%Y-%m-%d")},
    "input_sequences": {"heavy": {"name": "parental_H", "sequence": VH, "species": "mouse"},
                        "light": {"name": "parental_L", "sequence": VL, "species": "mouse"}},
    "annotation": {
        "numbering_scheme": "IMGT", "cdr_definition": "IMGT",
        "heavy_germline": hv, "heavy_germline_v_identity_pct": round(hv_id, 2),
        "light_germline": lv, "light_germline_v_identity_pct": round(lv_id, 2),
        "heavy_j_germline": hj, "heavy_j_identity_pct": round(hj_id, 2),
        "heavy_j_note": "동점 tie-break 이라 도구마다 갈려요 (Ch.04 참고)",
        "heavy_cdr3": CDR_H3, "known_paratope_residues": [],
    },
    "scoring": {"weights": W, "missing_policy": "결측 축은 분모에서 제외하고 가중치 재정규화 (0 대입 금지)",
                "germline_metric": "ANARCI V identity · VH·VL 평균"},
    "candidates": [
        {"id": f"HZ_{n}_01", "method": n,
         "sequences": {"heavy": cands[n][0], "light": cands[n][1]},
         "mutations": {"heavy": len(mutations(VH, cands[n][0])[0]),
                       "light": len(mutations(VL, cands[n][1])[0])},
         "scores": {"humanness_sapiens_paired": nn(out.loc[n, "humanness"]),
                    "nativeness_abnativ1_vh": nn(out.loc[n, "nativeness_AbNatiV1_VH"]),
                    "naturalness_abroberta_paired": nn(out.loc[n, "naturalness_AbRoBERTa"]),
                    "germline_v_identity_mean": nn(out.loc[n, "germline_V_mean"]),
                    "final_score": nn(out.loc[n, "score"]),
                    "used_weight": nn(out.loc[n, "used_weight"])},
         "structure": {"cdr_h3_rmsd": nn(out.loc[n, "cdr_h3_rmsd"])},
         "developability": {"new_liabilities": int(out.loc[n, "new_liabilities"]),
                            "new_n_glyc": int(out.loc[n, "new_glyc"])},
         "cdr_preserved": f"{int(out.loc[n, 'CDR_kept'])}/6",
         "hard_filter": out.loc[n, "hard_filter"],
         "decision": "advance" if out.loc[n, "hard_filter"] == "pass" else "reject/backmutate"}
        for n in out.index if n != "parental"
    ],
}
(MY / "candidate_report.yaml").write_text(yaml.safe_dump(db, allow_unicode=True, sort_keys=False))
print("→", MY / "candidate_report.csv", "·", MY / "candidate_report.yaml")

print("\\n[GuideDB — annotation · scoring 블록]")
print(yaml.safe_dump({k: db[k] for k in ("annotation", "scoring")}, allow_unicode=True, sort_keys=False))
print("[GuideDB — 후보 1건]")
print(yaml.safe_dump({"candidates": [{k: v_ for k, v_ in db["candidates"][0].items() if k != "sequences"}]},
                     allow_unicode=True, sort_keys=False))

nulls = sum(1 for cd in db["candidates"] for v_ in list(cd["scores"].values()) + list(cd["structure"].values()) if v_ is None)
print(f"\\n판정 — YAML 에 남은 null {nulls}개는 '아직 안 쟀다' 는 기록이에요. 0 으로 메웠다면 이 정보가 사라져요.")
print("다음 라운드는 이 null 을 채우는 것부터 시작해요 — 무엇을 더 재야 하는지가 파일 안에 적혀 있는 셈이에요.")'''),

md("""## 7) 레퍼런스 대조 (본문 10.1.1)

같은 코드에 **커밋된 `data/` 만** 넣어 돌려요. 실행을 건너뛴 사람도 같은 표에 도달하는지, 내 순위가 레퍼런스 순위와 같은지 확인하는 절이에요."""),
co('''def ref_file(name):
    """이 절만은 내 결과가 아니라 커밋된 data/ 를 씁니다 — 대조의 기준면이라서요."""
    p = REF / name
    assert p.exists(), f"{p} 가 없어요. 저장소를 얕게 클론했다면 data/ 가 빠졌는지 확인하세요."
    return p

ref_v = read_fasta(ref_file("variants.fasta"))
ref_cands = {n: (ref_v[f"{n}_VH"], ref_v[f"{n}_VL"]) for n in cands}
ref_hum = pd.read_csv(ref_file("humanness_all_candidates.csv"))
ref_hum = ref_hum[ref_hum.chain == "paired"].set_index("candidate")["mean_self_prob"]
ref_gm = pd.read_csv(ref_file("germline_all_candidates.csv")).groupby("candidate")["v_identity"].mean()
ref_abn = pd.read_csv(ref_file("abnativ_summary_all_models.csv"))
ref_abn = ref_abn[(ref_abn.model_generation == "AbNatiV1") & (ref_abn.variant.str.endswith("_VH"))]
ref_nat = {str(r.variant).split("_")[0]: float(r.overall_score) for r in ref_abn.itertuples()}

ref_rows = []
for n, (h, l) in ref_cands.items():
    lost = sum(1 for _, r in ct.iterrows() if str(r["sequence"]) not in (h if r["chain"] == "H" else l))
    new_all = sum(len(scan(h)[m] - par_scan["VH"][m]) + len(scan(l)[m] - par_scan["VL"][m]) for m in MOTIFS)
    ref_rows.append({"candidate": n, "humanness": float(ref_hum.get(n, np.nan)),
                     "nativeness_AbNatiV1_VH": ref_nat.get(n, np.nan),
                     "germline_V_mean": float(ref_gm.get(n, np.nan)),
                     "new_liabilities": new_all, "CDR_kept": 6 - lost,
                     "cdr_h3_rmsd": 0.0 if n == "parental" else (h3_rmsd if n == "sapiens" else np.nan)})
ref_mt = pd.DataFrame(ref_rows).set_index("candidate")
ref_score, ref_w, _ = weighted_score(build_norm(ref_mt))
ref_out = ref_mt.assign(score=ref_score, used_weight=ref_w).sort_values("score", ascending=False)
display(ref_out[["score", "used_weight", "humanness", "nativeness_AbNatiV1_VH",
                 "germline_V_mean", "new_liabilities", "CDR_kept"]].round(4))

mine, refo = list(out.index), list(ref_out.index)
print("내 순위      :", " > ".join(mine))
print("레퍼런스 순위:", " > ".join(refo))
if mine == refo:
    print("판정 — 두 순위가 같아요. 실행을 건너뛴 사람도 같은 결론에 도달해요.")
else:
    diff = [n for n in mine if mine.index(n) != refo.index(n)]
    print(f"판정 — 순위가 다른 후보 {len(diff)}개 ({', '.join(diff)}). 내가 만든 후보 서열이 레퍼런스와 다르면 정상이에요.")
print("두 표의 숫자 자체가 다르면 후보 서열이 다른 것이고, 숫자가 같은데 순위만 다르면 가중치를 바꾼 거예요.")'''),

md("""## 8) in silico 는 여기까지 — 실험으로 넘기기 (본문 10.3 · 10.4)

이 가이드가 답한 건 **"계산상 더 사람답고 그럴듯해졌다"** 까지예요. 실제로 붙는지·안정한지·만들어지는지는 컴퓨터가 단정할 수 없어요. 그래서 랭킹의 결론은 "이게 정답" 이 아니라 **"이 순서로 실험한다"** 예요.

본문 10.3 의 최소 검증 순서에서 앞의 둘은 관문이고, **진짜 판정은 ③ 결합력**에서 나요. humanization 의 제1 실패 모드가 "사람다워졌지만 안 붙는다" 라서, parental 과 humanized 를 같은 조건에서 SPR/BLI 로 재 KD 가 유지되는지부터 봐요. 여기서 무너지면 뒤의 Tm·응집 데이터는 볼 이유가 없어요.

그리고 한 번으로 끝내지 않아요. 본문 10.4 의 **lab-in-the-loop** 은 예측 → wet 검증 → **그 실험 데이터로 모델 재학습** → 다시 예측으로 고리를 닫는 구조예요. Genentech/Roche 사례는 4개 표적(EGFR·IL-6·HER2·OSM)에 **1,800개 넘는 변이체**를 설계·실험하고 **4 라운드**로 표적마다 **3–100× 결합력 향상**(최고 ~100 pM)을 얻었어요. 그 사례는 humanization 이 아니라 affinity maturation 이라, 가져올 건 숫자가 아니라 **루프 구조**예요 — oracle 을 결합력 + humanness/면역원성으로 바꿔 끼우면 그대로 적용돼요."""),
co('''WET = pd.DataFrame([
    {"순서": 1, "단계": "소량 발현", "방법": "HEK293/CHO transient", "역할": "관문"},
    {"순서": 2, "단계": "정제", "방법": "Protein A/G · SEC purity", "역할": "관문"},
    {"순서": 3, "단계": "결합력", "방법": "ELISA 또는 BLI/SPR (parental 대비 KD 유지)", "역할": "★1순위 판정"},
    {"순서": 4, "단계": "안정성", "방법": "DSF/Tm · accelerated stability", "역할": "판정"},
    {"순서": 5, "단계": "응집", "방법": "SEC-MALS 또는 DLS", "역할": "판정"},
    {"순서": 6, "단계": "특이성", "방법": "cross-reactivity / polyspecificity panel", "역할": "판정"},
    {"순서": 7, "단계": "기능 assay", "방법": "neutralization · blocking · internalization 등", "역할": "판정"},
])
picks = list(adv.index) if len(adv) else []
WET["대상 후보"] = ", ".join(picks) if picks else "backmutation 후 재평가"
WET["parental 대조"] = ["필요" if s in (1, 2) else "필수" for s in WET["순서"]]
WET.to_csv(MY / "wet_lab_plan.csv", index=False)
display(WET)
print("→", MY / "wet_lab_plan.csv")

print(f"\\n판정 — in silico 로 좁힌 후보는 {len(cands)-1}종 중 {len(picks)}종이에요"
      + (f" ({', '.join(picks)})." if picks else "."))
print(f"첫 실험은 3번 결합력이에요 — parental 과 {picks[0] if picks else '재설계 후보'} 를 같은 조건에서 SPR/BLI 로 재고,")
print("KD 가 parental 대비 유지되면 4~7번으로 넘어가요. 무너지면 backmutation 으로 되돌아와요.")
print("그 실험값을 다시 이 표(metrics_table.csv)의 새 열로 붙이면 고리가 닫혀요 — 그게 lab-in-the-loop 이에요.")'''),

md("""## 이 랩에서 확인한 것

1. 랭킹은 **본문 10.1.1 의 가중합 + 10.1.2 의 hard filter** 두 층이에요. 점수는 평균이고, 결합은 평균으로 붙지 않아요.
2. 결측은 **분모에서 빼고 재정규화**해요. 0 으로 메우면 측정하지 않은 축이 그대로 감점이 돼요 — 이 랩에서는 구조 RMSD 가 없는 후보가 **0.21~0.23점** 손해를 보는데, 1·2위 격차보다 큰 값이에요.
3. 실측 지표(후보 5종).
   - **humanness**(Sapiens 재스코어링 paired) — parental 0.7303 · Sapiens **0.8424** · Humatch 0.7988 · AnthroAb 0.7941 · AnthroAb(FR-masked) 0.7136
   - **nativeness**(AbNatiV1 VH) — parental 0.6477 · Sapiens **0.8803** · Humatch 0.8305 · AnthroAb 0.8064 · FR-masked **측정 안 됨**
   - **germline V identity**(VH·VL 평균) — parental **0.72**(VH 0.63 · VL 0.81) → Sapiens 0.835 · Humatch 0.81
   - **CDR 보존** — Humatch **6/6**, AnthroAb(FR-masked) **6/6**, Sapiens **1/6**(CDR-H1 만 보존), AnthroAb(best_score) **1/6**(CDR-L3 만 보존)
   - **구조** — Sapiens CDR-H3 RMSD **0.5406 Å**(framework 0.2707 Å). 나머지 후보는 접지 않아 결측
4. 그래서 **"가장 사람다운 후보"와 "실험으로 넘길 후보"가 달라요.** 점수 1위 Sapiens 는 CDR 5개가 파손돼 hard filter 에 걸리고, 통과하는 건 CDR 을 지킨 Humatch 예요. Sapiens 계열을 쓰려면 Ch.05 의 **CDR 가드 적용본**으로 다시 만들어야 해요.
5. hard filter 7종 중 이 환경에서 잰 건 3종(+구조는 부분)이에요. **paratope 변경 · VH/VL interface core · charge patch** 는 못 쟀으니 `pass` 는 "잰 범위에서 통과" 로 읽어요.
6. 순위 그림(`10_ranking.png`)은 점수를 **축별 기여로 쪼갠 누적 막대**예요. 빗금 구간이 **결측 축을 0 으로 메우지 않아 되돌아온 몫**이라, 그림만 봐도 어느 후보의 점수가 얇은 근거 위에 서 있는지 보여요.
7. 산출물 — `my_run/metrics_table.csv` · `ranking.csv` · `candidate_report.csv` · `candidate_report.yaml`(GuideDB) · `wet_lab_plan.csv` · `10_ranking.png`.

전체 체크리스트·용어집 → **[Ch.11 부록](../11_appendix/11_appendix.md)**"""),
]
cells_all[("10_ranking_report", "10_ranking_lab.ipynb", "10 Ranking & Report Lab")] = c


# ── 저장 ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    total = 0
    for (folder, name, title), cells in cells_all.items():
        total += save(cells, folder, name, title)
    print(f"\n노트북 {len(cells_all)}종 · 총 {total} 셀 생성 완료 (각 챕터 폴더, Colab/로컬 공용).")
