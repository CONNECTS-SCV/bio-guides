---
title: "Ch.08 — developability (liability scan)"
chapter: 8
level: hands-on
language: ko
part: B
---

# Ch.08 — developability (liability scan)

항체가 항원에 잘 붙어도, **약으로 만들 수 없으면** 소용없어요. 응집·산화·이성질화·비특이 결합 같은 위험을 **developability**라고 하고, 후보 단계에서 미리 거르는 게 중요해요. 이 챕터에서 `liability_scan.py`로 demo 항체의 liability motif·물리화학 특성을 **직접 스캔**합니다.

> **실습 — [`08_dev_lab.ipynb`](08_dev_lab.ipynb)** · **전 셀 실행 3초** — liability scan을 **직접 실행**해 `my_run/liability.csv` 를 만들고, 커밋된 결과와 값이 완전히 같은지 대조해요.

---

## 8.1 developability risk 한눈에

| 항목 | 위험 | 스캔 방법 |
|------|------|-----------|
| Aggregation | 응집·면역원성 | hydrophobic patch, SAP |
| Deamidation | N-G·N-S에서 chemical liability | motif regex |
| Isomerization | D-G에서 구조 변화 | motif regex |
| Oxidation | Met·Trp 노출 산화 | Met/Trp count |
| N-glycosylation | CDR 내 glycosylation → binding 영향 | N-X-S/T sequon |
| Unpaired cysteine | mispairing·응집 | Cys count 홀짝 |
| Charge/pI | viscosity·비특이 결합 | pI 계산 |

`liability_scan.py`는 이 중 **motif·Cys·pI·GRAVY**를 빠르게 잡아줘요.

```bash
python scripts/liability_scan.py data/demo_mab.fa --out my_run/liability.csv
```

> **주의** — **robustness 보강**: QC 입력엔 가끔 `X`·`B`·`Z` 같은 모호 잔기가 섞여요. 원래 Biopython `ProteinAnalysis`는 여기서 예외로 죽는데, 이 저장소의 `liability_scan.py`는 모호 잔기를 `ambiguous_residues` 컬럼에 따로 기록하고 물리화학 계산은 표준 20종만으로 수행하도록 고쳤어요(Ch.03 정신 — 도구가 입력에 강건해야 함).

---

## 8.2 실행 결과 — demo 항체 liability scan

| 사슬 | length | pI | GRAVY | Cys (홀짝) | Trp | liability motif |
|------|--------|------|-------|-----------|-----|-----------------|
| demo_HC | 120 | 5.02 | −0.45 | 2 (짝, paired) | 4 | 없음 |
| demo_LC | 107 | 8.64 | −0.29 | 2 (짝, paired) | 1 | 없음 |

![demo mAb developability/liability 개요](08_liability_overview.png)

*그림. 2×2 패널로 본 demo 항체의 developability 지표. **좌상** 등전점 pI(주황, pH 7 기준선) · **우상** 평균 소수성 GRAVY(청록, 0 기준선) · **좌하** 시스테인 개수(보라, 짝수면 disulfide 짝맞음) · **우하** liability motif hit 수(누적 막대: N-glyc·deamidation NG/NS·isomerization DG). 가로축은 demo_HC / demo_LC. (이미지: `08_liability_overview.png`)*

**그림 읽는 법** — 좌상 pI 패널에서 중쇄(5.02)는 pH 7 기준선 아래(산성), 경쇄(8.64)는 위(염기성)로 갈려요 — 사슬 간 전하가 반대라 charge symmetry는 TAP로 따로 봐야 한다는 신호예요. 우상 GRAVY는 둘 다 0 아래(음수)라 평균적으로 친수성 → 용해도 측면 무난. 좌하 Cys 패널은 둘 다 정확히 2개(짝수)라 **unpaired cysteine 위험 없음**. 가장 중요한 건 우하 패널인데, **막대가 아예 비어 있어요** — deamidation·isomerization·N-glyc sequon이 0건이라는 뜻으로, 이 데모 항체는 **서열 liability가 깨끗**합니다. 만약 우하에 막대가 솟아 있고 그 위치가 CDR이라면, 결합력이 좋아도 임상 후보로는 위험 신호예요.

해석 포인트:

- **Cys 2개(짝수)** — 양쪽 다 도메인 내 disulfide가 짝이 맞아요. **unpaired cysteine 위험 없음**(홀수면 mispairing·응집 경고).
- **deamidation(N-G/N-S)·isomerization(D-G)·N-glyc sequon이 0건** — 이 데모 항체는 서열 liability가 깨끗한 편이에요.
- **pI**: 중쇄 5.02(산성) vs 경쇄 8.64(염기성) — 전하가 사슬 간 반대 방향. 전체 항체의 net charge·charge symmetry는 TAP 같은 도구로 따로 봐요.
- **GRAVY 둘 다 음수** — 평균적으로 친수성이라 용해도 측면은 무난.

> **심화** — **결합력(ipTM·affinity)만으로 후보를 고르면 안 돼요.** Ch.01에서 본 것처럼 affinity·specificity·developability의 **균형**이 핵심이에요. liability가 깨끗한 후보를 우선하고, 특히 **CDR 안에** Met/Trp(산화)·N-glyc sequon·NG/DG(불안정)가 몰려 있으면 임상으로 가기 어려워요.

---

## 8.3 TAP — 임상 기준 developability 프로파일

OPIG의 **TAP(Therapeutic Antibody Profiler)**는 variable domain 서열을 받아 ABodyBuilder2로 구조를 만들고, **임상 단계 항체 분포와 비교**해요.[23] TAP가 보는 5개 축:

- CDR length
- Surface hydrophobicity (PSH)
- Patches of positive charge (PPC)
- Patches of negative charge (PNC)
- Heavy/light chain charge symmetry (SFvCSP)

TAP 외에 병행하면 좋은 분석: sequence liability scan(이 챕터)·OASis humanness(Ch.05)·hydrophobic/charge patch 시각화·aggregation predictor·T-cell epitope prediction.

> **심화** — TAP는 "임상 항체 분포에서 벗어나는지"를 봐요. 벗어났다고 무조건 나쁜 건 아니지만, **왜 벗어났는지 설명하고 risk mitigation 전략을 제시**하는 게 좋은 보고서예요(Ch.10 체크리스트).

---

### 이 챕터 핵심 요약

1. `liability_scan.py` 실측: demo 항체는 **Cys 짝수(paired) + liability motif 0건**으로 서열 liability가 깨끗.
2. pI는 중쇄 5.0 / 경쇄 8.6으로 갈려요 — charge symmetry는 TAP로 별도 평가.
3. 도구는 입력에 강건해야 — **모호 잔기(X/B/Z)도 죽지 않게** 보강했어요.
4. 결합력만 보지 말고 **developability와 함께** — 특히 CDR 내 산화·glyc·불안정 motif를 경계.

다음 → **[09. repertoire & naturalness (OAS)](../09_repertoire/09_repertoire.md)**
