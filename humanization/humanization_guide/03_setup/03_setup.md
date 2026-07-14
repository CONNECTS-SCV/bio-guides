---
title: "Ch.03 — 환경 구성 (설치·검증)"
chapter: 3
language: ko
part: A
---

# Ch.03 — 환경 구성 (설치·검증)

이 챕터는 뒤의 모든 실습이 올라탈 **바닥**을 깝니다. 브라우저에서 노트북으로 따라올 거라면 설치는 노트북 첫 셀이 대신 해 주니 훑고 지나가도 됩니다. 로컬에서 직접 도구를 굴릴 거라면, 여기서 만드는 conda 환경 하나가 Ch.04~07의 실습을 거의 다 커버합니다.

> **실습 — `03_setup_check.ipynb`** · ① 직접 실행 → ② 내 결과 확인 → ③ 레퍼런스 대조 · **전 셀 6초**
>
> 도구를 직접 설치하고(ANARCI·abnumber·Sapiens) 러닝 예제 서열을 불러와 환경이 준비됐는지 확인합니다.

---

## 3.1 공용 환경 만들기 — `abhuman`

```bash
# ANARCI는 PyPI가 아니라 bioconda에 있습니다. (이게 첫 번째 함정!)
conda create -n abhuman -c conda-forge -c bioconda python=3.10 anarci hmmer -y
conda activate abhuman
ANARCI --help
```

`ANARCI --help`가 사용법을 출력하면 성공입니다. 이 `abhuman` 환경 하나에 Sapiens·AnthroAb를 얹으면 Ch.04·05·06의 실습이 그대로 돌아갑니다.

> **주의 — `pip install anarci`는 안 됩니다.** ANARCI는 HMMER에 의존하는 bioconda 패키지입니다. PyPI에서 찾으면 못 찾거나 엉뚱한 패키지를 받게 됩니다. 반드시 `-c bioconda`로 설치하십시오. bioconda의 noarch 빌드라 설치 자체는 간단합니다.

---

## 3.2 도구별 설치 경로 지도 — 어디서 받아야 하나

humanization 도구들은 **설치 채널이 제각각**입니다. 여기서 한 번 정리해 두면, 각 챕터에서 "왜 pip이 안 되지?" 하며 멈추는 일을 피할 수 있습니다. 실제로 겪은 실패와 그 해결(케이스 스터디)은 각 챕터에 그대로 실어 뒀습니다.

| 도구 | 설치 채널 | 같은 env에 꼭 필요한 것 | 상세 |
|---|---|---|---|
| **ANARCI** | `conda -c bioconda` (`anarci`, `hmmer`) | — | §3.1 · [Ch.04](../04_sequence_qc/04_sequence_qc.md) |
| **IgBLAST** | `conda -c bioconda` (`igblast`) | germline DB를 직접 빌드 | [Ch.04](../04_sequence_qc/04_sequence_qc.md) |
| **BioPhi** | `conda -c bioconda` (**PyPI에 없음**) | — | [Ch.05](../05_humanize_sapiens/05_humanize_sapiens.md) |
| **Sapiens** | `pip install sapiens` (PyPI) | 모델 가중치는 첫 실행 시 HF에서 자동 다운로드 | [Ch.05](../05_humanize_sapiens/05_humanize_sapiens.md) |
| **Humatch** | **GitHub source** (PyPI에 없음) | `anarci` (없으면 `ModuleNotFoundError`) | [Ch.06](../06_cdr_safe_tools/06_cdr_safe_tools.md) |
| **AnthroAb** | `pip install anthroab` (PyPI) | RoBERTa-base 모델(약 164MB) 자동 다운로드 | [Ch.06](../06_cdr_safe_tools/06_cdr_safe_tools.md) |
| **AbNatiV** | `pip install abnativ` (PyPI) | `abnativ init`(체크포인트 **모델당 약 1GB**) + `anarci` | [Ch.07](../07_nativeness/07_nativeness.md) |
| **Ab-RoBERTa** | HuggingFace (`mogam-ai/Ab-RoBERTa`) | 첫 실행 시 자동 다운로드 | [Ch.07](../07_nativeness/07_nativeness.md) |
| ABodyBuilder3 / ImmuneBuilder / AntiFold / TAP | pip · 웹 | — 〔본 환경 미실행〕 | [Ch.08](../08_structure/08_structure.md) · [Ch.09](../09_developability/09_developability.md) |

> **핵심 — 세 번의 `pip install` 실패.** `pip install anarci`, `pip install biophi`, `pip install humatch` — 셋 다 실패합니다. 각각 **bioconda·bioconda·GitHub source**가 정답입니다. 실제 오류 메시지와 해결 과정은 해당 챕터의 케이스 스터디에 남겨 뒀습니다.

---

## 3.3 환경을 나눌까, 합칠까

- **합치기(권장 시작점)** — `abhuman` 하나에 ANARCI·IgBLAST·Sapiens·AnthroAb·Humatch를 모두 넣으면, Humatch의 `import anarci` 문제가 애초에 생기지 않습니다.
- **나누기** — Humatch는 TensorFlow, AbNatiV는 PyTorch + ImmuneBuilder를 끌고 옵니다. 의존성 충돌이 걱정되면 `humatch`·`abnativ`를 별도 env로 분리하십시오(각 챕터의 설치 절이 분리 기준으로 쓰여 있습니다).

`anarci`는 **세 도구가 공통으로 import**합니다(ANARCI 자체, Humatch의 정렬, AbNatiV의 `-align`). env를 나누더라도 **각 env에 anarci를 넣어야** 합니다 — 이 한 줄이 Ch.06·07의 가장 흔한 에러를 막아 줍니다.

---

## 3.4 설치 검증 체크

```bash
conda activate abhuman
ANARCI --help                       # numbering 도구
python -c "import sapiens; print('sapiens ok')"
python -c "import anthroab; print('anthroab ok')"
python -c "import anarci; print('anarci import ok')"   # Humatch·AbNatiV가 내부적으로 쓰는 경로
```

마지막 줄이 특히 중요합니다. CLI로 `ANARCI`가 돌아가도 **파이썬 모듈 `anarci`가 import되지 않는** 상태면, Humatch와 AbNatiV `-align`이 뒤에서 죽습니다.

---

## 이 챕터 핵심 요약

1. 공용 env `abhuman`을 **bioconda**로 만듭니다(`anarci` + `hmmer`).
2. 설치 채널은 도구마다 다릅니다 — **bioconda(ANARCI·IgBLAST·BioPhi) · PyPI(Sapiens·AnthroAb·AbNatiV) · GitHub(Humatch)**.
3. 모델 가중치는 대부분 **첫 실행 때 자동 다운로드**되지만, AbNatiV만은 `abnativ init`을 먼저 돌려야 하고 체크포인트가 **모델당 약 1GB**입니다.
4. `import anarci`가 되는지 반드시 확인하세요 — Humatch·AbNatiV가 이 모듈에 의존합니다.

---

다음 → **[04. 입력 QC: ANARCI / IgBLAST](../04_sequence_qc/04_sequence_qc.md)**
