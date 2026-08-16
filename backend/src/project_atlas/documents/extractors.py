from pathlib import Path

from pypdf import PdfReader


def extract_pdf(path: Path) -> str:
    reader = PdfReader(path)
    pages = [(page.extract_text() or "").strip() for page in reader.pages]
    return "\n\f\n".join(pages).strip()


def extract_utf8_text(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def extract_text(path: Path, extension: str) -> str:
    if extension == ".pdf":
        return extract_pdf(path)
    if extension in {".txt", ".md"}:
        return extract_utf8_text(path)
    raise ValueError("Unsupported document extension")
