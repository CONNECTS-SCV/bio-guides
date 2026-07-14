"""build_combined.py — 챕터 본문(.md)들을 합쳐 combined.md 를 결정적으로 재생성.
실행: python build_combined.py   (repo 루트에서)

(BoltzGen 튜토리얼의 build_combined.py 에 대응 — 이미지 경로 재작성 규칙을 추가)

규칙
  · 00_README.md + 01~10 챕터 .md 를 순서대로 연결.
  · 각 문서의 YAML frontmatter(--- ... ---) 와 말미 "다음 →" 네비 푸터는 제거.
  · 문서 사이는 <div class="pagebreak"></div> 로 구분(mdpdf PDF 페이지 분리).
  · **이미지 경로 재작성**: 챕터 본문은 파일명만(`07_interface_contacts.png`)
    참조하지만, combined.md 는 repo 루트(=mdpdf BASE)에 놓이므로
    `07_interface/07_interface_contacts.png` 처럼 **챕터폴더/파일명** 으로 바꿔야
    mdpdf 뷰어가 이미지를 찾을 수 있다.
  → 본문 .md 만 고치면 이 스크립트로 combined.md 가 항상 동기화됨.
"""
import re
import pathlib

ROOT = pathlib.Path(__file__).parent
PAGEBREAK = '<div class="pagebreak"></div>'
IMG = re.compile(r'(!\[[^\]]*\]\()([^)/][^)]*\.png)(\))')  # 슬래시 없는(=파일명만) png 링크


def strip_frontmatter(text):
    m = re.match(r"\A---\n.*?\n---\n", text, flags=re.S)
    return text[m.end():] if m else text


def strip_nav_footer(text):
    return re.sub(r"(?:\n[ \t]*---[ \t]*)?\n+[ \t]*다음 →[^\n]*\n*\Z", "\n", text)


def qualify_images(text, folder):
    """파일명만 참조하는 이미지 링크를 '챕터폴더/파일명' 으로 바꾼다."""
    return IMG.sub(lambda m: f"{m.group(1)}{folder}/{m.group(2)}{m.group(3)}", text)


def strip_hr(text):
    """단독 '---'(수평선, thematic break) 줄을 제거 — 뷰어에서 거슬리고 편집해도 되살아나서.
    코드펜스(```) 안의 '---' 는 보존하고, 챕터 사이 구분은 pagebreak div 가 담당한다.
    제거 후 생기는 빈 줄 과다는 2줄로 정리한다."""
    out, fence = [], False
    for line in text.split("\n"):
        s = line.strip()
        if s.startswith("```"):
            fence = not fence
            out.append(line)
            continue
        if not fence and re.fullmatch(r"-{3,}", s):
            continue
        out.append(line)
    return re.sub(r"\n{3,}", "\n\n", "\n".join(out))


def clean(path, folder=None):
    t = path.read_text(encoding="utf-8")
    t = strip_nav_footer(strip_frontmatter(t))
    t = strip_hr(t).strip("\n")
    if folder:
        t = qualify_images(t, folder)
    return t


def chapter_files():
    out = []
    for d in sorted(ROOT.glob("[0-1][0-9]_*")):
        if d.is_dir() and (d / f"{d.name}.md").exists():
            out.append(d)
    return out


def main():
    parts = [clean(ROOT / "00_README.md")]  # README 는 이미지 없음
    chs = chapter_files()
    for d in chs:
        parts.append(clean(d / f"{d.name}.md", folder=d.name))
    combined = ("\n\n" + PAGEBREAK + "\n\n").join(parts) + "\n"
    (ROOT / "combined.md").write_text(combined, encoding="utf-8")
    print(f"combined.md 재생성: README + {len(chs)}개 챕터, {len(combined.splitlines())} 줄")
    for d in chs:
        print("  +", d.name)


if __name__ == "__main__":
    main()
