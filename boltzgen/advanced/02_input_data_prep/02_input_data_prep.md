---
title: "Ch.02 — 입력 데이터 준비: 설계 명세부터 타깃 정제까지"
chapter: 2
level: advanced
language: ko
---

# Ch.02 — 입력 데이터 준비

Ch.01에서 BoltzGen이 안에서 무슨 일을 하는지 봤습니다. 이제 이 엔진에 **무엇을, 어떻게 넣어줘야 하는지**를 깊이 있게 다뤄보겠습니다.

사실 BoltzGen 설계에서 **결과 품질의 절반 이상은 입력 단계에서 결정**됩니다. "쓰레기를 넣으면 쓰레기가 나온다(garbage in, garbage out)"는 말이 여기서도 정확히 통하기 때문입니다. 타깃 구조가 지저분하거나, 결합부위를 엉뚱하게 잡거나, entity 타입을 잘못 쓰면, 아무리 좋은 모델이라도 좋은 바인더를 만들 수 없습니다.

이 챕터에서는 **① 설계 명세(YAML)를 정확히 쓰는 법 → ② 타깃 구조를 준비·정제하는 법 → ③ 결합부위를 고르는 법 → ④ 품질을 검증하는 법** 순서로 가보겠습니다.

> **실습 — `02_data_prep.ipynb`** · Colab에서 열고 그대로 실행 · **전 셀 4초**
>
> RCSB 다운로드 · gemmi 검사 · entity 5종(단백질·DNA/RNA·소분자 CCD/SMILES·file) 명세 작성 · `boltzgen check`를 단계별로 따라 합니다.

---

## 2.1 BoltzGen 입력의 큰 그림

BoltzGen에 넣는 입력은 딱 두 종류입니다.

```
① 설계 명세 (YAML)  ─ "무엇을 만들지" 를 기술
② 타깃 구조 (CIF/PDB) ─ "어디에 붙일지" 의 실제 3D 좌표
```

YAML 안의 `file` entity가 ②번 구조 파일을 가리키고, 거기서 어떤 체인·잔기를 타깃으로 쓸지 골라냅니다. 그래서 우리가 준비할 것은 사실상 **이 두 파일을 제대로 만드는 것**입니다.

전체 흐름을 그림으로 보면 다음과 같습니다.

```
PDB/실험구조 ──(다운로드·정제)──▶ target.cif
                                      │
설계 의도 ──(YAML 작성)──▶ design_spec.yaml ──(file: path)──┘
                                      │
                                      ▼  boltzgen check 로 검증
                                  설계 가능 확인 → boltzgen run
```

---

## 2.2 entity 5종 — 정확한 문법

Ch.01에서 봤듯 BoltzGen은 5가지 entity를 다룹니다. 각각을 정확한 문법과 함께 하나씩 살펴보겠습니다. (이 표기들은 실제 `design_spec_showcasing_all_functionalities.yaml`에서 검증한 것입니다.)

### ① `protein` — 설계할(또는 고정할) 단백질

```yaml
- protein:
    id: B               # 체인 ID (타깃과 겹치면 안 됩니다!)
    sequence: 80..140   # 길이 80~140 사이 랜덤으로 디자인
```

서열 칸(`sequence`)에 무엇을 적느냐에 따라 의미가 완전히 달라집니다.

| 표기 | 의미 |
|------|------|
| `80..140` | 80~140 사이 랜덤 길이로 **완전 자유 디자인** |
| `120` | 정확히 120잔기 |
| `MKLV...` | 그 서열로 **고정**(디자인 안 함) |
| `3C8C6C5C3C1C2` | 고정 Cys 사이에 디자인 잔기 N개 (고리형 펩타이드용 — Ch.07) |

### ② `dna` / ③ `rna` — 핵산

```yaml
- dna: { id: D, sequence: ATGCGT }   # DNA 가닥
- rna: { id: R, sequence: AUGCGU }   # RNA 가닥
```

대부분의 경우 핵산은 **타깃**이라 `file`로 불러오지만(2.7 참고), 직접 서열로 명시할 수도 있습니다.

### ④ `ligand` — 소분자

소분자는 두 가지 방법으로 지정합니다.

```yaml
# 방법 1: CCD 코드 (PDB 화학성분 사전의 3글자 코드)
- ligand: { id: L, ccd: ATP }

# 방법 2: SMILES 문자열 (CCD에 없는 분자)
- ligand: { id: L, smiles: "CC(=O)Oc1ccccc1C(=O)O" }   # 아스피린
```

> **CCD vs SMILES, 언제 무엇을?** 잘 알려진 보조인자·기질(ATP, NAD, HEM, TSA 등)은 CCD 코드가 깔끔하고 정확합니다. 신약 후보처럼 표준 코드가 없는 분자는 SMILES나 `.sdf` 파일로 직접 넣습니다. CCD 코드는 RCSB(rcsb.org)에서 해당 리간드를 검색하면 찾을 수 있습니다.

### ⑤ `file` — 기존 구조에서 타깃 가져오기

가장 자주 쓰는 entity입니다. CIF/PDB 파일에서 **원하는 체인·잔기만 골라** 타깃으로 씁니다.

```yaml
- file:
    path: target.cif
    include:                  # 무엇을 포함할지
      - chain: { id: A }
    exclude:                  # 포함한 것 중 무엇을 뺄지 (선택)
      - chain: { id: A, res_index: 45..55 }
    structure_groups: "all"   # 타깃 구조를 모델에 보여줄지 (Ch.04에서 상세)
```

`include`/`exclude`의 `res_index`는 강력한 범위 문법을 씁니다.

| 표기 | 의미 |
|------|------|
| `45..55` | 45번부터 55번까지 |
| `..10` | 처음부터 10번까지 |
| `185..` | 185번부터 끝까지 |
| `10,29,33,40..48` | 개별 + 범위 혼합 |

---

## 2.3 타깃 구조 준비 — 어디서, 어떻게 가져오는가?

타깃의 3D 구조 파일(CIF/PDB)이 필요합니다. 보통 **RCSB Protein Data Bank**(rcsb.org)에서 받습니다.

### 실전: PDB에서 구조 다운로드하기

예를 들어 PD-L1(면역항암 표적) 구조 `7uxq`가 필요하다고 해보겠습니다. 명령 한 줄이면 됩니다.

```bash
curl -sSL -o 7uxq.cif "https://files.rcsb.org/download/7uxq.cif"
```

> **실전에서 자주 겪는 함정**: BoltzGen 예제 폴더(`example/fab_targets/`)에는 설계 명세(`pdl1.yaml`)는 있지만 **타깃 구조 파일(`7uxq.cif`)은 들어있지 않습니다!** 용량이 큰 구조 파일은 직접 받아야 하기 때문입니다. 이것을 모르고 바로 실행하면 `FileNotFoundError: ... 7uxq.cif` 로 1단계에서 죽습니다. 실제로 이 과정을 만들 때도 똑같이 겪었고, 위 `curl` 한 줄로 받아서 해결했습니다. (반면 zinc finger 예제는 `zf.cif`가 폴더에 들어 있어서 바로 돌아갑니다.)

### 어셈블리(assembly) 선택 — 의외로 중요합니다

PDB 구조는 보통 두 가지 버전이 있습니다.

- **비대칭 단위(asymmetric unit)**: 결정학에서 측정한 최소 단위
- **생물학적 어셈블리(biological assembly)**: 실제 생체 내에서 기능하는 형태

우리가 원하는 것은 **생물학적으로 의미 있는 형태**입니다. 예를 들어 나노바디 실습의 penguinpox 타깃은 `9bkq-assembly2.cif`처럼 **어셈블리 버전**을 씁니다. 어떤 올리고머 상태(단량체/이량체)에 결합시킬지가 설계에 영향을 주니, 타깃이 실제로 어떤 형태로 기능하는지 확인하고 맞는 어셈블리를 고르십시오.

```bash
# 생물학적 어셈블리 2번 받기
curl -sSL -o target.cif "https://files.rcsb.org/download/9bkq-assembly2.cif"
```

---

## 2.4 타깃 정제·전처리 — 깨끗하게 다듬기

받은 구조를 그대로 쓰면 안 되는 경우가 많습니다. **불필요하거나 방해되는 부분을 정리**해야 합니다.

### 무엇을 빼야 하는가?

| 대상 | 왜 빼는가? | 방법 |
|------|-----------|------|
| 관심 없는 체인 | 타깃과 무관한 단백질·결정화 보조물 | `include`로 필요한 체인만 선택 |
| 물 분자, 결정화 첨가물 | 설계와 무관, 노이즈 | `include`에서 자동 제외(단백질 체인만 지정) |
| Flexible loop / 무질서 영역 | 구조가 불확실해 예측이 흔들림 | `exclude`로 해당 `res_index` 제거 |
| 큰 막관통 영역 | 시스템이 불필요하게 커짐 | 필요 부분만 `include` |

### 실전 예: flexible loop 제거

타깃 중간에 구조가 불확실한 유연한 loop(예: 45~55번)가 있다면, 빼는 것이 예측 안정성에 좋습니다.

```yaml
- file:
    path: target.cif
    include:
      - chain: { id: A }
    exclude:
      - chain: { id: A, res_index: 45..55 }   # flexible loop 제거
      - chain: { id: A, res_index: 120..135 } # 무질서 영역 제거
```

> **왜 빼면 좋은가?** 유연한 영역은 구조 예측이 불확실해서, 그 위에 바인더를 설계하면 인터페이스가 흔들립니다. 또 시스템 크기가 줄면 계산도 빨라집니다. 다만 **결합부위 근처는 함부로 빼지 마십시오.** 결합에 필요한 잔기를 날려버릴 수 있습니다.

### 번호 재정렬 — `reset_res_index`

`exclude`나 `design_insertions`를 쓰면 잔기 번호가 군데군데 비거나 이상해집니다. `reset_res_index`로 연속 번호로 깔끔하게 정리할 수 있습니다(시각화·후속 분석이 편해집니다).

```yaml
    reset_res_index:
      - chain: { id: A }
```

---

## 2.5 결합부위 선정 — 어디에 붙일지 정하기

이것이 입력 준비에서 **가장 전략적인 결정**입니다. "타깃의 어디에 바인더를 붙일 것인가?"

### `binding_types` — 결합부위 지정

아무 데나 붙는 바인더는 부작용을 일으킬 수 있습니다. 특정 부위(효소 활성부위, 단백질 상호작용 인터페이스, 알려진 약물 포켓)만 노리려면 `binding_types`를 씁니다.

```yaml
- file:
    path: target.cif
    include:
      - chain: { id: A }
    binding_types:
      - chain:
          id: A
          binding: 343,344,251     # 이 잔기들에만 결합!
    structure_groups: "all"
```

`binding`의 표기도 범위 문법을 그대로 씁니다(`10..20,25,30..35`). 반대로, **절대 붙으면 안 되는 곳**은 `not_binding`으로 막습니다.

```yaml
    binding_types:
      - chain: { id: A, binding: 95..110 }     # 여기는 결합
      - chain: { id: B, not_binding: "all" }   # B 체인은 결합 금지
```

> **결합부위를 어떻게 고르는가?** 세 가지 단서를 보십시오. ① **알려진 기능 부위**(효소의 catalytic residues, 수용체-리간드 인터페이스) ② **구조적 포켓**(움푹 들어가 약물이 들어갈 공간) ③ **문헌/돌연변이 데이터**(어떤 잔기 변이가 기능을 죽이는가 → 그 잔기가 중요). 막고 싶은 단백질 상호작용이 있다면, 그 **인터페이스 잔기 자체를 binding 부위**로 지정하면 됩니다.

### `structure_groups` — 타깃 구조를 얼마나 "보여줄까"

이것은 약간 고급 개념인데, 모델에게 타깃 구조 정보를 **얼마나 노출할지**를 정합니다. visibility 값으로 조절합니다.

| visibility | 의미 | 언제? |
|:---:|------|------|
| `0` | 숨김 (구조 정보 없음 → 자유롭게 재설계) | de novo 설계, 타깃별 최적 구조 탐색 |
| `1` | 보임 (구조 유지) | 타깃을 고정해 그 위에 결합 |
| `2` | 별도 그룹 (상대 위치 자유) | 유연한 도메인, hinge |

대부분의 "타깃에 붙이기" 설계에서는 타깃을 `structure_groups: "all"`(보임)로 두고 그 구조에 결합시킵니다. (Ch.04와 Ch.11에서 visibility를 실제로 다르게 줘보며 차이를 봅니다.)

---

## 2.6 서열·위상학 표기 심화

설계 단백질의 서열 칸과 제약은 BoltzGen의 표현력이 가장 빛나는 부분입니다. 핵심만 정리하겠습니다(실습은 Ch.04·07).

### 시스테인 패턴 (이황화·고리형용)

```yaml
sequence: 3C8C6C5C3C1C2
```

읽는 법: `3`개 디자인 잔기 + `C`(Cys) + `8`개 + `C` + ... 이런 식입니다. 이 예는 시스테인이 정확히 6개 들어가, **3쌍의 이황화결합**(cystine knot)을 만들 수 있습니다. 합치면 3+1+8+1+6+1+5+1+3+1+1+1+2 = 34잔기입니다.

### 고리화 + 공유결합

```yaml
- protein:
    id: B
    sequence: 3C8C6C5C3C1C2
    cyclic: true                      # 머리-꼬리 고리화
constraints:
  - bond: { atom1: [B, 4, SG], atom2: [B, 26, SG] }   # Cys4–Cys26 이황화
  - bond: { atom1: [B, 13, SG], atom2: [B, 30, SG] }
  - bond: { atom1: [B, 20, SG], atom2: [B, 32, SG] }
```

`[체인, 잔기번호, 원자이름]` 형식이고, `SG`는 시스테인의 황 원자입니다.

### 2차구조 조건화 & 잔기 제약

```yaml
    secondary_structure:
        helix: 5..15      # 5~15번을 helix로
        sheet: 20..28     # 20~28번을 sheet로
    residue_constraints:
      - { position: 1, allowed: A }        # 1번은 Ala만
      - { position: 3..5, disallowed: CM } # 3~5번은 Cys/Met 금지
```

> `residue_constraints`는 특정 위치에 원하는/금지할 아미노산을 못박는 고급 기능입니다. 면역원성 회피, 특정 모티프 강제, 발현 최적화 등에 유용합니다(Ch.06).

---

## 2.7 핵산(DNA·RNA) 타깃 준비

핵산 결합 단백질(징크핑거, 전사인자 등)을 설계할 때, 타깃 DNA/RNA는 어떻게 넣는가?

가장 깔끔한 방법은 **DNA/RNA가 들어 있는 구조 파일을 `file`로 불러오는** 것입니다. BoltzGen은 CIF 안의 잔기 코드(CCD)를 보고 **단백질·DNA·RNA를 자동으로 구분**합니다. 그래서 별도의 특별한 설정 없이, 그냥 핵산 체인을 `include`하면 됩니다.

```yaml
entities:
  # 설계할 단백질 (DNA에 결합)
  - protein: { id: G, sequence: 40..120 }
  # 타깃: DNA가 들어 있는 구조에서 핵산 체인들 포함
  - file:
      path: zf.cif
      include:
        - chain: { id: C1 }   # DNA 가닥 1
        - chain: { id: B1 }   # DNA 가닥 2
```

> 위는 실제 zinc finger 예제(`denovo_zinc_finger_against_dna/vanilla_protein.yaml`)의 구조입니다. `zf.cif`에는 단백질과 DNA가 함께 들어 있고, DNA 가닥(C1, B1)만 타깃으로 골라 거기 결합하는 새 단백질(G)을 설계합니다. RNA도 똑같은 방식입니다. RNA가 든 CIF만 있으면 됩니다. (Ch.11에서 DNA·RNA 둘 다 실습합니다.)

---

## 2.8 품질 체크 — 실행 전에 반드시!

입력을 다 만들었으면, **돌리기 전에 검증**하십시오. 몇 시간짜리 작업이 입력 오류로 죽으면 너무 아깝습니다.

### `boltzgen check` — 설계 명세 검증

```bash
boltzgen check example/vanilla_protein/1g13prot.yaml
```

실제 출력은 다음과 같습니다.

```
************** Checking design spec: 1g13prot.yaml **************
Total designed residues: 90
Design specification visualization is written to 1g13prot.cif
```

두 가지를 알려줍니다.
- **`Total designed residues: 90`** — 이번에 90잔기로 샘플링됐다는 뜻입니다. `80..140` 범위라 매번 달라집니다(어떤 땐 90, 어떤 땐 130). 즉 **이 숫자는 매 실행마다 바뀌는 것이 정상**입니다.
- **`... visualization is written to 1g13prot.cif`** — 설계 명세를 눈으로 확인할 수 있는 CIF를 만들어줍니다. PyMOL로 열어서 "타깃이 맞나, 설계 영역이 의도대로인가"를 확인하십시오.

```bash
pymol 1g13prot.cif   # 타깃(예: 녹색)과 설계 자리(placeholder)를 시각적으로 확인
```

### 흔한 입력 오류 체크리스트

실행 전에 이것만 확인해도 대부분의 실패를 막습니다.

- **체인 ID 충돌** — 설계 단백질 `id`가 타깃 체인과 겹치지 않는가? (겹치면 안 됩니다)
- **타깃 구조 파일 존재** — `path`가 가리키는 CIF가 실제로 있는가? (예제는 직접 받아야 할 수 있음)
- **상대경로** — `path`는 **YAML 파일 위치 기준** 상대경로입니다. (나노바디처럼 `../nanobody_scaffolds/...`를 참조하면 폴더 구조가 유지돼야 함)
- **결합부위 잔기 번호** — `binding`에 적은 번호가 실제 타깃에 존재하는가?
- **프로토콜 정합** — 펩타이드면 `peptide-anything`, 소분자면 `protein-small_molecule`가 맞는가? (Ch.01의 흐름도)

---

### 이 챕터 핵심 요약

1. 입력 = **설계 명세(YAML)** + **타깃 구조(CIF)**. 결과 품질의 절반은 여기서 갈립니다.
2. entity 5종(protein/dna/rna/ligand/file)의 문법을 정확히, 특히 `file`의 `include`/`exclude`/`res_index` 범위 표기를 지키십시오.
3. 타깃은 RCSB에서 받아 **불필요한 체인·물·flexible loop를 정리**하고, **올바른 생물학적 어셈블리**를 고르십시오.
4. **결합부위(`binding_types`) 선정이 가장 전략적**입니다. 기능 부위·포켓·문헌 단서를 활용하십시오.
5. 핵산 타깃은 CIF에 들어 있으면 **자동 인식**되니 그냥 `include`하면 됩니다.
6. 실행 전 **`boltzgen check`**로 잔기 수·시각화를 확인하는 습관을 들이십시오.

다음 → **[03. 툴 설치 및 접근](../03_install_access/03_install_access.md)**
