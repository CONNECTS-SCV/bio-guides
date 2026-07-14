---
title: "Ch.02 — 명명법·도구 지도·전략·end-to-end 워크플로우"
chapter: 2
language: ko
part: A
---

# Ch.02 — 명명법·도구 지도·전략·end-to-end 워크플로우

`rituximab`은 chimeric, `trastuzumab`은 humanized. 이름 끝 몇 글자만 보고 항체 유래를 읽는 요령이에요. 그런데 최근 신규 후보명 앞에서는 이 요령이 통하지 않아요. **어미가 더 이상 유래를 말해주지 않거든요.** 규칙이 바뀐 줄 모르면 시작부터 이름을 잘못 읽어요.

Ch.01에서 "무엇을 지켜야 하는가"를 봤어요. 이번 챕터는 그 위에 판을 깔아요. 이름 규칙이 왜 끝났는지, 어떤 도구가 무슨 일을 하는지, 후보를 몇 개나 어떤 성격으로 만들지, 전체 파이프라인이 어떻게 굴러가는지를 차례로 봐요.

---

## 2.1 -ximab, -zumab, -umab — 이름만 봐도 알 수 있을까요?

결론부터 말하면 예전 약물명만 그래요. 신규 후보명은 아니에요. 왜 그렇게 됐는지 규칙과 사정을 함께 짚을게요.

### 옛 명명법: source substem

과거 monoclonal antibody INN(국제일반명) 명명법에서는 `-mab` 앞의 source substem이 항체의 유래를 나타냈어요.

| 어미 | 의미 | 일반적 해석 |
|---|---|---|
| `-omab` | murine antibody | 거의 mouse 서열 |
| `-ximab` | chimeric antibody | mouse variable + human constant |
| `-zumab` | humanized antibody | CDR 등 일부만 비인간 + 대부분 human framework |
| `-umab` | human antibody | human 서열 기반 |

그래서 `rituximab`은 chimeric(`-ximab`), `trastuzumab`은 humanized(`-zumab`)로 읽혔어요. 이 가이드에서 만드는 결과물도 개념상 `-zumab` 범주예요. CDR은 비인간 유래를 지키고 framework만 사람화하니까요.

### 2021년 새 명명 체계 — 왜 바뀌었고, 어떻게 바뀌었나

> **주의 —** 2017년부터 WHO INN은 신규 항체명에서 source substem(`-o-/-xi-/-zu-/-u-`)을 쓰지 않는 방향으로 바꿨어요. 2021년에는 `-mab` 어미 자체를 네 개의 새 접미사로 쪼갰고요. 별개의 두 변화지만, 이름으로 유래를 읽는 관행을 함께 끝냈어요.

바꾼 이유는 두 가지예요. 첫째, source substem이 부정확해졌어요. `-zu-`(humanized)와 `-u-`(human)의 경계가 흐려졌거든요. transgenic mouse나 phage display로 만든 항체는 사람 유래지만 완전한 human germline은 아니에요. 엔지니어링까지 섞이면 어미 하나로 가르기 어려워요.

둘째, `-mab`으로 끝나는 이름이 너무 많아졌어요. 발음도 구별도 어려웠죠. 게다가 단일클론항체가 아닌 새 형식까지 전부 `-mab`을 달았어요. 이중특이체나 fragment 말이에요. 그러면서 이름이 담던 정보가 사라졌어요.

그래서 2021년부터 신규 INN은 `-mab` 대신 다음 네 어미 중 하나를 써요.

| 새 어미 | 의미 | 적용 대상 |
|---|---|---|
| `-tug` | unmodified immunoglobulin | 표준 형식의 온전한 항체 |
| `-bart` | artificial antibody | 인공 설계·비천연 구성 항체 |
| `-mig` | multi-specific immunoglobulin | 이중·다중특이성 항체 |
| `-ment` | antibody fragment | Fab·scFv·VHH 등 fragment |

표를 자세히 보면 축이 완전히 바뀐 걸 알 수 있어요. 새 어미는 **유래(mouse/human)가 아니라 구조 형식(format)** 을 나타내요. `-zumab`처럼 humanized 여부를 이름만으로 알던 정보가 새 이름에는 아예 담기지 않아요.

그러니 "`-zumab`이면 무조건 humanized"라는 설명은 기존 약물명을 해석할 때만 유효해요. 최근 신규 후보명에는 적용되지 않아요. 유래는 이름이 아니라 **실제 서열을 ANARCI/IgBLAST로 분석해 판단**하세요([Ch.04](../04_sequence_qc/04_sequence_qc.md)). 우리 결과물은 개념상 humanized 항체지만, 최종 이름은 위 새 체계를 따르게 돼요.

---

## 2.2 Humanization 도구 지도 — 누가 무슨 일을 하나요?

도구가 많아서 처음엔 헷갈려요. 겁먹지 마세요. **후보를 만드는 도구**와 **후보를 평가·검증하는 도구**, 두 부류로 나누면 단순해져요.

### 후보를 만드는 도구 (generation)

| No. | 도구 | 역할 | 장점 | 한계 | 권장 용도 |
|---:|---|---|---|---|---|
| 1 | **BioPhi/Sapiens** | 자동 humanization + humanness 평가 | 오픈소스, 재현성, OAS 기반, Sapiens/OASis 통합 | 구조·결합력 보장은 아님 | 1차 후보 생성 |
| 2 | **Humatch** | gene-specific joint humanization | VH/VL 페어링까지 고려, 빠름 | 비교적 신규, 구조 검증 별도 | BioPhi와 병렬 후보 생성 |
| 3 | **AnthroAb** | RoBERTa masked-LM 기반 infilling | API·CLI 단순, position별 human-like residue 제안 | repo maturity 확인 필요, masking 설계 중요 | 교차검증, targeted mutation |
| 4 | Hu-mAb | legacy humanization/classifier | 개념 이해에 좋음 | SAbPred에서 humanization 비활성, Humatch 권장 | 역사·비교 섹션 |
| 5 | HuDiff/HuAbDiffusion | diffusion 기반 | 다양한 후보 | 연구용 성격 강함 | advanced/optional |
| 6 | IgCraft | human seq generation/inpainting | CDR motif scaffolding | 최신 연구용 | 후보 다양화 |

앞의 세 도구가 실무 주력이에요. 아래 세 개는 비교와 다양화용으로 알아두면 돼요.

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

이 중 실제로 돌린 도구를 밝혀둘게요. ANARCI·IgBLAST·Sapiens·Humatch·AnthroAb·AbNatiV 6종은 설치·실행해서 수치를 직접 뽑았어요. GPU나 웹 전용인 ABodyBuilder3·AntiFold·TAP·Hu-mAb 등은 **〔본 환경 미실행〕** 표시와 함께 정확한 명령 템플릿만 제공해요. 임의 값을 지어내지 않으려는 의도예요. 도구별 버전과 실행 환경은 [부록 재현 환경](../11_appendix/11_appendix.md)에 정리해 뒀어요.

---

## 2.3 Humanization 전략 — 어떤 후보 세트를 만들까요?

후보를 딱 하나만 만들어 "이게 사람화 결과예요" 하면 안 돼요. 자동 도구의 출력 하나는 **여러 가능한 답 중 하나**일 뿐이거든요. 실무에서는 한 parental 항체에서 공격적(aggressive)부터 보수적(conservative)까지 스펙트럼으로 여러 후보를 만들어 비교해요.

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

> **심화 — 왜 여러 도구를 같이 쓰나요?** BioPhi/Sapiens는 "서열 humanness" 축, Humatch는 "gene-specific + paired" 축, AnthroAb는 "targeted infilling" 축이에요. 축이 다른 세 도구가 같은 자리에 같은 사람 잔기를 제안하면, 그 mutation은 신뢰도가 높아요.

거꾸로 한 도구만 제안하는 mutation은 구조·결합 관점에서 한 번 더 따져봐요. ChatGPT·Claude·Gemini에게 같은 질문을 던지고 답이 겹치는 부분을 신뢰하는 것과 똑같은 발상이에요.

이 원칙은 [Ch.06](../06_cdr_safe_tools/06_cdr_safe_tools.md)에서 실제 수치로 확인돼요. 세 도구가 똑같은 치환을 제안한 자리는 실행 모드에 따라 **7곳 또는 12곳**이었어요. 그중 `I78T`는 모드를 바꿔도 살아남는 가장 강건한 합의였고요.

---

## 2.4 권장 end-to-end 워크플로우

이제 전체 그림을 쭉 훑어볼게요. 각 단계의 도구 사용법은 Ch.04부터 하나씩 깊이 들어가요.

### 입력 요구사항

최소한 이것만 있으면 시작할 수 있어요.

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

BioPhi/Sapiens와 Humatch를 **병렬로** 돌리는 게 기본값이에요. 여기에 AnthroAb를 더해 masked position별 residue 제안을 받아요. 공통 mutation은 우선 반영하고, 단독 제안 mutation은 따로 검토해요.

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

한 지표만 보고 순위를 매기지 마세요. 결합(CDR identity)·human-likeness·구조·개발성을 함께 봐야 후보가 제대로 갈려요.

### Step D — 구조 검증

ABodyBuilder3 또는 ImmuneBuilder로 parental과 humanized 후보 구조를 모두 예측하고 비교해요. complex 구조가 있으면 CDR conformation이 크게 흔들리는 후보를 낮은 rank로 내려요. 없으면 antibody-only라도 CDR-H3 geometry·VH/VL orientation·buried/interface mutation을 확인해요.

### Step E — 최종 후보 선정

5~20개를 남기고, §2.3의 조합으로 다양성을 확보해요. 그리고 이게 핵심인데, **in silico 결과는 출발점이지 결승선이 아니에요.** 최종 판정은 실험이 해요([Ch.10](../10_ranking_report/10_ranking_report.md)).

---

## 이 챕터 핵심 요약

1. 2021년 새 INN 체계에서 **어미는 유래가 아니라 형식(format)** 을 나타내요 — 이름으로 humanized 여부를 읽지 말고 **서열을 분석**하세요.
2. 도구는 **생성(BioPhi/Sapiens·Humatch·AnthroAb)** 과 **평가(ANARCI·IgBLAST·AbNatiV·구조·TAP)** 두 부류로 나눠 보면 단순해져요.
3. 후보는 하나가 아니라 **aggressive~conservative 스펙트럼 5~20개**로 만들고, **도구 간 합의(consensus) mutation**을 우선 신뢰해요.
4. 전체 흐름은 **QC → 생성 → 평가 → 구조 → 선정**, 그리고 마지막 판정은 실험이에요.

---

다음 → **[03. 환경 구성](../03_setup/03_setup.md)**
