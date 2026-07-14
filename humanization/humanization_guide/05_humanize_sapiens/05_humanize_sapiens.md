---
title: "Ch.05 — BioPhi / Sapiens / OASis"
chapter: 5
language: ko
part: B
---

# Ch.05 — BioPhi / Sapiens / OASis

드디어 후보를 만듭니다! BioPhi는 머크(Merck)가 공개한 humanization 통합 도구입니다. 그 안에서 실제 사람화를 담당하는 엔진이 **Sapiens**(항체 서열 전용 언어모델), humanness를 평가하는 게 **OASis**입니다.

> **실습 — `05_sapiens_lab.ipynb`** · ① 직접 실행 → ② 내 결과 확인 → ③ 레퍼런스 대조 · **전 셀 6초**
>
> Sapiens 를 직접 돌려 인간화 서열을 만들고, **CDR 가드가 없으면 CDR-L1 이 부서지는 사고**를 재현해 봅니다.

> **실습 —** 이 챕터의 humanization 수치는 `sapiens` 1.1.0을 실제 설치·실행해 뽑았습니다. 입력은 [Ch.04](../04_sequence_qc/04_sequence_qc.md)의 parental VH/VL입니다.

---

## 5.1 설치 — 또 하나의 함정

```bash
# 함정: BioPhi는 PyPI에 없습니다. bioconda에 있습니다.
#   pip install biophi  →  "No matching distribution found" (실제로 겪음)
conda activate abhuman
conda install -c bioconda biophi          # BioPhi 전체(웹/CLI 포함)

# humanization 엔진만 빠르게 쓰려면 Sapiens는 PyPI에 따로 있습니다:
python -m pip install sapiens             # 실제로 이게 가장 빨랐습니다
```

> **케이스 스터디 — 우리가 실제로 겪은 설치 실패**
> 초안에는 `pip install biophi`로 적혀 있었는데, 실제로 돌려보니 이렇게 죽었습니다.
> ```
> ERROR: Could not find a version that satisfies the requirement biophi (from versions: none)
> ERROR: No matching distribution found for biophi
> ```
> 확인해보니 BioPhi는 **bioconda 전용(v1.0.11)**이고, PyPI에는 없었습니다. 반면 humanization 엔진인 **Sapiens는 PyPI에 `sapiens`(v1.1.0)로 따로** 올라와 있었습니다. 그래서 "후보 서열만 빨리 뽑고 싶다"면 `pip install sapiens`가 제일 빠른 길입니다. 모델 가중치는 첫 실행 때 HuggingFace Hub에서 자동으로 받아옵니다.

---

## 5.2 Sapiens로 실제 humanization 돌리기

Sapiens 1.1.0의 핵심 함수는 `predict_scores`입니다 — 각 position마다 20개 아미노산에 대한 **사람 모델의 확률 분포**를 돌려줍니다. 여기서 position별로 가장 확률 높은 사람 잔기를 고르면, 그게 곧 Sapiens-humanized 서열입니다.

```python
import sapiens

vh = "QVQLQQSGPELVKPGASVKMSCKASGYTFTDYVINWGKQRSGQGLEWIGEIYPGSGTNYYNEKFKAKATLTADKSSNIAYMQLSSLTSEDSAVYFCARRGRYGLYAMDYWGQGTSVTVSS"

# 위치별 사람 아미노산 확률 (DataFrame: rows=position, cols=20 AA)
df = sapiens.predict_scores(vh, "H")

# Sapiens-humanized = 각 위치에서 가장 사람다운 잔기
humanized_vh = "".join(df.columns[df.values.argmax(axis=1)])
```

---

## 5.3 결과 해석 — 실제 출력으로

위 코드를 [Ch.04](../04_sequence_qc/04_sequence_qc.md)의 parental 서열에 그대로 돌린 **실측 결과**입니다.

**Heavy chain (VH)** — 120 residue 중 **21개 mutation** (parental 대비 약 82.5% identity)

```
PARENTAL : QVQLQQSGPELVKPGASVKMSCKASGYTFTDYVINWGKQRSGQGLEWIGEIYPGSGTNYYNEKFKAKATLTADKSSNIAYMQLSSLTSEDSAVYFCARRGRYGLYAMDYWGQGTSVTVSS
SAPIENS  : QVQLVQSGPELKKPGASVKVSCKASGYTFTDYVINWVRQAPGQGLEWIGWINPGSGTTYYAEKFKGRVTLTADKSTNTAYMELSSLTSEDTAVYFCARRGRYGDYAMDVWGQGTLVTVSS
muts     : Q5V, V12K, M20V, G37V, K38R, R40A, S41P, E50W, Y52N, N58T, N61A, A66G, K67R, A68V, S76T, I78T, Q82E, S91T, L104D, Y109V, S115L
```

대부분 framework 자리(`R40A`, `A66G`, `K67R` 등)에 들어간 전형적인 murine→human 치환입니다. 좋은 신호입니다.

**Light chain (VL)** — **17개 mutation**

```
PARENTAL : QSALTQPPSASGSPGQSVTISCTGTSSDVGHKFPVSWYQQYPGKAPKLLIYKNLLRPSGVPDRFSGSKSGTSASLAITGLQAEDGADYYCQSYDSSLRVVFGGGTKTVVLG
SAPIENS  : ...muts: H31A, K32Y, F33N, P34D, K52G, L54S, L55N, ...
```

> **주의 — 흔한 함정이 실제로 터졌습니다!** 경쇄 mutation을 보면 **H31, K32, F33, P34** 자리가 보이죠? [Ch.04](../04_sequence_qc/04_sequence_qc.md)에서 뽑은 light CDR1이 `SSDVGHKFP`였는데, **이 자리들이 바로 CDR1 안**입니다. 즉 가드 없이 argmax humanization을 돌리면 모델이 **CDR-L1까지 사람 잔기로 바꿔버립니다.** 이건 결합력을 깰 수 있는 위험한 mutation입니다.
>
> **그래서 실무에서는** ① ANARCI로 뽑은 CDR 좌표를 mask에서 제외하거나, ② BioPhi의 humanization 모드처럼 **CDR을 자동 보호**하도록 설정하거나, ③ 후처리로 CDR 내 mutation을 전부 parental로 되돌립니다. "도구가 준 서열을 그대로 쓰지 않는다"는 [Ch.02](../02_nomenclature_strategy/02_nomenclature_strategy.md)의 원칙이 바로 이래서 중요합니다.

---

## 5.4 humanness가 정말 좋아졌나요? — 실측

humanization을 했으면 "사람다움"이 실제로 올라갔는지 숫자로 봐야 합니다. 사람 Sapiens 모델이 각 잔기에 부여하는 확률의 평균(높을수록 사람답다)으로 parental과 humanized를 비교한 **실측값**입니다.

| 체인 | parental mean human-prob | humanized mean human-prob | 변화 |
|---|---:|---:|---|
| VH | 0.694 | **0.815** | ▲ +0.121 |
| VL | 0.770 | **0.872** | ▲ +0.102 |

이야기가 깔끔하게 맞아떨어집니다. **VL은 출발점(0.770)이 이미 높았습니다** — [Ch.04](../04_sequence_qc/04_sequence_qc.md)에서 light germline identity가 81%로 높았던 것과 정확히 일치합니다. 반대로 **VH는 출발점이 낮았다가(0.694) 크게 개선**됐습니다. ANARCI germline 분석과 Sapiens humanness가 같은 결론을 가리키는 것입니다.

> **그래프 —** `humanization_viz.humanness_bars(rows, title, outpath)` 로 parental vs humanized를 체인별 바 차트로 그릴 수 있습니다(공용 모듈 → `humanization_viz.py`).

> **심화 — OASis humanness란?** BioPhi의 OASis는 서열을 9-mer 펩타이드로 쪼개, 각 펩타이드가 OAS(Observed Antibody Space)의 실제 사람 항체에서 얼마나 자주 관찰되는지로 humanness를 매깁니다(`biophi oasis ...`). 위 mean human-prob는 그걸 단순화한 대용 지표입니다. OASis는 OAS DB 다운로드가 필요해서 본 표는 Sapiens 모델 확률로 계산했습니다.

---

## 이 챕터 핵심 요약

1. BioPhi는 **bioconda**, Sapiens는 **PyPI(`sapiens`)** — `pip install biophi`는 실패합니다.
2. Sapiens humanization = `predict_scores`의 **position별 argmax**.
3. 실측: VH 21 mutation·VL 17 mutation, humanness VH 0.694→0.815 / VL 0.770→0.872.
4. **가드 없이 돌리면 CDR까지 바뀝니다(실제로 CDR-L1이 바뀜)** — CDR 보호는 필수.

---

다음 → **[06. CDR-safe 도구: Humatch · AnthroAb](../06_cdr_safe_tools/06_cdr_safe_tools.md)**
