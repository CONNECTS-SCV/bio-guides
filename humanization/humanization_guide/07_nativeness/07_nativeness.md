---
title: "Ch.07 — Nativeness: AbNatiV · Ab-RoBERTa"
chapter: 7
language: ko
part: B
---

# Ch.07 — Nativeness: AbNatiV · Ab-RoBERTa

여기서 미묘하지만 중요한 질문 하나. 후보 서열이 "사람 잔기로 가득 차 있다"고 해서, 그게 **자연계에 실제로 존재할 법한 항체**일까요? 꼭 그렇진 않습니다. 사람 잔기들을 짜깁기하다 보면, 각 자리는 사람다운데 전체 조합은 부자연스러운 "프랑켄슈타인 서열"이 나올 수 있기 때문입니다.

AbNatiV는 바로 그걸 잡습니다. 후보가 **자연 사람 항체(또는 나노바디) 레퍼토리에 얼마나 그럴듯하게 들어맞는지**를 nativeness score로 매깁니다. 그리고 §7.2에서는 한 축 더 — **naturalness**(Ab-RoBERTa pseudo-likelihood)를 봅니다. 셋(humanness·nativeness·naturalness)은 **서로 다른 것**을 재고, 실제로 서로 어긋나는 순간이 나옵니다.

> **실습 — `07_nativeness_lab.ipynb`** · ① 직접 실행 → ② 내 결과 확인 → ③ 레퍼런스 대조 · **전 셀 96초**
>
> Ab-RoBERTa pseudo-likelihood 를 직접 계산해 변이체를 줄 세우고, nativeness 와 humanness 가 어떻게 다른지 봅니다.

> **실습 —** 이 챕터의 수치는 AbNatiV 2.0.8과 `mogam-ai/Ab-RoBERTa`를 실제로 돌려 얻은 값입니다.

---

## 7.1 AbNatiV — 사람답기만 하면 끝일까요?

### 7.1.1 설치 — 두 가지 함정을 먼저 넘습니다

```bash
conda create -n abnativ -c conda-forge python=3.10 -y
conda activate abnativ
python -m pip install abnativ                 # abnativ 2.0.8 설치됨 (ImmuneBuilder도 함께 딸려옴)

# (함정 1) 모델 가중치를 먼저 받아야 합니다. 안 받으면 score에서 FileNotFoundError가 납니다.
abnativ init                                  # VQ-VAE 체크포인트 다운로드 (각 ~1GB, 시간 걸림)

# (함정 2) score -align 은 내부적으로 anarci를 import합니다. 같은 env에 깔아주십시오.
conda install -c bioconda -c conda-forge anarci hmmer -y
```

> **케이스 스터디 — AbNatiV를 돌리기까지 넘은 두 함정.**
> ① `pip install abnativ` 직후 바로 `abnativ score`를 돌리면 `FileNotFoundError: .../pretrained_models/vh_model.ckpt`가 납니다. AbNatiV는 모델 가중치를 패키지에 포함하지 않고 **`abnativ init`으로 따로 받게** 되어 있습니다(VQ-VAE 체크포인트가 **모델당 약 1GB**라 다운로드가 꽤 깁니다). ② init을 받아도 `-align` 옵션은 ANARCI numbering을 쓰기 때문에, **Humatch와 똑같이 `import anarci` 에러**가 납니다. 같은 env에 ANARCI를 깔면 해결됩니다.

### 7.1.2 사용 예시

```bash
# 입력은 단일 서열 문자열 또는 FASTA. -nat 으로 모델 선택(VH / VKappa / VLambda / VHH)
abnativ score -nat VH -i "$PARENTAL_VH" -odir abn -oid par_vh -align -mean
abnativ score -nat VH -i "$HUMANIZED_VH" -odir abn -oid hum_vh -align -mean
# 결과: abn/{oid}_abnativ_seq_scores.csv  (서열당 nativeness score)
```

각 후보 VH/VL에 AbNatiV score를 계산하고, parental 대비 개선폭과 후보 간 순위를 정리합니다. humanness(OASis)와 nativeness(AbNatiV)는 **서로 보완**하는 지표입니다 — humanness만 높고 nativeness가 낮으면, 위에서 말한 프랑켄슈타인을 의심합니다.

### 7.1.3 실측 — parental vs humanized nativeness

[Ch.04](../04_sequence_qc/04_sequence_qc.md)의 parental과 [Ch.05](../05_humanize_sapiens/05_humanize_sapiens.md)의 Sapiens-humanized VH, 그리고 lambda 경쇄에 AbNatiV를 돌린 **실측 결과**입니다.

| 서열 | AbNatiV 전체 score | FR score | CDR-H3 score | 해석 |
|---|---:|---:|---:|---|
| VH parental | **0.648** | 0.632 | 0.614 | 비인간 — nativeness 낮음 |
| VH humanized (Sapiens) | **0.880** | 0.925 | 0.626 | ▲ **+0.232** 크게 개선, framework가 자연스러워짐 |
| VL (lambda) parental | **0.902** | 0.940 | 0.999 | 이미 매우 native — 손댈 여지 적음 |

> **핵심 — 네 도구가 같은 이야기를 합니다.** VH parental의 nativeness가 0.648로 낮은데, 이는 ANARCI/IgBLAST germline identity가 63%로 낮고(Ch.04) Sapiens humanness도 0.694로 낮았던 것(Ch.05)과 정확히 맞물립니다. humanization 후 nativeness가 **0.880으로 크게 오르고(framework score 0.632→0.925)**, 동시에 람다 경쇄는 parental에서 이미 0.902로 native합니다 — 이 역시 light germline identity 81%·humanness 0.770과 일치합니다. **germline identity·humanness·nativeness라는 독립적인 세 축의 지표가 모두 "heavy는 손볼 게 많고 light는 이미 사람답다"는 같은 결론**을 가리키는 것입니다.
>
> 흥미로운 점 하나 — humanized VH의 CDR-H3 score(0.626)는 parental(0.614)과 거의 같습니다. Sapiens가 CDR-H3를 건드리지 않았으니(Ch.05) 당연한 결과이고, "framework만 사람화하고 CDR은 보존한다"는 humanization 원칙이 nativeness 프로파일에서도 그대로 보입니다.

> **그래프 —** `humanization_viz.nativeness_panel(rows, title, outpath)` 로 FR/CDR 분해를 나란히 그리면, "framework만 올라가고 CDR은 그대로"인 패턴이 시각적으로 드러납니다.

> **심화 —** AbNatiV score는 0~1 범위로, 높을수록 자연 사람 레퍼토리에 가깝습니다. humanness(Sapiens/OASis)가 "사람 잔기를 얼마나 썼나"라면, nativeness는 "그 조합이 실제 사람 항체로서 얼마나 자연스러운가"를 봅니다. 둘을 함께 보면, 사람 잔기는 많지만(humanness↑) 조합이 어색한(nativeness↓) 프랑켄슈타인 후보를 걸러낼 수 있습니다.

---

<!-- 근거: Antibody_humanization_project/scripts/score_abroberta_pseudolikelihood.py (MODEL_ID=mogam-ai/Ab-RoBERTa, masked pseudo-LL), results/abroberta_pseudolikelihood.tsv, results/INDEPENDENT_HUMANNESS_METRICS_COMPARISON.md -->

## 7.2 naturalness 평가 — Ab-RoBERTa pseudo-likelihood (AbNatiV 보완)

AbNatiV가 "사람 레퍼토리 nativeness"를 본다면, 한 축 더 — **항체 서열의 자연스러움(naturalness)** 을 독립 언어모델로 점검할 수 있습니다. mutation 예측 후보를 검증할 때 AbNatiV와 **나란히** 보는 직교(orthogonal) 지표입니다. (이 절의 수치는 `Antibody_humanization_project/` 실측 결과입니다.)

### 7.2.1 무엇으로 재나 — Ab-RoBERTa pseudo-log-likelihood

항체 전용 언어모델 `mogam-ai/Ab-RoBERTa`로 각 position을 차례로 마스킹해 **실제 잔기의 로그확률**을 모아 평균합니다(masked pseudo-LL). 핵심 지표:

- `mean_log_prob` — **높을수록** 자연스러움(좋음)
- `perplexity = exp(-mean_log_prob)` — **낮을수록** 좋음
- `top1_fraction` / `top5_fraction` — 모델 1·5순위 안에 실제 잔기가 든 비율
- `paired` = VH·VL **길이가중 평균**

```bash
# 후보 FASTA(헤더 {name}_VH / {name}_VL)를 점수화. 모델은 첫 실행 시 HF에서 자동 다운로드
python scripts/score_abroberta_pseudolikelihood.py \
  --fasta candidates.fasta --output abroberta_pseudolikelihood.tsv
```

### 7.2.2 실측 — paired length-weighted

`results/abroberta_pseudolikelihood.tsv` 기준입니다.

| 후보 | paired mean log prob ↑ | perplexity ↓ |
|---|---:|---:|
| BioPhi/Sapiens | **-0.4973** | **1.6444** |
| AnthroAb (best-score) | -0.5285 | 1.6965 |
| parental | -0.7240 | 2.0627 |
| Humatch | -0.7717 | 2.1635 |
| AnthroAb (FR-masked) | -1.4223 | 4.1467 |

> **주의 — 이 표는 재실행으로 값이 바뀐 곳입니다.** 이전 판에는 Sapiens −0.6928, AnthroAb −0.8733으로 적혀 있었지만, 같은 방식(각 위치를 `<mask>`로 가려 진짜 잔기의 log P를 구하고 VH+VL 길이가중 평균)으로 다시 계산하니 위 값이 나왔습니다. parental(−0.7240)과 Humatch(−0.7717)는 이전 값과 정확히 일치했고, **Sapiens·AnthroAb 두 값만 재현되지 않았습니다.** 표는 실측값으로 교체했습니다. 순위도 이에 따라 바뀝니다(Sapiens가 여전히 1위이지만, AnthroAb best-score가 parental보다 위로 올라옵니다).

> **주의 — naturalness ≠ humanness.** Ab-RoBERTa는 사람다움(human-specific)이 아니라 **자연스러움** 점수입니다. 실제로 VH만 보면 **parental VH가 -0.5188로 가장 높습니다** — OASis·AbNatiV·Humatch는 모두 humanized VH가 더 사람답다고 하는데도요. "가장 사람다운 것"이 "가장 자연스러운 것"과 일치하지 않는다는 뜻이라, Ab-RoBERTa를 **주 humanness 점수로 쓰면 안 됩니다.**

### 7.2.3 다른 축과 나란히 보기

실측 패널입니다. **AbNatiV 열은 AbNatiV2(`-nat VH2`/`-nat VL2`) 기준**이에요 — 앞 절(7.1)의 표는 AbNatiV1(`-nat VH`/`-nat VLambda`)이라 값의 스케일이 다릅니다. 같은 후보인데 숫자가 달라 보이는 건 **모델 세대가 다르기 때문**이지, 오류가 아닙니다.

| 후보 | AbNatiV2 VH | AbNatiV2 VL | Humatch CNN (H/L) | Ab-RoBERTa paired |
|---|---:|---:|---:|---:|
| parental | 0.4927 | 0.6958 | — | -0.7240 |
| BioPhi/Sapiens | **0.7777** | **0.9525** | — | **-0.4973** |
| Humatch | 0.6925 | 0.7898 | 0.972 / 1.000 | -0.7717 |
| AnthroAb (best-score) | 0.7189 | 0.9195 | — | -0.5285 |

> **OASis 열은 뺐습니다.** OASis 백분위는 OAS 9-mer 데이터베이스(수십 GB)가 있어야 계산되는데, 이 과정의 실습 환경에서는 그 DB를 받지 않습니다. 재현할 수 없는 값을 표에 남겨 두는 대신, humanness 축은 Sapiens 확률(Ch.05)로 봅니다.
>
> **AbNatiV2 humanized 값도 바뀌었습니다.** 이전 판은 Sapiens 인간화 VH를 0.6900으로 적었지만, 실제로 돌리면 **0.7777**입니다(0.6900은 어떤 후보에서도 나오지 않았어요 — Humatch가 0.6925로 가장 가까울 뿐입니다). parental 0.4927은 정확히 일치했습니다.

> **권장 — 역할 분담.** 주 human-likeness 패널은 **OASis + Humatch CNN + AbNatiV2**로 잡고, **Ab-RoBERTa pseudo-likelihood는 naturalness 이상치(outlier) 탐지용 보조 지표**로 씁니다. 사람 잔기는 많지만(humanness↑) 서열이 부자연스러운(naturalness↓) 후보를 한 번 더 걸러내는 안전장치입니다.

---

## 이 챕터 핵심 요약

1. **AbNatiV**는 `abnativ init`(체크포인트 모델당 약 1GB)과 `anarci`가 선행 조건입니다.
2. 실측: VH nativeness **0.648 → 0.880**(FR 0.632→0.925), CDR-H3는 0.614→0.626으로 거의 불변 — "framework만 사람화" 원칙이 점수에 그대로 보입니다. VL(lambda)은 parental이 이미 0.902.
3. **humanness · nativeness · naturalness는 서로 다른 축**입니다. Ab-RoBERTa로 보면 **parental VH가 가장 자연스럽습니다(-0.5188)** — 사람다움과 자연스러움은 일치하지 않습니다.
4. 그래서 주 패널은 OASis+Humatch CNN+AbNatiV2, Ab-RoBERTa는 **이상치 탐지 보조**로 씁니다.

---

다음 → **[08. 구조 검증](../08_structure/08_structure.md)**
