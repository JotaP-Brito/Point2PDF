import base64
from io import BytesIO

from pypdf import PdfReader, PdfWriter

import point2PDF as app


def pdf_bytes():
    stream = BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    writer.write(stream)
    return stream.getvalue()


def configure_output(monkeypatch, tmp_path):
    monkeypatch.setattr(app, "OUTPUT_FOLDER", tmp_path)


def test_sanitize_filename_handles_invalid_and_reserved_names():
    assert app.sanitize_filename(' report<>?.pdf ') == 'report'
    assert app.sanitize_filename('CON') == 'output'
    assert app.sanitize_filename('..') == 'output'


def test_create_output_path_does_not_overwrite(monkeypatch, tmp_path):
    configure_output(monkeypatch, tmp_path)
    (tmp_path / 'report.pdf').touch()

    assert app.create_output_path('report').name == 'report (2).pdf'


def test_convert_file_accepts_existing_pdf_and_removes_upload(monkeypatch, tmp_path):
    configure_output(monkeypatch, tmp_path)
    result = app.convert_file(base64.b64encode(pdf_bytes()).decode(), 'source.pdf', 'report')

    assert result['success'] is True
    assert (tmp_path / 'report.pdf').exists()
    assert not list(tmp_path.glob('.upload-*'))
    assert len(PdfReader(result['file_path']).pages) == 1


def test_merge_pdfs_merges_pdf_inputs_and_cleans_temp_files(monkeypatch, tmp_path):
    configure_output(monkeypatch, tmp_path)
    encoded_pdf = base64.b64encode(pdf_bytes()).decode()

    result = app.merge_pdfs(
        [{'b64': encoded_pdf, 'original_name': 'first.pdf'}, {'b64': encoded_pdf, 'original_name': 'second.pdf'}],
        'combined',
    )

    assert result['success'] is True
    assert len(PdfReader(result['file_path']).pages) == 2
    assert not list(tmp_path.glob('.merge-*'))


def test_metadata_rejects_paths_outside_output_folder(monkeypatch, tmp_path):
    configure_output(monkeypatch, tmp_path)

    result = app.set_metadata(tmp_path.parent / 'outside.pdf')

    assert result == {'success': False, 'message': 'This PDF is outside the application output folder.'}
