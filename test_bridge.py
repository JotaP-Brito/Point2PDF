import eel
import base64
from pathlib import Path

@eel.expose
def convert_file(file_b64, original_name, output_name):
    """Pretend conversion – just creates an empty dummy PDF."""
    print("🚀🚀🚀 convert_file called in NEW SCRIPT 🚀🚀🚀")
    dummy_folder = Path.home() / "PDF_Converter_Output"
    dummy_folder.mkdir(exist_ok=True)
    safe_name = output_name if output_name.strip() else "test"
    dummy_pdf = dummy_folder / f"{safe_name}.pdf"
    dummy_pdf.touch()   # create empty file
    print(f"Dummy created: {dummy_pdf}")
    return {
        "success": True,
        "message": f"Dummy PDF created: {dummy_pdf.name}",
        "file_path": str(dummy_pdf)
    }

if __name__ == "__main__":
    eel.init(Path(__file__).parent)
    eel.start("index.html", size=(800, 600), port=5002)