import re
from html import escape


def format_ai_content(content: str) -> str:
    """Render Markdown-style response text as safe semantic HTML."""
    text = re.sub(r"<br\s*/?>\s*(?=•)", " • ", str(content or ""), flags=re.IGNORECASE)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    shloka_blocks: dict[str, str] = {}

    def preserve_shloka(match: re.Match[str]) -> str:
        key = f"DHARMA_SHLOKA_{len(shloka_blocks)}"
        verse = re.sub(r"\s*\n\s*", " ", match.group(2)).strip()
        shloka_blocks[key] = (
            '<div class="shloka-card">'
            '<div class="shloka-label">🪷 मूल श्लोक (Authentic Sanskrit)</div>'
            f'<div class="shloka-text">{escape(verse)}</div></div>'
        )
        return key

    text = re.sub(
        r"\*\*(मूल श्लोक[^*]*)\*\*\s*(.*?)(?=\n\s*\n|\n\s*\*\*(?:भावार्थ|धर्म)|$)",
        preserve_shloka,
        text,
        flags=re.DOTALL,
    )

    def inline_markup(value: str) -> str:
        safe_value = escape(value.strip())
        safe_value = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", safe_value)
        return re.sub(r"(?<!\*)\*([^*\n]+?)\*(?!\*)", r"<em>\1</em>", safe_value)

    def table_cells(line: str) -> list[str]:
        return [cell.strip() for cell in line.strip().strip("|").split("|")]

    output: list[str] = []
    list_kind: str | None = None
    table_headers: list[str] | None = None
    table_mode = False

    def close_list() -> None:
        nonlocal list_kind
        if list_kind:
            output.append(f"</{list_kind}>")
            list_kind = None

    lines = text.splitlines()
    for line_index, raw_line in enumerate(lines):
        line = raw_line.strip()
        if not line:
            next_content = next(
                (candidate.strip() for candidate in lines[line_index + 1:] if candidate.strip()),
                "",
            )
            if list_kind != "ol" or not re.match(r"^\d+[.)]\s+", next_content):
                close_list()
            table_mode = False
            continue

        if line.startswith("DHARMA_SHLOKA_") and line in shloka_blocks:
            close_list()
            output.append(shloka_blocks[line])
            continue

        if "|" in line:
            cells = table_cells(line)
            if cells and all(re.fullmatch(r":?-{3,}:?", cell.replace(" ", "")) for cell in cells):
                table_mode = True
                continue
            if len(cells) >= 2:
                close_list()
                if table_headers is None or not table_mode:
                    table_headers = cells
                    table_mode = True
                    continue
                heading = cells[0]
                if heading:
                    output.append(f"<h4>{inline_markup(heading)}</h4>")
                details: list[str] = []
                for index, value in enumerate(cells[1:], start=1):
                    label = table_headers[index] if index < len(table_headers) else ""
                    if not value:
                        continue
                    bullets = [part.strip(" •") for part in value.split(" • ") if part.strip(" •")]
                    if len(bullets) > 1:
                        detail_items = "".join(f"<li>{inline_markup(item)}</li>" for item in bullets)
                        details.append(
                            f"<li><strong>{inline_markup(label)}:</strong><ul>{detail_items}</ul></li>"
                        )
                    else:
                        details.append(
                            f"<li><strong>{inline_markup(label)}:</strong> {inline_markup(value)}</li>"
                        )
                if details:
                    output.append(f"<ul>{''.join(details)}</ul>")
                continue

        if table_mode:
            table_mode = False
            table_headers = None

        heading_match = re.match(r"^#{1,6}\s+(.+)$", line)
        if heading_match:
            close_list()
            output.append(f"<h3>{inline_markup(heading_match.group(1))}</h3>")
            continue
        if line.startswith("**") and line.endswith("**") and len(line) > 4:
            close_list()
            output.append(f"<h3>{inline_markup(line[2:-2])}</h3>")
            continue

        bullet_match = re.match(r"^(?:[-*•])\s+(.+)$", line)
        numbered_match = re.match(r"^\d+[.)]\s+(.+)$", line)
        match = bullet_match or numbered_match
        if match:
            kind = "ul" if bullet_match else "ol"
            if list_kind != kind:
                close_list()
                output.append(f"<{kind}>")
                list_kind = kind
            output.append(f"<li>{inline_markup(match.group(1))}</li>")
            continue

        close_list()
        output.append(f"<p>{inline_markup(line)}</p>")

    close_list()
    return "".join(output)
