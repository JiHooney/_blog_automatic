"""
브라우저 관리
Selenium WebDriver 인스턴스 생성 및 관리
"""
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv
from loguru import logger

load_dotenv()


class BrowserManager:
    """Selenium 브라우저 관리 클래스"""
    
    def __init__(self, headless: bool = None):
        """
        Args:
            headless: 헤드리스 모드 여부. None이면 환경변수에서 로드
        """
        if headless is None:
            headless = os.getenv("BROWSER_HEADLESS", "false").lower() == "true"
        
        self.headless = headless
        self.driver = None
    
    def create_driver(self) -> webdriver.Chrome:
        """Chrome WebDriver 생성
        
        Returns:
            Chrome WebDriver 인스턴스
        """
        options = Options()
        
        if self.headless:
            options.add_argument("--headless=new")
        
        # 기본 옵션
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        
        # 자동화 탐지 방지
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        
        # User-Agent 설정
        options.add_argument(
            "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        # ChromeDriver 자동 설치 및 생성
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        
        # 자동화 탐지 방지 스크립트
        self.driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {
                "source": """
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    })
                """
            }
        )
        
        logger.info(f"🌐 브라우저 생성 완료 (headless: {self.headless})")
        return self.driver
    
    def quit(self):
        """브라우저 종료"""
        if self.driver:
            self.driver.quit()
            self.driver = None
            logger.info("🌐 브라우저 종료")
    
    def __enter__(self):
        """Context manager 진입"""
        self.create_driver()
        return self.driver
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager 종료"""
        self.quit()
