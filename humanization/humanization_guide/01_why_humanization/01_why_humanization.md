---
title: "Ch.01 — 항체 humanization, 왜 하고 무엇을 지켜야 하나요?"
chapter: 1
language: ko
part: A
---

# Ch.01 — 항체 humanization, 왜 하고 무엇을 지켜야 하나요?

mouse 항체가 실험실에서는 항원에 기가 막히게 잘 붙어요. 그런데 사람 몸에 넣는 순간 이야기가 달라져요. 면역계가 그걸 "남의 단백질"로 귀신같이 알아보거든요. 그래서 서열을 사람답게 고쳐요. 그러다 결합력을 통째로 날려먹기도 하고요.

이 챕터에서는 humanization이 **왜** 필요한지, 그리고 왜 그게 "사람처럼 보이게 칠하는 일"이 아니라 **결합력과 사람다움 사이의 줄타기**인지를 짚어요. 항체 구조에서 건드려도 되는 자리와 절대 건드리면 안 되는 자리, 그리고 고전 해법인 CDR grafting·backmutation까지 훑을게요.

---

## 1.1 항체는 어떻게 생겼나요? — 손가락은 CDR, 손바닥은 framework

항체는 heavy chain과 light chain으로 이뤄져요. 항원에 달라붙는 일은 주로 variable domain, 그중에서도 **VH와 VL의 CDR1/2/3**가 맡아요. CDR이 항원과 직접 악수하는 손가락이라면, framework region(FWR)은 그 손가락을 받쳐주는 손바닥·손목이에요.

여기서 흔한 오해가 하나 나와요. "그럼 framework는 사람 것으로 다 갈아끼워도 되겠네?" 아니에요. framework 안에도 결합에 중요한 자리가 숨어 있어요. 대표적으로 네 종류예요.

| 숨은 자리 | 하는 일 |
|---|---|
| **Vernier zone** | CDR loop의 모양(conformation)을 아래에서 받쳐줘요 |
| **VH/VL interface residue** | 두 도메인이 맞물리는 면이에요 |
| **canonical loop determinant** | CDR의 표준 형태를 결정해요 |
| **buried core residue** | 안쪽에 파묻혀 패킹을 잡아줘요 |

이 자리들을 함부로 사람 잔기로 바꾸면 어떻게 될까요? 서열은 사람다워졌는데 정작 항원에 안 붙는 사태가 벌어져요. 사람다움 점수만 보고 좋아하다가 약을 잃는 셈이죠.

> **주의 —** framework를 통째로 사람화하면 사람다움 점수는 확실히 올라가요. 그런데 CDR을 받치던 자리까지 함께 바뀌면 결합이 무너져요. 실제로 그런 일이 벌어지는 걸 [Ch.05](../05_humanize_sapiens/05_humanize_sapiens.md)에서 직접 보게 돼요.

---

## 1.2 그래서, humanization은 왜 하나요? — ADA/HAMA와 네 가지 균형

가장 근본적인 질문부터 볼게요. 비인간 항체를 사람 몸에 넣으면 무슨 일이 생길까요?

우리 면역계는 남의 단백질을 그냥 두지 않아요. mouse 유래 항체를 사람에게 투여하면 **항-약물 항체(ADA)** 반응이 생겨요. 옛날 표현으로는 **HAMA(Human Anti-Mouse Antibody)**죠. 그다음은 도미노예요.

- 약이 금방 제거돼서 **반감기(PK)가 짧아져요**
- 효능이 떨어지거나 **알러지·아나필락시스 같은 안전성 문제**가 생겨요
- 결국 **규제 승인**도 어려워져요

그래서 humanization의 진짜 목표는 "사람처럼 보이기" 하나가 아니에요. 네 가지의 **균형**이에요.

- 사람 항체 레퍼토리에 가까운 sequence profile 확보 (면역원성 ↓)
- CDR/paratope geometry 유지 (결합력 유지)
- 발현량·안정성·용해도 확보, aggregation 위험 ↓ (개발성)
- 제조 가능성·규제 적합성 개선

쉽게 비유하면 번역이에요. **외국어를 현지인처럼 자연스럽게 다듬되, 원문의 핵심 메시지는 한 글자도 바꾸지 않는 번역**이죠. 문장을 매끄럽게 고치다가 정작 뜻이 바뀌면 그건 번역 실패예요.

---

## 1.3 CDR grafting과 backmutation — 고전이지만 여전히 핵심

가장 고전적인 humanization은 **CDR grafting**이에요. murine 항체의 CDR을 통째로 떼어내요. 그리고 사람 germline(또는 사람 acceptor framework) 위에 이식해요. 손가락(CDR)은 그대로 두고 손바닥(framework)만 사람 것으로 바꾸는 셈이에요.

그런데 이렇게만 하면 결합력이 뚝 떨어지는 경우가 많아요. 왜 그럴까요? 사람 framework가 원래 CDR loop를 받쳐주던 미묘한 받침대 역할을 못 하기 때문이에요. 그래서 **backmutation**을 해요. framework의 일부 자리를 원래 murine 잔기로 되돌리는 작업이죠. 어디를 되돌릴지는 보통 이 순서로 검토해요.

| 우선순위 | 되돌림 후보 위치 | 이유 |
|---:|---|---|
| 1 | CDR 바로 인접 framework residue | CDR 모양에 직접 영향 |
| 2 | Vernier zone residue | loop conformation 받침대 |
| 3 | VH/VL interface residue | 두 도메인 페어링 유지 |
| 4 | buried core residue | 패킹 안정성 |
| 5 | canonical loop 지지 residue | 표준 loop 형태 유지 |
| 6 | 항원과 직접 접촉하는 framework residue | 드물지만 결정적 |

위쪽일수록 CDR 모양에 직접 영향을 줘요. 그래서 상위 후보부터 하나씩 되돌리며 결합력이 돌아오는지 확인해요. 반대로 되돌리는 자리가 늘어날수록 사람다움은 다시 내려가요. 이게 바로 줄타기예요.

> **심화 —** 요즘은 grafting 대신 **resurfacing**도 써요. 표면 노출 잔기만 사람 것으로 바꿔 면역원성을 낮추고 buried core는 보존하는 방식이에요. 사람 germline framework에 직접 맞추기도 하고요. BioPhi/Sapiens·Humatch 같은 **데이터 기반 자동 humanization**이 이 가이드가 다루는 현대적 방법이에요.

---

## 이 챕터 핵심 요약

1. 항원 결합은 **VH/VL의 CDR**이 담당해요. 하지만 framework에도 **Vernier zone·VH/VL interface·canonical determinant·buried core** 같은 "건드리면 안 되는" 자리가 숨어 있어요.
2. humanization의 목적은 면역원성(ADA/HAMA)을 줄이는 거예요. 다만 그 대가로 **결합력을 잃으면 실패**예요.
3. 고전 해법은 **CDR grafting + backmutation**이에요. 현대 해법은 데이터 기반 자동 humanization(Ch.05~07)이고요. 원리는 똑같아요. **CDR은 지키고 framework를 사람화한다**예요.

---

다음 → **[02. 명명법·도구 지도·전략](../02_nomenclature_strategy/02_nomenclature_strategy.md)**
