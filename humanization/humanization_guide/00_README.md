---
title: "항체 Humanization 완전 정복 — 비인간 항체를 사람 항체로"
subtitle: "ANARCI·BioPhi/Sapiens·Humatch·AnthroAb·AbNatiV로 잇는 통합 실무 과정"
series: "Antibody Humanization Complete Course"
version: "가이드 0.4 · 2026-06 실제 실행 검증"
language: ko
---

# 항체 Humanization 완전 정복 — 비인간 항체를 사람 항체로

> **이 과정은 항체 humanization을 처음부터 끝까지 다루는 자기완결형(self-contained) 통합 실무 가이드입니다.**
> 입력 서열 정리(numbering·CDR annotation)에서 출발해, 도구별 후보 생성(BioPhi/Sapiens·Humatch·AnthroAb)·정량 평가(humanness·nativeness·naturalness)·구조 검증·developability·랭킹·실험 검증 제안까지 한 문서 세트로 끝냅니다.
> 모든 명령과 수치는 **실제 실행 결과 기반입니다**. 돌리지 못한 도구는 **〔본 환경 미실행〕** 으로 정직하게 표시했습니다. (실행 환경 상세 → [부록 재현 환경](11_appendix/11_appendix.md))

---

## 0. 과정 개요

Humanization은 mouse·rat·rabbit 항체의 variable domain을 사람 항체 레퍼토리에 가깝게 바꾸는 일입니다. 그런데 항원에 달라붙는 CDR과 그걸 떠받치는 핵심 framework는 건드리면 안 됩니다. 이 두 요구가 정면으로 부딪힙니다. 그래서 도구 하나로 끝나지 않습니다.

대신 네 단계를 오가는 워크플로우로 보면 안전합니다.

1. **입력 정리** — VH/VL 분리, numbering, CDR/FWR annotation, germline assignment
2. **후보 생성** — BioPhi/Sapiens, Humatch, AnthroAb, CDR grafting/backmutation으로 humanized 후보 만들기
3. **평가** — humanness/nativeness, CDR 보존성, germline identity, liability, developability, VH/VL 페어링 점검
4. **구조 검증** — 구조 예측으로 CDR geometry·residue tolerance 확인

이 과정은 다음을 **모두** 담습니다.

- **개념·이론** — 왜 humanization을 하는가, CDR grafting·resurfacing·backmutation의 원리, 명명법의 함정
- **실무 전 과정** — 입력 준비(QC·numbering) → 설치 → 도구별 실행 → 메트릭 해석 → 랭킹
- **도구별 실습** — ANARCI · IgBLAST · BioPhi/Sapiens · Humatch · AnthroAb · AbNatiV · Ab-RoBERTa · 구조 검증
- **재현 가능한 명령과 그래프**, 그리고 실제 실행해 얻은 수치

### 0.1 한눈에 보는 권장 파이프라인

```text
Raw VH/VL FASTA
  → ANARCI / IgBLAST      : numbering, CDR/FWR annotation, germline assignment
  → BioPhi/Sapiens        : humanized 후보 생성
  → Humatch               : gene/pairing 관점 후보 보완
  → AnthroAb (masked-LM)  : targeted infilling + mutation 교차검증
  → AbNatiV / Ab-RoBERTa  : nativeness·naturalness 평가, 후보 필터링
  → ABodyBuilder3/ImmuneBuilder : 구조 예측, CDR loop sanity check
  → TAP / developability  : liability flagging
  → 후보 5~20개 rank
  → 실험 발현·결합·열안정성 검증
```

---

## 1. 대상 독자와 사전 요구사항

**대상**

- 비인간 항체 서열(mouse/rat/rabbit hybridoma 등)을 손에 쥐고, 이걸 치료용으로 사람화해야 하는 연구자
- in silico humanization 결과를 정량 해석하고, 후보에 순위를 매겨 실험으로 넘기려는 실무자
- BioPhi·Humatch·AnthroAb·AbNatiV·ANARCI·IgBLAST를 하나의 워크플로우로 엮으려는 계산생물학 실무자

**준비물**

- **웹 브라우저.** 실습 노트북은 Colab에서 그대로 열립니다. 챕터 상단 **실습 콜아웃**에 노트북 링크가 붙어 있습니다. 설치 없이 그 챕터의 명령을 따라 할 수 있습니다.
- Python·CLI 기본기와 conda 경험. 없어도 괜찮습니다 — [Ch.03](03_setup/03_setup.md)에서 환경을 함께 만듭니다.
- 항체 구조 기초(VH/VL, CDR/FWR, IgG/Fab/Fv). 핵심 용어는 본문과 [부록 용어집](11_appendix/11_appendix.md)에서 다시 설명합니다.
- 로컬에서 직접 돌리고 싶다면 conda 환경 하나면 됩니다([Ch.03](03_setup/03_setup.md)). 체크포인트를 내려받는 도구는 본문에 용량을 적어 뒀습니다.

---

## 2. 과정 구성 — 챕터별 자기완결

각 챕터는 **자기 폴더 안에 본문(.md)·노트북(.ipynb)·그래프(.png)** 를 함께 담습니다. 한 스텝을 배울 때 그 폴더만 보면 됩니다.

### Part A — 개념과 전략

| Ch | 폴더 | 영역 | 핵심 내용 |
|----|------|------|-----------|
| **01** | [01_why_humanization/](01_why_humanization/01_why_humanization.md) | 왜 humanization인가 | 항체 구조, CDR/FWR, Vernier zone, 면역원성(ADA/HAMA), CDR grafting + backmutation |
| **02** | [02_nomenclature_strategy/](02_nomenclature_strategy/02_nomenclature_strategy.md) | 명명법·도구 지도·전략 | `-ximab/-zumab/-umab`과 2021 신체계, 생성 vs 평가 도구, 후보 스펙트럼, end-to-end 워크플로우 |
| **03** | [03_setup/](03_setup/03_setup.md) | 환경 구성 | conda env, 도구별 설치 경로(bioconda·PyPI·GitHub), 설치 검증 |

### Part B — 도구별 실습 (실측 검증)

| Ch | 폴더 | 도구 | 본 환경 검증 |
|----|------|------|--------------|
| **04** | [04_sequence_qc/](04_sequence_qc/04_sequence_qc.md) | ANARCI · IgBLAST | ✅ ANARCI · ✅ IgBLAST |
| **05** | [05_humanize_sapiens/](05_humanize_sapiens/05_humanize_sapiens.md) | BioPhi / Sapiens | ✅ Sapiens |
| **06** | [06_cdr_safe_tools/](06_cdr_safe_tools/06_cdr_safe_tools.md) | Humatch · AnthroAb (+3-모델 비교) | ✅ Humatch · ✅ AnthroAb |
| **07** | [07_nativeness/](07_nativeness/07_nativeness.md) | AbNatiV · Ab-RoBERTa | ✅ AbNatiV · ✅ Ab-RoBERTa |
| **08** | [08_structure/](08_structure/08_structure.md) | ABodyBuilder3 / ImmuneBuilder / AntiFold | 〔본 환경 미실행〕 |
| **09** | [09_developability/](09_developability/09_developability.md) | liability 모티프 · TAP | 〔TAP 본 환경 미실행〕 |

### Part C — 정리와 운영

| Ch | 폴더 | 내용 |
|----|------|------|
| **10** | [10_ranking_report/](10_ranking_report/10_ranking_report.md) | 후보 랭킹 스키마 · 운영형 GuideDB YAML · 실험 검증 제안 · lab-in-the-loop |
| **11** | [11_appendix/](11_appendix/11_appendix.md) | 최종 체크리스트 · 참고자료 · 재현 환경 · 용어집 |

---

## 3. 실습 노트북 (각 챕터 폴더 안)

노트북은 별도 폴더에 모여 있지 않습니다. **해당 챕터 폴더 안**에 있고, 본문 상단 실습 콜아웃에서 링크됩니다. 브라우저(Colab)가 기본 경로이고, 로컬 주피터에서도 그대로 열립니다.

각 노트북은 **① 도구를 직접 실행 → ② 내가 만든 결과 확인 → ③ 레퍼런스 대조** 순서로 흘러갑니다. 여러분이 돌린 산출물은 챕터 폴더의 `my_run/`에 쌓입니다. 저장소에 커밋된 `data/`는 **대조군**으로만 씁니다. 어느 단계를 건너뛰거나 실패해도 자동으로 `data/`로 폴백하니 다음 절이 계속 돌아갑니다. 어느 쪽을 쓰는지는 노트북이 출력해 줍니다.

아래 **소요 시간은 노트북의 모든 셀을 실제로 실행해 측정한 값입니다**.

| 노트북 | 챕터 | 직접 실행하는 것 | 전 셀 실행 |
|--------|------|------------------|-----------|
| `03_setup_check.ipynb` | 03 | 도구 설치·환경 점검 | 6초 |
| `04_numbering_lab.ipynb` | 04 | ANARCI/abnumber numbering → CDR 추출 → germline 할당 | 1초 |
| `05_sapiens_lab.ipynb` | 05 | Sapiens 인간화 + **CDR 가드 실패 재현** | 6초 |
| `06_tools_lab.ipynb` | 06 | Humatch·AnthroAb 실행 + **3도구 합의 계산** | 32초 |
| `07_nativeness_lab.ipynb` | 07 | Ab-RoBERTa pseudo-likelihood 계산 (AbNatiV는 선택) | 96초 |
| `08_structure_lab.ipynb` | 08 | IgFold 구조 예측 + CDR-H3 RMSD | 7초 |
| `09_developability_lab.ipynb` | 09 | liability 모티프 스캔 | 1초 |
| `10_ranking_lab.ipynb` | 10 | 앞 랩 결과를 모아 랭킹 + candidate report | 5초 |

> 표의 시간은 **셀 실행 시간입니다**. Colab에서 처음 열면 여기에 패키지 설치가 더해집니다 — 실측으로 노트북 한 권당 **1~6분**(설치 포함, 두 번째 실행부터는 표의 시간).

공용 그래프 모듈 `humanization_viz.py`는 `humanization_guide/` 루트에 있습니다. 각 노트북이 `sys.path`에 루트를 추가해 import합니다.

AbNatiV만 예외입니다. 체크포인트가 약 2GB라 노트북에서 기본 비활성(`RUN_ABNATIV = False`)입니다. 켜지 않으면 커밋된 점수로 이어지고, 켜는 법은 Ch.07에 있습니다.

---

## 4. 빠른 시작 (Quick Start)

### (A) 브라우저에서 바로 — 설치 없음 (권장 입문)

[Ch.01](01_why_humanization/01_why_humanization.md)부터 읽으면서, 챕터 상단 실습 콜아웃의 노트북 링크를 Colab으로 엽니다. 명령·수치·그래프가 본문과 1:1로 대응합니다.

### (B) 로컬에서 직접 돌리기 — conda 환경 하나

```bash
# 1) 공용 환경 (Ch.03 상세) — ANARCI는 PyPI가 아니라 bioconda에 있습니다
conda create -n abhuman -c conda-forge -c bioconda python=3.10 anarci hmmer -y
conda activate abhuman
ANARCI --help

# 2) humanization 엔진 (Ch.05)
python -m pip install sapiens

# 3) parental 서열 numbering + germline (Ch.04)
ANARCI -i parental.fasta --scheme imgt --assign_germline --use_species human --csv -o anarci_gl
```

> **주의 —** `pip install anarci` / `pip install biophi` / `pip install humatch` 는 **모두 실패합니다**. 각각 bioconda·bioconda·GitHub source가 정답입니다. 자세한 사정은 [Ch.03](03_setup/03_setup.md)에 있습니다.

---

## 5. 학습 경로

```text
[개념]  01 왜 humanization → 02 명명법·도구 지도·전략
                                   │
[준비]  03 환경 구성 ───────────────┘
            │
[실습]  04 입력 QC(ANARCI/IgBLAST) → 05 BioPhi/Sapiens → 06 Humatch·AnthroAb
            → 07 AbNatiV·Ab-RoBERTa → 08 구조 검증 → 09 developability
            │
[정리]  10 랭킹·GuideDB·실험 검증 → 11 부록(체크리스트·참고자료·용어집)
```

- **입문자** — 01부터 11까지 순서대로.
- **급하면** — 03(환경) → 04(입력 QC) → 관심 도구 챕터로 바로. 단, 처음이라면 **04를 먼저** 보세요. 뒤의 모든 단계가 04에서 만든 numbering·annotation 위에서 돌아가기 때문입니다.

---

## 6. 표기 규약

- `코드` = 실제 명령·파일명·함수명·메트릭 컬럼명
- **실습 —** 직접 따라 할 부분 · **심화 —** 더 깊이 · **주의 —** 흔한 함정 · **케이스 스터디 —** 실제 겪은 사례
- 수치는 전부 실제 실행 결과입니다. 이 가이드를 검증한 환경에서 돌리지 못한 GPU·웹 전용 도구는 **〔본 환경 미실행〕** 으로 표시합니다. 임의 값을 지어내지 않으려는 뜻입니다.
- 실행 환경(하드웨어·버전)은 [부록 재현 환경](11_appendix/11_appendix.md)에 모아 뒀습니다.

---

다음 → **[01. 항체 humanization, 왜 하고 무엇을 지켜야 하나요?](01_why_humanization/01_why_humanization.md)**
