# 📄 Point2PDF

Convert files to PDF through a simple, modern drag-and-drop desktop interface.

Point2PDF provides fast PDF conversion for common file formats while maintaining a clean and lightweight user experience.

## ✨ Features

* Drag & drop or browse for files
* Custom PDF output naming
* Modern desktop interface built with Eel
* Silent conversion with no command windows
* Fast local processing
* Open output folder directly after conversion
* Supports multiple file formats

### Supported Formats

| Format                                       | Conversion Engine    |
| -------------------------------------------- | -------------------- |
| JPG, JPEG, PNG, BMP, GIF                     | Native               |
| TXT                                          | Native               |
| HTML                                         | Native               |
| DOCX                                         | Native               |
| XLSX, CSV, ODS                               | Native               |
| PPTX, ODP, DOC, XLS and other Office formats | LibreOffice fallback |

## 📦 Requirements

### Required

* Python 3.8 or newer
* LibreOffice (recommended for maximum format compatibility)

### Python Dependencies

Install all dependencies:

```bash
pip install -r requirements.txt
```

Or install manually:

```bash
pip install eel Pillow fpdf2 mammoth weasyprint pandas openpyxl odfpy
```

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/JotaP-Brito/Point2PDF.git
cd Point2PDF
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. (Optional) Install LibreOffice

LibreOffice improves compatibility with legacy and advanced Office formats.

Download:

https://www.libreoffice.org/download/download-libreoffice/

If needed, adjust the LibreOffice path inside:

```text
point2PDF.py
```

### 4. Run Point2PDF

```bash
python point2PDF.py
```

The application window will open automatically.

## 🖼️ Customisation

### Logo
<img width="200" alt="Point2PDF" src="https://github.com/user-attachments/assets/624cd9d1-efce-4913-8b59-ee5bdc666402" />



### UI Styling

Modify colors, spacing, animations, and layout directly inside:

```text
index.html
```

### Logo Size

To reduce the logo size, update the `.logo` CSS class:

```css
.logo {
    width: 140px;
    height: auto;
    display: block;
    margin: 0 auto 15px auto;
}
```

Recommended sizes:

* 120px → Compact
* 140px → Balanced
* 160px → Large

## 📁 Output Location

Converted PDFs are saved to:

```text
~/PDF_Converter_Output
```

Windows example:

```text
C:\Users\<username>\PDF_Converter_Output
```

## 📜 License

MIT License

Copyright (c) 2026 Joao Pedro Brito

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

---

Made with ❤️ by Joao Pedro Brito
