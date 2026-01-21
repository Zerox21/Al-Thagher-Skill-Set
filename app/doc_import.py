from __future__ import annotations
import os, re, json
from dataclasses import dataclass
from typing import List, Tuple, Optional

@dataclass
class ImportedQuestion:
    prompt: str
    meta_json: str | None
    qtype: str

def split_docx_text_to_questions(text: str) -> List[str]:
    # split on patterns like "1)" "1." "1-" including Arabic digits
    # Normalize line endings
    lines = [ln.strip() for ln in text.splitlines()]
    # Combine into a single string with 

    s = "\n".join([ln for ln in lines if ln])
    # Insert marker before question numbers
    pat = r"(?:^|\n)\s*([0-9٠-٩]{1,3})\s*[\)\.\-]\s+"
    parts = re.split(pat, s)
    if len(parts) <= 1:
        return [s] if s.strip() else []
    # parts structure: [prefix, num1, rest1, num2, rest2,...]
    out = []
    i = 1
    while i < len(parts):
        num = parts[i]
        body = parts[i+1] if i+1 < len(parts) else ""
        q = f"{num}) {body}".strip()
        if q:
            out.append(q)
        i += 2
    return out

def render_pdf_pages_to_images(pdf_path: str, out_dir: str, prefix: str) -> List[str]:
    """Return list of saved PNG filenames (relative to out_dir base)."""
    import fitz  # PyMuPDF
    os.makedirs(out_dir, exist_ok=True)
    doc = fitz.open(pdf_path)
    out_files = []
    for i in range(len(doc)):
        page = doc[i]
        mat = fitz.Matrix(2, 2)  # 2x for clarity
        pix = page.get_pixmap(matrix=mat, alpha=False)
        fname = f"{prefix}_p{i+1}.png"
        fpath = os.path.join(out_dir, fname)
        pix.save(fpath)
        out_files.append(fname)
    doc.close()
    return out_files
