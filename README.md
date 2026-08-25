# Point2PDF

Point2PDF is a local desktop app for converting common files to PDF through a drag-and-drop interface. It uses native Python libraries only; LibreOffice is not required.

## Features

- Convert one file or a batch of files locally
- Merge two or more supported files into one PDF
- Convert images with optional OCR, when Tesseract is installed
- Keep every sheet of XLSX and ODS workbooks
- Preserve existing PDFs when converting or merging them
- Choose an output name without overwriting prior PDFs
- Open the managed output folder after a conversion

## Supported input formats

| Format | Native conversion |
| --- | --- |
| PDF | Copy or merge pages |
| JPG, JPEG, PNG, BMP, GIF | Image-to-PDF; optional OCR |
| TXT | Text-to-PDF |
| HTML | HTML-to-PDF |
| DOCX | Document text and supported formatting-to-PDF |
| XLSX, CSV, ODS | Table-to-PDF; XLSX/ODS include all sheets |

Legacy Office files such as `.doc`, `.xls`, `.pptx`, and `.odp` are intentionally not supported. They require a separate office-rendering engine and are not advertised by the app.

## Install and run

Requires Python 3.9 or later.

```bash
pip install -r requirements.txt
python point2PDF.py
```

For OCR, install [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) and make `tesseract` available on your `PATH`. On Windows, the usual installation path is `C:\Program Files\Tesseract-OCR\tesseract.exe`.

## Development and testing

Install development dependencies and run the test suite:

```bash
pip install -r requirements-dev.txt
pytest
```

To build the Windows executable, install PyInstaller and run:

```bash
pyinstaller Point2PDF.spec
```

The spec is tracked and uses the bundled `gtk/` DLL folder, rather than a machine-specific MSYS2 path.

## Output location

All PDFs are saved to:

```text
~/PDF_Converter_Output
```

The app adds ` (2)`, ` (3)`, and so on when an output name already exists, so previous files are kept.

## License

MIT License. See [LICENSE](LICENSE).
