---
title: "항체 데이터베이스·분석 도구 완전 정복 — 공개 DB와 CLI로 배우는 항체 인포매틱스"
subtitle: "SAbDab·OAS·IMGT·Thera-SAbDab 기반 서열·구조·interface·humanness·developability 실습 과정"
series: "Antibody Informatics Complete Course"
version: "v0.3 · 2026-07 실행 검증 (ANARCI 2026.02 · Sapiens 1.1 · IgFold 0.4 · Biopython 1.87)"
language: ko
target_length: "A4 약 40쪽 + 실습 노트북 8종"
---

# 항체 데이터베이스·분석 도구 완전 정복

> **이 과정은 공개 항체 데이터베이스와 CLI 도구를 처음부터 끝까지 다루는 자기완결형(self-contained) 실습 과정입니다.**
> 항체 기본 개념(CDR·epitope·germline)부터 시작해, 공개 DB(SAbDab·OAS·IMGT·Thera-SAbDab) 탐색, 그리고 numbering·humanization·구조예측·interface·developability·repertoire까지 **실제 도구를 돌려가며** 한 문서 세트로 완결합니다.
> **읽는 실습이 아니라 만드는 실습입니다.** 노트북이 ANARCI·Sapiens·IgFold·contact 계산·OAS 다운로드를 **직접 실행**해 결과를 여러분의 `my_run/` 폴더에 만들고, 저장소에 커밋된 `data/`(레퍼런스)와 대조해 맞는지 확인합니다.

---

## 0. 과정 개요

컴퓨터로 치료용 항체를 분석하는 과정에는 아래 질문들이 포함되어 있습니다.

- 이 서열은 진짜 항체인가? 어디가 CDR이고 어디가 framework인가? (**numbering**)
- 어떤 germline에서 왔고, 사람 항체와 얼마나 닮았는가? (**germline·humanness**)
- 3D 구조는 어떻게 생겼는가? (**구조예측**)
- 항원의 어디에 어떻게 붙는가? (**interface**)
- 약으로 만들 수 있는가? (**developability**)
- 자연 항체 레퍼토리에서 정상 범위인가? (**repertoire**)

이 과정은 위 질문 하나하나를 **공개 DB + 오픈소스 CLI 도구**로 직접 풀어봅니다. 개념 → 환경 설치 → 도구별 실습 → 통합 파이프라인·보고서까지 이어집니다.

이 문서는 연구·교육 목적의 전산생물학 가이드이며, 임상적 의사결정이나 실험 검증을 대체하지 않습니다.

---

## 1. 대상 독자와 사전 요구사항

**대상**
- 항체를 **처음 다루는 연구자부터** 분석 파이프라인을 자동화하려는 실무자까지 본 과정에서 모두 다룹니다
- 항체 서열·구조를 직접 분석해야 하는 바이오·신약 연구개발자
- 후보 항체의 humanness·developability를 정량 평가하려는 계산생물학 실무자

**준비물**
- **웹 브라우저.** 실습 노트북은 Colab에서 그대로 열립니다. 첫 셀이 필요한 도구(ANARCI·Sapiens·IgFold 등)를 자동으로 설치하고, 나머지 셀이 그 도구를 실제로 돌립니다. 전 셀 실행 시간은 노트북마다 **3~16초**(아래 표, 실측).
- Python 기초와 단백질 서열·구조 기초(서열·도메인·결합 인터페이스). 핵심 용어는 본문에서 설명합니다.
- 로컬에서 돌리고 싶다면 conda 환경 3종을 제공합니다(Ch.03). 도구를 여러 번 반복 실행하거나 자기 데이터로 돌릴 때 편리합니다.

### 직접 생성이 기본값 — `my_run/` 과 `data/`

| 폴더 | 무엇 |
|------|------|
| `my_run/` | **여러분이 방금 만든 결과.** 노트북이 도구를 실행해 여기에 씁니다(저장소에는 없음, 실행하면 생깁니다) |
| `data/` | **레퍼런스(대조군).** 이 저장소를 만들 때 같은 도구로 만들어 커밋해 둔 결과 — 내 결과가 맞는지 비교하는 데 씁니다 |

각 절은 **① 직접 실행 → ② 내 결과 확인 → ③ 레퍼런스 대조** 순서입니다. 어느 단계를 건너뛰거나 실패해도 노트북의 `resolve()` 가 `my_run/` → `data/` 로 폴백하므로, 뒤 절이 멈추지 않습니다(어느 쪽을 쓰는지 항상 출력됩니다).

---

## 2. 과정 구성 — 스텝(챕터)별 자기완결

각 챕터는 **자기 폴더 안에 본문(.md)·노트북(.ipynb)·그래프(.png)·데이터(data/)를 모두** 담습니다. 한 스텝을 학습할 땐 그 폴더만 보면 됩니다.

`my_run/` 은 저장소에 없으며, **노트북을 돌리면 그 자리에서 생깁니다.**

### Part A — 개념과 환경

| Ch | 폴더 | 영역 | 핵심 내용 |
|----|------|------|-----------|
| **01** | [01_concepts/](01_concepts/01_concepts.md) | 항체 기본 개념 | IgG 구조, VH/VL·CDR·framework, numbering scheme, epitope/paratope, germline, developability |
| **02** | [02_databases/](02_databases/02_databases.md) | 항체 DB landscape | 구조/서열/치료/항원/mutation DB 분류, SAbDab·OAS·IMGT·Thera-SAbDab·CoV-AbDab·IEDB·AB-Bind·SKEMPI |
| **03** | [03_setup/](03_setup/03_setup.md) | 분석 환경 구축 | abseq/abstruct/abinterface conda 환경 분리, 의존성 충돌 회피, `boltzgen check`식 점검 |

### Part B — 도구별 실습 (Hands-on Labs)

| Ch | 폴더 | 분석 영역 | 노트북이 **직접 실행**하는 것 |
|----|------|-----------|-----------|
| **04** | [04_numbering/](04_numbering/04_numbering.md) | numbering·germline | **ANARCI 실행** → IMGT/Chothia numbering CSV + V/J germline 할당 |
| **05** | [05_humanness/](05_humanness/05_humanness.md) | humanness·humanization | **Sapiens 언어모델 실행** → humanness 점수 행렬 + humanized 서열 |
| **06** | [06_structure/](06_structure/06_structure.md) | 구조예측 | **IgFold 실행** → Fv 구조 예측(PDB) + 잔기별 예측오차 |
| **07** | [07_interface/](07_interface/07_interface.md) | 항원-항체 interface | **RCSB에서 1A14 다운로드 → contact 계산** → paratope/epitope |
| **08** | [08_developability/](08_developability/08_developability.md) | developability | **liability scan 실행** → motif·pI·GRAVY·unpaired Cys |
| **09** | [09_repertoire/](09_repertoire/09_repertoire.md) | repertoire·naturalness | **OAS data unit 다운로드 → CDR3 분포 집계** → 후보 percentile |

### 참조 (Reference)

| | 폴더 | 내용 |
|----|------|------|
| **부록** | [10_appendix/](10_appendix/10_appendix.md) | mini-pipeline 실행 예 · 보고서 체크리스트 · 용어집 · 참고문헌 24종 |

---

## 3. 실습 노트북 (각 챕터 폴더 안)

노트북은 별도 폴더가 아니라 **해당 챕터 폴더 안**에 있습니다. 첫 셀(0. 부트스트랩)이 저장소 클론 → 챕터 폴더 이동 → **도구 설치**까지 해주고, 나머지 셀이 그 도구를 실제로 돌립니다.

전 셀 실행 시간은 **직접 측정한 값**입니다(pip 전용 환경, CPU. 측정 환경 → [부록 E](10_appendix/10_appendix.md)).

| 노트북 | 위치 | 직접 실행하는 도구 | 전 셀 실행 |
|--------|------|--------------------|-----------|
| `02_db_explore.ipynb` | 02 | RCSB Search/Data API → 항체-항원 복합체 스냅샷 | **6초** |
| `03_setup_check.ipynb` | 03 | 스택 진단 + ANARCI 스모크 테스트 | **3초** |
| `04_numbering_lab.ipynb` | 04 | ANARCI (IMGT·Chothia·germline) | **9초** |
| `05_humanness_lab.ipynb` | 05 | Sapiens 언어모델 (humanness·humanization) | **16초** |
| `06_structure_lab.ipynb` | 06 | IgFold (Fv 구조예측) | **16초** |
| `07_interface_lab.ipynb` | 07 | RCSB CIF 다운로드 + contact 계산 | **10초** |
| `08_dev_lab.ipynb` | 08 | liability scan | **3초** |
| `09_repertoire_lab.ipynb` | 09 | OAS data unit 다운로드 + CDR3 분포 집계 | **8초** |

> 표의 시간은 **셀 실행 시간**입니다(도구가 이미 깔린 상태). Colab에서 처음 열면 여기에 첫 셀의 패키지 설치가 더해지며, 실측으로 노트북 한 권당 **1~6분**이고, 두 번째 실행부터는 표의 시간입니다.

공용 그래프 모듈 `antibody_viz.py`는 저장소 루트에 있고, 각 노트북은 `sys.path`에 루트를 추가해 import합니다. **노트북(.ipynb)은 손으로 고치지 말고 `gen_notebooks.py`를 고친 뒤 재생성**하세요.

---

## 4. 빠른 시작 (Quick Start)

### (A) 브라우저 — Colab에서 바로 실습 (기본 경로)

1. GitHub에서 원하는 챕터 노트북(예: `04_numbering/04_numbering_lab.ipynb`)을 엽니다.
2. **Open in Colab** 으로 실행합니다.
3. 위에서부터 그대로 실행하세요(고칠 값 없음). 클론 → 챕터 폴더 이동 → 도구 설치 → **도구 실행 → `my_run/` 에 결과 생성 → `data/` 와 대조**까지 그대로 흘러갑니다.

ANARCI 계열 노트북의 설치 한 줄은 다음과 같습니다(부트스트랩이 자동 실행).

```bash
!apt-get -qq install -y hmmer      # ANARCI가 부르는 hmmscan — pip 로는 안 깔려요
!pip -q install anarci abnumber
```

### (B) 로컬 — 반복 실행·자기 데이터용

```bash
# 1) 분석 환경 (Ch.03 상세)
conda env create -f environment/abseq.yml      # ANARCI(+HMMER)·Sapiens·Biopython·pandas
conda activate abseq

# 2) 설치 점검
ANARCI --help >/dev/null && echo "ANARCI OK"
python -c "import Bio, pandas, matplotlib; print('analysis stack OK')"

# 3) 첫 실행 (developability scan) — 결과는 my_run/ 에
python scripts/liability_scan.py 08_developability/data/demo_mab.fa \
  --out 08_developability/my_run/liability.csv

# 4) numbering (IMGT + germline)
ANARCI -i 04_numbering/data/demo_mab.fa -s imgt --assign_germline --csv \
  --outfile 04_numbering/my_run/demo_imgt
```

> 구조예측(IgFold)은 `environment/abstruct.yml`, interface 심화(FreeSASA/PLIP)는 `environment/abinterface.yml`을 쓰세요. 도구별 의존성 충돌을 피하려고 환경을 셋으로 나눴습니다(Ch.03).

---

## 5. 학습 경로

```
[개념]  01 개념 → 02 DB landscape → 03 환경 설치
                                        │
[실습]  04 numbering → 05 humanness → 06 구조예측
                                        │
        07 interface → 08 developability → 09 repertoire
        (관심 분석부터 선택 가능)
                                        │
[정리]  10 부록 (mini-pipeline · 보고서 체크리스트)
```

- **입문자**: 01 → 10 순서대로.
- **특정 분석이 급하면**: 03(설치) → 해당 실습 챕터로 바로.

---

## 6. 표기 규약

- `코드` = 실제 명령·파일명·컬럼명
- 본문 콜아웃 표기: **심화**(배경 지식) · **주의**(흔한 함정) · **실습**(노트북 연동 + 실측 실행 시간 배지)
- DB·도구는 **공식 출처**로 인용 (부록 참고문헌 [1]~[24])
- 모든 수치·그래프는 **도구를 실제로 실행한 결과**입니다(임의 값·합성 데이터 아님). 데이터 출처와 취득 시점은 [부록 E 재현 환경](10_appendix/10_appendix.md)에 적어 두었습니다.

---

다음 → **[01. 항체 기본 개념](01_concepts/01_concepts.md)**
