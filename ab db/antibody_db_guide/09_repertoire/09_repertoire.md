---
title: "Ch.09 — repertoire & naturalness (OAS)"
chapter: 9
level: hands-on
language: ko
part: B
---

# Ch.09 — repertoire & naturalness (OAS)

후보 항체가 "자연 human 항체 레퍼토리에서 정상 범위인가?"를 보는 게 **naturalness** 분석이에요. 비정상적으로 긴 CDR3, 희귀한 V gene, 이상한 motif는 발현·안정성·면역원성 위험 신호일 수 있거든요. 이 챕터는 **진짜 OAS(Observed Antibody Space) data unit을 직접 내려받아** CDR3 길이 분포를 그리고, 후보 항체가 어디쯤 위치하는지 봐요.

> **실습 — [`09_repertoire_lab.ipynb`](09_repertoire_lab.ipynb)** · **전 셀 실행 8초** — OAS data unit을 **직접 다운로드**해 `my_run/` 에 CDR3 분포를 집계하고, 후보의 CDR-H3 길이(ANARCI로 직접 계산)를 분포 위에 얹어요.

---

## 9.1 OAS와 naturalness — data unit 직접 받기

OAS는 10억+ 서열의 자연 항체 repertoire DB예요(Ch.02).[3][4] 핵심 가치는 **"자연 항체 서열 공간"**을 제공한다는 것 — 후보가 이 공간 안에 있으면 "사람 항체스럽다"는 신호예요.

주요 활용:

- **CDR-H3 길이 분포**: 후보 길이가 자연 분포 안인지
- **naturalness**: de novo 후보가 비정상 motif를 갖는지
- **V/J gene usage**: 후보 germline이 흔한지 희귀한지
- humanization·언어모델 학습 corpus

OAS는 **data unit**(study × run × 사슬 × isotype) 단위로 gzip CSV를 공개해요. 노트북이 받는 unit은 이거예요.

```bash
python scripts/fetch_oas_unit.py --out my_run/oas_subset.tsv.gz
python scripts/oas_cdr3_length.py my_run/oas_subset.tsv.gz --column cdr3_aa \
  --out my_run/oas_cdr3_length_summary.csv
```

| 항목 | 값 |
|------|-----|
| Data unit | `Eliyahu_2018 / ERR2843400_Heavy_IGHM.csv.gz` |
| 출처 | OAS unpaired (`opig.stats.ox.ac.uk/webapps/ngsdb/unpaired/…`) |
| 메타데이터 | Species **human** · BSource **PBMC** · BType **Unsorted-B-Cells** · Chain **Heavy** · Isotype **IgM** · Disease **HCV** |
| 서열 수 | **17,807** (전부 productive) · 원본 10 MB, 슬림 TSV 140 KB |
| 취득일 | 2026-07-14 (`data/oas_subset.tsv.gz` = 그날 받은 **진짜 OAS 데이터** 사본) |

> **주의** — **OAS 원본 CSV는 첫 줄이 메타데이터(JSON 한 줄)** 이고 둘째 줄이 헤더예요. 그냥 `pd.read_csv` 하면 컬럼을 못 찾습니다 — `skiprows=1` 이 필요해요(스크립트가 자동 감지합니다).

> **주의 — 이 unit의 한계를 알고 쓰세요.** 이건 **HCV 코호트 피험자 1명(subject CI15)의 IgM 레퍼토리**예요. "인간 레퍼토리 일반"의 대표값이 아니라 **한 사람의 한 시점 샘플**입니다. 교육·감(感) 잡기에는 충분하지만, 실전 benchmark라면 **여러 건강 도너의 여러 data unit**을 합쳐 쓰세요(같은 스크립트에 `--url` 만 바꾸면 됩니다).

---

## 9.2 실행 결과 — CDR3 길이 분포에서 후보의 위치

받은 unit **17,807 서열**의 CDR3(IMGT 정의) 길이 분포예요.

![OAS data unit heavy CDR3 길이 분포와 후보 위치](09_cdr3_length.png)

*그림. OAS data unit(Eliyahu 2018, human IgM heavy, 17,807 서열)의 CDR3 길이 분포. 가로축은 CDR3 길이(aa), 세로축은 해당 길이의 서열 수(파란 막대). 빨간 점선은 분포 평균(13.9 aa), 주황 실선은 후보 demo 항체의 CDR-H3 길이(13 aa) 위치. (이미지: `09_cdr3_length.png`)*

**그림 읽는 법** — 분포는 **14 aa 봉우리**를 중심으로 한 종형(오른쪽 꼬리가 긴) 모양이에요 — 실제 인간 heavy CDR3 길이 분포의 전형이죠. 후보(주황 실선, 13 aa)는 봉우리 바로 왼쪽, 즉 **분포의 한복판**에 있어요(하위 46 percentile). 그래서 "길이 측면에서 이 후보는 자연 human 항체와 다를 바 없다 = naturalness 정상"으로 읽어요. 만약 주황선이 오른쪽 꼬리 끝(예: 30 aa)에 찍혔다면 "비정상적으로 긴 CDR3 → 발현·안정성·면역원성 점검 필요" 경고였을 거예요. 반대로 너무 짧아도(왼쪽 꼬리) 결합 표면이 부족할 수 있고요. 단, 분포 중앙이라고 무조건 좋은 항체란 뜻은 아니에요(9.3 참고) — 어디까지나 "정상 범위"라는 신호일 뿐이에요.

| 통계 | 값 |
|------|-----|
| n (서열 수) | 17,807 |
| 평균 CDR3 길이 | 13.9 aa (최빈값 14 aa) |
| 범위 | 1 – 36 aa |
| 후보(demo) CDR-H3 | **13 aa** (IMGT: `NAGHDYDRGRFPY`) → 하위 **46 percentile** |

> **주의** — **길이를 잴 때 정의를 맞추세요.** OAS의 `cdr3_aa` 는 **IMGT CDR3(105–117, 양쪽 앵커 제외)** 이에요. 그래서 후보 항체도 **같은 IMGT 정의**로 재야 해요(노트북이 `abnumber` 로 직접 계산 → 13 aa). Kabat/Chothia CDR-H3로 재면 길이가 달라져서 **엉뚱한 percentile**이 나옵니다.

> **심화** — 분포 왼쪽 끝에 1~4 aa 짜리가 4건 있어요(전체의 0.02%). 실제 항체라기보다 **시퀀싱/어노테이션 노이즈**로 보는 게 맞고, 이런 꼬리를 어떻게 처리할지(자를지 남길지) 정하고 **보고서에 밝히는 것**이 repertoire 분석의 기본기예요. 이 과정에서는 자르지 않고 그대로 집계했습니다(그래서 최솟값이 1로 찍혀요).

---

## 9.3 주의 — naturalness 해석의 함정

- OAS는 **sequencing repertoire DB**예요 — 실험적 affinity를 직접 알려주지 않아요.
- 자연에서 **흔하다고 좋은 항체**라는 뜻이 아니에요(흔한 게 안전하다는 신호일 뿐).
- 자연에서 **드물다고 반드시 나쁜 후보**도 아니에요 — 신규성이 강점일 수도 있어요. 다만 "왜 드문지" 설명할 수 있어야 해요.

> **심화** — 그래서 naturalness는 **단독 판정이 아니라 다른 축과 함께** 봐요. 예: CDR3가 자연 범위 + humanness 높음(Ch.05) + liability 깨끗(Ch.08) + 구조 신뢰도 높음(Ch.06) → 균형 잡힌 후보. Thera-SAbDab의 임상 항체 분포와 비교하면 더 강력한 benchmark가 돼요.

---

## 9.4 통합 — 후보 항체 종합 triage

이 과정의 모든 분석을 한 후보에 모으면 이렇게 돼요(demo 항체 실측 종합).

| 축 | 챕터 | demo 항체 실행 결과 | 판정 |
|----|------|----------------|------|
| numbering·germline | 04 | 중쇄 = 마우스(IGHV14-4*02) / 경쇄 = human IGKV1-39*01 | 주의 — 중쇄 humanize 필요 |
| humanness | 05 | H 0.710 / L 0.902, 중쇄 17변이 | 주의→양호 (humanized) |
| 구조 신뢰도 | 06 | mean 0.3–0.4 Å, CDR-H3 2.65 Å | 양호 (H3만 주의) |
| interface | 07 | CDR-H2·H3 paratope (1A14 예시) | 양호 CDR 주도 |
| developability | 08 | Cys paired, motif 0건 | 양호 깨끗 |
| naturalness | 09 | CDR-H3 13 aa (46 percentile) | 양호 정상 |

> **심화** — 한 줄 결론: demo 항체는 **결합·구조·developability·naturalness는 양호하지만 중쇄가 마우스라 humanization이 필요**한 후보예요. 이렇게 여러 축을 한 표로 모으는 게 좋은 항체 분석 보고서의 핵심이에요(Ch.10).

---

### 이 챕터 핵심 요약

1. OAS는 **자연 항체 서열 공간** — 후보가 그 안에 있는지(naturalness)를 봐요. **data unit은 URL 하나로 직접 받을 수 있어요.**
2. 실행 결과: 실제 OAS unit 17,807 서열의 CDR3 평균 **13.9 aa**, demo CDR-H3(**13 aa**, IMGT)는 **46 percentile = 분포 중앙**.
3. **정의를 맞추세요** — OAS `cdr3_aa` 는 IMGT 기준. 후보도 IMGT로 재야 percentile이 의미 있어요.
4. **데이터의 출처와 한계를 밝히세요** — 이 unit은 HCV 코호트 한 명의 IgM 레퍼토리예요. 실전 benchmark는 여러 도너·여러 unit으로.
5. naturalness는 **단독 판정 금지** — 흔함≠좋음, 드묾≠나쁨. 다른 축과 함께.
6. 모든 챕터 분석을 **한 triage 표**로 모으면 후보의 강점·약점이 한눈에.

다음 → **[10. 부록 — mini-pipeline·보고서 체크리스트·용어집](../10_appendix/10_appendix.md)**
