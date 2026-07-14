#!/usr/bin/env bash
# 항체 튜토리얼 mdpdf 뷰어 실행 — 이 repo 루트가 BASE 가 되어 combined.md + 이미지를 서빙.
# 사용: bash run_viewer.sh            (flask 가 있는 conda env 기본값 = boltzgen_env)
#       bash run_viewer.sh <env이름>  (다른 env 로 실행)
# 그 뒤 브라우저로 http://localhost:5000 접속. Ctrl+C 로 종료.
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
ENVNAME="${1:-boltzgen_env}"
echo "[1/2] combined.md 동기화 (build_combined.py)"
conda run -n "$ENVNAME" python "$HERE/build_combined.py"
echo "[2/2] 뷰어 기동 → http://localhost:5000  (Ctrl+C 종료)"
exec conda run -n "$ENVNAME" python "$HERE/mdpdf/app.py"
