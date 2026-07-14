---
title: "시각 자산 계획서 — PyMOL 구조 렌더링 & 보충 이미지 가이드"
purpose: "튜토리얼 전반에 들어갈 단백질 구조 그림(PyMOL)과 보충 이미지의 위치·내용·렌더링 방법·파일을 정리"
language: ko
---

# 시각 자산 계획서 (Figure Plan)

이 문서는 BoltzGen 고급 과정 전반에 **어디에 어떤 그림을 넣으면 좋은지**를 정리한 계획서예요. 두 종류로 나눠요.

- **(S) 구조 렌더링**: 실제 설계 결과 CIF를 PyMOL로 렌더링한 단백질 구조 그림. 파일·스타일·명령까지 명시.
- **(I) 보충 이미지**: 구조가 아닌 개념도·다이어그램·스크린샷 등.

모든 구조 파일은 각 챕터의 `data/<exp>/final_designs/rank01_*.cif`(바인더+타깃 복합체)를 씁니다.

---

## 공통 규약 (모든 구조 그림에 적용)

논문 Figure 색 규약을 따라요: **바인더 = 금색(gold), 타깃 = 파랑(blue)**.

PyMOL 공통 세팅(스크립트 맨 앞에):
```python
bg_color white
set ray_opaque_background, 0
set cartoon_fancy_helices, 1
set ray_shadows, 0
set antialias, 2
set cartoon_transparency, 0
# 색: 바인더 금색 / 타깃 파랑
# 인터페이스 강조: 주황 / 이황화: 노랑 / 리간드: 초록 / 핵산: 하늘+사다리
```

렌더링은 `ray 1600,1200` 후 `png <name>.png, dpi=300`. 각 그림은 해당 챕터 폴더에 저장(예: `07_peptide_cyclic/07_cyclotide_structure.png`).

> 바인더/타깃 체인 식별법: 메트릭 CSV의 `num_design`(설계 길이)와 길이가 일치하는 체인이 **바인더**, 나머지가 **타깃**이에요. 각 챕터 표에 식별 결과를 적어뒀어요.

---

## 챕터별 그림 계획

### Ch.01 — 툴의 이해

| 종류 | 위치 | 내용 | 파일/방법 |
|------|------|------|-----------|
| (I) | 1.1 도입 | **자물쇠-열쇠 비유** 일러스트 (타깃=자물쇠, 바인더=열쇠) | 개념도 |
| (I) | 1.5 아키텍처 | **공식 논문 Figure**(any-modality 입력 → BoltzGen→BoltzIF→Boltz-2 → all-atom 출력) | 논문 Fig.1 인용 또는 재작도 |
| (I) | 1.5 입력 표현 | **Atomic/Token/Pairwise Feature 3계층** 다이어그램 | 개념도(원자·잔기·잔기쌍 매트릭스) |
| (S) | 1.1 또는 1.5 | **any-modality 출력 몽타주**: 단백질-단백질 / 단백질-DNA / 단백질-소분자 복합체 3개를 나란히 (바인더 금색, 타깃 파랑) | 각각 `09_nanobody`(단백질), `11_nucleic_acid/data/dna`, `10_small_molecule` 의 rank01 CIF |

### Ch.02 — 입력 데이터 준비

| 종류 | 위치 | 내용 | 파일/방법 |
|------|------|------|-----------|
| (S) | 2.3 타깃 준비 | **타깃 구조 + 체인 색칠** (include/exclude 개념): PD-L1(7uxq) 체인별 색, 제거할 flexible loop를 빨강 표시 | `example/fab_targets/7uxq.cif` |
| (S) | 2.5 결합부위 | **결합부위 하이라이트**: 타깃 cartoon(회색) + binding 잔기를 주황 sticks/surface | 임의 타깃 CIF + `binding_types` 잔기 |
| (S) | 2.8 boltzgen check | **명세 시각화 CIF**: `boltzgen check`가 만든 CIF(타깃 + 설계 placeholder)를 PyMOL로 | `boltzgen check` 산출 `*.cif` |
| (I) | 2.3 어셈블리 | 비대칭 단위 vs 생물학적 어셈블리 개념도 | 개념도 |

### Ch.03 — 설치 및 접근

| 종류 | 위치 | 내용 | 파일/방법 |
|------|------|------|-----------|
| (I) | 3.3 CUDA 정합 | **드라이버↔torch↔cuequivariance↔cuBLAS 4층 스택** 다이어그램 | 개념도(본문 ASCII를 그림으로) |
| (I) | 3.3 케이스 | `nvidia-smi` / 오류 메시지 **스크린샷** | 터미널 캡처 |

### Ch.04 — 기본 사용법

| 종류 | 위치 | 내용 | 파일/방법 |
|------|------|------|-----------|
| (I) | 4.2 파이프라인 | **6스텝 파이프라인 흐름도** (각 스텝 산출물 표시) | 개념도(논문 Fig.b 스타일) |
| (S) | 4.6 출력 구조 | **최종 디자인 1개 복합체** (바인더 금색 cartoon + 타깃 파랑 surface) — "이런 게 나온다" | `05_result_interpretation/data/vanilla/final_designs/rank001_1g13prot_79.cif` |
| (I) | 4.6 | **출력 디렉토리 트리** 그림 | 개념도 |

### Ch.05 — 결과 해석 (구조로 메트릭 이해)

| 종류 | 위치 | 내용 | 파일/방법 |
|------|------|------|-----------|
| (S) | 5.2 신뢰도 | **pLDDT 색칠 구조**: rank1 디자인을 B-factor(pLDDT) spectrum(파랑=높음~빨강=낮음)으로 — pLDDT를 눈으로 | vanilla rank001 CIF, `spectrum b` |
| (S) | 5.4 인터페이스 | **인터페이스 + 수소결합**: 바인더-타깃 접촉면 잔기 sticks + H-bond 점선 — ipTM/H-bond를 시각화 | vanilla rank001, `distance ... mode=2` |
| (그래프) | 5.10 | 2×2 메트릭 개요 (이미 생성됨 `05_vanilla_metrics.png`) | 완료 |
| (I) | 5.10 | **상관관계 히트맵**, **Top-3 레이더 차트** | 노트북 `05_analysis_viz.ipynb`에서 생성 가능 |

### Ch.06 — 고급 활용

| 종류 | 위치 | 내용 | 파일/방법 |
|------|------|------|-----------|
| (I) | 6.1 | **계층적 스크리닝** 깔때기 다이어그램 (10k→200→20→top) | 개념도 |
| (I) | 6.4 | **필터 4노브**(metrics_override/additional_filters/size_buckets/alpha) 효과 비교 도식 | 개념도 |

### Ch.07 — 펩타이드·고리형 (구조 그림 최우선!)

| 종류 | 위치 | 내용 | 파일/방법 |
|------|------|------|-----------|
| (S)★ | 7.8 실측 결과 | **Cystine knot 고리형 펩타이드**: 고리 backbone + 이황화 3쌍 강조 (이 과정 최고의 구조 샷) | `07_peptide_cyclic/data/cyclotide/final_designs/rank001_3ivq_02.cif` (체인 A=cyclotide 34aa·Cys 4/13/20/26/30/32, 체인 B=타깃) |
| (I) | 7.3/7.4 | linear vs cyclic, 이황화 형성, cystine knot 매듭 개념도 (기존 part3_*.png 재활용 가능) | 보충 |

### Ch.08 — 항체 Fab

| 종류 | 위치 | 내용 | 파일/방법 |
|------|------|------|-----------|
| (S) | 8.7 실측 결과 | **Fab–PD-L1 복합체**: Fab(금색) framework + **CDR 루프 주황 강조**, PD-L1(파랑 surface) | `08_antibody_fab/data/fab/final_designs/rank01_pdl1_05.cif` (3체인: PD-L1 타깃 + Fab VH/VL) |
| (I) | 8.1 | 일반 항체 vs Fab vs 나노바디 구조 비교도 | 보충 |
| (I) | 8.5 | developability liability 모티프(MetOx/HydroPatch 등) 위치 개념도 | 보충 |

### Ch.09 — 나노바디

| 종류 | 위치 | 내용 | 파일/방법 |
|------|------|------|-----------|
| (S) | 9.6 실측 결과 | **나노바디–penguinpox 복합체**: 나노바디(금색, 체인 B 120aa) + **CDR3 루프 빨강**, 타깃(파랑 surface, 체인 A 201aa) | `09_nanobody/data/nanobody/final_designs/rank01_penguinpox_07.cif` |
| (I) | 9.1 | epitope–paratope 상호작용 개념도 | 보충 |

### Ch.10 — 소분자·친화도

| 종류 | 위치 | 내용 | 파일/방법 |
|------|------|------|-----------|
| (S)★ | 10.6 실측 결과 | **소분자 결합 포켓**: 설계 단백질(체인 A 142aa, 회색 cartoon + 포켓 surface 컷어웨이) + 리간드 TSA(체인 B, 초록 sticks) | `10_small_molecule/data/small_molecule/final_designs/rank01_chorismite_29.cif` |
| (I) | 10.4 | binding pocket / shape complementarity 개념도 | 보충 |

### Ch.11 — 핵산 (DNA·RNA)

| 종류 | 위치 | 내용 | 파일/방법 |
|------|------|------|-----------|
| (S)★ | 11.5 DNA 결과 | **Zinc finger–DNA 복합체**: 설계 단백질(금색, 체인 A) helix가 **DNA(파랑 cartoon+사다리, 체인 B/C) major groove에 삽입**, **H-bond 점선 다수**, Zn 이온(회색 구) | `11_nucleic_acid/data/dna/final_designs/rank01_zinc_finger_06.cif` (A=단백질, B/C=DNA, D~I=이온) |
| (S) | 11.6 RNA 결과 | **단백질–RNA 헤어핀**: 설계 단백질(금색, 체인 A 84aa) + RNA 헤어핀(파랑 cartoon, 체인 B 17nt) | `11_nucleic_acid/data/rna/final_designs/rank01_rna_spec_29.cif` |
| (I) | 11.2 | DNA major/minor groove, zinc finger Zn 배위(Cys2-His2) 개념도 | 보충 |

---

## 핵심 PyMOL 레시피 (복사해서 바로 사용)

### A. Cystine knot 고리형 펩타이드 (Ch.07) — 대표 샷

```python
load 07_peptide_cyclic/data/cyclotide/final_designs/rank001_3ivq_02.cif, cyc
hide everything
# 공통 세팅
bg_color white
set cartoon_fancy_helices, 1
set ray_shadows, 0
# 타깃(체인 B): 파랑 반투명 표면
select tgt, cyc and chain B
show surface, tgt
color marine, tgt
set transparency, 0.55, tgt
# cyclotide(체인 A): 금색 cartoon
select pep, cyc and chain A
show cartoon, pep
color yelloworange, pep
# 이황화 3쌍: SG 노란 구 + Cys 스틱 + 거리
select cyssg, pep and name SG
show spheres, cyssg
color yellow, cyssg
set sphere_scale, 0.35, cyssg
show sticks, pep and resn CYS
distance ss1, /cyc//A/4/SG,  /cyc//A/26/SG
distance ss2, /cyc//A/13/SG, /cyc//A/30/SG
distance ss3, /cyc//A/20/SG, /cyc//A/32/SG
color red, ss1 or ss2 or ss3
orient pep
ray 1600, 1200
png 07_peptide_cyclic/07_cyclotide_structure.png, dpi=300
```

### B. 바인더–타깃 복합체 + 인터페이스 (Ch.05·08·09 공통 템플릿)

```python
load <rank01.cif>, cplx
hide everything
bg_color white
# 타깃(파랑 표면) / 바인더(금색 cartoon) — 체인 ID는 챕터 표 참고
select tgt, cplx and chain <TARGET_CHAIN>
select binder, cplx and chain <BINDER_CHAIN>
show surface, tgt; color marine, tgt; set transparency, 0.5, tgt
show cartoon, binder; color yelloworange, binder
# 인터페이스 잔기(5Å 이내) 주황 sticks
select iface, binder within 5 of tgt
show sticks, iface; color orange, iface
# 수소결합 점선
distance hb, binder, tgt, 3.5, mode=2
orient
ray 1600,1200
png <out>.png, dpi=300
```

### C. pLDDT 색칠 (Ch.05 — 신뢰도 시각화)

```python
load 05_result_interpretation/data/vanilla/final_designs/rank001_1g13prot_79.cif, m
hide everything; show cartoon
spectrum b, blue_white_red, m     # 파랑=높은 pLDDT, 빨강=낮음
orient; ray 1600,1200
png 05_result_interpretation/05_plddt_colored.png, dpi=300
```

### D. 소분자 포켓 (Ch.10)

```python
load 10_small_molecule/data/small_molecule/final_designs/rank01_chorismite_29.cif, sm
hide everything; bg_color white
select prot, sm and chain A
select lig,  sm and chain B
show surface, prot; color grey80, prot; set transparency, 0.3, prot
show sticks, lig; color green, lig; util.cnc lig
# 포켓 잔기(리간드 4Å 이내) 강조
select pocket, prot within 4 of lig
show sticks, pocket; color cyan, pocket
orient lig; zoom lig, 8
ray 1600,1200
png 10_small_molecule/10_pocket_structure.png, dpi=300
```

### E. Zinc finger–DNA (Ch.11)

```python
load 11_nucleic_acid/data/dna/final_designs/rank01_zinc_finger_06.cif, zf
hide everything; bg_color white
# DNA(체인 B,C): 파랑 cartoon + 사다리
select dna, zf and chain B+C
show cartoon, dna; set cartoon_ring_mode, 3, dna; set cartoon_ring_finder, 1, dna
color marine, dna
# 설계 단백질(체인 A): 금색
select prot, zf and chain A
show cartoon, prot; color yelloworange, prot
# Zn 등 이온: 회색 구
show spheres, zf and not polymer
color grey50, zf and not polymer
# 단백질–DNA 수소결합
distance hb, prot, dna, 3.5, mode=2
orient; ray 1600,1200
png 11_nucleic_acid/11_dna_structure.png, dpi=300
```

---

## 우선순위 (제작 권장 순서)

1. **(S)★ Ch.07 cystine knot** — 가장 인상적, 이황화·고리 한눈에
2. **(S)★ Ch.11 DNA** — major groove 삽입 + H-bond 다수, DNA 결합 특성 시각화
3. **(S)★ Ch.10 포켓** — 소분자 결합의 정수
4. **(S) Ch.08/09 항체·나노바디 복합체** — CDR 루프 강조
5. **(S) Ch.05 pLDDT 색칠 + 인터페이스** — 메트릭을 구조로 이해
6. **(I) Ch.01 아키텍처·feature, Ch.04 파이프라인 흐름도** — 개념 이해 보조
7. 나머지 보충 개념도

> 모든 (S) 구조 그림은 위 레시피로 **이 과정에서 실제 만든 CIF**를 렌더링하면 돼요. 별도 다운로드 없이 `data/` 폴더만으로 완성됩니다. (I) 보충 이미지는 개념도라 별도 작도가 필요해요(일부는 기존 part1~5 튜토리얼의 png 재활용 가능).
