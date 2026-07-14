---
title: "Ch.08 — 구조 검증: ABodyBuilder3 / ImmuneBuilder / AntiFold"
chapter: 8
language: ko
part: B
---

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

---

다음 → **[09. Developability 평가](../09_developability/09_developability.md)**
