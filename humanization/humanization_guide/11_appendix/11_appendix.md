---
title: "부록 — 최종 체크리스트 · 참고자료 · 재현 환경 · 용어집"
chapter: 11
language: ko
part: reference
---

# 부록 (Appendix) — 실무 레퍼런스

실습을 따라가다 보면 "그 도구 링크가 뭐였지?", "이 수치는 어디서 나온 거지?" 하고 다시 찾게 됩니다. 이 부록은 그럴 때 펴 보는 **레퍼런스 모음**입니다. 곁에 두고 필요할 때 찾아보십시오.

---

## A1. 최종 체크리스트

한 항체를 인간화해서 실험으로 넘기기까지 확인할 것들입니다. 왼쪽부터 순서대로 밟으면 됩니다.

### 입력 QC (→ Ch.04)

| 확인 항목 | 통과 기준 |
|---|---|
| VH/VL 분리 | 두 체인이 정확히 나뉨 |
| numbering | ANARCI 성공 (scheme: IMGT) |
| germline assignment | V identity 확인 — 낮은 체인일수록 humanization 여지 큼 |
| CDR 좌표 | 6개 CDR 좌표를 못 박아 보호 대상 확정 |

### 후보 생성 (→ Ch.05·06)

| 확인 항목 | 통과 기준 |
|---|---|
| BioPhi/Sapiens 후보 | 생성 완료 |
| Humatch 후보 | 생성 완료 |
| AnthroAb targeted 후보 | 생성 완료 |
| 변이 분류 | 공통 mutation과 tool-specific mutation을 분리 |

### CDR·구조 보호 (→ Ch.04·08)

| 확인 항목 | 통과 기준 |
|---|---|
| CDR 내 mutation | **0개** (또는 명시적 근거) — 가장 흔한 사고 지점 |
| Vernier·interface 잔기 | backmutation 필요 여부 검토 |

### 평가 (→ Ch.05·07·08·09)

| 확인 항목 | 통과 기준 |
|---|---|
| humanness | parental 대비 개선 (실측 예: VH 0.694→0.815) |
| nativeness | AbNatiV 점수 개선 |
| 구조 | ABodyBuilder3/ImmuneBuilder 예측 + CDR RMSD 확인 |
| developability | liability 스캔 — 특히 신규 glycosylation motif |

### 마무리 (→ Ch.10)

| 확인 항목 | 통과 기준 |
|---|---|
| 최종 후보 | 5~20개 (aggressive~conservative 스펙트럼) |
| 실험 설계 | 결합력 검증을 최우선으로 작성 |

> **주의 —** CDR mutation 0개는 체크리스트의 다른 어떤 항목보다 먼저입니다. humanness가 아무리 올라도 CDR을 건드린 후보는 결합력을 잃을 수 있습니다. 넣어야 한다면 근거를 문서에 남기십시오.

---

## A2. 지표 한눈에 보기

세 지표(humanness · nativeness · naturalness)는 이름이 비슷하지만 **다른 축**입니다. 이 가이드에서 실제로 뽑은 값과 함께 정리합니다.

| 지표 | 도구 | 무엇을 보나 | 이 가이드 실측 |
|---|---|---|---|
| humanness | Sapiens | 사람 잔기를 얼마나 썼나 | VH 0.694→**0.815** · VL 0.770→**0.872** |
| OASis | BioPhi | 9-mer의 사람 항체 관찰 빈도 | DB를 구할 수 없어 다루지 않음 |
| nativeness | AbNatiV1 | 사람 항체로서의 자연스러움 | VH 0.6477→**0.8803** (FR 0.6317→0.9245) · VL parental 0.9022 |
| nativeness | AbNatiV2 | 위와 같은 축, **다른 스케일** | VH 0.4927→**0.7777** |
| naturalness | Ab-RoBERTa | 언어모델이 본 서열의 그럴듯함 | Sapiens **-0.4973** · AnthroAb -0.5285 · parental -0.7240 · Humatch -0.7717 |
| paired CNN | Humatch | VH/VL 페어링 타당성 | 0.972 · 1.000 |
| germline identity | ANARCI · IgBLAST | 가장 가까운 사람 germline과의 일치율 | heavy IGHV1-69 **63%** · light IGLV1-40 **81%** |

AbNatiV1과 AbNatiV2는 값이 다릅니다. 모델 세대가 달라 스케일이 다르기 때문입니다 — 두 세대를 섞어서 비교하면 안 됩니다(Ch.07).

---

## A3. 참고자료

| 도구 | 역할 | 링크 |
|---|---|---|
| BioPhi | humanization 플랫폼 (OASis 포함) | https://github.com/Merck/BioPhi · web: https://biophi.dichlab.org/ |
| Sapiens | masked-LM humanization 엔진 | https://github.com/Merck/Sapiens (PyPI: `sapiens`) |
| Humatch | paired VH/VL humanization | https://github.com/oxpig/Humatch · paper: https://pmc.ncbi.nlm.nih.gov/articles/PMC11610552/ |
| AnthroAb | masked infilling humanization | https://github.com/nagarh/AnthroAb · VH: huggingface.co/hemantn/roberta-base-humAb-vh · VL: `...-vl` |
| Ab-RoBERTa | naturalness (pseudo-log-likelihood) | huggingface.co/mogam-ai/Ab-RoBERTa |
| Hu-mAb/SAbPred | germline 기반 humanization 웹 도구 | https://opig.stats.ox.ac.uk/webapps/sabdab-sabpred/sabpred/humab |
| AbNatiV | nativeness 스코어 | https://gitlab.developers.cam.ac.uk/ch/sormanni/abnativ |
| ANARCI | numbering · germline 할당 | https://github.com/oxpig/ANARCI (bioconda: `anarci`) |
| IgBLAST | germline 교차확인 | https://www.ncbi.nlm.nih.gov/igblast/ |
| ABodyBuilder3 | 항체 구조 예측 | https://github.com/exscientia/abodybuilder3 |
| ImmuneBuilder | 항체 구조 예측 | https://github.com/oxpig/ImmuneBuilder |
| AntiFold | inverse folding · residue tolerance | https://github.com/oxpig/AntiFold |
| TAP/SAbPred | developability 프로파일링 | https://opig.stats.ox.ac.uk/webapps/sabdab-sabpred/sabpred/tap |
| Thera-SAbDab | 임상단계 항체 DB | https://opig.stats.ox.ac.uk/webapps/sabdab-sabpred/TheraSAbDab |
| WHO 신규 mAb 명명법 | 2021 개정 INN 체계 | https://cdn.who.int/media/docs/default-source/international-nonproprietary-names-%28inn%29/new_mab_nomenclature-_2021rev.pdf |
| Lab-in-the-loop (Frey et al. 2025) | closed-loop 항체 설계 사례 | https://doi.org/10.1101/2025.02.19.639050 |

---

## A4. 재현 환경 (Reproducibility)

이 과정의 수치가 **어디서 나왔는지**를 밝혀 둡니다. 본문에는 실행 환경을 적지 않고, 하드웨어·버전 정보는 여기 한곳에 모았습니다.

| 항목 | 값 |
|---|---|
| 가이드 버전 | 0.4 · 2026-06 실제 실행 검증 |
| 검증 환경 | macOS (Apple Silicon, arm64) · conda/mamba · CPU (AbNatiV만 `mps`) |
| 실행·검증한 도구 | ANARCI · IgBLAST · Sapiens · Humatch · AnthroAb · AbNatiV (6종) |
| 예제 입력 | parental VH 120 aa / VL(lambda) 110 aa (mouse hybridoma 가정) |
| 미실행 도구 | ABodyBuilder3 · ImmuneBuilder · AntiFold(GPU) · TAP(웹 전용) |

> **노트북 검증 환경 —** 챕터 노트북 8권은 Colab 런타임과 같은 조건(**Ubuntu 22.04 · Python 3.12 · conda 없이 pip/apt만**)의 컨테이너에서, 패키지 설치부터 마지막 셀까지 **처음부터 끝까지 실제로 실행해** 확인했습니다.

### 도구별 실행 상태

| 단계 | 도구·버전 | 환경 | 상태 |
|---|---|---|---|
| numbering + germline | ANARCI 2024.05.21 (bioconda) | macOS arm64 / CPU | ✅ 실행·검증 (heavy IGHV1-69 63% / light IGLV1-40 81%) |
| germline 교차확인 | IgBLAST 1.22.0 (bioconda) | macOS arm64 / CPU | ✅ 실행·검증 (IGHV1-8*01 63.27%, ANARCI와 일치) |
| humanization + humanness | Sapiens 1.1.0 (PyPI) | macOS arm64 / CPU | ✅ 실행·검증 (VH 21 mut / VL 17 mut, humanness ▲) |
| paired humanization | Humatch 1.0.1 (GitHub source) | macOS arm64 / CPU | ✅ 실행·검증 (VH 18 mut / VL 2 mut, CDR 0 mut) |
| masked infilling | AnthroAb 1.1.0 (PyPI) | CPU | ✅ 실행·검증 (Sapiens와 겹치는 자리 다수 — Ch.06) |
| nativeness | AbNatiV 2.0.8 (PyPI) | CPU | ✅ 실행·검증 (**AbNatiV1** VH 0.6477→0.8803 / **AbNatiV2** VH 0.4927→0.7777) |
| naturalness | Ab-RoBERTa (`mogam-ai/Ab-RoBERTa`) | masked pseudo-LL, CPU | ✅ 실행·검증 (Sapiens paired **-0.4973**, parental -0.7240) |
| 구조 예측 | ABodyBuilder3 / ImmuneBuilder 1.2 | GPU 권장 | 〔본 환경 미실행 — 설치는 됨〕 |
| residue tolerance | AntiFold | GPU | 〔본 환경 미실행〕 |
| developability | TAP | 웹 전용 | 〔본 환경 미실행〕 |

GPU·웹 전용 도구(ABodyBuilder3 · AntiFold · TAP)는 돌리지 않았고, 그 사실을 본문에 **〔본 환경 미실행〕** 으로 명시했습니다. 구조 검증은 대신 **IgFold(CPU)** 로 실제 돌려 Ch.08 랩을 구성했습니다.

### 핵심 실측값이 말하는 것

총 **6개 도구(ANARCI · IgBLAST · Sapiens · Humatch · AnthroAb · AbNatiV)를 실제로 설치·실행**해 수치를 뽑았습니다. A2 표의 값들은 모두 한 가지 이야기를 가리킵니다 — **heavy chain은 비인간성이 뚜렷해 humanization 여지가 크고, lambda 경쇄는 이미 사람답다.**

몇 가지는 표만 봐서는 놓치기 쉬우니 따로 적습니다.

- **germline J 유전자**는 `IGHJ6*01`과 `IGHJ4*01`이 **85.71%로 완전 동점**입니다. 그래서 도구마다 다르게 나옵니다(Ch.04).
- **humanness 화살표의 오른쪽 값**은 인간화 서열을 **다시 스코어링한** 평균 self-probability입니다. 정의를 바꾸면 0.782/0.851이 나옵니다 — Ch.05에 두 정의를 모두 적어 뒀습니다.
- **mutation 수**는 Sapiens VH 21·VL 17, Humatch VH 18·VL 2(CDR 0개)입니다.
- **3도구 교차검증**에서 똑같은 치환을 제안한 자리는 AnthroAb 모드에 따라 **7곳(best-score) 또는 12곳(FR-masked)**입니다. `I78T`는 그중 **모드를 바꿔도 살아남는 가장 강건한 합의**입니다(Ch.06).

### 이전 판에서 바로잡은 값

이 과정을 만들면서 **모든 도구를 다시 돌렸습니다.** 그 결과 이전 판의 몇몇 수치가 재현되지 않아 실측값으로 교체했습니다. 재현되지 않은 것을 숨기지 않으려고 여기 남깁니다.

| 항목 | 이전 판 | 실측 | 왜 달라졌나 |
|---|---|---|---|
| Ab-RoBERTa (Sapiens) | -0.6928 | **-0.4973** | 같은 방식으로 재계산했으나 값이 다름. parental·Humatch는 정확히 일치했으므로 계산 방식 문제는 아님 |
| Ab-RoBERTa (AnthroAb) | -0.8733 | **-0.5285**(best-score) | 위와 동일 |
| AbNatiV2 VH (인간화) | 0.6900 | **0.7777** | 0.6900은 어떤 후보에서도 나오지 않음(Humatch 0.6925가 가장 근접) |
| "3도구 합의는 `I78T` 하나뿐" | — | **7곳 또는 12곳** | 합의 개수는 AnthroAb 실행 모드에 따라 달라짐 |
| 중쇄 J 유전자 | `IGHJ4*01` | `IGHJ6*01`(ANARCI) | 85.71% 완전 동점 — 도구 tie-break 차이 |

나머지 값은 **문자·소수점 단위까지 재현**됐습니다. germline V, CDR 6개, Sapiens 변이 21개 목록, humanness 0.694/0.770→0.815/0.872, Humatch CNN 0.972/1.000과 CDR 0변이, AbNatiV1 7개 값, Ab-RoBERTa의 parental·Humatch 점수가 여기에 해당합니다.

---

## A5. 용어집 (Glossary)

### 구조·영역

| 용어 | 뜻 |
|---|---|
| **VH / VL** | heavy·light chain의 variable domain. humanization의 작업 대상 |
| **CDR** | 항원과 직접 접촉하는 loop 6개(H1/H2/H3, L1/L2/L3). **보호 대상** |
| **CDR-H3** | 항원 결합에 가장 결정적인 loop. 여기 mutation이 들어가면 빨간불 (본 가이드 예제: `ARRGRYGLYAMDY`) |
| **FWR (framework region)** | CDR을 받쳐주는 구조적 뼈대. humanization이 실제로 바꾸는 영역 |
| **Vernier zone** | CDR loop의 conformation을 아래에서 받쳐주는 framework 자리. 사람화하면 결합력이 흔들릴 수 있음 |
| **VH/VL interface** | 두 도메인이 맞물리는 면. 여기 mutation은 페어링 orientation을 바꿀 수 있음 |
| **paratope** | 항원과 실제로 접촉하는 잔기 집합 |

### 인간화 기법

| 용어 | 뜻 |
|---|---|
| **CDR grafting** | murine CDR을 사람 framework에 이식하는 고전적 humanization |
| **backmutation** | 사람화한 framework 자리를 다시 원래(murine) 잔기로 되돌리는 것 — 결합력 복원용 |
| **resurfacing** | 표면 노출 잔기만 사람 것으로 바꾸고 buried core는 보존하는 방식 |
| **ADA / HAMA** | 항-약물 항체 / Human Anti-Mouse Antibody — 비인간 항체 투여 시의 면역 반응 |
| **source substem (`-o-/-xi-/-zu-/-u-`)** | 옛 INN 명명법에서 항체 유래를 나타내던 어미. **2021 신체계에서 폐지**(Ch.02) |
| **lab-in-the-loop** | 예측 → wet 검증 → 재학습을 반복하는 closed-loop 항체 설계 시스템 |

### 지표

| 용어 | 뜻 |
|---|---|
| **germline identity** | 가장 가까운 사람 germline V(J) 유전자와의 서열 일치율(%). 낮을수록 비인간적 = humanization 여지 큼 |
| **IMGT / Kabat / Chothia / Martin / AHo** | 항체 numbering scheme. 이 가이드는 **IMGT** 기본 |
| **humanness** | "사람 잔기를 얼마나 썼나" — Sapiens 확률·OASis %ile 등 |
| **OASis** | 서열을 9-mer 펩타이드로 쪼개 OAS(Observed Antibody Space) 사람 항체에서의 관찰 빈도로 humanness를 매기는 BioPhi 지표 |
| **nativeness** | "그 조합이 실제 사람 항체로서 얼마나 자연스러운가" — AbNatiV score(0~1) |
| **naturalness** | 항체 언어모델이 본 서열의 그럴듯함 — Ab-RoBERTa **pseudo-log-likelihood**. humanness와 **다른 축**(Ch.07) |
| **perplexity** | `exp(-mean_log_prob)`. 낮을수록 모델이 그 서열을 자연스럽다고 봄 |
| **RMSD** | 두 구조의 좌표 차이(Å). CDR-H3 backbone RMSD가 humanization 구조 검증의 핵심 지표 |

### 모델·알고리즘

| 용어 | 뜻 |
|---|---|
| **masked-LM (masked language model)** | 빈칸을 뚫고 그 자리에 올 잔기를 예측하는 모델(Sapiens · AnthroAb · Ab-RoBERTa) |
| **argmax vs softmax(sampling)** | 위치별 최고 확률 잔기 하나를 고르기(결정적) vs 분포에서 확률적으로 뽑기(다양성) |
| **infilling** | 마스킹한 자리만 채워 넣는 것(`predict_masked`) |
| **paired CNN** | VH/VL을 함께 보고 페어링 타당성을 점수화하는 Humatch의 분류기 |
| **inverse folding** | 구조 → 서열 예측. AntiFold가 residue tolerance를 주는 방식 |
| **residue tolerance** | 특정 구조 자리에서 어떤 잔기가 구조적으로 허용되는지의 분포 |

### 개발성

| 용어 | 뜻 |
|---|---|
| **developability / liability** | 약으로 만들 수 있는 정도 / 그 위험 모티프(`NXS/T`, `NG`, `DG`, `M/W` 등) |
| **SAP (Spatial Aggregation Propensity)** | 구조 표면 소수성 패치를 정량화한 응집 위험 지표 |
| **charge patch** | 표면 전하가 몰린 영역. 점도·클리어런스 위험과 연결 |
| **TAP (Therapeutic Antibody Profiler)** | 임상단계 항체 분포와 비교해 developability flag를 주는 웹 도구 |

---

본문으로 → **[00. 과정 개요](../00_README.md)**
