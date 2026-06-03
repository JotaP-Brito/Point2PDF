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

# ------------------------------------------------------------
# Configuration – adjust this path if necessary
# ------------------------------------------------------------
SOFFICE_PATH = r"C:\Program Files\LibreOffice\program\soffice.exe"
# Alternative if you have the 32-bit version:
# SOFFICE_PATH = r"C:\Program Files (x86)\LibreOffice\program\soffice.exe"

# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------
def sanitize_filename(name):
    """Remove invalid characters from a filename."""
    return re.sub(r'[\\/*?:"<>|]', "", name).strip()

# Output folder
UPLOAD_FOLDER = Path.home() / "PDF_Converter_Output"
UPLOAD_FOLDER.mkdir(exist_ok=True)

# ------------------------------------------------------------
# Conversion (simple, reliable, with detailed logs)
# ------------------------------------------------------------
def convert_to_pdf(input_path, output_dir, desired_stem):
    if not os.path.exists(SOFFICE_PATH):
        raise Exception(
            f"LibreOffice not found at:\n{SOFFICE_PATH}\n"
            "Please edit SOFFICE_PATH in point2PDF.py."
        )

    tmp_dir = Path(tempfile.mkdtemp())

    try:
        # A dedicated profile avoids any user‑profile lock or recovery prompts
        profile_dir = tmp_dir / "profile"

        cmd = [
            SOFFICE_PATH,
            f"-env:UserInstallation=file:///{profile_dir.as_posix()}",
            "--headless",
            "--nologo",
            "--nodefault",
            "--norestore",
            "--convert-to", "pdf",
            "--outdir", str(tmp_dir),
            str(input_path),
        ]

        print("[DEBUG] Starting LibreOffice...")
        print("[DEBUG] Input file:", input_path)
        print("[DEBUG] Temp output folder:", tmp_dir)
        print("[DEBUG] Command:", " ".join(cmd))

        # Run silently – no console window
        creationflags = subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,        # generous timeout for large files
            creationflags=creationflags,
        )

        print("[DEBUG] Return Code:", result.returncode)
        print("[DEBUG] STDOUT:", result.stdout.strip())
        print("[DEBUG] STDERR:", result.stderr.strip())

        if result.returncode != 0:
            raise Exception(
                f"LibreOffice failed.\n\nSTDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
            )

        # Find the produced PDF (LibreOffice uses the input stem)
        pdfs = list(tmp_dir.glob("*.pdf"))
        if not pdfs:
            raise Exception(
                "LibreOffice finished but no PDF was generated.\n\n"
                f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
            )

        final_path = output_dir / f"{desired_stem}.pdf"

        # Overwrite if exists
        if final_path.exists():
            final_path.unlink()

        shutil.move(str(pdfs[0]), str(final_path))
        print("[DEBUG] PDF saved to:", final_path)
        return final_path

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

# ------------------------------------------------------------
# Eel exposed functions
# ------------------------------------------------------------
@eel.expose
def convert_file(file_b64, original_name, output_name):
    try:
        print("🚀 convert_file started")
        print(f"[DEBUG] Original file name: {original_name}")
        print(f"[DEBUG] Requested output name: {output_name}")

        # Decode the file sent from the frontend
        file_bytes = base64.b64decode(file_b64)
        ext = Path(original_name).suffix or ".tmp"
        tmp_input = UPLOAD_FOLDER / f"{uuid.uuid4().hex}{ext}"
        print(f"[DEBUG] Saving temp input as: {tmp_input}")
        with open(tmp_input, "wb") as f:
            f.write(file_bytes)

        # Sanitize output name
        safe_name = sanitize_filename(output_name) or "output"
        print(f"[DEBUG] Sanitized output name: {safe_name}")

        # Convert
        result_path = convert_to_pdf(tmp_input, UPLOAD_FOLDER, safe_name)

        # Delete the temporary input file
        os.remove(tmp_input)

        return {
            "success": True,
            "message": f"PDF created: {result_path.name}",
            "file_path": str(result_path)
        }
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
    eel.start("index.html", size=(800, 600), port=5004)