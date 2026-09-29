#!/usr/bin/env python3
"""
gdocs_builder.py — Robust Markdown to Google Docs Renderer & Document Manager
Uses Google Workspace CLI (gws) with Google Docs API batchUpdate.
Implements the Google Docs REST API v1 specification for rich rendering:
  - Document Title & Heading Hierarchy (Title, Heading 1-4)
  - Fenced Code Blocks (Consolas/Roboto Mono, shading background, left accent border, ASCII diagram preservation)
  - Blockquotes (left border, italic, indent)
  - Horizontal Rules (borderBottom)
  - Metadata Header Lines (compact spacing)
  - Bullet Lists, Numbered Lists, Checklists
  - Tables (styled header row, body cell padding, inline styles in cells, column widths)
  - Inline Rich Formatting (Hyperlinks, raw URLs, inline code, bold, italic, strikethrough, nested styles)
  - BatchUpdate request chunking (chunks of 50) and exponential backoff retry on 429 quota limits.
  - Bidirectional read_doc AST conversion from Google Docs back to Markdown.
"""

import argparse
import json
import re
import subprocess
import sys
import time

# Monospace font family for code blocks and inline code runs
CODE_FONT_FAMILY = "Consolas"

# Metadata prefixes matching consult reports
METADATA_KEYS = (
    "To:",
    "From:",
    "Case ID:",
    "Case Number:",
    "Customer:",
    "Product:",
    "Priority:",
    "Subject:",
    "Status:",
    "Date:",
    "Author:",
)

# Inline markdown regex patterns in priority order
INLINE_PATTERNS = [
    ("code", re.compile(r"`([^`\n]+)`")),
    ("link", re.compile(r"\[([^\]\n]+)\]\(((?:https?://|mailto:|#|[^\s)]+)[^\s)]*)\)")),
    ("bold_italic", re.compile(r"\*\*\*(.+?)\*\*\*|___(.+?)___")),
    (
        "bold",
        re.compile(
            r"(?<!\*)\*\*(?![\s*])(.+?)(?<![\s*])\*\*(?!\*)|(?<![\w_])__(?![\s_])(.+?)(?<![\s_])__(?![\w_])"
        ),
    ),
    ("strike", re.compile(r"~~(.+?)~~")),
    (
        "italic",
        re.compile(
            r"(?<!\*)\*(?![\s*])(.+?)(?<![\s*])\*(?!\*)|(?<![\w_])_(?![\s_])(.+?)(?<![\s_])_(?![\w_])"
        ),
    ),
    ("raw_url", re.compile(r"https?://[^\s<>()]+[^\s<>().,:;!?]")),
]


def get_doc(doc_id):
    for attempt in range(5):
        cmd = [
            "gws",
            "docs",
            "documents",
            "get",
            "--params",
            json.dumps({"documentId": doc_id}),
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            try:
                return json.loads(res.stdout)
            except json.JSONDecodeError as err:
                print(f"[gdocs] JSON parse error: {err}", file=sys.stderr)
                sys.exit(1)
        elif "429" in res.stderr or "Quota exceeded" in res.stderr:
            wait_time = (attempt + 1) * 10
            print(
                f"[gdocs] Rate limit encountered, waiting {wait_time}s...",
                file=sys.stderr,
            )
            time.sleep(wait_time)
        else:
            print(f"[gdocs] Error fetching doc {doc_id}: {res.stderr}", file=sys.stderr)
            sys.exit(1)
    raise Exception("Failed to get_doc after retries")


def execute_batch(doc_id, requests):
    """
    Executes a list of batchUpdate requests on doc_id.
    Groups requests into chunks of 50 to avoid request payload limits,
    with exponential backoff retries on 429 quota limits.
    """
    if not requests:
        return {}

    CHUNK_SIZE = 50
    responses = []

    for i in range(0, len(requests), CHUNK_SIZE):
        chunk = requests[i : i + CHUNK_SIZE]
        body = {"requests": chunk}
        cmd = [
            "gws",
            "docs",
            "documents",
            "batchUpdate",
            "--params",
            json.dumps({"documentId": doc_id}),
            "--json",
            json.dumps(body),
        ]
        for attempt in range(8):
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode == 0:
                try:
                    responses.append(json.loads(res.stdout))
                    break
                except json.JSONDecodeError as err:
                    print(
                        f"[gdocs] JSON parse error during batchUpdate: {err}",
                        file=sys.stderr,
                    )
                    break
            elif "429" in res.stderr or "Quota exceeded" in res.stderr:
                wait_time = (attempt + 1) * 15
                print(
                    f"[gdocs] Rate limit encountered during batchUpdate, waiting {wait_time}s...",
                    file=sys.stderr,
                )
                time.sleep(wait_time)
            else:
                print(
                    f"[gdocs] Error during batchUpdate: {res.stderr}\n{res.stdout}",
                    file=sys.stderr,
                )
                raise Exception(f"batchUpdate failed: {res.stderr}")
        else:
            raise Exception("Failed execute_batch after retries")

    return responses[0] if len(responses) == 1 else responses


def create_doc(title):
    cmd = ["gws", "docs", "documents", "create", "--json", json.dumps({"title": title})]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"[gdocs] Error creating document: {res.stderr}", file=sys.stderr)
        sys.exit(1)
    try:
        data = json.loads(res.stdout)
    except json.JSONDecodeError as err:
        print(f"[gdocs] JSON parse error creating document: {err}", file=sys.stderr)
        sys.exit(1)
    doc_id = data.get("documentId")
    url = f"https://docs.google.com/document/d/{doc_id}/edit"
    print(f"Created Google Doc: '{title}'")
    print(f"Document ID: {doc_id}")
    print(f"URL: {url}")
    return doc_id, url


def clear_doc(doc_id):
    doc = get_doc(doc_id)
    end_idx = doc["body"]["content"][-1]["endIndex"]
    if end_idx > 2:
        reqs = [
            {"deleteParagraphBullets": {"range": {"startIndex": 1, "endIndex": end_idx - 1}}},
            {
                "updateParagraphStyle": {
                    "range": {"startIndex": 1, "endIndex": end_idx - 1},
                    "paragraphStyle": {"namedStyleType": "NORMAL_TEXT"},
                    "fields": "namedStyleType",
                }
            },
            {"deleteContentRange": {"range": {"startIndex": 1, "endIndex": end_idx - 1}}},
        ]
        execute_batch(doc_id, reqs)
        print(f"[gdocs] Cleared doc {doc_id}")


def _tokenize_inline(text, current_style):
    if not text:
        return []

    best_m = None
    best_type = None

    for p_type, pat in INLINE_PATTERNS:
        m = pat.search(text)
        if m and (
            best_m is None
            or m.start() < best_m.start()
            or (m.start() == best_m.start() and m.end() > best_m.end())
        ):
            best_m = m
            best_type = p_type

    if not best_m:
        return [(text, current_style)]

    frags = []
    # Prefix text before matched delimiter
    if best_m.start() > 0:
        frags.extend(_tokenize_inline(text[: best_m.start()], current_style))

    # Process matched token
    if best_type == "code":
        # Verbatim code inside backticks: strip backticks, do not parse nested markdown
        code_text = best_m.group(1)
        st = dict(current_style)
        st["code"] = True
        frags.append((code_text, st))
    elif best_type == "link":
        anchor = best_m.group(1)
        url = best_m.group(2)
        st = dict(current_style)
        st["link"] = url
        # Recursively parse inside anchor for bold, italic, code
        frags.extend(_tokenize_inline(anchor, st))
    elif best_type == "bold_italic":
        inner = best_m.group(1) if best_m.group(1) is not None else best_m.group(2)
        st = dict(current_style)
        st["bold"] = True
        st["italic"] = True
        frags.extend(_tokenize_inline(inner, st))
    elif best_type == "bold":
        inner = best_m.group(1) if best_m.group(1) is not None else best_m.group(2)
        st = dict(current_style)
        st["bold"] = True
        frags.extend(_tokenize_inline(inner, st))
    elif best_type == "strike":
        inner = best_m.group(1)
        st = dict(current_style)
        st["strikethrough"] = True
        frags.extend(_tokenize_inline(inner, st))
    elif best_type == "italic":
        inner = best_m.group(1) if best_m.group(1) is not None else best_m.group(2)
        st = dict(current_style)
        st["italic"] = True
        frags.extend(_tokenize_inline(inner, st))
    elif best_type == "raw_url":
        url = best_m.group(0)
        st = dict(current_style)
        st["link"] = url
        frags.append((url, st))

    # Suffix text after matched delimiter
    if best_m.end() < len(text):
        frags.extend(_tokenize_inline(text[best_m.end() :], current_style))

    return frags


_LATEX_SYMBOL_REPLACEMENTS = [
    (re.compile(r"\$\s*\\(?:rightarrow|to)\s*\$"), "→"),
    (re.compile(r"\$\s*\\leftarrow\s*\$"), "←"),
    (re.compile(r"\$\s*\\leftrightarrow\s*\$"), "↔"),
    (re.compile(r"\$\s*\\Rightarrow\s*\$"), "⇒"),
    (re.compile(r"\$\s*\\Leftarrow\s*\$"), "⇐"),
    (re.compile(r"\$\s*\\Leftrightarrow\s*\$"), "⇔"),
    (re.compile(r"\$\s*\\times\s*\$"), "×"),
    (re.compile(r"\$\s*\\pm\s*\$"), "±"),
    (re.compile(r"\$\s*\\approx\s*\$"), "≈"),
    (re.compile(r"\$\s*\\(?:neq|ne)\s*\$"), "≠"),
    (re.compile(r"\$\s*\\(?:leq|le)\s*\$"), "≤"),
    (re.compile(r"\$\s*\\(?:geq|ge)\s*\$"), "≥"),
    (re.compile(r"\$\s*\\(?:ldots|dots)\s*\$"), "…"),
]
_STANDALONE_TO_RE = re.compile(r"(^|\s+)\\to(\s+|$)")


def clean_latex_symbols(text: str) -> str:
    """
    Replaces common LaTeX inline math notation outside code blocks with clean Unicode symbols.
    """
    for pattern, repl in _LATEX_SYMBOL_REPLACEMENTS:
        text = pattern.sub(repl, text)
    text = text.replace(" \\to ", " → ")
    text = _STANDALONE_TO_RE.sub(r"\1→\2", text)
    return text


def extract_inline_formatting(raw_text):
    """
    Extracts inline markdown formatting (code, links, raw URLs, bold, italic, strikethrough).
    Returns clean_text (with markdown delimiters stripped) and a list of style spans.
    Each span dict includes:
      start, end, bold, italic, strikethrough, code, link, textStyle, fields.
    """
    raw_text = clean_latex_symbols(raw_text)
    frags = _tokenize_inline(raw_text, {})
    clean_text = ""
    spans = []

    for text_frag, style in frags:
        if not text_frag:
            continue
        start = len(clean_text)
        clean_text += text_frag
        end = len(clean_text)

        text_style = {}
        fields = []

        if style.get("bold"):
            text_style["bold"] = True
            fields.append("bold")
        if style.get("italic"):
            text_style["italic"] = True
            fields.append("italic")
        if style.get("strikethrough"):
            text_style["strikethrough"] = True
            fields.append("strikethrough")

        if style.get("code"):
            text_style["weightedFontFamily"] = {"fontFamily": CODE_FONT_FAMILY}
            text_style["fontSize"] = {"magnitude": 9.5, "unit": "PT"}
            text_style["foregroundColor"] = {
                "color": {"rgbColor": {"red": 0.075, "green": 0.45, "blue": 0.20}}
            }
            fields.extend(["weightedFontFamily", "fontSize", "foregroundColor"])

        if style.get("link"):
            text_style["link"] = {"url": style["link"]}
            text_style["underline"] = True
            fields.extend(["link", "underline"])
            if not style.get("code"):
                text_style["foregroundColor"] = {
                    "color": {"rgbColor": {"red": 0.08, "green": 0.4, "blue": 0.85}}
                }
                if "foregroundColor" not in fields:
                    fields.append("foregroundColor")

        if fields:
            # Merge with previous span if styling is identical and spans are contiguous
            if spans and spans[-1]["end"] == start and spans[-1]["textStyle"] == text_style:
                spans[-1]["end"] = end
            else:
                spans.append(
                    {
                        "start": start,
                        "end": end,
                        "bold": style.get("bold", False),
                        "italic": style.get("italic", False),
                        "strikethrough": style.get("strikethrough", False),
                        "code": style.get("code", False),
                        "link": style.get("link"),
                        "textStyle": text_style,
                        "fields": ",".join(dict.fromkeys(fields)),
                    }
                )

    return clean_text, spans


def extract_formatting(raw_text):
    """
    Backwards compatibility helper: returns clean_text and bold_ranges list of (start, end).
    """
    clean_text, spans = extract_inline_formatting(raw_text)
    bold_ranges = [(s["start"], s["end"]) for s in spans if s.get("bold")]
    return clean_text, bold_ranges


def is_metadata_line(line):
    clean = line.strip()
    if clean.startswith("- "):
        clean = clean[2:].strip()
    return any(clean.startswith((f"**{k}**", f"**{k}")) for k in METADATA_KEYS)


def parse_markdown_to_segments(md_text):
    """
    Parses Markdown text into an AST of document segments:
      - Title / Headings (HEADING_1 through HEADING_4)
      - Fenced code blocks (preserves exact whitespace, diagrams; strips ``` fence lines)
      - Blockquotes (> )
      - Horizontal rules (---, ***)
      - Metadata header lines (**Case ID:**, **Customer:**, etc.)
      - Bullet lists (- , * )
      - Numbered lists (1. , 2. )
      - Checklists (- [ ] , - [x] )
      - Tables (| ... |)
      - Paragraphs
    Self-referential deliverable links are stripped.
    """
    raw_lines = md_text.splitlines()

    # Determine if document has a top-level # Title
    has_doc_title = False
    in_code = False
    for line in raw_lines:
        s = line.strip()
        if s.startswith("```"):
            in_code = not in_code
            continue
        if not in_code and s.startswith("# ") and not s.startswith("## "):
            has_doc_title = True
            break

    elements = []
    in_table = False
    table_rows = []
    in_code_block = False
    code_lines = []
    code_lang = ""
    seen_first_h1 = False

    for line in raw_lines:
        stripped = line.strip()

        # Fenced code block delimiter
        if stripped.startswith("```"):
            if in_table and table_rows:
                elements.append({"type": "table", "rows": table_rows})
                table_rows = []
                in_table = False

            if in_code_block:
                elements.append({"type": "code_block", "lines": code_lines, "lang": code_lang})
                code_lines = []
                code_lang = ""
                in_code_block = False
            else:
                in_code_block = True
                code_lang = stripped[3:].strip()
                code_lines = []
            continue

        if in_code_block:
            # Preserve exact indentation, leading whitespace, ASCII diagrams
            code_lines.append(line.rstrip("\r\n"))
            continue

        # Strip self-referential Google Doc deliverable links
        if "Google Doc Deliverable:" in stripped or "[Open Google Doc]" in stripped:
            continue

        # Blank line
        if not stripped:
            if in_table and table_rows:
                elements.append({"type": "table", "rows": table_rows})
                table_rows = []
                in_table = False
            continue

        # Table rows
        if stripped.startswith("|") and stripped.endswith("|"):
            clean_check = stripped.replace("|", "").replace("-", "").replace(":", "").strip()
            if not clean_check:
                # Markdown separator row (|---|---|)
                continue
            cells = [c.strip() for c in stripped[1:-1].split("|")]
            table_rows.append(cells)
            in_table = True
            continue
        else:
            if in_table and table_rows:
                elements.append({"type": "table", "rows": table_rows})
                table_rows = []
                in_table = False

        # Metadata header lines
        if is_metadata_line(stripped):
            text_val = stripped[2:].strip() if stripped.startswith("- ") else stripped
            elements.append({"type": "metadata", "text": text_val})
            continue

        # Headings
        if stripped.startswith("# ") and not stripped.startswith("## "):
            h_text = stripped[2:].strip()
            if has_doc_title and not seen_first_h1:
                elements.append({"type": "title", "text": h_text})
                seen_first_h1 = True
            else:
                elements.append({"type": "heading_1", "text": h_text})
        elif stripped.startswith("## ") and not stripped.startswith("### "):
            h_text = stripped[3:].strip()
            if has_doc_title:
                elements.append({"type": "heading_1", "text": h_text})
            else:
                elements.append({"type": "heading_2", "text": h_text})
        elif stripped.startswith("### ") and not stripped.startswith("#### "):
            h_text = stripped[4:].strip()
            if has_doc_title:
                elements.append({"type": "heading_2", "text": h_text})
            else:
                elements.append({"type": "heading_3", "text": h_text})
        elif stripped.startswith("#### ") and not stripped.startswith("##### "):
            h_text = stripped[5:].strip()
            if has_doc_title:
                elements.append({"type": "heading_3", "text": h_text})
            else:
                elements.append({"type": "heading_4", "text": h_text})
        elif stripped.startswith("##### "):
            h_text = stripped[6:].strip()
            elements.append({"type": "heading_4", "text": h_text})
        elif stripped.startswith("> ") or stripped == ">":
            bq_text = stripped[2:].strip() if stripped.startswith("> ") else ""
            elements.append({"type": "blockquote", "text": bq_text})
        elif stripped in ("---", "***", "___") or re.match(r"^[-*_]{3,}$", stripped):
            elements.append({"type": "hr", "text": ""})
        elif stripped.startswith(("- [ ] ", "- [x] ", "* [ ] ", "* [x] ")):
            chk_text = stripped[6:].strip()
            elements.append({"type": "checklist", "text": chk_text})
        elif stripped.startswith(("- ", "* ")):
            elements.append({"type": "bullet", "text": stripped[2:].strip()})
        elif re.match(r"^\d+\.\s+", stripped):
            num_match = re.match(r"^\d+\.\s+(.*)", stripped)
            if num_match:
                elements.append({"type": "numbered", "text": num_match.group(1).strip()})
        elif (
            stripped.startswith("*") and stripped.endswith("*") and not stripped.startswith("**")
        ):
            elements.append({"type": "italic_para", "text": stripped[1:-1].strip()})
        else:
            elements.append({"type": "paragraph", "text": stripped})

    if in_code_block:
        elements.append({"type": "code_block", "lines": code_lines, "lang": code_lang})
    if in_table and table_rows:
        elements.append({"type": "table", "rows": table_rows})

    return elements


def render_markdown(doc_id, md_text, clear=True):
    if clear:
        clear_doc(doc_id)

    elements = parse_markdown_to_segments(md_text)

    # Split elements into segments separated by table
    segments = []
    current_seg = []
    for el in elements:
        if el["type"] == "table":
            if current_seg:
                segments.append(("text", current_seg))
                current_seg = []
            segments.append(("table", el["rows"]))
        else:
            current_seg.append(el)
    if current_seg:
        segments.append(("text", current_seg))

    for seg_type, seg_data in segments:
        doc = get_doc(doc_id)
        end_idx = doc["body"]["content"][-1]["endIndex"]
        insert_pos = end_idx - 1

        if seg_type == "text":
            full_text = ""
            p_style_reqs = []
            list_groups = []  # (start, end, preset)
            text_style_reqs = []

            for el in seg_data:
                el_type = el["type"]

                if el_type == "code_block":
                    lines = el.get("lines", [])
                    code_str = "\n".join(lines) + "\n" if lines else "\n"
                    p_start = insert_pos + len(full_text)
                    full_text += code_str
                    p_end = insert_pos + len(full_text)

                    # Code block paragraph styling
                    p_style_reqs.append(
                        {
                            "updateParagraphStyle": {
                                "range": {"startIndex": p_start, "endIndex": p_end},
                                "paragraphStyle": {
                                    "shading": {
                                        "backgroundColor": {
                                            "color": {
                                                "rgbColor": {
                                                    "red": 0.965,
                                                    "green": 0.973,
                                                    "blue": 0.98,
                                                }
                                            }
                                        }
                                    },
                                    "borderLeft": {
                                        "color": {
                                            "color": {
                                                "rgbColor": {
                                                    "red": 0.12,
                                                    "green": 0.42,
                                                    "blue": 0.85,
                                                }
                                            }
                                        },
                                        "width": {"magnitude": 3.0, "unit": "PT"},
                                        "padding": {"magnitude": 8.0, "unit": "PT"},
                                        "dashStyle": "SOLID",
                                    },
                                    "spaceAbove": {"magnitude": 1.0, "unit": "PT"},
                                    "spaceBelow": {"magnitude": 1.0, "unit": "PT"},
                                    "lineSpacing": 100.0,
                                    "indentStart": {"magnitude": 6.0, "unit": "PT"},
                                },
                                "fields": "shading,borderLeft,spaceAbove,spaceBelow,lineSpacing,indentStart",
                            }
                        }
                    )

                    # Code block text styling
                    text_style_reqs.append(
                        {
                            "updateTextStyle": {
                                "range": {"startIndex": p_start, "endIndex": p_end},
                                "textStyle": {
                                    "weightedFontFamily": {"fontFamily": CODE_FONT_FAMILY},
                                    "fontSize": {"magnitude": 9.0, "unit": "PT"},
                                    "foregroundColor": {
                                        "color": {
                                            "rgbColor": {
                                                "red": 0.12,
                                                "green": 0.15,
                                                "blue": 0.18,
                                            }
                                        }
                                    },
                                },
                                "fields": "weightedFontFamily,fontSize,foregroundColor",
                            }
                        }
                    )
                    continue

                if el_type == "hr":
                    p_start = insert_pos + len(full_text)
                    full_text += "\n"
                    p_end = insert_pos + len(full_text)
                    p_style_reqs.append(
                        {
                            "updateParagraphStyle": {
                                "range": {"startIndex": p_start, "endIndex": p_end},
                                "paragraphStyle": {
                                    "borderBottom": {
                                        "color": {
                                            "color": {
                                                "rgbColor": {
                                                    "red": 0.82,
                                                    "green": 0.85,
                                                    "blue": 0.9,
                                                }
                                            }
                                        },
                                        "width": {"magnitude": 1.0, "unit": "PT"},
                                        "padding": {"magnitude": 4.0, "unit": "PT"},
                                        "dashStyle": "SOLID",
                                    },
                                    "spaceAbove": {"magnitude": 8.0, "unit": "PT"},
                                    "spaceBelow": {"magnitude": 8.0, "unit": "PT"},
                                },
                                "fields": "borderBottom,spaceAbove,spaceBelow",
                            }
                        }
                    )
                    continue

                # Process inline formatting for other element types
                raw_el_text = el.get("text", "")
                clean_text, spans = extract_inline_formatting(raw_el_text)
                clean_text = clean_text.strip("\r\n") + "\n"

                p_start = insert_pos + len(full_text)
                full_text += clean_text
                p_end = insert_pos + len(full_text)

                # Paragraph styling based on element type
                if el_type == "title":
                    p_style_reqs.append(
                        {
                            "updateParagraphStyle": {
                                "range": {"startIndex": p_start, "endIndex": p_end},
                                "paragraphStyle": {
                                    "namedStyleType": "TITLE",
                                    "spaceBelow": {"magnitude": 8.0, "unit": "PT"},
                                },
                                "fields": "namedStyleType,spaceBelow",
                            }
                        }
                    )
                elif el_type == "heading_1":
                    p_style_reqs.append(
                        {
                            "updateParagraphStyle": {
                                "range": {"startIndex": p_start, "endIndex": p_end},
                                "paragraphStyle": {
                                    "namedStyleType": "HEADING_1",
                                    "spaceAbove": {"magnitude": 16.0, "unit": "PT"},
                                    "spaceBelow": {"magnitude": 6.0, "unit": "PT"},
                                    "keepWithNext": True,
                                },
                                "fields": "namedStyleType,spaceAbove,spaceBelow,keepWithNext",
                            }
                        }
                    )
                elif el_type == "heading_2":
                    p_style_reqs.append(
                        {
                            "updateParagraphStyle": {
                                "range": {"startIndex": p_start, "endIndex": p_end},
                                "paragraphStyle": {
                                    "namedStyleType": "HEADING_2",
                                    "spaceAbove": {"magnitude": 12.0, "unit": "PT"},
                                    "spaceBelow": {"magnitude": 4.0, "unit": "PT"},
                                    "keepWithNext": True,
                                },
                                "fields": "namedStyleType,spaceAbove,spaceBelow,keepWithNext",
                            }
                        }
                    )
                elif el_type == "heading_3":
                    p_style_reqs.append(
                        {
                            "updateParagraphStyle": {
                                "range": {"startIndex": p_start, "endIndex": p_end},
                                "paragraphStyle": {
                                    "namedStyleType": "HEADING_3",
                                    "spaceAbove": {"magnitude": 8.0, "unit": "PT"},
                                    "spaceBelow": {"magnitude": 3.0, "unit": "PT"},
                                    "keepWithNext": True,
                                },
                                "fields": "namedStyleType,spaceAbove,spaceBelow,keepWithNext",
                            }
                        }
                    )
                elif el_type == "heading_4":
                    p_style_reqs.append(
                        {
                            "updateParagraphStyle": {
                                "range": {"startIndex": p_start, "endIndex": p_end},
                                "paragraphStyle": {
                                    "namedStyleType": "HEADING_4",
                                    "spaceAbove": {"magnitude": 6.0, "unit": "PT"},
                                    "spaceBelow": {"magnitude": 2.0, "unit": "PT"},
                                    "keepWithNext": True,
                                },
                                "fields": "namedStyleType,spaceAbove,spaceBelow,keepWithNext",
                            }
                        }
                    )
                elif el_type == "blockquote":
                    p_style_reqs.append(
                        {
                            "updateParagraphStyle": {
                                "range": {"startIndex": p_start, "endIndex": p_end},
                                "paragraphStyle": {
                                    "borderLeft": {
                                        "color": {
                                            "color": {
                                                "rgbColor": {
                                                    "red": 0.6,
                                                    "green": 0.65,
                                                    "blue": 0.7,
                                                }
                                            }
                                        },
                                        "width": {"magnitude": 3.0, "unit": "PT"},
                                        "padding": {"magnitude": 8.0, "unit": "PT"},
                                        "dashStyle": "SOLID",
                                    },
                                    "spaceAbove": {"magnitude": 4.0, "unit": "PT"},
                                    "spaceBelow": {"magnitude": 4.0, "unit": "PT"},
                                    "indentStart": {"magnitude": 12.0, "unit": "PT"},
                                },
                                "fields": "borderLeft,spaceAbove,spaceBelow,indentStart",
                            }
                        }
                    )
                    text_style_reqs.append(
                        {
                            "updateTextStyle": {
                                "range": {"startIndex": p_start, "endIndex": p_end},
                                "textStyle": {"italic": True},
                                "fields": "italic",
                            }
                        }
                    )
                elif el_type == "metadata":
                    p_style_reqs.append(
                        {
                            "updateParagraphStyle": {
                                "range": {"startIndex": p_start, "endIndex": p_end},
                                "paragraphStyle": {
                                    "spaceAbove": {"magnitude": 1.0, "unit": "PT"},
                                    "spaceBelow": {"magnitude": 2.0, "unit": "PT"},
                                    "lineSpacing": 115.0,
                                },
                                "fields": "spaceAbove,spaceBelow,lineSpacing",
                            }
                        }
                    )
                elif el_type in ("bullet", "numbered", "checklist"):
                    preset = "BULLET_DISC_CIRCLE_SQUARE"
                    if el_type == "numbered":
                        preset = "NUMBERED_DECIMAL_ALPHA_ROMAN"
                    elif el_type == "checklist":
                        preset = "BULLET_CHECKBOX"

                    # Group contiguous list items sharing the same preset into a single range
                    if (
                        list_groups
                        and list_groups[-1][2] == preset
                        and list_groups[-1][1] == p_start
                    ):
                        list_groups[-1] = (list_groups[-1][0], p_end, preset)
                    else:
                        list_groups.append((p_start, p_end, preset))
                elif el_type == "italic_para":
                    text_style_reqs.append(
                        {
                            "updateTextStyle": {
                                "range": {"startIndex": p_start, "endIndex": p_end},
                                "textStyle": {
                                    "italic": True,
                                    "fontSize": {"magnitude": 11.0, "unit": "PT"},
                                    "foregroundColor": {
                                        "color": {
                                            "rgbColor": {
                                                "red": 0.4,
                                                "green": 0.4,
                                                "blue": 0.4,
                                            }
                                        }
                                    },
                                },
                                "fields": "italic,fontSize,foregroundColor",
                            }
                        }
                    )

                # Apply extracted inline style spans (code, links, bold, italic, strikethrough)
                for span in spans:
                    s_start = p_start + span["start"]
                    s_end = p_start + span["end"]
                    if s_end > s_start:
                        text_style_reqs.append(
                            {
                                "updateTextStyle": {
                                    "range": {"startIndex": s_start, "endIndex": s_end},
                                    "textStyle": span["textStyle"],
                                    "fields": span["fields"],
                                }
                            }
                        )

            # 1. Insert full text
            execute_batch(
                doc_id,
                [
                    {
                        "insertText": {
                            "location": {"index": insert_pos},
                            "text": full_text,
                        }
                    }
                ],
            )

            # 2. Build list bullet creation requests
            bullet_reqs = []
            for start, end, preset in list_groups:
                bullet_reqs.append(
                    {
                        "createParagraphBullets": {
                            "range": {"startIndex": start, "endIndex": end},
                            "bulletPreset": preset,
                        }
                    }
                )

            # 3. Execute all styling updates
            formatting_reqs = p_style_reqs + bullet_reqs + text_style_reqs
            execute_batch(doc_id, formatting_reqs)

        elif seg_type == "table":
            rows_data = seg_data
            num_rows = len(rows_data)
            num_cols = len(rows_data[0])

            execute_batch(
                doc_id,
                [
                    {
                        "insertTable": {
                            "rows": num_rows,
                            "columns": num_cols,
                            "location": {"index": insert_pos},
                        }
                    }
                ],
            )

            doc = get_doc(doc_id)
            table = None
            table_start_index = None
            for el in reversed(doc["body"]["content"]):
                if "table" in el:
                    table = el["table"]
                    table_start_index = el["startIndex"]
                    break

            cell_spans_map = {}
            cell_bullet_map = set()
            insert_reqs = []

            if table and "tableRows" in table:
                for r_idx in range(num_rows - 1, -1, -1):
                    row = table["tableRows"][r_idx]
                    for c_idx in range(num_cols - 1, -1, -1):
                        cell = row["tableCells"][c_idx]
                        cell_start = cell["content"][0]["paragraph"]["elements"][0]["startIndex"]
                        raw_cell_text = rows_data[r_idx][c_idx]
                        clean_text, spans = extract_inline_formatting(raw_cell_text)
                        if spans:
                            cell_spans_map[(r_idx, c_idx)] = spans

                        # Check if cell has bullet points separated by • or ; •
                        if "• " in clean_text or "; •" in clean_text:
                            items = [
                                re.sub(r"^[•\-\*]\s*", "", part).strip()
                                for part in re.split(r";\s*•\s*|•\s*", clean_text)
                                if part.strip()
                            ]
                            if len(items) > 1 or (
                                len(items) == 1 and clean_text.strip().startswith("•")
                            ):
                                clean_text = "\n".join(items) + "\n"
                                cell_bullet_map.add((r_idx, c_idx))

                        if clean_text:
                            insert_reqs.append(
                                {
                                    "insertText": {
                                        "location": {"index": cell_start},
                                        "text": clean_text,
                                    }
                                }
                            )
            execute_batch(doc_id, insert_reqs)

            doc = get_doc(doc_id)
            for el in reversed(doc["body"]["content"]):
                if "table" in el:
                    table = el["table"]
                    table_start_index = el["startIndex"]
                    break

            # Remove trailing blank newlines from multi-paragraph cells
            if table and "tableRows" in table:
                cleanup_del_reqs = []
                for r_idx in range(len(table["tableRows"])):
                    for c_idx in range(len(table["tableRows"][r_idx]["tableCells"])):
                        cell = table["tableRows"][r_idx]["tableCells"][c_idx]
                        c_content = cell.get("content", [])
                        if len(c_content) > 1:
                            last_p = c_content[-1].get("paragraph", {})
                            last_text = "".join(
                                pe.get("textRun", {}).get("content", "")
                                for pe in last_p.get("elements", [])
                            )
                            if last_text == "\n":
                                prev_p = c_content[-2].get("paragraph", {})
                                e_prev = prev_p.get("elements", [{}])[-1].get("endIndex")
                                s_last = last_p.get("elements", [{}])[0].get("startIndex")
                                if e_prev is not None and s_last is not None:
                                    cleanup_del_reqs.append(
                                        {
                                            "startIndex": e_prev - 1,
                                            "endIndex": s_last,
                                        }
                                    )
                if cleanup_del_reqs:
                    cleanup_del_reqs.sort(key=lambda x: x["startIndex"], reverse=True)
                    execute_batch(
                        doc_id,
                        [
                            {
                                "deleteContentRange": {
                                    "range": {
                                        "startIndex": r["startIndex"],
                                        "endIndex": r["endIndex"],
                                    }
                                }
                            }
                            for r in cleanup_del_reqs
                        ],
                    )
                    doc = get_doc(doc_id)
                    for el in reversed(doc["body"]["content"]):
                        if "table" in el:
                            table = el["table"]
                            table_start_index = el["startIndex"]
                            break

            style_reqs = []
            if table and "tableRows" in table and len(table["tableRows"]) > 0:
                # 1. Header row background (#E8F0FE)
                style_reqs.append(
                    {
                        "updateTableCellStyle": {
                            "tableRange": {
                                "tableCellLocation": {
                                    "tableStartLocation": {"index": table_start_index},
                                    "rowIndex": 0,
                                    "columnIndex": 0,
                                },
                                "rowSpan": 1,
                                "columnSpan": num_cols,
                            },
                            "tableCellStyle": {
                                "backgroundColor": {
                                    "color": {
                                        "rgbColor": {
                                            "red": 0.91,
                                            "green": 0.94,
                                            "blue": 0.996,
                                        }
                                    }
                                }
                            },
                            "fields": "backgroundColor",
                        }
                    }
                )

                # 2. Table cell padding for all rows (top/bottom: 5 PT, left/right: 8 PT)
                style_reqs.append(
                    {
                        "updateTableCellStyle": {
                            "tableRange": {
                                "tableCellLocation": {
                                    "tableStartLocation": {"index": table_start_index},
                                    "rowIndex": 0,
                                    "columnIndex": 0,
                                },
                                "rowSpan": num_rows,
                                "columnSpan": num_cols,
                            },
                            "tableCellStyle": {
                                "paddingTop": {"magnitude": 5.0, "unit": "PT"},
                                "paddingBottom": {"magnitude": 5.0, "unit": "PT"},
                                "paddingLeft": {"magnitude": 8.0, "unit": "PT"},
                                "paddingRight": {"magnitude": 8.0, "unit": "PT"},
                            },
                            "fields": "paddingTop,paddingBottom,paddingLeft,paddingRight",
                        }
                    }
                )

                # 3. Header row text formatting (bold, 10.5 PT, navy blue text)
                header_row = table["tableRows"][0]
                for cell in header_row["tableCells"]:
                    cell_start = cell["content"][0]["paragraph"]["elements"][0]["startIndex"]
                    cell_end = cell["content"][0]["paragraph"]["elements"][-1]["endIndex"]
                    style_reqs.append(
                        {
                            "updateTextStyle": {
                                "range": {
                                    "startIndex": cell_start,
                                    "endIndex": cell_end,
                                },
                                "textStyle": {
                                    "bold": True,
                                    "fontSize": {"magnitude": 10.5, "unit": "PT"},
                                    "foregroundColor": {
                                        "color": {
                                            "rgbColor": {
                                                "red": 0.05,
                                                "green": 0.22,
                                                "blue": 0.45,
                                            }
                                        }
                                    },
                                },
                                "fields": "bold,fontSize,foregroundColor",
                            }
                        }
                    )

                # 4. Body rows text formatting (10.0 PT)
                for r_idx in range(1, num_rows):
                    row = table["tableRows"][r_idx]
                    for cell in row["tableCells"]:
                        cell_start = cell["content"][0]["paragraph"]["elements"][0]["startIndex"]
                        cell_end = cell["content"][0]["paragraph"]["elements"][-1]["endIndex"]
                        style_reqs.append(
                            {
                                "updateTextStyle": {
                                    "range": {
                                        "startIndex": cell_start,
                                        "endIndex": cell_end,
                                    },
                                    "textStyle": {"fontSize": {"magnitude": 10.0, "unit": "PT"}},
                                    "fields": "fontSize",
                                }
                            }
                        )

                # 5. Inline formatting inside table cells (bold, inline code, links)
                doc = get_doc(doc_id)
                for el in reversed(doc["body"]["content"]):
                    if "table" in el:
                        table = el["table"]
                        table_start_index = el["startIndex"]
                        break

                for (r_idx, c_idx), spans in cell_spans_map.items():
                    if r_idx < len(table["tableRows"]):
                        row = table["tableRows"][r_idx]
                        if c_idx < len(row["tableCells"]):
                            cell = row["tableCells"][c_idx]
                            cell_start = cell["content"][0]["paragraph"]["elements"][0][
                                "startIndex"
                            ]
                            for span in spans:
                                s_start = cell_start + span["start"]
                                s_end = cell_start + span["end"]
                                if s_end > s_start:
                                    style_reqs.append(
                                        {
                                            "updateTextStyle": {
                                                "range": {
                                                    "startIndex": s_start,
                                                    "endIndex": s_end,
                                                },
                                                "textStyle": span["textStyle"],
                                                "fields": span["fields"],
                                            }
                                        }
                                    )

                # 6. Apply native bullets to table cells that have multiple items
                for r_idx, c_idx in cell_bullet_map:
                    if r_idx < len(table["tableRows"]):
                        cell = table["tableRows"][r_idx]["tableCells"][c_idx]
                        p_ranges = []
                        for p_elem in cell.get("content", []):
                            p = p_elem.get("paragraph", {})
                            t_str = "".join(
                                pe.get("textRun", {}).get("content", "")
                                for pe in p.get("elements", [])
                            ).strip()
                            if t_str:
                                p_start = p.get("elements", [{}])[0].get("startIndex")
                                p_end = p.get("elements", [{}])[-1].get("endIndex")
                                if p_start is not None and p_end is not None:
                                    p_ranges.append((p_start, p_end))
                        if len(p_ranges) > 1:
                            style_reqs.append(
                                {
                                    "createParagraphBullets": {
                                        "range": {
                                            "startIndex": p_ranges[0][0],
                                            "endIndex": p_ranges[-1][1],
                                        },
                                        "bulletPreset": "BULLET_DISC_CIRCLE_SQUARE",
                                    }
                                }
                            )

                # 7. Stretch table columns to full width (850 pt) with balanced proportions
                headers = [c.strip() for c in rows_data[0]] if num_rows > 0 else []
                headers_lower = [h.lower() for h in headers]
                if num_cols == 3:
                    if any("risk" in h for h in headers_lower):
                        col_widths = [160.0, 210.0, 480.0]
                    elif any("horizon" in h for h in headers_lower):
                        col_widths = [140.0, 180.0, 530.0]
                    elif any("phase" in h for h in headers_lower) or any(
                        "vs" in h for h in headers_lower
                    ):
                        col_widths = [170.0, 340.0, 340.0]
                    elif any("dimension" in h for h in headers_lower) or any(
                        "branch" in h for h in headers_lower
                    ):
                        col_widths = [160.0, 180.0, 510.0]
                    else:
                        col_widths = [160.0, 330.0, 360.0]
                elif num_cols == 4:
                    if any("no" in h for h in headers_lower) or any(
                        "text" in h for h in headers_lower
                    ):
                        col_widths = [40.0, 190.0, 240.0, 380.0]
                    else:
                        col_widths = [130.0, 150.0, 115.0, 455.0]
                elif num_cols == 5:
                    if any("objective" in h for h in headers_lower) or any(
                        "kpi" in h for h in headers_lower
                    ):
                        col_widths = [125.0, 165.0, 180.0, 180.0, 200.0]
                    elif any(
                        "functional specification" in h and "non-functional" not in h
                        for h in headers_lower
                    ):
                        col_widths = [55.0, 135.0, 105.0, 365.0, 190.0]
                    elif any("req id" in h for h in headers_lower):
                        col_widths = [85.0, 135.0, 105.0, 340.0, 185.0]
                    elif any("baseline" in h for h in headers_lower) and any(
                        "target" in h for h in headers_lower
                    ):
                        col_widths = [110.0, 175.0, 265.0, 90.0, 210.0]
                    else:
                        w = round(850.0 / 5, 1)
                        col_widths = [w] * 5
                elif num_cols == 6:
                    if any("step" in h for h in headers_lower) and any(
                        "stage" in h for h in headers_lower
                    ):
                        col_widths = [50.0, 130.0, 110.0, 110.0, 250.0, 200.0]
                    else:
                        w = round(850.0 / 6, 1)
                        col_widths = [w] * 6
                else:
                    w = round(850.0 / num_cols, 1)
                    col_widths = [w] * num_cols

                for c_idx, width in enumerate(col_widths):
                    style_reqs.append(
                        {
                            "updateTableColumnProperties": {
                                "tableStartLocation": {"index": table_start_index},
                                "columnIndices": [c_idx],
                                "tableColumnProperties": {
                                    "widthType": "FIXED_WIDTH",
                                    "width": {"magnitude": width, "unit": "PT"},
                                },
                                "fields": "widthType,width",
                            }
                        }
                    )

                execute_batch(doc_id, style_reqs)


def format_text_run(element, in_code_block=False):
    tr = element.get("textRun")
    if not tr:
        return ""
    content = tr.get("content", "")
    if not content:
        return ""
    if in_code_block:
        return content

    style = tr.get("textStyle", {})
    bold = style.get("bold", False)
    italic = style.get("italic", False)
    strikethrough = style.get("strikethrough", False)
    link = style.get("link", {}).get("url")
    font = style.get("weightedFontFamily", {}).get("fontFamily", "")
    is_code = font in (
        "Consolas",
        "Roboto Mono",
        "Courier New",
    )

    match = re.match(r"^(\s*)(.*?)(\s*)$", content, re.DOTALL)
    if not match:
        return content

    lead_ws, core_text, trail_ws = match.groups()
    if not core_text:
        return content

    if is_code:
        core_text = f"`{core_text}`"
    if bold:
        core_text = f"**{core_text}**"
    if italic:
        core_text = f"*{core_text}*"
    if strikethrough:
        core_text = f"~~{core_text}~~"
    if link:
        core_text = f"[{core_text}]({link})"

    return f"{lead_ws}{core_text}{trail_ws}"


def read_doc(doc_id):
    """
    Reads a Google Doc and converts it back into Markdown AST representation.
      - Preserves code blocks (fenced with ```text ... ```)
      - Preserves monospace runs as inline `code`
      - Preserves hyperlinks as [text](url)
      - Preserves headings, bullets, numbered lists, checklists, tables
    """
    doc = get_doc(doc_id)

    def process_content(content):
        text = ""
        in_code_block = False
        code_lines = []

        def flush_code():
            nonlocal in_code_block, code_lines, text
            if in_code_block:
                text += "```text\n" + "\n".join(code_lines) + "\n```\n\n"
                in_code_block = False
                code_lines = []

        for el in content:
            if "paragraph" in el:
                p = el["paragraph"]
                p_style = p.get("paragraphStyle", {})
                is_code = bool(
                    p_style.get("shading", {}).get("backgroundColor")
                    and p_style.get("borderLeft")
                )

                if is_code:
                    in_code_block = True
                    raw_line = "".join(
                        pe.get("textRun", {}).get("content", "") for pe in p.get("elements", [])
                    ).rstrip("\r\n")
                    code_lines.append(raw_line)
                    continue
                else:
                    flush_code()

                p_text = "".join(format_text_run(pe) for pe in p.get("elements", []))
                named_style = p_style.get("namedStyleType", "")
                clean_p_text = p_text.strip()
                if not clean_p_text:
                    continue

                if "TITLE" in named_style:
                    text += f"# {clean_p_text}\n\n"
                elif "HEADING_1" in named_style:
                    text += f"## {clean_p_text}\n\n"
                elif "HEADING_2" in named_style:
                    text += f"### {clean_p_text}\n\n"
                elif "HEADING_3" in named_style:
                    text += f"#### {clean_p_text}\n\n"
                elif "HEADING_4" in named_style:
                    text += f"##### {clean_p_text}\n\n"
                elif "SUBTITLE" in named_style:
                    text += f"*{clean_p_text}*\n\n"
                elif "bullet" in p:
                    nesting = p.get("bullet", {}).get("nestingLevel", 0)
                    indent = "  " * nesting
                    lid = p.get("bullet", {}).get("listId", "")
                    nls = (
                        doc.get("lists", {})
                        .get(lid, {})
                        .get("listProperties", {})
                        .get("nestingLevels", [{}])
                    )
                    nl = nls[nesting] if nesting < len(nls) else (nls[0] if nls else {})
                    gt = nl.get("glyphType")
                    gs = nl.get("glyphSymbol")
                    if gs in ("\u25a1", "□"):
                        text += f"{indent}- [ ] {clean_p_text}\n"
                    elif gt and gt != "GLYPH_TYPE_UNSPECIFIED":
                        text += f"{indent}1. {clean_p_text}\n"
                    else:
                        text += f"{indent}- {clean_p_text}\n"
                elif p_style.get("borderBottom"):
                    text += "---\n\n"
                else:
                    text += f"{clean_p_text}\n\n"
            elif "table" in el:
                flush_code()
                table = el["table"]
                rows = table.get("tableRows", [])
                for r_idx, row in enumerate(rows):
                    row_cells = []
                    for cell in row.get("tableCells", []):
                        cell_p = cell.get("content", [{}])[0].get("paragraph", {})
                        cell_text = (
                            "".join(format_text_run(pe) for pe in cell_p.get("elements", []))
                            .strip()
                            .replace("\n", " ")
                        )
                        row_cells.append(cell_text)
                    text += "| " + " | ".join(row_cells) + " |\n"
                    if r_idx == 0:
                        text += "| " + " | ".join(["---"] * len(row_cells)) + " |\n"
                text += "\n"

        flush_code()
        return text.strip()

    tabs = doc.get("tabs", [])
    if tabs:
        full_out = []
        for tab in tabs:
            tab_title = tab.get("tabProperties", {}).get("title", "Tab")
            tab_content = tab.get("documentTab", {}).get("body", {}).get("content", [])
            tab_md = process_content(tab_content)
            full_out.append(f"<!-- TAB: {tab_title} -->\n\n{tab_md}")
        return "\n\n---\n\n".join(full_out)
    else:
        body_content = doc.get("body", {}).get("content", [])
        return process_content(body_content)


def main():
    parser = argparse.ArgumentParser(
        description="Google Docs Markdown Renderer & Document Manager"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # create
    create_p = subparsers.add_parser("create", help="Create a new Google Doc")
    create_p.add_argument("title", help="Title of the document")

    # render
    render_p = subparsers.add_parser("render", help="Render markdown into a Google Doc")
    render_p.add_argument("doc_id", help="Target Google Document ID")
    render_p.add_argument(
        "file", nargs="?", default="-", help="Markdown file path or '-' for stdin"
    )
    render_p.add_argument(
        "--append", action="store_true", help="Append instead of clearing document"
    )

    # parse (AST dump)
    parse_p = subparsers.add_parser("parse", help="Parse markdown and output AST segments JSON")
    parse_p.add_argument(
        "file", nargs="?", default="-", help="Markdown file path or '-' for stdin"
    )

    # read
    read_p = subparsers.add_parser("read", help="Read and convert a Google Doc to Markdown")
    read_p.add_argument("doc_id", help="Google Document ID")

    # clear
    clear_p = subparsers.add_parser("clear", help="Clear document content")
    clear_p.add_argument("doc_id", help="Google Document ID")

    args = parser.parse_args()

    if args.command == "create":
        create_doc(args.title)
    elif args.command == "render":
        if args.file == "-":
            md_text = sys.stdin.read()
        else:
            try:
                with open(args.file) as f:
                    md_text = f.read()
            except OSError as err:
                print(f"[gdocs] Error reading file {args.file}: {err}", file=sys.stderr)
                sys.exit(1)
        render_markdown(args.doc_id, md_text, clear=not args.append)
        print(
            f"Successfully rendered markdown to https://docs.google.com/document/d/{args.doc_id}/edit"
        )
    elif args.command == "parse":
        if args.file == "-":
            md_text = sys.stdin.read()
        else:
            try:
                with open(args.file) as f:
                    md_text = f.read()
            except OSError as err:
                print(f"[gdocs] Error reading file {args.file}: {err}", file=sys.stderr)
                sys.exit(1)
        segments = parse_markdown_to_segments(md_text)
        print(json.dumps(segments, indent=2))
    elif args.command == "read":
        print(read_doc(args.doc_id))
    elif args.command == "clear":
        clear_doc(args.doc_id)


if __name__ == "__main__":
    main()
