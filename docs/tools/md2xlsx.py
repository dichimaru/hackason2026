#!/usr/bin/env python3
"""Markdown の設計ドキュメントを閲覧用 xlsx に変換する。

編集は Markdown 側で行い、xlsx は生成物として扱う (手で xlsx を編集しない)。
Python 標準ライブラリのみで動作する (xlsx = zip + XML を直接組み立てる)。

使い方:
    python3 docs/tools/render_mermaid.py   # 先に mermaid を PNG 化 (図がある場合)
    python3 docs/tools/md2xlsx.py          # docs/*.md をすべて変換

    python3 docs/tools/md2xlsx.py docs/basic-design.md    # 個別に変換
    python3 docs/tools/md2xlsx.py -o /path/out.xlsx docs/basic-design.md

変換ルール:
    # 見出し1     → ブックのタイトル (先頭シートの1行目)
    ## 見出し2    → シート1枚
    ### / ####    → シート内の見出し行
    表            → 罫線・ヘッダ着色付きのセル範囲
    箇条書き      → 「・」付きのテキスト行
    ``` コード    → 等幅フォントのテキスト行 (ASCII の構成図もそのまま残す)
    ![alt](path)  → 画像として埋め込む

    mermaid ブロックは xlsx では描画できないため、直後に
        <!-- xlsx-image: images/er-diagram.png -->
    を置くと、その PNG (render_mermaid.py の出力) を画像として埋め込み、
    mermaid のソースは xlsx 側には出力しない。PNG が未生成のときは
    ソースを等幅テキストとして残す。
"""
from __future__ import annotations

import argparse
import math
import re
import struct
import sys
import unicodedata
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

# ---------------------------------------------------------------- Markdown 解析

BLOCK_TABLE = "table"
BLOCK_TEXT = "text"
BLOCK_HEAD = "head"
BLOCK_CODE = "code"
BLOCK_IMAGE = "image"
BLOCK_BLANK = "blank"

IMAGE_MARKER_RE = re.compile(r"<!--\s*xlsx-image:\s*(.+?)\s*-->")
MD_IMAGE_RE = re.compile(r"^!\[([^\]]*)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)$")
HTML_COMMENT_RE = re.compile(r"^<!--.*-->$")


class Section:
    """## 見出し2 ごとの塊 (= xlsx の1シート)。"""

    def __init__(self, title: str) -> None:
        self.title = title
        self.blocks: list[tuple[str, object]] = []


def strip_inline(text: str) -> str:
    """閲覧用にインライン記法を落とす。リンクは「文字列 (URL)」に展開する。"""
    text = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", r"\1", text)
    text = re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)",
        lambda m: m.group(1) if m.group(1) == m.group(2) else f"{m.group(1)} ({m.group(2)})",
        text,
    )
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"(?<!\w)_([^_]+)_(?!\w)", r"\1", text)
    text = text.replace("`", "")
    text = re.sub(r"<br\s*/?>", "\n", text)
    return text.strip()


def split_row(line: str) -> list[str]:
    body = line.strip()
    if body.startswith("|"):
        body = body[1:]
    if body.endswith("|") and not body.endswith(r"\|"):
        body = body[:-1]
    cells = [c.replace("\x00", "|") for c in body.replace(r"\|", "\x00").split("|")]
    return [strip_inline(c) for c in cells]


def is_separator(line: str) -> bool:
    return bool(re.fullmatch(r"\|[\s:|-]+\|?", line.strip()))


def parse(md: str, base_dir: Path) -> tuple[str, list[Section]]:
    lines = md.splitlines()
    doc_title = ""
    sections: list[Section] = [Section("概要")]
    i = 0
    in_code = False
    code_lang = ""
    code: list[str] = []

    while i < len(lines):
        raw = lines[i]
        line = raw.rstrip()

        if line.strip().startswith("```"):
            if in_code:
                sections[-1].blocks.append((BLOCK_CODE, (code_lang, code)))
                code, code_lang, in_code = [], "", False
            else:
                code_lang = line.strip()[3:].strip().lower()
                in_code = True
            i += 1
            continue
        if in_code:
            code.append(raw)
            i += 1
            continue

        marker = IMAGE_MARKER_RE.match(line.strip())
        if marker:
            sections[-1].blocks.append((BLOCK_IMAGE, ("", marker.group(1))))
            i += 1
            continue
        if HTML_COMMENT_RE.match(line.strip()):  # md 専用のコメントは落とす
            i += 1
            continue

        md_image = MD_IMAGE_RE.match(line.strip())
        if md_image:
            sections[-1].blocks.append((BLOCK_IMAGE, (md_image.group(1), md_image.group(2))))
            i += 1
            continue

        if line.startswith("# "):
            doc_title = strip_inline(line[2:])
            i += 1
            continue
        if line.startswith("## "):
            sections.append(Section(strip_inline(line[3:])))
            i += 1
            continue
        if re.match(r"#{3,6} ", line):
            level = len(line) - len(line.lstrip("#"))
            sections[-1].blocks.append((BLOCK_HEAD, (level, strip_inline(line.lstrip("# ")))))
            i += 1
            continue

        # 表: ヘッダ行 + 区切り行 + データ行
        if line.startswith("|") and i + 1 < len(lines) and is_separator(lines[i + 1]):
            header = split_row(line)
            rows: list[list[str]] = []
            i += 2
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(split_row(lines[i]))
                i += 1
            width = max([len(header)] + [len(r) for r in rows])
            pad = lambda r: r + [""] * (width - len(r))
            sections[-1].blocks.append((BLOCK_TABLE, (pad(header), [pad(r) for r in rows])))
            continue

        if re.match(r"^\s*(?:[-*+]|\d+\.)\s", line):
            indent = (len(line) - len(line.lstrip())) // 2
            item = re.sub(r"^\s*(?:[-*+]|\d+\.)\s+", "", line)
            sections[-1].blocks.append(
                (BLOCK_TEXT, "　" * indent + "・" + strip_inline(item))
            )
            i += 1
            continue

        if re.fullmatch(r"-{3,}|\*{3,}|_{3,}", line.strip()):
            i += 1
            continue

        if not line.strip():
            sections[-1].blocks.append((BLOCK_BLANK, ""))
            i += 1
            continue

        sections[-1].blocks.append((BLOCK_TEXT, strip_inline(line)))
        i += 1

    if in_code:  # 閉じ忘れの ``` を落とさない
        sections[-1].blocks.append((BLOCK_CODE, (code_lang, code)))

    for s in sections:
        drop_rendered_mermaid(s, base_dir)
        while s.blocks and s.blocks[0][0] == BLOCK_BLANK:  # 前後の空行を詰める
            s.blocks.pop(0)
        while s.blocks and s.blocks[-1][0] == BLOCK_BLANK:
            s.blocks.pop()
    return doc_title, [s for s in sections if s.blocks]


def drop_rendered_mermaid(section: Section, base_dir: Path) -> None:
    """PNG が用意されている mermaid ブロックは、ソースを xlsx へ出力しない。"""
    keep: list[tuple[str, object]] = []
    for idx, block in enumerate(section.blocks):
        if block[0] == BLOCK_CODE and block[1][0] == "mermaid":
            for follower in section.blocks[idx + 1 : idx + 4]:
                if follower[0] == BLOCK_BLANK:
                    continue
                if follower[0] == BLOCK_IMAGE and (base_dir / follower[1][1]).exists():
                    break
                follower = None
                break
            else:
                follower = None
            if follower is not None:
                continue
        keep.append(block)
    section.blocks = keep


# ------------------------------------------------------------------ xlsx 組み立て

# セルスタイル (styles.xml の cellXfs の並び順と一致させる)
S_DEFAULT, S_TITLE, S_H2, S_H3, S_H4, S_TEXT, S_MONO, S_TH, S_TD, S_TD_NUM = range(10)

MAX_COL_WIDTH = 46
MIN_COL_WIDTH = 6
MAX_IMAGE_PX = 720  # 画像の表示幅上限。Retina 解像度の PNG もこの幅に収める
ROW_HEIGHT_PX = 20  # 既定行高 (15pt) 相当。画像下に空ける行数の計算に使う
EMU_PER_PX = 9525


def disp_len(text: str) -> int:
    """全角を2文字幅として数える表示幅。列幅の見積りに使う。"""
    return sum(2 if unicodedata.east_asian_width(c) in "WFA" else 1 for c in text)


def col_letter(idx: int) -> str:
    name = ""
    idx += 1
    while idx:
        idx, rem = divmod(idx - 1, 26)
        name = chr(65 + rem) + name
    return name


def png_size(path: Path) -> tuple[int, int]:
    """PNG の IHDR から幅・高さ (px) を読む。"""
    with path.open("rb") as f:
        head = f.read(24)
    if head[:8] != b"\x89PNG\r\n\x1a\n" or head[12:16] != b"IHDR":
        raise ValueError(f"PNG として読めません: {path}")
    return struct.unpack(">II", head[16:24])


class Image:
    def __init__(self, path: Path, row: int, alt: str) -> None:
        self.path = path
        self.row = row  # 0 始まり
        self.alt = alt or path.stem
        px_w, px_h = png_size(path)
        scale = min(1.0, MAX_IMAGE_PX / px_w)
        self.disp_w = round(px_w * scale)
        self.disp_h = round(px_h * scale)

    @property
    def rows_needed(self) -> int:
        return math.ceil(self.disp_h / ROW_HEIGHT_PX) + 1


class Sheet:
    def __init__(self, name: str) -> None:
        self.name = name
        self.rows: list[list[tuple[str, int] | None]] = []
        self.widths: dict[int, int] = {}
        self.images: list[Image] = []

    def add(self, cells: list[tuple[str, int] | None]) -> None:
        self.rows.append(cells)

    def blank(self) -> None:
        self.rows.append([])

    def note_width(self, col: int, text: str) -> None:
        cur = self.widths.get(col, 0)
        self.widths[col] = max(cur, min(disp_len(text) + 2, MAX_COL_WIDTH))

    def add_image(self, path: Path, alt: str) -> None:
        img = Image(path, len(self.rows), alt)
        self.images.append(img)
        for _ in range(img.rows_needed):  # 画像の下に本文が潜らないよう行を空ける
            self.blank()


NUM_RE = re.compile(r"-?\d+(?:\.\d+)?")


def cell_xml(ref: str, value: str, style: int) -> str:
    if style == S_TD and NUM_RE.fullmatch(value):
        return f'<c r="{ref}" s="{S_TD_NUM}"><v>{value}</v></c>'
    if not value:
        return f'<c r="{ref}" s="{style}"/>'
    return (
        f'<c r="{ref}" s="{style}" t="inlineStr">'
        f'<is><t xml:space="preserve">{escape(value)}</t></is></c>'
    )


def sheet_xml(sheet: Sheet, drawing_rel_id: str | None) -> str:
    cols = ""
    if sheet.widths:
        parts = [
            f'<col min="{c + 1}" max="{c + 1}" width="{max(w, MIN_COL_WIDTH)}" customWidth="1"/>'
            for c, w in sorted(sheet.widths.items())
        ]
        cols = f"<cols>{''.join(parts)}</cols>"
    body = []
    for r, cells in enumerate(sheet.rows, start=1):
        if not cells:
            body.append(f'<row r="{r}"/>')
            continue
        xml_cells = [
            cell_xml(f"{col_letter(c)}{r}", value, style)
            for c, cell in enumerate(cells)
            if cell is not None
            for value, style in [cell]
        ]
        body.append(f'<row r="{r}">{"".join(xml_cells)}</row>')
    drawing = f'<drawing r:id="{drawing_rel_id}"/>' if drawing_rel_id else ""
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        '<sheetViews><sheetView workbookViewId="0"/></sheetViews>'
        '<sheetFormatPr defaultRowHeight="15"/>'
        f"{cols}<sheetData>{''.join(body)}</sheetData>"
        '<pageMargins left="0.5" right="0.5" top="0.6" bottom="0.6" header="0.3" footer="0.3"/>'
        f"{drawing}</worksheet>"
    )


def drawing_xml(images: list[Image]) -> str:
    anchors = []
    for n, img in enumerate(images, start=1):
        anchors.append(
            "<xdr:oneCellAnchor>"
            "<xdr:from>"
            "<xdr:col>0</xdr:col><xdr:colOff>0</xdr:colOff>"
            f"<xdr:row>{img.row}</xdr:row><xdr:rowOff>0</xdr:rowOff>"
            "</xdr:from>"
            f'<xdr:ext cx="{img.disp_w * EMU_PER_PX}" cy="{img.disp_h * EMU_PER_PX}"/>'
            "<xdr:pic>"
            "<xdr:nvPicPr>"
            f'<xdr:cNvPr id="{n + 1}" name="Picture {n}" descr="{escape(img.alt)}"/>'
            '<xdr:cNvPicPr><a:picLocks noChangeAspect="1"/></xdr:cNvPicPr>'
            "</xdr:nvPicPr>"
            f'<xdr:blipFill><a:blip r:embed="rId{n}"/>'
            "<a:stretch><a:fillRect/></a:stretch></xdr:blipFill>"
            "<xdr:spPr>"
            '<a:xfrm><a:off x="0" y="0"/>'
            f'<a:ext cx="{img.disp_w * EMU_PER_PX}" cy="{img.disp_h * EMU_PER_PX}"/></a:xfrm>'
            '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>'
            "</xdr:spPr>"
            "</xdr:pic>"
            "<xdr:clientData/>"
            "</xdr:oneCellAnchor>"
        )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<xdr:wsDr xmlns:xdr="http://schemas.openxmlformats.org/drawingml/2006/'
        'spreadsheetDrawing" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        f"{''.join(anchors)}</xdr:wsDr>"
    )


STYLES_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
<fonts count="7">
  <font><sz val="11"/><name val="Yu Gothic"/></font>
  <font><b/><sz val="16"/><name val="Yu Gothic"/></font>
  <font><b/><sz val="14"/><color rgb="FF1F3864"/><name val="Yu Gothic"/></font>
  <font><b/><sz val="12"/><color rgb="FF1F3864"/><name val="Yu Gothic"/></font>
  <font><b/><sz val="11"/><name val="Yu Gothic"/></font>
  <font><b/><sz val="11"/><color rgb="FFFFFFFF"/><name val="Yu Gothic"/></font>
  <font><sz val="10"/><name val="Menlo"/></font>
</fonts>
<fills count="3">
  <fill><patternFill patternType="none"/></fill>
  <fill><patternFill patternType="gray125"/></fill>
  <fill><patternFill patternType="solid"><fgColor rgb="FF44546A"/><bgColor indexed="64"/></patternFill></fill>
</fills>
<borders count="2">
  <border><left/><right/><top/><bottom/><diagonal/></border>
  <border>
    <left style="thin"><color rgb="FFBFBFBF"/></left>
    <right style="thin"><color rgb="FFBFBFBF"/></right>
    <top style="thin"><color rgb="FFBFBFBF"/></top>
    <bottom style="thin"><color rgb="FFBFBFBF"/></bottom>
    <diagonal/>
  </border>
</borders>
<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
<cellXfs count="10">
  <xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>
  <xf numFmtId="0" fontId="1" fillId="0" borderId="0" xfId="0" applyFont="1"/>
  <xf numFmtId="0" fontId="2" fillId="0" borderId="0" xfId="0" applyFont="1"/>
  <xf numFmtId="0" fontId="3" fillId="0" borderId="0" xfId="0" applyFont="1"/>
  <xf numFmtId="0" fontId="4" fillId="0" borderId="0" xfId="0" applyFont="1"/>
  <xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0" applyAlignment="1">
    <alignment vertical="top"/></xf>
  <xf numFmtId="0" fontId="6" fillId="0" borderId="0" xfId="0" applyFont="1" applyAlignment="1">
    <alignment vertical="top"/></xf>
  <xf numFmtId="0" fontId="5" fillId="2" borderId="1" xfId="0"
      applyFont="1" applyFill="1" applyBorder="1" applyAlignment="1">
    <alignment horizontal="center" vertical="center" wrapText="1"/></xf>
  <xf numFmtId="0" fontId="0" fillId="0" borderId="1" xfId="0" applyBorder="1" applyAlignment="1">
    <alignment vertical="top" wrapText="1"/></xf>
  <xf numFmtId="0" fontId="0" fillId="0" borderId="1" xfId="0" applyBorder="1" applyAlignment="1">
    <alignment horizontal="center" vertical="top"/></xf>
</cellXfs>
<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>
</styleSheet>"""

INVALID_SHEET_CHARS = str.maketrans({c: "-" for c in r"[]:*?/\\"})


def sheet_name(title: str, used: set[str]) -> str:
    """シート名は31文字・記号制限があるので、長い場合は補足の括弧から削る。"""
    name = title.translate(INVALID_SHEET_CHARS).strip() or "Sheet"
    if len(name) > 31:
        name = re.sub(r"\s*[(（][^)）]*[)）]\s*$", "", name).strip() or name
    if len(name) > 31:
        name = name[:30] + "…"
    base, n = name, 2
    while name.lower() in used:
        suffix = f"({n})"
        name = base[: 31 - len(suffix)] + suffix
        n += 1
    used.add(name.lower())
    return name


def build_sheets(doc_title: str, sections: list[Section], base_dir: Path) -> list[Sheet]:
    sheets: list[Sheet] = []
    used: set[str] = set()
    for si, section in enumerate(sections):
        sh = Sheet(sheet_name(section.title, used))
        if si == 0 and doc_title:
            sh.add([(doc_title, S_TITLE)])
            sh.blank()
        sh.add([(section.title, S_H2)])
        sh.blank()

        for kind, payload in section.blocks:
            if kind == BLOCK_BLANK:
                if sh.rows and sh.rows[-1]:
                    sh.blank()
            elif kind == BLOCK_HEAD:
                level, text = payload
                if sh.rows and sh.rows[-1]:
                    sh.blank()
                sh.add([(text, S_H3 if level == 3 else S_H4)])
            elif kind == BLOCK_TEXT:
                sh.add([(payload, S_TEXT)])
            elif kind == BLOCK_CODE:
                for ln in payload[1]:
                    sh.add([(ln, S_MONO)])
            elif kind == BLOCK_IMAGE:
                alt, rel = payload
                path = base_dir / rel
                if path.exists():
                    sh.add_image(path, alt)
                else:
                    print(f"警告: 画像が見つかりません: {path}", file=sys.stderr)
                    sh.add([(f"(画像未生成: {rel})", S_TEXT)])
            elif kind == BLOCK_TABLE:
                header, rows = payload
                sh.add([(c, S_TH) for c in header])
                for c, text in enumerate(header):
                    sh.note_width(c, text)
                for row in rows:
                    sh.add([(c, S_TD) for c in row])
                    for c, text in enumerate(row):
                        sh.note_width(c, text)
                sh.blank()
        sheets.append(sh)
    return sheets


R_OFFICE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


def write_xlsx(path: Path, sheets: list[Sheet]) -> None:
    n = len(sheets)
    types = [
        '<Default Extension="rels" '
        'ContentType="application/vnd.openxmlformats-package.relationships+xml"/>',
        '<Default Extension="xml" ContentType="application/xml"/>',
        '<Default Extension="png" ContentType="image/png"/>',
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-'
        'officedocument.spreadsheetml.sheet.main+xml"/>',
        '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-'
        'officedocument.spreadsheetml.styles+xml"/>',
    ] + [
        f'<Override PartName="/xl/worksheets/sheet{i}.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        for i in range(1, n + 1)
    ] + [
        f'<Override PartName="/xl/drawings/drawing{i}.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.drawing+xml"/>'
        for i, s in enumerate(sheets, start=1)
        if s.images
    ]
    sheet_tags = "".join(
        f'<sheet name="{escape(s.name)}" sheetId="{i}" r:id="rId{i}"/>'
        for i, s in enumerate(sheets, start=1)
    )
    wb_rels = "".join(
        f'<Relationship Id="rId{i}" Type="{R_OFFICE}/worksheet" '
        f'Target="worksheets/sheet{i}.xml"/>'
        for i in range(1, n + 1)
    ) + f'<Relationship Id="rId{n + 1}" Type="{R_OFFICE}/styles" Target="styles.xml"/>'

    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            f"{''.join(types)}</Types>",
        )
        z.writestr(
            "_rels/.rels",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            f'<Relationship Id="rId1" Type="{R_OFFICE}/officeDocument" '
            'Target="xl/workbook.xml"/></Relationships>',
        )
        z.writestr(
            "xl/workbook.xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
            f'xmlns:r="{R_OFFICE}">'
            f"<sheets>{sheet_tags}</sheets></workbook>",
        )
        z.writestr(
            "xl/_rels/workbook.xml.rels",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            f"{wb_rels}</Relationships>",
        )
        z.writestr("xl/styles.xml", STYLES_XML)

        media_seq = 0
        for i, s in enumerate(sheets, start=1):
            drawing_rel = "rId1" if s.images else None
            z.writestr(f"xl/worksheets/sheet{i}.xml", sheet_xml(s, drawing_rel))
            if not s.images:
                continue
            z.writestr(
                f"xl/worksheets/_rels/sheet{i}.xml.rels",
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/'
                'relationships">'
                f'<Relationship Id="rId1" Type="{R_OFFICE}/drawing" '
                f'Target="../drawings/drawing{i}.xml"/></Relationships>',
            )
            z.writestr(f"xl/drawings/drawing{i}.xml", drawing_xml(s.images))
            rels = []
            for k, img in enumerate(s.images, start=1):
                media_seq += 1
                media_name = f"image{media_seq}{img.path.suffix.lower()}"
                z.writestr(f"xl/media/{media_name}", img.path.read_bytes())
                rels.append(
                    f'<Relationship Id="rId{k}" Type="{R_OFFICE}/image" '
                    f'Target="../media/{media_name}"/>'
                )
            z.writestr(
                f"xl/drawings/_rels/drawing{i}.xml.rels",
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/'
                f'relationships">{"".join(rels)}</Relationships>',
            )


def convert(md_path: Path, out_path: Path) -> tuple[Path, int, int]:
    base_dir = md_path.resolve().parent
    doc_title, sections = parse(md_path.read_text(encoding="utf-8"), base_dir)
    sheets = build_sheets(doc_title, sections, base_dir)
    if not sheets:
        raise SystemExit(f"{md_path}: 変換できる内容がありません")
    write_xlsx(out_path, sheets)
    return out_path, len(sheets), sum(len(s.images) for s in sheets)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Markdown を閲覧用 xlsx に変換する")
    ap.add_argument("sources", nargs="*", type=Path, help="変換する .md (既定: docs/*.md)")
    ap.add_argument("-o", "--output", type=Path, help="出力先 .xlsx (入力1件のときのみ)")
    args = ap.parse_args(argv)

    docs_dir = Path(__file__).resolve().parent.parent
    sources = args.sources or sorted(docs_dir.glob("*.md"))
    if not sources:
        print("変換対象の .md が見つかりません", file=sys.stderr)
        return 1
    if args.output and len(sources) != 1:
        print("-o は入力が1件のときだけ指定できます", file=sys.stderr)
        return 1

    for src in sources:
        out = args.output or src.with_suffix(".xlsx")
        path, sheet_count, image_count = convert(src, out)
        extra = f", 画像 {image_count} 件" if image_count else ""
        print(f"{src} -> {path} ({sheet_count} シート{extra})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
