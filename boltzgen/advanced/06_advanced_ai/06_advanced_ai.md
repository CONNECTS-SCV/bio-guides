---
title: "Ch.06 — 고급 활용 및 AI 적용: 워크플로우·자동화·산업 적용"
chapter: 6
level: advanced
language: ko
---

# Ch.06 — 고급 활용 및 AI 적용

여기까지 오셨다면 이제 BoltzGen을 "돌릴 줄 아는" 단계는 넘었어요. 이 챕터에서는 진짜 전문가들이 쓰는 **고급 전략**을 다뤄요. 단순히 한 번 돌리는 게 아니라, **여러 단계를 조합하고, 자동화하고, 커스터마이즈하고, 실제 연구·산업 문제에 적용**하는 법이에요.

이 챕터의 기법들을 익히면, 수백~수천 개 디자인을 효율적으로 걸러내고, 반복 실험을 자동화하고, 특정 목적에 맞게 BoltzGen을 길들일 수 있게 돼요.

> **실습 — `06_advanced_filtering.ipynb`** · **분석 셀 3초** — Ch.05에서 직접 돌린 결과가 있으면 그걸 이어받습니다
>
> `data/vanilla`의 `all_designs_metrics.csv`(전체 디자인)에 직접 하드필터를 걸고, CLI 옵션(`metrics_override`·`additional_filters`·`alpha`·`size_buckets`) 매핑과 `compare_bars` 비교 시각화까지 해봅니다.

---

## 6.1 계층적 스크리닝 (Hierarchical Screening)

가장 중요한 고급 전략이에요. 무작정 6만 개를 돌려서 다 분석하는 건 비효율적이에요. 대신 **단계적으로 좁혀가요.**

```
Level 1 — 넓고 얕게: num_designs 大, 빠른 필터
    boltzgen run spec.yaml --num_designs 10000 --budget 200 --output L1
        ↓ 상위 후보 선별, YAML 제약 보강(결합부위 좁히기 등)
Level 2 — 좁고 깊게: 유망 영역 집중 재생성
    boltzgen run spec_refined.yaml --num_designs 5000 --budget 20 --output L2
        ↓
Level 3 — 최종 검증: 실험 가능한 top 5~10
```

이 방식의 핵심은 **Level이 올라갈수록 num_designs는 줄이고 제약은 강화**하는 거예요. Level 1에서 "어느 결합 전략이 잘 되는지" 감을 잡고, Level 2에서 그 방향으로 집중 탐색하는 거죠. 비용은 줄이고 품질은 올리는 패턴이에요.

---

## 6.2 단계별 툴 조합 — `--steps`로 파이프라인 분해

Ch.04에서 `--steps`를 배웠죠. 고급에서는 이걸 **워크플로우 설계의 핵심 도구**로 써요.

```bash
# 1) 무거운 생성·검증은 한 번만 (design~analysis)
boltzgen run spec.yaml --output run1 \
  --steps design inverse_folding folding design_folding analysis \
  --num_designs 5000

# 2) 필터링은 기준 바꿔가며 여러 번 (각 몇 초)
boltzgen run spec.yaml --output run1 --steps filtering --budget 20
boltzgen run spec.yaml --output run1 --steps filtering --budget 50 \
  --additional_filters 'designfolding-filter_rmsd<2.0'
```

> 심화 — 핵심 통찰: **생성(무거움)과 선별(가벼움)을 분리**하면, 한 번의 비싼 생성으로 수십 가지 선별 전략을 실험할 수 있어요. "어떤 기준이 실험에서 잘 맞았나"를 데이터로 학습해, 다음 프로젝트의 필터를 개선하는 선순환을 만들 수 있죠.

---

## 6.3 자동화 파이프라인 — 파라미터 스윕

여러 설정을 체계적으로 비교하려면 스윕(sweep)을 자동화해요.

```python
# sweep.py — num_designs × budget 조합 자동 실행
import subprocess, itertools, pandas as pd, pathlib

budgets = [20, 50, 100]
nums    = [1000, 5000]
results = []
for budget, num in itertools.product(budgets, nums):
    out = f"sweep/b{budget}_n{num}"
    subprocess.run(["boltzgen","run","design.yaml","--output",out,
                    "--protocol","protein-anything",
                    "--num_designs",str(num),"--budget",str(budget)], check=True)
    csv = pathlib.Path(out)/"final_ranked_designs"/f"final_designs_metrics_{budget}.csv"
    df = pd.read_csv(csv); df["budget"]=budget; df["num_designs"]=num
    results.append(df)

allr = pd.concat(results)
# 설정별 평균 ipTM 비교 → 최적 운영점 탐색
print(allr.groupby(["num_designs","budget"])["design_to_target_iptm"].mean())
```

여러 타깃·프로토콜을 동시에 돌리는 패턴도 있어요(GPU 여유가 있을 때).

```bash
boltzgen run spec.yaml --protocol protein-anything --output out/prot &
boltzgen run spec.yaml --protocol peptide-anything --output out/pep &
wait   # 모두 완료 대기 후 비교
```

> 심화 — GPU가 하나면 동시 실행은 메모리 경합·OOM을 부르니, **순차 실행 + 백그라운드 큐**가 안전해요. 큰 작업은 `--num_designs`를 쪼개 여러 번 돌린 뒤 `boltzgen merge`로 합치는 게 정석이에요(메모리 안정성 + 중단 복구).

---

## 6.4 필터링 고급 제어 — 선별을 내 마음대로

`filtering` 스텝은 여러 강력한 노브를 제공해요. 이걸 잘 쓰면 "내 프로젝트에 맞는 선별 기준"을 정밀하게 만들 수 있어요.

### `--metrics_override` — 메트릭별 가중치

어떤 메트릭을 더/덜 중요하게 볼지 가중치를 줘요(값이 클수록 *덜* 중요하게 = down-weight).

```bash
# 수소결합과 ΔSASA의 중요도를 낮춤 (ipTM·RMSD를 상대적으로 강조)
boltzgen run spec.yaml --output out --steps filtering \
  --metrics_override plip_hbonds_refolded=4 delta_sasa_refolded=2
```

### `--additional_filters` — 하드 필터

특정 조건을 못 넘으면 아예 탈락시켜요.

```bash
boltzgen run spec.yaml --output out --steps filtering \
  --additional_filters 'design_ALA<0.3' 'design_GLY<0.2' \
                       'designfolding-filter_rmsd<2.0'
```

`feature>threshold` 또는 `feature<threshold` 형식인데, **부등호는 "통과 조건"이지 "탈락 조건"이 아니에요.**

- `<` = **이 값 이하만 통과**(작을수록 좋은 지표 — 낮은 값이 좋다).
- `>` = **이 값 이상만 통과**(클수록 좋은 지표 — 높은 값이 좋다).

그래서 위 예는 "Ala 비율 0.3 이하 **그리고** Gly 비율 0.2 이하 **그리고** 단독 재접힘 RMSD 2Å 이하인 디자인만 통과"예요. 헷갈리기 쉬운 지점: Ala가 너무 많은 디자인을 **버리고** 싶다면 `design_ALA<0.3`이 맞아요. `design_ALA>0.3`이라고 쓰면 정반대로 **Ala가 30% 넘는 디자인만 남겨요**(내장 `filter_biased`가 Ala-rich 배제를 `ALA_fraction / lower_is_better: true / 0.3`으로 표현하는 것과 같은 방향이에요).

### `--size_buckets` — 크기 구간별 할당

길이 구간마다 최대 몇 개씩 뽑을지 정해요(다양한 크기 확보).

```bash
boltzgen run spec.yaml --output out --steps filtering \
  --size_buckets 10-20:5 20-30:10
```

### `--alpha` — 품질 ↔ 다양성

Ch.05의 다양성 목적함수 가중치예요. 0이면 품질만, 1이면 다양성만.

```bash
boltzgen run spec.yaml --output out --steps filtering --alpha 0.3   # 다양성 강조
```

### `--filter_biased` — 아미노산 조성 이상치 제거

ALA/GLY/GLU/LEU/VAL이 비정상적으로 많은(생성 모델이 종종 만드는 "치트성") 디자인을 거를지(기본 true).

> 심화 — 이 네 노브(`metrics_override`/`additional_filters`/`size_buckets`/`alpha`)를 조합하면 "내 실험 성공률 데이터에 맞춘 맞춤 선별기"를 만들 수 있어요. 예를 들어 과거 실험에서 "ΔSASA 큰 게 잘 됐다"면 그 가중치를 올리고, "Ala 많으면 실패했다"면 하드 필터를 거는 식으로요. 이게 **AI 설계를 실험 피드백으로 개선하는 루프**의 출발점이에요.

---

## 6.5 커스텀 Scaffold 만들기

항체·나노바디뿐 아니라, **내가 가진 검증된 단백질 골격**을 scaffold로 써서 그 위에 결합부위만 재설계할 수 있어요. scaffold YAML은 이렇게 만들어요.

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
  - group: { id: A, visibility: 2 }                       # 골격 구조 유지
  - group: { id: A, visibility: 0, res_index: 26..34,52..59,98..118 }  # 결합부위는 자유
design_insertions:            # 결합부위 길이 가변 (loop 연장)
  - insertion: { id: A, res_index: 26, num_residues: 1..5 }
reset_res_index:
  - chain: { id: A }
```

그리고 타깃 YAML에서 이 scaffold를 불러와요.

```yaml
entities:
  - file: { path: target.cif, include: [ { chain: { id: B } } ] }
  - file: { path: my_scaffold.yaml }   # 여러 개 나열하면 BoltzGen이 최적 선택
```

> 심화 — 여러 scaffold를 동시에 주면, BoltzGen이 각 골격으로 설계를 시도하고 **자동으로 최적을 선택**해요. CDR3 길이가 다른 scaffold들을 섞으면(짧은 것=평평한 epitope, 긴 것=깊은 pocket) 다양한 타깃 형태에 대응할 수 있어요. 이게 Ch.08(Fab 14종)·Ch.09(나노바디) 실습의 핵심 전략이에요.

---

## 6.6 모델 커스터마이즈 — 체크포인트·커널·역접힘

BoltzGen은 모델 컴포넌트를 교체·조절할 수 있어요(연구용 고급 기능).

| 옵션 | 용도 |
|------|------|
| `--design_checkpoints A.ckpt B.ckpt` | 백본 생성 체크포인트 교체(기본 diverse+adherence) |
| `--inverse_fold_checkpoint C.ckpt` | 역접힘 모델 교체(fine-tune한 가중치 등) |
| `--folding_checkpoint D.ckpt` | 검증(Boltz-2) 체크포인트 교체 |
| `--affinity_checkpoint E.ckpt` | 친화도 예측기 교체 |
| `--step_scale`, `--noise_scale` | 확산 스케줄 고정(탐색 보수성 조절) |

> 심화 — Fine-tuning/custom: 특정 단백질군(예: 막단백질, 특정 효소 패밀리)에 대해 역접힘 모델을 자체 데이터로 fine-tune한 뒤 `--inverse_fold_checkpoint`로 끼워 넣으면, 그 도메인에 특화된 서열 설계가 가능해요. 또 `--design_checkpoints`로 다양성/제약준수 비중이 다른 커스텀 확산 모델을 조합할 수도 있고요. 이건 연구 프론티어 영역이라, 표준 워크플로우로 충분치 않을 때만 손대세요.

---

## 6.7 다른 도구와의 연계 (Tool Chaining)

BoltzGen 결과를 다른 도구로 **교차 검증·후처리**하면 신뢰도가 올라가요.

- **AutoDock Vina** — 소분자 결합을 독립적으로 재도킹해 친화도 교차 검증.
  ```bash
  vina --receptor protein.pdbqt --ligand ligand.pdbqt --out docked.pdbqt
  ```
- **PyMOL** — 인터페이스 잔기·수소결합·이황화 거리 시각 검증(`refold_cif` 사용).
- **ESM / 서열 분석** — 면역원성·발현성·humanness 예측을 서열에 추가로 적용.
- **MD 시뮬레이션(GROMACS 등)** — 상위 후보의 결합 안정성을 동역학으로 검증.

> 심화 — 권장 검증 파이프라인: BoltzGen(생성·1차 검증) → liability/humanness(서열 필터) → 분자도킹·MD(물리 검증) → 실험. 각 단계가 다른 가정으로 거르니, 통과한 후보의 신뢰도가 곱으로 올라가요.

---

## 6.8 연구·산업 적용 방안

마지막으로, 이 모든 걸 **실제 문제**에 어떻게 적용하는지 큰 그림을 그려볼게요.

| 분야 | 적용 | 추천 프로토콜 / 전략 |
|------|------|----------------------|
| 항암 신약 | 종양 단백질 억제 바인더 | nanobody/peptide, 결합부위=기능 부위 |
| 항바이러스 | 표면 단백질 중화 | nanobody-anything, 변이 내성 고려한 부위 선정 |
| 자가면역 | 사이토카인 차단 항체 | antibody-anything, liability 최소화 |
| 진단 | 바이오마커 검출 시약 | nanobody(안정·저비용), 특이성 우선 |
| 효소·그린케미스트리 | 신규 촉매·기질 결합 | protein-small_molecule, affinity 활용 |
| 바이오센서 | 특정 분자 감지 | small_molecule binding, 구조 변화 설계 |
| 합성생물학 | 유전자 조절(DNA/RNA 결합) | DNA/RNA 타깃, zinc finger 패턴(Ch.11) |

**실전 케이스 흐름(예: 신약 후보 발굴)**

```
타깃 선정·구조 확보(Ch.02) → 결합부위 전략 수립
   → Level 1 광역 스크리닝(num_designs 10k+)
   → liability/affinity로 필터(Ch.06.4)
   → Level 2 집중 재설계 → top 10~50 선별
   → 도킹/MD 교차검증(Ch.06.7) → 합성·실험 검증
   → 실험 결과로 필터 기준 개선 → 다음 라운드
```

> 심화 — AI 설계는 **실험을 대체하는 게 아니라 앞단을 압축**하는 거예요. 핵심 가치는 "수만 개 가상 후보를 며칠 만에 만들고, 정량 메트릭으로 수십 개로 좁혀, 실험 자원을 가장 유망한 곳에 집중"시키는 데 있어요. 그리고 실험 피드백을 필터·모델에 되먹이면(6.4·6.6), 라운드를 거듭할수록 똑똑해지는 폐루프가 완성돼요.

---

### 이 챕터 핵심 요약

1. **계층적 스크리닝**(넓게→좁게)으로 비용↓ 품질↑.
2. **`--steps`로 생성/선별 분리** — 비싼 생성 한 번, 가벼운 필터 여러 번.
3. **파라미터 스윕**(subprocess+pandas)으로 최적 운영점 자동 탐색, 대규모는 `merge`.
4. 필터 4노브(**`metrics_override`·`additional_filters`·`size_buckets`·`alpha`**)로 맞춤 선별기 구축.
5. **커스텀 scaffold·체크포인트**로 도메인 특화, **타 도구 연계**로 교차 검증.
6. AI 설계의 본질은 **실험 앞단 압축 + 피드백 폐루프**예요.

다음 → **[07. 실습: 펩타이드·고리형 설계](../07_peptide_cyclic/07_peptide_cyclic.md)** (Part B 시작)
