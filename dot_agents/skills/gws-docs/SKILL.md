---
name: gws-docs
description: Manages bidirectional conversion between Markdown and Google Docs via gws and the Google Docs REST API. Creates documents, renders Markdown into styled Google Docs (headings, tables, code blocks, lists, inline formatting), and parses Google Docs (including multi-tab docs) back into Markdown. Use when reading, creating, formatting, or updating Google Docs.
---

# Google Docs Bidirectional Markdown Skill (`gws-docs`)

## Overview

`gws-docs` converts between **Markdown** and **Google Docs** via the `gws` CLI and the Google Docs REST API (`batchUpdate` / `get`), handling rate-limit retries (`429 Quota Exceeded`), request chunking, and multi-tab documents.

**Required CLI dependencies:** `python3`, `gws` (authenticated with Google Docs API scope).

---

## Utility Script (`gdocs_builder.py`)

Run `~/.agents/skills/gws-docs/gdocs_builder.py` directly (do not load the script into context unless debugging AST conversion logic).

### 1. Read & Parse a Google Doc to Markdown

```bash
python3 ~/.agents/skills/gws-docs/gdocs_builder.py read <DOCUMENT_ID>
```

Outputs clean Markdown preserving headings, bold/italic/strikethrough/code spans, hyperlinks, nested lists, and tables (including `<!-- TAB: ... -->` dividers for multi-tab documents).

### 2. Validate Markdown AST Before Rendering (`parse`)

```bash
python3 ~/.agents/skills/gws-docs/gdocs_builder.py parse /path/to/content.md
```

Outputs the parsed AST segment JSON without modifying any remote Google Doc.

### 3. Render Markdown into a Google Doc (`render`)

Replaces document content by default, or appends when `--append` is passed:

```bash
# Replace existing document content with rendered Markdown
python3 ~/.agents/skills/gws-docs/gdocs_builder.py render <DOCUMENT_ID> /path/to/content.md

# Append rendered Markdown to the end of the document
python3 ~/.agents/skills/gws-docs/gdocs_builder.py render <DOCUMENT_ID> /path/to/content.md --append
```

Or stream Markdown via `stdin` (`-`):

```bash
cat << 'EOF' | python3 ~/.agents/skills/gws-docs/gdocs_builder.py render <DOCUMENT_ID> -
# Document Title
## Document Subtitle
*Status: Draft*

# 1. Section
- **Key finding:** Supporting detail with `inline_code` and [link](https://example.com)

| Column 1 | Column 2 |
| :--- | :--- |
| Value A | Value B |
EOF
```

### 4. Create a New Google Doc (`create`)

```bash
python3 ~/.agents/skills/gws-docs/gdocs_builder.py create "Document Title"
```

### 5. Clear a Google Doc (`clear`)

```bash
python3 ~/.agents/skills/gws-docs/gdocs_builder.py clear <DOCUMENT_ID>
```

---

## Validation Feedback Loop for Document Updates

When publishing or updating an important Google Doc, follow this plan-validate-execute loop:

```text
Document Update Progress:
- [ ] Step 1: Write Markdown draft to tmp/draft.md
- [ ] Step 2: Validate AST structure locally (run gdocs_builder.py parse tmp/draft.md)
- [ ] Step 3: Render into target Google Doc (run gdocs_builder.py render <DOC_ID> tmp/draft.md)
- [ ] Step 4: Read back and verify structure (run gdocs_builder.py read <DOC_ID>)
```

If Step 2 or Step 4 reveals malformed tables, unclosed code fences, or unintended heading levels, fix `tmp/draft.md` and re-run `render`.

---

## Supported Syntax & Styling Matrix

| Markdown Element                                 | Google Doc Element              | Visual Style / Attributes                                        |
| :----------------------------------------------- | :------------------------------ | :--------------------------------------------------------------- |
| First `# Line`                                   | Document `TITLE`                | 26pt font, bold                                                  |
| First `## Line`                                  | Document `SUBTITLE`             | 15pt font, gray subtitle                                         |
| `To:` / `From:` / `Case ID:` / `*Italic*` header | Metadata Block                  | Compact spacing, 10pt gray/bold-key metadata                     |
| `# Section` .. `#### Subtopic`                   | `HEADING_1` .. `HEADING_4`      | 20pt / 16pt / 14pt / 12pt section headers                        |
| `- item` / `1. item` / `- [x] item`              | Bulleted / Numbered / Checklist | Nested list indentation and inline styles                        |
| ` ```lang ... ``` `                              | Fenced Code Block               | `Consolas` monospace, shaded box, left accent border             |
| `> quote`                                        | Blockquote                      | Indented italic paragraph with left border                       |
| `---`                                            | Horizontal Rule                 | Bottom paragraph border                                          |
| `\| Col 1 \| Col 2 \|`                           | Native `Table`                  | `#E8F0FE` header shading, bold dark-blue header text, 9.5pt font |
