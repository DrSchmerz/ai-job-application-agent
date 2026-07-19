"""Tests for core.cv — text extraction + local profile parsing."""
import pytest
from core import cv


def test_extract_txt(tmp_path):
    f = tmp_path / "cv.txt"
    f.write_text("Python data scientist with SQL and pandas.")
    assert "Python" in cv.extract_text(f)


def test_extract_docx_roundtrip(tmp_path):
    import docx
    f = tmp_path / "cv.docx"
    d = docx.Document()
    d.add_paragraph("Machine learning engineer skilled in PyTorch and Docker.")
    d.save(str(f))
    text = cv.extract_text(f)
    assert "PyTorch" in text and "Docker" in text


def test_unsupported_format_raises(tmp_path):
    f = tmp_path / "cv.rtf"
    f.write_text("x")
    with pytest.raises(ValueError):
        cv.extract_text(f)


def test_parse_cv_local_fallback():
    profile = cv.parse_cv("Data engineer: Python, SQL, Spark, ETL, stakeholder management.")
    assert profile["source"] == "local"
    assert "python" in profile["skills"]
    assert "spark" in profile["skills"]
    assert "stakeholder" in profile["skills"]


def test_parse_cv_empty():
    assert cv.parse_cv("")["skills"] == []
