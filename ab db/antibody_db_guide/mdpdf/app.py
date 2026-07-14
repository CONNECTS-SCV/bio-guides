#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Markdown → PDF 웹 에디터 백엔드.
좌측 마크다운(원본) ↔ 우측 미리보기/WYSIWYG 양방향 편집(Toast UI).
PDF/HTML/DOCX 내보내기는 pandoc → weasyprint 로 서버에서 충실 렌더.
"""
import io, os, re, json, subprocess, tempfile, pathlib
from urllib.parse import quote
from flask import Flask, request, send_file, send_from_directory, Response, abort

APP_DIR = pathlib.Path(__file__).resolve().parent          # advanced/mdpdf/
BASE    = APP_DIR.parent                                    # advanced/  (이미지·combined.md 루트)
DIST    = APP_DIR / "editor-app" / "dist"                   # BlockNote(노션형) 빌드 산출물
SESS    = APP_DIR / "sessions"                              # 편집 세션(.json) 저장 위치
WEBTEX  = "https://latex.codecogs.com/png.image?\\dpi{140}"

# BlockNote(노션형) HTML 의 블록별 색/정렬을 weasyprint 가 렌더하도록 매핑
_TEXT = {"gray": "#9b9a97", "brown": "#64473a", "red": "#e03e3e", "orange": "#d9730d",
         "yellow": "#dfab01", "green": "#0f7b6c", "blue": "#0b6e99", "purple": "#6940a5", "pink": "#ad1a72"}
_BG = {"gray": "#ebeced", "brown": "#e9e5e3", "red": "#fbe4e4", "orange": "#faebdd", "yellow": "#fbf3db",
       "green": "#ddedea", "blue": "#ddebf1", "purple": "#eae4f2", "pink": "#f4dfeb"}
BN_EXPORT_CSS = (
    "".join(f'[data-text-color="{k}"]{{color:{v};}}' for k, v in _TEXT.items())
    + "".join(f'[data-background-color="{k}"]{{background-color:{v};}}' for k, v in _BG.items())
    + '[data-text-alignment="center"]{text-align:center;}'
    + '[data-text-alignment="right"]{text-align:right;}'
    + '[data-text-alignment="justify"]{text-align:justify;}'
)

app = Flask(__name__)


def math_to_img(html):
    """HTML 텍스트의 $$…$$ / $…$ 수식을 codecogs PNG 이미지로 치환(weasyprint용).
    ① 코드 영역(<pre>/<code>)의 $(셸 변수 ${VAR} 등)는 수식으로 오인하지 않도록 잠시 치워 두고,
    ② 매칭이 '<'(태그)를 가로지르지 못하게 제한한다. → 코드블록의 $ 가 멀리 떨어진 다른 $ 와
    짝지어져 그 사이의 </code></pre>·표·제목까지 통째로 삼키며 '코드박스가 이후 내용을 감싸는'
    구조 파손을 방지(수식 본문은 HTML에서 '<' 를 &lt; 로 보유하므로 '<' 제외가 안전)."""
    def url(tex):
        return "https://latex.codecogs.com/png.image?" + quote("\\dpi{140} " + tex.strip())
    # ① 코드 영역을 placeholder 로 치환(수식 치환 대상에서 제외). <pre>…</pre> 먼저 → 내부 <code> 포함
    stash = []
    def hide(m):
        stash.append(m.group(0))
        return f"\x00{len(stash) - 1}\x00"
    html = re.sub(r"<pre\b[\s\S]*?</pre>", hide, html, flags=re.I)
    html = re.sub(r"<code\b[\s\S]*?</code>", hide, html, flags=re.I)
    # ② display $$…$$ — 태그(<)를 넘지 않도록 제한
    html = re.sub(r"\$\$([^<]+?)\$\$",
                  lambda m: f'<img class="math display" src="{url(m.group(1))}" alt="">',
                  html)
    # ③ inline $…$ — 한 줄·한 텍스트노드 내부로 한정(<·줄바꿈·$ 제외)
    html = re.sub(r"(?<![\$\w])\$(?!\$)([^<$\n]+?)(?<!\$)\$(?![\$\w])",
                  lambda m: f'<img class="math inline" src="{url(m.group(1))}" alt="">',
                  html)
    # ④ 코드 영역 복원(replacement 에 lambda 사용 → 백슬래시·\1 오해석 방지)
    html = re.sub(r"\x00(\d+)\x00", lambda m: stash[int(m.group(1))], html)
    return html


@app.after_request
def _no_cache(resp):
    """에디터/스타일은 항상 최신으로 — 캐시로 인한 옛 코드·옛 404 혼선 방지."""
    ct = resp.headers.get("Content-Type", "")
    if any(k in ct for k in ("text/html", "css", "javascript")):
        resp.headers["Cache-Control"] = "no-store"
    return resp


def build_export_css(vars_dict, pagesize="A4", margin=None):
    """style_vars.css(변수 기반) *뒤에* 사용자 오버라이드를 붙여 우선 적용되게 함."""
    css = (APP_DIR / "style_vars.css").read_text(encoding="utf-8")
    root = ""
    if vars_dict:
        decls = "".join(f"{k}:{v};" for k, v in vars_dict.items() if v not in (None, ""))
        root = f":root{{{decls}}}\n"
    page = f"@page{{size:{pagesize};"
    if margin:
        page += f"margin:{margin};"
    page += "}\n"
    # base 를 먼저, 사용자 오버라이드(:root, @page)를 나중에 → 카스케이드상 사용자값이 이김
    return css + "\n" + page + root


@app.route("/")
def index():
    """기본: 클래식 에디터(마크다운 + WYSIWYG 분할)."""
    return send_from_directory(APP_DIR, "editor.html")


@app.route("/notion")
def notion():
    """BlockNote(노션형) 빌드 — 있으면 제공."""
    if (DIST / "index.html").exists():
        return send_from_directory(DIST, "index.html")
    abort(404)


@app.route("/bundle/<path:p>")
def bundle(p):
    return send_from_directory(DIST / "bundle", p)


@app.route("/assets/<path:p>")
def assets(p):
    return send_from_directory(APP_DIR, p)


@app.route("/files/<path:p>")
def files(p):
    """튜토리얼 이미지 등 정적 자원(advanced/ 기준)."""
    return send_from_directory(BASE, p)


@app.route("/default_md")
def default_md():
    f = BASE / "combined.md"
    if f.exists():
        txt = f.read_text(encoding="utf-8")
    else:
        txt = "# 새 문서\n\n좌측에서 마크다운을 편집하거나, 우측 미리보기를 직접 수정하세요.\n"
    return Response(txt, mimetype="text/plain; charset=utf-8")


@app.route("/save", methods=["POST"])
def save():
    """현재 마크다운을 서버의 .md 파일로 저장(Ctrl+S). BASE 밖 경로는 거부."""
    data = request.get_json(force=True)
    rel = (data.get("path") or "").strip().lstrip("/")
    md = data.get("markdown", "")
    if not rel or not rel.lower().endswith((".md", ".markdown", ".txt")):
        return Response("저장 경로(.md/.markdown/.txt)가 필요합니다.", status=400)
    target = (BASE / rel).resolve()
    if not str(target).startswith(str(BASE.resolve()) + os.sep) and target != BASE.resolve():
        return Response("허용되지 않은 경로입니다.", status=403)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(md, encoding="utf-8")
    return {"ok": True, "path": rel, "bytes": len(md.encode("utf-8"))}


def _safe_name(s):
    return re.sub(r"[^0-9A-Za-z가-힣 _.-]", "", (s or "").strip())[:60]


@app.route("/sessions", methods=["GET"])
def list_sessions():
    """저장된 편집 세션 이름 목록."""
    SESS.mkdir(exist_ok=True)
    return {"sessions": sorted(p.stem for p in SESS.glob("*.json"))}


@app.route("/save_session", methods=["POST"])
def save_session():
    """편집 세션 전체(마크다운 + 스타일 변수 + 페이지/줌/보기 상태)를 JSON 으로 저장."""
    data = request.get_json(force=True)
    name = _safe_name(data.get("name"))
    if not name:
        return Response("세션 이름이 필요합니다.", status=400)
    SESS.mkdir(exist_ok=True)
    (SESS / f"{name}.json").write_text(
        json.dumps(data.get("session") or {}, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"ok": True, "name": name}


@app.route("/load_session", methods=["GET"])
def load_session():
    name = _safe_name(request.args.get("name"))
    f = SESS / f"{name}.json"
    if not name or not f.exists():
        return Response("세션을 찾을 수 없습니다.", status=404)
    return Response(f.read_text(encoding="utf-8"), mimetype="application/json; charset=utf-8")


@app.route("/export", methods=["POST"])
def export():
    data      = request.get_json(force=True)
    md        = data.get("markdown", "")
    fmt       = data.get("format", "pdf")        # pdf | html | docx
    vars_d    = data.get("vars") or {}
    pagesize  = data.get("pagesize", "A4")
    margin    = data.get("margin")
    html_body = data.get("html")

    # ── 노션형(BlockNote): 블록 HTML 직접 렌더 → 블록별 색·정렬·표 크기 보존 ──
    if html_body is not None and fmt in ("pdf", "html"):
        css  = build_export_css(vars_d, pagesize, margin)
        body = math_to_img(html_body)
        full = ("<!doctype html><html><head><meta charset='utf-8'><style>\n"
                + css + "\n" + BN_EXPORT_CSS + "\n</style></head><body>\n" + body + "\n</body></html>")
        if fmt == "html":
            return send_file(io.BytesIO(full.encode("utf-8")), mimetype="text/html",
                             as_attachment=True, download_name="document.html")
        from weasyprint import HTML
        pdf_bytes = HTML(string=full, base_url=str(BASE) + os.sep).write_pdf()
        return send_file(io.BytesIO(pdf_bytes), mimetype="application/pdf",
                         as_attachment=True, download_name="document.pdf")

    with tempfile.TemporaryDirectory() as tmp:
        td = pathlib.Path(tmp)
        (td / "doc.md").write_text(md, encoding="utf-8")

        # ── DOCX: pandoc 직접 (reference.docx 있으면 사용) ──
        if fmt == "docx":
            out = td / "doc.docx"
            cmd = ["pandoc", str(td / "doc.md"), "-o", str(out),
                   "--resource-path", str(BASE)]
            ref = APP_DIR / "reference.docx"
            if ref.exists():
                cmd += ["--reference-doc", str(ref)]
            subprocess.run(cmd, check=True, cwd=str(BASE))
            return send_file(str(out), as_attachment=True, download_name="document.docx")

        # ── HTML 생성 (pandoc, 스타일 inline + webtex 수식) ──
        css    = build_export_css(vars_d, pagesize, margin)
        header = td / "head.html"
        header.write_text(f"<style>\n{css}\n</style>\n", encoding="utf-8")
        htmlp  = td / "doc.html"
        subprocess.run(
            ["pandoc", str(td / "doc.md"), "-f", "gfm+tex_math_dollars", "-t", "html5", "-s",
             "--no-highlight",                       # 구문강조 끔 → 코드 색/배경을 --code-fg/--code-bg 로 일관 제어(미리보기와 일치)
             "--include-in-header", str(header),
             f"--webtex={WEBTEX}",
             "--resource-path", str(BASE),
             "-o", str(htmlp)],
            check=True, cwd=str(BASE))

        if fmt == "html":
            return send_file(str(htmlp), as_attachment=True, download_name="document.html")

        # ── PDF: weasyprint (base_url=BASE 로 상대 이미지 해석) ──
        from weasyprint import HTML
        html_text = htmlp.read_text(encoding="utf-8")
        pdf_bytes = HTML(string=html_text, base_url=str(BASE) + os.sep).write_pdf()
        return send_file(io.BytesIO(pdf_bytes), mimetype="application/pdf",
                         as_attachment=True, download_name="document.pdf")


@app.route("/<path:p>")
def passthrough(p):
    """마크다운의 상대 이미지 경로(예: 04_basic_usage/x.png)를 BASE 기준으로 서빙.
    덕분에 미리보기·WYSIWYG 에서 경로 변환 없이 이미지가 그대로 표시된다."""
    full = (BASE / p)
    if full.is_file():
        return send_from_directory(BASE, p)
    abort(404)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
