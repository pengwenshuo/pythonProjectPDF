"""图片转 PDF"""

from pathlib import Path

from .utils import _check_overwrite
from .image_processor import ImageProcessor


def image_to_pdf(image_path: Path) -> bool:
    """单张图片转 PDF"""
    pdf_path = image_path.with_suffix('.pdf')
    if not _check_overwrite(pdf_path):
        return False

    processor = ImageProcessor()
    img = processor.process(image_path)
    if img is None:
        return False

    try:
        img.save(pdf_path, format="PDF", resolution=200.0)
        print(f"  [OK] {image_path.name} → {pdf_path.name}")
        return True
    except Exception as err:
        print(f"  [失败] {image_path.name}: {err}")
        return False
    finally:
        img.close()
