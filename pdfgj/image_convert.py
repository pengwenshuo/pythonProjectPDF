"""图片转 PDF"""

from pathlib import Path
from PIL import Image

from .utils import _check_overwrite


def image_to_pdf(image_path: Path) -> bool:
    """单张图片转 PDF，自动将透明背景转为白底"""
    pdf_path = image_path.with_suffix('.pdf')
    if not _check_overwrite(pdf_path):
        return False
    try:
        img = Image.open(image_path)
        # 透明/调色板模式统一转 RGB，透明部分用白底填充
        if img.mode in ('RGBA', 'P'):
            if img.mode == 'P':
                img = img.convert('RGBA')
            bg = Image.new('RGB', img.size, (255, 255, 255))
            bg.paste(img, mask=img.split()[3] if img.mode == 'RGBA' else None)
            img = bg
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        img.save(pdf_path, format="PDF", save_all=True, resolution=200.0)
        print(f"  [OK] {image_path.name} → {pdf_path.name}")
        return True
    except Exception as err:
        print(f"  [失败] {image_path.name}: {err}")
        return False
