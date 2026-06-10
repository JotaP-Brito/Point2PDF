import subprocess
import sys
import os
import platform
import re
import tempfile
import shutil
from pathlib import Path
import uuid
import base64
import eel
from PIL import Image
import img2pdf
import mammoth
from weasyprint import HTML
from fpdf import FPDF
import pandas as pd
import pytesseract
from io import BytesIO
from pypdf import PdfMerger

# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------
def sanitize_filename(name):
    """Remove invalid characters from a filename."""
    return re.sub(r'[\\/*?:"<>|]', "", name).strip()

# Output folder
UPLOAD_FOLDER = Path.home() / "PDF_Converter_Output"
UPLOAD_FOLDER.mkdir(exist_ok=True)

@eel.expose
def merge_pdfs(file_data_list, output_name):
    """
    file_data_list: list of {b64, original_name}
    Converts each file to PDF locally, merges them, returns the merged PDF path.
    """
    temp_pdfs = []
    try:
        # Convert each file individually
        for idx, fdata in enumerate(file_data_list):
            b64 = fdata.get("b64", "")
            orig_name = fdata.get("original_name", f"file_{idx}")
            file_bytes = base64.b64decode(b64)
            ext = Path(orig_name).suffix or ".tmp"
            tmp_input = UPLOAD_FOLDER / f"merge_{idx}_{uuid.uuid4().hex}{ext}"
            with open(tmp_input, "wb") as f:
                f.write(file_bytes)
            
            safe_stem = sanitize_filename(f"temp_{idx}_{uuid.uuid4().hex}")
            success, result = convert_locally(tmp_input, UPLOAD_FOLDER, safe_stem)
            os.remove(tmp_input)
            
            if success:
                temp_pdfs.append(result)
            else:
                return {"success": False, "message": f"Failed to convert {orig_name}: {result}"}
        
        # Merge all temporary PDFs
        safe_output = sanitize_filename(output_name) or "merged"
        merged_path = UPLOAD_FOLDER / f"{safe_output}.pdf"
        
        merger = PdfMerger()
        for pdf_path in temp_pdfs:
            merger.append(pdf_path)
        merger.write(str(merged_path))
        merger.close()
        
        # Clean up temporary PDFs
        for pdf_path in temp_pdfs:
            try:
                os.remove(pdf_path)
            except:
                pass
        
        return {
            "success": True,
            "message": f"Merged PDF created: {merged_path.name}",
            "file_path": str(merged_path)
        }
    except Exception as e:
        return {"success": False, "message": str(e)}


@eel.expose
def get_gif_list():
    gif_dir = Path(__file__).parent / "gifs"
    if gif_dir.exists():
        files = [f"gifs/{f.name}" for f in gif_dir.iterdir() if f.suffix.lower() == ".gif"]
        return files
    return []


# ------------------------------------------------------------
# Pure Python converters (no LibreOffice needed)
# ------------------------------------------------------------
def convert_locally(input_path, output_dir, desired_stem, ocr=False):
    """
    Convert file using local Python libraries.
    ocr: If True and file is an image, produce a searchable PDF (OCR).
    Returns (True, pdf_path) or (False, error_msg).
    """
    ext = Path(input_path).suffix.lower()
    output_pdf = output_dir / f"{desired_stem}.pdf"

    try:
        # ------- Images -------
        if ext in ('.jpg', '.jpeg', '.png', '.bmp', '.gif'):
            if ocr:
                # Use Tesseract to produce a searchable PDF
                # pytesseract.image_to_pdf_or_hocr returns the raw PDF bytes
                img = Image.open(input_path)
                pdf_bytes = pytesseract.image_to_pdf_or_hocr(img, extension='pdf')
                with open(output_pdf, 'wb') as f:
                    f.write(pdf_bytes)
                return True, str(output_pdf)
            else:
                img = Image.open(input_path).convert('RGB')
                img.save(output_pdf, 'PDF')
                return True, str(output_pdf)

        # ------- Plain text -------
        elif ext == '.txt':
            pdf = FPDF()
            pdf.add_page()
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.set_font("Arial", size=12)
            with open(input_path, 'r', encoding='utf-8', errors='replace') as f:
                for line in f:
                    pdf.cell(200, 10, txt=line.strip(), ln=True)
            pdf.output(str(output_pdf))
            return True, str(output_pdf)

        # ------- HTML -------
        elif ext == '.html':
            HTML(filename=input_path).write_pdf(output_pdf)
            return True, str(output_pdf)

        # ------- DOCX → HTML → PDF -------
        elif ext == '.docx':
            with open(input_path, "rb") as f:
                result = mammoth.convert_to_html(f)
            html = result.value
            HTML(string=html).write_pdf(output_pdf)
            return True, str(output_pdf)

        # ------- Spreadsheets (xlsx, ods, csv) -------
        elif ext in ('.xlsx', '.ods', '.csv'):
            if ext == '.csv':
                df = pd.read_csv(input_path)
            elif ext == '.xlsx':
                df = pd.read_excel(input_path, engine='openpyxl')
            elif ext == '.ods':
                df = pd.read_excel(input_path, engine='odf')
            
            html_template = f"""<!DOCTYPE html>
            <html>
            <head>
            <meta charset="utf-8">
            <style>
            @page {{ size: A4 landscape; margin: 1cm; }}
            body {{ font-family: Arial, sans-serif; font-size: 10px; }}
            table {{ width: 100%; border-collapse: collapse; word-wrap: break-word; }}
            th {{ background-color: #2e7d32; color: white; padding: 6px; text-align: left; font-weight: bold; }}
            td {{ padding: 4px 6px; border-bottom: 1px solid #ddd; }}
            tr:nth-child(even) {{ background-color: #f9f9f9; }}
            </style>
            </head>
            <body>
            {df.to_html(index=False, na_rep='')}
            </body>
            </html>"""
            HTML(string=html_template).write_pdf(output_pdf)
            return True, str(output_pdf)

        # ------- Not supported -------
        else:
            return False, f"File type '{ext}' not supported."

    except Exception as e:
        return False, f"Local conversion failed: {e}"


# ------------------------------------------------------------
# Single file conversion (existing, now with OCR)
# ------------------------------------------------------------
@eel.expose
def convert_file(file_b64, original_name, output_name, ocr=False):
    try:
        file_bytes = base64.b64decode(file_b64)
        ext = Path(original_name).suffix or ".tmp"
        tmp_input = UPLOAD_FOLDER / f"{uuid.uuid4().hex}{ext}"
        with open(tmp_input, "wb") as f:
            f.write(file_bytes)

        safe_name = sanitize_filename(output_name) or "output"
        success, result = convert_locally(tmp_input, UPLOAD_FOLDER, safe_name, ocr=ocr)
        os.remove(tmp_input)

        if success:
            return {
                "success": True,
                "message": f"PDF created: {Path(result).name}",
                "file_path": result
            }
        else:
            return {"success": False, "message": result}
    except Exception as e:
        return {"success": False, "message": str(e)}


# ------------------------------------------------------------
# Batch conversion (new)
# ------------------------------------------------------------
@eel.expose
def convert_batch(files_data):
    """
    files_data: list of {b64, original_name, output_name, ocr (optional)}
    Returns list of results for each file.
    """
    results = []
    for idx, fdata in enumerate(files_data):
        b64 = fdata.get("b64", "")
        orig_name = fdata.get("original_name", f"file_{idx}")
        out_name = fdata.get("output_name", "")
        ocr = fdata.get("ocr", False)

        res = convert_file(b64, orig_name, out_name, ocr)
        res["index"] = idx
        results.append(res)
    return results


@eel.expose
def open_file_explorer(path):
    folder = Path(path).parent
    if folder.exists():
        if sys.platform == "win32":
            os.startfile(folder)
        elif sys.platform == "darwin":
            subprocess.run(["open", str(folder)])
        else:
            subprocess.run(["xdg-open", str(folder)])


# ------------------------------------------------------------
# Start the Eel app
# ------------------------------------------------------------
if __name__ == "__main__":
    eel.init(Path(__file__).parent)
    eel.start("index.html", size=(1920, 1080), port=5004,
              cmdline_args=['--start-fullscreen'])