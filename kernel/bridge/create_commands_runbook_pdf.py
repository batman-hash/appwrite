#!/usr/bin/env python3
"""
Create a simple PDF from COMMANDS_RUNBOOK.md without external dependencies.
"""
from pathlib import Path
import io
import textwrap


SOURCE_FILE = Path("COMMANDS_RUNBOOK.md")
OUTPUT_FILE = Path("COMMANDS_RUNBOOK.pdf")
PAGE_WIDTH = 612
PAGE_HEIGHT = 792
MARGIN_X = 50
TOP_Y = 742
LINES_PER_PAGE = 48
FONT_SIZE = 10
LINE_HEIGHT = 14
WRAP_WIDTH = 92


def normalize_markdown_lines(markdown_text: str) -> list[str]:
    """Convert simple markdown into printable plain text lines."""
    lines: list[str] = []
    in_code_block = False

    for raw_line in markdown_text.splitlines():
        line = raw_line.rstrip()

        if line.startswith("```"):
            in_code_block = not in_code_block
            if not in_code_block:
                lines.append("")
            continue

        if in_code_block:
            lines.append(f"    {line}")
            continue

        if line.startswith("#"):
            heading = line.lstrip("#").strip()
            if lines and lines[-1] != "":
                lines.append("")
            lines.append(heading.upper())
            lines.append("-" * min(len(heading), 72))
            continue

        if line.startswith("Comment:"):
            lines.append(f"Comment: {line.split(':', 1)[1].strip()}")
            continue

        cleaned = (
            line.replace("`", "")
            .replace("**", "")
            .replace("✅ ", "")
        )
        lines.append(cleaned)

    return lines


def wrap_lines(lines: list[str]) -> list[str]:
    """Wrap text lines so they fit inside the PDF page width."""
    wrapped: list[str] = []
    for line in lines:
        if not line:
            wrapped.append("")
            continue

        indent = "    " if line.startswith("    ") else ""
        content = line[len(indent):]
        wrapped_lines = textwrap.wrap(
            content,
            width=WRAP_WIDTH - len(indent),
            break_long_words=False,
            break_on_hyphens=False,
        )
        if not wrapped_lines:
            wrapped.append(indent)
            continue
        for entry in wrapped_lines:
            wrapped.append(f"{indent}{entry}")
    return wrapped


def chunk_pages(lines: list[str]) -> list[list[str]]:
    """Split lines into pages."""
    if not lines:
        return [["Commands Runbook is empty."]]
    return [lines[index:index + LINES_PER_PAGE] for index in range(0, len(lines), LINES_PER_PAGE)]


def pdf_escape(value: str) -> str:
    """Escape text content for PDF literal strings."""
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def build_content_stream(lines: list[str]) -> bytes:
    """Create the page text stream."""
    parts = [
        "BT",
        f"/F1 {FONT_SIZE} Tf",
        f"{LINE_HEIGHT} TL",
        f"1 0 0 1 {MARGIN_X} {TOP_Y} Tm",
    ]

    for index, line in enumerate(lines):
        escaped = pdf_escape(line)
        if index == 0:
            parts.append(f"({escaped}) Tj")
        else:
            parts.append(f"T* ({escaped}) Tj")

    parts.append("ET")
    return "\n".join(parts).encode("latin-1", errors="replace")


def build_pdf(page_groups: list[list[str]]) -> bytes:
    """Build a minimal multi-page PDF document."""
    objects: dict[int, bytes] = {
        1: b"<< /Type /Catalog /Pages 2 0 R >>",
        3: b"<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>",
    }

    page_object_numbers: list[int] = []
    next_object = 4

    for page_lines in page_groups:
        page_number = next_object
        content_number = next_object + 1
        next_object += 2

        stream = build_content_stream(page_lines)
        objects[content_number] = (
            f"<< /Length {len(stream)} >>\nstream\n".encode("latin-1")
            + stream
            + b"\nendstream"
        )
        objects[page_number] = (
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {PAGE_WIDTH} {PAGE_HEIGHT}] "
            f"/Resources << /Font << /F1 3 0 R >> >> /Contents {content_number} 0 R >>"
        ).encode("latin-1")
        page_object_numbers.append(page_number)

    kids = " ".join(f"{number} 0 R" for number in page_object_numbers)
    objects[2] = f"<< /Type /Pages /Kids [{kids}] /Count {len(page_object_numbers)} >>".encode("latin-1")

    buffer = io.BytesIO()
    buffer.write(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")

    offsets = [0] * (max(objects) + 1)
    for object_number in range(1, max(objects) + 1):
        offsets[object_number] = buffer.tell()
        buffer.write(f"{object_number} 0 obj\n".encode("latin-1"))
        buffer.write(objects[object_number])
        buffer.write(b"\nendobj\n")

    xref_offset = buffer.tell()
    buffer.write(f"xref\n0 {len(offsets)}\n".encode("latin-1"))
    buffer.write(b"0000000000 65535 f \n")
    for object_number in range(1, len(offsets)):
        buffer.write(f"{offsets[object_number]:010d} 00000 n \n".encode("latin-1"))

    buffer.write(
        (
            f"trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\n"
            f"startxref\n{xref_offset}\n%%EOF\n"
        ).encode("latin-1")
    )
    return buffer.getvalue()


def main() -> None:
    markdown_text = SOURCE_FILE.read_text(encoding="utf-8")
    lines = normalize_markdown_lines(markdown_text)
    wrapped_lines = wrap_lines(lines)
    pages = chunk_pages(wrapped_lines)
    pdf_bytes = build_pdf(pages)
    OUTPUT_FILE.write_bytes(pdf_bytes)
    print(f"✅ PDF created: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
