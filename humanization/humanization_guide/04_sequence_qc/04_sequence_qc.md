---
title: "Ch.04 — 입력 QC: ANARCI / IgBLAST"
chapter: 4
language: ko
part: B
---

# Ch.04 — 입력 QC: ANARCI / IgBLAST

뒤 챕터에서 "왜 CDR이 안 맞지?" 하며 반나절을 태우는 일, 거의 전부 여기서 시작돼요. humanization의 모든 단계가 이 챕터에서 만든 **numbering과 annotation 위에서** 돌아가거든요. 좌표 하나가 밀리면 그 뒤는 전부 밀려요.

이 챕터에서는 parental 서열을 ANARCI에 넣어 numbering·CDR·germline을 뽑고, **어디를 보호하고 어디를 고칠지**를 숫자로 확정해요. 그리고 IgBLAST로 같은 결론이 나오는지 독립 검증까지 해볼게요.

> **실습 — `04_numbering_lab.ipynb`** · ① 직접 실행 → ② 내 결과 확인 → ③ 레퍼런스 대조 · **전 셀 1초**
>
> ANARCI/abnumber 로 직접 numbering 해 CDR 6개를 뽑고, germline 을 할당해 **보호할 좌표**를 확정해요.

---

## 4.1 ANARCI 실행 — numbering + germline

ANARCI는 antibody/TCR variable domain을 numbering하고 chain type을 분류해요. IMGT·Chothia·Kabat·Martin·AHo scheme을 지원하는데, 이 가이드는 **IMGT를 기본**으로 둘게요.

이 챕터의 모든 명령과 수치는 **ANARCI 2024.05.21 · IgBLAST 1.22.0**을 실제로 설치해 돌려 본 결과예요. 환경은 [Ch.03](../03_setup/03_setup.md)의 `abhuman`을 그대로 씁니다.

넣을 서열은 다음 parental 항체예요(mouse hybridoma 가정). **이 서열이 가이드 전체를 관통하는 예제**라, Ch.05~07의 모든 수치가 이 두 체인에서 나와요.

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

`--assign_germline`이 이 챕터의 알맹이예요. IgBLAST 없이도 "가장 가까운 사람 germline과 % identity"를 바로 주거든요. humanization의 출발점을 잡는 데 이보다 빠른 방법이 없어요.

---

## 4.2 결과 해석 — germline 컬럼이 전략을 말해줘요

많은 분들이 "돌아갔다"에서 멈춰요. 그런데 진짜 정보는 germline 컬럼에 있어요. 위 명령을 실제로 돌려 `anarci_gl_H.csv`/`anarci_gl_KL.csv`에서 핵심 컬럼만 뽑으면 이렇게 나와요.

| 체인 | chain_type | 가장 가까운 human V gene | V identity | J gene | J identity |
|---|---|---|---:|---|---:|
| Heavy | H | `IGHV1-69*06` | **63%** | `IGHJ6*01` | 86% |
| Light | L (lambda) | `IGLV1-40*01` | **81%** | `IGLJ2*01` | 83% |

이 표 한 장이 humanization 전략을 거의 다 말해줘요.

Heavy chain의 V identity가 **63%**예요. 사람 germline과 꽤 멀어요. 이 항체가 진짜 비인간 유래임을 확인해주는 동시에, **heavy framework에 손댈 여지가 크다**는 뜻이에요. 반대로 light chain은 **81%**죠. 람다 경쇄가 이미 상당히 사람다워요. 고칠 자리가 적다는 신호예요. 즉 **노력의 무게중심을 heavy에 둬야 해요.**

J 유전자는 이야기가 좀 달라요. 여기서 도구가 갈려요.

> **주의 — J 유전자는 도구마다 다르게 나와요.** ANARCI는 `IGHJ6*01`, abnumber는 같은 서열에 `IGHJ4*01`을 답해요. 틀린 게 아니라 **완전한 동점**이에요. J 절편 14잔기 중 12개가 맞아 둘 다 **85.71%**라, 어느 쪽이 먼저 나오냐는 도구의 tie-break(참조 세트·순회 순서) 문제예요.

V 유전자는 격차가 커서 이런 일이 없어요(`IGHV1-69*06` 63%). **J는 짧아서 동점이 흔해요.** 그러니 backmutation 판단의 근거로는 V 유전자를 쓰고, J는 참고로만 봐요. 더 엄밀한 V(D)J 분석이나 junction 분석이 필요하면 IgBLAST를 병행하세요(§4.4).

---

## 4.3 CDR 추출 — 무엇을 지켜야 하는지부터 못 박기

humanization에서 가장 먼저 할 일은 고칠 곳을 찾는 게 아니에요. **"여기는 절대 안 건드린다"를 표시하는 것**이에요. ANARCI의 IMGT numbering에서 CDR 위치(27–38, 56–65, 105–117)를 뽑으면 위 서열의 실제 CDR이 이렇게 나와요.

| 체인 | CDR1 | CDR2 | CDR3 |
|---|---|---|---|
| Heavy | `GYTFTDYV` | `IYPGSGTN` | `ARRGRYGLYAMDY` |
| Light | `SSDVGHKFP` | `KNL` | `QSYDSSLRVV` |

이 잔기들은 뒤에서 어떤 도구를 쓰든 **기본적으로 보호**해요. 특히 **CDR-H3(`ARRGRYGLYAMDY`)** 는 항원 결합에 가장 결정적인 loop예요. 여기에 mutation이 들어가면 빨간불이에요.

왜 이렇게까지 못을 박을까요. 자동 humanization 도구를 가드 없이 돌리면, 모델이 "사람 레퍼토리에서 이 자리는 보통 X더라" 하면서 **CDR까지 사람 잔기로 바꿔버려요.** 좌표를 미리 고정해두지 않으면 알아채기도 어렵고요. [Ch.05](../05_humanize_sapiens/05_humanize_sapiens.md)에서 실제로 그 사고가 나는 걸 보여드릴게요.

---

## 4.4 IgBLAST — ANARCI 결과를 독립적으로 한 번 더 확인하기

ANARCI의 germline 추정이 맞는지, 두 번째 도구로 교차확인하면 더 든든해요. IgBLAST는 V/D/J germline assignment를 BLAST 방식으로 해줘요.

진입장벽은 **germline DB를 직접 마련해야** 한다는 점이에요. 여기서 깔끔한 트릭이 하나 있어요. ANARCI 패키지 안에 사람 germline 서열이 들어 있으니, 그걸 FASTA로 뽑아 DB로 만들면 돼요. 외부 다운로드 없이 그대로 재현돼요.

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

parental heavy chain의 top V hit는 이렇게 나왔어요.

```text
# Fields: query, subject, % identity, alignment length, mismatches, ..., evalue, bit score
V  parental_H  IGHV1-8*01    63.27   98  36  ...  1.87e-43  130
V  parental_H  IGHV1-69*08   63.27   98  36  ...  2.66e-43  130
```

> **심화 — 두 도구가 같은 곳을 가리켜요.** IgBLAST top hit는 **IGHV1-8\*01, 63.27%**, §4.2의 ANARCI는 **IGHV1-69, 63%**예요. 유전자명은 한 끗 다르지만 **둘 다 IGHV1 subgroup이고 identity가 63%로 같아요.** 정렬 시드와 점수 방식이 다른 두 도구가 독립적으로 같은 결론을 냈어요.

즉 "IGHV1 계열, 사람과 약 63% 거리"라는 §4.2의 판단이 한 번 더 확인된 거예요. humanization 여지가 크다는 결론도 그대로 유지돼요. 참고로 `igblastp`는 단백질 모드라 J·junction은 다루지 않아요. V gene과 % identity 확인이 주 용도예요.

humanization에서 IgBLAST는 "parental의 V gene이 뭔지, humanized 후보의 germline identity가 얼마나 올라갔는지"를 엄밀히 확인하는 데 써요.

---

## 이 챕터 핵심 요약

1. ANARCI는 `pip`이 아니라 **bioconda**로 설치해요(HMMER 의존).
2. `--assign_germline`으로 **가장 가까운 사람 germline과 % identity**를 바로 얻어요 — 실측 heavy 63%(IGHV1-69), light 81%(IGLV1-40).
3. J 유전자는 `IGHJ6*01`과 `IGHJ4*01`이 **85.71%로 완전 동점**이라 도구마다 갈려요. 판단 근거는 V로 잡아요.
4. IgBLAST로 교차확인하면 **IGHV1-8 63.27%** — 같은 IGHV1 계열·같은 identity로 ANARCI와 결론 일치.
5. V identity가 낮은 체인(여기선 heavy)에 humanization 여지가 커요.
6. 뒤 단계로 가기 전에 **CDR 좌표를 못 박아** 보호 대상을 명확히 합니다.

---

다음 → **[05. BioPhi / Sapiens / OASis](../05_humanize_sapiens/05_humanize_sapiens.md)**
