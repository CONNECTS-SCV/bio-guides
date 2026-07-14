---
title: "BoltzGen 완전 정복 — AI 바인더 설계 통합 심화 과정"
subtitle: "단백질·펩타이드·항체·나노바디·소분자·핵산 설계의 기초부터 자동화까지"
series: "BoltzGen Complete Course"
version: "boltzgen 0.3.2 기준 · 2026-06 실행 검증"
language: ko
target_length: "A4 약 50쪽"
---

# BoltzGen 완전 정복 — AI 바인더 설계 통합 심화 과정

> **이 과정은 BoltzGen을 처음부터 끝까지 다루는 자기완결형(self-contained) 통합 심화 튜토리얼입니다.**
> 입문 개념(바인더란 무엇인가, 설치, 첫 실행)부터 시작해, 펩타이드·고리형·항체·나노바디·소분자·핵산까지 **모든 바인더 타입의 실전 설계**, 그리고 메트릭 정량 해석·파이프라인 자동화·연구/산업 적용까지 한 문서 세트로 완결합니다.
> 사전 지식이 없어도 이 과정만으로 학습할 수 있으며, 모든 명령·수치·그래프는 **BoltzGen 0.3.2를 실제 실행해 재현·검증**했습니다. (재현 환경 상세 → 부록 A8)

---

## 0. 과정 개요

BoltzGen은 MIT에서 개발한 **생성형 AI 기반 바인더 설계 도구**입니다. 타깃(단백질·핵산·소분자)에 결합하는 단백질/펩타이드/항체/나노바디를, 백본 생성(diffusion) → 서열 설계(inverse folding) → 구조 검증(Boltz-2) → 분석 → 필터링의 자동 파이프라인으로 만들어냅니다.

이 과정은 다음을 **모두** 담습니다.

- **개념·이론**: 왜 AI 바인더 설계인가, 6개 프로토콜·모델 아키텍처·입출력 데이터 구조
- **실무 전 과정**: 입력 준비(QC·포맷변환) → 설치/접근(로컬·클라우드) → 실행(옵션 전략) → 해석(메트릭·시각화) → 자동화
- **타깃별 실습 5종**: 펩타이드/고리형 · 항체 Fab · 나노바디 · 소분자(친화도) · 핵산(DNA/RNA)
- **단계별 Jupyter 노트북**과 **재현 가능한 그래프**

---

## 1. 대상 독자와 사전 요구사항

**대상**
- BoltzGen을 **처음 접하는 사람부터** 실전 활용·자동화를 원하는 연구자까지 — 이 과정 하나로 완결
- 항체/나노바디/펩타이드/핵산/효소 바인더를 **직접 설계**해야 하는 바이오·신약 연구개발자
- 설계 결과를 **정량 해석하고 파이프라인으로 자동화**하려는 계산생물학 실무자

**준비물**
- **웹 브라우저.** 실습 노트북은 Colab 무료 런타임에서 그대로 열려요. 실습 랩(04·05·07~11)은 **설계 셀이 여러분의 결과를 `my_run/`에 만들고, 분석 셀이 그 결과를 읽어** 표·그래프를 그립니다. 설계 셀을 건너뛰거나 실패해도 괜찮아요 — 각 챕터의 `data/` 폴더에 **레퍼런스 설계 결과(메트릭 CSV·구조 CIF)가 커밋돼 있어서** 자동으로 그쪽으로 폴백하거든요. 분석 셀만 돌리면 노트북 한 권이 **몇 초**면 끝나요.
- Python 기초와 단백질 구조 기초(서열·2차구조·도메인·결합 인터페이스). 핵심 용어는 본문에서 설명해요.
- 설계를 **직접 돌려보고 싶을 때만** NVIDIA GPU가 필요해요(BoltzGen은 CPU 폴백이 없어요). 이 과정의 예제는 Colab **무료 T4 런타임**에서 전부 돌아갑니다 — Ch.03에서 그대로 따라 하면 돼요.

---

## 2. 과정 구성 — 스텝(챕터)별 자기완결

각 챕터는 **자기 폴더 안에 본문(.md)·노트북(.ipynb)·그래프(.png)·데이터(data/)를 모두** 담습니다. 한 스텝을 학습할 때 그 폴더만 보면 됩니다.

### Part A — 핵심 워크플로우 (6대 영역)

| Ch | 폴더 | 영역 | 핵심 내용 |
|----|------|------|-----------|
| **01** | [01_tool_understanding/](01_tool_understanding/01_tool_understanding.md) | 툴의 이해 | 바인더 설계의 의미, 6 프로토콜 선택 기준, diffusion+inverse folding+Boltz-2 아키텍처 |
| **02** | [02_input_data_prep/](02_input_data_prep/02_input_data_prep.md) | 입력 데이터 준비 | entity 5종, CIF/PDB 준비·정제, 결합부위 선정, 품질 체크 |
| **03** | [03_install_access/](03_install_access/03_install_access.md) | 툴 설치 및 접근 | 로컬·클라우드·Colab, GPU/CUDA 의존성, **cuBLAS/cuequivariance 실전 트러블슈팅** |
| **04** | [04_basic_usage/](04_basic_usage/04_basic_usage.md) | 기본 사용법 | 6스텝 파이프라인, `--steps`·`--config`·`--num_designs`/`--budget` 전략 |
| **05** | [05_result_interpretation/](05_result_interpretation/05_result_interpretation.md) | 결과 해석 | 메트릭 수십 종, `filter.ipynb`, **시각화 스타일 가이드** |
| **06** | [06_advanced_ai/](06_advanced_ai/06_advanced_ai.md) | 고급 활용·AI 적용 | 계층적 스크리닝, 자동화, `metrics_override`/`additional_filters`, 커스텀 scaffold |

### Part B — 타깃별 실습 (Hands-on Labs)

| Ch | 폴더 | 타깃 타입 | 실측 예제 |
|----|------|-----------|-----------|
| **07** | [07_peptide_cyclic/](07_peptide_cyclic/07_peptide_cyclic.md) | 펩타이드·고리형 | cyclotide(3ivq), cyclic·disulfide·cystine-knot |
| **08** | [08_antibody_fab/](08_antibody_fab/08_antibody_fab.md) | 항체 Fab | PD-L1(7uxq) + 임상 항체 14종 scaffold |
| **09** | [09_nanobody/](09_nanobody/09_nanobody.md) | 나노바디 | penguinpox(9bkq), scaffold 다중 그래프팅, developability |
| **10** | [10_small_molecule/](10_small_molecule/10_small_molecule.md) | 소분자·효소 | chorismate(TSA), **친화도(affinity) 예측** |
| **11** | [11_nucleic_acid/](11_nucleic_acid/11_nucleic_acid.md) | 핵산(DNA/RNA) | de novo zinc finger(DNA) + RNA 커스텀 타깃 |

### 참조 (Reference)

| | 폴더 | 내용 |
|----|------|------|
| **부록** | [12_appendix/](12_appendix/12_appendix.md) | 메트릭 240컬럼 사전 · CLI 전체 레퍼런스 · YAML 치트시트 · 트러블슈팅 종합 · FAQ · 용어집 |

---

## 3. 실습 노트북 (각 챕터 폴더 안)

노트북은 별도 폴더가 아니라 **해당 챕터 폴더 안**에 있습니다. 실행 결과·그래프도 같은 폴더의 `data/`·`.png`에 저장됩니다.

첫 셀(부트스트랩)이 저장소를 클론하고 해당 챕터 폴더로 자동 이동해 `data/`의 실제 결과로 실습합니다 — **고칠 값은 없습니다.** 로컬 주피터에서도 그대로 열려요.

**실습 랩(04·05·07~11)은 여러분이 직접 BoltzGen을 돌려 결과를 만드는 구조**입니다 — 설계 셀이 `my_run/`에 내 결과를 만들고, 이어지는 분석 셀이 **그 결과**를 읽습니다. 설계 셀을 건너뛰면 저장소에 커밋된 레퍼런스 결과로 이어져 실습이 끊기지 않아요.

아래 **소요 시간은 노트북을 실제로 실행해 측정한 값**입니다(분석 셀 기준. 설계 셀은 별도 — 4.(B) 참고).

| 노트북 | 위치(챕터) | 내용 | 분석 셀 |
|--------|-----------|------|--------|
| `02_data_prep.ipynb` | 02 | CIF 다운로드·gemmi 검사, entity 5종 명세 작성, `boltzgen check` | 4초 |
| `03_setup_check.ipynb` | 03 | 설치·GPU·CUDA·cuequivariance 진단, `boltzgen check` | 19초 |
| `04_run_pipeline.ipynb` | 04 | **직접 스모크 실행**(6스텝) → 내 출력 구조 해부 | 5초 |
| `05_analysis_viz.ipynb` | 05 | **직접 설계 실행** → 메트릭 로드·해석·그래프·상관행렬 | 6초 |
| `06_advanced_filtering.ipynb` | 06 | 하드필터·`metrics_override`·`additional_filters`·다양성(alpha) — 05의 내 결과를 이어받음 | 3초 |
| `07_peptide_lab.ipynb` | 07 | **직접 설계 실행** → cyclotide 메트릭·Cys 보존·disulfide 거리(gemmi) | 7초 |
| `08_fab_lab.ipynb` | 08 | **직접 설계 실행** → 항체 Fab + developability + VH/VL framework 검증 | 5초 |
| `09_nanobody_lab.ipynb` | 09 | **직접 설계 실행** → 나노바디 메트릭·VHH framework 보존 | 3초 |
| `10_small_molecule_lab.ipynb` | 10 | **직접 설계 실행** → 소분자 메트릭·affinity 랭킹·포켓 품질 | 3초 |
| `11_nucleic_lab.ipynb` | 11 | **직접 설계 실행** → DNA/RNA 분석·DNA vs RNA H-bond 비교 | 3초 |

> 표의 시간은 **셀 실행 시간**입니다. Colab에서 처음 열면 여기에 패키지 설치가 더해져요 — 실측으로 노트북 한 권당 **1~6분**(설치 포함, 두 번째 실행부터는 표의 시간).


공용 그래프 모듈 `boltzgen_viz.py`는 advanced/ 루트에 있으며, 각 노트북은 `sys.path`에 루트를 추가해 import합니다.

---

## 4. 빠른 시작 (Quick Start)

### (A) 브라우저에서 바로 — 설치 없음 (권장 입문)

1. GitHub에서 원하는 챕터 노트북(예: `05_result_interpretation/05_analysis_viz.ipynb`)을 열고 **Open in Colab** 으로 엽니다. 2. 위에서부터 실행하면 클론→챕터 폴더 이동→`data/`의 실제 결과로 표·그래프가 그대로 재현됩니다. **런타임은 기본값 그대로, 고칠 값도 없습니다.**

### (B) 직접 설계까지 — Colab GPU 런타임 또는 로컬

설계 실행(`boltzgen run`)에는 NVIDIA GPU가 필요해요. Colab이라면 **런타임 → 런타임 유형 변경 → T4 GPU**로 바꾸면 아래를 그대로 쓸 수 있고, 로컬 GPU가 있다면 로컬에서 해도 됩니다.

```bash
# 1) 환경 (Ch.03 상세)
conda create -n boltzgen_env python=3.12 -y && conda activate boltzgen_env
git clone https://github.com/HannesStark/boltzgen.git && cd boltzgen
python -m pip install -e .

# 2) GPU·CUDA 검증 (Ch.03 트러블슈팅 — cuBLAS 정합 주의)
python -c "import torch; print('CUDA:', torch.cuda.is_available())"

# 3) 설계 명세 검증
boltzgen check example/vanilla_protein/1g13prot.yaml

# 4) 첫 실행 (스모크 테스트 규모)
boltzgen run example/vanilla_protein/1g13prot.yaml \
  --output workbench/test --protocol protein-anything \
  --num_designs 4 --budget 2
```

> 이 스모크 실행(`num_designs 4`)은 6스텝 전체가 **약 5분**이었어요(가중치가 캐시된 상태의 실측값. 측정 환경 → 부록 A8). 첫 실행에는 모델 가중치 약 6GB 다운로드가 더해집니다.
>
> 설계 규모별 실측(가중치 캐시 기준).
>
> | 규모 | 소요 | 최종 선별 |
> |------|------|-----------|
> | `--num_designs 4 --budget 2` (Ch.04 스모크) | **약 5분** (307초) | 2개 |
> | `--num_designs 8 --budget 4` (Ch.05·07~11 랩) | **약 10분** (585초) | 4개 |
>
> 실습 랩의 설계 셀은 모두 두 번째 규모(8/4)예요. 규모를 키우면 시간은 대체로 `num_designs`에 비례해 늘고, 복합체가 클수록 refolding이 더 무거워져요(Ch.01의 단계별 시간 표 참고).

> 설치 후 `CUDA: False` 또는 `cuequivariance ... undefined symbol: cublasGemmGroupedBatchedEx` 오류가 나면 **Ch.03의 "CUDA/cuBLAS 트러블슈팅"** 을 먼저 보세요. 드라이버↔torch↔cuequivariance의 CUDA 버전 정합이 핵심입니다.

---

## 5. 학습 경로

```
[개념]  01 툴 이해 → 02 입력 준비 → 03 설치/접근
                                        │
[실행]  04 기본 사용 ────────────────────┘
            │
[해석]  05 결과 해석 → 06 고급/AI 적용
            │
[실습]  07 펩타이드 · 08 항체 · 09 나노바디 · 10 소분자 · 11 핵산
        (관심 타깃부터 선택 가능)
```

- **입문자**: 01 → 11 순서대로.
- **특정 타깃이 급하면**: 03(설치) → 04(실행) → 해당 실습 챕터로 바로.

---

## 6. 표기 규약

- `코드` = 실제 명령·파일명·컬럼명
- 실습(노트북 연동) · 그래프 · 흔한 함정 · 심화 팁
- 메트릭은 **실제 CSV 컬럼명**으로 병기 (예: ipTM = `design_to_target_iptm`)
- 모든 수치·그래프는 실제 실행 결과 기반(임의 값 아님)

---

다음 → **[01. 툴의 이해](01_tool_understanding/01_tool_understanding.md)**
