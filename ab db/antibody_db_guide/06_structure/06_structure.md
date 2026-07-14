---
title: "Ch.06 — 구조예측 (IgFold)"
chapter: 6
level: hands-on
language: ko
part: B
---

# Ch.06 — 항체 구조예측 (IgFold)

서열만으로는 항원에 어떻게 붙는지, CDR loop가 어떤 모양인지 알 수 없어요. 그래서 **구조예측**이 필요해요. 항체 전용 딥러닝 구조예측 도구 **IgFold**로 demo 항체의 Fv 구조를 **직접 예측**해봅니다.[18][19]

> **실습 — [`06_structure_lab.ipynb`](06_structure_lab.ipynb)** · **전 셀 실행 16초** — IgFold를 **직접 실행**해 `my_run/demo_antibody_igfold.pdb` 를 만들고, 커밋된 예측 구조와 **CA-RMSD**로 대조해요. (예측 자체는 CPU에서 9초로 측정 — 이 노트북에서 가장 무거운 단계예요.)

---

## 6.1 IgFold로 예측하기 — 직접 실행

IgFold는 항체 언어모델(AntiBERTy) + graph network로 backbone 좌표를 빠르게 예측해요. 예측 PDB의 **B-factor 컬럼에 잔기별 예측오차(Å)**를 적어줘서, "어디를 못 믿겠는지"를 바로 알 수 있어요.

```bash
python scripts/run_igfold_demo.py --fasta data/demo_mab.fa --out my_run/demo_antibody_igfold.pdb
```

스크립트 알맹이는 이게 전부예요.

```python
import torch
torch.load = (lambda f: (lambda *a, **k: f(*a, **{**k, "weights_only": False})))(torch.load)  # ① 참고
from igfold import IgFoldRunner
seqs = {"H": "EVQLQQSGAE...VTVSA", "L": "DIQMTQSPSS...TKVEIK"}
IgFoldRunner().fold("my_run/demo_antibody_igfold.pdb", sequences=seqs,
                    do_refine=False, do_renum=True)
```

> **주의** — **실제로 겪은 3가지 함정**(Ch.03의 3.3에 상세).
> ① torch≥2.6의 `weights_only=True` → 체크포인트 로드 실패. `torch.load`를 `weights_only=False`로 감싸요.
> ② **최신 transformers(5.x)에서는 체크포인트 unpickle 이 실패해요**(`Trie`·`BasicTokenizer` AttributeError) → **`transformers==4.36.2`** 로 고정(노트북 부트스트랩이 자동으로 맞춰 줍니다).
> ③ torch가 시스템 드라이버보다 최신 CUDA로 빌드됐으면 GPU 초기화가 실패해요 → 스크립트의 `--cpu`(=`CUDA_VISIBLE_DEVICES=""`)로 우회.

---

## 6.2 실행 결과 — 예측 신뢰도 프로파일

예측된 Fv는 **1,115 atoms** (중쇄 120잔기 + 경쇄 107잔기). 사슬별 예측오차는 이래요.

| 사슬 | 잔기 수 | 평균 예측오차 | 최대 예측오차 |
|------|---------|---------------|---------------|
| Heavy (H) | 120 | **0.44 Å** | **2.65 Å** |
| Light (L) | 107 | **0.28 Å** | 0.89 Å |

![demo mAb Fv 구조 예측 신뢰도 프로파일](06_structure_confidence.png)

*그림. IgFold가 예측한 demo mAb Fv의 잔기별 신뢰도 프로파일. 가로축은 잔기 번호, 세로축은 PDB B-factor 컬럼에 기록된 예측오차(Å, 낮을수록 신뢰도 높음). 보라색 선이 중쇄(H, 평균 0.44 Å), 주황색 선이 경쇄(L, 평균 0.28 Å), 빨간 점선(1 Å)은 "신뢰할 만함" 기준선이에요. (이미지: `06_structure_confidence.png`)*

**그림 읽는 법** — 대부분의 잔기가 빨간 1 Å 선 아래에 깔려 있어요(신뢰도 높음). 그런데 중쇄(보라)에서 딱 한 곳만 2.65 Å까지 솟구치는 봉우리가 보이는데, 잔기 번호를 보면 **CDR-H3 구간**이에요. 즉 IgFold도 "framework·경쇄 골격은 확신하지만 CDR-H3 loop의 정확한 형태는 자신 없다"고 말하는 거예요. 경쇄(주황)는 전 구간이 1 Å 아래로 평탄해서 가장 안정적으로 예측됐고요. 그래서 이 후보를 다룰 땐 **framework·경쇄 좌표는 신뢰하되, CDR-H3는 ImmuneBuilder 등으로 교차검증**하는 게 안전해요.

같은 예측오차를 **3D 구조에 입히면** 훨씬 직관적이에요.

![IgFold 예측 Fv 구조 — 예측오차 컬러링](06_structure_3d.png)

*그림. IgFold가 예측한 demo mAb Fv의 3D cartoon(PyMOL 렌더). 색은 위 선그래프와 동일한 잔기별 예측오차(B-factor)로, **파랑 = 낮음(신뢰)·빨강 = 높음(불확실)** 스펙트럼이에요. 두 개의 β-sheet 면역글로불린 도메인(VH·VL)이 맞물린 전형적 Fv 모양이고, 윗부분에 빨간 loop 하나가 도드라져요. (이미지: `06_structure_3d.png`)*

**그림 읽는 법** — 구조 거의 전체가 파랑(예측오차 < 1 Å)인데 위쪽에 딱 하나 빨간 loop가 튀죠 — 그게 **CDR-H3**예요. 선그래프의 2.65 Å 봉우리가 3D에서는 바로 이 빨간 loop로 나타나는 거예요. "골격은 단단히 예측됐고, 항원 결합을 좌우하는 CDR-H3만 형태가 불확실하다"를 **2D 그래프와 3D 구조 두 방식으로 동일하게** 확인하는 셈이에요.

> **주의** — **이 3D 그림만은 여러분이 노트북에서 다시 만들 수 없어요.** PyMOL은 pip로 설치되지 않아서(Colab 불가) 이 절은 **커밋된 렌더 이미지**를 그대로 보여줍니다. 대신 렌더 스크립트(`scripts/render_06_structure.pml`)와 입력 PDB가 저장소에 있으니, 로컬에 open-source PyMOL이 있으면 노트북이 자동으로 다시 렌더해요(`pymol -cq scripts/render_06_structure.pml`). 위의 **선그래프는 여러분의 예측 결과로 직접 그립니다.**

---

## 6.2b 내 예측이 맞게 나왔나 — 레퍼런스와 대조

노트북 4절이 **내 예측 PDB와 커밋된 예측 PDB를 CA-RMSD로 비교**해요. 같은 서열·같은 모델이라도 BLAS·스레드 수에 따라 좌표가 소수점 단위로 흔들릴 수 있어서, "완전 동일"이 아니라 **RMSD로** 보는 게 맞아요.

| 비교 항목 | 값 |
|-----------|-----|
| CA 원자 수 | 227 (내 결과 = 레퍼런스) |
| **CA-RMSD (내 예측 vs 커밋 예측)** | **0.002 Å** |
| 사슬별 예측오차 | H: mean 0.44 / max 2.65 Å · L: mean 0.28 / max 0.89 Å (양쪽 동일) |

0.002 Å면 사실상 같은 구조예요 — **IgFold 예측은 결정론적으로 재현됩니다.**

> **심화** — 그래프에서 중쇄에 **2.65 Å짜리 뾰족한 봉우리**가 보일 거예요. 위치를 보면 **CDR-H3 부근**이에요. Ch.01에서 "CDR-H3는 길이·서열 다양성이 가장 크다"고 했죠 — 그래서 구조예측도 여기서 가장 불확실해요. 반대로 framework와 경쇄는 0.3~0.4 Å로 매우 신뢰도가 높아요(< 1 Å). **"전체 구조는 믿되, CDR-H3 loop는 조심"**이 정확한 해석이에요.

---

## 6.3 주의 — 예측 구조를 과신하지 마세요

- 예측 구조는 **실험 구조가 아니에요**. 보고서에서 실험 구조처럼 단정하면 안 돼요.
- CDR-H3·long loop·unusual antibody는 불확실성이 커요(위 2.65 Å가 그 증거).
- 항체 단독 구조 예측이 **항원 결합 pose를 보장하지 않아요** — 결합 분석은 복합체 구조로(Ch.07).

---

## 6.4 ImmuneBuilder와 교차검증

IgFold 외에 OPIG의 **ImmuneBuilder**(ABodyBuilder2/NanoBodyBuilder2/TCRBuilder2)도 있어요.[20] 두 모델을 함께 쓰면 신뢰도를 교차검증할 수 있어요.

1. 같은 VH/VL을 두 모델로 예측
2. framework RMSD와 CDR RMSD 비교
3. **CDR-H3 orientation 차이** 확인 (여기서 갈리면 불확실성 큼)
4. 구조적 불확실성이 큰 후보는 후순위로

> **심화** — TAP(Ch.08 developability profiler)는 내부적으로 ABodyBuilder2로 구조 모델을 만들어 developability를 평가해요 — 구조예측이 developability 분석의 입력이 되는 셈이에요.

---

### 이 챕터 핵심 요약

1. IgFold로 demo Fv를 **직접 예측**(**1,115 atoms**, CPU 9초 실측) — B-factor에 잔기별 예측오차가 들어 있어요.
2. framework·경쇄는 0.3~0.4 Å로 신뢰도 높고, **CDR-H3에서 2.65 Å로 가장 불확실** — 이론과 정확히 일치.
3. 내 예측 vs 커밋된 예측 **CA-RMSD 0.002 Å** — 재현성 확인.
4. 설치 함정(torch `weights_only`·**transformers 4.36.2 고정**·CUDA)은 Ch.03 회피책으로 해결. **PyMOL 3D 렌더만 pip 불가 → 커밋 이미지 사용.**
5. 예측≠실험. CDR-H3는 조심하고, ImmuneBuilder로 교차검증, 결합은 복합체로 확인.

다음 → **[07. 항원-항체 interface 분석](../07_interface/07_interface.md)**
