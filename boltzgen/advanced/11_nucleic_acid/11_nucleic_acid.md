---
title: "Ch.11 — 실습: 핵산(DNA·RNA) 결합 단백질 설계"
chapter: 11
level: advanced
language: ko
part: B
---

# Ch.11 — 실습: 핵산(DNA·RNA) 결합 단백질 설계

드디어 마지막 실습입니다! 이번엔 가장 특별한 타깃, **핵산(DNA·RNA)**에 결합하는 단백질을 설계합니다. 유전자 편집 도구, 맞춤형 전사인자, 핵산 센서 — 합성생물학의 핵심 도구들이 여기서 나옵니다.

DNA 결합 단백질의 슈퍼스타인 **zinc finger**를 de novo로 설계하고(BoltzGen의 고급 입력 기능을 총동원합니다), 이어서 **RNA 타깃**까지 다뤄보겠습니다.

> **실습 — `11_nucleic_lab.ipynb`** · ① 직접 설계 실행 → ② 내 결과 확인 → ③ 레퍼런스 대조 · **분석 셀 3초**
>
> zinc finger(DNA)를 직접 돌려 그 결과를 로드·그래프화하고(건너뛰면 `data/dna`), 커밋된 `data/rna`와 **DNA vs RNA 인터페이스 H-bond를 비교(`compare_bars`)** 합니다.

---

## 11.1 왜 핵산 결합 단백질인가

DNA·RNA에 특이적으로 결합하는 단백질은 생명공학의 가장 강력한 도구입니다.

- **유전자 편집** — 특정 DNA 서열을 찾아가는 단백질(zinc finger, TALEN 등)은 CRISPR의 대안·보완 도구.
- **맞춤형 전사인자** — 원하는 유전자의 발현을 켜고 끄는 조절 단백질.
- **핵산 센서·진단** — 특정 서열(병원체 DNA/RNA)을 검출.
- **RNA 조절** — mRNA·비암호화 RNA에 결합해 번역·안정성 조절.

즉 "유전 정보 자체를 읽고 조작하는" 단백질을 설계하는 것입니다.

---

## 11.2 DNA는 단백질과 무엇이 다른가

핵산 결합 설계가 특별한 이유는, DNA·RNA가 단백질과 물리적으로 매우 다르기 때문입니다.

- **음전하 backbone** — 인산(phosphate) 골격 때문에 온통 음전하입니다. 그래서 결합 단백질은 보통 **양전하 잔기(Arg, Lys)가 인산과 정전기 상호작용**을 합니다. (실측에서 DNA 결합 디자인이 수소결합을 20개 넘게 만드는 것도 이 때문입니다.)
- **이중 나선 + groove** — major groove와 minor groove라는 두 홈이 있어, 단백질이 접근하는 경로가 구분됩니다.
- **염기 서열 인식** — 특정 염기 서열을 정확히 읽어야 합니다(일반 단백질 결합과 차원이 다른 특이성).

### Zinc Finger의 작동 원리

zinc finger는 아연 이온(Zn²⁺)이 구조를 잡아주는 작은 도메인입니다.

```
       Zn²⁺
      /    \
   Cys      His       ← Zn을 붙잡는 4개 잔기(보통 Cys2-His2)
      \    /
     α-helix  ──▶  DNA major groove에 삽입, 약 3개 염기쌍 인식
```

아연이 구조를 단단히 고정하고, 그 안정된 α-helix가 DNA major groove에 들어가 염기를 읽습니다. helix 하나가 약 3염기쌍을 인식합니다.

---

## 11.3 핵산 타깃 준비 — 자동 인식

좋은 소식! Ch.02에서 봤듯, **핵산 타깃은 특별한 설정이 거의 필요 없습니다.** DNA/RNA가 들어 있는 CIF를 `file`로 불러와 `include`하면, BoltzGen이 잔기 코드(CCD)를 보고 **DNA·RNA를 자동으로 구분·처리**합니다.

```yaml
entities:
  - protein: { id: G, sequence: 40..120 }   # DNA에 결합할 새 단백질
  - file:
      path: zf.cif
      include:
        - chain: { id: C1 }   # DNA 가닥 1 (자동으로 DNA로 인식)
        - chain: { id: B1 }   # DNA 가닥 2
```

이것이 가장 단순한 de novo DNA 결합 단백질 설계입니다(`denovo_zinc_finger_against_dna/vanilla_protein.yaml`). 단백질(G)을 새로 만들어 DNA 가닥(C1, B1)에 붙입니다.

---

## 11.4 Zinc Finger 재설계 — 고급 입력 기능 총동원

진짜 zinc finger 예제(`zinc_finger.yaml`)는 BoltzGen에서 **가장 복잡한 설계 명세** 중 하나입니다. 기존 zinc finger를 재설계하면서, Ch.02에서 배운 고급 기능을 거의 다 씁니다. 한 줄씩 뜯어보겠습니다.

```yaml
entities:
  - file:
      path: zf.cif
      include: "all"                    # 전체 포함 후
      exclude:                          # 불필요한 부분 제외
        - chain: { id: A1, res_index: ..10,63..69,185.. }
      design_insertions:                # finger 사이 linker 삽입
        - insertion: { id: A1, res_index: 63, num_residues: 3..8 }
      structure_groups:                 # 구조를 숨겨 자유 재설계
        - group: { visibility: 0, id: "all" }
      design:                           # 재설계할 영역
        - chain: { id: A1, res_index: 11..184 }
      not_design:                       # Zn 배위 잔기 등 고정
        - chain: { id: A1, res_index: 11..20,29,33,39..48,57,61,72..81,90,94,100..109,118,122,129..138,147,151,157..166,175,179 }
      reset_res_index:                  # 번호 정리
        - chain: { id: A1 }
```

각 기능의 역할.

| 기능 | 무엇을 하나 | 왜 |
|------|------------|----|
| `exclude` | N/C 말단·특정 구간 제거 | 불필요한 부분 정리, 시스템 경량화 |
| `design_insertions` | finger 사이 linker(3~8잔기) 삽입 | DNA 인식 최적화를 위한 유연성 |
| `structure_groups: visibility 0` | 구조 숨김 → 자유 재설계 | 타깃 DNA마다 최적 구조가 다르므로 |
| `design` / `not_design` | 재설계 영역 vs 고정 영역 분리 | **Zn 배위 잔기(Cys/His)는 절대 고정** |
| `reset_res_index` | 잔기 번호 연속 정리 | exclude·insertion 후 번호 정돈 |

> 심화 — `not_design`에 들어간 잔기들이 핵심입니다. zinc finger는 `Cys-X2-Cys-X12-His-X3-His` 패턴으로 Zn²⁺을 붙잡는데, **이 4개 잔기 중 하나라도 바뀌면 Zn이 안 붙고 구조가 무너집니다.** 그래서 이들을 `not_design`으로 못박는 것입니다. 효소의 catalytic triad, 이황화 Cys, 금속 결합 부위 등 "기능에 필수인 잔기"는 항상 이렇게 고정해야 합니다.

실행.

```bash
boltzgen run example/denovo_zinc_finger_against_dna/zinc_finger.yaml \
  --output workbench/dna --protocol protein-anything \
  --num_designs 30 --budget 10
```

> **직접 돌려보려면** — 이 명령이 아래 실측 결과(11.5)를 만든 그 명령입니다. 복합체는 248~253 토큰(단백질 + DNA 이중가닥 + Zn 이온)이라 Colab **T4 런타임**에서 그대로 돌아가고, 더 가볍게는 `--num_designs 8 --budget 4` — **약 10분(실측 585초, 최종 4개)** 규모입니다. 노트북은 여러분이 만든 `my_run/`을 먼저 읽고, 설계를 건너뛰면 커밋된 `data/dna` 레퍼런스로 폴백하니 규모를 줄여도 학습에 지장 없습니다.

---

## 11.5 실측 결과 — DNA 결합 단백질 (Zinc Finger)

실제로 `protein-anything`, num_designs 30, budget 10으로 돌린 zinc finger 재설계 결과입니다. 6단계가 정상 완료됐습니다.

![DNA 결합 메트릭 개요](11_dna_metrics.png)

1위 디자인의 복합체 구조입니다.

![Zinc finger–DNA 구조](11_dna_structure.png)

*설계한 단백질(금색)이 DNA 이중나선(파랑)의 groove를 따라 결합한 모습. 회색 구는 Zn 이온, 빨간 점선은 다수의 수소결합입니다. 단백질이 DNA를 휘감듯 따라가는 것이 보입니다 — 평균 H-bond 30.8개가 이렇게 만들어집니다.*

최종 선별셋의 실제 수치(상위 5개).

| rank | id | pTM | ipTM | RMSD(Å) | H-bond | 길이(aa) |
|------|----|-----|------|---------|--------|----------|
| 1 | zinc_finger_06 | 0.506 | 0.503 | 2.43 | 23 | 102 |
| 2 | zinc_finger_22 | 0.546 | **0.588** | 2.37 | 30 | 101 |
| 3 | zinc_finger_02 | 0.550 | 0.577 | 2.14 | **42** | 98 |
| 4 | zinc_finger_14 | 0.516 | 0.561 | 2.20 | 27 | 100 |
| 5 | zinc_finger_08 | 0.511 | 0.557 | 2.06 | 20 | 101 |

이 결과가 DNA 결합의 특성을 교과서처럼 보여줍니다.

- **H-bond가 압도적으로 많습니다 (20~42개, 최종 10개 전체 평균 30.8개!)**. 단백질-단백질 결합이 보통 한 자릿수인 것과 비교하면 차원이 다릅니다. 이것이 바로 11.2에서 말한 DNA **인산 골격**과의 광범위한 수소결합·정전기 상호작용입니다. 양전하 잔기(Arg/Lys)가 음전하 인산을 따라 줄줄이 결합하는 것입니다.
- **ipTM이 높습니다 (최종 10개 0.50~0.67)**. 나노바디(Ch.09, 0.2대)나 항체(Ch.08, 0.4대)보다 높은데, DNA의 강한 음전하가 안정적인 정전기 결합을 만들기 때문입니다. 소규모(num_designs 30)인데도 이만큼 나온 것은 DNA 타깃이 "결합하기 유리한" 표면이라는 뜻입니다. (위 표의 상위 5개만 보면 0.50~0.59입니다.)
- **pTM은 0.50~0.60으로 다소 낮습니다**. zinc finger는 작고 복잡한 도메인이라 구조 신뢰도가 일반 단백질 바인더보다 낮게 나오는 편입니다.
- **RMSD는 상위 8개가 2.0~2.4Å로 양호하지만, rank 9·10은 11.6Å대로 자기일관성이 무너집니다.** 이 둘(`zinc_finger_29`·`zinc_finger_28`)은 RMSD 필터를 통과하지 못했는데도 **ipTM이 0.635·0.670으로 전체 최고**라 최종 10위 안에 올라온 사례입니다 — 랭킹은 여러 지표의 종합이라, "최종 선별셋에 들었다 = 모든 지표가 좋다"가 아니라는 것을 보여줍니다. 실험 후보를 고를 땐 순위만 보지 말고 RMSD 같은 자기일관성 지표를 따로 확인해야 합니다.

> 심화 — H-bond 수가 곧 결합 품질은 아닙니다. DNA 결합에서 진짜 중요한 것은 **염기 서열 특이성**(특정 염기를 읽는가)인데, 이것은 H-bond 총수보다 인터페이스의 *기하·위치*에 달려 있습니다. 그래서 실전에서는 H-bond가 많은 후보 중 **결합부위가 의도한 DNA 염기에 정확히 놓이는지**를 PyMOL로 검증하고, 비슷한 서열에 오프타깃 결합하지 않는지 비교합니다. Zn 배위 잔기를 `not_design`으로 고정한 것이 이 특이성의 토대입니다(11.4).

---

## 11.6 RNA 결합 단백질 설계

DNA를 했으니 RNA도 해보겠습니다. 방법은 **완전히 동일**합니다 — RNA가 들어 있는 CIF만 있으면 BoltzGen이 자동으로 RNA로 인식합니다.

RNA는 DNA와 몇 가지가 다릅니다.
- 단일 가닥(single-strand)인 경우가 많고, 복잡한 2차/3차 구조(헤어핀, 루프, pseudoknot)를 가집니다.
- 그래서 결합 부위가 더 다양하고, 구조 의존적입니다.

RNA 타깃 준비(노트북 `11_nucleic_lab.ipynb`에서 실습).

```python
# 1) RNA-단백질 복합체 구조를 받아 RNA 체인을 타깃으로 추출
import urllib.request
urllib.request.urlretrieve("https://files.rcsb.org/download/XXXX.cif", "rna_target.cif")
# 2) 설계 명세
```
```yaml
entities:
  - protein: { id: P, sequence: 60..120 }   # RNA에 결합할 단백질
  - file:
      path: rna_target.cif
      include:
        - chain: { id: R }    # RNA 가닥 (자동 인식)
      structure_groups: "all"
```

```bash
boltzgen run rna_spec.yaml --output workbench/rna \
  --protocol protein-anything --num_designs 30 --budget 10
```

### 실측 결과 — RNA 결합 단백질

실제로 1URN의 **U1 snRNA 헤어핀(20 nt)**을 타깃으로, `protein-anything`, num_designs 30, budget 10으로 돌린 결과입니다. RNA만 깨끗이 추출해 단일 체인(R) PDB로 만든 타깃입니다(위 준비 과정).

![RNA 결합 메트릭 개요](11_rna_metrics.png)

1위 디자인의 복합체 구조입니다.

![단백질–RNA 구조](11_rna_structure.png)

*설계한 단백질(금색)이 RNA 헤어핀(파랑)에 결합한 모습. DNA 이중나선과 달리 단일가닥 RNA가 접힌 형태에 결합하는 것이 보입니다.*

최종 선별셋의 실제 수치(상위 5개).

| rank | id | pTM | ipTM | RMSD(Å) | H-bond | 길이(aa) |
|------|----|-----|------|---------|--------|----------|
| 1 | rna_spec_29 | 0.652 | 0.451 | 2.33 | 9 | 84 |
| 2 | rna_spec_07 | 0.587 | 0.436 | 2.43 | 11 | 109 |
| 3 | rna_spec_04 | 0.532 | 0.359 | 2.40 | 14 | 84 |
| 4 | rna_spec_16 | 0.607 | 0.424 | 2.24 | 10 | 92 |
| 5 | rna_spec_09 | 0.573 | 0.424 | 2.39 | 13 | 117 |

해석 — DNA와 비교하면 RNA 결합의 특성이 드러납니다.

- **H-bond 평균 9.3개**(최종 10개 전체) — 단백질-단백질(한 자릿수)보다는 많지만 **DNA(평균 30.8개)보다는 훨씬 적습니다**. RNA도 인산 골격이 음전하지만, 타깃이 20nt 단일가닥 헤어핀이라 DNA 이중나선보다 접촉면이 작기 때문입니다.
- **ipTM 0.36~0.45** — DNA(0.50~0.59)보다 낮습니다. RNA는 단일가닥이라 구조가 더 유연·불규칙해서 결합 인터페이스를 잡기가 DNA보다 까다롭습니다.
- **pTM 0.53~0.65** — 다소 낮은 편. 작은 설계 단백질 + 유연한 RNA 타깃 조합이라 그렇습니다.
- **RMSD 2.2~2.4Å** — 양호.

> 심화 — DNA vs RNA 설계 난이도: DNA 이중나선은 규칙적인 groove 구조라 결합 단백질 설계가 (상대적으로) 수월하고 H-bond·ipTM이 높게 나옵니다. 반면 RNA는 단일가닥에 헤어핀·루프·pseudoknot 같은 복잡하고 유연한 3차 구조를 가져, 결합부위가 다양하고 예측이 더 어렵습니다. 그래서 RNA 결합 단백질 설계는 **타깃 RNA의 구조를 잘 정의**하고(이번엔 잘 구조화된 U1 헤어핀 사용), num_designs를 충분히 키우는 것이 특히 중요합니다.

---

## 11.7 응용 — 유전자 편집과 합성생물학

- **맞춤형 zinc finger 뉴클레아제(ZFN)** — 원하는 DNA 서열을 찾아가 자르는 유전자 가위(CRISPR의 단백질 기반 대안).
- **합성 전사인자** — zinc finger array로 특정 프로모터를 표적해 유전자 발현을 켜고/끄기.
- **RNA 표적 치료** — 질병 관련 mRNA에 결합해 번역을 막는 단백질 치료제.
- **바이오센서** — 병원체 핵산 서열을 검출하는 진단 도구.

> 심화 — 핵산 결합 설계에서 가장 중요한 것은 **특이성**입니다. 비슷한 서열에 잘못 결합하면 오프타깃 효과가 생기기 때문입니다. 그래서 결합부위(binding_types)를 정밀하게 지정하고, 여러 후보를 만들어 특이성을 비교하는 것이 핵심입니다. Zn 배위 잔기 같은 기능 필수 잔기는 반드시 `not_design`으로 고정합니다.

---

### 이 챕터 핵심 요약

1. 핵산 결합 단백질 = **유전자 편집·전사 조절·진단**의 핵심 도구.
2. DNA/RNA는 **음전하 backbone**이라 양전하 잔기와 정전기·수소결합 → **H-bond 수가 매우 많음**.
3. 핵산 타깃은 CIF에 있으면 **자동 인식** — 그냥 `include`.
4. Zinc finger 재설계는 **고급 입력 기능 총동원**(exclude·design_insertions·visibility 0·design/not_design·reset_res_index), 특히 **Zn 배위 잔기는 not_design으로 고정**.
5. RNA도 방법은 동일 — RNA가 든 CIF만 있으면 됨. 단일가닥·복잡 구조라 결합부위가 다양.

---

**이것으로 Part B(타깃별 실습)를 모두 마쳤습니다!** 단백질·펩타이드·항체·나노바디·소분자·핵산 — 모든 바인더 타입을 직접 설계하고 해석하는 법을 익혔습니다. 이제 여러분만의 타깃에 도전해보십시오.

처음으로 → **[00. 과정 개요](../00_README.md)**
