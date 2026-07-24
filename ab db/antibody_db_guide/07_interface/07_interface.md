---
title: "Ch.07 — 항원-항체 interface 분석"
chapter: 7
level: hands-on
language: ko
part: B
---

# Ch.07 — 항원-항체 interface 분석

항체가 "어디에, 어떻게" 붙는지를 보는 것이 interface 분석입니다. 실제 항원-항체 복합체 구조(PDB)에서 **paratope(항체 쪽 접촉 잔기)**와 **epitope(항원 쪽 접촉 잔기)**를 뽑고, contact·H-bond·BSA를 정량합니다. 이 챕터는 실제 복합체 **1A14(Fab–neuraminidase)**를 **여러분이 RCSB에서 직접 받아** `pdb_contacts.py`로 분석합니다.

> **실습 — [`07_interface_lab.ipynb`](07_interface_lab.ipynb)** · **전 셀 실행 10초** — RCSB에서 **1A14.cif 를 직접 다운로드**(`my_run/pdb/`)하고 contact을 계산해 `my_run/contacts_*.tsv` 를 만든 뒤, 커밋된 결과와 대조합니다.

---

## 7.1 interface에서 보는 것들

| 항목 | 설명 |
|------|------|
| Contact residue | 일정 cutoff(보통 4 Å) 내 접촉 잔기 |
| Hydrogen bond | 방향·거리 조건을 만족하는 polar interaction |
| Salt bridge | 양/음전하 잔기 간 electrostatic |
| Hydrophobic contact | 비극성 잔기 간 접촉 |
| Buried surface area (BSA) | 결합으로 묻히는 표면적 |
| Shape complementarity | paratope·epitope 표면의 기하학적 적합성 |

간단한 contact는 **4 Å cutoff**로 시작하고, 논문 수준에선 H-bond geometry·solvent accessibility(FreeSASA)·interface area·energy term을 함께 봅니다.

---

## 7.2 복합체 받아서 contact 계산 — 직접 실행

```bash
# ① 먼저 구조를 내려받고 chain 목록부터 확인 (my_run/pdb/1A14.cif 로 저장)
python scripts/pdb_contacts.py --pdb 1A14 --outdir my_run/pdb
# ② 항원-항체 contact
python scripts/pdb_contacts.py --pdb 1A14 --chain1 H --chain2 N --cutoff 4.0 \
    --outdir my_run/pdb --out my_run/contacts_H_N.tsv
```

`--pdb 1A14`만 주면 RCSB(`files.rcsb.org`)에서 CIF를 받아 chain 목록을 찍어줍니다.

```
[download] https://files.rcsb.org/download/1A14.cif
Chains: A, H, L, N
```

> **주의** — Ch.02에서 겪은 대로 **chain ID를 직접 확인하세요**. 1A14는 항체가 H/L, 항원(neuraminidase)이 **N**입니다. 그래서 "항원-항체" interface는 `--chain1 H --chain2 N`이고, `--chain1 H --chain2 L`은 **VH–VL(중쇄-경쇄) packing** interface입니다(전혀 다른 분석!). 이것을 헷갈리면 엉뚱한 것을 분석하게 됩니다. (Ch.02의 2HRP에서는 chain N이 **중쇄**였다는 것도 기억하세요.)

> **심화 — 저장소에 `data/pdb/1A14.cif` 가 이미 있는데 왜 또 받는가?** 커밋본은 **오프라인 폴백**입니다(네트워크가 막힌 사내망·비행기 안). 기본 경로는 **여러분이 직접 받는 것**이고(`--outdir my_run/pdb`), 다운로드가 실패할 때만 `--fallback-cif data/pdb/1A14.cif` 로 커밋본을 씁니다. 노트북이 이 두 경로를 모두 넣어 실행합니다. 어느 쪽을 썼는지는 셀 출력(`[download]` / `[네트워크 실패] … 커밋된 사본으로 대체`)에 그대로 찍힙니다.

---

## 7.3 실행 결과 — paratope·epitope

H(항체)–N(항원) 4 Å contact: **15개 residue pair, 총 39 atom contacts**. 상위 접촉은 다음과 같습니다.

| 항체 잔기 (paratope) | CDR | 항원 잔기 (epitope) | atom contacts |
|----------------------|-----|---------------------|---------------|
| Tyr H99 | CDR-H3 | Asn N400 | **6** |
| Asp H56 | CDR-H2 | Ser N370 | 5 |
| Asn H54 | CDR-H2 | Thr N401 | 5 |
| Asp H56 | CDR-H2 | Trp N403 | 4 |
| Tyr H100A | CDR-H3 | Ala N369 | 3 |

![1A14 항원-항체 interface contact 상위 residue pair](07_interface_contacts.png)

*그림. 1A14(Fab–neuraminidase) 복합체에서 4 Å 이내로 접촉하는 항체(H)–항원(N) residue pair를 atom contact 수 기준 상위 15개로 나타낸 가로 막대그래프. 세로축은 "paratope 잔기 ↔ epitope 잔기" 쌍, 가로축은 그 쌍의 원자 접촉 수(주황 막대, 길수록 강한 접촉). (이미지: `07_interface_contacts.png`)*

**그림 읽는 법** — 가장 위(가장 긴 막대)가 **Tyr H99 ↔ Asn N400 (6 contacts)**, 그다음이 Asp H56·Asn H54가 항원의 N370·N401·N403과 만드는 접촉입니다. paratope 쪽(H 잔기)을 보면 번호가 **52·54·56(CDR-H2)**과 **99·100A(CDR-H3)**에 몰려 있으며, 이론대로 CDR이 결합을 주도한다는 것을 막대 길이로 직접 확인하는 것입니다. 항원 쪽(N 잔기)은 N369·370·400·401·403처럼 번호가 가까워서, neuraminidase 표면의 **한 패치에 모인 conformational epitope**임을 알 수 있습니다. 막대가 긴(접촉 많은) 잔기일수록 affinity maturation·humanization에서 **함부로 바꾸면 안 되는 hot-spot**입니다.

이 접촉을 **복합체 3D 구조로 보면** paratope·epitope가 어떻게 맞물리는지 한눈에 들어옵니다.

![1A14 Fab–neuraminidase 복합체 — paratope/epitope 강조](07_complex_3d.png)

*그림. 1A14 복합체의 결합 계면(PyMOL 렌더). **베이지 표면**이 항원 neuraminidase(chain N), **하늘색 cartoon**이 항체 중쇄(H), **연두색 cartoon**이 경쇄(L)입니다. 항체 쪽 paratope 접촉 잔기는 **주황 스틱**, 항원 쪽 epitope 잔기는 **빨강 스틱**으로 표시했습니다. (이미지: `07_complex_3d.png`)*

**그림 읽는 법** — 주황 스틱(paratope, CDR-H2·H3 loop)이 항원 표면의 **빨간 epitope 패치**로 정확히 파고드는 것이 보입니다. 위 표·막대그래프에서 숫자로 본 "Tyr H99·Asp H56·Asn H54 ↔ N400·N370·N401" 접촉이, 3D에서는 이렇게 **CDR loop가 항원 표면의 오목한 자리에 꽂히는 모습**으로 나타납니다. 빨간 잔기들이 표면 한 패치에 모여 있는 것도 conformational epitope의 증거입니다. 보고서에서 "이 항체가 항원의 어디에 붙는가"를 한 장으로 전달하는 핵심 figure입니다.

> **주의** — Ch.06과 마찬가지로 **이 3D 렌더만은 pip 경로로 재생성할 수 없습니다**(PyMOL은 Colab 미지원). 커밋된 이미지를 보여주고, 로컬에 PyMOL이 있으면 노트북이 자동 재렌더합니다(`pymol -cq scripts/render_07_complex.pml`). **contact 표와 막대그래프는 여러분이 방금 계산한 값으로 그립니다.**

> **심화** — **paratope이 CDR-H2(54·56)와 CDR-H3(99·100A)에 몰려 있으며**, 이론대로 CDR이 결합을 주도합니다. Tyr·Asn·Asp가 자주 보이는데, 방향족(Tyr)·극성(Asn/Asp) 잔기가 항원과 H-bond·packing을 만드는 전형적 패턴입니다. 항원 쪽 epitope 잔기는 N369·N370·N400·N401·N403으로, neuraminidase 표면의 한 패치에 모여 있습니다(conformational epitope).

비교로, **H–L(VH/VL packing)** interface는 33개 pair로 더 넓습니다. 두 가변 도메인이 맞물리는 큰 계면이기 때문입니다. interface 분석할 땐 "무엇 대 무엇"인지가 결과를 완전히 바꿉니다.

---

## 7.4 FreeSASA·PLIP로 더 깊이

contact만으로 부족할 때.

```bash
# SASA / buried surface area
freesasa data/pdb/1A14.cif --format=rsa > data/1A14.rsa
# PLIP (Docker, 설치 환경에 따라 조정)
docker run --rm -v $PWD:/work pharmai/plip:latest -f /work/data/pdb/1A14.cif -o /work/data/plip_out
```

> **심화** — `pdb_contacts.py`는 Biopython만 쓰므로 `abseq`로도 돌아갑니다. FreeSASA·PLIP는 `abinterface` 환경(Ch.03)입니다. 항체-항원 interface에선 PLIP 결과 + 자체 contact script를 함께 쓰면 해석이 더 안정적입니다.

---

### 이 챕터 핵심 요약

1. 실제 복합체 **1A14(Fab–neuraminidase)**를 **직접 다운로드**해 contact 계산 — 항원은 chain **N**(꼭 chain ID 확인!).
2. 실행 결과 paratope이 **CDR-H2(54·56)·CDR-H3(99·100A)**에 집중 — 이론대로 CDR이 결합 주도. (H–N 15 pair / 39 atom contacts, 노트북에서 레퍼런스와 **완전 일치** 확인)
3. epitope 잔기(N369·370·400·401·403)가 표면 한 패치에 모인 **conformational epitope**.
4. `--chain2 N`(항원, 15 pair) vs `--chain2 L`(VH/VL packing, 33 pair)은 완전히 다른 분석 — cutoff·chain을 항상 명시.
5. 커밋된 `data/pdb/1A14.cif` 는 **오프라인 폴백**일 뿐이며, 기본 경로는 직접 다운로드입니다.

다음 → **[08. developability (liability scan)](../08_developability/08_developability.md)**
