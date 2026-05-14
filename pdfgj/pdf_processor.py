"""PDF处理器：文件验证、页面标准化、方向矫正"""

from pathlib import Path
from .deps import _has_pypdf, PdfReader


class PDFProcessor:
    """PDF处理器：验证、标准化、方向矫正"""

    # A4画布尺寸（点）
    A4_WIDTH = 595.28
    A4_HEIGHT = 841.89

    def __init__(self):
        if not _has_pypdf:
            raise RuntimeError("缺少 pypdf 库，无法处理 PDF。请运行: pip install pypdf")

    def validate_file(self, file_path: Path) -> tuple[bool, str]:
        """验证PDF文件

        Args:
            file_path: PDF文件路径

        Returns:
            tuple[bool, str]: (是否有效, 错误信息)
        """
        # 检测0字节文件
        if file_path.stat().st_size == 0:
            return False, "文件为空（0字节）"

        # 检测无法打开的PDF
        try:
            reader = PdfReader(str(file_path))
        except Exception as e:
            return False, f"无法打开PDF: {e}"

        # 检测空白页面
        if len(reader.pages) == 0:
            return False, "PDF没有页面"

        return True, ""

    def standardize_page(self, page):
        """标准化页面到A4尺寸

        Args:
            page: 原始PDF页面

        Returns:
            标准化后的A4页面
        """
        # 获取原始页面尺寸
        original_width = float(page.mediabox.width)
        original_height = float(page.mediabox.height)

        # 计算缩放比例
        scale_x = self.A4_WIDTH / original_width
        scale_y = self.A4_HEIGHT / original_height
        scale = min(scale_x, scale_y)  # 保持宽高比

        # 计算新尺寸
        new_width = original_width * scale
        new_height = original_height * scale

        # 计算居中偏移
        offset_x = (self.A4_WIDTH - new_width) / 2
        offset_y = (self.A4_HEIGHT - new_height) / 2

        # 创建新的A4页面
        from pypdf import PageObject, Transformation
        new_page = PageObject.create_blank_page(
            width=self.A4_WIDTH,
            height=self.A4_HEIGHT
        )

        # 合并原始页面到新页面
        new_page.merge_transformed_page(
            page,
            Transformation().scale(scale).translate(offset_x, offset_y)
        )

        return new_page

    def correct_orientation(self, page):
        """矫正页面方向

        Args:
            page: 原始PDF页面

        Returns:
            矫正方向后的页面
        """
        # 获取旋转属性（pypdf 使用 /Rotate，兼容 /Rotation）
        rotation = page.get('/Rotate', page.get('/Rotation', 0))

        # 如果有旋转，需要矫正
        if rotation != 0:
            from pypdf import PageObject, Transformation
            w = float(page.mediabox.width)
            h = float(page.mediabox.height)
            # 90/270度旋转时交换宽高
            if rotation in (90, 270, -90, -270):
                w, h = h, w
            new_page = PageObject.create_blank_page(width=w, height=h)
            # 旋转围绕页面中心点
            new_page.merge_transformed_page(
                page,
                Transformation().rotate(-rotation)
            )
            return new_page

        return page

    def process_pdf(self, file_path: Path) -> tuple[bool, list, str]:
        """处理PDF文件

        Args:
            file_path: PDF文件路径

        Returns:
            tuple[bool, list, str]: (是否成功, 处理后的页面列表, 错误信息)
        """
        # 验证文件
        is_valid, error_msg = self.validate_file(file_path)
        if not is_valid:
            return False, [], error_msg

        # 读取PDF
        try:
            reader = PdfReader(str(file_path))
        except Exception as e:
            return False, [], f"无法打开PDF: {e}"

        # 处理每一页
        processed_pages = []
        for page in reader.pages:
            # 矫正方向
            page = self.correct_orientation(page)
            # 标准化到A4
            page = self.standardize_page(page)
            processed_pages.append(page)

        return True, processed_pages, ""
