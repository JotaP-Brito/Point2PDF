import base64
import binascii
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

# Prefer the project's GTK runtime on Windows. This avoids accidentally loading
# incompatible GTK DLLs installed by unrelated applications such as Tesseract.
_DLL_DIRECTORY = None
if hasattr(os, "add_dll_directory"):
    runtime_root = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))
    bundled_gtk = runtime_root / "gtk"
    if bundled_gtk.is_dir():
        _DLL_DIRECTORY = os.add_dll_directory(str(bundled_gtk))
        os.environ.setdefault("WEASYPRINT_DLL_DIRECTORIES", str(bundled_gtk))

import eel
import mammoth
import pandas as pd
import pytesseract
from fpdf import FPDF
from PIL import Image
from pypdf import PdfReader, PdfWriter


# ----- Silence Fontconfig warnings on Windows (WeasyPrint) -----
if platform.system() == "Windows":
    for fontconfig_path in (
        r"C:\msys64\mingw64\etc\fonts",
        r"C:\Program Files\GTK3-Runtime Win64\etc\fonts",
        r"C:\Program Files (x86)\GTK3-Runtime Win32\etc\fonts",
    ):
        if os.path.isdir(fontconfig_path):
            os.environ["FONTCONFIG_PATH"] = fontconfig_path
            break


OUTPUT_FOLDER = Path.home() / "Cadmus_Output"
MAX_FILE_SIZE_BYTES = 100 * 1024 * 1024
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".gif"}
SPREADSHEET_EXTENSIONS = {".xlsx", ".ods", ".csv"}
SUPPORTED_EXTENSIONS = IMAGE_EXTENSIONS | SPREADSHEET_EXTENSIONS | {".txt", ".html", ".docx", ".pdf"}
WINDOWS_RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{number}" for number in range(1, 10)),
    *(f"LPT{number}" for number in range(1, 10)),
}


def sanitize_filename(name, fallback="output"):
    """Return a safe, portable filename stem without an extension."""
    candidate = Path(str(name)).name
    candidate = re.sub(r'[\\/*?:"<>|]', "", candidate).strip(". ")
    candidate = re.sub(r"\s+", " ", candidate)
    if candidate.lower().endswith(".pdf"):
        candidate = candidate[:-4].rstrip(". ")
    if not candidate or candidate.upper() in WINDOWS_RESERVED_NAMES:
        candidate = fallback
    return candidate[:120]


def ensure_output_folder():
    OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)
    return OUTPUT_FOLDER


def create_output_path(stem, suffix=".pdf"):
    """Choose a non-destructive output path inside the application folder."""
    ensure_output_folder()
    safe_stem = sanitize_filename(stem)
    candidate = OUTPUT_FOLDER / f"{safe_stem}{suffix}"
    number = 2
    while candidate.exists():
        candidate = OUTPUT_FOLDER / f"{safe_stem} ({number}){suffix}"
        number += 1
    return candidate


def is_output_file(path):
    """Reject paths outside the folder managed by this application."""
    try:
        Path(path).resolve().relative_to(OUTPUT_FOLDER.resolve())
        return True
    except (OSError, ValueError):
        return False


def decode_upload(file_b64):
    if not isinstance(file_b64, str):
        raise ValueError("The uploaded file is invalid.")
    if len(file_b64) > (MAX_FILE_SIZE_BYTES * 4 // 3) + 4:
        raise ValueError("Files larger than 100 MB are not supported.")
    try:
        file_bytes = base64.b64decode(file_b64, validate=True)
    except (binascii.Error, ValueError) as error:
        raise ValueError("The uploaded file is not valid base64 data.") from error
    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        raise ValueError("Files larger than 100 MB are not supported.")
    return file_bytes


def write_html_pdf(*, output_pdf, filename=None, html=None, base_url=None):
    """Load WeasyPrint only for formats that require the GTK rendering stack."""
    from weasyprint import HTML

    if filename:
        HTML(filename=str(filename), base_url=str(base_url)).write_pdf(str(output_pdf))
    else:
        HTML(string=html, base_url=str(base_url) if base_url else None).write_pdf(str(output_pdf))


@eel.expose
def get_gif_list():
    gif_dir = Path(__file__).parent / "gifs"
    if not gif_dir.exists():
        return []
    return sorted(f"gifs/{file.name}" for file in gif_dir.iterdir() if file.suffix.lower() == ".gif")


def convert_locally(input_path, output_pdf, ocr=False):
    """Convert one supported file to a backend-selected PDF path."""
    input_path = Path(input_path)
    output_pdf = Path(output_pdf)
    extension = input_path.suffix.lower()

    try:
        if extension == ".pdf":
            shutil.copyfile(input_path, output_pdf)

        elif extension in IMAGE_EXTENSIONS:
            with Image.open(input_path) as image:
                if ocr:
                    pdf_bytes = pytesseract.image_to_pdf_or_hocr(image, extension="pdf")
                    output_pdf.write_bytes(pdf_bytes)
                else:
                    image.convert("RGB").save(output_pdf, "PDF")

        elif extension == ".txt":
            pdf = FPDF()
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.add_page()
            pdf.set_font("Helvetica", size=12)
            with input_path.open("r", encoding="utf-8", errors="replace") as text_file:
                for line in text_file:
                    pdf.multi_cell(0, 7, text=line.rstrip("\r\n"))
            pdf.output(str(output_pdf))

        elif extension == ".html":
            write_html_pdf(output_pdf=output_pdf, filename=input_path, base_url=input_path.parent)

        elif extension == ".docx":
            with input_path.open("rb") as document:
                html = mammoth.convert_to_html(document).value
            write_html_pdf(output_pdf=output_pdf, html=html, base_url=input_path.parent)

        elif extension in SPREADSHEET_EXTENSIONS:
            if extension == ".csv":
                sheets = {input_path.stem: pd.read_csv(input_path)}
            elif extension == ".xlsx":
                sheets = pd.read_excel(input_path, engine="openpyxl", sheet_name=None)
            else:
                sheets = pd.read_excel(input_path, engine="odf", sheet_name=None)

            tables = "".join(
                f'<section><h1>{sheet_name}</h1>{dataframe.to_html(index=False, na_rep="", escape=True)}</section>'
                for sheet_name, dataframe in sheets.items()
            )
            html = f"""<!doctype html>
<html><head><meta charset="utf-8"><style>
@page {{ size: A4 landscape; margin: 1cm; }}
body {{ font-family: Arial, sans-serif; font-size: 10px; }}
section {{ break-after: page; }} section:last-child {{ break-after: auto; }}
table {{ width: 100%; border-collapse: collapse; overflow-wrap: anywhere; }}
th {{ background: #2e7d32; color: white; padding: 6px; text-align: left; }}
td {{ padding: 4px 6px; border-bottom: 1px solid #ddd; }}
tr:nth-child(even) {{ background: #f9f9f9; }}
</style></head><body>{tables}</body></html>"""
            write_html_pdf(output_pdf=output_pdf, html=html)

        else:
            return False, f"File type '{extension or '(no extension)'}' is not supported."
        return True, str(output_pdf)
    except Exception as error:
        return False, f"Conversion failed: {error}"


def encrypt_pdf_file(file_path, password):
    if not password:
        return True, str(file_path)
    if not is_output_file(file_path):
        return False, "This PDF is outside the application output folder."
    try:
        reader = PdfReader(file_path)
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
        writer.encrypt(password)
        encrypted_path = create_output_path(f"{Path(file_path).stem}_encrypted")
        with encrypted_path.open("xb") as encrypted_file:
            writer.write(encrypted_file)
        return True, str(encrypted_path)
    except Exception as error:
        return False, str(error)


@eel.expose
def encrypt_pdf(file_path, password):
    success, result = encrypt_pdf_file(file_path, password)
    if success:
        return {"success": True, "message": f"Encrypted PDF: {Path(result).name}", "file_path": result}
    return {"success": False, "message": result}


@eel.expose
def convert_file(file_b64, original_name, output_name, ocr=False, password=None):
    temporary_input = None
    try:
        file_bytes = decode_upload(file_b64)
        extension = Path(str(original_name)).suffix.lower()
        if extension not in SUPPORTED_EXTENSIONS:
            return {"success": False, "message": f"File type '{extension or '(no extension)'}' is not supported."}

        ensure_output_folder()
        temporary_input = OUTPUT_FOLDER / f".upload-{uuid.uuid4().hex}{extension}"
        temporary_input.write_bytes(file_bytes)
        output_pdf = create_output_path(sanitize_filename(output_name, "output"))
        success, result = convert_locally(temporary_input, output_pdf, ocr=bool(ocr))
        if not success:
            return {"success": False, "message": result}

        if password:
            encrypted, encrypted_result = encrypt_pdf_file(result, password)
            if not encrypted:
                return {"success": False, "message": encrypted_result}
            Path(result).unlink(missing_ok=True)
            result = encrypted_result
            message = f"PDF created (encrypted): {Path(result).name}"
        else:
            message = f"PDF created: {Path(result).name}"
        return {"success": True, "message": message, "file_path": result}
    except ValueError as error:
        return {"success": False, "message": str(error)}
    except Exception as error:
        return {"success": False, "message": f"Conversion failed: {error}"}
    finally:
        if temporary_input:
            temporary_input.unlink(missing_ok=True)


@eel.expose
def convert_batch(files_data):
    if not isinstance(files_data, list):
        return [{"index": 0, "success": False, "message": "The batch data is invalid."}]
    results = []
    for index, file_data in enumerate(files_data):
        if not isinstance(file_data, dict):
            results.append({"index": index, "success": False, "message": "The file data is invalid."})
            continue
        result = convert_file(
            file_data.get("b64", ""),
            file_data.get("original_name", f"file_{index}"),
            file_data.get("output_name", ""),
            file_data.get("ocr", False),
            file_data.get("password"),
        )
        result["index"] = index
        results.append(result)
    return results


@eel.expose
def merge_pdfs(file_data_list, output_name):
    if not isinstance(file_data_list, list) or len(file_data_list) < 2:
        return {"success": False, "message": "Select at least two supported files to merge."}

    try:
        ensure_output_folder()
        with tempfile.TemporaryDirectory(prefix=".merge-", dir=OUTPUT_FOLDER) as temporary_dir_name:
            temporary_dir = Path(temporary_dir_name)
            pdf_paths = []
            for index, file_data in enumerate(file_data_list):
                if not isinstance(file_data, dict):
                    return {"success": False, "message": f"File {index + 1} is invalid."}
                original_name = file_data.get("original_name", f"file_{index + 1}")
                extension = Path(str(original_name)).suffix.lower()
                if extension not in SUPPORTED_EXTENSIONS:
                    return {"success": False, "message": f"{original_name}: unsupported file type."}
                input_path = temporary_dir / f"input-{index}{extension}"
                input_path.write_bytes(decode_upload(file_data.get("b64", "")))
                pdf_path = temporary_dir / f"converted-{index}.pdf"
                success, result = convert_locally(input_path, pdf_path, ocr=bool(file_data.get("ocr", False)))
                if not success:
                    return {"success": False, "message": f"Failed to convert {original_name}: {result}"}
                pdf_paths.append(Path(result))

            merged_path = create_output_path(sanitize_filename(output_name, "merged"))
            writer = PdfWriter()
            for pdf_path in pdf_paths:
                reader = PdfReader(pdf_path)
                for page in reader.pages:
                    writer.add_page(page)
            with merged_path.open("xb") as merged_file:
                writer.write(merged_file)

        return {"success": True, "message": f"Merged PDF created: {merged_path.name}", "file_path": str(merged_path)}
    except ValueError as error:
        return {"success": False, "message": str(error)}
    except Exception as error:
        return {"success": False, "message": f"Merge failed: {error}"}


@eel.expose
def set_metadata(file_path, title="", author="", subject="", keywords=""):
    if not is_output_file(file_path):
        return {"success": False, "message": "This PDF is outside the application output folder."}
    try:
        reader = PdfReader(file_path)
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
        writer.add_metadata({
            "/Title": str(title), "/Author": str(author),
            "/Subject": str(subject), "/Keywords": str(keywords),
        })
        metadata_path = create_output_path(f"{Path(file_path).stem}_metadata")
        with metadata_path.open("xb") as metadata_file:
            writer.write(metadata_file)
        return {"success": True, "file_path": str(metadata_path)}
    except Exception as error:
        return {"success": False, "message": str(error)}


@eel.expose
def open_file_explorer(_path=None):
    """Open only the managed output directory; never a caller-provided directory."""
    ensure_output_folder()
    if sys.platform == "win32":
        os.startfile(OUTPUT_FOLDER)
    elif sys.platform == "darwin":
        subprocess.run(["open", str(OUTPUT_FOLDER)], check=False)
    else:
        subprocess.run(["xdg-open", str(OUTPUT_FOLDER)], check=False)


def start_app():
    eel.init(Path(__file__).parent)
    eel.start("index.html", size=(1920, 1080), port=5004, cmdline_args=["--start-fullscreen"])


if __name__ == "__main__":
    start_app()
