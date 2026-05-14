"""图片预处理器：验证、EXIF矫正、GIF处理、格式转换"""

from pathlib import Path
from PIL import Image, ImageOps

from .constants import IMG_FORMATS


class ImageProcessor:
    """图片预处理器：验证、EXIF矫正、GIF处理、格式转换"""

    def validate(self, image_path: Path) -> tuple[bool, str]:
        """验证图片文件是否可读、格式是否支持"""
        if not image_path.exists():
            return False, "文件不存在"

        if image_path.suffix.lower() not in IMG_FORMATS:
            return False, f"不支持的格式: {image_path.suffix}"

        try:
            with Image.open(image_path) as img:
                img.verify()
        except Exception as e:
            return False, f"无法打开图片: {e}"

        return True, ""

    def process(self, image_path: Path) -> Image.Image | None:
        """处理单张图片：验证 → EXIF矫正 → GIF取帧 → 格式转换"""
        is_valid, error_msg = self.validate(image_path)
        if not is_valid:
            print(f"  [跳过] {image_path.name}: {error_msg}")
            return None

        try:
            img = Image.open(image_path)
        except Exception as e:
            print(f"  [跳过] {image_path.name}: 无法打开图片: {e}")
            return None

        try:
            # GIF只取第一帧
            if image_path.suffix.lower() == '.gif':
                new_img = self._extract_gif_frame(img)
                if new_img is None:
                    print(f"  [跳过] {image_path.name}: GIF取帧失败")
                    return None
                if new_img is not img:
                    img.close()
                img = new_img

            # EXIF方向矫正
            new_img = self._fix_exif_orientation(img)
            if new_img is not img:
                img.close()
            img = new_img

            # 格式转换（RGBA/P → RGB）
            new_img = self._normalize_mode(img)
            if new_img is not img:
                img.close()
            img = new_img

            return img
        except MemoryError:
            print(f"  [跳过] {image_path.name}: 内存不足")
            img.close()
            return None
        except Exception as e:
            print(f"  [跳过] {image_path.name}: 处理失败: {e}")
            img.close()
            return None

    def _fix_exif_orientation(self, img: Image.Image) -> Image.Image:
        """根据EXIF方向信息矫正图片旋转"""
        try:
            return ImageOps.exif_transpose(img)
        except Exception:
            # EXIF读取失败，返回原图
            return img

    def _extract_gif_frame(self, img: Image.Image) -> Image.Image | None:
        """提取GIF第一帧"""
        try:
            img.seek(0)
            # 复制第一帧，避免后续帧影响
            frame = img.copy()
            img.close()
            return frame
        except Exception:
            # 取帧失败，尝试重新打开
            try:
                img.close()
                return Image.open(img.filename)
            except Exception:
                return None

    def _normalize_mode(self, img: Image.Image) -> Image.Image:
        """统一图片模式：RGBA/P → RGB，白底填充"""
        if img.mode in ('RGBA', 'P'):
            if img.mode == 'P':
                img = img.convert('RGBA')
            bg = Image.new('RGB', img.size, (255, 255, 255))
            bg.paste(img, mask=img.split()[3] if img.mode == 'RGBA' else None)
            return bg
        elif img.mode != 'RGB':
            return img.convert('RGB')
        return img
