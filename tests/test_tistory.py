"""
티스토리 발행자 테스트
pytest tests/test_tistory.py -v
"""
import os
import sys
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# 프로젝트 루트를 path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestTistoryPublisher:
    """TistoryPublisher 단위 테스트"""
    
    @pytest.fixture
    def mock_env(self, monkeypatch):
        """테스트용 환경변수 설정"""
        monkeypatch.setenv("TISTORY_ID", "test@test.com")
        monkeypatch.setenv("TISTORY_PASSWORD", "testpassword")
        monkeypatch.setenv("TISTORY_BLOG_NAME", "testblog")
    
    def test_clipboard_method_selection_macos(self, mock_env):
        """macOS에서 올바른 클립보드 메서드 선택"""
        with patch('platform.system', return_value='Darwin'):
            with patch('src.publishers.tistory.BrowserManager'):
                from src.publishers.tistory import TistoryPublisher
                publisher = TistoryPublisher(headless=True)
                
                # _get_paste_key가 COMMAND를 반환해야 함
                from selenium.webdriver.common.keys import Keys
                assert publisher._get_paste_key() == Keys.COMMAND
    
    def test_clipboard_method_selection_windows(self, mock_env):
        """Windows에서 올바른 클립보드 메서드 선택"""
        with patch('platform.system', return_value='Windows'):
            with patch('src.publishers.tistory.BrowserManager'):
                from src.publishers.tistory import TistoryPublisher
                publisher = TistoryPublisher(headless=True)
                
                # _get_paste_key가 CONTROL을 반환해야 함
                from selenium.webdriver.common.keys import Keys
                assert publisher._get_paste_key() == Keys.CONTROL
    
    def test_clipboard_method_selection_linux(self, mock_env):
        """Linux에서 올바른 클립보드 메서드 선택"""
        with patch('platform.system', return_value='Linux'):
            with patch('src.publishers.tistory.BrowserManager'):
                from src.publishers.tistory import TistoryPublisher
                publisher = TistoryPublisher(headless=True)
                
                # _get_paste_key가 CONTROL을 반환해야 함
                from selenium.webdriver.common.keys import Keys
                assert publisher._get_paste_key() == Keys.CONTROL
    
    def test_missing_credentials(self, monkeypatch):
        """환경변수 미설정 시 예외 발생"""
        monkeypatch.delenv("TISTORY_ID", raising=False)
        monkeypatch.delenv("TISTORY_PASSWORD", raising=False)
        monkeypatch.delenv("TISTORY_BLOG_NAME", raising=False)
        
        with patch('src.publishers.tistory.BrowserManager'):
            from src.publishers.tistory import TistoryPublisher
            with pytest.raises(ValueError):
                TistoryPublisher(headless=True)


class TestImageResize:
    """이미지 리사이즈 관련 테스트"""
    
    def test_large_image_detection(self, tmp_path):
        """4MB 이상 이미지 감지"""
        # 큰 더미 파일 생성
        large_file = tmp_path / "large.jpg"
        large_file.write_bytes(b"0" * (5 * 1024 * 1024))  # 5MB
        
        file_size_mb = large_file.stat().st_size / (1024 * 1024)
        assert file_size_mb > 4


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
