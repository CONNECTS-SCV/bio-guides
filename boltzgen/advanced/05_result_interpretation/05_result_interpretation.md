---
title: "Ch.05 — 결과 해석: 메트릭 정량 해석과 시각화"
chapter: 5
level: advanced
language: ko
---

# Ch.05 — 결과 해석

드디어 설계 결과가 나왔습니다. 그런데 여기서 많은 분들이 길을 잃습니다. **메트릭 CSV에 컬럼이 240개가 넘기 때문입니다!** 이걸 다 봐야 하는가? 어떤 것이 중요한가? 무슨 값이면 좋은 것인가?

이 챕터에서는 이 수많은 메트릭을 **카테고리별로 정리**하고, 각각이 무엇을 재는지·어떤 값이면 좋은지·어떻게 순위가 매겨지는지를 깊이 있게 풀어드리겠습니다. 그리고 마지막에는 우리가 직접 만든 **실측 그래프**로 한눈에 보는 법까지 다루겠습니다.

> **실습 — `05_analysis_viz.ipynb`** · ① 직접 설계 실행 → ② 내 결과 확인 → ③ 레퍼런스 대조 · **분석 셀 6초**
>
> 설계를 직접 돌려 `my_run/`에 결과를 만들고, 그 결과로 로드·해석·그래프(상관 히트맵)를 진행합니다. 설계를 건너뛰면 `data/vanilla`의 레퍼런스 결과로 이어집니다. 그래프는 `../boltzgen_viz.py` 모듈을 씁니다.

---

## 5.1 메트릭의 큰 그림 — 240개를 7개 카테고리로

겁먹지 마십시오. 240여 개 컬럼은 사실 **7개 카테고리**로 묶입니다. 우리가 실제로 자주 보는 것은 이 중 10여 개뿐입니다.

| 카테고리 | 무엇을 재나 | 대표 컬럼 |
|----------|------------|-----------|
| 신뢰도(confidence) | 구조·인터페이스 예측이 얼마나 믿을 만한가 | `design_ptm`, `design_to_target_iptm`, `complex_plddt` |
| 위치오차(PAE) | 잔기 간 상대 위치 오차 | `min_design_to_target_pae` |
| 구조편차(RMSD) | 설계 vs 재예측 구조 차이 | `filter_rmsd`, `designfolding-filter_rmsd` |
| 인터페이스 | 결합면의 물리적 상호작용 | `plip_hbonds_refolded`, `plip_saltbridge_refolded`, `delta_sasa_refolded` |
| 개발성(liability) | 항체·나노바디의 제조 안정성 | `liability_score`, `liability_*_count` |
| 친화도(affinity) | 소분자 결합 세기 | `affinity_pred_value`, `affinity_probability_binary` |
| 다양성/신규성 | 디자인 간 다양성, 학습셋 대비 신규성 | `vendi_*`, `novelty` |

> 참고 — 일부 컬럼은 **데이터셋·실행 옵션에 따라 생성되지 않을 수 있습니다**. `affinity_*`는 소분자 프로토콜에서만, `liability_*`는 항체/나노바디에서만 나오고, `vendi_*`·`novelty`·`complex_plddt`는 실행·분석 옵션에 따라 다릅니다. 본인 CSV의 실제 컬럼은 `df.columns`로 확인하십시오.

하나씩 깊이 들어가 보겠습니다.

---

## 5.2 신뢰도 메트릭 — pTM, ipTM, pLDDT

### TM-score와 pTM

먼저 **TM-score**(Template Modeling score)를 알아야 합니다. 두 구조가 얼마나 비슷한지를 0~1로 재는 지표인데, 이렇게 정의됩니다.

$$
\text{TM} = \frac{1}{L}\sum_{i=1}^{L}\frac{1}{1+\left(d_i/d_0(L)\right)^2}, \qquad d_0(L)=1.24\sqrt[3]{L-15}-1.8
$$

여기서 $d_i$는 정렬된 $i$번째 잔기 쌍의 거리, $L$은 길이입니다. 핵심은 **분모에 길이 보정 $d_0$이 들어가서, RMSD와 달리 길이에 덜 휘둘린다**는 점입니다. 그래서 단백질 비교의 표준 지표로 쓰입니다. TM ≥ 0.5면 "같은 fold"로 봅니다.

**pTM**(predicted TM-score)은 모델이 *스스로 예측한* TM-score입니다. 즉 "내가 예측한 이 구조가 실제 구조와 TM 얼마쯤 될 것 같다"는 자기 신뢰도입니다. BoltzGen에서.

- **`design_ptm`** = 설계 단백질 자체의 구조 신뢰도. 높을수록 좋음. **0.7 이상이면 양호, 0.8 이상이면 우수**.

### ipTM — 인터페이스 신뢰도 (가장 중요!)

**ipTM**(interface pTM)은 pTM을 **서로 다른 체인 사이의 잔기 쌍에만** 적용한 것입니다. 즉 "바인더와 타깃이 만나는 면을 얼마나 자신 있게 예측했나"입니다.

- **`design_to_target_iptm`** = 바인더-타깃 인터페이스 신뢰도. **바인더 설계에서 가장 결정적인 단일 지표**입니다. 결합 자체의 믿음직함을 재기 때문입니다.
- 해석: **0.5 이상이면 결합 가능성 양호**. 어려운 타깃에서는 0.3~0.5도 의미 있습니다.

> 심화 — 왜 ipTM이 pTM보다 중요한가? pTM이 높아도(구조는 잘 잡혀도) ipTM이 낮으면 "혼자서는 잘 접히지만 타깃엔 안 붙는" 디자인일 수 있습니다. 우리 목적은 *결합*이니, 인터페이스 신뢰도가 본질입니다. 실제로 나노바디·핵산 실습에서 **ipTM이 순위를 강하게 좌우하는 핵심 지표**임을 보게 됩니다(단, 최종 순위는 ipTM·pTM·PAE 종합).

### pLDDT — 잔기별 국소 신뢰도

**pLDDT**(predicted lDDT)는 잔기 하나하나의 국소 구조 신뢰도입니다(0~100 또는 0~1). `complex_plddt`로 들어 있습니다. CIF 파일의 B-factor 칸에도 인코딩돼서, PyMOL에서 색으로 볼 수 있습니다(파랑=높음, 빨강=낮음).

![pLDDT 색칠 구조](05_plddt_structure.png)

*실제 1위 디자인(바인더)을 pLDDT로 색칠한 모습(파랑=신뢰도 높음, 빨강=낮음). 보통 코어는 파랗고(안정) 말단·loop는 붉은 편입니다. 메트릭 숫자(`complex_plddt`)를 구조 위에서 직접 눈으로 확인하는 방법입니다. (렌더링: `../FIGURE_PLAN.md`)*

> 주의 — 흔한 오해 하나. pLDDT는 **순위 결정의 주 지표가 아닙니다**. BoltzGen 바인더 설계의 순위는 ipTM·pTM·PAE·H-bond·salt-bridge·ΔSASA 종합으로 정해지고, pLDDT(`complex_plddt`)는 240여 컬럼 중 하나의 보조 지표일 뿐입니다. (다른 도구 경험 때문에 pLDDT를 1순위로 보는 분들이 많아 강조합니다.)

---

## 5.3 위치오차(PAE)와 구조편차(RMSD)

### PAE — Predicted Aligned Error

**PAE**는 "잔기 A 기준으로 정렬했을 때 잔기 B의 위치 오차가 몇 Å일까"의 예측입니다. 낮을수록 좋습니다(단위 Å).

- **`min_design_to_target_pae`** = 바인더-타깃 사이 최소 PAE. **낮을수록 인터페이스 위치가 확실**. 5Å 미만이면 좋은 편.

### RMSD — 자기일관성의 핵심

Ch.01의 "자기일관성"을 기억하실 것입니다. 그것을 숫자로 재는 것이 RMSD입니다. **설계한 백본 구조**와 **Boltz-2가 서열로부터 다시 예측한 구조**가 얼마나 다른지를 Å로 잽니다.

$$
\text{RMSD} = \sqrt{\frac{1}{N}\sum_{i=1}^{N}\lVert \mathbf{x}_i^{\text{design}}-\mathbf{x}_i^{\text{refold}}\rVert^2}
$$

- **`filter_rmsd`** = 필터링에 쓰는 RMSD. **2Å 미만 우수, 2~5Å 양호, 5Å 초과 주의**.
- **`designfolding-filter_rmsd`** = 바인더를 *단독으로* 다시 접었을 때의 RMSD(단백질 프로토콜만). 타깃 없이도 구조가 유지되는지.

> 심화 — RMSD가 낮다는 것은 "설계 의도대로 서열이 그 구조를 실현한다"는 뜻입니다. 즉 합성했을 때 의도한 모양이 나올 가능성이 높습니다. 다만 RMSD가 낮아도 ipTM이 낮으면 "모양은 맞는데 안 붙는" 경우라, **RMSD와 ipTM을 함께** 봐야 합니다.

---

## 5.4 인터페이스 메트릭 — 결합면을 들여다보기

구조가 맞아도, *실제로 어떻게 붙는지*를 봐야 합니다. BoltzGen은 PLIP(Protein-Ligand Interaction Profiler) 등으로 결합면의 물리적 상호작용을 셉니다.

- **`plip_hbonds_refolded`** = 인터페이스 수소결합 개수. 많을수록 결합이 단단할 수 있음(단, 위치·맥락이 더 중요).
- **`plip_saltbridge_refolded`** = 염다리(이온 결합) 개수. 전하 상호작용.
- **`delta_sasa_refolded`** = 결합으로 묻히는 표면적(ΔSASA, Å²). **클수록 접촉면이 넓다** → 강한 결합 경향.

> 주의 — 수소결합 개수만 보고 판단하지 마십시오. 실측에서 **H-bond 0개인데 순위가 높은** 디자인도 있습니다(소수성·정전기 상호작용으로 충분히 결합). 인터페이스 메트릭은 *조합*으로 봐야 합니다.

---

## 5.5 개발성(Developability) — 항체·나노바디의 숨은 핵심

항체/나노바디 프로토콜에서는 특별한 메트릭군이 추가됩니다. 바로 **developability liabilities**(개발성 위험 모티프)입니다. 이것은 "실험에서 잘 붙느냐"를 넘어 **약으로 만들 수 있느냐**를 봅니다.

| 컬럼 | 의미 |
|------|------|
| `liability_score` | 종합 위험 점수 (낮을수록 좋음) |
| `liability_num_violations` | 위반 모티프 총 개수 |
| `liability_high/medium/low_severity_violations` | 심각도별 위반 수 |
| `liability_MetOx_count` | 메티오닌 산화 위험 |
| `liability_TrpOx_count` | 트립토판 산화 위험 |
| `liability_AspCleave/AspBridge_count` | 아스파르트산 이성질화·절단 위험 |
| `liability_ProtTryp_count` | 단백분해 효소 절단 부위 |
| `liability_HydroPatch_count` | 소수성 패치(응집 위험) |

> 심화 — 이것이 왜 중요한가? 결합은 잘하는데 Met이 산화되거나 Asp가 이성질화되면, 보관 중에 변질되거나 면역원성이 생겨 **약으로 못 씁니다**. 그래서 항체 설계에서는 ipTM뿐 아니라 `liability_score`가 낮은(=제조 안정성이 좋은) 후보를 함께 고릅니다. (Ch.08 항체 실습에서 실제 liability를 봅니다.)

---

## 5.6 친화도(Affinity) — 소분자 결합의 세기

소분자 프로토콜(`protein-small_molecule`)에서만 나오는 메트릭입니다. 별도의 affinity 스텝(Ch.04)이 예측해줍니다.

- **`affinity_pred_value`** = 예측 결합 친화도 (대략 결합 세기의 회귀값).
- **`affinity_probability_binary`** (및 `_binary1`, `_binary2`) = "결합한다/안 한다" 이진 확률.

> 심화 — 친화도 예측은 본질적으로 어려운 문제라, 절대값보다 **상대 비교**로 쓰는 것이 안전합니다. "후보들 중 affinity_pred_value가 상대적으로 높은 것"을 우선 검토하는 식입니다. (Ch.10에서 chorismate 결합 효소로 실습.)

---

## 5.7 다양성·신규성

- **`vendi_*`**(vendi_tm_align 등) = 선택된 디자인 집합의 **다양성 점수**. 서로 얼마나 다른지.
- **`novelty`** = 학습 데이터(기존 단백질) 대비 **얼마나 새로운가**(FoldSeek 기반). 신규 fold를 원하면 높을수록 좋음.

이 둘은 개별 디자인보다 **선별 집합 전체의 성격**을 평가할 때 봅니다.

---

## 5.8 순위는 어떻게 정해질까 — `rank_*` → `final_rank`

가장 자주 받는 질문입니다. "왜 pTM 1등이 최종 1등이 아닌가?"

BoltzGen은 **한 메트릭으로 줄세우지 않습니다.** 여러 메트릭을 각각 순위화한 뒤(컬럼 `rank_*`) 종합합니다.

```
rank_design_to_target_iptm      (ipTM)
rank_design_ptm                 (pTM)
rank_neg_min_design_to_target_pae  (PAE, 낮을수록 좋으니 음수화)
rank_plip_hbonds_refolded       (H-bond)
rank_plip_saltbridge_refolded   (salt-bridge)
rank_delta_sasa_refolded        (ΔSASA)
        ↓ 종합
   max_rank → secondary_rank → final_rank
```

그래서 한 지표만 특출난 디자인보다, **여러 지표가 고르게 좋은** 디자인이 위로 올라옵니다.

### 다양성 선택 — lazy-greedy

`budget`개를 최종 선별할 때는 품질만이 아니라 다양성도 봅니다. 목적함수는 대략 다음과 같습니다.

$$
\text{score}(d) = (1-\alpha)\cdot \text{quality}(d) + \alpha\cdot \big(1 - \max_{s\in S}\text{sim}(d, s)\big)
$$

여기서 $S$는 이미 뽑힌 집합, $\text{sim}$은 서열 유사도, $\alpha$는 **품질↔다양성 가중치**(`--alpha`)입니다. $\alpha=0$이면 품질만, $\alpha=1$이면 다양성만. 이것을 lazy-greedy로 하나씩 골라 `budget`을 채웁니다.

> 심화 — `--alpha`를 올리면 서로 더 다른 디자인이 뽑힙니다(실험 다각화). 기본값은 작습니다(펩타이드 0.01, 그 외 0.001). Ch.06에서 이 값을 조절해 선별 성격을 바꿔봅니다.

---

## 5.9 공식 도구 — `filter.ipynb`

BoltzGen 레포에는 `filter.ipynb`라는 **공식 필터링·시각화 노트북**이 들어 있습니다. 분석까지 끝난 결과에서.

1. **하드 필터** 적용 (예: RMSD < 2.5)
2. **품질 순위** 계산 (메트릭별 가중치 `metrics_override`)
3. **다양성 선택** (lazy-greedy, `alpha`)
4. **시각화** — `results_overview.pdf`(표·히스토그램·산점도·서열 로고·liability 히트맵)

핵심 파라미터.

```python
Filter(
    design_dir=..., outdir=..., budget=5,
    use_affinity=False,            # 소분자면 True
    refolding_rmsd_threshold=2.5,  # RMSD 하드 필터
    alpha=0.1,                     # 품질↔다양성
    metrics_override={...},        # 메트릭별 중요도
    additional_filters=[...],      # 추가 하드 필터
)
```

필터링은 몇 초면 끝나니, **`boltzgen run --steps filtering`이나 이 노트북으로 기준을 여러 번 바꿔가며** 최적 선별을 찾는 것이 실전 워크플로우입니다(Ch.06).

---

## 5.10 시각화 — 한눈에 보기 (실측 그래프)

수십 개 메트릭을 표로만 보면 감이 안 옵니다. 그래서 우리는 `../boltzgen_viz.py` 모듈로 **핵심 4지표를 2×2 그래프**로 그립니다. 아래는 실제 vanilla 단백질 설계(10개 최종 디자인)의 메트릭 개요입니다.

![Vanilla 단백질 메트릭 개요](05_vanilla_metrics.png)

이 그림을 읽는 법은 다음과 같습니다.

- **좌상(pTM)**: 10개 모두 0.7 임계선 위 → 구조 신뢰도 전반 양호. rank 3이 0.828로 최고.
- **우상(ipTM)**: 0.44~0.66 분포. rank 5·6·8·9·10이 0.6 이상으로 인터페이스가 가장 믿음직합니다(최고는 rank 6의 0.663). (흥미롭게도 pTM 최고인 rank 3은 ipTM이 0.44로 낮습니다. 이래서 한 지표만 보면 안 됩니다.)
- **좌하(RMSD)**: 9/10이 2Å 미만 → 자기일관성 우수. rank 1만 2.44Å.
- **우하(길이 vs H-bond, rank 색)**: 길이 84~130aa로 다양, H-bond 0~8개. 길이와 H-bond가 비례하지 않음(rank 5는 102aa에 8개, rank 2는 130aa에 1개).

> 심화 — 이 한 장으로 "구조는 다 괜찮은데 인터페이스(ipTM)에서 갈린다"는 핵심을 즉시 파악할 수 있습니다. 실험 후보를 고른다면 **ipTM이 0.6을 넘는 rank 5·6·8·9·10**을 우선 보고, 구조 안정성을 원하면 RMSD가 최저인 디자인을, 다양성을 원하면 서로 다른 길이·전략을 섞어 고르면 됩니다. 같은 모듈로 항체·나노바디·핵산·소분자 그래프도 그립니다(Part B).

### 메트릭 간 상관관계도 봐두면 좋습니다

추가로, 메트릭끼리 얼마나 독립적인지(상관관계)를 보면 "어떤 지표를 함께 봐야 하는지" 감이 옵니다. 보통 pTM과 ipTM은 약한 상관(서로 다른 정보), 길이와 H-bond는 중간 상관을 보입니다. 즉 **각 메트릭이 독립적인 정보를 주니 종합 판단이 필요**하다는 결론으로 이어집니다(노트북 `05_analysis_viz.ipynb` 3절에서 상관행렬 생성).

---

### 이 챕터 핵심 요약

1. 240개 메트릭은 **7개 카테고리**로 묶입니다. 실제로는 ipTM·pTM·RMSD·PAE·H-bond·ΔSASA·(liability/affinity) 정도를 봅니다.
2. **ipTM(`design_to_target_iptm`)이 결합의 핵심 지표**, RMSD는 자기일관성, 둘을 함께 봐야 합니다.
3. pLDDT(`complex_plddt`)는 **순위의 주 지표가 아닙니다.** 보조 지표입니다.
4. 항체·나노바디는 **liability(개발성)**, 소분자는 **affinity**가 추가 핵심.
5. 순위는 `rank_*` 종합(`final_rank`), 선별은 품질↔다양성(`alpha`)의 lazy-greedy.
6. `boltzgen_viz.py`의 **2×2 개요 그래프**로 핵심을 한눈에 — "구조는 OK, 인터페이스에서 갈린다"를 즉시 파악.

다음 → **[06. 고급 활용 및 AI 적용](../06_advanced_ai/06_advanced_ai.md)**
