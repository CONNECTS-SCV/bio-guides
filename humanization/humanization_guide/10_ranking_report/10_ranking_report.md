---
title: "Ch.10 — 후보 랭킹 · GuideDB · 실험 검증"
chapter: 10
language: ko
part: C
---

# Ch.10 — 후보 랭킹 · GuideDB · 실험 검증

후보가 5개인데, 뭘 먼저 실험하죠? Ch.04~09를 지나오며 점수는 잔뜩 쌓였어요. humanness, nativeness, CDR RMSD, liability… 표를 아무리 들여다봐도 **하나를 고르는 순간은 오지 않아요.** 지표가 많다는 건 아직 판단을 안 했다는 뜻이거든요.

이 챕터에서 그 판단을 코드로 못 박아요. 여러 점수를 **하나의 순위**로 합치고, 절대 넘으면 안 되는 선을 **hard filter**로 세우고, 프로젝트를 YAML 한 장으로 관리하고, 마지막에 실험실로 넘겨요. in silico 파트의 종착역이에요.

> **실습 — `10_ranking_lab.ipynb`** · ① 직접 실행 → ② 내 결과 확인 → ③ 레퍼런스 대조 · **전 셀 5초**
>
> 앞 랩들이 만든 내 산출물을 모아 가중합 랭킹을 매기고 candidate report 를 뽑아요.

---

## 10.1 후보 랭킹 스키마 — 점수를 한 줄로 접기

### 10.1.1 기본 score

지표 6개를 나란히 두면 후보 간 우열이 안 보여요. 그래서 **가중합**으로 접어요. 가중치는 "무엇을 얼마나 중요하게 볼지"를 숫자로 적는 선언이에요.

```text
Final score =
    0.25 * Humanness score          (OASis / Sapiens)
  + 0.20 * Nativeness score         (AbNatiV)
  + 0.20 * CDR/structure 보존 score (CDR RMSD)
  + 0.15 * Developability score     (TAP/liability)
  + 0.10 * Germline/framework 일관성 (IgBLAST/ANARCI)
  + 0.10 * 전문가 수동 review score
```

humanization의 목적 자체인 **humanness가 0.25로 가장 무거워요.** 그 뒤를 nativeness와 CDR/구조 보존이 각각 **0.20**으로 받쳐요. 사람답게 만들면서도 원래 모양을 잃지 않아야 하니까요. developability는 **0.15**, germline 일관성과 전문가 review는 각각 **0.10**이에요.

이 숫자는 고정값이 아니에요. **프로젝트마다 튜닝하세요.** 응집이 문제였던 파이프라인이면 developability 비중을 올리고, 면역원성이 관건이면 humanness를 더 밀어 올리는 식이에요.

### 10.1.2 Hard filter — 즉시 탈락 또는 backmutation 검토

가중합에는 함정이 있어요. **다른 점수가 좋으면 치명적 결함이 묻혀요.** CDR-H3를 건드려 결합이 깨진 후보도, humanness가 높으면 총점 상위에 올라올 수 있거든요. 그래서 점수와 별개로 **무조건 걸리는 선**을 따로 둬요. 아래 항목에 걸리면 즉시 탈락이거나, 최소한 backmutation을 검토해야 해요.

- CDR-H3 핵심 residue 변경
- 알려진 paratope residue 변경
- VH/VL interface core residue 변경
- CDR 구조 RMSD 급증
- CDR/paratope에 N-glycosylation motif 신규 생성
- severe hydrophobic/charge patch 증가
- AbNatiV/OASis가 parental 대비 개선되지 않음

마지막 항목이 특히 중요해요. 사람다워지지도 않았는데 변이만 넣은 후보는, 리스크만 지고 얻은 게 없는 거예요.

### 10.1.3 Candidate report 템플릿

후보 하나는 이 한 장으로 요약돼요. 실험 담당자에게 넘기는 최소 단위예요.

| 필드 | 예시 |
|---|---|
| Candidate ID | `HZ_Sapiens_01` |
| Parent antibody | parental clone name |
| Method | BioPhi/Sapiens |
| VH mutations | `Q5V, M20V, ... S115L` (21개) |
| VL mutations | `K52G, L54S, ...` (CDR 제외 후) |
| CDR mutations | none (보호) / 있으면 명시 |
| Humanness | VH 0.815 / VL 0.872 |
| AbNatiV | H/L score |
| Germline | `IGHV1-69` / `IGLV1-40` |
| Structure note | CDR-H3 stable, interface ok |
| Developability | none / `NXS` motif / charge patch |
| Final recommendation | advance / backmutate / reject |

마지막 줄이 이 표의 존재 이유예요. **advance / backmutate / reject 중 하나로 끝내세요.** 결론 없는 리포트는 다음 회의에서 같은 논쟁을 반복하게 만들어요.

---

## 10.2 운영형 GuideDB schema

후보가 늘면 노트북과 CSV가 흩어져요. 어떤 서열이 어떤 점수를 받았는지, 왜 그 결정을 내렸는지 3개월 뒤엔 아무도 몰라요. 그래서 가이드를 문서가 아니라 **내부 DB(JSON/YAML)** 로 굴려요. 프로젝트 하나가 입력·annotation·후보·점수·결정까지 **자기완결적으로** 들고 있어야 해요.

```yaml
project:
  id: GPC3_Humanization_001
  target: GPC3
  parent_clone: mouse_clone_A
  date: 2026-06-19

input_sequences:
  heavy: { name: parental_H, sequence: "QVQL...", species: mouse }
  light: { name: parental_L, sequence: "QSALT...", species: mouse }

annotation:
  numbering_scheme: IMGT
  cdr_definition: IMGT
  heavy_germline: IGHV1-69*06   # ANARCI 실측, V identity 0.63
  light_germline: IGLV1-40*01   # ANARCI 실측, V identity 0.81
  heavy_cdr3: ARRGRYGLYAMDY     # 보호 대상
  known_paratope_residues: []

candidates:
  - id: HZ_Sapiens_01
    method: BioPhi/Sapiens
    mutations: { heavy: 21, light: 17 }   # CDR 후처리 전
    scores:
      humanness: { vh: 0.815, vl: 0.872 } # 실측
      abnativ: null
      developability: null
    structure: { pdb: candidate_01.pdb, cdr_h3_rmsd: null }
    decision: pending
```

`null`은 아직 채우지 않은 값이에요. 구조와 developability는 [Ch.08](../08_structure/08_structure.md)·[Ch.09](../09_developability/09_developability.md)를 돌린 뒤 채워요. 빈 칸을 0으로 메우지 마세요 — **"측정 안 함"과 "나쁨"은 완전히 다른 상태**예요. 가중합에 그대로 들어가면 멀쩡한 후보를 떨어뜨려요.

주석에 근거를 남기는 것도 습관으로 만드세요. 위 YAML의 V identity **0.63**(heavy)·**0.81**(light)과 humanness **0.815 / 0.872**는 모두 실측값이고, 어디서 나온 숫자인지 한 줄로 붙어 있어요.

---

## 10.3 실험 검증 제안

다시 한 번 짚어요. **in silico 결과만으로 성공 판정하지 않아요.** AI·통계 도구는 실험할 가치가 있는 후보를 빠르게 좁혀주는 출발점이지, 결승선이 아니에요. 최소 검증 순서는 이래요.

1. **소량 발현** — HEK293/CHO transient expression
2. **정제** — Protein A/G, SEC purity
3. **결합력** — ELISA 또는 BLI/SPR (parental 대비 KD 유지 확인)
4. **안정성** — DSF/Tm, accelerated stability
5. **응집** — SEC-MALS 또는 DLS
6. **특이성** — cross-reactivity / polyspecificity panel
7. **기능 assay** — neutralization, blocking, internalization 등 target biology에 맞게

순서에 뜻이 있어요. 앞의 둘은 관문이고, 진짜 판정은 ③에서 나요.

> **주의 —** 가장 먼저, 가장 싸게 확인할 건 ③ **결합력**이에요. humanization의 제1 실패 모드가 "사람다워졌지만 안 붙는다"거든요. parental과 humanized를 같은 조건에서 SPR/BLI로 재서, KD가 유지되는지부터 보세요. 여기서 무너지면 뒤의 Tm·응집 데이터는 볼 이유가 없어요.

---

<!-- 근거: Frey, Hötzel, Stanton et al. "Lab-in-the-loop therapeutic antibody design with deep learning", bioRxiv 2025.02.19.639050 (Abstract L30-44; Fig.1a caption; §2.2–2.3; §4.4.4–4.4.5). 예측↔wet closed-loop 개념. 논문이 직접 assay한 항목은 결합력(SPR)·발현·비특이성(BV ELISA)·in silico TAP. 중복 점검: wet 검증 패널은 §10.3과 중복되어 재나열 제거하고 §10.3 포인터로 대체 — 이 절은 closed-loop/재학습(§10.3에 없는 부분)만 보완. -->

## 10.4 맺음말 — 예측을 넘어 closed-loop 검증으로 (lab-in-the-loop)

여기까지가 이 가이드가 다룬 **in silico 예측**이에요. ANARCI/IgBLAST로 무엇을 지킬지 못 박고 → BioPhi·Humatch·AnthroAb로 후보를 만들고 → AbNatiV·Ab-RoBERTa·구조 예측으로 사람다움·nativeness·naturalness를 채점했어요. 하지만 이 점수들이 답하는 건 **"계산상 더 사람답고 그럴듯해졌다"** 까지예요. 실제로 붙는지·안정한지·만들어지는지·면역원성이 낮은지는 컴퓨터가 단정할 수 없어요.

그래서 최종 판정은 wet-lab이에요. 그 구체적 순서와 항목은 §10.3에 이미 정리했으니 되풀이하지 않을게요. 이 절이 덧붙이는 건 하나예요. **한 번의 검증을 어떻게 반복 시스템으로 끌어올리는가.**

방법은 고리를 닫는 거예요. 예측 → wet 검증(§10.3) → **그 실험 데이터로 모델을 재학습** → 다시 예측. 이 닫힌 고리가 **lab-in-the-loop**이고, AI 항체 설계를 한 번의 예측이 아니라 라운드를 거듭하며 똑똑해지는 시스템으로 바꿔요. §10.3이 "한 배치를 어떻게 검증하나"라면, 이 절은 "그 결과를 어떻게 다음 설계에 되먹이나"예요.

| 단계 | 하는 일 | 이 가이드 / 사례 |
|---|---|---|
| ① 예측 (in silico) | 후보 생성 + 사람다움·nativeness·구조·developability 채점 | 본 가이드 Ch.04–10 |
| ② wet 검증 | 발현·결합력·Tm·응집·특이성·면역원성 실측 | 본 가이드 §10.3 |
| ③ 재학습 (loop) | 실험 데이터를 generative model·property oracle에 다시 학습 | lab-in-the-loop |

실제로 돌아간 사례가 있어요. Genentech/Roche의 **Lab-in-the-loop(LitL)** 이에요. generative 모델(후보 생성) + property predictor(발현·결합력·비특이성 oracle) + active learning ranking + in vitro SPR을 **하나의 반복 루프**로 묶었어요. 4개 표적(EGFR·IL-6·HER2·OSM)에 대해 **>1,800개 변이체를 설계·실험**했고, **4 라운드** 최적화로 표적마다 **3–100× 결합력 향상**(최고 결합체 ~100 pM)을 얻었어요. 핵심은 매 라운드의 실험 결과를 다시 모델 학습에 먹여 점점 좋은 후보를 내놓는 **flywheel** 구조예요.

> **주의 —** LitL은 *humanization*이 아니라 *affinity maturation* 사례예요. 직접 assay한 property도 **결합력(SPR)·발현·비특이성(BV ELISA)·in silico TAP**뿐이고, Tm·응집·면역원성은 실측이 아니에요. 가져올 건 **루프 구조**예요. oracle을 *결합력 + humanness/면역원성*으로 바꿔 끼우면 humanization 후보 선정에 그대로 적용돼요.

**참고문헌 —** Frey N.C., Hötzel I., Stanton S.D., *et al.* "Lab-in-the-loop therapeutic antibody design with deep learning." *bioRxiv* 2025.02.19.639050 (2025). https://doi.org/10.1101/2025.02.19.639050

---

## 이 챕터 핵심 요약

1. 랭킹은 **humanness(0.25)·nativeness(0.20)·구조 보존(0.20)·developability(0.15)·germline 일관성(0.10)·전문가 review(0.10)** 의 가중합이에요.
2. 가중합만 믿지 말고 **hard filter**로 치명적 결함을 따로 걸러요(CDR-H3 변경, 신규 glycosylation motif 등).
3. 프로젝트는 **GuideDB YAML** 한 장으로 입력·annotation·후보·점수·결정을 자기완결적으로 관리해요. `null`은 0이 아니에요.
4. 실험 검증의 **1순위는 결합력**이에요. humanization의 제1 실패 모드가 "사람다워졌지만 안 붙는다"거든요.
5. 한 번의 예측으로 끝내지 말고 **예측 → wet 검증 → 재학습**의 closed loop(lab-in-the-loop)로 굴리세요.

---

다음 → **[11. 부록 — 체크리스트·참고자료·재현 환경·용어집](../11_appendix/11_appendix.md)**
