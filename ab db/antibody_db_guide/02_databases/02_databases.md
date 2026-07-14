---
title: "Ch.02 — 항체 데이터베이스 landscape"
chapter: 2
level: intro
language: ko
part: A
---

# Ch.02 — 항체 데이터베이스 landscape

항체 분석은 결국 "어떤 DB에서 무엇을 가져오느냐"로 시작해요. 그런데 항체 DB는 종류가 많고 성격이 제각각이라, 먼저 **지도(landscape)**를 그려두는 게 중요해요. 이 챕터에서 DB들을 성격별로 분류하고, **공개 API로 항체-항원 복합체 스냅샷을 직접 받아** 표로 만들어 봅니다.

> **실습 — [`02_db_explore.ipynb`](02_db_explore.ipynb)** · **전 셀 실행 6초** — RCSB Search/Data API를 **직접 호출**해 항체-항원 복합체 12건의 스냅샷을 `my_run/` 에 만들고, 커밋된 레퍼런스 스냅샷과 대조해요.

---

## 2.1 항체 DB는 어떻게 분류하나

데이터의 **성격**으로 나누는 게 가장 이해하기 쉬워요.

| DB 유형 | 대표 DB | 주요 데이터 | 주 용도 |
|---------|---------|------------|---------|
| 구조 DB | SAbDab, IMGT/3Dstructure-DB, SAbDab-nano | 항체 구조, 항원-항체 복합체 | 구조 비교, epitope/paratope 분석 |
| 서열 repertoire DB | OAS, AIRR Data Commons, iReceptor | BCR/항체 서열 대량 데이터 | naturalness, germline, repertoire |
| 치료용 항체 DB | Thera-SAbDab | 임상/승인 항체 서열·메타데이터 | benchmark, developability 비교 |
| 질병·항원 특화 DB | CoV-AbDab, IEDB | 항원 특이 항체, epitope | 중화항체, epitope 분석 |
| affinity/mutation DB | AB-Bind, SKEMPI | mutation별 binding 변화 | affinity maturation, ΔΔG 예측 |
| 통합 분석 시스템 | abYsis | sequence/structure annotation | 항체-aware annotation |

한 줄 요약으로 외워두면 편해요.

- **SAbDab** = 구조를 찾는 곳 (Ch.06·07)
- **OAS** = 자연 항체 서열 공간을 보는 곳 (Ch.09)
- **Thera-SAbDab** = 치료용 항체 benchmark를 만드는 곳 (Ch.05)
- **AB-Bind / SKEMPI** = mutation이 결합력에 미치는 영향을 보는 곳
- **IEDB** = 항원 epitope 실험 데이터를 찾는 곳

---

## 2.2 SAbDab — Structural Antibody Database

SAbDab은 PDB의 항체 구조를 **consistent fashion으로 annotation**해 제공하는 대표 구조 DB예요.[1] 항체 chain·antigen chain·resolution·method·species·affinity·CDR length 같은 항체 분석용 필드로 검색할 수 있어요.[2]

SAbDab을 쓸 때 확인할 필드(노트북에서 체크리스트로 만들어요).

- PDB ID, heavy/light/antigen chain ID, resolution, antibody species, antigen type
- affinity value 존재 여부, bound/unbound 여부, CDR sequence/length

**SAbDab-nano**는 nanobody/VHH 구조를 모은 하위 resource예요. nanobody는 VH/VL pair 없이 단일 domain으로 항원을 인식해서, 긴 CDR3·concave epitope 접근성 등 설계 전략이 일반 항체와 달라요.

---

## 2.2b 직접 해보기 — 항체-항원 복합체 스냅샷 만들기

SAbDab·Thera-SAbDab 웹 UI는 스크립트로 바로 긁기 어려워요(JS 렌더링 앱이라 HTML만 돌아옵니다). 그래서 이 과정에서는 **같은 원본인 PDB**를 RCSB **Search API + Data API**로 직접 조회해 "SAbDab스러운" 요약 표를 만듭니다. 노트북이 하는 일이 이거예요.

```bash
python scripts/fetch_rcsb_ab_snapshot.py --rows 12 --out 02_databases/my_run/rcsb_ab_complexes.csv
```

- **검색 조건**: X-ray · 해상도 ≤ 2.5 Å · 단백질 entity ≥ 3 · full-text `"Fab antibody complex"`
- **정렬**: release date 오름차순(오래된 entry부터) → 시간이 지나도 목록이 잘 안 흔들려요
- **사슬 역할 파생**: entity 설명(`pdbx_description`)에 `HEAVY`/`LIGHT`가 있으면 그대로, 없으면(`"FAB NC10"` 같은 이름) 사슬 ID가 `H*`/`L*`인지로 추정

`data/rcsb_ab_complexes.csv` 는 **2026-07-14에 같은 스크립트로 받아 커밋해 둔 스냅샷**(대조군)이에요. 그날 조건에 맞는 entry는 **939건**이었고, 그중 오래된 12건이 아래예요.

| PDB | 공개일 | 해상도 (Å) | H | L | 항원 사슬 | 항원 |
|-----|--------|-----------|---|---|-----------|------|
| 1FDL | 1991-10-15 | 2.50 | H | L | Y | Hen egg white lysozyme |
| 1NCA | 1994-01-31 | 2.50 | H | L | **N** | Influenza N9 neuraminidase |
| 1TET | 1994-01-31 | 2.30 | H | L | P | Cholera toxin peptide 3 |
| 1VFB | 1994-05-31 | 1.80 | **B** | **A** | C | Hen egg white lysozyme |
| 1MLC | 1995-06-03 | 2.50 | B;D | A;C | E;F | Hen egg white lysozyme |
| 2HRP | 1997-12-31 | 2.20 | H | L | P;Q | HIV-1 protease peptide |
| 1KB5 | 1998-04-08 | 2.50 | H | L | B;A | KB5-C20 **T-cell 수용체** |

*(전체 12건은 `data/rcsb_ab_complexes.csv`. 노트북에서 직접 받아 이 표와 대조합니다.)*

> **주의** — **이 표 안에 함정이 세 개나 있어요.**
> ① **1VFB의 항체 사슬은 H/L이 아니라 B/A예요.** "항체=H/L"은 관례일 뿐 규칙이 아닙니다.
> ② **2HRP에는 항체가 두 벌(H/L, N/M)** 들어 있어요 — 여기서 chain **N은 항원이 아니라 중쇄**예요(1NCA에서는 N이 항원이었죠!).
> ③ **1KB5의 "항원"은 T-cell 수용체**예요 — full-text 검색은 이런 걸 같이 물어옵니다. 검색 결과는 항상 눈으로 검수하세요.
>
> 그래서 실전 규칙은 하나예요 — **chain ID를 직접 확인하고, 무엇이 항원인지 눈으로 보세요.** Ch.07에서 1A14를 열 때 이걸 그대로 겪습니다.

> **심화** — 같은 항체가 여러 PDB entry로 존재하고(1NCA/1NCB/1NCC가 그래요 — 같은 NC41 Fab–neuraminidase의 변이체 시리즈), biological assembly와 asymmetric unit이 다를 수 있어요. glycan·ligand·buffer·engineered mutation이 섞여 있을 수도 있고요.

---

## 2.3 OAS — Observed Antibody Space

OAS는 구조 DB가 아니라 **대규모 항체 repertoire 서열 DB**예요. 10억 개 이상의 sequence와 80개 이상 연구의 repertoire를 모았고[3], cleaned·annotated·translated된 unpaired/paired 서열을 제공해요.[4]

핵심 가치는 **"자연 항체 서열 공간"**이에요. de novo 설계나 humanization에서 후보 서열이 자연 human repertoire와 얼마나 가까운지 평가할 때 강력하죠. Ch.09에서 OAS 서브셋으로 CDR3 길이 분포를 그려 후보의 위치를 봐요.

> **주의** — OAS는 규모가 커서 전체 다운로드보다 **subset 분석**이 현실적이에요. unpaired/paired 구분, sequencing platform·species·disease state·isotype 메타데이터, 서열 중복·clonal expansion·sequencing error를 꼭 고려하세요.

---

## 2.4 IMGT/3Dstructure-DB

IMGT는 immunoglobulins·TCR·MHC를 다루는 국제 immunogenetics 표준 체계예요.[5] IMGT/3Dstructure-DB는 그 표준 안에서 면역 단백질 구조를 annotation해요. SAbDab과 비교하면.

| 항목 | SAbDab | IMGT/3Dstructure-DB |
|------|--------|---------------------|
| 중심 관점 | 항체 구조 실무 분석 | IMGT 표준 immunogenetics annotation |
| 강점 | chain·항원-항체 구조 검색, dataset 구축 | IMGT numbering, domain annotation, 표준 nomenclature |
| 활용 | 구조 기반 antibody engineering | germline/numbering 기준 통일 |

> **심화** — ANARCI의 IMGT scheme(Ch.04)이 바로 이 IMGT 표준 numbering을 따라요. germline 기준을 통일하고 싶으면 IMGT를 기준으로 잡으세요.

---

## 2.5 치료·질병 특화 DB

**Thera-SAbDab**은 WHO-recognized 치료용 항체와 single-domain 항체의 sequence·structure·metadata를 추적해요.[7] 후보 항체를 **임상 항체 분포와 비교(benchmark)**할 때 기준선이 돼요(Ch.05).

**CoV-AbDab**은 SARS-CoV-2·SARS-CoV-1·MERS-CoV에 결합하는 published/patented 항체·나노바디를 모은 public DB예요.[9][10] 중화항체 epitope class·escape mutation 분석에 좋아요.

**IEDB**는 NIAID가 지원하는 epitope DB로, antibody·T-cell epitope 실험 데이터를 catalog해요.[8] 단, epitope 중심이라 항체 서열·구조가 항상 들어있진 않아요 — 항원 epitope을 찾고 SAbDab 구조와 연결하는 식으로 쓰면 좋아요.

---

## 2.6 affinity·mutation DB와 통합 시스템

- **AB-Bind**: 32개 complex의 1,101개 mutant에 대한 실험 ΔΔG.[11] CDR mutation의 affinity 영향 학습·alanine scanning 해석용.
- **SKEMPI 2.0**: 항체 전용은 아니지만 구조 있는 PPI에서 mutation→binding/kinetics 영향 7,085건.[12] antibody-antigen subset으로 affinity maturation benchmark.
- **AIRR / iReceptor / VDJServer**: repertoire 데이터 표준화·검색·분석 생태계.[13][14]
- **abYsis**: 항체 서열·구조를 통합 annotation하는 web 시스템.[15]

> **심화** — AB-Bind는 antibody-focused, SKEMPI는 broader PPI mutation dataset이에요. 항체 affinity prediction을 검증할 땐 둘을 같이 보면 좋아요.

---

### 이 챕터 핵심 요약

1. 항체 DB는 **구조 / 서열 repertoire / 치료 / 항원 특화 / mutation / 통합**으로 나뉘어요.
2. 실무 4대 축: **SAbDab(구조) · OAS(서열) · IMGT(표준) · Thera-SAbDab(benchmark)** — 이 과정 제목이기도 해요.
3. 구조 스냅샷은 **RCSB Search/Data API로 직접** 뽑을 수 있어요(노트북에서 실행). 웹 UI가 막히면 API로 우회하세요.
4. 스냅샷을 직접 만들어 보면 배우는 것: **사슬 ID는 규칙이 아니라 관례**(1VFB=B/A), **같은 문자가 entry마다 다른 역할**(N=항원 vs 중쇄), **검색 노이즈**(TCR 복합체)가 섞인다는 것.
5. epitope을 찾을 땐 IEDB에서 정보를 얻고 SAbDab 구조와 연결하는 식으로 DB를 **조합**하세요.

다음 → **[03. 분석 환경 구축](../03_setup/03_setup.md)**
