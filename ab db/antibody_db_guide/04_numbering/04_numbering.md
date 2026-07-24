---
title: "Ch.04 — numbering & germline (ANARCI)"
chapter: 4
level: hands-on
language: ko
part: B
---

# Ch.04 — numbering & germline (ANARCI)

항체 서열을 받으면 가장 먼저 할 일은 "**어디가 CDR이고 어디가 framework인가**"를 정하는 것입니다. 그래야 그다음 모든 분석(humanization·interface·developability)이 같은 좌표 위에서 돌아가기 때문입니다. 이것을 해주는 표준 도구가 **ANARCI**입니다.[16]

이 챕터에서는 데모 항체(demo mAb)를 **여러분이 직접 ANARCI로** IMGT·Chothia numbering하고, V/J germline까지 할당해봅니다.

> **실습 — [`04_numbering_lab.ipynb`](04_numbering_lab.ipynb)** · **전 셀 실행 9초** — ANARCI를 **직접 실행**해 `my_run/` 에 numbering CSV를 만들고, 커밋된 레퍼런스 CSV와 셀 단위로 대조합니다.

---

## 4.1 ANARCI로 numbering하기 — 직접 실행

ANARCI는 항체·TCR variable domain을 IMGT·Chothia·Kabat·Martin·AHo로 numbering합니다. CSV로 받으면 각 위치가 컬럼이 되어 다루기 쉽습니다.

```bash
# IMGT numbering + germline 할당 (CSV) — 결과는 내 폴더(my_run/)에
ANARCI -i data/demo_mab.fa -s imgt --assign_germline --csv --outfile my_run/demo_imgt
# Chothia numbering
ANARCI -i data/demo_mab.fa -s chothia --csv --outfile my_run/demo_chothia
```

실행하면 사슬별 CSV가 생깁니다(`demo_imgt_H.csv`, `demo_imgt_KL.csv`). 노트북이 이 두 명령을 그대로 돌립니다.

---

## 4.2 실행 결과 — germline 할당

ANARCI `--assign_germline`이 붙여준 결과입니다(노트북에서 그대로 재현됩니다).

| 사슬 | chain type | V gene | V identity | J gene | J identity |
|------|-----------|--------|-----------|--------|-----------|
| Heavy | H | **IGHV14-4*02** (mouse) | 95% | IGHJ3*01 | 93% |
| Light | K (κ) | **IGKV1-39*01** (human) | 100% | IGKJ4*01 | 100% |

> **심화** — **핵심 발견**: heavy chain의 V gene이 **IGHV14-4**이며, 이것은 **마우스(mouse) germline 유전자**입니다(인간 IGHV는 1~7 패밀리). 즉 우리 demo 항체의 중쇄는 **murine 유래**라는 뜻입니다. 반면 경쇄는 **IGKV1-39\*01에 100% 일치**하는 human germline입니다. 이 비대칭이 다음 챕터(Ch.05)로 그대로 이어집니다. Sapiens도 중쇄만 "덜 사람스럽다"고 판정하고, humanize 시 중쇄만 고칩니다.

> **주의** — 노트북의 레퍼런스 대조에서 **bit score만 살짝 다를 수 있습니다**(예: 경쇄 193.1 vs 194.6). germline 할당(gene·identity)은 같은데 점수만 다르다면, 그것은 **ANARCI/HMM 프로파일 DB 버전 차이**입니다(레퍼런스는 2024.05, pip 최신은 2026.02). numbering 컬럼과 germline 이름이 같으면 정상입니다 — 보고서엔 **도구 버전을 함께 적으세요.**

> **참고** — 이 과정은 germline 레퍼런스로 **IMGT**를 표준으로 씁니다(ANARCI도 IMGT/GENE-DB를 참조). 다만 IMGT가 유일한 germline 목록은 아니라는 점만 알아두면 됩니다. 최신 repertoire 데이터에서 새로 발견된 allele은 **OGRDB**라는 곳에 따로 정리되므로, 나중에 희귀 유전자를 다룰 일이 있으면 이런 보완 레퍼런스가 있다는 것을 기억해두세요.[25]

---

## 4.3 IMGT vs Chothia — boundary가 정말 달라져요

Ch.01에서 "scheme을 꼭 명시하라"고 했습니다. 같은 demo 중쇄를 두 scheme으로 numbering하면 CDR-H1 경계에 들어가는 잔기 수가 실제로 달라집니다.

| scheme | CDR-H1 정의 구간 | demo 중쇄에서 점유 잔기 |
|--------|------------------|------------------------|
| IMGT | 27–38 | **8** 잔기 |
| Chothia | 26–32 | **7** 잔기 |

> **주의** — 그래서 "H31"이 어떤 scheme이냐에 따라 다른 위치를 가리킵니다. 보고서·mutation table에는 항상 **(IMGT)** 또는 **(Chothia)**를 명시하세요. 노트북에서 두 CSV의 같은 위치 잔기를 나란히 비교해봅니다.

---

## 4.4 Workflow — 서열을 받았을 때 가장 먼저 (QC)

ANARCI numbering은 항체 QC의 1단계입니다. 실전 순서는 다음과 같습니다.

1. FASTA header 정리(항체 ID·chain type)
2. **ANARCI로 chain type·numbering 확인** ← 이 챕터
3. IgBLAST/IMGT로 V/D/J germline 할당 (ANARCI `--assign_germline`로도 가능)
4. CDR sequence·length 추출
5. unusual residue·stop codon·ambiguous AA 확인 (Ch.08 liability_scan)
6. liability motif scan (Ch.08)
7. OAS·Thera-SAbDab reference와 비교 (Ch.09)
8. 구조예측 필요 여부 판단 (Ch.06)

| QC 항목 | Heavy | Light |
|---------|-------|-------|
| Chain type | H | κ |
| V gene | IGHV14-4*02 (mouse, 95%) | IGKV1-39*01 (human, 100%) |
| CDR3 (IMGT) | NAGHDYDRGRFPY (13 aa) | QQSYSTPLT (9 aa) |
| Numbering 성공 | 양호 | 양호 |
| Sequence length | 120 | 107 |

> **심화** — IgBLAST(NCBI)는 standalone 설치·germline DB 설정이 다소 복잡합니다. 이 과정에선 ANARCI `--assign_germline`으로 germline까지 한 번에 받았지만, 정밀한 D gene·junction 분석이 필요하면 IgBLAST 웹/standalone을 병행하세요.[17]

---

### 이 챕터 핵심 요약

1. ANARCI는 항체 numbering의 표준 도구이며, CSV로 받으면 각 위치가 컬럼이 됩니다. **노트북에서 직접 돌려 `my_run/` 에 만들었습니다.**
2. 실행 결과: demo 중쇄는 **마우스 germline(IGHV14-4*02, 95%)**, 경쇄는 **human IGKV1-39*01(100%)** → Ch.05 humanization 대상은 중쇄.
3. **IMGT(CDR-H1 27–38, 8잔기) vs Chothia(26–32, 7잔기)** 경계가 실제로 다르며, scheme 명시는 선택이 아니라 필수입니다.
4. 레퍼런스와 **bit score만 다른 것은 도구 버전 차이**이며, germline·numbering이 같으면 정상입니다. 보고서엔 도구 버전을 적으세요.
5. numbering은 모든 후속 분석의 공통 좌표계이며, QC의 1단계입니다.

다음 → **[05. humanness & humanization (BioPhi/Sapiens)](../05_humanness/05_humanness.md)**
