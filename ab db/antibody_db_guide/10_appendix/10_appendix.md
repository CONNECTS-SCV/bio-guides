---
title: "Ch.10 — 부록: mini-pipeline · 보고서 체크리스트 · 용어집"
chapter: 10
level: reference
language: ko
part: Reference
---

# Ch.10 — 부록

이 과정에서 쓴 도구·데이터·체크리스트를 한곳에 모았습니다. 실전에서 후보 항체를 받았을 때 이 부록만 보고도 한 바퀴 돌릴 수 있도록 하기 위함입니다.

---

## A. Mini-pipeline — 한 번에 돌리기

서열 1개를 받아 QC → humanness → 구조 → interface → liability → repertoire 까지 도는 예입니다. 각 줄은 **실제로 실행해 검증한 명령**이고, 노트북이 돌리는 것과 같은 스크립트입니다. 산출물은 전부 각 챕터의 `my_run/` 에 쌓입니다.

```bash
# 0) 환경 (Ch.03)
conda env create -f environment/abseq.yml && conda activate abseq

# 1) numbering & germline (Ch.04)
ANARCI -i 04_numbering/data/demo_mab.fa -s imgt --assign_germline --csv \
  --outfile 04_numbering/my_run/demo_imgt

# 2) humanness + humanization (Ch.05; pip 만으로 — BioPhi CLI 불필요)
python scripts/sapiens_humanize.py 05_humanness/data/demo_mab.fa \
  --scores-out 05_humanness/my_run/demo_sapiens_scores.csv \
  --fasta-out  05_humanness/my_run/demo_humanized.fa

# 3) 구조예측 (Ch.06; abstruct 환경. GPU 없으면 --cpu)
conda activate abstruct
python scripts/run_igfold_demo.py --fasta 06_structure/data/demo_mab.fa \
  --out 06_structure/my_run/demo_antibody_igfold.pdb

# 4) interface — 복합체 직접 다운로드 + contact (Ch.07, 인터넷 필요)
conda activate abseq
python scripts/pdb_contacts.py --pdb 1A14 --outdir 07_interface/my_run/pdb   # chain 확인
python scripts/pdb_contacts.py --pdb 1A14 --chain1 H --chain2 N --cutoff 4.0 \
  --outdir 07_interface/my_run/pdb --out 07_interface/my_run/contacts_H_N.tsv

# 5) developability — liability scan (Ch.08)
python scripts/liability_scan.py 08_developability/data/demo_mab.fa \
  --out 08_developability/my_run/liability.csv

# 6) repertoire — OAS data unit 다운로드 + CDR3 분포 (Ch.09)
python scripts/fetch_oas_unit.py --out 09_repertoire/my_run/oas_subset.tsv.gz
python scripts/oas_cdr3_length.py 09_repertoire/my_run/oas_subset.tsv.gz \
  --column cdr3_aa --out 09_repertoire/my_run/oas_cdr3_length_summary.csv

# 7) (참고) DB 스냅샷 — RCSB Search/Data API (Ch.02)
python scripts/fetch_rcsb_ab_snapshot.py --rows 12 \
  --out 02_databases/my_run/rcsb_ab_complexes.csv
```

보고서에 넣을 산출물: numbering CSV, humanness scores + humanized FASTA, IgFold PDB, contact table, `liability.csv`, `oas_cdr3_length_summary.csv`, 그리고 각 챕터 노트북이 그린 `.png`(메트릭 차트 5종). **PyMOL 3D 렌더 2종(Ch.06·07)은 pip 경로로 재생성되지 않아 커밋 이미지를 씁니다** — 재현하려면 로컬 PyMOL + `scripts/render_*.pml`.

---

## B. 좋은 항체 분석 보고서 체크리스트

최종 보고서에 이 항목들이 들어가야 합니다.

| 체크 항목 | 본 과정 챕터 |
|-----------|--------------|
| Input sequence와 chain type이 명확하다 | 04 |
| Numbering scheme을 명시했다 (IMGT/Kabat/Chothia) | 01·04 |
| CDR/FR boundary를 제시했다 | 04 |
| Germline assignment 방법을 설명했다 | 04 |
| 사용 DB와 버전을 기록했다 | 02 |
| 사용 도구와 파라미터를 기록했다 | 03 |
| 구조예측 결과를 실험 구조처럼 과장하지 않았다 | 06 |
| Interface 분석에서 chain ID와 cutoff를 명시했다 | 07 |
| Developability risk를 affinity와 함께 평가했다 | 08 |
| Naturalness를 단독 판정에 쓰지 않았다 | 09 |
| 모든 외부 데이터·그림 출처를 표기했다 | 전부 |

---

## C. 용어집

| 용어 | 설명 |
|------|------|
| ADCC | Antibody-dependent cellular cytotoxicity |
| CDC | Complement-dependent cytotoxicity |
| CDR | Complementarity-determining region (상보성 결정 영역) |
| FR | Framework region |
| Fv | VH/VL로 구성된 최소 antigen-binding unit |
| Fab | Antigen-binding fragment |
| Fc | Effector function·half-life 관련 영역 |
| Germline | 항체 V/D/J gene segment의 원형 유전자 |
| SHM | Somatic hypermutation |
| Epitope | 항원에서 항체가 인식하는 부위 |
| Paratope | 항체에서 항원을 인식하는 부위 |
| Developability | 항체가 실제 의약품으로 개발될 가능성 |
| Humanness | 항체 서열이 human repertoire와 유사한 정도 |
| Liability motif | 화학적/생산성/안정성 risk를 유발하는 sequence motif |
| Vernier zone | CDR conformation을 지지하는 framework 잔기 |
| BSA | Buried surface area (결합으로 묻히는 표면적) |

---

## D. 참고문헌

| # | 자료 | 링크 |
|---|------|------|
| [1] | SAbDab official page | <https://opig.stats.ox.ac.uk/webapps/sabdab-sabpred/sabdab> |
| [2] | Dunbar J. et al. SAbDab. NAR 2014 | <https://academic.oup.com/nar/article/42/D1/D1140/1044118> |
| [3] | OAS official page | <https://opig.stats.ox.ac.uk/webapps/oas/> |
| [4] | Olsen T.H. et al. Observed Antibody Space. Protein Science 2022 | <https://onlinelibrary.wiley.com/doi/full/10.1002/pro.4205> |
| [5] | IMGT — the international ImMunoGeneTics information system | <https://www.imgt.org/> |
| [6] | BioPhi GitHub | <https://github.com/merck/biophi> |
| [7] | Raybould M.I.J. et al. Thera-SAbDab. NAR 2020 | <https://academic.oup.com/nar/article/48/D1/D383/5573951> |
| [8] | IEDB official page | <https://www.iedb.org/> |
| [9] | Raybould M.I.J. et al. CoV-AbDab. Bioinformatics 2021 | <https://academic.oup.com/bioinformatics/article/37/5/734/5893556> |
| [10] | CoV-AbDab official page | <https://opig.stats.ox.ac.uk/webapps/covabdab/> |
| [11] | Sirin S. et al. AB-Bind. Protein Science 2016 | <https://pmc.ncbi.nlm.nih.gov/articles/PMC4815335/> |
| [12] | Jankauskaitė J. et al. SKEMPI 2.0. Bioinformatics 2019 | <https://academic.oup.com/bioinformatics/article/35/3/462/5055583> |
| [13] | iReceptor Gateway | <https://gateway.ireceptor.org/> |
| [14] | VDJServer AIRR docs | <https://docs.airr-community.org/en/stable/miairr/vdjserver.html> |
| [15] | abYsis official page | <https://www.abysis.org/> |
| [16] | ANARCI / SAbPred | <https://opig.stats.ox.ac.uk/webapps/sabdab-sabpred/sabpred/anarci/> |
| [17] | NCBI IgBLAST | <https://www.ncbi.nlm.nih.gov/igblast/> |
| [18] | IgFold GitHub | <https://github.com/Graylab/IgFold> |
| [19] | Ruffolo J.A. et al. IgFold. Nature Communications 2023 | <https://www.nature.com/articles/s41467-023-38063-x> |
| [20] | ImmuneBuilder GitHub | <https://github.com/oxpig/ImmuneBuilder> |
| [21] | PLIP 2025 update | <https://academic.oup.com/nar/article/53/W1/W463/8128215> |
| [22] | FreeSASA official page | <https://freesasa.github.io/> |
| [23] | TAP official page | <https://opig.stats.ox.ac.uk/webapps/sabdab-sabpred/sabpred/tap> |
| [24] | ChimeraX GitHub | <https://github.com/RBVI/ChimeraX> |
| [25] | OGRDB (AIRR Community germline reference) | <https://ogrdb.airr-community.org/> |
| [26] | Jain T. et al. Biophysical properties of the clinical-stage antibody landscape. PNAS 2017 | <https://www.pnas.org/doi/10.1073/pnas.1616408114> |

---

## E. 재현 환경 (Reproducibility)

이 과정의 수치·그래프가 **어디서 나왔는지**를 밝혀 둡니다. 같은 사양을 갖출 필요는 없습니다. 노트북은 여러분 환경에서 도구를 다시 돌려 `my_run/` 에 결과를 새로 만들기 때문입니다.

### E.1 노트북 실행 시간 (실측)

`jupyter nbconvert --to notebook --execute` 로 **전 셀을 실제 실행해 측정**한 값입니다. 도구가 이미 설치된 상태의 실행 시간이고, **pip 설치 시간은 빠져 있습니다**.

| 노트북 | 전 셀 실행 (콜드) | 두 번째 실행 (웜) | 그중 무거운 단계 |
|--------|------------------|------------------|------------------|
| `02_db_explore.ipynb` | 6초 | 4.8초 | RCSB API 2회 왕복 |
| `03_setup_check.ipynb` | 3초 | 2.3초 | — |
| `04_numbering_lab.ipynb` | 9초 | 2.8초 | ANARCI(hmmscan) 2회 |
| `05_humanness_lab.ipynb` | 16초 | 5.7초 | Sapiens 추론 (H 3.3초 + L 1.0초) |
| `06_structure_lab.ipynb` | 16초 | 14.5초 | **IgFold 예측 9.0초** (CPU) |
| `07_interface_lab.ipynb` | 10초 | 6.8초 | 1A14 CIF 다운로드 + contact 3회 |
| `08_dev_lab.ipynb` | 3초 | 3.0초 | — |
| `09_repertoire_lab.ipynb` | 8초 | 8.4초 | OAS unit 10 MB 다운로드 (3.8초) |

본문 실습 콜아웃의 배지는 **콜드 실행 값**입니다(더 보수적인 쪽).

### E.2 측정·검증 환경

| 항목 | 값 |
|------|-----|
| 실행 방식 | **pip 전용 가상환경**(Colab 경로를 그대로 흉내) + `hmmscan`(HMMER 3.4) |
| Python | 3.11 |
| 도구 버전 | ANARCI 2026.2.13 · abnumber 0.4.4 · **sapiens 1.1.0** · **IgFold 0.4.0** · transformers **4.36.2**(고정) · torch 2.13 · Biopython 1.87 · pandas 3.0 |
| 하드웨어 | Intel Core i9-14900K · 32 스레드 · RAM 31 GB · **GPU 미사용**(`CUDA_VISIBLE_DEVICES=""`, torch 스레드 4) |
| 네트워크 | RCSB(`files.rcsb.org`·`search.rcsb.org`·`data.rcsb.org`) · OAS(`opig.stats.ox.ac.uk`) 접속 필요 |
| 그림 | 메트릭 차트 5종 = 노트북이 `antibody_viz.py` 로 생성 · 3D 렌더 2종(Ch.06·07) = **PyMOL(open-source) 로컬 렌더**, pip 경로에서는 재생성 불가 |

> IgFold 예측 시간은 CPU 스레드 수에 민감합니다(위 환경에서 4스레드 9.0초). Colab 무료 런타임은 코어가 적어 더 걸릴 수 있습니다.

### E.3 커밋된 레퍼런스 데이터의 출처

`data/` 는 **대조군**입니다. 각 파일이 언제·무엇으로 만들어졌는지는 다음과 같습니다.

| 파일 | 출처 · 취득 시점 |
|------|------------------|
| `02_databases/data/rcsb_ab_complexes.csv` | RCSB Search+Data API 스냅샷 (`fetch_rcsb_ab_snapshot.py`, **2026-07-14**. 그날 조건 충족 entry 939건 중 오래된 12건) |
| `03_setup/data/setup_expected.csv` | ANARCI/abnumber IMGT numbering 결과 (정답지) |
| `04_numbering/data/demo_*.csv` | ANARCI 2024.05 실행 결과 (bit score만 최신 버전과 다를 수 있음 — Ch.04) |
| `05_humanness/data/demo_sapiens_scores.csv`·`demo_humanized.fa` | **bioconda BioPhi CLI** 실행 결과 (pip `sapiens` 재현본과 완전 일치 확인) |
| `06_structure/data/demo_antibody_igfold.pdb` | IgFold CPU 실행 결과 (1,115 atoms. 재실행 시 CA-RMSD 0.002 Å) |
| `07_interface/data/pdb/1A14.cif` | RCSB 다운로드 사본 — **오프라인 폴백용**(기본 경로는 직접 다운로드) |
| `07_interface/data/contacts_H_*.tsv` | `pdb_contacts.py` 4 Å contact 계산 결과 (H–N 15 pair / H–L 33 pair) |
| `08_developability/data/liability.csv` | `liability_scan.py` 실행 결과 |
| `09_repertoire/data/oas_subset.tsv.gz` | **진짜 OAS data unit** — `Eliyahu_2018 / ERR2843400_Heavy_IGHM` (human PBMC, unsorted B cells, IgM heavy, HCV 코호트 subject CI15), productive 17,807 서열, **2026-07-14** 다운로드 |
| `09_repertoire/data/oas_cdr3_length_summary.csv` | 위 unit을 `oas_cdr3_length.py` 로 집계한 결과 |

> **주의 — 이전 버전(v0.2)의 정정.** v0.2의 `oas_subset.tsv.gz` 는 실제 OAS 데이터가 아니라 **합성(시뮬레이션) 서열 3,000개**(seed=20260618)였고, 그 위에서 계산한 "평균 CDR3 19.3 aa, 후보 18 aa" 도 합성 분포에서 나온 값이었습니다. v0.3에서 **진짜 OAS data unit**으로 교체하고 모든 수치를 다시 계산했습니다(평균 **13.9 aa**, 후보 **13 aa**). 옛 문서를 인용 중이라면 이 수치를 갱신하세요.

---

### 과정을 마치며

이 과정은 공개 DB(**SAbDab·OAS·IMGT·Thera-SAbDab**)와 오픈소스 도구(**ANARCI·Sapiens·IgFold·Biopython contact**)로 항체를 *numbering → humanness → 구조 → interface → developability → repertoire* 순으로 한 바퀴 돌았습니다. 그것도 **읽기만 한 것이 아니라 매 챕터에서 도구를 직접 돌려** `my_run/` 에 결과를 만들고 레퍼런스와 대조하면서 진행했습니다.

이제 `data/demo_mab.fa` 를 **여러분의 후보 서열**로 바꾸고 같은 노트북을 다시 돌려 보세요. numbering·humanness·구조·liability·percentile 이 전부 여러분 항체 기준으로 새로 계산됩니다.

처음으로 → **[00. README (과정 인덱스)](../00_README.md)**
