---
title: "Ch.10 — 후보 랭킹 · GuideDB · 실험 검증"
chapter: 10
language: ko
part: C
---

# Ch.10 — 후보 랭킹 · GuideDB · 실험 검증

Ch.04~09에서 지표를 잔뜩 모았습니다. 이제 그걸 **하나의 순위**로 합치고, 프로젝트로 관리하고, 실험으로 넘깁니다. 이 챕터가 in silico 파트의 종착역입니다.

> **실습 — `10_ranking_lab.ipynb`** · ① 직접 실행 → ② 내 결과 확인 → ③ 레퍼런스 대조 · **전 셀 5초**
>
> 앞 랩들이 만든 내 산출물을 모아 가중합 랭킹을 매기고 candidate report 를 뽑습니다.

---

## 10.1 후보 랭킹 스키마

### 10.1.1 기본 score

여러 지표를 하나로 합칠 때 쓰는 가중합 예시입니다(프로젝트마다 가중치는 튜닝).

```text
Final score =
    0.25 * Humanness score          (OASis / Sapiens)
  + 0.20 * Nativeness score         (AbNatiV)
  + 0.20 * CDR/structure 보존 score (CDR RMSD)
  + 0.15 * Developability score     (TAP/liability)
  + 0.10 * Germline/framework 일관성 (IgBLAST/ANARCI)
  + 0.10 * 전문가 수동 review score
```

### 10.1.2 Hard filter — 즉시 탈락 또는 backmutation 검토

- CDR-H3 핵심 residue 변경
- 알려진 paratope residue 변경
- VH/VL interface core residue 변경
- CDR 구조 RMSD 급증
- CDR/paratope에 N-glycosylation motif 신규 생성
- severe hydrophobic/charge patch 증가
- AbNatiV/OASis가 parental 대비 개선되지 않음

### 10.1.3 Candidate report 템플릿

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

---

## 10.2 운영형 GuideDB schema

가이드를 단순 문서가 아니라 내부 DB(JSON/YAML)로 관리하려면 이 스키마를 추천합니다. 각 프로젝트가 자기완결적으로 입력·후보·점수·결정을 담습니다.

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

`null`은 아직 채우지 않은 값입니다 — 구조·developability는 [Ch.08](../08_structure/08_structure.md)·[Ch.09](../09_developability/09_developability.md)를 돌린 뒤 채웁니다.

---

## 10.3 실험 검증 제안

다시 한 번 — **in silico 결과만으로 성공 판정하지 않습니다.** AI·통계 도구는 실험할 가치가 있는 후보를 빠르게 좁혀주는 강력한 출발점이지, 결승선이 아닙니다. 최소 검증 순서는 이렇습니다.

1. **소량 발현** — HEK293/CHO transient expression
2. **정제** — Protein A/G, SEC purity
3. **결합력** — ELISA 또는 BLI/SPR (parental 대비 KD 유지 확인)
4. **안정성** — DSF/Tm, accelerated stability
5. **응집** — SEC-MALS 또는 DLS
6. **특이성** — cross-reactivity / polyspecificity panel
7. **기능 assay** — neutralization, blocking, internalization 등 target biology에 맞게

> **핵심 —** 가장 먼저, 가장 싸게 확인할 것은 ③ 결합력입니다. humanization의 제1 실패 모드가 "사람다워졌지만 안 붙는다"기 때문입니다. parental과 humanized를 같은 조건에서 SPR/BLI로 비교해 KD가 유지되는지부터 보십시오.

---

<!-- 근거: Frey, Hötzel, Stanton et al. "Lab-in-the-loop therapeutic antibody design with deep learning", bioRxiv 2025.02.19.639050 (Abstract L30-44; Fig.1a caption; §2.2–2.3; §4.4.4–4.4.5). 예측↔wet closed-loop 개념. 논문이 직접 assay한 항목은 결합력(SPR)·발현·비특이성(BV ELISA)·in silico TAP. 중복 점검: wet 검증 패널은 §10.3과 중복되어 재나열 제거하고 §10.3 포인터로 대체 — 이 절은 closed-loop/재학습(§10.3에 없는 부분)만 보완. -->

## 10.4 맺음말 — 예측을 넘어 closed-loop 검증으로 (lab-in-the-loop)

여기까지가 이 가이드가 다룬 **in silico 예측**입니다. ANARCI/IgBLAST로 무엇을 지킬지 못 박고 → BioPhi·Humatch·AnthroAb로 후보를 만들고 → AbNatiV·Ab-RoBERTa·구조 예측으로 사람다움·nativeness·naturalness를 채점했습니다. 하지만 이 모든 점수가 답하는 것은 **"계산상 더 사람답고 그럴듯해졌다"** 까지입니다. 실제로 **붙는지·안정한지·만들어지는지·면역원성이 낮은지**는 컴퓨터가 단정할 수 없습니다.

**그래서 최종 판정은 wet-lab입니다 — 그 구체적 순서·항목(발현·정제·결합력·Tm·응집·특이성·기능 assay)은 §10.3에 정리돼 있습니다.** 이 절은 그 내용을 되풀이하지 않고, **한 번의 검증을 어떻게 반복 시스템으로 끌어올리는가**만 덧붙입니다.

> **핵심 — 예측과 검증을 닫힌 고리로 묶습니다.** 예측 → wet 검증(§10.3) → 그 실험 데이터로 모델을 **재학습** → 다시 예측. 이 closed loop가 **lab-in-the-loop**이고, AI 항체 설계를 한 번의 예측이 아니라 **라운드를 거듭하며 똑똑해지는 시스템**으로 바꿉니다. §10.3이 "한 배치를 **어떻게 검증하나**"라면, 이 절은 "그 검증 결과를 **어떻게 다음 설계에 되먹이나**"입니다.

| 단계 | 하는 일 | 이 가이드 / 사례 |
|---|---|---|
| ① 예측 (in silico) | 후보 생성 + 사람다움·nativeness·구조·developability 채점 | 본 가이드 Ch.04–10 |
| ② wet 검증 | 발현·결합력·Tm·응집·특이성·면역원성 실측 | 본 가이드 §10.3 |
| ③ 재학습 (loop) | 실험 데이터를 generative model·property oracle에 다시 학습 | lab-in-the-loop |

**사례 — Genentech/Roche의 Lab-in-the-loop (LitL).** generative 모델(후보 생성) + property predictor(발현·결합력·비특이성 oracle) + active learning ranking + in vitro SPR을 **하나의 반복 루프**로 묶어, 4개 표적(EGFR·IL-6·HER2·OSM)에 대해 **>1,800개 변이체를 설계·실험**하고 **4 라운드** 최적화로 표적마다 **3–100× 결합력 향상**(최고 결합체 ~100 pM)을 얻었습니다. 핵심은 매 라운드의 실험 결과를 다시 모델 학습에 먹여 점점 좋은 후보를 내놓는 **flywheel** 구조입니다.

> **주의 — 사례의 범위.** LitL 논문은 *humanization*이 아니라 *affinity maturation* 사례이고, 실제로 직접 assay한 property는 **결합력(SPR)·발현·비특이성(BV ELISA)·in silico developability(TAP)** 입니다(Tm·응집·면역원성을 직접 측정한 것은 아님). 다만 **"AI 예측 ↔ wet 검증 ↔ 재학습"이라는 closed-loop 구조 자체**는 humanization 후보 선정에도 그대로 적용됩니다 — oracle을 *결합력 + humanness/면역원성*으로 바꿔 끼우면 됩니다.

**참고문헌 —** Frey N.C., Hötzel I., Stanton S.D., *et al.* "Lab-in-the-loop therapeutic antibody design with deep learning." *bioRxiv* 2025.02.19.639050 (2025). https://doi.org/10.1101/2025.02.19.639050

---

## 이 챕터 핵심 요약

1. 랭킹은 **humanness·nativeness·구조 보존·developability·germline 일관성·전문가 review**의 가중합, 그리고 **hard filter**(CDR-H3 변경, 신규 glycosylation motif 등)로 거릅니다.
2. 프로젝트는 **GuideDB YAML** 한 장으로 입력·annotation·후보·점수·결정을 자기완결적으로 관리합니다.
3. 실험 검증의 **1순위는 결합력**입니다 — humanization의 제1 실패 모드가 "사람다워졌지만 안 붙는다"이기 때문입니다.
4. 한 번의 예측으로 끝내지 말고 **예측 → wet 검증 → 재학습**의 closed loop(lab-in-the-loop)로 굴리세요.

---

다음 → **[11. 부록 — 체크리스트·참고자료·재현 환경·용어집](../11_appendix/11_appendix.md)**
