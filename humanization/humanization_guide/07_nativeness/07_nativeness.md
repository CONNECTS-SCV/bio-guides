---
title: "Ch.07 — Nativeness: AbNatiV · Ab-RoBERTa"
chapter: 7
language: ko
part: B
---

# Ch.07 — Nativeness: AbNatiV · Ab-RoBERTa

사람답기만 하면 끝일까요? 후보 서열이 사람 잔기로 가득 차 있다고 해서, 그게 **자연계에 실제로 존재할 법한 항체**인 건 아니에요. 사람 잔기를 여기저기서 짜깁기하면 각 자리는 사람다운데 전체 조합은 어색한 **프랑켄슈타인 서열**이 나와요.

이 챕터에서는 축을 두 개 더 세워요. **nativeness**(AbNatiV)는 후보가 자연 사람 레퍼토리에 얼마나 그럴듯하게 들어맞는지를 보고, **naturalness**(Ab-RoBERTa pseudo-likelihood)는 항체 언어모델이 그 서열을 얼마나 자연스럽다고 여기는지를 봐요. 그리고 humanness·nativeness·naturalness 셋이 **서로 어긋나는 순간**을 실측으로 직접 보게 돼요.

> **실습 — `07_nativeness_lab.ipynb`** · ① 직접 실행 → ② 내 결과 확인 → ③ 레퍼런스 대조 · **전 셀 96초**
>
> Ab-RoBERTa pseudo-likelihood를 직접 계산해 변이체를 줄 세우고, nativeness와 humanness가 어떻게 다른지 봐요. 이 챕터의 수치는 AbNatiV 2.0.8과 `mogam-ai/Ab-RoBERTa`를 실제로 돌려 얻은 값이에요.

---

## 7.1 AbNatiV — 자연 레퍼토리에 얼마나 들어맞나

AbNatiV는 자연 항체 레퍼토리로 학습한 VQ-VAE 모델이에요. 후보 서열을 넣으면 **0~1 사이 nativeness score**를 주고, 높을수록 자연 사람 항체에 가까워요. humanness가 "사람 잔기를 얼마나 썼나"라면, nativeness는 "그 조합이 실제 항체로서 얼마나 자연스러운가"예요. 그래서 humanness는 높은데 nativeness가 낮으면 프랑켄슈타인을 의심해요.

### 7.1.1 설치 — 두 가지 함정을 먼저 넘어요

설치는 한 줄인데, 그대로 돌리면 두 번 막혀요. 함정을 미리 넘고 가요.

```bash
conda create -n abnativ -c conda-forge python=3.10 -y
conda activate abnativ
python -m pip install abnativ                 # abnativ 2.0.8 설치됨 (ImmuneBuilder도 함께 딸려옴)

# (함정 1) 모델 가중치를 먼저 받아야 해요. 안 받으면 score에서 FileNotFoundError가 나요.
abnativ init                                  # VQ-VAE 체크포인트 다운로드 (각 ~1GB, 시간 걸림)

# (함정 2) score -align 은 내부적으로 anarci를 import해요. 같은 env에 깔아주세요.
conda install -c bioconda -c conda-forge anarci hmmer -y
```

첫 번째 함정부터 볼게요. `pip install abnativ` 직후 바로 `abnativ score`를 돌리면 `FileNotFoundError: .../pretrained_models/vh_model.ckpt`가 나요. AbNatiV는 모델 가중치를 패키지에 포함하지 않고 **`abnativ init`으로 따로 받게** 되어 있거든요. VQ-VAE 체크포인트가 **모델당 약 1GB**라 다운로드가 꽤 길어요.

두 번째 함정은 init을 받은 뒤에 나와요. `-align` 옵션이 ANARCI numbering을 쓰기 때문에, **Humatch에서 겪은 것과 똑같은 `import anarci` 에러**가 나요. 같은 env에 ANARCI를 깔면 풀려요.

### 7.1.2 사용 예시

입력은 단일 서열 문자열이나 FASTA예요. `-nat`으로 모델을 고르는데, 여기서 **어떤 모델을 고르느냐가 점수의 스케일을 좌우해요**(7.1.3의 함정으로 이어져요).

```bash
# -nat 으로 모델 선택(VH / VKappa / VLambda / VHH)
abnativ score -nat VH -i "$PARENTAL_VH" -odir abn -oid par_vh -align -mean
abnativ score -nat VH -i "$HUMANIZED_VH" -odir abn -oid hum_vh -align -mean
# 결과: abn/{oid}_abnativ_seq_scores.csv  (서열당 nativeness score)
```

`-align`은 ANARCI로 번호를 매겨 FR·CDR 구간을 나눠 주고, `-mean`은 잔기별 점수를 평균해 서열 하나당 한 값으로 접어 줘요. 그래서 전체 score뿐 아니라 **FR score와 CDR score를 따로** 볼 수 있어요. 이 분해가 다음 절의 핵심이에요.

### 7.1.3 실측 — parental vs humanized nativeness

[Ch.04](../04_sequence_qc/04_sequence_qc.md)의 parental과 [Ch.05](../05_humanize_sapiens/05_humanize_sapiens.md)의 Sapiens-humanized VH, 그리고 lambda 경쇄에 AbNatiV를 돌린 **실측 결과**예요. 이 표는 **AbNatiV1**(`-nat VH` / `-nat VLambda`) 기준이에요.

| 서열 | AbNatiV1 전체 score | FR score | CDR-H3 score |
|---|---:|---:|---:|
| VH parental | **0.648** | 0.632 | 0.614 |
| VH humanized (Sapiens) | **0.880** | 0.925 | 0.626 |
| VL (lambda) parental | **0.902** | 0.940 | 0.999 |

![AbNatiV1 VH nativeness](07_nativeness.png)

*네 후보의 AbNatiV1 VH nativeness를 overall / FR / CDR-H3로 분해한 실측 막대예요. `abnativ score -nat VH ... -align -mean`의 출력을 `07_nativeness_lab.ipynb`에서 그린 것이고, 표의 parental(0.648)·sapiens(0.880) 열이 왼쪽 두 그룹이에요. 초록(FR) 막대만 크게 솟고 분홍(CDR) 막대는 제자리인 패턴이 한눈에 보여요.*

숫자를 읽어 볼게요. VH parental의 nativeness는 **0.648**로 낮아요. 그리고 이건 앞 챕터들과 정확히 맞물려요 — ANARCI/IgBLAST germline identity가 **63%**로 낮았고(Ch.04), Sapiens humanness도 **0.694**로 낮았죠(Ch.05). humanization 후 nativeness는 **0.880**으로 크게 오르는데, 그 상승분 **+0.232**는 거의 전부 framework에서 나와요(FR 0.632 → **0.925**).

반면 람다 경쇄는 parental이 이미 **0.902**예요. 손댈 여지가 적다는 뜻이고, 이 역시 light germline identity **81%**·humanness **0.770**과 일치해요. germline identity·humanness·nativeness는 서로 독립적인 세 축인데, 셋 모두 **"heavy는 손볼 게 많고 light는 이미 사람답다"**는 같은 결론을 가리켜요.

흥미로운 건 CDR-H3예요. humanized VH의 CDR-H3 score(**0.626**)는 parental(**0.614**)과 사실상 같아요. Sapiens가 CDR-H3를 건드리지 않았으니 당연한 결과인데(Ch.05), 덕분에 **"framework만 사람화하고 CDR은 보존한다"**는 humanization 원칙이 점수 프로파일에도 그대로 찍혀 나와요. 그림에서 FR 막대만 솟고 CDR 막대가 평평한 게 바로 그거예요.

> **주의 — AbNatiV는 세대를 구분해 적어요.** 위 표는 **AbNatiV1**(`-nat VH` / `-nat VLambda`), 7.2.3의 표는 **AbNatiV2**(`-nat VH2` / `-nat VL2`) 기준이에요. 같은 후보인데 숫자가 달라 보이는 건 **모델 세대가 다르기 때문**이지 오류가 아니에요. 세대를 섞어서 비교하지 마세요.

---

<!-- 근거: Antibody_humanization_project/scripts/score_abroberta_pseudolikelihood.py (MODEL_ID=mogam-ai/Ab-RoBERTa, masked pseudo-LL), results/abroberta_pseudolikelihood.tsv, results/INDEPENDENT_HUMANNESS_METRICS_COMPARISON.md -->

## 7.2 naturalness 평가 — Ab-RoBERTa pseudo-likelihood (AbNatiV 보완)

AbNatiV가 "사람 레퍼토리에 들어맞나"를 본다면, 한 축 더 세울 수 있어요. **항체 서열 자체의 자연스러움(naturalness)** 을 독립 언어모델로 점검하는 거예요. mutation 후보를 검증할 때 AbNatiV와 **나란히** 보는 직교(orthogonal) 지표예요. 이 절의 수치는 `Antibody_humanization_project/` 실측 결과예요.

### 7.2.1 무엇으로 재나 — Ab-RoBERTa pseudo-log-likelihood

항체 전용 언어모델 `mogam-ai/Ab-RoBERTa`로 각 position을 차례로 `<mask>`로 가리고, **그 자리에 있던 진짜 잔기의 로그확률**을 받아 모아 평균해요. 이게 masked pseudo-log-likelihood예요. 핵심 지표는 네 가지예요.

- `mean_log_prob` — **높을수록** 자연스러움(좋음)
- `perplexity = exp(-mean_log_prob)` — **낮을수록** 좋음
- `top1_fraction` / `top5_fraction` — 모델 1·5순위 안에 실제 잔기가 든 비율
- `paired` — VH·VL **길이가중 평균**

모델은 첫 실행 때 HF에서 자동으로 내려받아요.

```bash
# 후보 FASTA(헤더 {name}_VH / {name}_VL)를 점수화
python scripts/score_abroberta_pseudolikelihood.py \
  --fasta candidates.fasta --output abroberta_pseudolikelihood.tsv
```

### 7.2.2 실측 — paired length-weighted

`results/abroberta_pseudolikelihood.tsv` 기준이에요.

| 후보 | paired mean log prob ↑ | perplexity ↓ |
|---|---:|---:|
| BioPhi/Sapiens | **-0.4973** | **1.6444** |
| AnthroAb (best-score) | -0.5285 | 1.6965 |
| parental | -0.7240 | 2.0627 |
| Humatch | -0.7717 | 2.1635 |
| AnthroAb (FR-masked) | -1.4223 | 4.1467 |

이 표는 **재실행으로 값이 바뀐 곳**이라 짚고 갈게요. 이전 판에는 Sapiens가 **-0.6928**, AnthroAb가 **-0.8733**으로 적혀 있었어요. 그런데 같은 방식으로 다시 계산하니 위 값이 나왔어요. parental(**-0.7240**)과 Humatch(**-0.7717**)는 이전 값과 정확히 일치했고, **Sapiens·AnthroAb 두 값만 재현되지 않았어요.** 그래서 표를 실측값으로 교체했고, 순위도 이에 따라 바뀌어요 — Sapiens가 여전히 1위지만 AnthroAb best-score가 parental보다 위로 올라와요.

![Ab-RoBERTa naturalness](07_naturalness.png)

*parental과 Sapiens humanized를 VH·VL·paired로 나눠 본 Ab-RoBERTa 실측이에요. 세로축은 `perplexity`의 역수에 해당하는 per-residue pseudo-likelihood, 즉 `exp(mean_log_prob)`이라 **높을수록 자연스러움**이에요. 값은 `results/abroberta_pseudolikelihood.tsv`에서 왔어요. 보라색(humanized) 막대가 VL과 paired에서는 올라가는데, **VH에서만 오히려 내려간다**는 게 이 그림의 요점이에요.*

그림의 VH 막대가 이 절에서 가장 중요한 사실이에요. humanization이 VH의 naturalness를 **떨어뜨렸어요**. VH만 떼어 놓고 보면 **parental VH가 -0.5188로 가장 자연스러워요.** AbNatiV도 Humatch도 모두 humanized VH가 더 사람답다고 하는데도 그래요. 사람다움을 올리는 편집이 자연스러움을 깎을 수 있다는 뜻이에요.

> **주의 — naturalness는 humanness가 아니에요.** Ab-RoBERTa는 사람다움(human-specific)이 아니라 **자연스러움**을 재요. 그래서 "가장 사람다운 것"과 "가장 자연스러운 것"이 어긋나요. Ab-RoBERTa를 **주 humanness 점수로 쓰면 안 돼요.** 보조 축으로만 쓰세요.

### 7.2.3 다른 축과 나란히 보기

세 축을 한 표에 놓아요. **AbNatiV 열은 AbNatiV2**(`-nat VH2` / `-nat VL2`) 기준이에요.

| 후보 | AbNatiV2 VH | AbNatiV2 VL | Humatch CNN (H/L) | Ab-RoBERTa paired |
|---|---:|---:|---:|---:|
| parental | 0.4927 | 0.6958 | — | -0.7240 |
| BioPhi/Sapiens | **0.7777** | **0.9525** | — | **-0.4973** |
| Humatch | 0.6925 | 0.7898 | 0.972 / 1.000 | -0.7717 |
| AnthroAb (best-score) | 0.7189 | 0.9195 | — | -0.5285 |

여기도 정정한 값이 있어요. 이전 판은 Sapiens 인간화 VH의 AbNatiV2를 **0.6900**으로 적었는데, 실제로 돌리면 **0.7777**이에요. 0.6900은 **어떤 후보에서도 나오지 않았어요** — Humatch가 **0.6925**로 가장 가까울 뿐이에요. parental **0.4927**은 정확히 일치했고요.

OASis 열은 뺐어요. OASis 백분위는 OAS 9-mer 데이터베이스(수십 GB)가 있어야 계산되는데, 이 과정의 실습 환경에서는 그 DB를 구할 수 없어요. 재현할 수 없는 값을 표에 남겨 두는 대신 **humanness 축은 Sapiens 확률(Ch.05)로** 봐요.

마지막은 역할 분담이에요. 주 human-likeness 패널은 **Humatch CNN + AbNatiV2**로 잡고(OASis를 쓸 수 있는 환경이면 여기에 더해요), **Ab-RoBERTa pseudo-likelihood는 naturalness 이상치(outlier) 탐지용 보조 지표**로 써요. 사람 잔기는 많은데(humanness↑) 서열이 부자연스러운(naturalness↓) 후보를 한 번 더 걸러내는 안전장치예요.

---

## 이 챕터 핵심 요약

1. **AbNatiV**는 `abnativ init`(체크포인트 모델당 약 1GB)과 `anarci`가 선행 조건이에요. 이 둘을 안 넘으면 `abnativ score`가 안 돌아가요.
2. 실측(AbNatiV1): VH nativeness **0.648 → 0.880**(FR 0.632 → 0.925), CDR-H3는 0.614 → 0.626으로 거의 불변이에요. "framework만 사람화" 원칙이 점수에 그대로 보여요. VL(lambda)은 parental이 이미 0.902예요.
3. **AbNatiV1과 AbNatiV2는 세대가 달라요.** 값의 스케일이 다르니 표기를 구분하고, 섞어 비교하지 마세요.
4. **humanness · nativeness · naturalness는 서로 다른 축이에요.** Ab-RoBERTa로 보면 **parental VH가 -0.5188로 가장 자연스러워요** — 사람다움과 자연스러움은 일치하지 않아요.
5. 그래서 주 패널은 Humatch CNN + AbNatiV2로 잡고, Ab-RoBERTa는 **이상치 탐지 보조**로 써요.

---

다음 → **[08. 구조 검증](../08_structure/08_structure.md)**
