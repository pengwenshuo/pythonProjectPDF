"""pytest 配置文件"""

import pytest
from pathlib import Path

# 添加项目根目录到 Python 路径
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))


def pytest_configure(config):
    """pytest 配置"""
    # 添加自定义标记
    config.addinivalue_line(
        "markers",
        "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers",
        "integration: marks tests as integration tests"
    )


@pytest.fixture
def sample_pdf_files(tmp_path):
    """创建示例 PDF 文件用于测试"""
    files = []
    for i in range(3):
        file_path = tmp_path / f"test_{i}.pdf"
        file_path.write_text(f"PDF content {i}")
        files.append(file_path)
    return files


@pytest.fixture
def sample_image_files(tmp_path):
    """创建示例图片文件用于测试"""
    files = []
    for i, ext in enumerate(['.jpg', '.png', '.bmp']):
        file_path = tmp_path / f"image_{i}{ext}"
        file_path.write_bytes(b"fake image content")
        files.append(file_path)
    return files