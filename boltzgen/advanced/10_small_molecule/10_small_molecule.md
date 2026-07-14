---
title: "Ch.10 — 실습: 소분자 결합 단백질·친화도 예측"
chapter: 10
level: advanced
language: ko
part: B
---

# Ch.10 — 실습: 소분자 결합 단백질·친화도 예측

지금까지는 단백질·펩타이드·항체로 **다른 단백질에 붙는** 바인더를 만들었어요. 이번엔 방향이 조금 달라요. **작은 화합물(소분자, ligand)에 결합하는 단백질**을 설계해볼 거예요. 효소·바이오센서·약물 운반체 설계의 토대가 되는 실습이에요.

그리고 이 프로토콜만의 특별한 기능, **결합 친화도(affinity) 예측**도 직접 봐요.

> **실습 — `10_small_molecule_lab.ipynb`** · ① 직접 설계 실행 → ② 내 결과 확인 → ③ 레퍼런스 대조 · **분석 셀 3초**
>
> 내가 돌린 chorismate 바인더 결과(건너뛰면 `data/small_molecule`) 로드 · **affinity 패널 그래프** · 친화도(`affinity_pred_value`/`affinity_probability_binary`) 랭킹 · 포켓 품질(ΔSASA·H-bond) 분석.

---

## 10.1 왜 소분자 결합 단백질인가

작은 화합물에 결합하는 단백질은 쓰임새가 정말 넓어요.

- **효소(enzyme)** — 기질(substrate)에 결합해 화학 반응을 촉매. 신규 효소 설계는 그린케미스트리·바이오 제조의 핵심.
- **바이오센서** — 특정 분자(대사물질·독소·마커)에 결합하면 신호를 내는 검출기.
- **약물 운반·격리** — 약물이나 독성 분자를 붙잡아 운반하거나 중화.
- **대사 조절** — 보조인자(ATP, NAD 등)나 대사물질에 결합해 경로를 조절.

즉 "단백질이 작은 분자를 정확히 알아보고 붙잡는" 능력을 설계하는 거예요.

---

## 10.2 ligand 지정 — CCD vs SMILES

소분자(ligand)는 두 가지로 지정해요(Ch.02 복습).

```yaml
# 방법 1: CCD 코드 (PDB 화학성분 사전, 잘 알려진 분자)
- ligand: { id: B, ccd: TSA }    # chorismate mutase의 전이상태 유사체

# 방법 2: SMILES (표준 코드가 없는 신약 후보 등)
- ligand: { id: B, smiles: "C1CNC[C@@H]1OC2=C(...)..." }
```

이번 실습 타깃은 **chorismate**(아미노산 생합성 중간체)예요. 정확히는 그 전이상태 유사체(CCD `TSA`)에 결합하는 단백질을 설계해, chorismate mutase 같은 효소의 활성부위를 모사해요.

```yaml
entities:
  - protein: { id: A, sequence: 140..180 }   # 설계할 효소(140~180잔기)
  - ligand:  { id: B, ccd: TSA }              # 결합할 소분자
```

> 심화 — 소분자 결합은 단백질-단백질보다 까다로워요. 작은 분자는 결합면이 좁아 "포켓"에 정확히 맞아야 하거든요. 그래서 `num_designs`를 더 크게(3,000+) 잡는 걸 권장해요. CCD 코드는 RCSB에서 해당 분자를 검색해 찾고, 없으면 SMILES나 `.sdf`로 직접 넣어요.

---

## 10.3 `protein-small_molecule` 프로토콜 — 7단계!

소분자 프로토콜은 다른 것과 결정적으로 달라요. **affinity(친화도) 예측 단계가 추가**돼서 **7단계**예요.

```
design → inverse_folding → folding → design_folding → affinity → analysis → filtering
                                                       ↑ 소분자만!
```

`design_folding`도 포함(단백질 기반이라)되고, 거기에 `affinity` 스텝이 더해져요.

```bash
boltzgen run example/protein_binding_small_molecule/chorismite.yaml \
  --output workbench/sm --protocol protein-small_molecule \
  --num_designs 30 --budget 10
```

> 주의 — affinity 예측을 쓰려면 반드시 `protein-small_molecule` 프로토콜이어야 해요. 다른 프로토콜로 돌리면 affinity 컬럼이 안 나와요.

> **직접 돌려보려면** — 위 명령이 이 챕터의 실측 결과(10.6)를 만든 그 명령이에요(복합체 156~176 토큰 — 단백질 140~160잔기 + TSA 리간드 16원자. **리간드는 원자당 1토큰**이라 16을 더해요. 부록 A8 참고). 다만 이 프로토콜은 **affinity 단계가 추가된 7단계**라 디자인당 시간이 더 걸려요(affinity만 ~17초). Colab **T4 런타임**에서 맛만 보려면 `--num_designs 8 --budget 4`로 줄이세요 — **약 10분(실측 585초, 최종 4개)** 규모예요.
>
> **프로덕션 규모**로 갈 때는 `--num_designs 3000 --budget 40` 정도로 키워요. 수 시간~수십 시간이 걸리는 규모라, 학습 단계에서는 위의 30개로 충분해요.

---

## 10.4 Binding Pocket — 소분자가 들어갈 공간

소분자 결합의 핵심은 **포켓(pocket)**이에요. 단백질 표면에 움푹 들어간 공간에 소분자가 쏙 들어가, 안쪽 잔기들과 다양한 상호작용(수소결합·소수성·π-π 스택·염다리)을 맺어요.

좋은 포켓의 조건.
- **모양 상보성(shape complementarity)** — 소분자와 포켓 모양이 잘 맞음
- **충분한 매몰** — 소분자가 충분히 묻힘(노출되면 약하게 결합)
- **적절한 상호작용** — 수소결합·소수성 접촉이 골고루

결과에서 `delta_sasa_refolded`(매몰 표면적)와 `plip_hbonds_refolded`(수소결합)로 포켓 품질을 가늠해요.

---

## 10.5 친화도(Affinity) 메트릭 — 어떻게 읽나

이 프로토콜만의 특별한 출력이에요.

| 컬럼 | 의미 |
|------|------|
| `affinity_pred_value` | 예측 결합 친화도(회귀값, 대략 결합 세기) |
| `affinity_probability_binary` | "결합한다" 이진 확률 |
| `affinity_probability_binary1`, `_binary2` | 보조 이진 분류 확률 |
| `affinity_pred_value1`, `_value2` | 보조 회귀값 |

> 심화 — 친화도 예측은 본질적으로 어려운 문제라, **절대값보다 상대 비교**로 쓰는 게 안전해요. "후보들 중 affinity_pred_value가 상대적으로 높고 affinity_probability_binary가 높은 것"을 우선 검토하는 식이에요. 그리고 BoltzGen affinity는 1차 스크리닝 신호로 쓰고, 유망 후보는 **AutoDock Vina 같은 도킹·MD로 교차 검증**하는 게 정석이에요(Ch.06.7).

---

## 10.6 실측 결과 — Chorismate 결합 단백질

실제로 `protein-small_molecule`, num_designs 30, budget 10으로 돌린 결과예요. **7단계(affinity 포함)**가 정상 완료됐어요.

![Small molecule 메트릭 개요](10_small_molecule_metrics.png)

1위 디자인의 결합 포켓을 들여다보면 이래요.

![소분자 결합 포켓](10_pocket_structure.png)

*설계한 단백질의 포켓(회색 표면)에 소분자 리간드 chorismate/TSA(초록 sticks)가 쏙 들어간 모습. 청록색이 포켓을 이루는 잔기예요. "이 분자 하나를 감싸는 주머니"를 설계한다는 게 이런 거예요.*

최종 선별셋의 실제 수치(상위 5개).

| rank | id | pTM | ipTM | RMSD(Å) | affinity_pred_value | p_bind |
|------|----|-----|------|---------|---------------------|--------|
| 1 | chorismite_29 | 0.780 | 0.776 | 1.76 | 2.11 | 0.38 |
| 2 | chorismite_28 | 0.768 | 0.761 | **0.79** | 2.39 | 0.41 |
| 3 | chorismite_12 | 0.767 | **0.841** | 0.80 | 2.34 | 0.40 |
| 4 | chorismite_10 | 0.760 | 0.781 | **0.68** | 1.62 | 0.37 |
| 5 | chorismite_14 | 0.813 | 0.757 | 0.80 | 2.01 | 0.35 |

해석 — **우리가 돌린 6개 실습 중 가장 좋은 결과**예요.

- **ipTM이 0.76~0.84로 높게 나왔어요**(rank 3은 0.841). 다만 **주의** — 소분자처럼 작고 조밀한 인터페이스는 ipTM이 높게 나오는 경향이 있어, **단백질-단백질 ipTM과 절대값을 직접 비교하면 안 돼요**(Ch.05). "소분자가 작고 잘 정의된 분자라 그에 맞는 포켓 설계가 큰 단백질 인터페이스보다 수월했다" 정도로 해석하세요.
- **RMSD가 0.68~1.76Å로 매우 낮아요** (rank 2~5는 1Å 미만!). 자기일관성이 탁월하다는 뜻 — 설계 서열이 의도한 포켓 구조를 아주 안정적으로 실현해요.
- **pTM 0.76~0.81**로 구조 신뢰도도 좋아요.
- **affinity 예측**(`affinity_pred_value` 1.6~2.4, `affinity_probability_binary` 0.35~0.41): 절대값보다 상대 비교로 봐요. rank 2·3(affinity 2.39·2.34)이 결합이 가장 강할 것으로 예측돼요.

> 심화 — 왜 소분자가 가장 잘 나왔을까요? 결합 인터페이스가 **작고 명확**하기 때문이에요. 큰 단백질-단백질 인터페이스는 넓은 면을 동시에 맞춰야 해서 어렵지만, 소분자 포켓은 "이 분자 하나를 감싸는 주머니"만 잘 만들면 돼요. 다만 주의할 점 — **ipTM·RMSD가 좋아도 affinity는 별도로 봐야** 해요. 구조적으로 잘 감싸도 실제 결합 세기(친화도)는 다를 수 있거든요. 그래서 affinity 예측이 높은 rank 2·3을 우선 검토하고, AutoDock Vina로 교차 검증하는 게 정석이에요(Ch.06.7).

---

## 10.7 응용 — 바이오센서와 교차 검증

**형광 바이오센서 예시**: 특정 분자(예: glutamate)에 결합하면 구조가 바뀌며 형광이 켜지는 센서.

```yaml
entities:
  - protein: { id: A, sequence: 200..250 }   # 형광 단백질 변이체
  - ligand:  { id: L, ccd: GLU }              # 검출할 분자
```

리간드가 결합 → 구조 변화 → 형광 변화 → 검출. 매우 특이적인 분자 감지가 가능해요.

**교차 검증**: BoltzGen affinity는 빠른 1차 신호예요. 상위 후보는 AutoDock Vina로 재도킹해 친화도를 독립 검증하고, 필요하면 MD로 결합 안정성까지 확인하세요(Ch.06.7).

```bash
# 구조 준비 후 Vina 재도킹
vina --receptor protein.pdbqt --ligand ligand.pdbqt --out docked.pdbqt
```

---

### 이 챕터 핵심 요약

1. 소분자 결합 단백질 = **효소·센서·운반체**의 토대. 작은 분자를 포켓에 정확히 붙잡는 설계.
2. ligand는 **CCD 코드**(알려진 분자) 또는 **SMILES**(신약 후보)로 지정.
3. `protein-small_molecule`은 **affinity 단계가 추가된 7단계** — 친화도 예측은 이 프로토콜에서만.
4. 포켓 품질은 `delta_sasa_refolded`·`plip_hbonds_refolded`, 결합 세기는 `affinity_pred_value`·`affinity_probability_binary`로 — **절대값보다 상대 비교**.
5. 까다로운 타깃이라 `num_designs`를 크게, 유망 후보는 **도킹·MD로 교차 검증**.

다음 → **[11. 실습: 핵산(DNA·RNA) 결합 단백질](../11_nucleic_acid/11_nucleic_acid.md)**
