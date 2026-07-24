---
title: "부록 — 메트릭 사전·CLI 레퍼런스·YAML 치트시트·트러블슈팅·FAQ·용어집"
chapter: 12
level: advanced
language: ko
part: reference
---

# 부록 (Appendix) — 실무 레퍼런스

본문을 따라 실습하다 보면 "이 메트릭이 뭐였지?", "그 옵션 이름이 뭐였지?" 하고 다시 찾게 됩니다. 이 부록은 그럴 때 빠르게 찾아보는 **레퍼런스 모음**입니다. 곁에 두고 필요할 때 펴 보십시오.

---

## A1. 메트릭 전체 사전 (출력 CSV 컬럼)

BoltzGen 메트릭 CSV는 240개가 넘는 컬럼을 갖지만, 카테고리로 묶으면 한눈에 들어옵니다. (Ch.05의 확장판)

### 신뢰도 (Confidence)

| 컬럼 | 의미 | 좋은 값 |
|------|------|---------|
| `design_ptm` | 설계 단백질 자체 구조 신뢰도(pTM) | 높을수록 (>0.7 양호, >0.8 우수) |
| `design_to_target_iptm` | 바인더-타깃 인터페이스 신뢰도(ipTM) — **핵심** | 높을수록 (>0.5 양호) |
| `design_residue_iptm` | 잔기별 인터페이스 TM | 높을수록 |
| `design_iptm` | 설계 영역 내부 신뢰도 | 높을수록 |
| `iptm` / `ptm` | 복합체 전체 ipTM / pTM | 높을수록 |
| `target_ptm` | 타깃 체인 pTM | 높을수록 |
| `protein_iptm` / `ligand_iptm` | 단백질-단백질 / 리간드-단백질 인터페이스 | 높을수록 |
| `complex_plddt` / `complex_iplddt` | 복합체 / 인터페이스 pLDDT | 높을수록 (보조 지표) |

### 위치오차 (PAE)

| 컬럼 | 의미 | 좋은 값 |
|------|------|---------|
| `min_design_to_target_pae` | 바인더-타깃 최소 PAE | 낮을수록 (<5Å) |
| `min_interaction_pae` / `interaction_pae` | 복합체 최소/평균 상호작용 PAE | 낮을수록 |
| `complex_pde` / `complex_ipde` | 복합체/인터페이스 PAE | 낮을수록 |

### 구조편차 (RMSD)

| 컬럼 | 의미 | 좋은 값 |
|------|------|---------|
| `filter_rmsd` | 필터링용 RMSD(자기일관성) | 낮을수록 (<2Å 우수) |
| `designfolding-filter_rmsd` | 바인더 단독 재접힘 RMSD | 낮을수록 |
| `rmsd_design` / `rmsd_target` | 설계/타깃 백본 RMSD | 낮을수록 |
| `designability_rmsd_2` / `_rmsd_4` | RMSD ≤ 2/4Å 통과 여부(불리언) | True |

### 인터페이스 (PLIP/SASA)

| 컬럼 | 의미 | 비고 |
|------|------|------|
| `plip_hbonds_refolded` | 인터페이스 수소결합 수 | 많을수록(맥락 의존). DNA는 매우 많음 |
| `plip_saltbridge_refolded` | 염다리(이온결합) 수 | 전하 상호작용 |
| `delta_sasa_refolded` | 매몰 표면적(ΔSASA, Å²) | 클수록 넓은 접촉 |

### 개발성 (Liability — 항체/나노바디)

| 컬럼 | 의미 |
|------|------|
| `liability_score` | 종합 위험 점수 (**낮을수록 좋음**) |
| `liability_num_violations` | 위반 모티프 총 개수 |
| `liability_high/medium/low_severity_violations` | 심각도별 위반 수 |
| `liability_MetOx_count` | 메티오닌 산화 위험 |
| `liability_TrpOx_count` | 트립토판 산화 위험 |
| `liability_AspCleave/AspBridge_count` | 아스파르트산 이성질화·절단 |
| `liability_ProtTryp_count` | 단백분해 절단 부위 |
| `liability_HydroPatch_count` | 소수성 패치(응집 위험) |

### 친화도 (Affinity — 소분자)

| 컬럼 | 의미 |
|------|------|
| `affinity_pred_value` | 예측 결합 친화도(회귀값) |
| `affinity_probability_binary` (`_binary1`, `_binary2`) | 결합 이진 확률 |

### 다양성·신규성·서열

| 컬럼 | 의미 |
|------|------|
| `vendi_tm_align` 등 | 선별 집합 다양성 점수 |
| `novelty` | 학습셋 대비 신규성(FoldSeek) |
| `num_design` | 재설계된 잔기 수(설계 영역 길이) |
| `designed_sequence` / `designed_chain_sequence` | 설계 서열 |
| `largest_hydrophobic` | 최대 소수성 패치 |

### 순위 (Ranking)

| 컬럼 | 의미 |
|------|------|
| `rank_design_to_target_iptm`, `rank_design_ptm`, `rank_neg_min_design_to_target_pae`, `rank_plip_hbonds_refolded`, `rank_plip_saltbridge_refolded`, `rank_delta_sasa_refolded` | 메트릭별 순위 |
| `max_rank` → `secondary_rank` → `final_rank` | 종합 순위(최종) |
| `quality_score` | 종합 품질 점수 |

---

## A2. CLI 옵션 전체 레퍼런스 (`boltzgen run`)

### 일반
- `design_spec` (위치 인자) — YAML 파일(들) 또는 config 디렉토리
- `--protocol {protein-anything, peptide-anything, protein-small_molecule, nanobody-anything, antibody-anything, protein-redesign}` (기본 protein-anything)
- `--output OUTPUT` — 출력 디렉토리
- `--config <step> k=v ...` — 스텝별 설정 오버라이드 (예: `--config analysis num_processes=24`)
- `--devices N` / `--num_workers N` — GPU 수 / 데이터로더 워커
- `--use_kernels {auto,true,false}` — CUDA 커널(기본 auto)
- `--reuse` — 기존 결과 재사용, 부족분만 생성
- `--steps {design,inverse_folding,folding,design_folding,affinity,analysis,filtering} ...` — 부분 실행
- `--cache DIR` / `--models_token T` / `--force_download` — 모델 캐시·토큰·재다운로드

### 설계(design) 스텝
- `--num_designs N` (기본 10,000) — 생성 디자인 수
- `--diffusion_batch_size N` — 배치 크기(기본: <100이면 1, 아니면 10; 같은 배치는 길이 공유)
- `--design_checkpoints A.ckpt B.ckpt` — 백본 체크포인트(기본 diverse+adherence)
- `--step_scale` / `--noise_scale` — 디퓨전 스케줄 고정

### 역접힘(inverse folding)
- `--inverse_fold_num_sequences N` (기본 1) — 백본당 서열 수
- `--inverse_fold_avoid 'KEC'` — 금지 잔기(기본: protein 없음, peptide/nb/ab는 'C')
- `--skip_inverse_folding` / `--only_inverse_fold`
- `--inverse_fold_checkpoint C.ckpt`

### 검증(folding/affinity)
- `--folding_checkpoint D.ckpt` / `--affinity_checkpoint E.ckpt`

### 필터링(filtering)
- `--budget N` (기본 30) — 최종 선별 수
- `--alpha A` (기본 peptide 0.01, 그 외 0.001) — 품질↔다양성
- `--metrics_override metric=weight ...` — 메트릭 가중치(클수록 down-weight)
- `--additional_filters 'feat>th' 'feat<th' ...` — 하드 필터
- `--size_buckets min-max:count ...` — 크기 구간별 할당
- `--filter_biased {true,false}` — AA 조성 이상치 제거
- `--refolding_rmsd_threshold X` — RMSD 하드 필터

### 기타 서브커맨드
- `boltzgen check <yaml>` — 설계 명세 검증(designed residues + 시각화 CIF)
- `boltzgen download` — 모델 가중치 미리 받기
- `boltzgen configure` / `execute` — 설정 생성 / 사전설정 실행
- `boltzgen merge <dir1> <dir2> ... --output <merged>` — 출력 병합

---

## A3. 프로토콜 비교표

| 프로토콜 | 스텝수 | design_folding | inverse fold Cys | affinity | 용도 |
|----------|:---:|:---:|:---:|:---:|------|
| `protein-anything` | 6 | 함 | 허용 | 안 함 | 단백질→단백질/펩타이드 |
| `peptide-anything` | 5 | 안 함 | 금지 | 안 함 | (고리형) 펩타이드 |
| `protein-small_molecule` | 7 | 함 | 허용 | **함** | 단백질→소분자 |
| `nanobody-anything` | 5 | 안 함 | 금지 | 안 함 | 나노바디 CDR |
| `antibody-anything` | 5 | 안 함 | 금지 | 안 함 | 항체 Fab CDR |
| `protein-redesign` | 5 | 안 함 | 허용 | 안 함 | 기존 단백질 재설계 |

---

## A4. 설계 명세(YAML) 치트시트

```yaml
entities:
  # 설계 단백질 (서열 표기)
  - protein:
      id: B
      sequence: 80..140        # 범위 랜덤 / 120 고정 / MKLV.. 고정서열 / 3C8C6C5C3C1C2 Cys패턴
      cyclic: true             # 머리-꼬리 고리화
      secondary_structure: { helix: 5..15, sheet: 20..28 }
      residue_constraints:
        - { position: 1, allowed: A }
        - { position: 3..5, disallowed: CM }
  # 핵산
  - dna: { id: D, sequence: ATGC }
  - rna: { id: R, sequence: AUGC }
  # 소분자
  - ligand: { id: L, ccd: ATP }          # 또는 smiles: "..."
  # 타깃(파일에서 추출)
  - file:
      path: target.cif                    # YAML 위치 기준 상대경로
      include: [ { chain: { id: A } } ]   # 또는 "all"
      exclude: [ { chain: { id: A, res_index: 45..55 } } ]
      binding_types:                      # 결합부위 지정
        - chain: { id: A, binding: 95..110 }
        - chain: { id: B, not_binding: "all" }
      structure_groups:                   # visibility 0(숨김)/1(보임)/2(별도그룹)
        - group: { id: A, visibility: 1 }
      design:      [ { chain: { id: A, res_index: 11..184 } } ]
      not_design:  [ { chain: { id: A, res_index: 11,14,29,33 } } ]   # 기능 필수 잔기 고정
      design_insertions: [ { insertion: { id: A, res_index: 63, num_residues: 3..8 } } ]
      reset_res_index: [ { chain: { id: A } } ]
constraints:
  - bond: { atom1: [B, 4, SG], atom2: [B, 26, SG] }   # 이황화 등
```

**res_index 범위 문법**: `45..55`(범위) · `..10`(처음~10) · `185..`(185~끝) · `10,29,40..48`(혼합)

---

## A5. 트러블슈팅 종합 (전 챕터 함정 모음)

| 증상 | 원인 | 해결 | 참조 |
|------|------|------|------|
| `torch.cuda.is_available()==False`, "driver too old" | torch CUDA가 드라이버보다 높음(major 불일치) | 드라이버 CUDA에 맞는 빌드(cu124 등) | Ch.03 |
| `undefined symbol: cublasGemmGroupedBatchedEx` | cuBLAS < 12.5 | `nvidia-cublas-cu12>=12.5` 설치 | Ch.03 |
| `bad interpreter` / 엉뚱한 pip | pip이 다른 환경 가리킴 | `python -m pip` 사용 | Ch.03 |
| 분석 단계 CPU 폭주·PC 멈춤 | analysis `num_processes` 기본 32 | `--config analysis num_processes=24` | Ch.03·06 |
| `CUDA out of memory` | 배치/시스템 큼 | `--diffusion_batch_size` 축소, 타깃 축소, `--num_designs` 분할 후 merge | Ch.03 |
| `FileNotFoundError: ...cif` | 타깃 구조 파일 미존재 | RCSB에서 직접 다운로드 | Ch.02 |
| `Specified chain id X not in file` | mmCIF auth/label 체인ID 불일치 | RNA만 추출해 PDB로 저장 후 단일 체인 지정 | Ch.11 |
| `0/N designs passed filters` | 제약 과다/타깃 어려움 | 제약 완화, `--num_designs` 증가, 필터 조정 | Ch.06 |
| 모든 디자인이 비슷함 | 다양성 부족 | `--budget`↑, `--num_designs`↑, `--alpha`↑ | Ch.05·06 |
| RMSD 전부 높음 | 서열이 잘 안 접힘 | secondary_structure·disulfide·scaffold 추가 | Ch.07 |
| 측쇄가 원점에 뭉침 | inverse_folded 파일 시각화 | `refold_cif` 사용 | Ch.01·04 |

---

## A6. 자주 묻는 질문 (FAQ)

**Q. 챕터 노트북을 돌리려면 뭐가 필요합니까?**
A. 브라우저면 됩니다. 노트북의 설계 셀은 GPU 런타임이 필요하지만, 건너뛰면 각 챕터 `data/`에 커밋된 **레퍼런스 설계 결과(CSV·CIF)로 자동 폴백**해 분석·그래프가 그대로 이어집니다 — 그 경우 Colab 기본 런타임에서 **한 권이 몇 초** 만에 완주합니다. 설계를 **직접 돌리는 `boltzgen run`만** NVIDIA GPU에서 동작합니다(CPU 폴백이 없어 GPU가 없으면 시작 즉시 종료). 이 과정의 설계 예제는 Colab **무료 T4 런타임**에서 전부 돌아갑니다.

**Q. Colab T4에서 설계를 돌릴 때 알아둘 것이 있습니까?**
A. T4는 compute capability 7.5라 가속 커널이 **자동으로 꺼진 채 정상 실행**됩니다(`Using kernels: False`). bf16 네이티브 지원이 없어 정밀도 오류가 나면 `--config folding trainer.precision=32`로 우회하십시오. 세션 시간 제한이 있으니 `--num_designs`는 4~30으로 — Part B 실습이 실제로 이 규모입니다. Colab Pro의 **L4**(capability 8.9)면 가속 커널까지 켜집니다.

**Q. num_designs는 얼마로 잡아야 합니까?**
A. 테스트는 4~100, 일반 설계는 1,000~5,000, 어려운 타깃은 10,000~60,000. 많이 뽑을수록 좋은 디자인을 만날 확률이 올라갑니다(Ch.04).

**Q. pLDDT가 높은데 왜 순위가 낮습니까?**
A. pLDDT(`complex_plddt`)는 순위의 주 지표가 아닙니다. 순위는 ipTM·pTM·PAE·H-bond·salt-bridge·ΔSASA 종합으로 정해집니다(Ch.05).

**Q. ipTM이 0.3대인데 쓸 수 있습니까?**
A. 어려운 타깃·소규모 런에서는 0.3~0.5도 의미 있습니다. 단, 실전에선 `num_designs`를 키워 0.5+ 후보를 꼬리에서 건지십시오(Ch.09).

**Q. 결과를 실험 없이 바로 써도 됩니까?**
A. 아니요. BoltzGen은 후보를 빠르게 좁혀주는 도구입니다. 상위 후보는 반드시 실험(또는 도킹·MD)으로 검증하십시오(Ch.06).

**Q. CPU/PC가 멈춥니다.**
A. 분석 단계가 기본 32 프로세스를 띄웁니다. `--config analysis num_processes=24`로 줄이고, 필요하면 `taskset -c 0-27`로 코어를 제한하십시오(Ch.03).

**Q. 한 GPU에서 여러 설계를 동시에 돌려도 됩니까?**
A. 권장하지 않습니다. 메모리 경합으로 OOM이 나기 쉽습니다. 순차 실행 + `merge`가 안전합니다(Ch.06).

**Q. 항체/나노바디에서 ipTM만 보면 됩니까?**
A. 아니요. developability(`liability_score`)를 함께 봐야 약으로 만들 수 있습니다(Ch.08·09).

---

## A7. 용어집 (Glossary)

- **바인더(binder)**: 타깃에 결합하도록 설계된 분자.
- **백본(backbone)**: 단백질의 골격(주쇄) 구조. 서열 없이 형태만.
- **역접힘(inverse folding)**: 구조→서열 예측(접힘의 역).
- **자기일관성(self-consistency)**: 생성 구조 ↔ 재예측 구조의 일치도(품질 신호).
- **pTM / ipTM**: 예측 TM-score / 인터페이스 pTM(신뢰도).
- **PAE**: Predicted Aligned Error(위치 오차, 낮을수록 좋음).
- **pLDDT**: 잔기별 국소 신뢰도(보조 지표).
- **RMSD**: 두 구조의 좌표 차이(Å).
- **CDR**: 항체·나노바디의 항원 결합 loop(H1/H2/H3, L1/L2/L3).
- **scaffold**: 재사용하는 검증된 골격 구조(CDR만 재설계).
- **cystine knot**: 이황화 3쌍이 얽힌 초안정 구조.
- **developability / liability**: 약으로 만들 수 있는 정도 / 그 위험 모티프.
- **affinity**: 결합 친화도(세기).
- **CCD**: PDB 화학성분 사전 3글자 코드(소분자).
- **SMILES**: 분자 구조의 텍스트 표현.
- **diffusion**: 노이즈에서 점진적으로 구조를 생성하는 방식.
- **any-modality**: 단백질·핵산·소분자 등 **어떤 종류의 타깃이든** 같은 방식으로 입력받는 것(BoltzGen의 핵심 특징).
- **all-atom**: 백본뿐 아니라 측쇄·리간드 원자까지 포함한 **전체 원자** 구조. BoltzGen 출력이 all-atom.
- **BoltzGen (Design)**: 백본·all-atom 구조를 생성하는 본체 모델(`diverse`+`adherence` 체크포인트).
- **BoltzIF**: 서열 재설계(inverse folding) **전용 모델의 공식 이름**(= `boltzgen1_ifold`).
- **Boltz-2**: 구조 예측(refolding)과 친화도 예측을 담당하는 모델(`boltz2_conf_final`).
- **refolding**: 설계 서열을 Boltz-2로 다시 접어 의도한 복합체가 형성되는지 검증하는 단계(본 과정의 `folding`).
- **Atomic / Token / Pairwise Features**: 입력을 **원자 / 잔기(토큰) / 잔기쌍** 3계층으로 인코딩한 표현. any-modality를 하나로 다루는 비결(Ch.01.5).
- **helicon**: 스테이플(staple)로 고정한 나선형 펩타이드. 논문 출력 예시(Helicon–Protein) 중 하나.
- **ΔSASA (delta SASA)**: 결합으로 묻히는 용매 접근 표면적 변화(Å², 클수록 넓은 접촉).

---

## A8. 재현 환경 (Reproducibility)

이 과정의 수치·그래프가 **어디서 나왔는지**를 밝혀 둡니다. 재현하려고 같은 사양을 갖출 필요는 없습니다 — 노트북은 아래 산출물을 읽어 쓰기 때문입니다.

| 항목 | 값 |
|------|-----|
| BoltzGen | 0.3.2 |
| 설계 실행 환경 | NVIDIA GPU 24GB / CUDA 12.4 / PyTorch cu124 |
| 노트북 실행 환경 | Python 3.12 + pandas · matplotlib · gemmi (GPU 미사용) |
| 노트북 실행 시간 | 분석 셀 기준 한 권당 3~19초 (전 셀 실행, 실측) |
| 설계 실행 시간 | `num_designs 4` 6스텝 **307초** (가중치 캐시 상태, 실측) |
| 커밋된 결과 | `05·07·08·09·10·11`의 `data/` — `all_designs_metrics.csv`, `final_designs_metrics_10.csv`, `final_designs/rank*.cif`, `steps.yaml` |
| 실습 복합체 크기 | 158~372 토큰 (소분자 158 · cyclotide 174 · DNA 252 · vanilla 269 · 나노바디 321 · Fab 350~372) |
| 설계 피크 VRAM | **9.9GB** — 이 과정에서 가장 큰 Fab 예제(`num_designs 8`)를 **가속 커널 끄고**(T4와 같은 조건) 돌려 측정한 값. 16GB 카드에 들어갑니다. |

> **노트북 검증 환경** — 26개 노트북은 Colab 런타임과 같은 조건(**Ubuntu 22.04 · Python 3.12 · conda 없이 pip/apt만**)의 컨테이너에서, 저장소 클론부터 패키지 설치까지 **처음부터 끝까지 실제로 실행해** 확인했습니다.

> **토큰 세는 법** — 위 값은 각 실습의 **rank 1 디자인(설계 + 타깃)** 기준입니다. 단백질·DNA·RNA 같은 **폴리머는 잔기 1개 = 토큰 1개**지만, **소분자 리간드는 원자 1개 = 토큰 1개**로 쪼개집니다(BoltzGen이 비폴리머를 원자 단위로 토큰화하기 때문). 그래서 소분자 실습(Ch.10)의 158토큰은 *단백질 142잔기 + TSA 리간드 16원자*입니다 — 리간드를 "1잔기"로 세면 143이 되는데, 그것은 모델이 실제로 보는 토큰 수가 아닙니다.

설계 규모: vanilla·cyclotide 100개, Fab·나노바디·소분자·DNA·RNA 각 30개(`--budget 10`).

---

본문으로 → **[00. 과정 개요](../00_README.md)**
