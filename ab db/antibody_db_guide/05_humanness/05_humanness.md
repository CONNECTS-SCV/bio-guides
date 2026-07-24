---
title: "Ch.05 — humanness & humanization (BioPhi/Sapiens)"
chapter: 5
level: hands-on
language: ko
part: B
---

# Ch.05 — humanness & humanization (BioPhi/Sapiens)

Ch.04에서 우리 demo 항체의 중쇄가 **마우스 germline(IGHV14-4)**이라는 것을 확인했습니다. 마우스 항체를 사람에게 투여하면 면역원성(anti-drug antibody) 위험이 큽니다. 그래서 **humanization**(결합은 유지하면서 사람 항체에 가깝게 서열을 고치는 작업)이 필요합니다. 이 챕터에서 **BioPhi의 Sapiens** 언어모델을 직접 돌려 humanness를 점수화하고 실제로 humanize해봅니다.[6]

> **실습 — [`05_humanness_lab.ipynb`](05_humanness_lab.ipynb)** · **전 셀 실행 16초** — Sapiens를 **직접 실행**해 점수 행렬·humanized 서열을 `my_run/` 에 만들고, **bioconda BioPhi CLI로 만든 레퍼런스와 대조**합니다(같으면 재현 성공).

---

## 5.1 humanness란 — 그리고 Colab에서 BioPhi를 쓰는 법

humanness는 항체 서열이 **자연 human antibody repertoire와 얼마나 닮았는지**를 나타냅니다. BioPhi는 두 도구를 묶어 제공합니다.

- **Sapiens**: 항체 언어모델. 각 위치에서 "사람 항체라면 어떤 아미노산일까"를 확률로 줍니다 → humanization·humanness 점수.
- **OASis**: OAS 9-mer 사전 기반 humanness 평가(별도 DB 필요, 용량 큼).

이번엔 Sapiens로 진행합니다(OASis는 DB 다운로드가 커서 Ch.09 OAS와 연계해 설명).

원래 명령은 다음과 같습니다.

```bash
biophi sapiens data/demo_mab.fa --scores-only --output data/demo_sapiens_scores.csv   # 점수 행렬
biophi sapiens data/demo_mab.fa --fasta-only  --output data/demo_humanized.fa          # humanized 서열
```

**그런데 BioPhi CLI는 bioconda 전용이라 Colab(pip)에서는 쓸 수 없습니다.** 여기서 막히지 않는 방법이 있습니다. **BioPhi가 내부에서 쓰는 부품 두 개가 모두 pip에 있기 때문입니다.**

| 부품 | 역할 | 설치 |
|------|------|------|
| `sapiens` | 위치별 아미노산 확률(언어모델) | `pip install sapiens` |
| `abnumber` | numbering·CDR 정의·**CDR grafting** | `pip install abnumber` (+ hmmer) |

BioPhi의 Sapiens humanization 알고리즘은 딱 세 줄입니다(원본 `sapiens_humanize_chain` 그대로).

```python
pred = sapiens.predict_scores(chain.seq, chain.chain_type)   # ① 위치별 확률 행렬
best = "".join(pred.idxmax(axis=1).values)                    # ② 각 위치 최대확률 아미노산
humanized = parental.graft_cdrs_onto(parental.clone(best))    # ③ 원본 CDR 재이식 (결합부위 보존)
```

이것을 담은 것이 [`scripts/sapiens_humanize.py`](../scripts/sapiens_humanize.py)이고, 노트북이 이 스크립트를 돌립니다.

```bash
python scripts/sapiens_humanize.py data/demo_mab.fa \
    --scores-out my_run/demo_sapiens_scores.csv --fasta-out my_run/demo_humanized.fa
```

> **심화** — **이것이 진짜 BioPhi와 같은 결과인가?** 그렇습니다. `data/`의 레퍼런스는 **bioconda BioPhi CLI로 만든 것**이고, 노트북 마지막 절에서 내 pip 결과와 대조합니다. 실측: humanness(H 0.7101 / L 0.9022)와 humanized 서열이 **완전히 동일**했습니다.

> **주의** — 로컬에서 BioPhi CLI를 굳이 쓴다면: BioPhi가 `~/.local`의 신버전 werkzeug를 끌어와 `cannot import name 'url_encode'`로 죽는 함정이 있습니다. → `PYTHONNOUSERSITE=1`로 user-site를 격리하면 해결됩니다.

---

## 5.2 실행 결과 — Sapiens humanness

데모 항체의 사슬별 humanness(입력 잔기에 Sapiens가 준 평균 확률, 높을수록 사람스러움)입니다. 노트북에서 여러분이 직접 만든 숫자와 같아야 합니다.

| 사슬 | mean Sapiens humanness | 해석 |
|------|------------------------|------|
| Heavy (H) | **0.710** | 상대적으로 낮음 → 마우스 framework 흔적 |
| Light (L, κ) | **0.902** | 사람 항체에 가까움 |

![Sapiens humanness 개요 — 사슬별 humanness와 humanizing 변이 수](05_humanness_overview.png)

*그림. 좌우 2개 패널. **왼쪽**은 사슬별 평균 Sapiens humanness(입력 잔기에 모델이 부여한 평균 확률, 높을수록 사람스러움) — 보라 막대, 빨간 점선(~0.8)이 "사람스러움" 기준. **오른쪽**은 원본 → humanized 변환에서 바뀐 잔기 수 — 주황 막대. 가로축은 chain H / chain L. (이미지: `05_humanness_overview.png`)*

**그림 읽는 법** — 왼쪽 패널에서 중쇄(H)는 0.71로 빨간 기준선(0.8) **아래**에 있고, 경쇄(L)는 0.90으로 기준선 **위**에 있습니다. 즉 중쇄가 덜 사람스럽다는 뜻입니다. 오른쪽 패널을 보면 그 결과가 그대로 행동으로 나타납니다. 덜 사람스러운 **중쇄는 17곳**이나 바뀐 반면, 이미 사람스러운 **경쇄는 0곳**이 바뀌었습니다. 두 패널을 나란히 보면 "humanness가 낮은 사슬일수록 humanize 시 더 많이 손본다"는 인과가 한눈에 들어옵니다. 그리고 이것은 Ch.04에서 ANARCI가 중쇄를 마우스 germline으로 판정한 것과 정확히 일치하는, **세 번째 독립 증거**입니다.

> **심화** — Ch.04와 완벽히 맞아떨어집니다. ANARCI가 중쇄를 **마우스 germline**으로 판정했는데, Sapiens도 중쇄 humanness를 0.71로 낮게(=덜 사람스럽게) 평가했습니다. 경쇄(κ)는 0.90으로 이미 사람스럽습니다. **두 독립 도구(germline 할당 + 언어모델)가 같은 결론**에 도달한 것입니다.

---

## 5.3 실행 결과 — 실제 humanize하면 몇 군데 바뀌나

Sapiens가 만든 humanized 서열을 원본과 비교했습니다.

| 사슬 | 길이 | 변이 수 | 변이율 |
|------|------|---------|--------|
| Heavy | 120 | **17** | 14% |
| Light | 107 | **0** | 0% |

> **심화** — 마우스 중쇄는 사람스럽게 만드느라 **17개**나 바뀐 반면, 이미 사람스럽던 경쇄는 **0개**로, Sapiens가 "고칠 필요 없다"고 본 것입니다. 이것이 humanness 점수와 정확히 일치합니다(낮은 humanness = 많은 변이).

---

## 5.4 주의 — humanization의 함정 — 결합을 잃지 마세요

humanness만 보고 무작정 바꾸면 항원 결합을 잃을 수 있습니다. Ch.01에서 본 **Vernier zone / CDR-supporting residue** 때문입니다.

실전 humanization workflow.

1. ANARCI로 CDR/FR 정의 (Ch.04)
2. IgBLAST/IMGT로 closest human germline 탐색
3. Sapiens/BioPhi로 humanized 후보 생성 ← 이 챕터
4. **CDR-supporting residue·Vernier zone 검토** (함부로 바꾸지 않기)
5. **항원 접촉 residue는 가급적 보존** (Ch.07 interface 분석으로 확인)
6. back-mutation 후보 선정
7. 원본·humanized 구조예측 후 CDR RMSD·paratope geometry 비교 (Ch.06)
8. humanness·developability 재평가 (Ch.08)

humanization mutation table 예 (Chothia numbering 기준, scheme 명시).

| Position | Region | Original | Humanized | 근거 | Back-mutation |
|----------|--------|----------|-----------|------|---------------|
| H27 | CDR-H1 | Y | Y | 항원 접촉 가능성 | 유지 |
| H71 | FR3 | K | R | human germline 유사도↑ | 후보 |
| L49 | FR2 | A | S | CDR-L2 support 가능성 | 검토 |

> **주의** — 목표는 "100% 사람 서열"이 아니라 "**면역원성을 낮추면서 결합을 유지**"하는 것입니다. 그래서 humanness↑와 결합 유지 사이의 균형점을 찾고, 위험한 위치는 back-mutation으로 되돌립니다.

---

### 이 챕터 핵심 요약

1. **Sapiens humanness**: 중쇄 0.710(마우스 흔적) vs 경쇄 0.902(사람스러움) — Ch.04 germline 결과와 일치.
2. 실제 humanize 시 **중쇄 17개 변이, 경쇄 0개**로, humanness 낮은 쪽이 더 많이 바뀝니다.
3. **BioPhi CLI는 bioconda 전용이지만, 부품(`sapiens`+`abnumber`)은 pip**이며, Colab에서도 같은 알고리즘을 직접 돌릴 수 있고, 결과가 CLI와 **비트 단위로 같음**을 노트북이 대조로 보여줍니다.
4. humanization = **argmax 재구성 + 원본 CDR 재이식**이며, CDR을 건드리지 않는 것이 기본값이라는 것을 코드로 확인하세요.
5. humanness만 좇지 말고 **Vernier zone·항원 접촉 잔기 보존 + back-mutation**으로 결합을 지키세요.

다음 → **[06. 구조예측 (IgFold)](../06_structure/06_structure.md)**
