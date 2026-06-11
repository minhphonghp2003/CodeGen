"""File append/upsert logic for adding members to existing C# files."""

from __future__ import annotations

import re
from pathlib import Path


def find_type_closing_brace(content: str) -> int:
    """Find the index of the closing brace at depth 2 (type-level).

    Depth 0 = top level, depth 1 = namespace, depth 2 = type.
    We want the last '}' that closes the type.
    """
    depth = 0
    last_type_close = -1
    for i, ch in enumerate(content):
        if ch == "{":
            depth += 1
        elif ch == "}":
            if depth == 2:
                last_type_close = i
            depth -= 1
    return last_type_close


def append_interface_line(content: str, interface_line: str) -> str:
    """Append a new interface implementation to the class declaration.

    Finds the last IRequestHandler<...> line, adds a comma, and inserts
    the new interface on the next line with matching indentation.
    """
    lines = content.splitlines()
    last_idx = -1
    for i, line in enumerate(lines):
        if "IRequestHandler<" in line and line.rstrip().endswith(">"):
            last_idx = i

    if last_idx < 0:
        return content

    # Add comma to current last interface line
    lines[last_idx] = lines[last_idx].rstrip() + ","

    # Match indentation
    indent_match = re.match(r"^(\s*)", lines[last_idx])
    indent = indent_match.group(1) if indent_match else "        "
    lines.insert(last_idx + 1, indent + interface_line)

    return "\n".join(lines)


def upsert_member(
    file_path: Path,
    marker: str,
    new_file_content: str,
    member_content: str,
    interface_line: str | None,
    solution_dir: Path,
    dry_run: bool = False,
) -> str:
    """Append a member to an existing file, or create the file if missing.

    Returns a status message.
    """
    rel = file_path.relative_to(solution_dir) if file_path.is_absolute() else file_path

    if not file_path.exists():
        if dry_run:
            return f"WOULD CREATE: {rel}"
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(new_file_content, encoding="utf-8")
        return f"CREATED: {rel}"

    content = file_path.read_text(encoding="utf-8")

    if marker in content:
        return f"SKIPPED (already has {marker}): {rel}"

    if dry_run:
        return f"WOULD APPEND: {rel}"

    # Append interface line to class declaration if needed
    if interface_line:
        content = append_interface_line(content, interface_line)

    # Find insertion point
    insert_at = find_type_closing_brace(content)
    if insert_at < 0:
        return f"SKIPPED (no insertion point): {rel}"

    content = content[:insert_at] + "\n" + member_content + content[insert_at:]
    file_path.write_text(content, encoding="utf-8")
    return f"APPENDED: {rel}"
