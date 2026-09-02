#!/usr/bin/env python3
"""
gdocs_builder.py — Robust Markdown to Google Docs Renderer & Document Manager
Uses Google Workspace CLI (gws) with Google Docs API batchUpdate.
"""

import argparse
import json
import re
import subprocess
import sys
import time

def get_doc(doc_id):
    for attempt in range(5):
        cmd = ['gws', 'docs', 'documents', 'get', '--params', json.dumps({"documentId": doc_id})]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            try:
                return json.loads(res.stdout)
            except json.JSONDecodeError as err:
                print(f"[gdocs] JSON parse error: {err}", file=sys.stderr)
                sys.exit(1)
        elif "429" in res.stderr or "Quota exceeded" in res.stderr:
            wait_time = (attempt + 1) * 10
            print(f"[gdocs] Rate limit encountered, waiting {wait_time}s...", file=sys.stderr)
            time.sleep(wait_time)
        else:
            print(f"[gdocs] Error fetching doc {doc_id}: {res.stderr}", file=sys.stderr)
            sys.exit(1)
    raise Exception("Failed to get_doc after retries")

def execute_batch(doc_id, requests):
    if not requests:
        return {}
    body = {"requests": requests}
    cmd = [
        'gws', 'docs', 'documents', 'batchUpdate',
        '--params', json.dumps({"documentId": doc_id}),
        '--json', json.dumps(body)
    ]
    for attempt in range(8):
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            try:
                return json.loads(res.stdout)
            except json.JSONDecodeError as err:
                print(f"[gdocs] JSON parse error during batchUpdate: {err}", file=sys.stderr)
                return {}
        elif "429" in res.stderr or "Quota exceeded" in res.stderr:
            wait_time = (attempt + 1) * 15
            print(f"[gdocs] Rate limit encountered during batchUpdate, waiting {wait_time}s...", file=sys.stderr)
            time.sleep(wait_time)
        else:
            print(f"[gdocs] Error during batchUpdate: {res.stderr}\n{res.stdout}", file=sys.stderr)
            raise Exception(f"batchUpdate failed: {res.stderr}")
    raise Exception("Failed execute_batch after retries")

def create_doc(title):
    cmd = [
        'gws', 'docs', 'documents', 'create',
        '--json', json.dumps({"title": title})
    ]
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
    end_idx = doc['body']['content'][-1]['endIndex']
    if end_idx > 2:
        execute_batch(doc_id, [{
            "deleteContentRange": {
                "range": {"startIndex": 1, "endIndex": end_idx - 1}
            }
        }])
        print(f"[gdocs] Cleared doc {doc_id}")

def parse_markdown_to_segments(md_text):
    lines = md_text.strip().split('\n')
    elements = []
    in_table = False
    table_rows = []
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
            
        if stripped.startswith('|') and stripped.endswith('|'):
            # Ignore separator row like |---|---|
            clean_check = stripped.replace('|', '').replace('-', '').replace(':', '').strip()
            if not clean_check:
                continue
            cells = [c.strip() for c in stripped[1:-1].split('|')]
            table_rows.append(cells)
            in_table = True
            continue
        else:
            if in_table and table_rows:
                elements.append({'type': 'table', 'rows': table_rows})
                table_rows = []
                in_table = False
                
        if stripped.startswith('# '):
            elements.append({'type': 'heading_1', 'text': stripped[2:].strip()})
        elif stripped.startswith('## '):
            elements.append({'type': 'heading_2', 'text': stripped[3:].strip()})
        elif stripped.startswith('### '):
            elements.append({'type': 'heading_3', 'text': stripped[4:].strip()})
        elif stripped.startswith('- '):
            elements.append({'type': 'bullet', 'text': stripped[2:].strip()})
        elif stripped.startswith('*') and stripped.endswith('*') and not stripped.startswith('**'):
            elements.append({'type': 'italic_para', 'text': stripped[1:-1].strip()})
        else:
            elements.append({'type': 'paragraph', 'text': stripped})
            
    if in_table and table_rows:
        elements.append({'type': 'table', 'rows': table_rows})
        
    return elements

def extract_formatting(raw_text):
    """
    Extracts **bold** markers and returns clean text plus relative bold character ranges.
    """
    bold_ranges = []
    clean_text = ""
    pattern = re.compile(r'\*\*(.*?)\*\*')
    last_end = 0
    
    for m in pattern.finditer(raw_text):
        clean_text += raw_text[last_end:m.start()]
        b_start = len(clean_text)
        bold_content = m.group(1)
        clean_text += bold_content
        b_end = len(clean_text)
        bold_ranges.append((b_start, b_end))
        last_end = m.end()
        
    clean_text += raw_text[last_end:]
    return clean_text, bold_ranges

def render_markdown(doc_id, md_text, clear=True):
    if clear:
        clear_doc(doc_id)
            
    elements = parse_markdown_to_segments(md_text)
    
    # Split elements into segments by table
    segments = []
    current_seg = []
    for el in elements:
        if el['type'] == 'table':
            if current_seg:
                segments.append(('text', current_seg))
                current_seg = []
            segments.append(('table', el['rows']))
        else:
            current_seg.append(el)
    if current_seg:
        segments.append(('text', current_seg))
        
    for seg_idx, (seg_type, seg_data) in enumerate(segments):
        doc = get_doc(doc_id)
        end_idx = doc['body']['content'][-1]['endIndex']
        insert_pos = end_idx - 1
        
        if seg_type == 'text':
            full_text = ""
            paragraph_styles = [] # (start, end, style)
            bullets = []          # (start, end)
            bold_ranges = []      # (start, end)
            italic_ranges = []    # (start, end)
            color_ranges = []     # (start, end, color)
            font_size_ranges = [] # (start, end, size)
            
            for el_idx, el in enumerate(seg_data):
                clean_text, b_ranges = extract_formatting(el['text'])
                clean_text = clean_text.strip('\r\n') + '\n'
                
                p_start = insert_pos + len(full_text)
                full_text += clean_text
                p_end = insert_pos + len(full_text)
                
                if el['type'] == 'heading_1':
                    if seg_idx == 0 and el_idx == 0:
                        paragraph_styles.append((p_start, p_end, 'TITLE'))
                    else:
                        paragraph_styles.append((p_start, p_end, 'HEADING_1'))
                elif el['type'] == 'heading_2':
                    if seg_idx == 0 and el_idx == 1:
                        paragraph_styles.append((p_start, p_end, 'SUBTITLE'))
                    else:
                        paragraph_styles.append((p_start, p_end, 'HEADING_2'))
                elif el['type'] == 'heading_3':
                    paragraph_styles.append((p_start, p_end, 'HEADING_3'))
                elif el['type'] == 'bullet':
                    bullets.append((p_start, p_end))
                elif el['type'] == 'italic_para':
                    italic_ranges.append((p_start, p_end))
                    color_ranges.append((p_start, p_end, {"red": 0.4, "green": 0.4, "blue": 0.4}))
                    font_size_ranges.append((p_start, p_end, 10.0))
                    
                for b_s, b_e in b_ranges:
                    bold_ranges.append((p_start + b_s, p_start + b_e))
                    
            # 1. Insert Text
            execute_batch(doc_id, [{
                "insertText": {
                    "location": {"index": insert_pos},
                    "text": full_text
                }
            }])
            
            # 2. Apply formatting
            reqs = []
            for s, e, st in paragraph_styles:
                reqs.append({
                    "updateParagraphStyle": {
                        "range": {"startIndex": s, "endIndex": e},
                        "paragraphStyle": {"namedStyleType": st},
                        "fields": "namedStyleType"
                    }
                })
            for s, e in bullets:
                reqs.append({
                    "createParagraphBullets": {
                        "range": {"startIndex": s, "endIndex": e},
                        "bulletPreset": "BULLET_DISC_CIRCLE_SQUARE"
                    }
                })
            for s, e in italic_ranges:
                reqs.append({
                    "updateTextStyle": {
                        "range": {"startIndex": s, "endIndex": e},
                        "textStyle": {"italic": True},
                        "fields": "italic"
                    }
                })
            for s, e, col in color_ranges:
                reqs.append({
                    "updateTextStyle": {
                        "range": {"startIndex": s, "endIndex": e},
                        "textStyle": {"foregroundColor": {"color": {"rgbColor": col}}},
                        "fields": "foregroundColor"
                    }
                })
            for s, e, sz in font_size_ranges:
                reqs.append({
                    "updateTextStyle": {
                        "range": {"startIndex": s, "endIndex": e},
                        "textStyle": {"fontSize": {"magnitude": sz, "unit": "PT"}},
                        "fields": "fontSize"
                    }
                })
            for s, e in bold_ranges:
                reqs.append({
                    "updateTextStyle": {
                        "range": {"startIndex": s, "endIndex": e},
                        "textStyle": {"bold": True},
                        "fields": "bold"
                    }
                })
            execute_batch(doc_id, reqs)
            
        elif seg_type == 'table':
            rows_data = seg_data
            num_rows = len(rows_data)
            num_cols = len(rows_data[0])
            
            execute_batch(doc_id, [{
                "insertTable": {
                    "rows": num_rows,
                    "columns": num_cols,
                    "location": {"index": insert_pos}
                }
            }])
            
            doc = get_doc(doc_id)
            table = None
            table_start_index = None
            for el in reversed(doc['body']['content']):
                if 'table' in el:
                    table = el['table']
                    table_start_index = el['startIndex']
                    break
                    
            insert_reqs = []
            if table and 'tableRows' in table:
                for r_idx in range(num_rows - 1, -1, -1):
                    row = table['tableRows'][r_idx]
                    for c_idx in range(num_cols - 1, -1, -1):
                        cell = row['tableCells'][c_idx]
                        cell_start = cell['content'][0]['paragraph']['elements'][0]['startIndex']
                        text_to_insert = rows_data[r_idx][c_idx]
                        insert_reqs.append({
                            "insertText": {
                                "location": {"index": cell_start},
                                "text": text_to_insert
                            }
                        })
            execute_batch(doc_id, insert_reqs)
            
            doc = get_doc(doc_id)
            for el in reversed(doc['body']['content']):
                if 'table' in el:
                    table = el['table']
                    table_start_index = el['startIndex']
                    break
                    
            style_reqs = []
            if table and 'tableRows' in table and len(table['tableRows']) > 0:
                header_row = table['tableRows'][0]
                for c_idx, cell in enumerate(header_row['tableCells']):
                    cell_start = cell['content'][0]['paragraph']['elements'][0]['startIndex']
                    cell_end = cell['content'][0]['paragraph']['elements'][-1]['endIndex']
                    style_reqs.append({
                        "updateTextStyle": {
                            "range": {"startIndex": cell_start, "endIndex": cell_end},
                            "textStyle": {
                                "bold": True,
                                "fontSize": {"magnitude": 9.5, "unit": "PT"},
                                "foregroundColor": {"color": {"rgbColor": {"red": 0.08, "green": 0.2, "blue": 0.45}}}
                            },
                            "fields": "bold,fontSize,foregroundColor"
                        }
                    })
                
                style_reqs.append({
                    "updateTableCellStyle": {
                        "tableRange": {
                            "tableCellLocation": {
                                "tableStartLocation": {"index": table_start_index},
                                "rowIndex": 0,
                                "columnIndex": 0
                            },
                            "rowSpan": 1,
                            "columnSpan": num_cols
                        },
                        "tableCellStyle": {
                            "backgroundColor": {
                                "color": {"rgbColor": {"red": 0.92, "green": 0.95, "blue": 0.99}}
                            }
                        },
                        "fields": "backgroundColor"
                    }
                })
                
                for r_idx in range(1, num_rows):
                    row = table['tableRows'][r_idx]
                    for c_idx in range(num_cols):
                        cell = row['tableCells'][c_idx]
                        cell_start = cell['content'][0]['paragraph']['elements'][0]['startIndex']
                        cell_end = cell['content'][0]['paragraph']['elements'][-1]['endIndex']
                        style_reqs.append({
                            "updateTextStyle": {
                                "range": {"startIndex": cell_start, "endIndex": cell_end},
                                "textStyle": {
                                    "fontSize": {"magnitude": 9.0, "unit": "PT"}
                                },
                                "fields": "fontSize"
                            }
                        })
            execute_batch(doc_id, style_reqs)

def format_text_run(element):
    tr = element.get('textRun')
    if not tr:
        return ""
    content = tr.get('content', '')
    if not content:
        return ""
        
    style = tr.get('textStyle', {})
    bold = style.get('bold', False)
    italic = style.get('italic', False)
    link = style.get('link', {}).get('url')
    
    match = re.match(r'^(\s*)(.*?)(\s*)$', content, re.DOTALL)
    if not match:
        return content
        
    lead_ws, core_text, trail_ws = match.groups()
    if not core_text:
        return content
        
    if link:
        core_text = f"[{core_text}]({link})"
    if bold:
        core_text = f"**{core_text}**"
    if italic:
        core_text = f"*{core_text}*"
        
    return f"{lead_ws}{core_text}{trail_ws}"

def read_doc(doc_id):
    doc = get_doc(doc_id)
    
    def process_content(content):
        text = ""
        for el in content:
            if 'paragraph' in el:
                p = el['paragraph']
                p_text = "".join([format_text_run(pe) for pe in p.get('elements', [])])
                named_style = p.get('paragraphStyle', {}).get('namedStyleType', '')
                
                clean_p_text = p_text.strip()
                if not clean_p_text:
                    continue
                    
                if 'HEADING_1' in named_style:
                    text += f"\n# {clean_p_text}\n"
                elif 'HEADING_2' in named_style:
                    text += f"\n## {clean_p_text}\n"
                elif 'HEADING_3' in named_style:
                    text += f"\n### {clean_p_text}\n"
                elif 'TITLE' in named_style:
                    text += f"\n# {clean_p_text}\n"
                elif 'SUBTITLE' in named_style:
                    text += f"\n*{clean_p_text}*\n"
                elif 'bullet' in p:
                    nesting = p.get('bullet', {}).get('nestingLevel', 0)
                    indent = "  " * nesting
                    text += f"{indent}- {clean_p_text}\n"
                else:
                    text += f"{clean_p_text}\n\n"
            elif 'table' in el:
                table = el['table']
                text += "\n"
                rows = table.get('tableRows', [])
                for r_idx, row in enumerate(rows):
                    row_cells = []
                    for cell in row.get('tableCells', []):
                        cell_text = "".join([
                            format_text_run(pe)
                            for pe in cell.get('content', [{}])[0].get('paragraph', {}).get('elements', [])
                        ]).strip().replace('\n', ' ')
                        row_cells.append(cell_text)
                    text += "| " + " | ".join(row_cells) + " |\n"
                    # Add separator after header row
                    if r_idx == 0:
                        sep = ["---"] * len(row_cells)
                        text += "| " + " | ".join(sep) + " |\n"
                text += "\n"
        return text.strip()

    tabs = doc.get('tabs', [])
    if tabs:
        full_out = []
        for tab in tabs:
            tab_title = tab.get('tabProperties', {}).get('title', 'Tab')
            tab_content = tab.get('documentTab', {}).get('body', {}).get('content', [])
            tab_md = process_content(tab_content)
            full_out.append(f"<!-- TAB: {tab_title} -->\n\n{tab_md}")
        return "\n\n---\n\n".join(full_out)
    else:
        body_content = doc.get('body', {}).get('content', [])
        return process_content(body_content)

def main():
    parser = argparse.ArgumentParser(description="Google Docs Markdown Renderer & Document Manager")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # create
    create_p = subparsers.add_parser("create", help="Create a new Google Doc")
    create_p.add_argument("title", help="Title of the document")
    
    # render
    render_p = subparsers.add_parser("render", help="Render markdown into a Google Doc")
    render_p.add_argument("doc_id", help="Target Google Document ID")
    render_p.add_argument("file", nargs="?", default="-", help="Markdown file path or '-' for stdin")
    render_p.add_argument("--append", action="store_true", help="Append instead of clearing document")
    
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
                with open(args.file, "r") as f:
                    md_text = f.read()
            except (IOError, OSError) as err:
                print(f"[gdocs] Error reading file {args.file}: {err}", file=sys.stderr)
                sys.exit(1)
        render_markdown(args.doc_id, md_text, clear=not args.append)
        print(f"Successfully rendered markdown to https://docs.google.com/document/d/{args.doc_id}/edit")
    elif args.command == "read":
        print(read_doc(args.doc_id))
    elif args.command == "clear":
        clear_doc(args.doc_id)

if __name__ == "__main__":
    main()
