---
name: gws-docs
description: Bidirectional Google Docs manager. Create, format, render Markdown into Google Docs, and read/parse Google Docs back into Markdown with accurate headings, tables, bullets, and inline styles.
---

# Google Docs Bidirectional Markdown Skill (`gws-docs`)

## Overview

The `gws-docs` skill provides complete bidirectional workflows between **Markdown** and **Google Docs** via `gws` and the Google Docs API:

1. **Markdown $\rightarrow$ Google Docs Renderer:** Converts standard Markdown into Google Docs API `batchUpdate` requests (Titles, Subtitles, Headings 1–3, Bullet Lists, and Styled Tables with `#E8F0FE` header backgrounds).
2. **Google Docs $\rightarrow$ Markdown Parser:** Reads any Google Doc (including multi-tab documents) and extracts clean, readable Markdown preserving headings, bolding, italics, hyperlinks, bullet nesting, and tables.
3. **Zero Formatting Defects:** Prevents accidental empty headings, stray blank bullet points, and index shifting errors.
4. **Resilient Rate-Limit Handling:** Automatically retries with exponential backoff on `429 Quota Exceeded` errors.

---

## CLI Utility (`gdocs_builder.py`)

Executable script location:
`/usr/local/google/home/ervinadrian/.agents/skills/gws-docs/gdocs_builder.py`

### 1. Read & Parse Google Doc to Markdown

```bash
python3 /usr/local/google/home/ervinadrian/.agents/skills/gws-docs/gdocs_builder.py read <DOCUMENT_ID>
```

*Outputs clean Markdown with `# Headings`, `**bold**`, `*italics*`, `[hyperlinks](url)`, `- bullets`, and `| markdown | tables |`.*

### 2. Render Markdown to Google Doc (Full Formatting)

```bash
python3 /usr/local/google/home/ervinadrian/.agents/skills/gws-docs/gdocs_builder.py render <DOCUMENT_ID> /path/to/content.md
```

Or via pipeline stdin:

```bash
cat << 'EOF' | python3 /usr/local/google/home/ervinadrian/.agents/skills/gws-docs/gdocs_builder.py render <DOCUMENT_ID> -
# Document Title
## Document Subtitle
*Scope: ...*

# 1. Section
- **Point 1:** Details
- **Point 2:** Details

| Col 1 | Col 2 |
| A | B |
EOF
```

### 3. Create a New Document

```bash
python3 /usr/local/google/home/ervinadrian/.agents/skills/gws-docs/gdocs_builder.py create "Document Title"
```

### 4. Clear a Document

```bash
python3 /usr/local/google/home/ervinadrian/.agents/skills/gws-docs/gdocs_builder.py clear <DOCUMENT_ID>
```

---

## Supported Syntax & Styling Matrix

| Markdown Element | Google Doc Element | Visual Style / Attributes |
| :--- | :--- | :--- |
| First `# Line` | Document `TITLE` | 26pt font, bold |
| First `## Line` | Document `SUBTITLE` | 15pt font, gray subtitle |
| `*Italic text*` line | Metadata Block | 10pt font, italic, #666666 gray |
| `# Section` | `HEADING_1` | 20pt section header |
| `## Subsection` | `HEADING_2` | 16pt subsection header |
| `### Topic` | `HEADING_3` | 14pt topic header |
| `- **Prefix:** Text` | Bulleted Paragraph | Bullet disc, prefix is **bolded** |
| `\| Col 1 \| Col 2 \|` | Native `Table` | Header row has `#E8F0FE` background, bold dark blue text, 9.5pt font |
