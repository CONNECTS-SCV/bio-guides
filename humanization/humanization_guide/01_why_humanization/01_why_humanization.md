---
title: "Ch.01 — 항체 humanization, 왜 하고 무엇을 지켜야 하나요?"
chapter: 1
language: ko
part: A
---

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

우리 면역계는 "남의 단백질"을 귀신같이 알아봅니다. mouse 유래 항체를 사람에게 투여하면 **항-약물 항체(ADA), 옛날 표현으로 HAMA(Human Anti-Mouse Antibody)** 반응이 생깁니다. 그러면.

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

---

다음 → **[02. 명명법·도구 지도·전략](../02_nomenclature_strategy/02_nomenclature_strategy.md)**
