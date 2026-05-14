"""com_core 模块的单元测试"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

# 添加项目根目录到 Python 路径
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from pdfgj.com_core import _is_com_error, _classify_com_error, _precheck_file


class TestIsComError:
    """_is_com_error 函数的测试类"""

    def test_com_error_type(self):
        """测试 com_error 类型"""
        # 创建自定义异常类模拟 com_error
        class com_error(Exception):
            pass

        # 修改类的 __qualname__ 属性
        com_error.__qualname__ = 'com_error'
        error = com_error("test")
        assert _is_com_error(error) is True

    def test_pywintypes_error(self):
        """测试 pywintypes.error 类型"""
        # 创建自定义异常类模拟 pywintypes.error
        class error(Exception):
            pass

        # 修改类的属性
        error.__module__ = 'pywintypes'
        error.__qualname__ = 'error'
        error_instance = error("test")
        assert _is_com_error(error_instance) is True

    def test_other_error(self):
        """测试其他异常类型"""
        error = ValueError("test")
        assert _is_com_error(error) is False

    def test_real_exception(self):
        """测试真实的 Python 异常"""
        error = ValueError("test error")
        assert _is_com_error(error) is False

    def test_real_type_error(self):
        """测试真实的 TypeError"""
        error = TypeError("test error")
        assert _is_com_error(error) is False


class TestClassifyComError:
    """_classify_com_error 函数的测试类"""

    def test_known_error_code(self):
        """测试已知错误码"""
        error = Exception("Error 0x800a175d occurred")
        result = _classify_com_error(error)
        assert "文档设置了修改密码" in result

    def test_file_locked_error(self):
        """测试文件锁定错误"""
        error = Exception("Error 0x800a1391 occurred")
        result = _classify_com_error(error)
        assert "文件正在被其他程序使用" in result

    def test_file_not_found_error(self):
        """测试文件不存在错误"""
        error = Exception("Error 0x800a03ec occurred")
        result = _classify_com_error(error)
        assert "文件不存在或路径无效" in result

    def test_unknown_error(self):
        """测试未知错误"""
        error = Exception("Some unknown error occurred")
        result = _classify_com_error(error)
        assert "COM 错误" in result
        assert "Some unknown error occurred" in result

    def test_error_with_details(self):
        """测试带有详细信息的错误"""
        error = Exception("Error 0x800a136b: format mismatch")
        result = _classify_com_error(error)
        assert "文件格式不兼容" in result


class TestPrecheckFile:
    """_precheck_file 函数的测试类"""

    def test_nonexistent_file(self):
        """测试不存在的文件"""
        result = _precheck_file(Path("nonexistent_file.txt"))
        assert result is not None
        assert "文件不存在" in result

    def test_directory_path(self):
        """测试目录路径"""
        # 使用当前目录作为测试
        result = _precheck_file(Path("."))
        assert result is not None
        assert "路径不是文件" in result

    def test_permission_error(self, tmp_path, monkeypatch):
        """测试权限错误（改为警告）"""
        test_file = tmp_path / "test.txt"
        test_file.touch()

        def mock_open(*args, **kwargs):
            raise PermissionError("Access denied")

        monkeypatch.setattr("builtins.open", mock_open)
        result = _precheck_file(test_file)
        # 权限错误应该返回 None（警告，不阻断）
        assert result is None

    def test_os_error(self, tmp_path, monkeypatch):
        """测试 OS 错误（改为警告）"""
        test_file = tmp_path / "test.txt"
        test_file.touch()

        def mock_open(*args, **kwargs):
            raise OSError("OS error")

        monkeypatch.setattr("builtins.open", mock_open)
        result = _precheck_file(test_file)
        # OS错误应该返回 None（警告，不阻断）
        assert result is None


class TestGetComPid:
    """_get_com_pid 函数的测试类"""

    def test_get_pid_success(self):
        """测试成功获取PID"""
        from pdfgj.com_core import _get_com_pid

        class MockApp:
            PID = 12345

        result = _get_com_pid(MockApp())
        assert result == 12345

    def test_get_pid_failure(self):
        """测试获取PID失败"""
        from pdfgj.com_core import _get_com_pid

        class MockApp:
            pass

        result = _get_com_pid(MockApp())
        assert result is None


class TestBatchConvert:
    """_batch_convert 函数的测试类"""

    def test_batch_convert_no_win32(self, monkeypatch):
        """测试缺少 pywin32"""
        from pdfgj import com_core
        monkeypatch.setattr(com_core, '_has_win32', False)

        result = com_core._batch_convert([Path("test.docx")], None, "Word")
        assert result == ["test.docx"]

    def test_batch_convert_runtime_error(self, monkeypatch):
        """测试运行时错误"""
        from pdfgj import com_core
        monkeypatch.setattr(com_core, '_has_win32', True)

        # 模拟一个会抛出 RuntimeError 的转换器
        class MockConverter:
            def __enter__(self):
                raise RuntimeError("测试错误")
            def __exit__(self, *args):
                pass

        result = com_core._batch_convert([Path("test.docx")], MockConverter, "Word")
        assert result == ["test.docx"]


class TestComQuit:
    """_com_quit 函数的测试类"""

    def test_com_quit_none_app(self):
        """测试 app 为 None"""
        from pdfgj.com_core import _com_quit
        _com_quit(None, "Word.Application")

    @patch('pdfgj.com_core.subprocess.run')
    @patch('pdfgj.com_core.time.sleep')
    def test_com_quit_normal_exit(self, mock_sleep, mock_run):
        """测试正常退出"""
        from pdfgj.com_core import _com_quit
        mock_app = MagicMock()
        # tasklist 显示进程已退出
        mock_run.return_value = MagicMock(stdout="", returncode=0)
        _com_quit(mock_app, "Word.Application")
        mock_app.Quit.assert_called_once()

    @patch('pdfgj.com_core.subprocess.run')
    @patch('pdfgj.com_core.time.sleep')
    @patch('pdfgj.com_core._get_com_pid', return_value=12345)
    def test_com_quit_force_kill_by_pid(self, mock_pid, mock_sleep, mock_run):
        """测试通过 PID 强制终止"""
        from pdfgj.com_core import _com_quit
        mock_app = MagicMock()
        # 第一次 tasklist 显示进程还在，kill 后 tasklist 显示已退出
        mock_run.side_effect = [
            MagicMock(stdout="WINWORD.EXE", returncode=0),  # 还在
            MagicMock(returncode=0),  # taskkill
            MagicMock(stdout="", returncode=0),  # 已退出
        ]
        _com_quit(mock_app, "Word.Application")
        mock_app.Quit.assert_called_once()

    @patch('pdfgj.com_core.subprocess.run')
    @patch('pdfgj.com_core.time.sleep')
    @patch('pdfgj.com_core._get_com_pid', return_value=None)
    def test_com_quit_no_pid_no_kill_office(self, mock_pid, mock_sleep, mock_run):
        """测试无 PID 且未授权 kill-office"""
        from pdfgj.com_core import _com_quit
        import pdfgj.utils
        pdfgj.utils._allow_kill_office = False

        mock_app = MagicMock()
        mock_run.return_value = MagicMock(stdout="WINWORD.EXE", returncode=0)
        _com_quit(mock_app, "Word.Application")
        mock_app.Quit.assert_called_once()
        pdfgj.utils._allow_kill_office = False

    @patch('pdfgj.com_core.subprocess.run')
    @patch('pdfgj.com_core.time.sleep')
    @patch('pdfgj.com_core._get_com_pid', return_value=None)
    def test_com_quit_no_pid_with_kill_office(self, mock_pid, mock_sleep, mock_run):
        """测试无 PID 且授权 kill-office"""
        from pdfgj.com_core import _com_quit
        import pdfgj.utils
        pdfgj.utils._allow_kill_office = True

        mock_app = MagicMock()
        # 进程名终止后 tasklist 显示已退出
        mock_run.side_effect = [
            MagicMock(stdout="WINWORD.EXE", returncode=0),  # 还在
            MagicMock(returncode=0),  # taskkill /IM
            MagicMock(stdout="", returncode=0),  # 已退出
        ]
        _com_quit(mock_app, "Word.Application")
        mock_app.Quit.assert_called_once()
        pdfgj.utils._allow_kill_office = False


class TestComConverter:
    """COMConverter 基类测试"""

    def test_com_converter_no_win32(self, monkeypatch):
        """测试缺少 pywin32"""
        from pdfgj import com_core
        monkeypatch.setattr(com_core, '_has_win32', False)
        with pytest.raises(RuntimeError, match="缺少 pywin32"):
            com_core.COMConverter()

    def test_com_converter_app_name_not_implemented(self):
        """测试 app_name 未实现"""
        with patch('pdfgj.com_core._has_win32', True), \
             patch('pdfgj.com_core.pythoncom'), \
             patch('pdfgj.com_core.DispatchEx'):
            from pdfgj.com_core import COMConverter
            converter = COMConverter()
            with pytest.raises(NotImplementedError):
                _ = converter.app_name

    def test_com_converter_setup_not_implemented(self):
        """测试 setup 未实现"""
        with patch('pdfgj.com_core._has_win32', True), \
             patch('pdfgj.com_core.pythoncom'), \
             patch('pdfgj.com_core.DispatchEx'):
            from pdfgj.com_core import COMConverter
            converter = COMConverter()
            with pytest.raises(NotImplementedError):
                converter.setup(MagicMock())

    def test_com_converter_convert_not_implemented(self):
        """测试 convert 未实现"""
        with patch('pdfgj.com_core._has_win32', True), \
             patch('pdfgj.com_core.pythoncom'), \
             patch('pdfgj.com_core.DispatchEx'):
            from pdfgj.com_core import COMConverter
            converter = COMConverter()
            with pytest.raises(NotImplementedError):
                converter.convert(Path("test.docx"))

    def test_com_converter_context_manager(self):
        """测试上下文管理器"""
        with patch('pdfgj.com_core._has_win32', True), \
             patch('pdfgj.com_core.pythoncom') as mock_com, \
             patch('pdfgj.com_core.DispatchEx') as mock_dispatch:
            mock_com.CoInitialize.return_value = 0
            from pdfgj.com_core import COMConverter

            class TestConverter(COMConverter):
                @property
                def app_name(self):
                    return 'Word.Application'
                def setup(self, app):
                    pass

            converter = TestConverter()
            with patch('pdfgj.com_core._com_quit'):
                with converter as ctx:
                    assert ctx is converter
                    mock_dispatch.assert_called_once_with('Word.Application')


class TestBatchConvert:
    """_batch_convert 函数的测试类"""

    def test_batch_convert_no_win32(self, monkeypatch):
        """测试缺少 pywin32"""
        from pdfgj import com_core
        monkeypatch.setattr(com_core, '_has_win32', False)

        result = com_core._batch_convert([Path("test.docx")], None, "Word")
        assert result == ["test.docx"]

    def test_batch_convert_runtime_error(self, monkeypatch):
        """测试运行时错误"""
        from pdfgj import com_core
        monkeypatch.setattr(com_core, '_has_win32', True)

        class MockConverter:
            def __enter__(self):
                raise RuntimeError("测试错误")
            def __exit__(self, *args):
                pass

        result = com_core._batch_convert([Path("test.docx")], MockConverter, "Word")
        assert result == ["test.docx"]

    def test_batch_convert_success(self, monkeypatch):
        """测试成功转换"""
        from pdfgj import com_core
        monkeypatch.setattr(com_core, '_has_win32', True)

        class MockConverter:
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
            def convert(self, path):
                return True

        with patch('pdfgj.com_core.utils._progress_bar'):
            result = com_core._batch_convert([Path("test.docx")], MockConverter, "Word")
            assert result == []

    def test_batch_convert_partial_failure(self, monkeypatch):
        """测试部分失败"""
        from pdfgj import com_core
        monkeypatch.setattr(com_core, '_has_win32', True)

        class MockConverter:
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
            def convert(self, path):
                return path.name != "fail.docx"

        with patch('pdfgj.com_core.utils._progress_bar'):
            files = [Path("ok.docx"), Path("fail.docx")]
            result = com_core._batch_convert(files, MockConverter, "Word")
            assert result == ["fail.docx"]

    def test_batch_convert_com_error(self, monkeypatch):
        """测试 COM 错误"""
        from pdfgj import com_core
        monkeypatch.setattr(com_core, '_has_win32', True)

        class MockConverter:
            def __enter__(self):
                raise Exception("Error 0x800a03ec")
            def __exit__(self, *args):
                pass

        with patch('pdfgj.com_core._is_com_error', return_value=True):
            result = com_core._batch_convert([Path("test.docx")], MockConverter, "Word")
            assert result == ["test.docx"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])