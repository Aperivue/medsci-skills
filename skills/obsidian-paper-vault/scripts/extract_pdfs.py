"""
Extract text from a folder of PDFs using PyMuPDF.

Usage:
    python extract_pdfs.py <pdf_folder> <output_folder> [max_pages]

Default max_pages: 12 (covers abstract + intro + methods + results + discussion
for most research papers).

Output: One .txt file per PDF in the output folder, with page breaks marked by
'===PAGE BREAK==='.

A PDF whose extracted pages contain no text at all (an image-only scan) is
reported as 'FAILED <name>: no extractable text ... (needs OCR)', is not
counted as extracted, and gets no .txt file: an empty text file handed to a
note-writing subagent is the condition under which it invents a note.

max_pages must be an integer >= 1; anything else exits 2 naming the value.
"""

import fitz  # PyMuPDF
import sys
import os


def extract_pdf_pages(pdf_path, output_dir, max_pages=12):
    """Extract text from the first max_pages of a PDF to a .txt file."""
    if not os.path.exists(pdf_path):
        print(f"ERROR: PDF not found at {pdf_path}")
        return False

    filename = os.path.basename(pdf_path)
    base_name = os.path.splitext(filename)[0]
    out_path = os.path.join(output_dir, f"{base_name}.txt")

    try:
        doc = fitz.open(pdf_path)
        num_pages = min(len(doc), max_pages)
        texts = []
        for page_num in range(num_pages):
            page = doc.load_page(page_num)
            texts.append(page.get_text("text"))

        full_text = "\n\n===PAGE BREAK===\n\n".join(texts)

        if not "".join(texts).strip():
            print(f"FAILED {filename}: no extractable text in the first "
                  f"{num_pages} page(s) (needs OCR); no .txt written")
            return False

        with open(out_path, "w", encoding="utf-8") as f:
            f.write(full_text)

        return True
    except Exception as e:
        print(f"FAILED {filename}: {e}")
        return False


def extract_folder(pdf_folder, output_folder, max_pages=12):
    """Extract text from all PDFs in a folder."""
    os.makedirs(output_folder, exist_ok=True)
    count = 0
    failed = 0

    for filename in os.listdir(pdf_folder):
        if filename.lower().endswith(".pdf"):
            pdf_path = os.path.join(pdf_folder, filename)
            if extract_pdf_pages(pdf_path, output_folder, max_pages):
                count += 1
            else:
                failed += 1

    print(f"Extracted {count} PDFs (up to {max_pages} pages each)")
    if failed:
        print(f"Failed: {failed}")
    return count, failed


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python extract_pdfs.py <pdf_folder> <output_folder> [max_pages]")
        sys.exit(1)

    pdf_folder = sys.argv[1]
    output_folder = sys.argv[2]
    max_pages = 12
    if len(sys.argv) > 3:
        try:
            max_pages = int(sys.argv[3])
        except ValueError:
            max_pages = 0
        if max_pages < 1:
            print(f"ERROR: max_pages must be an integer >= 1, got {sys.argv[3]!r}")
            sys.exit(2)

    if os.path.isdir(pdf_folder):
        extract_folder(pdf_folder, output_folder, max_pages)
    elif os.path.isfile(pdf_folder):
        # Single PDF
        os.makedirs(output_folder, exist_ok=True)
        extract_pdf_pages(pdf_folder, output_folder, max_pages)
    else:
        print(f"ERROR: {pdf_folder} is not a file or directory")
        sys.exit(1)
