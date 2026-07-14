---
title: "Ch.04 — 입력 QC: ANARCI / IgBLAST"
chapter: 4
language: ko
part: B
---

# Ch.04 — 입력 QC: ANARCI / IgBLAST

이번 챕터는 좀 실무적입니다. 그런데 솔직히, 뒤의 모든 단계가 여기서 만든 numbering·annotation 위에서 돌아가기 때문에, **가장 중요한 챕터**라고 해도 과언이 아닙니다. 여기를 대충 하면 뒤에서 "왜 CDR이 안 맞지?" 하면서 헤매게 됩니다.

> **실습 — `04_numbering_lab.ipynb`** · ① 직접 실행 → ② 내 결과 확인 → ③ 레퍼런스 대조 · **전 셀 1초**
>
> ANARCI/abnumber 로 직접 numbering 해 CDR 6개를 뽑고, germline 을 할당해 **보호할 좌표**를 확정합니다.

> **실습 —** 이 챕터의 모든 명령과 수치는 ANARCI 2024.05.21 · IgBLAST 1.22.0을 실제로 설치해 돌려 본 결과입니다. 환경은 [Ch.03](../03_setup/03_setup.md)의 `abhuman`을 그대로 씁니다.

---

## 4.1 ANARCI 실행 — numbering + germline

ANARCI는 antibody/TCR variable domain을 numbering하고 chain type을 분류합니다. IMGT·Chothia·Kabat·Martin·AHo scheme을 지원하는데, 이 가이드는 **IMGT를 기본**으로 두겠습니다.

실제로 다음 parental 서열(mouse hybridoma 가정)을 넣어보겠습니다. **이 서열이 가이드 전체를 관통하는 예제**입니다 — Ch.05~07의 모든 수치가 이 두 체인에서 나옵니다.

```bash
cat > parental.fasta <<'FASTA'
>parental_H
QVQLQQSGPELVKPGASVKMSCKASGYTFTDYVINWGKQRSGQGLEWIGEIYPGSGTNYYNEKFKAKATLTADKSSNIAYMQLSSLTSEDSAVYFCARRGRYGLYAMDYWGQGTSVTVSS
>parental_L
QSALTQPPSASGSPGQSVTISCTGTSSDVGHKFPVSWYQQYPGKAPKLLIYKNLLRPSGVPDRFSGSKSGTSASLAITGLQAEDGADYYCQSYDSSLRVVFGGGTKTVVLG
FASTA

# numbering + CDR/FWR (CSV로 출력)
ANARCI -i parental.fasta --scheme imgt --csv -o anarci_out

# germline assignment까지 (humanization에서 핵심!)
ANARCI -i parental.fasta --scheme imgt --assign_germline --use_species human --csv -o anarci_gl
```

---

## 4.2 결과 해석 — 실제 출력으로

여기서 많은 분들이 그냥 "돌아갔다"에서 멈추는데, 진짜 정보는 germline 컬럼에 있습니다. 위 명령을 실제로 돌려서 `anarci_gl_H.csv`/`anarci_gl_KL.csv`에서 핵심 컬럼만 뽑으면 이렇게 나옵니다.

| 체인 | chain_type | 가장 가까운 human V gene | V identity | J gene | J identity |
|---|---|---|---:|---|---:|
| Heavy | H | `IGHV1-69*06` | **63%** | `IGHJ6*01` | 86% |
| Light | L (lambda) | `IGLV1-40*01` | **81%** | `IGLJ2*01` | 83% |

> **함정 — 중쇄 J 유전자는 도구마다 다르게 나옵니다.** ANARCI는 `IGHJ6*01`(85.71%)을 고르지만, abnumber의 germline 조회는 같은 서열에 `IGHJ4*01`을 답합니다. 틀린 게 아니라 **완전한 동점**이에요 — J 절편 14잔기 중 12개가 맞아 둘 다 85.71%이고, 어느 쪽이 먼저 나오냐는 도구의 tie-break(참조 세트·순회 순서)에 달렸습니다. V 유전자(`IGHV1-69*06` 63%)처럼 격차가 큰 경우와 달리, **J는 짧아서 동점이 흔합니다.** 그래서 backmutation 판단의 근거로는 V 유전자를 쓰고, J는 참고로만 봅니다.

이 표 한 장이 humanization 전략을 거의 다 말해줍니다.

- **Heavy chain V identity가 63%** — 사람 germline과 꽤 멉니다. 이 항체가 진짜 비인간 유래임을 확인해주고, **heavy framework에 humanization 여지가 크다**는 뜻입니다.
- **Light chain V identity가 81%** — 람다 경쇄가 이미 상당히 사람답습니다. 즉 light는 손댈 자리가 적고, **노력의 무게중심을 heavy에 둬야 한다**는 신호입니다.

> **심화 —** ANARCI의 `--assign_germline`은 IgBLAST 없이도 "가장 가까운 사람 germline과 % identity"를 바로 줘서, humanization 출발점 파악에 빠르고 편합니다. 더 엄밀한 V(D)J 분석이나 junction 분석이 필요하면 IgBLAST를 병행하십시오(§4.4).

---

## 4.3 CDR 추출 — 무엇을 지켜야 하는지부터 못 박기

humanization에서 가장 먼저 해야 할 일은 **"여기는 절대 안 건드린다"는 CDR을 명확히 표시**하는 것입니다. ANARCI의 IMGT numbering에서 CDR 위치(27–38, 56–65, 105–117)를 뽑으면, 위 서열의 실제 CDR은 이렇게 나옵니다.

| 체인 | CDR1 | CDR2 | CDR3 |
|---|---|---|---|
| Heavy | `GYTFTDYV` | `IYPGSGTN` | `ARRGRYGLYAMDY` |
| Light | `SSDVGHKFP` | `KNL` | `QSYDSSLRVV` |

이 잔기들은 뒤에서 어떤 도구를 쓰든 **기본적으로 보호**합니다. 특히 **CDR-H3(`ARRGRYGLYAMDY`)** 는 항원 결합에 가장 결정적인 loop라, 여기에 mutation이 들어가면 빨간불입니다.

> **흔한 함정 —** 자동 humanization 도구를 아무 가드 없이 돌리면, 모델이 "사람 레퍼토리에서 이 자리는 보통 X더라" 하면서 **CDR까지 사람 잔기로 바꿔버리는** 일이 생깁니다. 그래서 CDR 좌표를 미리 못 박아두는 이 단계가 중요합니다. [Ch.05](../05_humanize_sapiens/05_humanize_sapiens.md)에서 실제로 그런 사고가 나는 걸 보여드리겠습니다.

---

## 4.4 IgBLAST — ANARCI 결과를 독립적으로 한 번 더 확인하기

ANARCI의 germline 추정이 맞는지, 두 번째 도구로 교차확인하면 더 든든합니다. IgBLAST는 V/D/J germline assignment를 BLAST 방식으로 해줍니다. 단, **germline DB를 직접 마련해야** 하는 게 진입장벽인데 — 여기서 깔끔한 트릭이 하나 있습니다.

> **실습 —** IgBLAST 1.22.0을 bioconda로 깔고, germline DB는 **ANARCI가 내장한 사람 germline 서열로 직접 빌드**했습니다. 외부 다운로드 없이 재현됩니다.

```bash
conda install -c bioconda igblast -y       # igblastp, makeigblastdb 포함

# (트릭) ANARCI 패키지 안에 사람 IGHV germline 250개가 들어 있습니다. 이걸 FASTA로 뽑아 DB로 만듭니다.
python - <<'PY'
from anarci import germlines
g = germlines.all_germlines
with open("human_IGHV.fasta","w") as fh:
    for gene, alleles in g['V']['H']['human'].items():
        seq = "".join(next(iter(alleles.values()))).replace("-","").replace(".","")
        fh.write(f">{gene}\n{seq}\n")
PY

makeigblastdb -in human_IGHV.fasta -dbtype prot -out db/human_gl_V

export IGDATA=$(dirname $(dirname $(which igblastp)))/share/igblast
igblastp -query parental_H.fasta -germline_db_V db/human_gl_V -organism human -outfmt 7
```

**실측 결과** — parental heavy chain의 top V hit:

```text
# Fields: query, subject, % identity, alignment length, mismatches, ..., evalue, bit score
V  parental_H  IGHV1-8*01    63.27   98  36  ...  1.87e-43  130
V  parental_H  IGHV1-69*08   63.27   98  36  ...  2.66e-43  130
```

> **심화 — 두 도구가 같은 결론을 가리킵니다.** IgBLAST의 top hit는 **IGHV1-8\*01, 63.27% identity**입니다. §4.2에서 ANARCI는 **IGHV1-69, 63%**라고 했습니다. top 유전자명은 IGHV1-8 vs IGHV1-69로 한 끗 다르지만 **둘 다 IGHV1 subgroup이고 identity가 63%로 동일**합니다. 정렬 시드와 점수 방식이 다른 두 도구가 독립적으로 "IGHV1 계열, 사람과 약 63% 거리"라는 같은 결론을 낸 것입니다. humanization 여지가 크다는 §4.2의 판단이 한 번 더 확인됐습니다. (참고: `igblastp`는 단백질 모드라 J·junction은 다루지 않습니다. V gene·% identity 확인이 주 용도입니다.)

humanization에서 IgBLAST는 "parental의 V gene이 뭔지, humanized 후보의 germline identity가 얼마나 올라갔는지"를 엄밀히 확인하는 데 써요.

---

## 이 챕터 핵심 요약

1. ANARCI는 `pip`이 아니라 **bioconda**로 설치합니다(HMMER 의존).
2. `--assign_germline`으로 **가장 가까운 사람 germline과 % identity**를 바로 얻습니다 — 실측: heavy 63%(IGHV1-69), light 81%(IGLV1-40).
3. IgBLAST로 교차확인하면 **IGHV1-8 63.27%** — 같은 IGHV1 계열·같은 identity로 ANARCI와 결론 일치.
4. V identity가 낮은 체인(여기선 heavy)에 humanization 여지가 커요.
5. 뒤 단계로 가기 전에 **CDR 좌표를 못 박아** 보호 대상을 명확히 합니다.

---

다음 → **[05. BioPhi / Sapiens / OASis](../05_humanize_sapiens/05_humanize_sapiens.md)**
