#!/usr/bin/env python3
"""Markdown 内の mermaid ブロックを PNG に書き出す。

xlsx には mermaid を描画する仕組みがないため、あらかじめ画像にしておき
md2xlsx.py がその画像を埋め込む。md 側は mermaid のまま残るので、
GitHub 上では従来どおり mermaid として表示される。

出力先の指定方法: mermaid ブロックの直後に次の1行を置く。
    <!-- xlsx-image: images/er-diagram.png -->
指定が無いブロックは images/<mdのファイル名>-mermaid<連番>.png に出力する。

使い方:
    python3 docs/tools/render_mermaid.py            # docs/*.md をすべて処理
    python3 docs/tools/render_mermaid.py docs/table-definition.md

必要なもの: Node.js (mermaid-cli を npx 経由で実行する。初回のみダウンロードが走る)
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

MERMAID_CLI = "@mermaid-js/mermaid-cli"
SCALE = 2  # Retina 相当。埋め込み時に等倍へ戻す

# mermaid の描画設定。日本語が入るのでフォントを明示する。
MERMAID_CONFIG = """{
  "theme": "default",
  "themeVariables": {
    "fontFamily": "Hiragino Sans, Yu Gothic, Meiryo, sans-serif",
    "fontSize": "14px"
  },
  "er": { "layoutDirection": "LR", "entityPadding": 12 }
}
"""


def extract_blocks(md_path: Path) -> list[tuple[str, Path]]:
    """(mermaid ソース, 出力 PNG パス) の一覧を返す。"""
    lines = md_path.read_text(encoding="utf-8").splitlines()
    blocks: list[tuple[str, Path]] = []
    i, seq = 0, 0
    while i < len(lines):
        if lines[i].strip().startswith("```mermaid"):
            body: list[str] = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                body.append(lines[i])
                i += 1
            i += 1
            seq += 1
            out = None
            for look in lines[i : i + 3]:  # 直後数行からマーカーを探す
                marker = look.strip()
                if marker.startswith("<!-- xlsx-image:") and marker.endswith("-->"):
                    rel = marker[len("<!-- xlsx-image:") : -len("-->")].strip()
                    out = (md_path.parent / rel).resolve()
                    break
            if out is None:
                out = md_path.parent / "images" / f"{md_path.stem}-mermaid{seq}.png"
            blocks.append(("\n".join(body), out))
            continue
        i += 1
    return blocks


def render(source: str, out_path: Path) -> None:
    if shutil.which("npx") is None:
        raise SystemExit("npx が見つかりません。Node.js を入れてから再実行してください")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        mmd = Path(tmp) / "diagram.mmd"
        cfg = Path(tmp) / "config.json"
        mmd.write_text(source, encoding="utf-8")
        cfg.write_text(MERMAID_CONFIG, encoding="utf-8")
        cmd = [
            "npx", "-y", MERMAID_CLI,
            "-i", str(mmd),
            "-o", str(out_path),
            "-c", str(cfg),
            "-b", "white",
            "-s", str(SCALE),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0 or not out_path.exists():
            sys.stderr.write(proc.stdout + proc.stderr)
            raise SystemExit(f"mermaid の描画に失敗しました: {out_path}")


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Markdown の mermaid を PNG に書き出す")
    ap.add_argument("sources", nargs="*", type=Path, help="対象の .md (既定: docs/*.md)")
    args = ap.parse_args(argv)

    docs_dir = Path(__file__).resolve().parent.parent
    sources = args.sources or sorted(docs_dir.glob("*.md"))
    total = 0
    for src in sources:
        for source, out in extract_blocks(src):
            render(source, out)
            print(f"{src} -> {out.relative_to(docs_dir.parent)}")
            total += 1
    if total == 0:
        print("mermaid ブロックが見つかりませんでした")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
