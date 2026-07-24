---
title: "Ch.03 — 분석 환경 구축"
chapter: 3
level: intro
language: ko
part: A
---

# Ch.03 — 분석 환경 구축

항체 분석 도구는 의존성 충돌이 정말 잦습니다. ANARCI는 HMMER 실행파일을, IgFold는 특정 torch/transformers를, FreeSASA/PLIP는 또 다른 스택을 요구하기 때문입니다. 이 챕터는 **브라우저(Colab)에서 바로 시작하는 경로**를 먼저 깔고, 로컬에서 반복 실행할 때 쓰는 conda 환경 3종을 이어서 다룹니다.

> **실습 — [`03_setup_check.ipynb`](03_setup_check.ipynb)** · **전 셀 실행 3초** — import 여부만 보는 것이 아니라 **ANARCI를 실제로 한 번 돌려** numbering 결과가 나오는지 확인하고, 정답지(`data/setup_expected.csv`)와 대조합니다.

---

## 3.0 브라우저에서 바로 시작 — Colab 설치 두 줄

노트북 첫 셀(부트스트랩)이 아래를 자동으로 해줍니다. 손으로 칠 일은 없지만, **무슨 일이 일어나는지는 알아야** 문제가 생겼을 때 고칠 수 있습니다.

```bash
!apt-get -qq install -y hmmer        # ANARCI가 호출하는 hmmscan 실행파일
!pip -q install anarci abnumber
```

> **주의** — **`pip install anarci` 만으로는 돌아가지 않습니다.** ANARCI는 내부적으로 **HMMER의 `hmmscan` 실행파일**을 subprocess로 부르는데, 이것은 파이썬 패키지가 아니라 시스템 바이너리입니다. 빼먹으면 numbering 시점에 이렇게 죽습니다.
>
> ```
> FileNotFoundError: [Errno 2] No such file or directory: 'hmmscan'
> ```
>
> `apt-get install hmmer`(Colab/Ubuntu) 또는 `conda install -c bioconda hmmer`(로컬) 로 먼저 깔아 주세요. 이 한 줄이면 `abnumber.Chain(seq, scheme='imgt')` 가 **0.1초 만에** 돕니다.

챕터별로 pip 로 더 얹는 것들입니다. **전부 pip 한 줄이고, 노트북 부트스트랩이 자동으로 깝니다.**

| 챕터 | 추가로 설치하는 것 | 비고 |
|------|--------------------|------|
| 02 · 07 | `requests` · `biopython` | RCSB API·CIF 파싱 |
| 03 · 04 · 09 | `anarci` `abnumber` (+ hmmer) | numbering |
| 05 | `sapiens` `abnumber` (+ hmmer) | **BioPhi CLI는 bioconda 전용**이지만, 그 안에서 쓰는 `sapiens` 모델은 pip에 있습니다(5.1) |
| 06 | `igfold` + **`transformers==4.36.2`** | 버전 고정 이유는 3.3 |

**한 가지만 pip로 안 됩니다 — PyMOL.** Ch.06·07의 3D 렌더 그림은 PyMOL로 만들었는데, PyMOL은 pip 로 설치되지 않습니다(Colab 불가). 그래서 그 절만은 **저장소에 커밋된 렌더 이미지**를 보여주고, 로컬에 PyMOL이 있으면 자동으로 다시 렌더합니다. 렌더 스크립트(`scripts/render_*.pml`)와 입력 구조는 모두 들어 있으니 재현은 언제든 가능합니다.

---

## 3.1 로컬 — 환경을 셋으로 나누는 이유

| 환경 | 포함 도구 | 목적 |
|------|-----------|------|
| `abseq` | ANARCI(+HMMER), abnumber, Sapiens, pandas, Biopython, matplotlib | numbering, humanness, sequence QC, 모든 분석/플로팅 |
| `abstruct` | IgFold(+transformers 4.36.2), Biopython | 구조예측, PDB 처리 |
| `abinterface` | FreeSASA, PLIP, MDAnalysis | surface/interface 심화 분석 |

> **심화** — 환경을 나누는 이유는 다음과 같습니다. **IgFold는 옛 transformers(4.x)를 요구**하는데, 같은 환경의 다른 도구는 최신 transformers를 원할 수 있습니다. 한 환경에 합치면 한쪽을 업데이트할 때 다른 쪽이 깨집니다. Colab에서는 노트북마다 런타임이 따로라 이 충돌이 자연히 없으므로, **Colab이 더 편한 면도 있습니다.**

환경 정의 파일은 [`environment/`](../environment/)에 있습니다(`abseq.yml`·`abstruct.yml`·`abinterface.yml`).

---

## 3.2 abseq — 서열 분석 메인 환경

대부분의 실습(Ch.03·04·05·08·09 + 모든 그래프)은 이 환경 하나로 돌아갑니다.

```yaml
# environment/abseq.yml
name: abseq
channels: [conda-forge, bioconda]
dependencies:
  - python=3.11
  - pandas
  - biopython
  - matplotlib
  - requests
  - hmmer          # ← ANARCI가 부르는 hmmscan (conda로만 옴)
  - jupyter
  - pip
  - pip: [anarci, abnumber, sapiens]
```

```bash
conda env create -f environment/abseq.yml
conda activate abseq
ANARCI --help >/dev/null && echo "ANARCI OK"
```

> **주의** — **BioPhi CLI(`biophi sapiens`)는 PyPI가 아니라 bioconda**에 있습니다(`pip install biophi` → `No matching distribution`). 그런데 BioPhi가 **내부에서 쓰는 부품**인 `sapiens`(언어모델)와 `abnumber`(numbering)는 **둘 다 pip에 있습니다.** 그래서 이 과정의 Ch.05는 BioPhi CLI 대신 두 부품으로 같은 알고리즘을 직접 돌립니다. Colab에서도 그대로 되고, 결과도 CLI와 **완전히 같습니다**(Ch.05에서 대조합니다).

---

## 3.3 abstruct — 구조예측 환경 (IgFold)

```yaml
# environment/abstruct.yml
name: abstruct
channels: [conda-forge, bioconda]
dependencies:
  - python=3.10
  - pandas
  - biopython
  - hmmer
  - pip
  - pip: [igfold, "transformers==4.36.2", anarci, abnumber]
```

```bash
conda env create -f environment/abstruct.yml
conda activate abstruct
python -c "import igfold, torch; print('igfold OK, CUDA:', torch.cuda.is_available())"
```

> **주의** — **IgFold 설치에서 실제로 겪은 함정 셋** (전부 회피책이 코드에 들어 있습니다).
> 1. **torch ≥ 2.6의 `weights_only=True`** 기본값 → IgFold 체크포인트 로드가 막힙니다. → `torch.load`를 `weights_only=False`로 감싸면 됩니다(신뢰된 패키지 가중치).
> 2. **transformers 5.x 비호환.** 체크포인트에 **옛 토크나이저 객체가 pickle 돼 있어서**, 클래스가 옮겨지거나 사라지면 unpickle이 실패합니다. 실제로 이렇게 죽습니다.
>    ```
>    AttributeError: module 'transformers.tokenization_utils_sentencepiece' has no attribute 'Trie'
>    AttributeError: module 'transformers.models.bert.tokenization_bert' has no attribute 'BasicTokenizer'
>    ```
>    사라진 심볼을 하나씩 되돌려 붙이는 것은 끝이 없으므로, **`transformers==4.36.2`로 고정**하는 것이 정답입니다(노트북 부트스트랩이 자동으로 맞춰 줍니다).
> 3. torch가 시스템 드라이버보다 최신 CUDA로 빌드돼 있으면 GPU 초기화에서 실패합니다. → `CUDA_VISIBLE_DEVICES=""` (스크립트의 `--cpu` 옵션)로 우회합니다.

이 회피책들은 [`scripts/run_igfold_demo.py`](../scripts/run_igfold_demo.py)에 그대로 들어 있고, Ch.06 노트북이 그 스크립트를 실행합니다.

---

## 3.4 abinterface — interface 분석 환경

```yaml
# environment/abinterface.yml
name: abinterface
channels: [conda-forge, bioconda]
dependencies:
  - python=3.9
  - pandas
  - biopython
  - freesasa
  - mdanalysis
  - openbabel
  - pip
  - pip: [plip]
```

> **심화** — PLIP는 Docker로도 돌릴 수 있습니다(Ch.07). contact 계산만 할 땐 `pdb_contacts.py`가 Biopython만 쓰므로 `abseq`로도 충분합니다.

---

## 3.5 설치 점검 — "설치됐다"의 기준은 결과가 나오는가

import 가 된다고 도구가 도는 것은 아닙니다(ANARCI가 대표적입니다. import는 되는데 `hmmscan`이 없어 실행에서 죽습니다). 그래서 점검도 **실제로 한 번 돌려 보는 것**으로 합니다.

```bash
conda activate abseq
ANARCI --help >/dev/null 2>&1 && echo "[abseq] ANARCI OK"
python -c "from abnumber import Chain; c=Chain('EVQLQQSGAEVVRSGASVKLSCTASGFNIKDYYIHWVKQRPEKGLEWIGWIDPEIGDTEYVPKFQGKATMTADTSSNTAYLQLSSLTSEDTAVYYCNAGHDYDRGRFPYWGQGTLVTVSA', scheme='imgt'); print('[abseq] numbering OK:', c.chain_type, c.cdr3_seq)"

conda activate abstruct
python -c "import igfold, transformers; print('[abstruct] igfold OK, transformers', transformers.__version__)"

conda activate abinterface
freesasa --help >/dev/null 2>&1 && echo "[abinterface] FreeSASA OK"
```

노트북 `03_setup_check.ipynb`가 위를 자동으로 돌리고, 나온 numbering 결과를 정답지(`data/setup_expected.csv` — 같은 서열을 ANARCI로 돌려 커밋해 둔 값)와 **대조**까지 해줍니다. 데모 중쇄가 `chain_type=H`, CDR3 `NAGHDYDRGRFPY` 로 나오면 환경이 제대로 선 것입니다.

---

### 이 챕터 핵심 요약

1. **Colab 경로**: `apt-get install hmmer` + `pip install anarci abnumber` — ANARCI가 부르는 **hmmscan은 pip로 안 깔린다**는 게 1번 함정.
2. **BioPhi CLI는 bioconda 전용**이지만, 그 부품인 **`sapiens`·`abnumber`는 pip**에 있어 Colab에서도 humanization을 그대로 돌릴 수 있습니다.
3. **IgFold는 `transformers==4.36.2` 고정**(체크포인트에 pickle 된 옛 토크나이저) + `weights_only=False` 패치가 필수.
4. **PyMOL만 pip로 못 깝니다** — 3D 렌더 절은 커밋된 이미지로 대체(스크립트·입력은 저장소에 있음).
5. 점검은 import 가 아니라 **실제 실행 결과로**. `03_setup_check.ipynb`가 정답지와 대조해 줍니다.

다음 → **[04. numbering & germline (ANARCI)](../04_numbering/04_numbering.md)**
