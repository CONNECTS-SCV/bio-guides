"""build_combined.py — 챕터 본문(.md)들을 합쳐 combined.md 를 결정적으로 재생성.
실행: python build_combined.py

규칙(boltzgen advanced/ 가이드와 동일 형식)
  · 00_README.md + 01~11 챕터 .md 를 순서대로 연결.
  · 각 문서의 YAML frontmatter(--- ... ---) 와 말미 "다음 → [..]" 네비 푸터는 제거.
  · 문서 사이는 <div class="pagebreak"></div> 로 구분(mdpdf PDF 페이지 분리).
  → 본문 .md 만 고치면 이 스크립트로 combined.md 가 항상 동기화됨.
"""
import re, pathlib

ROOT = pathlib.Path(__file__).parent
PAGEBREAK = '<div class="pagebreak"></div>'


def strip_frontmatter(text):
    m = re.match(r"\A---\n.*?\n---\n", text, flags=re.S)
    return text[m.end():] if m else text


def strip_nav_footer(text):
    # 말미의 "다음 → ..." 네비게이션(과 바로 앞 --- 구분선) 제거
    return re.sub(r"(?:\n[ \t]*---[ \t]*)?\n+[ \t]*다음 →[^\n]*\n*\Z", "\n", text)


def clean(path):
    t = path.read_text(encoding="utf-8")
    return strip_nav_footer(strip_frontmatter(t)).strip("\n")


def chapter_files():
    out = []
    for d in sorted(ROOT.glob("[0-1][0-9]_*")):
        if not d.is_dir():
            continue
        md = d / f"{d.name}.md"
        if md.exists():
            out.append(md)
    return out


def main():
    parts = [clean(ROOT / "00_README.md")]
    chs = chapter_files()
    for md in chs:
        parts.append(clean(md))
    combined = ("\n\n" + PAGEBREAK + "\n\n").join(parts) + "\n"
    (ROOT / "combined.md").write_text(combined, encoding="utf-8")
    print(f"combined.md 재생성: README + {len(chs)}개 챕터, {len(combined.splitlines())} 줄")
    for md in chs:
        print("  +", md.relative_to(ROOT))


if __name__ == "__main__":
    main()
