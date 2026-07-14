# 항체 Humanization 완전 정복 — 비인간 항체를 사람 항체로

> **이 과정은 항체 humanization을 처음부터 끝까지 다루는 자기완결형(self-contained) 통합 실무 가이드입니다.**
> 입력 서열 정리(numbering·CDR annotation)부터 시작해, 도구별 후보 생성(BioPhi/Sapiens·Humatch·AnthroAb)·정량 평가(humanness·nativeness·naturalness)·구조 검증·developability·랭킹·실험 검증 제안까지 한 문서 세트로 완결합니다.
> 모든 명령·수치는 **실제 실행 결과 기반**이며, 돌리지 못한 도구는 본문에 **〔본 환경 미실행〕** 으로 정직하게 표시합니다. (실행 환경 상세 → [부록 재현 환경](11_appendix/11_appendix.md))

---

## 0. 과정 개요

항체 humanization은 mouse·rat·rabbit 같은 비인간 항체의 variable domain을, 사람 항체 레퍼토리에 최대한 가깝게 바꾸면서, 항원에 달라붙는 데 꼭 필요한 CDR·핵심 framework는 그대로 지키는 작업입니다. 단일 도구 하나로 끝나는 문제가 아니며, 다음 네 단계를 반복하는 워크플로우로 보는 것이 안전합니다.

1. **입력 정리** — VH/VL 분리, numbering, CDR/FWR annotation, germline assignment
2. **후보 생성** — BioPhi/Sapiens, Humatch, AnthroAb, CDR grafting/backmutation, generative 모델로 humanized 후보 생성
3. **평가** — humanness/nativeness, CDR 보존성, germline identity, liabilities, developability, VH/VL 페어링 타당성 점검
4. **구조 검증** — ABodyBuilder3/ImmuneBuilder 구조 예측, CDR geometry·developability surface·residue tolerance 확인

이 과정은 다음을 **모두** 담습니다.

- **개념·이론**: 왜 humanization을 하는가, CDR grafting·resurfacing·backmutation의 원리, 명명법의 함정
- **실무 전 과정**: 입력 준비(QC·numbering) → 설치/접근 → 실행(도구별 전략) → 해석(메트릭) → 랭킹·자동화
- **도구별 실습**: ANARCI · IgBLAST · BioPhi/Sapiens · Humatch · AnthroAb · AbNatiV · Ab-RoBERTa · 구조 검증
- **단계별 워크플로우와 재현 가능한 명령**, 그리고 실제 실행해 얻은 수치

### 0.1 한눈에 보는 권장 파이프라인

```text
Raw VH/VL FASTA
  → ANARCI / IgBLAST      : numbering, CDR/FWR annotation, germline assignment
  → BioPhi/Sapiens        : 후보 생성 + OASis humanness 평가
  → Humatch               : gene/pairing 관점 후보 보완
  → AnthroAb (masked-LM)  : targeted infilling + mutation 교차검증
  → AbNatiV               : nativeness 평가, 후보 필터링
  → ABodyBuilder3/ImmuneBuilder : 구조 예측, CDR loop sanity check
  → TAP / developability  : liability flagging
  → 후보 5~20개 rank
  → 실험 발현·결합·열안정성 검증
```

---

## 1. 대상 독자와 사전 요구사항

**대상**

- 비인간 항체 서열(mouse/rat/rabbit hybridoma 등)을 확보하고, 이를 임상·치료용으로 사람화해야 하는 연구자
- in silico humanization 결과를 정량적으로 해석하고, 후보를 순위 매겨 실험으로 넘기려는 실무자
- BioPhi·Humatch·AnthroAb·AbNatiV·ANARCI·IgBLAST 계열 도구를 하나의 워크플로우로 엮으려는 계산생물학 실무자

**준비물**

- **웹 브라우저.** 각 챕터의 실습 노트북은 Colab에서 그대로 열립니다 — 챕터 상단의 **실습 콜아웃**에 노트북 링크가 붙습니다. 설치 없이 그 챕터의 명령을 그대로 따라 할 수 있습니다.
- Python·CLI 기본기와 conda 사용 경험. 없어도 [Ch.03](03_setup/03_setup.md)에서 환경을 함께 만듭니다.
- 항체 구조 기초 — VH/VL, CDR/FWR, IgG/Fab/Fv 수준. 핵심 용어는 본문과 [부록 용어집](11_appendix/11_appendix.md)에서 다시 설명합니다.
- 로컬에서 도구를 직접 돌리고 싶다면 conda 환경 하나면 됩니다([Ch.03](03_setup/03_setup.md)). AbNatiV처럼 체크포인트를 내려받는 도구는 본문에 다운로드 용량을 적어 뒀습니다(예: AbNatiV 모델당 약 1GB).

---

## 2. 과정 구성 — 챕터별 자기완결

각 챕터는 **자기 폴더 안에 본문(.md)·노트북(.ipynb)·그래프(.png)** 를 담습니다. 한 스텝을 학습할 때 그 폴더만 보면 됩니다.

### Part A — 개념과 전략

| Ch | 폴더 | 영역 | 핵심 내용 |
|----|------|------|-----------|
| **01** | [01_why_humanization/](01_why_humanization/01_why_humanization.md) | 왜 humanization인가 | 항체 구조, CDR/FWR, Vernier zone, 면역원성(ADA/HAMA), CDR grafting + backmutation |
| **02** | [02_nomenclature_strategy/](02_nomenclature_strategy/02_nomenclature_strategy.md) | 명명법·도구 지도·전략 | `-ximab/-zumab/-umab`과 2021 신체계, 생성 vs 평가 도구, 후보 스펙트럼, end-to-end 워크플로우 |
| **03** | [03_setup/](03_setup/03_setup.md) | 환경 구성 | conda env, 도구별 설치 경로(bioconda·PyPI·GitHub), 설치 검증 |

### Part B — 도구별 실습 (실측 검증)

| Ch | 폴더 | 도구 | 본 환경 검증 |
|----|------|------|--------------|
| **04** | [04_sequence_qc/](04_sequence_qc/04_sequence_qc.md) | ANARCI · IgBLAST | ✅ ANARCI · ✅ IgBLAST |
| **05** | [05_humanize_sapiens/](05_humanize_sapiens/05_humanize_sapiens.md) | BioPhi / Sapiens / OASis | ✅ Sapiens |
| **06** | [06_cdr_safe_tools/](06_cdr_safe_tools/06_cdr_safe_tools.md) | Humatch · AnthroAb (+3-모델 비교) | ✅ Humatch · ✅ AnthroAb |
| **07** | [07_nativeness/](07_nativeness/07_nativeness.md) | AbNatiV · Ab-RoBERTa | ✅ AbNatiV · ✅ Ab-RoBERTa |
| **08** | [08_structure/](08_structure/08_structure.md) | ABodyBuilder3 / ImmuneBuilder / AntiFold | 〔본 환경 미실행〕 |
| **09** | [09_developability/](09_developability/09_developability.md) | liability 모티프 · TAP | 〔TAP 본 환경 미실행〕 |

### Part C — 정리와 운영

| Ch | 폴더 | 내용 |
|----|------|------|
| **10** | [10_ranking_report/](10_ranking_report/10_ranking_report.md) | 후보 랭킹 스키마 · 운영형 GuideDB YAML · 실험 검증 제안 · lab-in-the-loop |
| **11** | [11_appendix/](11_appendix/11_appendix.md) | 최종 체크리스트 · 참고자료 · 재현 환경 · 용어집 |

---

## 3. 실습 노트북 (각 챕터 폴더 안)

노트북은 별도 폴더가 아니라 **해당 챕터 폴더 안**에 있고, 챕터 본문 상단의 **실습 콜아웃**에서 링크됩니다. 브라우저(Colab)에서 여는 것이 기본 경로이고, 로컬 주피터에서도 그대로 열립니다.

각 노트북은 **① 도구를 직접 실행 → ② 내가 만든 결과 확인 → ③ 레퍼런스 대조** 순서로 진행합니다. 여러분이 돌린 산출물은 챕터 폴더의 `my_run/`에 쌓이고, 저장소에 커밋된 `data/`는 **대조군**으로만 씁니다. 어떤 단계를 건너뛰거나 실패해도 자동으로 `data/`로 폴백해서 다음 절이 계속 돌아갑니다(어느 쪽을 쓰는지 노트북이 출력해 줍니다).

아래 **소요 시간은 노트북의 모든 셀을 실제로 실행해 측정한 값**입니다.

| 노트북 | 챕터 | 직접 실행하는 것 | 전 셀 실행 |
|--------|------|------------------|-----------|
| `03_setup_check.ipynb` | 03 | 도구 설치·환경 점검 | 6초 |
| `04_numbering_lab.ipynb` | 04 | ANARCI/abnumber numbering → CDR 추출 → germline 할당 | 1초 |
| `05_sapiens_lab.ipynb` | 05 | Sapiens 인간화 + **CDR 가드 실패 재현** | 6초 |
| `06_tools_lab.ipynb` | 06 | Humatch·AnthroAb 실행 + **3도구 합의 계산** | 32초 |
| `07_nativeness_lab.ipynb` | 07 | Ab-RoBERTa pseudo-likelihood 계산 (AbNatiV는 선택) | 96초 |
| `08_structure_lab.ipynb` | 08 | IgFold 구조 예측 + CDR-H3 RMSD | 7초 |
| `09_developability_lab.ipynb` | 09 | liability 모티프 스캔 | 1초 |
| `10_ranking_lab.ipynb` | 10 | 앞 랩 결과를 모아 랭킹 + candidate report | 5초 |

> 표의 시간은 **셀 실행 시간**입니다. Colab에서 처음 열면 여기에 패키지 설치가 더해져요 — 실측으로 노트북 한 권당 **1~6분**(설치 포함, 두 번째 실행부터는 표의 시간).


공용 그래프 모듈 `humanization_viz.py`는 `humanization_guide/` 루트에 있고, 각 노트북이 `sys.path`에 루트를 추가해 import합니다.

> AbNatiV만 예외입니다 — 체크포인트가 약 2GB라 노트북에서 기본 비활성(`RUN_ABNATIV = False`)이고, 켜지 않으면 커밋된 점수로 이어집니다. 켜는 법은 Ch.07에 있습니다.

---

## 4. 빠른 시작 (Quick Start)

### (A) 브라우저에서 바로 — 설치 없음 (권장 입문)

[Ch.01](01_why_humanization/01_why_humanization.md)부터 읽으면서, 각 챕터 상단 실습 콜아웃의 노트북 링크를 Colab으로 엽니다. 명령·수치·그래프가 본문과 1:1로 대응합니다.

### (B) 로컬에서 직접 돌리기 — conda 환경 하나

```bash
# 1) 공용 환경 (Ch.03 상세) — ANARCI는 PyPI가 아니라 bioconda에 있습니다
conda create -n abhuman -c conda-forge -c bioconda python=3.10 anarci hmmer -y
conda activate abhuman
ANARCI --help

# 2) humanization 엔진 (Ch.05)
python -m pip install sapiens

# 3) parental 서열 numbering + germline (Ch.04)
ANARCI -i parental.fasta --scheme imgt --assign_germline --use_species human --csv -o anarci_gl
```

> `pip install anarci` / `pip install biophi` / `pip install humatch` 는 **모두 실패**합니다. 각각 bioconda·bioconda·GitHub source가 정답입니다 — 자세한 사정은 [Ch.03](03_setup/03_setup.md).

---

## 5. 학습 경로

```text
[개념]  01 왜 humanization → 02 명명법·도구 지도·전략
                                   │
[준비]  03 환경 구성 ───────────────┘
            │
[실습]  04 입력 QC(ANARCI/IgBLAST) → 05 BioPhi/Sapiens → 06 Humatch·AnthroAb
            → 07 AbNatiV·Ab-RoBERTa → 08 구조 검증 → 09 developability
            │
[정리]  10 랭킹·GuideDB·실험 검증 → 11 부록(체크리스트·참고자료·용어집)
```

- **입문자**: 01 → 11 순서대로.
- **급하면**: 03(환경) → 04(입력 QC) → 관심 도구 챕터로 바로. 단, 처음이라면 **04를 먼저** 보길 권합니다. 뒤의 모든 단계가 여기서 만든 numbering·annotation 위에서 돌아가기 때문입니다.

---

## 6. 표기 규약

- `코드` = 실제 명령·파일명·함수명·메트릭 컬럼명
- **실습 —** 직접 따라 할 수 있는 부분 · **심화 —** 더 깊이 · **주의 —** 흔한 함정 · **케이스 스터디 —** 실제 겪은 사례
- 수치는 실제 실행 결과 기반이며, 이 가이드를 검증한 환경에서 돌리지 못한 GPU·웹 전용 도구는 **〔본 환경 미실행〕** 으로 표시합니다. 임의 값을 지어내지 않으려는 의도입니다.
- 실행 환경(하드웨어·버전) 정보는 [부록 재현 환경](11_appendix/11_appendix.md)에 모아 뒀습니다.

<div class="pagebreak"></div>

# Ch.01 — 항체 humanization, 왜 하고 무엇을 지켜야 하나요?

이 챕터를 다 읽고 나면, humanization이 단순히 "사람처럼 보이게 칠하는 일"이 아니라 **결합력과 사람다움 사이의 줄타기**라는 걸 이해하게 될 것입니다. 자, 시작해볼까요?

---

## 1.1 항체는 어떻게 생겼나요?

항체는 heavy chain과 light chain으로 이뤄져 있고, 항원에 달라붙는 일은 주로 variable domain인 **VH와 VL의 CDR1/2/3**가 담당합니다. CDR이 항원과 직접 악수하는 손가락이라면, framework region(FWR)은 그 손가락을 받쳐주는 손바닥·손목 같은 구조적 뼈대입니다.

여기서 흔한 오해 하나. "그럼 framework는 사람 것으로 다 갈아끼워도 되겠네?" — 아닙니다. framework 안에도 결합에 중요한 자리가 숨어 있습니다.

- **Vernier zone** — CDR loop의 모양(conformation)을 아래에서 받쳐주는 자리
- **VH/VL interface residue** — 두 도메인이 맞물리는 면
- **canonical loop determinant** — CDR의 표준 형태를 결정하는 핵심 잔기
- **buried core residue** — 안쪽에 파묻혀 패킹을 잡아주는 자리

이 자리들을 함부로 사람 잔기로 바꾸면, 서열은 사람다워졌는데 정작 항원에 안 붙는 사태가 벌어집니다. 뒤에서 실제로 그런 일이 일어나는 걸 보게 될 것입니다([Ch.05](../05_humanize_sapiens/05_humanize_sapiens.md)의 주의 콜아웃).

---

## 1.2 그래서, humanization은 왜 하나요?

가장 근본적인 질문부터 보겠습니다. 비인간 항체를 사람 몸에 넣으면 무슨 일이 생길까요?

우리 면역계는 "남의 단백질"을 귀신같이 알아봅니다. mouse 유래 항체를 사람에게 투여하면 **항-약물 항체(ADA), 옛날 표현으로 HAMA(Human Anti-Mouse Antibody)** 반응이 생깁니다. 그러면:

- 약이 금방 제거돼서 **반감기(PK)가 짧아지고**
- 효능이 떨어지거나 **알러지·아나필락시스 같은 안전성 문제**가 생기고
- 결국 **규제 승인**도 어려워져요

그래서 humanization의 진짜 목표는 "사람처럼 보이기" 하나가 아니라, 다음의 **균형**입니다.

- 사람 항체 레퍼토리에 가까운 sequence profile 확보 (면역원성 ↓)
- CDR/paratope geometry 유지 (결합력 유지)
- 발현량·안정성·용해도 확보, aggregation 위험 ↓ (개발성)
- 제조 가능성·규제 적합성 개선

쉽게 비유하면, **외국어를 현지인처럼 자연스럽게 다듬되, 원문의 핵심 메시지는 한 글자도 바꾸지 않는 번역**과 같습니다. 문장을 매끄럽게 고치다가 정작 뜻이 바뀌면 번역 실패입니다.

---

## 1.3 CDR grafting과 backmutation — 고전이지만 여전히 핵심

가장 고전적인 humanization은 **CDR grafting**입니다. murine 항체의 CDR을 통째로 떼어내서, 사람 germline(또는 사람 acceptor framework) 위에 이식하는 것입니다. 손가락(CDR)은 그대로 두고 손바닥(framework)만 사람 것으로 바꾸는 셈입니다.

그런데 이렇게만 하면 결합력이 뚝 떨어지는 경우가 많습니다. 사람 framework가 원래 CDR loop를 받쳐주던 미묘한 받침대 역할을 못 하기 때문입니다. 그래서 **backmutation** — framework의 일부 자리를 원래 murine 잔기로 되돌리는 작업 — 을 합니다. 어디를 되돌릴지는 보통 이 순서로 검토합니다.

| 우선순위 | 되돌림 후보 위치 | 이유 |
|---:|---|---|
| 1 | CDR 바로 인접 framework residue | CDR 모양에 직접 영향 |
| 2 | Vernier zone residue | loop conformation 받침대 |
| 3 | VH/VL interface residue | 두 도메인 페어링 유지 |
| 4 | buried core residue | 패킹 안정성 |
| 5 | canonical loop 지지 residue | 표준 loop 형태 유지 |
| 6 | 항원과 직접 접촉하는 framework residue | 드물지만 결정적 |

> **심화 —** 요즘은 grafting 대신 **resurfacing**(표면 노출 잔기만 사람 것으로 바꿔 면역원성을 낮추고 buried core는 보존)이나, 사람 germline framework에 직접 맞추는 방식, 그리고 BioPhi/Sapiens·Humatch 같은 **데이터 기반 자동 humanization**을 많이 써요. 이 가이드의 도구들이 바로 그 현대적 방법들입니다.

---

## 이 챕터 핵심 요약

1. 항원 결합은 **VH/VL의 CDR**이 담당하지만, framework에도 **Vernier zone·VH/VL interface·canonical determinant·buried core** 같은 "건드리면 안 되는" 자리가 숨어 있습니다.
2. humanization의 목적은 면역원성(ADA/HAMA) 감소 — 하지만 그 대가로 **결합력을 잃으면 실패**입니다.
3. 고전적 해법은 **CDR grafting + backmutation**이고, 현대적 해법은 데이터 기반 자동 humanization(Ch.05~07)입니다. 원리는 같습니다: **CDR은 지키고 framework를 사람화한다.**

<div class="pagebreak"></div>

# Ch.02 — 명명법·도구 지도·전략·end-to-end 워크플로우

Ch.01에서 "무엇을 지켜야 하는가"를 봤습니다. 이번 챕터는 그 위에 **판을 깝니다** — 이름만 보고 항체 유래를 읽던 관행이 왜 끝났는지, 어떤 도구가 무슨 일을 하는지, 후보를 몇 개나 어떤 성격으로 만들지, 그리고 전체 파이프라인이 어떻게 굴러가는지.

---

## 2.1 -ximab, -zumab, -umab — 이름만 봐도 알 수 있을까요?

논문이나 약물명에서 `rituximab`, `trastuzumab` 같은 이름을 보면, 끝부분만으로 항체의 유래를 짐작할 수 있던 시절이 있었습니다. 이 절에서 그 규칙과 — 더 중요한 — **그 규칙이 더 이상 통하지 않게 된 사정**을 짚겠습니다.

### 옛 명명법: source substem

과거 monoclonal antibody INN(국제일반명) 명명법에서는 `-mab` 앞의 source substem이 항체의 유래를 나타냈습니다.

| 어미 | 의미 | 일반적 해석 |
|---|---|---|
| `-omab` | murine antibody | 거의 mouse 서열 |
| `-ximab` | chimeric antibody | mouse variable + human constant |
| `-zumab` | humanized antibody | CDR 등 일부만 비인간 + 대부분 human framework |
| `-umab` | human antibody | human 서열 기반 |

예를 들어 `rituximab`은 chimeric(`-ximab`), `trastuzumab`은 humanized(`-zumab`)로 읽혔습니다. 우리가 이 가이드에서 만드는 결과물은 보통 `-zumab` 범주에 들어갑니다 — CDR은 비인간 유래를 지키면서 framework를 사람화하기 때문입니다.

### 2021년 새 명명 체계 — 왜 바뀌었고, 어떻게 바뀌었나

> **주의 —** 2017년부터 WHO INN은 **신규 항체명에서 source substem(`-o-/-xi-/-zu-/-u-`)을 더 이상 쓰지 않는 방향**으로 바꿨고, 2021년에는 기존 `-mab` 어미 자체를 **네 개의 새 접미사로 쪼개는** 체계를 도입했습니다.

**왜 바꿨을까요?** 두 가지 이유가 큽니다.

- **source substem이 부정확해졌습니다.** `-zu-`(humanized)와 `-u-`(human)의 경계가 모호해졌습니다. transgenic mouse·phage display로 만든 항체는 "사람 유래"지만 완전한 human germline은 아니고, 엔지니어링이 섞이면서 "이게 humanized냐 human이냐"를 어미 하나로 가르기 어려워졌습니다.
- **`-mab`로 끝나는 이름이 너무 많아졌습니다.** 발음·구별이 어렵고, 단일클론항체가 아닌 새로운 형식(이중특이체·fragment 등)까지 전부 `-mab`을 달면서 정보가 사라졌습니다.

**그래서 2021년부터 신규 INN은 `-mab` 대신 다음 네 어미 중 하나를 씁니다.**

| 새 어미 | 의미 | 적용 대상 |
|---|---|---|
| `-tug` | unmodified immunoglobulin | 표준 형식의 온전한 항체 |
| `-bart` | artificial antibody | 인공 설계·비천연 구성 항체 |
| `-mig` | multi-specific immunoglobulin | 이중·다중특이성 항체 |
| `-ment` | antibody fragment | Fab·scFv·VHH 등 fragment |

> **핵심 —** 새 체계에서는 **어미가 "유래(mouse/human)"가 아니라 "구조 형식(format)"을 나타냅니다.** 즉 `-zumab`처럼 humanized인지 아닌지를 이름만으로 알던 정보가 새 이름에는 아예 담기지 않습니다. (source substem 폐지와 stem 분할은 별개의 변화이지만, 둘 다 "이름으로 유래를 읽는" 관행을 끝냈다는 점에서 함께 기억하면 됩니다.)

그래서 "`-zumab`이면 무조건 humanized"라는 설명은 **기존 약물명을 해석할 때만** 유효합니다. 최근 신규 후보명에는 적용되지 않습니다. 이름이 아니라 **실제 서열을 ANARCI/IgBLAST로 분석해 유래를 판단하는 것**이 정확합니다([Ch.04](../04_sequence_qc/04_sequence_qc.md)). 우리가 이 가이드에서 만드는 결과물은 개념상 여전히 humanized 항체(과거 `-zumab` 범주)이지만, 최종 이름은 위 새 체계를 따르게 됩니다.

---

## 2.2 Humanization 도구 지도 — 누가 무슨 일을 하나요?

도구가 많아서 처음엔 헷갈립니다. 겁먹지 마십시오. 크게 **후보를 만드는 도구**와 **후보를 평가·검증하는 도구**, 두 부류로 나누면 단순해집니다.

### 후보를 만드는 도구 (generation)

| No. | 도구 | 역할 | 장점 | 한계 | 권장 용도 |
|---:|---|---|---|---|---|
| 1 | **BioPhi/Sapiens** | 자동 humanization + humanness 평가 | 오픈소스, 재현성, OAS 기반, Sapiens/OASis 통합 | 구조·결합력 보장은 아님 | 1차 후보 생성 |
| 2 | **Humatch** | gene-specific joint humanization | VH/VL 페어링까지 고려, 빠름 | 비교적 신규, 구조 검증 별도 | BioPhi와 병렬 후보 생성 |
| 3 | **AnthroAb** | RoBERTa masked-LM 기반 infilling | API·CLI 단순, position별 human-like residue 제안 | repo maturity 확인 필요, masking 설계 중요 | 교차검증, targeted mutation |
| 4 | Hu-mAb | legacy humanization/classifier | 개념 이해에 좋음 | SAbPred에서 humanization 비활성, Humatch 권장 | 역사·비교 섹션 |
| 5 | HuDiff/HuAbDiffusion | diffusion 기반 | 다양한 후보 | 연구용 성격 강함 | advanced/optional |
| 6 | IgCraft | human seq generation/inpainting | CDR motif scaffolding | 최신 연구용 | 후보 다양화 |

### 후보를 평가·검증하는 도구 (evaluation)

| 도구 | 역할 | 워크플로우 내 위치 |
|---|---|---|
| **ANARCI** | numbering, CDR/FWR annotation, germline assignment | 입력 QC, CDR 보존성 비교 |
| **IgBLAST** | V/D/J germline assignment | germline similarity, species/gene 확인 |
| **AbNatiV** | nativeness/humanness 평가 | 후보 필터링·rank score |
| **ABodyBuilder3** | antibody 구조 예측 | 구조 보존성, CDR loop sanity check |
| **ImmuneBuilder** | antibody/nanobody/TCR 구조 예측 프레임워크 | 구조 예측 백엔드 |
| **AntiFold** | 구조 기반 residue tolerance/inverse folding | backmutation 후보 prioritization |
| **TAP** | developability profile | 후보별 risk flagging |
| Thera-SAbDab/SAbDab | 치료항체·구조 데이터 참조 | 레퍼런스, benchmark |

> **이 가이드에서 실제로 돌린 도구** — ANARCI·IgBLAST·Sapiens·Humatch·AnthroAb·AbNatiV 6종은 실제로 설치·실행해 수치를 뽑았습니다. GPU나 웹 전용인 ABodyBuilder3·AntiFold·TAP·Hu-mAb 등은 **〔본 환경 미실행〕** 표시와 함께 정확한 명령 템플릿만 제공합니다. 이건 임의 값을 지어내지 않으려는 의도입니다. (도구별 버전·실행 환경 → [부록 재현 환경](../11_appendix/11_appendix.md))

---

## 2.3 Humanization 전략 — 어떤 후보 세트를 만들까요?

후보를 딱 하나만 만들어서 "이게 사람화 결과입니다" 하면 안 됩니다. 자동 도구의 출력 하나는 **여러 가능한 답 중 하나일 뿐**이기 때문입니다. 실무에서는 한 parental 항체에서 **공격적(aggressive)~보수적(conservative) 스펙트럼**으로 여러 후보를 만들어 비교합니다.

### 후보 스펙트럼

| 후보 성격 | mutation 양 | 노리는 것 | 위험 |
|---|---|---|---|
| Aggressive | 많음 | 최대 humanness | 결합력·구조 손실 위험 ↑ |
| Conservative | 적음 | 결합력 보존 | humanness 개선 폭 ↓ |
| Consensus | 도구 공통 | 신뢰도 높은 mutation만 | 보수적 |
| Backmutated | conservative+선택적 복귀 | 결합 복원 | 설계 노력 ↑ |

### 권장 후보 조합 (최종 5~20개)

- aggressive humanization 2~3개
- conservative humanization 2~3개
- BioPhi-derived 2~3개 / Humatch-derived 2~3개 / AnthroAb-derived 2~3개
- consensus·backmutation 후보 3~5개
- developability-optimized 후보 2~3개

> **심화 — 왜 여러 도구를 같이 쓰나요?** BioPhi/Sapiens는 "서열 humanness" 축, Humatch는 "gene-specific + paired" 축, AnthroAb는 "targeted infilling" 축입니다. **세 도구가 같은 자리에 같은 사람 잔기를 제안하면 그 mutation은 신뢰도가 높습니다.** 한 도구만 제안하는 mutation은 구조·결합 관점으로 한 번 더 따져봅니다. ChatGPT·Claude·Gemini에게 같은 질문을 던지고 답이 겹치는 부분을 신뢰하는 것과 똑같은 발상입니다.

이 원칙은 [Ch.06](../06_cdr_safe_tools/06_cdr_safe_tools.md)에서 실제 수치로 확인됩니다 — 세 도구가 똑같은 치환을 제안한 자리는 실행 모드에 따라 **7곳 또는 12곳**이었고, 그중 `I78T`는 **모드를 바꿔도 살아남는** 가장 강건한 합의였습니다.

---

## 2.4 권장 end-to-end 워크플로우

이제 전체 그림을 한 번 쭉 훑어보겠습니다. 각 단계의 도구 사용법은 Ch.04부터 하나씩 깊이 들어갑니다.

### 입력 요구사항

최소한 이것만 있으면 시작할 수 있습니다.

```text
VH amino acid sequence
VL amino acid sequence
species/source        : mouse / rat / rabbit / unknown
antigen name
binding data (있으면) : KD, EC50, SPR/BLI, ELISA
structure (있으면)    : antibody-only 또는 antibody-antigen complex
must-preserve residues: 알려진 paratope, mutagenesis hotspot
```

### Step A — 서열 QC

1. VH/VL이 정확히 분리됐는지 확인 (scFv라면 linker 기준으로 자르기)
2. stop codon·비표준 아미노산·truncation 확인
3. ANARCI로 chain type과 numbering 확인
4. IgBLAST(또는 ANARCI `--assign_germline`)로 V/J gene과 germline identity 확인

### Step B — 후보 생성

BioPhi/Sapiens와 Humatch를 **병렬로** 돌리는 걸 기본값으로 둡니다. 여기에 AnthroAb를 더해 masked position별 residue 제안을 받습니다. 공통 mutation은 우선 반영하고, 단독 제안 mutation은 따로 검토합니다.

### Step C — 평가 지표

| 지표 | 목적 | 권장 해석 |
|---|---|---|
| CDR identity | 결합 유지 가능성 | CDR mutation은 원칙적으로 제한 |
| FWR human mutation count | humanization 정도 | 과하면 구조 리스크 |
| Human germline identity | human-likeness | VH/VL 각각 평가 |
| OASis humanness | human repertoire peptide 관점 | 낮은 peptide risk 선호 |
| AbNatiV score | natural human repertoire 유사성 | rank에 반영 |
| CDR RMSD | 구조 유지 | antibody-only라도 비교 |
| VH/VL interface risk | chain 페어링 | interface mutation 주의 |
| developability flags | 제조·안정성 | hydrophobic/charge patch, liabilities |

### Step D — 구조 검증

ABodyBuilder3 또는 ImmuneBuilder로 parental과 humanized 후보 구조를 모두 예측하고 비교합니다. complex 구조가 있으면 CDR conformation이 크게 흔들리는 후보는 낮은 rank로. 없으면 antibody-only라도 CDR-H3 geometry·VH/VL orientation·buried/interface mutation을 확인합니다.

### Step E — 최종 후보 선정

5~20개를 남기고, §2.3의 조합으로 다양성을 확보합니다. 그리고 이게 핵심인데 — **in silico 결과는 출발점이지 결승선이 아닙니다.** 최종 판정은 실험([Ch.10](../10_ranking_report/10_ranking_report.md))이 합니다.

---

## 이 챕터 핵심 요약

1. 2021년 새 INN 체계에서 **어미는 유래가 아니라 형식(format)** 을 나타냅니다 — 이름으로 humanized 여부를 읽지 말고 **서열을 분석**하세요.
2. 도구는 **생성(BioPhi/Sapiens·Humatch·AnthroAb)** 과 **평가(ANARCI·IgBLAST·AbNatiV·구조·TAP)** 두 부류로 나눠 보면 단순해집니다.
3. 후보는 하나가 아니라 **aggressive~conservative 스펙트럼 5~20개**로 만들고, **도구 간 합의(consensus) mutation**을 우선 신뢰합니다.
4. 전체 흐름은 **QC → 생성 → 평가 → 구조 → 선정**, 그리고 마지막 판정은 실험입니다.

<div class="pagebreak"></div>

# Ch.03 — 환경 구성 (설치·검증)

이 챕터는 뒤의 모든 실습이 올라탈 **바닥**을 깝니다. 브라우저에서 노트북으로 따라올 거라면 설치는 노트북 첫 셀이 대신 해 주니 훑고 지나가도 됩니다. 로컬에서 직접 도구를 굴릴 거라면, 여기서 만드는 conda 환경 하나가 Ch.04~07의 실습을 거의 다 커버합니다.

> **실습 — `03_setup_check.ipynb`** · ① 직접 실행 → ② 내 결과 확인 → ③ 레퍼런스 대조 · **전 셀 6초**
>
> 도구를 직접 설치하고(ANARCI·abnumber·Sapiens) 러닝 예제 서열을 불러와 환경이 준비됐는지 확인합니다.

---

## 3.1 공용 환경 만들기 — `abhuman`

```bash
# ANARCI는 PyPI가 아니라 bioconda에 있습니다. (이게 첫 번째 함정!)
conda create -n abhuman -c conda-forge -c bioconda python=3.10 anarci hmmer -y
conda activate abhuman
ANARCI --help
```

`ANARCI --help`가 사용법을 출력하면 성공입니다. 이 `abhuman` 환경 하나에 Sapiens·AnthroAb를 얹으면 Ch.04·05·06의 실습이 그대로 돌아갑니다.

> **주의 — `pip install anarci`는 안 됩니다.** ANARCI는 HMMER에 의존하는 bioconda 패키지입니다. PyPI에서 찾으면 못 찾거나 엉뚱한 패키지를 받게 됩니다. 반드시 `-c bioconda`로 설치하십시오. bioconda의 noarch 빌드라 설치 자체는 간단합니다.

---

## 3.2 도구별 설치 경로 지도 — 어디서 받아야 하나

humanization 도구들은 **설치 채널이 제각각**입니다. 여기서 한 번 정리해 두면, 각 챕터에서 "왜 pip이 안 되지?" 하며 멈추는 일을 피할 수 있습니다. 실제로 겪은 실패와 그 해결(케이스 스터디)은 각 챕터에 그대로 실어 뒀습니다.

| 도구 | 설치 채널 | 같은 env에 꼭 필요한 것 | 상세 |
|---|---|---|---|
| **ANARCI** | `conda -c bioconda` (`anarci`, `hmmer`) | — | §3.1 · [Ch.04](../04_sequence_qc/04_sequence_qc.md) |
| **IgBLAST** | `conda -c bioconda` (`igblast`) | germline DB를 직접 빌드 | [Ch.04](../04_sequence_qc/04_sequence_qc.md) |
| **BioPhi** | `conda -c bioconda` (**PyPI에 없음**) | — | [Ch.05](../05_humanize_sapiens/05_humanize_sapiens.md) |
| **Sapiens** | `pip install sapiens` (PyPI) | 모델 가중치는 첫 실행 시 HF에서 자동 다운로드 | [Ch.05](../05_humanize_sapiens/05_humanize_sapiens.md) |
| **Humatch** | **GitHub source** (PyPI에 없음) | `anarci` (없으면 `ModuleNotFoundError`) | [Ch.06](../06_cdr_safe_tools/06_cdr_safe_tools.md) |
| **AnthroAb** | `pip install anthroab` (PyPI) | RoBERTa-base 모델(약 164MB) 자동 다운로드 | [Ch.06](../06_cdr_safe_tools/06_cdr_safe_tools.md) |
| **AbNatiV** | `pip install abnativ` (PyPI) | `abnativ init`(체크포인트 **모델당 약 1GB**) + `anarci` | [Ch.07](../07_nativeness/07_nativeness.md) |
| **Ab-RoBERTa** | HuggingFace (`mogam-ai/Ab-RoBERTa`) | 첫 실행 시 자동 다운로드 | [Ch.07](../07_nativeness/07_nativeness.md) |
| ABodyBuilder3 / ImmuneBuilder / AntiFold / TAP | pip · 웹 | — 〔본 환경 미실행〕 | [Ch.08](../08_structure/08_structure.md) · [Ch.09](../09_developability/09_developability.md) |

> **핵심 — 세 번의 `pip install` 실패.** `pip install anarci`, `pip install biophi`, `pip install humatch` — 셋 다 실패합니다. 각각 **bioconda·bioconda·GitHub source**가 정답입니다. 실제 오류 메시지와 해결 과정은 해당 챕터의 케이스 스터디에 남겨 뒀습니다.

---

## 3.3 환경을 나눌까, 합칠까

- **합치기(권장 시작점)** — `abhuman` 하나에 ANARCI·IgBLAST·Sapiens·AnthroAb·Humatch를 모두 넣으면, Humatch의 `import anarci` 문제가 애초에 생기지 않습니다.
- **나누기** — Humatch는 TensorFlow, AbNatiV는 PyTorch + ImmuneBuilder를 끌고 옵니다. 의존성 충돌이 걱정되면 `humatch`·`abnativ`를 별도 env로 분리하십시오(각 챕터의 설치 절이 분리 기준으로 쓰여 있습니다).

`anarci`는 **세 도구가 공통으로 import**합니다(ANARCI 자체, Humatch의 정렬, AbNatiV의 `-align`). env를 나누더라도 **각 env에 anarci를 넣어야** 합니다 — 이 한 줄이 Ch.06·07의 가장 흔한 에러를 막아 줍니다.

---

## 3.4 설치 검증 체크

```bash
conda activate abhuman
ANARCI --help                       # numbering 도구
python -c "import sapiens; print('sapiens ok')"
python -c "import anthroab; print('anthroab ok')"
python -c "import anarci; print('anarci import ok')"   # Humatch·AbNatiV가 내부적으로 쓰는 경로
```

마지막 줄이 특히 중요합니다. CLI로 `ANARCI`가 돌아가도 **파이썬 모듈 `anarci`가 import되지 않는** 상태면, Humatch와 AbNatiV `-align`이 뒤에서 죽습니다.

---

## 이 챕터 핵심 요약

1. 공용 env `abhuman`을 **bioconda**로 만듭니다(`anarci` + `hmmer`).
2. 설치 채널은 도구마다 다릅니다 — **bioconda(ANARCI·IgBLAST·BioPhi) · PyPI(Sapiens·AnthroAb·AbNatiV) · GitHub(Humatch)**.
3. 모델 가중치는 대부분 **첫 실행 때 자동 다운로드**되지만, AbNatiV만은 `abnativ init`을 먼저 돌려야 하고 체크포인트가 **모델당 약 1GB**입니다.
4. `import anarci`가 되는지 반드시 확인하세요 — Humatch·AbNatiV가 이 모듈에 의존합니다.

<div class="pagebreak"></div>

# Ch.04 — 입력 QC: ANARCI / IgBLAST

이번 챕터는 좀 실무적입니다. 그런데 솔직히, 뒤의 모든 단계가 여기서 만든 numbering·annotation 위에서 돌아가기 때문에, **가장 중요한 챕터**라고 해도 과언이 아닙니다. 여기를 대충 하면 뒤에서 "왜 CDR이 안 맞지?" 하면서 헤매게 됩니다.

> **실습 — `04_numbering_lab.ipynb`** · ① 직접 실행 → ② 내 결과 확인 → ③ 레퍼런스 대조 · **전 셀 1초**
>
> ANARCI/abnumber 로 직접 numbering 해 CDR 6개를 뽑고, germline 을 할당해 **보호할 좌표**를 확정합니다.

> **실습 —** 이 챕터의 모든 명령과 수치는 ANARCI 2024.05.21 · IgBLAST 1.22.0을 실제로 설치해 돌려 본 결과입니다. 환경은 [Ch.03](../03_setup/03_setup.md)의 `abhuman`을 그대로 씁니다.

---

## 4.1 ANARCI 실행 — numbering + germline

ANARCI는 antibody/TCR variable domain을 numbering하고 chain type을 분류합니다. IMGT·Chothia·Kabat·Martin·AHo scheme을 지원하는데, 이 가이드는 **IMGT를 기본**으로 두겠습니다.

실제로 다음 parental 서열(mouse hybridoma 가정)을 넣어보겠습니다. **이 서열이 가이드 전체를 관통하는 예제**입니다 — Ch.05~07의 모든 수치가 이 두 체인에서 나옵니다.

```bash
cat > parental.fasta <<'FASTA'
>parental_H
QVQLQQSGPELVKPGASVKMSCKASGYTFTDYVINWGKQRSGQGLEWIGEIYPGSGTNYYNEKFKAKATLTADKSSNIAYMQLSSLTSEDSAVYFCARRGRYGLYAMDYWGQGTSVTVSS
>parental_L
QSALTQPPSASGSPGQSVTISCTGTSSDVGHKFPVSWYQQYPGKAPKLLIYKNLLRPSGVPDRFSGSKSGTSASLAITGLQAEDGADYYCQSYDSSLRVVFGGGTKTVVLG
FASTA

# numbering + CDR/FWR (CSV로 출력)
ANARCI -i parental.fasta --scheme imgt --csv -o anarci_out

# germline assignment까지 (humanization에서 핵심!)
ANARCI -i parental.fasta --scheme imgt --assign_germline --use_species human --csv -o anarci_gl
```

---

## 4.2 결과 해석 — 실제 출력으로

여기서 많은 분들이 그냥 "돌아갔다"에서 멈추는데, 진짜 정보는 germline 컬럼에 있습니다. 위 명령을 실제로 돌려서 `anarci_gl_H.csv`/`anarci_gl_KL.csv`에서 핵심 컬럼만 뽑으면 이렇게 나옵니다.

| 체인 | chain_type | 가장 가까운 human V gene | V identity | J gene | J identity |
|---|---|---|---:|---|---:|
| Heavy | H | `IGHV1-69*06` | **63%** | `IGHJ6*01` | 86% |
| Light | L (lambda) | `IGLV1-40*01` | **81%** | `IGLJ2*01` | 83% |

> **함정 — 중쇄 J 유전자는 도구마다 다르게 나옵니다.** ANARCI는 `IGHJ6*01`(85.71%)을 고르지만, abnumber의 germline 조회는 같은 서열에 `IGHJ4*01`을 답합니다. 틀린 게 아니라 **완전한 동점**이에요 — J 절편 14잔기 중 12개가 맞아 둘 다 85.71%이고, 어느 쪽이 먼저 나오냐는 도구의 tie-break(참조 세트·순회 순서)에 달렸습니다. V 유전자(`IGHV1-69*06` 63%)처럼 격차가 큰 경우와 달리, **J는 짧아서 동점이 흔합니다.** 그래서 backmutation 판단의 근거로는 V 유전자를 쓰고, J는 참고로만 봅니다.

이 표 한 장이 humanization 전략을 거의 다 말해줍니다.

- **Heavy chain V identity가 63%** — 사람 germline과 꽤 멉니다. 이 항체가 진짜 비인간 유래임을 확인해주고, **heavy framework에 humanization 여지가 크다**는 뜻입니다.
- **Light chain V identity가 81%** — 람다 경쇄가 이미 상당히 사람답습니다. 즉 light는 손댈 자리가 적고, **노력의 무게중심을 heavy에 둬야 한다**는 신호입니다.

> **심화 —** ANARCI의 `--assign_germline`은 IgBLAST 없이도 "가장 가까운 사람 germline과 % identity"를 바로 줘서, humanization 출발점 파악에 빠르고 편합니다. 더 엄밀한 V(D)J 분석이나 junction 분석이 필요하면 IgBLAST를 병행하십시오(§4.4).

---

## 4.3 CDR 추출 — 무엇을 지켜야 하는지부터 못 박기

humanization에서 가장 먼저 해야 할 일은 **"여기는 절대 안 건드린다"는 CDR을 명확히 표시**하는 것입니다. ANARCI의 IMGT numbering에서 CDR 위치(27–38, 56–65, 105–117)를 뽑으면, 위 서열의 실제 CDR은 이렇게 나옵니다.

| 체인 | CDR1 | CDR2 | CDR3 |
|---|---|---|---|
| Heavy | `GYTFTDYV` | `IYPGSGTN` | `ARRGRYGLYAMDY` |
| Light | `SSDVGHKFP` | `KNL` | `QSYDSSLRVV` |

이 잔기들은 뒤에서 어떤 도구를 쓰든 **기본적으로 보호**합니다. 특히 **CDR-H3(`ARRGRYGLYAMDY`)** 는 항원 결합에 가장 결정적인 loop라, 여기에 mutation이 들어가면 빨간불입니다.

> **흔한 함정 —** 자동 humanization 도구를 아무 가드 없이 돌리면, 모델이 "사람 레퍼토리에서 이 자리는 보통 X더라" 하면서 **CDR까지 사람 잔기로 바꿔버리는** 일이 생깁니다. 그래서 CDR 좌표를 미리 못 박아두는 이 단계가 중요합니다. [Ch.05](../05_humanize_sapiens/05_humanize_sapiens.md)에서 실제로 그런 사고가 나는 걸 보여드리겠습니다.

---

## 4.4 IgBLAST — ANARCI 결과를 독립적으로 한 번 더 확인하기

ANARCI의 germline 추정이 맞는지, 두 번째 도구로 교차확인하면 더 든든합니다. IgBLAST는 V/D/J germline assignment를 BLAST 방식으로 해줍니다. 단, **germline DB를 직접 마련해야** 하는 게 진입장벽인데 — 여기서 깔끔한 트릭이 하나 있습니다.

> **실습 —** IgBLAST 1.22.0을 bioconda로 깔고, germline DB는 **ANARCI가 내장한 사람 germline 서열로 직접 빌드**했습니다. 외부 다운로드 없이 재현됩니다.

```bash
conda install -c bioconda igblast -y       # igblastp, makeigblastdb 포함

# (트릭) ANARCI 패키지 안에 사람 IGHV germline 250개가 들어 있습니다. 이걸 FASTA로 뽑아 DB로 만듭니다.
python - <<'PY'
from anarci import germlines
g = germlines.all_germlines
with open("human_IGHV.fasta","w") as fh:
    for gene, alleles in g['V']['H']['human'].items():
        seq = "".join(next(iter(alleles.values()))).replace("-","").replace(".","")
        fh.write(f">{gene}\n{seq}\n")
PY

makeigblastdb -in human_IGHV.fasta -dbtype prot -out db/human_gl_V

export IGDATA=$(dirname $(dirname $(which igblastp)))/share/igblast
igblastp -query parental_H.fasta -germline_db_V db/human_gl_V -organism human -outfmt 7
```

**실측 결과** — parental heavy chain의 top V hit:

```text
# Fields: query, subject, % identity, alignment length, mismatches, ..., evalue, bit score
V  parental_H  IGHV1-8*01    63.27   98  36  ...  1.87e-43  130
V  parental_H  IGHV1-69*08   63.27   98  36  ...  2.66e-43  130
```

> **심화 — 두 도구가 같은 결론을 가리킵니다.** IgBLAST의 top hit는 **IGHV1-8\*01, 63.27% identity**입니다. §4.2에서 ANARCI는 **IGHV1-69, 63%**라고 했습니다. top 유전자명은 IGHV1-8 vs IGHV1-69로 한 끗 다르지만 **둘 다 IGHV1 subgroup이고 identity가 63%로 동일**합니다. 정렬 시드와 점수 방식이 다른 두 도구가 독립적으로 "IGHV1 계열, 사람과 약 63% 거리"라는 같은 결론을 낸 것입니다. humanization 여지가 크다는 §4.2의 판단이 한 번 더 확인됐습니다. (참고: `igblastp`는 단백질 모드라 J·junction은 다루지 않습니다. V gene·% identity 확인이 주 용도입니다.)

humanization에서 IgBLAST는 "parental의 V gene이 뭔지, humanized 후보의 germline identity가 얼마나 올라갔는지"를 엄밀히 확인하는 데 써요.

---

## 이 챕터 핵심 요약

1. ANARCI는 `pip`이 아니라 **bioconda**로 설치합니다(HMMER 의존).
2. `--assign_germline`으로 **가장 가까운 사람 germline과 % identity**를 바로 얻습니다 — 실측: heavy 63%(IGHV1-69), light 81%(IGLV1-40).
3. IgBLAST로 교차확인하면 **IGHV1-8 63.27%** — 같은 IGHV1 계열·같은 identity로 ANARCI와 결론 일치.
4. V identity가 낮은 체인(여기선 heavy)에 humanization 여지가 커요.
5. 뒤 단계로 가기 전에 **CDR 좌표를 못 박아** 보호 대상을 명확히 합니다.

<div class="pagebreak"></div>

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

<div class="pagebreak"></div>

# Ch.06 — CDR-safe 도구: Humatch · AnthroAb

[Ch.05](../05_humanize_sapiens/05_humanize_sapiens.md)에서 Sapiens는 후보를 잘 만들었지만, 가드 없이 돌리자 **CDR-L1을 건드려버렸습니다.** 이번 챕터의 두 도구는 그 문제를 다른 방식으로 다룹니다 — Humatch는 CDR 보호를 **도구 안에 내장**하고, AnthroAb는 **내가 지정한 자리만** 채웁니다. 그리고 마지막에 세 생성 모델(Sapiens·Humatch·AnthroAb)을 나란히 비교합니다.

> **실습 — `06_tools_lab.ipynb`** · ① 직접 실행 → ② 내 결과 확인 → ③ 레퍼런스 대조 · **전 셀 32초**
>
> Humatch·AnthroAb 를 직접 실행해 CDR 보존 여부를 확인하고, **세 도구의 합의 위치**를 실측으로 계산합니다.

> **실습 —** 이 챕터의 수치는 Humatch 1.0.1(GitHub source)·AnthroAb 1.1.0(PyPI)을 실제 설치·실행해 뽑았습니다.

---

## 6.1 Humatch — gene-specific·paired humanization

BioPhi/Sapiens가 "서열 humanness" 축이라면, Humatch는 다른 축을 봅니다. heavy와 light를 따로 보지 않고 **gene-specific하게, 그리고 VH/VL 페어링까지 함께** 고려해서 사람화합니다. OPIG(옥스퍼드)에서 나온 도구입니다.

### 6.1.1 설치 — GitHub source

```bash
# 함정: pip install humatch 안 됩니다(PyPI에 없음). GitHub에서 설치합니다.
conda create -n humatch -c conda-forge python=3.10 -y
conda activate humatch
git clone https://github.com/oxpig/Humatch.git
cd Humatch
python -m pip install .          # humatch 1.0.1 + tensorflow 2.21 설치됨

# (핵심) Humatch는 내부적으로 anarci 모듈을 import합니다. 같은 env에 깔아주십시오.
conda install -c bioconda -c conda-forge anarci -y
```

> **케이스 스터디 — `ModuleNotFoundError: No module named 'anarci'`**
> 초안의 `pip install Humatch`는 `No matching distribution found`로 실패합니다(PyPI에 없음). GitHub source로 깔면 `humatch 1.0.1`과 TensorFlow 2.21이 **문제없이 설치**됐습니다. 그런데 막상 `Humatch-humanise --help`를 돌리니 이렇게 죽었습니다.
> ```
> File ".../Humatch/align.py", line 12, in <module>
>     import anarci
> ModuleNotFoundError: No module named 'anarci'
> ```
> Humatch가 정렬에 ANARCI를 쓰는데, 의존성으로 자동 설치되진 않았습니다. **같은 env에 `conda install -c bioconda anarci`로 깔아주니 CLI가 정상 동작**했습니다. [Ch.03](../03_setup/03_setup.md)의 `abhuman` env에 Humatch를 함께 깔면 이 문제를 아예 피할 수 있습니다.

### 6.1.2 CLI 사용 예시

```bash
Humatch-humanise \
  -H QVQLQQSGPELVKPGASVKMSCKASGYTFTDYVINWGKQRSGQGLEWIGEIYPGSGTNYYNEKFKAKATLTADKSSNIAYMQLSSLTSEDSAVYFCARRGRYGLYAMDYWGQGTSVTVSS \
  -L QSALTQPPSASGSPGQSVTISCTGTSSDVGHKFPVSWYQQYPGKAPKLLIYKNLLRPSGVPDRFSGSKSGTSASLAITGLQAEDGADYYCQSYDSSLRVVFGGGTKTVVLG \
  -v
```

### 6.1.3 실행하면 무슨 일이 일어나나요? — 실제 로그

`Humatch-humanise`를 돌리면 먼저 모델 가중치(heavy/light/paired CNN)를 Zenodo에서 받고, config를 출력한 뒤 humanization을 시작합니다. 실제 로그의 config 부분이 이것입니다.

```text
Config:                         Value
max_edit                           60
GL_allow_CDR_mutations_H        False    ← heavy CDR은 기본 보호
CNN_allow_CDR_mutations_H       False
GL_allow_CDR_mutations_L        False    ← light CDR도 기본 보호
CNN_allow_CDR_mutations_L       False
CNN_target_score_H               0.95    ← 이 점수에 도달할 때까지 사람화
CNN_target_score_L               0.95
...
Loading CNNs
Downloading heavy/light/paired model weights from zenodo... done
Humanising 1 sequences
```

> **심화 — 여기서 Sapiens와 결정적으로 다릅니다!** [Ch.05](../05_humanize_sapiens/05_humanize_sapiens.md)에서 가드 없는 Sapiens argmax는 CDR-L1을 건드려버렸습니다. 그런데 Humatch는 **`allow_CDR_mutations=False`가 기본값**이라, 시키지 않는 한 CDR을 아예 안 건드립니다. 즉 Humatch는 "CDR 보호"가 도구 안에 내장돼 있습니다. 대신 framework를 **CNN 점수가 목표치(0.95)에 닿을 때까지 single-point variant를 반복 탐색**하며 사람화합니다. 이 반복 탐색은 시간이 꽤 걸립니다 — 코어를 여러 개 쓰거나 GPU에서 돌리면 빨라집니다.

> **케이스 스터디 — multiprocessing 함정.** Python API로 직접 호출할 때, config의 `num_cpus`가 16이면 macOS처럼 프로세스를 spawn 방식으로 띄우는 플랫폼에서 `An attempt has been made to start a new process before the current process has finished its bootstrapping phase` 오류로 죽습니다. 해결은 둘 중 하나입니다. ① 스크립트를 `if __name__ == "__main__":` 가드 안에서 실행하거나, ② `config["num_cpus"]=1`로 단일 코어로 돌려요(느리지만 확실).

### 6.1.4 결과 해석 — 실측, 그리고 Sapiens와의 결정적 차이

위 명령을 [Ch.04](../04_sequence_qc/04_sequence_qc.md)의 parental 서열에 실제로 돌린(single-thread) **실측 결과**입니다. Humatch가 분류한 gene family는 **HV=`hv1`, LV=`lv2`** 로, Ch.04의 ANARCI 결과(IGHV1·IGLV1-40)와 **정확히 일치**합니다 — 두 도구가 독립적으로 같은 결론을 낸 것입니다.

| 체인 | gene | mutation 수 | 최종 CNN 점수 | CDR 변경 |
|---|---|---:|---:|---|
| VH | hv1 | **18** | 0.972 | **0개** (CDR-H3 `ARRGRYGLYAMDY` 그대로) |
| VL | lv2 | **2** | 1.000 | **0개** (CDR-L1 그대로) |

VH mutation(18개: `Q5V, R40A, A66G, K67R, I78T, ...`)은 **전부 framework**입니다. Sapiens가 찾은 mutation과 `Q5V·M20V·R40A·A66G·K67R·I78T·Q82E·S91T` 등 상당수가 겹칩니다 — 두 도구가 공통으로 제안하는 자리라 **신뢰도가 높은 humanizing position**이라는 뜻입니다([Ch.02](../02_nomenclature_strategy/02_nomenclature_strategy.md) 심화의 "교차검증" 원칙이 실제로 작동!).

> **주의 — 같은 입력, 전혀 다른 CDR 안전성.** 똑같은 경쇄에 대해:
> - **Sapiens(가드 없는 argmax)** → CDR-L1(`H31A, K32Y, F33N, P34D`)에 **mutation 4개**
> - **Humatch(기본 설정)** → VL 전체에 mutation 2개(`G85E, V108T`), **CDR에는 0개**
>
> 도구를 바꾼 게 아니라 **"CDR을 보호하느냐"는 설계 철학의 차이**가 이 결과를 가릅니다. 그래서 BioPhi/Sapiens를 쓸 땐 CDR 보호를 직접 챙기고(Ch.05), Humatch는 그게 내장돼 있다는 걸 이해하고 쓰는 게 중요합니다.

정리하면, 실무에서는 두 축을 이렇게 나눠 써요.

- **BioPhi/Sapiens** = sequence humanness 중심 후보 축 (CDR 보호는 직접 챙겨야 함)
- **Humatch** = gene-specific + paired humanization 보완 축 (CDR 보호 내장, **paired CNN**으로 VH/VL 페어링 타당성까지 점수화)

두 축의 결과를 나란히 놓고, **공통 mutation은 신뢰**(위 VH에서 실제로 다수 겹침), 단독 mutation은 검토 — 이렇게 써요.

---

## 6.2 AnthroAb — masked-LM targeted infilling

AnthroAb는 사람 항체 서열에 특화된 **RoBERTa 계열 masked language model**입니다. 빈칸(`*`)을 뚫어 둔 자리에 "사람이라면 여기 뭐가 올까?"를 채워주는(infilling) 도구입니다. VH·VL 모델이 따로 있습니다.

<!-- 근거: anthroab/predict.py(predict_best_score=전체 argmax / predict_masked=*·X 자리만), anthroab/cli.py(--humanize는 predict_masked만 사용), notebooks/antibody_infilling.ipynb("humanize all positions, not just masks" / "Predictions can even be made in CDR3 regions") -->

### 6.2.1 두 가지 사용 모드 — 자동 전체 변경 vs 커스텀 마스킹

AnthroAb는 사실 **두 가지 방식**으로 humanization을 할 수 있습니다. repo의 `anthroab/predict.py`를 직접 확인한 결과이며, 두 함수의 동작이 정반대입니다.

| 모드 | 함수 | 무엇을 바꾸나 | 노출 |
|---|---|---|---|
| **① 자동 전체 변경** | `predict_best_score(seq, chain)` | **모든 position**을 각 자리에서 가장 사람다운(human-likely) 잔기로 교체 | **API 전용** (CLI 없음) |
| **② 커스텀 마스킹** | `predict_masked(seq, chain)` | `*`(또는 `X`)로 표시한 **자리만** 교체, 나머지는 parental 그대로 | **CLI(`--humanize`) + API** |

**① 자동 전체 변경 — `predict_best_score`**

각 position의 사람 모델 확률 분포(`predict_scores`)에서 argmax(가장 확률 높은 잔기)를 뽑아 **서열 전체를 다시 씁니다.** 마스킹이 필요 없습니다 — parental 서열을 그대로 넣으면 됩니다.

```python
import anthroab
vh = "QVQLQQSGPELVKPGASVKMSCKASG...YAMDYWGQGTSVTVSS"   # 마스킹 없이 그대로
humanized_vh = anthroab.predict_best_score(vh, "H")    # 모든 자리를 가장 사람다운 잔기로
```

이는 [Ch.05](../05_humanize_sapiens/05_humanize_sapiens.md)의 Sapiens `predict_scores` → argmax와 **개념·구현이 동일**합니다(AnthroAb README도 "Sapiens 인터페이스·기능을 그대로 따른다"고 명시).

> **주의 — `predict_best_score`는 CDR을 보호하지 않습니다.** repo 노트북(`antibody_infilling.ipynb`)이 직접 "humanize **all positions**, not just masks"라고 적고, 별도로 "Predictions can even be made in **CDR3** regions"라고 명시합니다. 즉 자동 모드는 Ch.05의 가드 없는 Sapiens argmax와 똑같이 **CDR까지 바꿔버릴 수 있습니다.** 자동 모드를 쓸 거면 [Ch.04](../04_sequence_qc/04_sequence_qc.md)의 ANARCI CDR 좌표로 **후처리 복원**(또는 CDR 마스킹 제외)이 필수입니다.

**② 커스텀 마스킹 — `predict_masked`**

내가 바꾸고 싶은 자리만 `*`(또는 `X`)로 표시하면, **그 자리만** 사람 잔기로 채우고 나머지는 parental을 보존합니다. 내부적으로는 `predict_best_score`를 돌린 뒤 **마스킹 안 한 자리를 원래대로 되돌리는** 방식입니다(repo 소스 기준). CLI `--humanize`가 쓰는 게 바로 이 모드이고, 구체적 사용법은 §6.2.4에서 다룹니다.

> **권장 — 그래서 기본은 ②번입니다.** humanization에는 절대 건드리면 안 되는 CDR이 있으니(Ch.04), 안전한 기본값은 "FWR 후보 자리만 `*`로 찍는" 커스텀 마스킹입니다. ①번 자동 모드는 "최대 사람화" 후보를 빠르게 보고 싶을 때 쓰되, **반드시 CDR 가드와 함께** 씁니다.

### 6.2.2 어떻게 쓰는 게 안전한가요?

AnthroAb는 "서열 전체를 한 방에 자동 humanization"하는 도구로 쓰기보다, **콕 집은 자리만 채워보는** 용도가 안전합니다.

- BioPhi/Sapiens나 Humatch가 제안한 framework mutation을 **독립적으로 재확인**
- ANARCI로 정한 FWR 후보 위치만 `*`로 masking → targeted infilling
- CDR은 기본 보호, 꼭 필요할 때만 low-risk CDR edge에 제한적으로
- aggressive보다 **conservative·backmutation 후보** 설계의 보조 근거로

### 6.2.3 설치

```bash
conda activate abhuman
python -m pip install anthroab        # anthroab 1.1.0 설치됨
# 또는 source:
git clone https://github.com/nagarh/AnthroAb && cd AnthroAb && pip install -e .
```

> **실습 —** AnthroAb 1.1.0을 `pip install`로 깔았습니다. RoBERTa-base 모델(VH: `hemantn/roberta-base-humAb-vh`, VL: `...-vl`)은 첫 실행 때 HuggingFace에서 자동으로 받아옵니다(가중치 약 164MB). API가 Sapiens와 거의 똑같아서(`predict_masked`, `predict_scores`) 배우기 쉽습니다.

### 6.2.4 masked FASTA 규칙과 실행

`*`로 표시한 자리를 사람다운 잔기로 채웁니다. header는 `{name}_VH` / `{name}_VL` 형식을 권장합니다.

```bash
cat > anthroab_input.fasta <<'FASTA'
>cloneA_VH
**QL*QSGPELVKPGASVKMSCKASGYTFTDYVINWGKQRSGQGLEWIGEIYPGSGTNYYNEKFKAKATLTADKSSNIAYMQLSSLTSEDSAVYFCARRGRYGLYAMDYWGQGTSVTVSS
>cloneA_VL
QSALTQPPSASGSPGQSVTISCTGTSSDVGHKFPVSWYQQYPGKAPKLLIYKNLLRPSGVPDRFSGSKSGTSASLAITGLQAEDGADYYCQSYDSSLRVVFGGGTKTVVLG
FASTA

anthroab -i anthroab_input.fasta -o anthroab_output.fasta --humanize
```

```python
import anthroab
masked_vh = "**QL*QSGPELVKPGASVKMSCKASG..."   # 바꿀 자리만 *
humanized_vh = anthroab.predict_masked(masked_vh, "H")
```

### 6.2.5 masking 전략

| masking 대상 | 권장 여부 | 설명 |
|---|---|---|
| FWR exposed residue | ✅ 권장 | humanness 개선 크고 결합 위험 낮음 |
| FWR buried residue | ⚠️ 주의 | packing 불안정 가능, 구조 검증 |
| Vernier zone | 🔸 제한적 | CDR conformation 받침대, backmutation과 함께 |
| VH/VL interface | ⚠️ 주의 | 페어링 orientation 변화 가능 |
| CDR core/paratope | ⛔ 보호 | 근거 없이는 절대 masking 안 함 |
| CDR edge residue | 🔸 제한적 | immunogenicity/developability 명확할 때만 |

### 6.2.6 실측 — Sapiens 제안을 AnthroAb로 교차검증

[Ch.05](../05_humanize_sapiens/05_humanize_sapiens.md)에서 Sapiens가 제안한 framework 위치(`Q5V, V12K, M20V, R40A, A66G, K67R, A68V, I78T, Q82E, S91T`)를 `*`로 masking해서 AnthroAb에게 "이 자리, 사람이라면 뭐가 올까?"를 독립적으로 물어봤습니다. 두 도구가 같은 답을 내면 신뢰도가 올라가는 것입니다.

```python
import anthroab
VH = "QVQLQQSGPELVKPGASVKMSCKASG...YAMDYWGQGTSVTVSS"
masked = VH 위치 [5,12,20,40,66,67,68,78,82,91]을 "*"로 치환
filled = anthroab.predict_masked(masked, "H")
```

**실측 결과:**

| 위치 | parental | Sapiens 제안 | AnthroAb 제안 | 합의? |
|---:|:---:|:---:|:---:|:---:|
| 78 | I | **T** | **T** | ✅ 합의 |
| 5 | Q | V | Q | ✗ |
| 40 | R | A | G | ✗ |
| 66 | A | G | D | ✗ |
| 67 | K | R | K | ✗ |

> **심화 — 합의된 것만 믿습니다.** 위 표는 AnthroAb의 **FR-masked 모드**에서 Sapiens와 겹치는 자리를 뽑은 것입니다. 세 도구(Sapiens·Humatch·AnthroAb)가 **똑같은 치환을 제안한 자리**를 실제로 세어 보면(`data/three_way_consensus.csv`, 노트북에서 직접 계산합니다):
>
> - **AnthroAb best-score 모드**: 합의 **7곳** — H5(Q→V), H21(M→V), H42(G→V), H68(N→A), H74(A→G), H75(K→R), L99(G→E) *(IMGT 번호)*. **이 모드에서는 `I78T`가 합의에 들지 않습니다.**
> - **AnthroAb FR-masked 모드**: 합의 **12곳** — 위 7곳에 H46·H76·H86·H99 등이 추가되고, `I78T`(IMGT `H86`)가 **여기 포함됩니다.**
>
> 즉 `I78T`는 **합의 중 하나**이지, "유일한 합의"가 아닙니다(이전 판의 서술을 실측에 맞게 바로잡았습니다). 그럼에도 `I78T`가 특별한 이유는 따로 있습니다 — **번호 체계나 도구 모드를 바꿔도 살아남는**, 가장 강건한 합의라는 점입니다. 반대로 H45·H68처럼 **모드에 따라 제안 잔기가 갈리는 자리**(R→A vs R→P)는 합의로 치면 안 됩니다.
>
> 도구마다 답이 갈리는 게 정상입니다. 그래서 도구 하나의 출력을 그대로 쓰지 않고, **여러 표를 모아 합의를 보는** 워크플로우가 중요한 것입니다. 그리고 합의를 셀 때는 **어떤 모드로 돌린 결과인지 반드시 함께 적어야** 합니다 — 모드가 다르면 합의 개수가 7이 되기도, 12가 되기도 하니까요.
>
> **번호 주의** — Sapiens·AnthroAb의 변이 표기(`I78T`)는 **서열 1-based 인덱스**이고, 위 합의 목록은 **IMGT 번호**입니다(`I78T` = IMGT `H86`). 두 체계를 섞으면 엉뚱한 잔기를 건드리게 되니, 노트북에서 `raw2imgt_H.json` 매핑으로 항상 변환해 씁니다.

> **그래프 —** `humanization_viz.mutation_map(rows, title, outpath)` 로 위치별 도구 제안을 한 장에 겹쳐 그리면, 합의 자리(pos 78)가 한눈에 보입니다.

### 6.2.7 결과 해석

AnthroAb 출력은 최종 후보가 아니라 **mutation 제안의 한 표(vote)** 로 봅니다. 우선순위를 올릴 만한 경우:

- BioPhi/Sapiens·Humatch·AnthroAb가 **같은 자리에 같은 잔기**를 제안 (실측: `I78T`가 세 도구 합의)
- 제안 잔기가 human germline·OAS repertoire에서 흔히 관찰됨
- 구조(ABodyBuilder3) 상 CDR geometry·interface가 안정적
- AbNatiV/OASis/TAP 지표가 parental 대비 개선

반대로 CDR·Vernier·interface·buried core에서 **AnthroAb만 단독 제안**한 mutation은 보수적으로 다룹니다.

---

<!-- 근거: biophi/biophi/humanization/methods/humanization.py(argmax+CDR graft), Humatch/Humatch/humanise.py·model.py(Conv1D CNN + germline-likeness + single-point greedy), HF config prihodad/biophi-sapiens1-vh(4L/128H) vs hemantn/roberta-base-humAb-vh(12L/768H), model.safetensors 2.2MB vs 164MB, AnthroAb README, Antibody_humanization_project/results/anthroab_argmax_softmax_comparison/ -->

## 6.3 모델 비교 — BioPhi/Sapiens vs Humatch vs AnthroAb

Ch.05~06에서 세 생성 도구를 각각 봤으니, 이제 **나란히 비교**해 언제 무엇을 쓸지 정리합니다. (아래는 각 repo 소스를 직접 확인한 결과입니다.)

### 6.3.1 BioPhi/Sapiens vs Humatch — 학습 알고리즘 차이 및 장단점

| | BioPhi/Sapiens | Humatch |
|---|---|---|
| 방식 | 생성형 **언어모델(LM)** — RoBERTa masked-LM | 판별형 **CNN 분류기**(Conv1D; heavy/light/paired) + germline-likeness |
| 사람화 원리 | 위치별 사람 잔기 확률 → **argmax(greedy)**, iterative | **탐색**: ① germline-likeness 매칭 → ② CNN 점수가 목표(기본 0.95)에 닿을 때까지 single-point greedy |
| 페어링 | VH/VL 따로 | **VH/VL paired CNN**까지 함께 |
| CDR | 기본 보호(parental CDR graft back) + Vernier backmutation 옵션 | 기본 보호(`allow_CDR_mutations=False`) + 위치 고정 지원 |
| 속도 | 빠름(LM 추론 × iter) | 반복 탐색이라 무거움(§6.1.3) |

- **BioPhi/Sapiens(LM)** — 장점: 문맥을 학습한 부드러운 per-position 사람 프로파일, OASis로 검증, **확률행렬**을 줘서 설명·마스킹·targeted에 유리. 단점: argmax는 **결정적 단일 답**, 사람 분류기/페어링을 직접 최적화하진 않음.
- **Humatch(CNN 탐색)** — 장점: 사람 분류기 점수를 **목표치까지 직접 최적화**, gene-specific + **paired**, 빠른 설계 지향, CDR 보호·위치 고정. 단점: 반복 탐색이라 계산 부담, 분류기 결정경계로 밀어붙이는 경향, 상대적 신규.
- 근거: `biophi/.../humanization/methods/humanization.py`(argmax + CDR graft), `Humatch/Humatch/humanise.py`·`model.py`(CNN + single-point search).

### 6.3.2 BioPhi/Sapiens vs AnthroAb — 학습 데이터·모델 구조·크기, CDR

둘은 **API가 동일**합니다(둘 다 `RobertaForMaskedLM`, `predict_scores`/`predict_masked`/`predict_best_score`) — AnthroAb README가 "Sapiens 인터페이스·기능을 그대로 따른다"고 명시합니다. 차이는 **데이터와 덩치**입니다.

| | BioPhi/Sapiens (`prihodad/biophi-sapiens1-vh`) | AnthroAb (`hemantn/roberta-base-humAb-vh`) |
|---|---|---|
| 구조 | RoBERTa, **4층 / 128차원** / 8 heads / FFN 256 | RoBERTa-base, **12층 / 768차원** / 12 heads / FFN 3072 |
| 가중치 크기 | **~2.2 MB** (≈0.5M params) | **~164 MB** (≈85M params) |
| max position | 146 | 192(VH) / 145(VL) |
| 학습 데이터 | OAS 항체 레퍼토리 (BioPhi/Sapiens, Prihoda 2022) | **human OAS (≤2025)** 에서 from scratch (README) |
| CDR | BioPhi 파이프라인이 **자동 보호**(parental CDR graft + Vernier 옵션) | 모델 자체엔 보호 없음 — `predict_best_score`(자동)는 **CDR 포함 전체 변경**, `predict_masked`만 마스킹 자리 변경(§6.2.1) |

→ 한 줄 요약: **AnthroAb는 Sapiens 설계를 그대로 따르되, 약 75배 큰 RoBERTa-base로 더 최신 human OAS에 재학습한 버전**입니다. 단 CDR 보호가 BioPhi처럼 파이프라인에 내장돼 있지 않으니 §6.2.1의 두 모드 구분이 중요합니다.

- 근거: HF config(`prihodad/biophi-sapiens1-vh` 4L/128H vs `hemantn/roberta-base-humAb-vh` 12L/768H), 가중치 `model.safetensors` 2.2MB vs 164MB, AnthroAb README.

### 6.3.3 BioPhi의 argmax 방법 vs softmax 방법 — 차이 및 장단점

BioPhi/Sapiens는 위치별 **softmax 확률분포**를 만든 뒤, 그 분포를 **어떻게 쓰느냐**에서 갈립니다.

| | argmax (BioPhi 기본) | softmax (sampling) |
|---|---|---|
| 방식 | 위치별 **최고 확률 잔기** 선택(greedy) | 분포에서 **확률적으로 샘플**(temperature) |
| 결과 | 결정적 **단일 서열 1개** | 같은 자리에서 **다양한 후보 다수** |
| 다양성 | 없음 | temperature↑ → 다양성↑, T→0 ≈ argmax |
| 용도 | "최대 사람화" 1안, 재현성 | 후보 라이브러리 생성 → downstream 스크리닝 |

- **argmax** — 장점: 결정적·재현 가능, "가장 사람다운" 단일 답. 단점: 후보 1개뿐, 더 나은 대안을 놓칠 수 있음.
- **softmax(sampling)** — 장점: 후보 다양성(스크리닝용 라이브러리), 분포 탐색. 단점: 시드 의존 확률적, 낮은 확률(위험) 잔기 포함 가능 → downstream 필터링 필수.
- 근거: `biophi/.../humanization.py`는 `pred.idxmax(axis=1)` = **argmax만** 구현(BioPhi 기본). softmax 샘플링은 동일 확률출력의 대안적 사용으로, 동일 인터페이스의 Sapiens/AnthroAb에서 실측(`ANTHROAB_ARGMAX_SOFTMAX_COMPARISON.md`: argmax H=10개 고정 mutation, softmax T=1=시드마다 11~15개).

> **주의 — BioPhi 자체는 argmax만 제공합니다.** softmax 샘플링은 같은 확률출력을 다르게 쓰는 방법으로, 동일 API의 Sapiens/AnthroAb에서 구현·검증했습니다. 어떤 방식이든 최종 후보는 구조·결합·발현 실험으로 검증해야 합니다.

---

## 이 챕터 핵심 요약

1. **Humatch**는 `allow_CDR_mutations=False`가 기본값 — CDR 보호가 도구에 **내장**돼 있고, CNN 점수 0.95를 목표로 framework를 반복 탐색합니다. 실측: VH 18 mut(CNN 0.972)·VL 2 mut, **CDR 변경 0개**.
2. **AnthroAb**는 두 모드가 정반대입니다 — `predict_best_score`(전체 변경, CDR 미보호) vs `predict_masked`(마스킹 자리만). 기본은 **커스텀 마스킹**.
3. 교차검증 실측: 10개 위치 중 Sapiens·AnthroAb가 합의한 건 **pos 78(I→T) 하나**, Humatch까지 더하면 **세 도구 합의 = `I78T`**.
4. 세 모델은 축이 다릅니다 — Sapiens(LM·확률행렬) · Humatch(CNN 탐색·paired) · AnthroAb(75배 큰 RoBERTa-base·targeted infilling).

<div class="pagebreak"></div>

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

<div class="pagebreak"></div>

# Ch.08 — 구조 검증: ABodyBuilder3 / ImmuneBuilder / AntiFold

서열 humanness가 좋아졌어도, **CDR loop 모양·VH/VL orientation·buried packing이 망가지면 결합력이 떨어집니다.** 그래서 parental과 humanized 후보의 구조를 모두 예측해서 비교합니다. 이건 "내가 만든 서열을 독립된 모델에게 다시 접어보게 한다"는 발상입니다 — **만든 사람과 검증하는 사람을 분리**하는 것입니다.

> **실습 — `08_structure_lab.ipynb`** · ① 직접 실행 → ② 내 결과 확인 → ③ 레퍼런스 대조 · **전 셀 7초**
>
> IgFold 로 parental·humanized 구조를 직접 예측하고 CDR-H3 RMSD 로 비교합니다.

---

## 8.1 실행 예시 〔본 환경 미실행 — GPU/모델 가중치〕

```bash
pip install ImmuneBuilder   # 설치는 최신 README 기준 확인
python predict_ab_structure.py --heavy H.fasta --light L.fasta --out candidate.pdb
```

> **정직한 표시 —** 이 챕터의 도구(ABodyBuilder3·ImmuneBuilder·AntiFold)는 **이 가이드를 검증한 환경에서 실행하지 않았습니다.** 그래서 구조 예측 수치는 싣지 않고, 명령 템플릿과 해석 기준만 제공합니다. 임의 값을 지어내지 않으려는 의도입니다. (도구별 실행 상태 → [부록 재현 환경](../11_appendix/11_appendix.md))

---

## 8.2 구조 비교 지표

| 비교 항목 | 기준 |
|---|---|
| CDR-H3 backbone RMSD | parental 대비 낮을수록 선호 (가장 중요) |
| CDR-L1/L2/L3, H1/H2 RMSD | canonical loop 유지 |
| VH/VL orientation | interface mutation 영향 |
| buried residue mutation | packing 불안정 여부 |
| solvent-exposed hydrophobic patch | aggregation risk |
| positive/negative charge patch | viscosity/clearance risk |

---

## 8.3 AntiFold로 backmutation 우선순위 잡기 〔본 환경 미실행〕

> **심화 —** AntiFold는 구조 기반 inverse folding으로, 각 자리에 "구조적으로 어떤 잔기가 허용되는지(residue tolerance)"를 알려줍니다. humanized 후보 구조에서 AntiFold가 "이 자리는 사람 잔기를 잘 허용 안 한다"고 하면, 그 자리가 backmutation 1순위 후보입니다. Sapiens mutation 목록과 AntiFold tolerance를 겹쳐 보면, "사람답게 바꾸고 싶지만 구조가 거부하는" 자리를 콕 집을 수 있습니다.

[Ch.01](../01_why_humanization/01_why_humanization.md)의 backmutation 우선순위 표(CDR 인접 → Vernier → interface → buried core …)를 AntiFold tolerance로 **데이터화**하는 셈입니다. 즉 "어디를 되돌릴까"를 감이 아니라 구조 모델의 점수로 정합니다.

---

## 이 챕터 핵심 요약

1. 서열 지표가 좋아져도 **CDR-H3 geometry·VH/VL orientation·packing이 깨지면 실패**입니다 — 만든 도구와 다른 도구로 검증합니다.
2. 가장 중요한 단일 지표는 **CDR-H3 backbone RMSD**(parental 대비).
3. **AntiFold**의 residue tolerance는 backmutation 후보 우선순위를 정하는 데 유용합니다.
4. 이 챕터 도구들은 **〔본 환경 미실행〕** — 명령 템플릿과 판정 기준만 제공합니다.

<div class="pagebreak"></div>

# Ch.09 — Developability 평가

후보를 humanness만으로 줄 세우면 안 됩니다. 발현·안정성·응집·점도 같은 **개발성(developability)** liability를 함께 봐야 합니다. **사람답지만 만들 수 없는 항체는 약이 못 됩니다.**

> **실습 — `09_developability_lab.ipynb`** · ① 직접 실행 → ② 내 결과 확인 → ③ 레퍼런스 대조 · **전 셀 1초**
>
> liability 모티프(N-glyc·deamidation·oxidation·isomerization)를 직접 스캔해 후보별 위험을 비교합니다.

---

## 9.1 무엇을 보나 — liability 지도

| 항목 | 예시 liability |
|---|---|
| Chemical liability | N-glycosylation `NXS/T`, deamidation `NG/NS`, oxidation `Met/Trp`, isomerization `DG` |
| Aggregation risk | exposed hydrophobic patch, high SAP |
| Charge risk | high pI, large positive patch, 비대칭 charge 분포 |
| Stability risk | buried polar mutation, proline/glycine disruption |
| Expression risk | non-natural motif, 비정상 framework residue |
| Polyspecificity | 큰 hydrophobic/positive paratope |

- **SAP**(Spatial Aggregation Propensity)는 구조 표면의 소수성 패치를 정량화합니다 — [Ch.08](../08_structure/08_structure.md)에서 예측한 구조가 있어야 계산됩니다.
- **charge patch**는 표면 전하가 한쪽으로 몰린 정도로, 점도(viscosity)·클리어런스 위험과 연결됩니다.

---

## 9.2 가장 흔한 사고 — humanization이 새 liability를 만든다

> **주의 —** humanization mutation이 **새 liability를 만들 수 있습니다.** 예를 들어 어떤 자리를 N으로 바꿨더니 바로 뒤가 S/T라서 `NXS/T` glycosylation motif가 새로 생기는 식입니다. 그래서 humanized 후보는 반드시 motif 스캔을 다시 해야 합니다.

**parental에 없던 모티프가 humanized 후보에 생겼는지**를 보는 게 핵심입니다. 서열 수준 스캔은 정규식 한 줄이면 되므로, 후보를 만들 때마다 자동으로 돌리세요.

```python
import re

MOTIFS = {
    "N-glycosylation": r"N[^P][ST]",   # NXS/T (X != P)
    "deamidation":     r"N[GS]",       # NG / NS
    "isomerization":   r"DG",
    "oxidation":       r"[MW]",
}

def scan(seq):
    return {name: [m.start() + 1 for m in re.finditer(p, seq)]
            for name, p in MOTIFS.items()}

# parental에 없던 자리만 = humanization이 새로 만든 liability
new_flags = {k: sorted(set(scan(humanized)[k]) - set(scan(parental)[k])) for k in MOTIFS}
```

> **그래프 —** `humanization_viz.liability_overview(rows, title, outpath)` 로 후보별 모티프 개수를 나란히 비교하면, "humanness는 올랐는데 liability도 같이 올라간" 후보가 바로 보입니다.

---

## 9.3 TAP — 임상 항체 분포와 비교하기 〔웹 전용, 본 환경 미실행〕

**TAP**(Therapeutic Antibody Profiler)는 임상단계 항체 분포와 비교해 developability flag를 줍니다. 단, TAP도 구조 예측 품질에 의존하므로 **절대값보다 후보 간 상대 비교**에 더 유용합니다.

---

## 이 챕터 핵심 요약

1. humanness가 높아도 **liability가 붙으면 약이 못 됩니다** — 랭킹에 developability를 반드시 포함하세요([Ch.10](../10_ranking_report/10_ranking_report.md)).
2. humanization은 **새 모티프를 만들 수 있습니다**(특히 신규 `NXS/T`) — parental 대비 **증분 스캔**이 정답입니다.
3. 구조 기반 지표(SAP·charge patch·TAP)는 Ch.08의 예측 구조 위에서 돌아가고, **후보 간 상대 비교**로 읽습니다.

<div class="pagebreak"></div>

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

<div class="pagebreak"></div>

# 부록 — 최종 체크리스트 · 참고자료 · 재현 환경 · 용어집

실습을 따라가다 보면 "그 도구 링크가 뭐였지?", "이 수치는 어디서 나온 거지?" 하고 다시 찾게 됩니다. 이 부록은 그럴 때 펴 보는 **레퍼런스 모음**입니다.

---

## A1. 최종 체크리스트

```text
[ 입력 QC ]  → Ch.04
□ VH/VL 정확히 분리됨
□ ANARCI numbering 성공 (scheme: IMGT)
□ germline assignment 확인 (V identity 낮은 체인 = humanization 여지 큼)
□ CDR 좌표 못 박음 (보호 대상 명확화)

[ 후보 생성 ]  → Ch.05·06
□ BioPhi/Sapiens 후보 생성
□ Humatch 후보 생성
□ AnthroAb targeted 후보 생성
□ 공통 mutation vs tool-specific mutation 분리

[ CDR·구조 보호 ]  → Ch.04·08
□ CDR 내 mutation 0개 (또는 명시적 근거 있음)  ← 가장 흔한 사고 지점
□ Vernier/interface residue backmutation 검토

[ 평가 ]  → Ch.05·07·08·09
□ OASis/humanness 개선 확인 (실측 예: VH 0.694→0.815)
□ AbNatiV nativeness 개선 확인
□ ABodyBuilder3/ImmuneBuilder 구조 예측 + CDR RMSD
□ developability liability(특히 신규 glycosylation motif) 스캔

[ 마무리 ]  → Ch.10
□ 최종 후보 5~20개 선정 (aggressive~conservative 스펙트럼)
□ 실험 검증 디자인 작성 (결합력 우선)
```

---

## A2. 참고자료

| 도구 | 링크 |
|---|---|
| BioPhi | https://github.com/Merck/BioPhi · web: https://biophi.dichlab.org/ |
| Sapiens | https://github.com/Merck/Sapiens (PyPI: `sapiens`) |
| Humatch | https://github.com/oxpig/Humatch · paper: https://pmc.ncbi.nlm.nih.gov/articles/PMC11610552/ |
| AnthroAb | https://github.com/nagarh/AnthroAb · VH: huggingface.co/hemantn/roberta-base-humAb-vh · VL: `...-vl` |
| Ab-RoBERTa | huggingface.co/mogam-ai/Ab-RoBERTa |
| Hu-mAb/SAbPred | https://opig.stats.ox.ac.uk/webapps/sabdab-sabpred/sabpred/humab |
| AbNatiV | https://gitlab.developers.cam.ac.uk/ch/sormanni/abnativ |
| ANARCI | https://github.com/oxpig/ANARCI (bioconda: `anarci`) |
| IgBLAST | https://www.ncbi.nlm.nih.gov/igblast/ |
| ABodyBuilder3 | https://github.com/exscientia/abodybuilder3 |
| ImmuneBuilder | https://github.com/oxpig/ImmuneBuilder |
| AntiFold | https://github.com/oxpig/AntiFold |
| TAP/SAbPred | https://opig.stats.ox.ac.uk/webapps/sabdab-sabpred/sabpred/tap |
| Thera-SAbDab | https://opig.stats.ox.ac.uk/webapps/sabdab-sabpred/TheraSAbDab |
| WHO 신규 mAb 명명법 | https://cdn.who.int/media/docs/default-source/international-nonproprietary-names-%28inn%29/new_mab_nomenclature-_2021rev.pdf |
| Lab-in-the-loop (Frey et al. 2025) | https://doi.org/10.1101/2025.02.19.639050 |

---

## A3. 재현 환경 (Reproducibility)

이 과정의 수치가 **어디서 나왔는지**를 밝혀 둡니다. 본문에는 실행 환경을 적지 않고, 하드웨어·버전 정보는 여기 한곳에 모았습니다.

| 항목 | 값 |
|---|---|
| 가이드 버전 | 0.4 · 2026-06 실제 실행 검증 |
| 검증 환경 | macOS (Apple Silicon, arm64) · conda/mamba · CPU (AbNatiV만 `mps`) |
| 실행·검증한 도구 | ANARCI · IgBLAST · Sapiens · Humatch · AnthroAb · AbNatiV (6종) |
| 예제 입력 | parental VH 120 aa / VL(lambda) 110 aa (mouse hybridoma 가정) |
| 미실행 도구 | ABodyBuilder3 · ImmuneBuilder · AntiFold(GPU) · TAP(웹 전용) |

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

### 핵심 실측값 요약

총 **6개 도구(ANARCI·IgBLAST·Sapiens·Humatch·AnthroAb·AbNatiV)를 실제로 설치·실행**해 수치를 뽑았습니다. 핵심 실측값은 다음과 같으며, 모두 일관된 한 가지 이야기를 가리킵니다 — **heavy chain은 비인간성이 뚜렷해 humanization 여지가 크고, lambda 경쇄는 이미 사람답다.**

- **germline identity** (ANARCI/IgBLAST): heavy IGHV1-69 **63%**, light IGLV1-40 **81%**. 중쇄 J는 `IGHJ6*01`/`IGHJ4*01` **동점**(85.71%)이라 도구마다 다르게 나옵니다(Ch.04).
- **humanness** (Sapiens): VH 0.694→**0.815**, VL 0.770→**0.872**. 단 이 화살표의 오른쪽 값은 **인간화 서열을 다시 스코어링한** 평균 self-probability입니다(정의를 바꾸면 0.782/0.851이 나옵니다 — Ch.05에 두 정의를 모두 적어 뒀습니다).
- **mutation 수**: Sapiens VH 21·VL 17 / Humatch VH 18·VL 2 (CDR 0개)
- **교차검증**: 세 도구가 똑같은 치환을 제안한 자리는 AnthroAb 모드에 따라 **7곳(best-score) 또는 12곳(FR-masked)**. `I78T`는 그중 **모드를 바꿔도 살아남는 가장 강건한 합의**입니다(Ch.06).
- **nativeness** (AbNatiV): **AbNatiV1** VH 0.6477→**0.8803**(FR 0.6317→0.9245), VL parental **0.9022** / **AbNatiV2** VH 0.4927→**0.7777**. 두 세대는 스케일이 달라 값이 다릅니다 — 섞어 읽지 마세요(Ch.07).
- **naturalness** (Ab-RoBERTa): paired mean log-prob — Sapiens **-0.4973** > AnthroAb(best-score) -0.5285 > parental -0.7240 > Humatch -0.7717

### 이전 판에서 바로잡은 값

이 과정을 만들면서 **모든 도구를 다시 돌렸고**, 그 결과 이전 판의 몇몇 수치가 재현되지 않아 실측값으로 교체했습니다. 재현되지 않은 것을 숨기지 않기 위해 여기 남깁니다.

| 항목 | 이전 판 | 실측 | 왜 달라졌나 |
|---|---|---|---|
| Ab-RoBERTa (Sapiens) | -0.6928 | **-0.4973** | 같은 방식으로 재계산했으나 값이 다름. parental·Humatch는 정확히 일치했으므로 계산 방식 문제는 아님 |
| Ab-RoBERTa (AnthroAb) | -0.8733 | **-0.5285**(best-score) | 위와 동일 |
| AbNatiV2 VH (인간화) | 0.6900 | **0.7777** | 0.6900은 어떤 후보에서도 나오지 않음(Humatch 0.6925가 가장 근접) |
| "3도구 합의는 `I78T` 하나뿐" | — | **7곳 또는 12곳** | 합의 개수는 AnthroAb 실행 모드에 따라 달라짐 |
| 중쇄 J 유전자 | `IGHJ4*01` | `IGHJ6*01`(ANARCI) | 85.71% 완전 동점 — 도구 tie-break 차이 |

나머지 값(germline V, CDR 6개, Sapiens 변이 21개 목록, humanness 0.694/0.770→0.815/0.872, Humatch CNN 0.972/1.000·CDR 0변이, AbNatiV1 7개 값, Ab-RoBERTa parental·Humatch)은 **문자·소수점 단위까지 재현**됐습니다.

GPU·웹 전용 도구(ABodyBuilder3·AntiFold·TAP)는 실행하지 않았고, 그 사실을 본문에 **〔본 환경 미실행〕** 으로 명시했습니다. 구조 검증은 대신 **IgFold(CPU)** 로 실제 돌려 Ch.08 랩을 구성했습니다.

---

## A4. 용어집 (Glossary)

- **VH / VL**: heavy·light chain의 variable domain. humanization의 작업 대상.
- **CDR**: complementarity-determining region — 항원과 직접 접촉하는 loop 3개(H1/H2/H3, L1/L2/L3). **보호 대상.**
- **CDR-H3**: 항원 결합에 가장 결정적인 loop. 여기 mutation이 들어가면 빨간불(본 가이드 예제: `ARRGRYGLYAMDY`).
- **FWR (framework region)**: CDR을 받쳐주는 구조적 뼈대. humanization이 실제로 바꾸는 영역.
- **Vernier zone**: CDR loop의 conformation을 아래에서 받쳐주는 framework 자리. 사람화하면 결합력이 흔들릴 수 있음.
- **VH/VL interface**: 두 도메인이 맞물리는 면. 여기 mutation은 페어링 orientation을 바꿀 수 있음.
- **paratope**: 항원과 실제로 접촉하는 잔기 집합.
- **CDR grafting**: murine CDR을 사람 framework에 이식하는 고전적 humanization.
- **backmutation**: 사람화한 framework 자리를 다시 원래(murine) 잔기로 되돌리는 것 — 결합력 복원용.
- **resurfacing**: 표면 노출 잔기만 사람 것으로 바꾸고 buried core는 보존하는 방식.
- **ADA / HAMA**: 항-약물 항체 / Human Anti-Mouse Antibody — 비인간 항체 투여 시의 면역 반응.
- **germline identity**: 가장 가까운 사람 germline V(J) 유전자와의 서열 일치율(%). 낮을수록 비인간적 = humanization 여지 큼.
- **IMGT / Kabat / Chothia / Martin / AHo**: 항체 numbering scheme. 이 가이드는 **IMGT** 기본.
- **humanness**: "사람 잔기를 얼마나 썼나" — Sapiens 확률·OASis %ile 등.
- **OASis**: 서열을 9-mer 펩타이드로 쪼개 OAS(Observed Antibody Space) 사람 항체에서의 관찰 빈도로 humanness를 매기는 BioPhi 지표.
- **nativeness**: "그 조합이 실제 사람 항체로서 얼마나 자연스러운가" — AbNatiV score(0~1).
- **naturalness**: 항체 언어모델이 본 서열의 그럴듯함 — Ab-RoBERTa **pseudo-log-likelihood**. humanness와 **다른 축**(Ch.07).
- **perplexity**: `exp(-mean_log_prob)`. 낮을수록 모델이 그 서열을 자연스럽다고 봄.
- **masked-LM (masked language model)**: 빈칸을 뚫고 그 자리에 올 잔기를 예측하는 모델(Sapiens·AnthroAb·Ab-RoBERTa).
- **argmax vs softmax(sampling)**: 위치별 최고 확률 잔기 하나를 고르기(결정적) vs 분포에서 확률적으로 뽑기(다양성).
- **infilling**: 마스킹한 자리만 채워 넣는 것(`predict_masked`).
- **paired CNN**: VH/VL을 함께 보고 페어링 타당성을 점수화하는 Humatch의 분류기.
- **inverse folding**: 구조 → 서열 예측. AntiFold가 residue tolerance를 주는 방식.
- **residue tolerance**: 특정 구조 자리에서 어떤 잔기가 구조적으로 허용되는지의 분포.
- **RMSD**: 두 구조의 좌표 차이(Å). CDR-H3 backbone RMSD가 humanization 구조 검증의 핵심 지표.
- **developability / liability**: 약으로 만들 수 있는 정도 / 그 위험 모티프(`NXS/T`, `NG`, `DG`, `M/W` 등).
- **SAP (Spatial Aggregation Propensity)**: 구조 표면 소수성 패치를 정량화한 응집 위험 지표.
- **charge patch**: 표면 전하가 몰린 영역. 점도·클리어런스 위험과 연결.
- **TAP (Therapeutic Antibody Profiler)**: 임상단계 항체 분포와 비교해 developability flag를 주는 웹 도구.
- **lab-in-the-loop**: 예측 → wet 검증 → 재학습을 반복하는 closed-loop 항체 설계 시스템.
- **source substem (`-o-/-xi-/-zu-/-u-`)**: 옛 INN 명명법에서 항체 유래를 나타내던 어미. **2021 신체계에서 폐지**(Ch.02).

---

본문으로 → **[00. 과정 개요](../00_README.md)**
