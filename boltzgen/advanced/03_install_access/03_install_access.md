---
title: "Ch.03 — 툴 설치 및 접근: 로컬·클라우드·CUDA 트러블슈팅"
chapter: 3
level: advanced
language: ko
---

# Ch.03 — 툴 설치 및 접근

이번 챕터는 조금 실무적이에요. BoltzGen을 **실제로 내 환경에 올리는** 방법을 다룹니다. 그런데 솔직히 말하면, 딥러닝 도구 설치에서 가장 골치 아픈 건 패키지 설치 자체가 아니라 **GPU·CUDA 버전 정합**이에요. 여기서 막혀서 며칠을 날리는 경우가 정말 많거든요.

그래서 이 챕터는 단순 설치 가이드를 넘어, **실제로 우리가 이 과정을 준비하며 겪은 CUDA 트러블슈팅을 케이스 스터디로** 풀어드릴게요. 똑같은 함정에 빠지지 않도록요.

> **실습 — `03_setup_check.ipynb`** · **전 셀 19초**
>
> 이 챕터의 설치·검증(설치 → nvidia-smi → torch → cuequivariance 커널 → `boltzgen check`)을 그대로 담고 있어요. Colab에서 **런타임 → T4 GPU**로 바꾸면 `pip install boltzgen`부터 검증까지 실제로 돌아갑니다(cuBLAS ≥ 12.5 보강 셀 포함).

---

## 3.1 어디서 돌릴까요? — 로컬 vs 클라우드

먼저 큰 그림부터. BoltzGen을 돌릴 수 있는 환경은 크게 세 가지예요.

| 환경 | 장점 | 단점 | 추천 상황 |
|------|------|------|-----------|
| **Colab** | 설치 없이 브라우저에서 바로. 무료 T4 GPU 런타임 제공 | 세션 시간·유휴 제한 | 이 과정의 실습 전부, 소규모 설계 |
| **로컬 GPU 워크스테이션** | 빠르고, 데이터가 내 손안에, 비용 통제 | 환경 구성 필요 | 반복 실험, 대규모 설계, 민감 데이터 |
| **클라우드 GPU**(AWS/GCP/Lambda 등) | 큰 GPU를 필요할 때만 | 시간당 과금, 데이터 전송 | 일시적 대규모 작업 |

세 환경 모두 아래 3.2~3.4가 똑같이 적용돼요. 설치 방식은 동일하고, 다른 건 **어느 GPU 위에서 도느냐**뿐이에요.

디스크는 어느 환경이든 필요해요. BoltzGen은 모델 가중치만 약 6GB, 결과는 프로젝트에 따라 수 GB~수십 GB까지 쓰니 **최소 20~30GB 여유**를 확보하세요.

---

## 3.1.5 실행 로그와 메모리 — 알아둘 것 세 가지

설치를 마치고 처음 `boltzgen run`을 돌리면 로그에 낯선 줄들이 지나가요. 그중 **셋만 알면** 실행을 통제할 수 있어요.

### ① `Using kernels` — 가속 커널은 GPU 세대에 따라 켜지고 꺼져요

```
Using kernels: False [device capability: (7, 5)]
```

`--use_kernels auto`(기본값)일 때, BoltzGen은 **compute capability가 8 이상인 GPU에서만** cuequivariance 가속 커널을 씁니다. T4(7.5) 같은 이전 세대에서는 알아서 꺼요 — **꺼진 채로 정상 실행되고**, 가속만 빠지니 조금 느려질 뿐이에요. (덕분에 3.3에서 다룰 `cublasGemmGroupedBatchedEx` 커널 오류도 이 경우엔 아예 안 터져요.)

> 심화 — `design`·`folding`·`affinity` 단계의 기본 정밀도는 **`bf16-mixed`** 인데, bf16 네이티브 지원은 capability 8.0(Ampere) 이상이에요. T4·V100에서 정밀도 관련 오류가 나면 해당 단계만 32비트로 바꿔 우회하세요: `--config folding trainer.precision=32`.

### ② `Using diffusion batch size` — 유일하게 신경 쓸 메모리 레버

```
Using diffusion batch size: 1
```

이 값을 지정하지 않으면 BoltzGen이 **`num_designs`가 100 미만이면 1, 100 이상이면 10**으로 자동 결정해요. 배치 10이면 백본을 10개씩 동시에 생성하니 메모리 사용량이 확 뜁니다. 즉 **99 → 100으로 늘리는 순간이 분기점**이에요.

```bash
# 100개 이상 뽑는데 메모리가 빠듯하면 배치를 명시
boltzgen run spec.yaml --output out --protocol protein-anything \
  --num_designs 100 --budget 10 --diffusion_batch_size 1
```

이 과정의 실습 예제는 전부 `num_designs` 4~30이라 **자동으로 배치 1**이고, 그래서 이 옵션을 쓸 일이 없어요. 프로덕션 규모로 키울 때 기억해 두면 되는 값이에요.

### ③ 큰 작업은 쪼개고 합치기

메모리가 모자라거나 중간에 끊길 위험이 있으면, 나눠 돌린 뒤 합치는 게 정석이에요.

```bash
boltzgen run spec.yaml --output batch1 --num_designs 50
boltzgen run spec.yaml --output batch2 --num_designs 50
boltzgen merge batch1 batch2 --output merged
```

`CUDA out of memory`가 뜨면 이 두 가지(②·③)를 먼저 시도하고, 그래도 안 되면 타깃에서 불필요한 체인을 덜어내 크기를 줄이세요(Ch.02).

> 참고 — 파이프라인에서 가장 무거운 **folding 단계는 내부적으로 `batch_size: 1`이 고정**이에요. 디자인을 몇 개 뽑든 GPU에 한 번에 올라가는 건 복합체 하나예요. 그래서 `num_designs`를 키울 때 늘어나는 건 메모리가 아니라 **시간**입니다.

---

## 3.2 로컬 설치 — conda + pip

설치 자체는 간단해요. conda로 깨끗한 환경을 만들고 BoltzGen을 설치하면 돼요.

```bash
# 1) 전용 가상환경 (Python 3.12 권장; BoltzGen은 3.11+ 요구)
conda create -n boltzgen_env python=3.12 -y
conda activate boltzgen_env

# 2-A) PyPI에서 설치 (가장 간단)
pip install boltzgen

# 2-B) 또는 레포를 클론해 editable 설치 (예제·소스가 함께 필요하면 권장)
git clone https://github.com/HannesStark/boltzgen.git
cd boltzgen
python -m pip install -e .
```

**왜 `python -m pip`를 쓰나요?** 시스템에 여러 파이썬·pip이 섞여 있으면, 그냥 `pip`이 엉뚱한(다른 환경의) pip을 가리키는 일이 생겨요. 실제로 우리도 `~/.local/bin/pip`이 삭제된 환경을 가리키고 있어서 `bad interpreter` 오류가 났었어요. `python -m pip`는 **지금 활성화된 환경의 파이썬에 딸린 pip**을 확실히 쓰게 해줘서 이런 사고를 막아줘요. 습관으로 들이면 좋아요.

설치되는 주요 의존성: PyTorch, CUDA 라이브러리들(nvidia-cublas-cu12 등), Biotite/Biopython(생물정보학), RDKit(화학), cuequivariance(가속 커널), PyTorch Lightning, gemmi 등 수십 개예요. 전부 합쳐 3~5GB라 시간이 좀 걸려요.

---

## 3.3 (핵심) GPU·CUDA 의존성 — 왜 여기서 막히나

이 절이 이 챕터의 진짜 핵심이에요. **드라이버 ↔ PyTorch ↔ cuequivariance ↔ cuBLAS**, 이 네 가지의 CUDA 버전이 서로 맞아야 GPU가 동작해요. 하나라도 어긋나면 "설치는 됐는데 GPU를 못 쓰는" 상황이 벌어져요.

### 먼저 개념: CUDA 버전이 왜 여러 개인가

GPU를 쓰려면 세 층이 맞물려야 해요.

```
[ NVIDIA 드라이버 ]  ← 이게 지원하는 "최대 CUDA 버전"이 정해져 있음
        ▲
[ CUDA 런타임/라이브러리 ]  ← PyTorch가 번들로 들고 옴 (cu124, cu126, cu130 …)
        ▲
[ PyTorch / cuequivariance ]  ← 위 라이브러리에 링크되어 동작
```

핵심 규칙 두 가지.

1. **드라이버가 지원하는 CUDA보다 높은 CUDA로 빌드된 PyTorch는 못 돌아가요.** (예: 드라이버가 CUDA 12.4까지 지원하는데 PyTorch가 CUDA 13용이면 GPU 인식 실패)
2. **같은 major 버전(12.x) 안에서는 forward minor 호환**이 돼요. (드라이버가 12.4여도 12.6용 라이브러리는 대체로 돌아감. 하지만 12 → 13처럼 major가 바뀌면 안 됨)

드라이버가 지원하는 CUDA는 이렇게 확인해요.

```bash
nvidia-smi      # 우상단 "CUDA Version: 12.4" 가 드라이버가 지원하는 상한
```

### 케이스 스터디: 우리가 실제로 겪은 두 번의 실패

이 과정을 준비하면서 환경을 새로 구성했는데, **두 번 연속으로 막혔어요.** 그 과정을 그대로 보여드릴게요 — 여러분이 똑같이 겪을 가능성이 높거든요.

**실패 ①: GPU를 아예 못 봄**

`pip install`을 하면 pip이 **가장 최신 PyTorch**를 끌어와요. 그게 하필 `torch 2.12.0+cu130`(CUDA 13 번들)이었어요. 그런데 우리 드라이버(550.x)는 **CUDA 12.4까지만** 지원해요. 결과는.

```python
>>> import torch
>>> torch.cuda.is_available()
UserWarning: CUDA initialization: The NVIDIA driver on your system is too old (found version 12040)...
False
```

`torch.version.cuda`가 `13.0`으로 찍혔어요. CUDA 13은 더 높은 드라이버를 요구하니, **major 버전 불일치**로 GPU를 못 쓰는 거예요.

→ **해결**: PyTorch를 드라이버가 지원하는 CUDA 빌드로 교체. 드라이버가 12.4니까 `cu124` 빌드를 명시했어요.

```bash
python -m pip install "torch==2.6.0" \
  --index-url https://download.pytorch.org/whl/cu124 \
  --extra-index-url https://pypi.org/simple
```

이걸로 `torch 2.6.0+cu124`, `torch.cuda.is_available() == True`가 됐어요. 하지만...

**실패 ②: import는 되는데 design 단계에서 죽음**

torch는 고쳤는데, 막상 `boltzgen run`을 돌리니 1단계(design)에서 이런 오류로 죽었어요.

```
Error while loading libcue_ops.so: undefined symbol: cublasGemmGroupedBatchedEx, version libcublas.so.12
ImportError: Error importing triangle_multiplicative_update from cuequivariance_ops_torch.
```

원인이 흥미로워요. BoltzGen의 가속 커널 `cuequivariance_ops`는 **cuBLAS 12.5 이상에서 추가된 함수**(`cublasGemmGroupedBatchedEx`)를 필요로 해요. 그런데 우리가 깐 `torch 2.6.0+cu124`는 **cuBLAS 12.4**를 번들로 들고 왔거든요. 12.4에는 그 함수가 없으니, 커널 로딩이 실패한 거예요. (실제로 `cuequivariance_ops_cu12`의 의존성을 보면 `nvidia-cublas-cu12>=12.5`를 요구해요.)

→ **해결**: cuBLAS만 12.5 이상으로 올려요. cuBLAS는 12.x 안에서 하위 호환이라 torch도 그대로 잘 돌아가요.

```bash
python -m pip install "nvidia-cublas-cu12==12.9.2.10"
```

검증하면 이제 둘 다 통과해요.

```python
>>> import torch; torch.cuda.is_available()
True
>>> from cuequivariance_ops_torch import triangle_multiplicative_update   # 성공!
```

> 주의 — pip이 "torch 2.6.0은 cublas 12.4.5.8을 요구한다"고 **경고**를 띄울 거예요. 하지만 cuBLAS는 12.x 안에서 하위 호환이라 실제로는 문제가 없어요(우리가 design·folding 단계까지 전부 정상 동작을 확인했어요). 이 경고는 무시해도 돼요.

### 정리: CUDA 정합 체크리스트

| 점검 | 명령 | 통과 조건 |
|------|------|-----------|
| 드라이버 CUDA 상한 | `nvidia-smi` | "CUDA Version: 12.x" 확인 |
| PyTorch CUDA 빌드 | `python -c "import torch; print(torch.version.cuda)"` | 드라이버 상한 이하의 12.x |
| GPU 인식 | `python -c "import torch; print(torch.cuda.is_available())"` | `True` |
| cuequivariance 커널 | `python -c "from cuequivariance_ops_torch import triangle_multiplicative_update"` | 오류 없음 |
| cuBLAS 버전 | `python -m pip show nvidia-cublas-cu12` | `>= 12.5` |

이 다섯 줄만 통과하면, 설치 문제의 95%는 이미 해결된 거예요.

---

## 3.4 모델 가중치 다운로드

BoltzGen은 첫 실행 시 모델 가중치를 **HuggingFace Hub에서 자동으로** 받아요. 약 6GB이고, 한 번 받으면 캐시(`~/.cache/huggingface/`)에 저장돼 재사용돼요. 받아지는 아티팩트.

```
boltzgen1_diverse.ckpt / boltzgen1_adherence.ckpt   (백본 생성)
boltzgen1_ifold.ckpt                                 (역접힘)
boltz2_conf_final.ckpt                               (구조 검증)
+ inference-data (mols.zip 등 보조 데이터)
```

미리 받아두고 싶으면 `boltzgen download`를 쓰면 돼요. 관련 옵션.

```bash
boltzgen download                 # 미리 가중치 받기
# 실행 시 옵션
#   --cache <DIR>        : 모델 캐시 위치 지정 (기본 ~/.cache)
#   --models_token <T>   : HuggingFace 토큰 (rate limit 완화·빠른 다운로드)
#   --force_download     : 재다운로드
```

> 심화 — `HF_TOKEN`을 설정하면 익명 요청보다 다운로드가 빠르고 rate limit이 완화돼요. 로그에 `Warning: You are sending unauthenticated requests to the HF Hub`가 보이면 토큰을 안 쓰고 있는 거예요(동작엔 문제 없지만 느릴 수 있어요).

---

## 3.5 클라우드 · Colab · API 기반 실행

### 클라우드 GPU

원리는 로컬과 같아요. GPU 인스턴스(예: A100/L4)를 띄우고, 3.2~3.4를 그대로 하면 돼요. 단, **그 인스턴스의 드라이버가 지원하는 CUDA**에 맞춰 PyTorch 빌드를 고르는 게(3.3) 똑같이 중요해요. 클라우드 이미지는 보통 최신 드라이버라 cu124~cu126이 무난해요.

대규모 작업은 SLURM 같은 스케줄러로 배치 제출을 많이 해요. 예시.

```bash
#!/bin/bash
#SBATCH --job-name=boltzgen
#SBATCH --gpus=1
#SBATCH --time=24:00:00
#SBATCH --mem=64G
source activate boltzgen_env
boltzgen run design.yaml --num_designs 50000 --budget 500 --output ${SLURM_JOB_ID}
```

### Colab — 이 과정의 기본 실습 환경

**(A) 챕터 노트북 — 런타임 기본값 그대로**

실습 랩(04·05·07~11)의 노트북은 **설계 셀이 여러분의 결과를 `my_run/`에 만들고, 분석 셀이 그 결과를 읽어** 표·그래프를 그려요. 설계 셀을 건너뛰거나 실패하면 **커밋된 레퍼런스 결과**(`data/`의 CSV·CIF)로 자동 폴백하니 실습이 끊기지 않아요. 첫 셀부터 그대로 실행하면 되고, 설계 셀을 빼면 노트북 한 권이 **몇 초** 만에 완주합니다.

**(B) 설계까지 직접 — 무료 T4 GPU 런타임**

`boltzgen run`을 돌려보려면 **런타임 → 런타임 유형 변경 → T4 GPU**로 바꾸세요. 무료 티어에서 받을 수 있는 GPU예요.

```python
# Colab 셀 (런타임 → GPU 선택 후)
!pip -q install boltzgen

# 어떤 GPU를 받았는지, 가속 커널이 켜지는지 확인
import torch
cap = torch.cuda.get_device_capability()
print(torch.cuda.get_device_name(0), "| compute capability:", cap)
print("가속 커널:", "ON" if cap[0] >= 8 else "OFF (자동 비활성 — 정상 동작, 조금 느림)")

# 전 단계가 도는지 작은 규모로 확인
!boltzgen run example/vanilla_protein/1g13prot.yaml \
  --output workbench/smoke --protocol protein-anything \
  --num_designs 4 --budget 2
```

T4는 compute capability 7.5라 가속 커널이 자동으로 꺼진 채 돌아요(3.1.5의 ①). 무료 티어는 세션 시간·유휴 제한이 있으니 `--num_designs`는 **4~30** 정도로 두세요 — Part B의 실습 예제가 실제로 이 규모예요.

> 함정 — T4·V100은 bf16 네이티브 지원이 없어요. 정밀도 관련 오류가 뜨면 `--config folding trainer.precision=32`(필요하면 `design`·`affinity`도 동일하게)를 붙여 32비트로 우회하세요. Colab **Pro의 L4(capability 8.9)** 면 가속 커널까지 켜집니다.

수천~수만 개 규모의 대규모 설계는 세션 제한 때문에 로컬/클라우드 GPU가 편해요.

### 프로그램적 접근(파이썬)

BoltzGen은 CLI가 1급 인터페이스지만, 파이썬에서 `subprocess`로 감싸 **파이프라인을 자동화**하는 방식을 많이 써요. 결과 CSV를 pandas로 바로 분석하고요(Ch.05·Ch.06).

```python
import subprocess, pandas as pd
subprocess.run([
    "boltzgen","run","design.yaml","--output","out",
    "--protocol","protein-anything","--num_designs","1000","--budget","50",
], check=True)
df = pd.read_csv("out/final_ranked_designs/all_designs_metrics.csv")
```

---

## 3.6 설치 검증 — 한 번에 확인하기

설치가 끝나면 아래를 순서대로 확인하세요. (노트북 `03_setup_check.ipynb`에 그대로 들어 있어요.)

```bash
# 1) 버전
boltzgen --version            # 예: boltzgen 0.3.2

# 2) 서브커맨드 확인
boltzgen --help               # run / configure / execute / download / check / merge

# 3) GPU·커널 (3.3의 다섯 줄)
python -c "import torch; print('cuda', torch.cuda.is_available(), torch.version.cuda)"
python -c "from cuequivariance_ops_torch import triangle_multiplicative_update; print('kernel ok')"

# 4) 설계 명세 검증 (가벼운 엔드투엔드 체크)
boltzgen check example/vanilla_protein/1g13prot.yaml
#   → Total designed residues: NN
#   → Design specification visualization is written to 1g13prot.cif
```

마지막으로, 작은 규모로 **전체 파이프라인이 끝까지 도는지** 한 번 돌려보세요(첫 실행이라 모델 다운로드 포함).

```bash
boltzgen run example/vanilla_protein/1g13prot.yaml \
  --output workbench/smoke_test --protocol protein-anything \
  --num_designs 4 --budget 2
```

`num_designs 4`면 모델 로딩까지 포함해 **수 분**이면 끝나요. 6스텝(design→inverse_folding→folding→design_folding→analysis→filtering)이 전부 `completed successfully`로 찍히면 환경 구성 끝이에요.

---

## 3.7 흔한 설치 오류와 해결

| 증상 | 원인 | 해결 |
|------|------|------|
| `torch.cuda.is_available() == False`, "driver too old" | PyTorch CUDA가 드라이버보다 높음(major 불일치) | 드라이버 CUDA에 맞는 빌드로 재설치(예: cu124) |
| `undefined symbol: cublasGemmGroupedBatchedEx` | cuBLAS < 12.5 (cuequivariance 요구 미달) | `nvidia-cublas-cu12>=12.5` 설치 |
| `bad interpreter` / 엉뚱한 pip | `pip`이 다른(삭제된) 환경을 가리킴 | `python -m pip` 사용 |
| `CUDA out of memory` | 배치/시스템이 너무 큼 | `--diffusion_batch_size` 축소, 타깃 크기 축소, `--num_designs` 분할 후 `merge` |
| 모델 다운로드 느림/실패 | HF rate limit | `HF_TOKEN`/`--models_token` 설정, `--force_download` |
| `FileNotFoundError: ...cif` | 타깃 구조 파일 미존재 | RCSB에서 직접 다운로드(Ch.02) |

> 심화 — GPU 메모리가 부족할 때 가장 효과적인 건 `--num_designs`를 쪼개 여러 번 돌린 뒤 `boltzgen merge`로 합치는 거예요. 예: 1000개씩 3번 → `boltzgen merge batch1 batch2 batch3 --output merged`. 큰 작업을 안정적으로 끝내는 실전 패턴이에요(Ch.06).

---

### 이 챕터 핵심 요약

1. 설치는 `conda create → pip install (또는 -e .)`로 간단하지만, **진짜 관문은 CUDA 정합**이에요.
2. **드라이버 ↔ torch ↔ cuequivariance ↔ cuBLAS** 네 층의 CUDA 버전을 맞추세요. 드라이버 상한(`nvidia-smi`)에 맞는 torch 빌드를 고르고(major 일치), cuBLAS는 **12.5 이상**으로.
3. 우리가 겪은 2단 함정(① CUDA13 torch로 GPU 미인식 → cu124 교체, ② cuBLAS 12.4로 커널 실패 → cuBLAS 12.9로 해결)을 기억하면 똑같이 막혔을 때 5분이면 풀려요.
4. 설치 후 **3.6의 검증 시퀀스**(version·help·cuda·kernel·check·smoke test)를 습관처럼 돌리세요.

다음 → **[04. 기본 사용법](../04_basic_usage/04_basic_usage.md)**
