---
title: "Ch.09 — Developability 평가"
chapter: 9
language: ko
part: B
---

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

---

다음 → **[10. 후보 랭킹·GuideDB·실험 검증](../10_ranking_report/10_ranking_report.md)**
