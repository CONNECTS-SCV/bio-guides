---
title: "Ch.01 — 항체 기본 개념"
chapter: 1
level: intro
language: ko
part: A
---

# Ch.01 — 항체 기본 개념

본격적인 분석에 들어가기 전에, 항체가 어떻게 생겼고 왜 일반 단백질처럼 다루면 안 되는지부터 잡고 갈게요. 이 챕터의 용어들은 뒤의 모든 실습 챕터에서 계속 나오니까, 여기서 한 번 제대로 익혀두면 나머지가 훨씬 쉬워요.

> 이 챕터는 개념 위주라 노트북이 없어요. 다음 [Ch.02 DB landscape](../02_databases/02_databases.md)부터 실제 데이터를 만집니다.

---

## 1.1 항체란 무엇인가

항체는 B cell이 만드는 면역 단백질이에요. 특정 **항원(antigen)**을 알아보고 달라붙는 게 일이죠. 치료용 항체를 개발할 땐 "얼마나 세게 붙느냐(affinity)"만 보는 게 아니라, 표적 선택성·안정성·생산성·면역원성·용해도·응집 위험 같은 **developability** 요소를 같이 봐요.

항체 분석에서 가장 기본이 되는 단위는 이거예요.

| 용어 | 의미 | 분석에서의 중요성 |
|------|------|------------------|
| Antigen | 항체가 인식하는 표적 분자 | 항체 discovery와 epitope 분석의 출발점 |
| Antibody | 항원을 인식하는 면역 단백질 | 서열·구조·developability 분석 대상 |
| Epitope | 항원에서 항체가 인식하는 부위 | 중화능·선택성·escape mutation 분석에 중요 |
| Paratope | 항체에서 항원을 인식하는 부위 | CDR 중심의 binding interface |
| Affinity | 항체와 항원 간 결합 강도 | KD, kon, koff 등으로 표현 |
| Specificity | 원하는 항원만 선택적으로 인식하는 정도 | off-target·cross-reactivity 평가에 중요 |

> **주의** — 항체는 일반 단백질과 달라요. V(D)J recombination과 somatic hypermutation 때문에 서열이 엄청나게 다양하고, 결합 부위가 **CDR loop 중심**으로 구성돼요. 그래서 일반 단백질 numbering이나 단순 sequence alignment만으로는 구조적·면역학적 의미를 제대로 못 읽어요. 항체 전용 numbering(1.4)이 필요한 이유예요.

---

## 1.2 IgG 구조 — heavy/light chain, Fab, Fc

가장 널리 쓰는 치료용 항체 형식은 **IgG**예요. heavy chain 2개 + light chain 2개로 된 Y자 모양 단백질이죠.

| 구조 단위 | 설명 |
|-----------|------|
| Heavy chain | 긴 사슬. VH, CH1, hinge, CH2, CH3 domain 포함 |
| Light chain | 짧은 사슬. VL, CL domain 포함 |
| VH / VL | heavy/light chain의 variable domain |
| Fab | 항원을 결합하는 팔. VH/VL + CH1/CL |
| Fc | effector function·FcRn binding·half-life 관련 영역 |

항원 결합은 주로 **Fv(VH+VL) 영역과 CDR loop**가 담당해요. 반면 ADCC/CDC/FcRn binding 같은 effector·약동학 특성은 **Fc**가 맡아요. 전산 분석에서 다루는 단위는 보통 이거예요.

- **Fv**: VH + VL. 항원 결합 부위의 최소 구조 단위.
- **Fab**: Fv + constant domain. 구조 안정성·실제 복합체 분석에 유용.
- **scFv**: VH와 VL을 linker로 이은 single-chain format.
- **VHH/nanobody**: 단일 variable domain. 낙타과 항체 유래.

---

## 1.3 VH/VL, CDR, framework region

variable domain은 **framework region(FR)**과 **CDR(complementarity-determining region)**으로 나뉘어요. CDR이 항원과 직접 닿고, framework는 그 CDR loop의 위치·구조를 지지해요.

| Chain | CDR | 특징 |
|-------|-----|------|
| Heavy | CDR-H1, H2, H3 | **CDR-H3**가 다양성이 가장 크고 결합 특이성을 좌우 |
| Light | CDR-L1, L2, L3 | 항원 접촉 + VH/VL orientation 안정화 |

CDR-H3는 V·D·J segment가 만나는 junction에서 만들어져서 길이·서열 다양성이 극단적으로 커요. 많은 항체가 CDR-H3로 epitope 중심을 인식하지만, 전부 그런 건 아니에요 — light chain CDR이나 framework 근처 residue가 중요한 접촉을 만들기도 해요.

> **심화** — **CDR만 보존한다고 결합력이 유지되는 건 아니에요.** framework residue 일부는 CDR conformation·VH/VL packing·paratope geometry를 지지하거든요. humanization(Ch.05)이나 affinity maturation에서는 이런 residue를 **Vernier zone** 또는 **CDR-supporting residue**로 보고 조심히 다뤄요.

---

## 1.4 항체 numbering이 중요한 이유

항체 서열은 그냥 1번부터 센 잔기 번호로 비교하기 어려워요. 항체마다 CDR 길이가 다르고 insertion/deletion이 있거든요. 그래서 **numbering scheme**을 써요.

| Numbering scheme | 특징 | 주 사용처 |
|------------------|------|-----------|
| Kabat | sequence variability 기반 | 전통적 항체 문헌, 일부 특허 |
| Chothia | canonical structure·loop boundary 반영 | 구조 기반 분석 |
| IMGT | 표준화된 immunogenetics 체계 | germline, V/J assignment, 국제 표준 |
| AHo | 구조 비교용 균일 numbering | 다중 항체 구조 비교 |
| Martin / Enhanced Chothia | 구조 분석 개선 | ANARCI 등에서 지원 |

> **주의** — **보고서에 residue 위치를 쓸 땐 반드시 어떤 scheme인지 명시하세요.** 예를 들어 "H52"가 Kabat/Chothia에선 CDR-H2지만 IMGT에선 FR2예요 — scheme이 다르면 같은 번호가 다른 위치를 가리켜요. Ch.04에서 ANARCI로 직접 IMGT vs Chothia boundary 차이를 봅니다.

---

## 1.5 Epitope과 paratope

항체-항원 결합을 이해하려면 둘을 구분해야 해요. **epitope = 항원 쪽 표면 부위**, **paratope = 항체 쪽 표면 부위**.

- **Linear epitope**: 서열상 연속된 peptide 구간.
- **Conformational epitope**: 3D에서 가까이 모인 여러 residue. 서열상으론 멀 수 있음.

> **심화** — 치료용·중화 항체에서는 conformational epitope이 매우 중요해요. 그래서 서열만으로 epitope을 결론짓기보다, 구조·solvent accessibility·항원 conformational state·glycan shielding을 같이 봐야 해요. Ch.07에서 실제 복합체 구조로 epitope/paratope 잔기를 뽑아봐요.

---

## 1.6 Germline, V(D)J recombination, somatic hypermutation

variable domain은 germline V·D·J gene segment의 조합으로 만들어져요. heavy는 V+D+J, light는 V+J가 결합하고, 이후 항원을 만난 B cell이 **somatic hypermutation**으로 mutation을 쌓고 **affinity maturation**으로 잘 붙는 clone이 선택돼요.

germline 정보가 분석에서 중요한 이유:

1. 항체가 어떤 V/J gene family에서 왔는지 알 수 있어요.
2. humanization에서 적절한 human framework를 고를 수 있어요.
3. somatic mutation 정도를 추정할 수 있어요.
4. 특정 germline이 특정 항원 class에 반복 쓰이는지 분석할 수 있어요.
5. 후보 항체가 자연 human repertoire와 얼마나 닮았는지 평가할 수 있어요.

IgBLAST, IMGT/V-QUEST, OAS, BioPhi/OASis가 이 과정의 단골 도구예요(Ch.04·05·09).

---

## 1.7 Chimeric, humanized, fully human

치료용 항체는 인간 서열 비율·기원에 따라 나뉘어요.

| 유형 | 일반적 suffix | 설명 |
|------|---------------|------|
| Murine | -omab | mouse 유래 |
| Chimeric | -ximab | mouse variable + human constant |
| Humanized | -zumab | human framework에 비인간 CDR grafting |
| Human | -umab | fully human 또는 human platform 유래 |

> **주의** — 이 suffix 분류는 역사적인 것이고, 최신 INN naming(2021~)에서는 체계가 바뀌었어요. 개념 이해용으로만 쓰고, 규제 명명은 따로 확인하세요. **humanization의 핵심**은 면역원성을 줄이면서 결합 특성을 유지하는 것 — 단순히 CDR을 붙여넣으면 실패할 수 있고, CDR 구조를 지지하는 framework residue는 back-mutation 후보가 돼요(Ch.05).

---

## 1.8 Developability란

developability는 후보 항체가 **실제 약으로 개발될 수 있는 가능성**이에요. affinity가 좋아도 이게 나쁘면 생산·정제·제형·보관·투여에서 문제가 생겨요.

| 항목 | 위험 |
|------|------|
| Aggregation | 응집, 면역원성 증가 |
| Hydrophobic patch | 비특이 결합, 낮은 용해도 |
| Charge patch | 높은 viscosity, 비특이 결합 |
| Deamidation motif | N-G·N-S에서 chemical liability |
| Isomerization motif | D-G에서 구조 변화 |
| Oxidation | Met·Trp 노출 시 산화 |
| N-glycosylation motif | CDR 내 glycosylation → binding 영향 |
| Unpaired cysteine | mispairing·응집 위험 |
| Immunogenicity | T-cell epitope·non-human motif |

> **심화** — 좋은 후보는 affinity·specificity·developability의 **균형**을 가져요. 전산에서는 TAP·BioPhi/OASis·CamSol·SAP·liability scan을 조합해 초기 risk를 봐요 — 이걸 Ch.08에서 `liability_scan.py`로 직접 돌립니다.

---

### 이 챕터 핵심 요약

1. 항체 결합은 **Fv(VH+VL)의 CDR loop**가 담당, 특히 **CDR-H3**가 다양성·특이성의 핵심.
2. framework는 거의 고정이지만 **Vernier zone**처럼 CDR을 지지하는 residue가 있어 조심해야 해요.
3. 항체는 CDR 길이가 제각각이라 **numbering scheme(IMGT/Kabat/Chothia)**이 필수 — 위치를 말할 땐 scheme을 꼭 명시.
4. **germline·humanness·developability**가 치료 항체 분석의 3대 축이고, 뒤 챕터에서 도구로 하나씩 측정해요.

다음 → **[02. 항체 데이터베이스 landscape](../02_databases/02_databases.md)**
