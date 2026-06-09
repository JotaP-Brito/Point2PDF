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
def get_gif_list():
    gif_dir = Path(__file__).parent / "gifs"
    print(f"[DEBUG] get_gif_list called – gif_dir exists: {gif_dir.exists()}")
    if gif_dir.exists():
        files = [f"gifs/{f.name}" for f in gif_dir.iterdir() if f.suffix.lower() == ".gif"]
        print(f"[DEBUG] Found {len(files)} GIFs: {files[:5]}...")
        return files
    print("[DEBUG] gifs folder not found!")
    return []

# ------------------------------------------------------------
# Pure Python converters (no LibreOffice needed)
# ------------------------------------------------------------
def convert_locally(input_path, output_dir, desired_stem):
    """
    Try to convert the file using local Python libraries.
    Returns:
        (True, pdf_path)   if successful
        (False, error_msg) if not supported or failed
    """
    ext = Path(input_path).suffix.lower()
    output_pdf = output_dir / f"{desired_stem}.pdf"

    try:
        # ------- Images -------
        if ext in ('.jpg', '.jpeg', '.png', '.bmp', '.gif'):
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
            @page {{
                size: A4 landscape;
                margin: 1cm;
            }}
            body {{
                font-family: Arial, sans-serif;
                font-size: 10px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                word-wrap: break-word;
            }}
            th {{
                background-color: #2e7d32;
                color: white;
                padding: 6px;
                text-align: left;
                font-weight: bold;
            }}
            td {{
                padding: 4px 6px;
                border-bottom: 1px solid #ddd;
            }}
            tr:nth-child(even) {{
                background-color: #f9f9f9;
            }}
            </style>
            </head>
            <body>
            {df.to_html(index=False, na_rep='')}
            </body>
            </html>"""
            HTML(string=html_template).write_pdf(output_pdf)
            return True, str(output_pdf)
        # ------- Not supported locally -------
        else:
            return False, f"File type '{ext}' is not supported by the internal converter."

    except Exception as e:
        return False, f"Local conversion failed: {e}"

# ------------------------------------------------------------
# Eel exposed functions
# ------------------------------------------------------------
@eel.expose
def convert_file(file_b64, original_name, output_name):
    try:
        print("🚀 convert_file started")
        print(f"[DEBUG] Original file name: {original_name}")
        print(f"[DEBUG] Requested output name: {output_name}")

        file_bytes = base64.b64decode(file_b64)
        ext = Path(original_name).suffix or ".tmp"
        tmp_input = UPLOAD_FOLDER / f"{uuid.uuid4().hex}{ext}"
        print(f"[DEBUG] Saving temp input as: {tmp_input}")
        with open(tmp_input, "wb") as f:
            f.write(file_bytes)

        safe_name = sanitize_filename(output_name) or "output"
        print(f"[DEBUG] Sanitized output name: {safe_name}")

        # ---- Call converter----
        local_success, local_result = convert_locally(tmp_input, UPLOAD_FOLDER, safe_name)

        if local_success:
            os.remove(tmp_input)
            return {
                "success": True,
                "message": f"PDF created (internal): {Path(local_result).name}",
                "file_path": local_result
            }
        else:
            print("Unfortunately, We don't support this extension")

    except Exception as e:
        print(f"[DEBUG] ❌ Error: {e}")
        return {"success": False, "message": str(e)}

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
    eel.start("index.html", size=(1920, 1080), port=5004,cmdline_args=['--start-fullscreen'])