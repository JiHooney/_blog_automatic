"""
네이버 블로그 자동화
Selenium을 사용하여 네이버 블로그에 글 발행
"""
import os
import re
import time
from pathlib import Path
from typing import Optional, List
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from dotenv import load_dotenv
from loguru import logger

from .base import BasePublisher
from ..utils.browser import BrowserManager

load_dotenv()


class NaverPublisher(BasePublisher):
    """네이버 블로그 발행자"""
    
    PLATFORM_NAME = "naver"
    
    # 네이버 URL
    LOGIN_URL = "https://nid.naver.com/nidlogin.login"
    BLOG_HOME_URL = "https://blog.naver.com/{blog_id}"
    BLOG_WRITE_URL = "https://blog.naver.com/{blog_id}/postwrite"
    
    def __init__(self, headless: bool = None):
        """
        Args:
            headless: 헤드리스 모드 여부
        """
        super().__init__()
        self.browser_manager = BrowserManager(headless=headless)
        self.naver_id = os.getenv("NAVER_ID")
        self.naver_password = os.getenv("NAVER_PASSWORD")
        
        if not self.naver_id or not self.naver_password:
            raise ValueError("NAVER_ID 또는 NAVER_PASSWORD가 설정되지 않았습니다.")
    
    def login(self) -> bool:
        """네이버 로그인
        
        Returns:
            로그인 성공 여부
        """
        try:
            self.driver = self.browser_manager.create_driver()
            self.driver.get(self.LOGIN_URL)
            time.sleep(2)
            
            logger.info("🔐 네이버 로그인 시도 중...")
            
            # 아이디 입력 (JavaScript로 직접 입력 - 보안 키패드 우회)
            self.driver.execute_script(
                f"document.getElementById('id').value = '{self.naver_id}'"
            )
            time.sleep(0.5)
            
            # 비밀번호 입력
            self.driver.execute_script(
                f"document.getElementById('pw').value = '{self.naver_password}'"
            )
            time.sleep(0.5)
            
            # 로그인 버튼 클릭
            login_btn = self.driver.find_element(By.ID, "log.login")
            login_btn.click()
            
            time.sleep(3)
            
            # 로그인 성공 확인
            if "nid.naver.com" not in self.driver.current_url:
                self.is_logged_in = True
                logger.success("✅ 네이버 로그인 성공")
                return True
            else:
                # 캡차나 2차 인증이 필요할 수 있음
                logger.warning("⚠️ 추가 인증이 필요할 수 있습니다. 브라우저를 확인해주세요.")
                # 수동 인증을 위해 대기
                input("인증 완료 후 Enter를 눌러주세요...")
                self.is_logged_in = True
                return True
                
        except Exception as e:
            logger.error(f"❌ 네이버 로그인 실패: {e}")
            return False
    
    def publish(
        self,
        title: str,
        content: str,
        category: Optional[str] = None,
        tags: Optional[list] = None,
        images: Optional[list] = None
    ) -> bool:
        """네이버 블로그에 글 발행
        
        Args:
            title: 글 제목
            content: 글 내용
            category: 카테고리 (사용하지 않음 - 네이버는 수동 설정 필요)
            tags: 태그 목록
            images: 이미지 파일 경로 목록
        
        Returns:
            발행 성공 여부
        """
        if not self.is_logged_in:
            if not self.login():
                return False
        
        try:
            # 글쓰기 페이지로 이동
            write_url = self.BLOG_WRITE_URL.format(blog_id=self.naver_id)
            self.driver.get(write_url)
            time.sleep(2)  # 기본 로딩 대기 (4초 → 2초로 단축)
            
            logger.info(f"📝 네이버 블로그 글 작성 중: {title}")
            
            from selenium.webdriver.common.action_chains import ActionChains
            
            # JavaScript로 빠르게 팝업/도움말 닫기
            self.driver.execute_script("""
                // 도움말 패널 숨기기
                var helpPanel = document.querySelector('[class*="help-panel"], [class*="helpPanel"], .se-help-panel');
                if (helpPanel) helpPanel.style.display = 'none';
                
                // 도움말 닫기 버튼 클릭
                var closeButtons = document.querySelectorAll('[class*="close"], [class*="Close"]');
                closeButtons.forEach(function(btn) {
                    if (btn.offsetParent !== null) {  // visible check
                        try { btn.click(); } catch(e) {}
                    }
                });
                
                // 모달/오버레이 숨기기
                var modals = document.querySelectorAll('[class*="modal"], [class*="overlay"], [class*="popup"]');
                modals.forEach(function(m) {
                    if (m.style) m.style.display = 'none';
                });
            """)
            time.sleep(0.5)
            
            # "작성중인 글" 복구 팝업 처리 (있을 경우만)
            try:
                # 빠른 체크 - 1초만 대기
                btn = WebDriverWait(self.driver, 1).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '새로 작성') or contains(text(), '아니오')]"))
                )
                if btn:
                    btn.click()
                    logger.info("✅ '작성중인 글' 팝업 - 새로 작성 선택")
                    time.sleep(0.5)
            except:
                pass  # 팝업이 없으면 빠르게 통과
            
            # ESC로 남은 팝업 닫기
            ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
            time.sleep(0.3)
            
            # 제목 영역 클릭 - "제목" 텍스트가 있는 영역
            # 네이버 에디터는 클릭으로 활성화 필요
            title_area = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".se-documentTitle, .se-title-text, .se-component.se-documentTitle"))
            )
            
            # ActionChains로 클릭
            actions = ActionChains(self.driver)
            actions.move_to_element(title_area).click().perform()
            time.sleep(0.5)
            
            # 제목 입력
            actions = ActionChains(self.driver)
            actions.send_keys(title).perform()
            time.sleep(0.5)  # 1초 → 0.5초
            
            logger.info(f"✅ 제목 입력 완료: {title}")
            
            # 본문 영역 직접 클릭 (Tab 대신)
            # 본문 영역: "글감과 함께 나의 일상을 기록해보세요!" 플레이스홀더가 있는 영역
            content_area = None
            content_selectors = [
                ".se-component.se-text.se-l-default",
                ".se-text-paragraph",
                "[data-placeholder]",
                ".se-section-text",
                ".se-component-content"
            ]
            
            for selector in content_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for elem in elements:
                        # 제목 영역이 아닌 본문 영역 찾기
                        try:
                            class_attr = elem.get_attribute('class') or ''
                            parent_class = elem.find_element(By.XPATH, "..").get_attribute('class') or ''
                            if 'title' not in class_attr.lower() and 'title' not in parent_class.lower():
                                if 'documentTitle' not in class_attr and 'documentTitle' not in parent_class:
                                    content_area = elem
                                    break
                        except:
                            content_area = elem
                            break
                    if content_area:
                        break
                except:
                    continue
            
            if content_area:
                actions = ActionChains(self.driver)
                actions.move_to_element(content_area).click().perform()
                time.sleep(0.3)  # 0.5초 → 0.3초
                logger.info("✅ 본문 영역 클릭 완료")
            else:
                # 본문 영역을 못 찾으면 Tab으로 이동 시도
                actions = ActionChains(self.driver)
                actions.send_keys(Keys.TAB).perform()
                time.sleep(0.3)
            
            # 이미지 파일 매핑 생성
            image_map = {}
            if images:
                for img_path in images:
                    img_name = Path(img_path).name.lower()
                    image_map[img_name] = img_path
                logger.info(f"📷 이미지 {len(image_map)}개 로드: {list(image_map.keys())}")
            
            # 본문 입력 - 코드 블록 먼저 분리 후 문단별로 입력
            # 마크다운 코드 블록 패턴: ```언어\n코드\n```
            code_block_pattern = re.compile(r'```(\w*)\n(.*?)```', re.DOTALL)
            
            # 코드 블록을 플레이스홀더로 치환하고 나중에 처리
            code_blocks = []
            def replace_code_block(match):
                lang = match.group(1) or ''
                code = match.group(2).strip()
                idx = len(code_blocks)
                code_blocks.append({'lang': lang, 'code': code})
                return f'__CODE_BLOCK_{idx}__'
            
            content_with_placeholders = code_block_pattern.sub(replace_code_block, content)
            
            paragraphs = content_with_placeholders.split('\n\n')
            last_was_naver_map = False  # 이전 문단이 네이버 지도 링크였는지 추적
            
            for para in paragraphs:
                if para.strip():
                    text = para.strip()
                    
                    # 코드 블록 플레이스홀더 확인
                    code_placeholder_match = re.match(r'__CODE_BLOCK_(\d+)__', text)
                    if code_placeholder_match:
                        idx = int(code_placeholder_match.group(1))
                        block = code_blocks[idx]
                        if self._insert_code_block(block['code'], block['lang']):
                            logger.info(f"💻 코드 블록 삽입 완료 (언어: {block['lang'] or 'plain'})")
                        else:
                            # 소스코드 블록 삽입 실패 시 일반 텍스트로 입력
                            actions = ActionChains(self.driver)
                            actions.send_keys(f"[코드]\n{block['code']}\n[/코드]").send_keys(Keys.ENTER).send_keys(Keys.ENTER).perform()
                            logger.warning("⚠️ 소스코드 블록 대신 일반 텍스트로 입력됨")
                        time.sleep(0.5)
                        continue
                    
                    # [IMAGE: 파일명] 패턴 확인
                    image_match = re.match(r'\[IMAGE:\s*([^\]]+)\]', text, re.IGNORECASE)
                    if image_match:
                        # 네이버 지도 링크 직후 이미지 업로드 시 대기
                        if last_was_naver_map:
                            logger.info("⏳ 네이버 지도 로딩 대기 중...")
                            time.sleep(5)
                            last_was_naver_map = False
                        
                        image_name = image_match.group(1).strip()
                        # 이미지 업로드 시도
                        if self._upload_image(image_name, image_map):
                            logger.info(f"📷 이미지 업로드 완료: {image_name}")
                        else:
                            # 이미지 업로드 실패 시 설명 텍스트만 입력
                            actions = ActionChains(self.driver)
                            actions.send_keys(f"[사진: {image_name}]").send_keys(Keys.ENTER).send_keys(Keys.ENTER).perform()
                        time.sleep(0.5)
                        continue
                    
                    # 마크다운 헤딩 처리
                    if text.startswith('### '):
                        text = text[4:]
                    elif text.startswith('## '):
                        text = text[3:]
                    elif text.startswith('# '):
                        text = text[2:]
                    
                    # 볼드 마크다운 제거
                    text = text.replace('**', '')
                    
                    # 네이버 지도 링크 감지 (naver.me 또는 map.naver.com)
                    if 'naver.me' in text or 'map.naver.com' in text:
                        last_was_naver_map = True
                        logger.info("🗺️ 네이버 지도 링크 감지")
                    else:
                        last_was_naver_map = False
                    
                    actions = ActionChains(self.driver)
                    actions.send_keys(text).send_keys(Keys.ENTER).send_keys(Keys.ENTER).perform()
                    time.sleep(0.1)  # 0.2초 + 0.1초 → 0.1초로 통합
            
            time.sleep(1)  # 2초 → 1초
            logger.info("✅ 본문 입력 완료")
            
            # 발행 전 도움말 패널 닫기 (발행 버튼을 가릴 수 있음)
            try:
                # JavaScript로 도움말 패널 숨기기
                self.driver.execute_script("""
                    var helpPanel = document.querySelector('.se-help-panel, [class*="help-panel"], [class*="helpPanel"]');
                    if (helpPanel) helpPanel.style.display = 'none';
                    
                    var helpTitle = document.querySelector('.se-help-title');
                    if (helpTitle) helpTitle.parentElement.style.display = 'none';
                """)
                time.sleep(0.3)
            except:
                pass
            
            # ESC 키로 팝업 닫기
            ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
            time.sleep(0.5)
            
            # 발행 버튼 클릭 - 오른쪽 상단의 초록색 "발행" 버튼
            # 에러 메시지에서 확인된 클래스: publish_btn__m9KHH
            publish_btn = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "button[class*='publish_btn'], button[class*='publish']"))
            )
            
            # JavaScript로 직접 클릭 (다른 요소가 가려도 클릭 가능)
            self.driver.execute_script("arguments[0].click();", publish_btn)
            logger.info("✅ 발행 버튼 클릭 - 발행 설정 팝업 열기")
            time.sleep(2)
            
            # 카테고리 선택 (발행 팝업이 열린 후)
            if category:
                self._select_category(category)
                time.sleep(0.5)
            
            # 태그 입력 (발행 팝업이 열린 후)
            if tags:
                self._add_tags(tags)
                time.sleep(1)
            
            # 최종 발행 버튼 클릭 (팝업 내 발행 버튼)
            # 팝업 내 최종 발행 버튼 찾기
            # 스크린샷에서 보이는 "✓ 발행" 버튼
            time.sleep(1)
            
            final_publish_selectors = [
                "div[class*='layer_btn_area'] button",
                "button[class*='confirm_btn']",
                "div[class*='layer_publish'] button[class*='ok']",
                "div[class*='layer_publish'] button[class*='confirm']",
                "//button[contains(text(), '발행') and ancestor::div[contains(@class, 'layer')]]",
                "//button[text()='발행']"
            ]
            
            final_btn = None
            for selector in final_publish_selectors:
                try:
                    if selector.startswith('//'):
                        final_btn = self.driver.find_element(By.XPATH, selector)
                    else:
                        final_btn = WebDriverWait(self.driver, 2).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                    if final_btn:
                        break
                except:
                    continue
            
            if final_btn:
                self.driver.execute_script("arguments[0].click();", final_btn)
                logger.info("✅ 최종 발행 버튼 클릭")
            else:
                # 모든 버튼 중에서 '발행' 텍스트가 있는 버튼 찾기
                buttons = self.driver.find_elements(By.TAG_NAME, "button")
                for btn in buttons:
                    try:
                        if '발행' in btn.text and btn.is_displayed():
                            # 상단 발행 버튼이 아닌 팝업 내 버튼인지 확인
                            btn_location = btn.location
                            if btn_location['y'] > 300:  # 화면 하단에 있는 버튼
                                self.driver.execute_script("arguments[0].click();", btn)
                                logger.info("✅ 최종 발행 버튼 클릭 (텍스트 검색)")
                                break
                    except:
                        continue
            
            time.sleep(3)
            logger.success(f"✅ 네이버 블로그 발행 완료: {title}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 네이버 블로그 발행 실패: {e}")
            # 스크린샷 저장
            try:
                self.driver.save_screenshot("naver_error.png")
                logger.info("📸 에러 스크린샷 저장: naver_error.png")
            except:
                pass
            return False
    
    def _select_category(self, category: str):
        """카테고리 선택"""
        try:
            from selenium.webdriver.common.action_chains import ActionChains
            
            # 카테고리 선택 버튼 클릭하여 드롭다운 열기
            # HTML: button class="selectbox_button__jb1Dt"
            category_btn = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[class*='selectbox_button']"))
            )
            
            # 현재 선택된 카테고리 확인
            try:
                current_text = category_btn.find_element(By.CSS_SELECTOR, "span[class*='text']").text.strip()
                if category in current_text:
                    logger.info(f"📁 카테고리 이미 선택됨: {category}")
                    return True
            except:
                pass
            
            category_btn.click()
            time.sleep(0.5)
            
            # 드롭다운이 열린 후 카테고리 텍스트를 포함한 요소 찾기
            # XPath로 텍스트 검색
            try:
                # 방법 1: 텍스트를 포함한 클릭 가능한 요소 찾기
                category_item = WebDriverWait(self.driver, 3).until(
                    EC.element_to_be_clickable((By.XPATH, f"//*[contains(text(), '{category}') and (self::button or self::li or self::div or self::span)]"))
                )
                
                # 클릭 가능한 부모 요소 찾기 (span인 경우 부모 클릭)
                tag_name = category_item.tag_name.lower()
                if tag_name == 'span':
                    # 부모 요소 클릭 시도
                    parent = category_item.find_element(By.XPATH, "..")
                    parent.click()
                else:
                    category_item.click()
                    
                logger.info(f"� 카테고리 선택: {category}")
                time.sleep(0.5)
                return True
                
            except Exception as e1:
                logger.warning(f"방법1 실패: {e1}")
                
                # 방법 2: 모든 li 또는 button 중에서 텍스트 매칭
                try:
                    all_items = self.driver.find_elements(By.CSS_SELECTOR, "li, button, [role='option'], [role='menuitem']")
                    for item in all_items:
                        try:
                            item_text = item.text.strip()
                            if category in item_text and item.is_displayed():
                                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", item)
                                time.sleep(0.1)
                                item.click()
                                logger.info(f"📁 카테고리 선택: {category}")
                                time.sleep(0.5)
                                return True
                        except:
                            continue
                except Exception as e2:
                    logger.warning(f"방법2 실패: {e2}")
            
            logger.warning(f"⚠️ 카테고리를 찾을 수 없음: {category}")
            # ESC로 드롭다운 닫기
            ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
            return False
            
        except Exception as e:
            logger.warning(f"⚠️ 카테고리 선택 실패: {e}")
            return False
    
    def _add_tags(self, tags: list):
        """태그 추가"""
        try:
            from selenium.webdriver.common.action_chains import ActionChains
            
            # 태그 입력 영역 찾기 - 발행 팝업 내부
            # HTML: div class="tag_area__VlMvI" > div class="tag_textarea__CD7pC"
            tag_selectors = [
                "div[class*='tag_textarea']",
                "div[class*='tag_area'] div[class*='textarea']",
                ".tag_textarea__CD7pC",
                "div[class*='tag_input']",
                "[class*='tag'] [contenteditable]",
                "div[class*='tag_area']"
            ]
            
            tag_input = None
            for selector in tag_selectors:
                try:
                    tag_input = WebDriverWait(self.driver, 3).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    if tag_input:
                        break
                except:
                    continue
            
            if tag_input:
                # 태그 영역 클릭
                tag_input.click()
                time.sleep(0.3)
                
                for tag in tags[:30]:  # 최대 30개
                    actions = ActionChains(self.driver)
                    actions.send_keys(tag).perform()
                    time.sleep(0.1)
                    actions = ActionChains(self.driver)
                    actions.send_keys(Keys.ENTER).perform()
                    time.sleep(0.2)
                
                logger.info(f"🏷️ 태그 추가: {', '.join(tags[:30])}")
            else:
                logger.warning("⚠️ 태그 입력 영역을 찾지 못했습니다.")
                
        except Exception as e:
            logger.warning(f"⚠️ 태그 추가 실패: {e}")
    
    def _markdown_to_html(self, markdown_text: str) -> str:
        """마크다운을 간단한 HTML로 변환"""
        import re
        
        html = markdown_text
        
        # 헤딩
        html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
        html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
        
        # 볼드
        html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
        
        # 이미지 마커는 그대로 유지
        # [IMAGE: ...] 형식
        
        # 문단
        paragraphs = html.split('\n\n')
        html = ''.join(f'<p>{p}</p>' for p in paragraphs if p.strip())
        
        return html
    
    def _upload_image(self, image_name: str, image_map: dict) -> bool:
        """이미지 업로드
        
        Args:
            image_name: 이미지 파일명 또는 설명
            image_map: {파일명: 경로} 딕셔너리
        
        Returns:
            업로드 성공 여부
        """
        from selenium.webdriver.common.action_chains import ActionChains
        
        # 이미지 업로드 전 에디터 안정화 대기
        time.sleep(1)
        
        # 재시도 로직 (최대 3회)
        for attempt in range(3):
            try:
                # 이미지 파일 찾기
                image_path = None
                image_name_lower = image_name.lower().replace(' ', '')
                
                # 정확한 파일명 매칭 또는 부분 매칭
                for name, path in image_map.items():
                    name_clean = name.lower().replace(' ', '')
                    # 정확한 매칭
                    if image_name_lower == name_clean:
                        image_path = path
                        break
                    # 부분 매칭 (파일명에 검색어가 포함되거나 검색어에 파일명이 포함)
                    if image_name_lower in name_clean or name_clean in image_name_lower:
                        image_path = path
                        break
                    # 숫자 매칭 (예: "2.내부인테리어.jpg" vs "2.내부인테리어.jpg")
                    if name_clean.startswith(image_name_lower.split('.')[0] + '.'):
                        image_path = path
                        break
                
                if not image_path or not Path(image_path).exists():
                    logger.warning(f"⚠️ 이미지 파일을 찾을 수 없음: {image_name}")
                    return False
                
                if attempt == 0:
                    logger.info(f"📷 이미지 업로드 시도: {image_path}")
                else:
                    logger.info(f"📷 이미지 업로드 재시도 ({attempt + 1}/3): {image_path}")
                
                # ESC 키로 팝업/오버레이 닫기
                ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
                time.sleep(0.5)
                
                # 현재 포커스된 영역 클릭하여 에디터 활성화
                try:
                    active_element = self.driver.switch_to.active_element
                    ActionChains(self.driver).move_to_element(active_element).click().perform()
                    time.sleep(0.3)
                except:
                    pass
                
                # 네이버 에디터에서 사진 버튼 클릭
                # 툴바에서 사진 아이콘 찾기
                photo_btn_selectors = [
                    "button[data-name='image']",
                    "[class*='se-toolbar'] button[class*='image']",
                    "button.se-image-toolbar-button",
                    "[class*='photo']",
                    "[data-tooltip*='사진']"
                ]
                
                photo_btn = None
                for selector in photo_btn_selectors:
                    try:
                        photo_btn = WebDriverWait(self.driver, 2).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                        if photo_btn:
                            break
                    except:
                        continue
                
                if not photo_btn:
                    # 대체 방법: 파일 input 직접 사용
                    logger.info("📷 파일 input 직접 사용 시도")
                    
                    # 숨겨진 파일 input 찾기 또는 생성
                    try:
                        file_input = self.driver.find_element(By.CSS_SELECTOR, "input[type='file'][accept*='image']")
                    except:
                        # JavaScript로 파일 input 생성
                        self.driver.execute_script("""
                            var input = document.createElement('input');
                            input.type = 'file';
                            input.id = 'temp_image_upload';
                            input.style.display = 'none';
                            input.accept = 'image/*';
                            document.body.appendChild(input);
                        """)
                        file_input = self.driver.find_element(By.ID, "temp_image_upload")
                    
                    # 파일 경로 전송
                    file_input.send_keys(str(Path(image_path).absolute()))
                    time.sleep(3)
                    
                    logger.info(f"✅ 이미지 업로드 완료: {image_name}")
                    return True
                else:
                    # 사진 버튼 클릭
                    self.driver.execute_script("arguments[0].click();", photo_btn)
                    time.sleep(1)
                    
                    # 파일 선택 다이얼로그
                    file_input = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']"))
                    )
                    file_input.send_keys(str(Path(image_path).absolute()))
                    time.sleep(3)
                    
                    logger.info(f"✅ 이미지 업로드 완료: {image_name}")
                    return True
                    
            except Exception as e:
                logger.warning(f"⚠️ 이미지 업로드 시도 {attempt + 1} 실패: {e}")
                if attempt < 2:
                    time.sleep(2)  # 재시도 전 대기
                    continue
                return False
        
        return False
    
    def _insert_code_block(self, code: str, language: str = "") -> bool:
        """네이버 에디터에 소스코드 블록 삽입
        
        Args:
            code: 삽입할 코드 내용
            language: 프로그래밍 언어 (선택)
        
        Returns:
            삽입 성공 여부
        """
        from selenium.webdriver.common.action_chains import ActionChains
        
        try:
            logger.info(f"💻 소스코드 블록 삽입 시도 (언어: {language or 'plain'})")
            
            # 1. 툴바에서 '소스코드' 버튼 찾기 및 클릭
            code_btn_selectors = [
                "button[data-name='code']",
                ".se-code-toolbar-button",
                "button.se-document-toolbar-basic-button[data-name='code']",
                "[class*='toolbar'] button[class*='code']",
                "button[data-log='dot.code']",
            ]
            
            code_btn = None
            for selector in code_btn_selectors:
                try:
                    code_btn = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    if code_btn:
                        break
                except:
                    continue
            
            if not code_btn:
                # XPath로 '소스코드' 텍스트가 있는 버튼 찾기
                try:
                    code_btn = self.driver.find_element(
                        By.XPATH, 
                        "//button[contains(@class, 'toolbar') and .//span[contains(text(), '소스코드')]]"
                    )
                except:
                    pass
            
            if not code_btn:
                logger.warning("⚠️ 소스코드 버튼을 찾을 수 없음 - 일반 텍스트로 삽입")
                return False
            
            # 버튼 클릭
            self.driver.execute_script("arguments[0].click();", code_btn)
            time.sleep(1)
            
            # 2. 소스코드 입력 영역 찾기 (textarea 또는 contenteditable)
            code_input_selectors = [
                ".se-code-source-editor",
                "textarea.se-code-source-editor",
                ".se-module-code textarea",
                ".se-section-code textarea",
                "[class*='code'] textarea",
            ]
            
            code_input = None
            for selector in code_input_selectors:
                try:
                    code_input = WebDriverWait(self.driver, 3).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    if code_input:
                        break
                except:
                    continue
            
            if code_input:
                # textarea에 직접 입력
                code_input.click()
                time.sleep(0.3)
                
                # JavaScript로 값 설정 (긴 코드도 빠르게 입력)
                self.driver.execute_script(
                    "arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('input', {bubbles: true}));",
                    code_input,
                    code
                )
                time.sleep(0.5)
                
                logger.info("✅ 소스코드 블록 삽입 완료")
            else:
                # contenteditable 영역에 입력 시도
                try:
                    code_area = self.driver.find_element(By.CSS_SELECTOR, ".se-module-code, .se-section-code")
                    code_area.click()
                    time.sleep(0.3)
                    
                    actions = ActionChains(self.driver)
                    # 코드를 줄 단위로 입력
                    for line in code.split('\n'):
                        actions.send_keys(line).send_keys(Keys.ENTER)
                    actions.perform()
                    time.sleep(0.5)
                    
                    logger.info("✅ 소스코드 블록 삽입 완료 (contenteditable)")
                except Exception as e:
                    logger.warning(f"⚠️ 소스코드 영역 입력 실패: {e}")
                    return False
            
            # 3. 코드 블록 외부로 커서 이동 (ESC 또는 클릭)
            ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
            time.sleep(0.3)
            
            # 본문 영역 클릭하여 커서 이동
            try:
                # 코드 블록 다음에 새 텍스트 영역 생성을 위해 Enter
                ActionChains(self.driver).send_keys(Keys.ENTER).perform()
                time.sleep(0.3)
            except:
                pass
            
            return True
            
        except Exception as e:
            logger.warning(f"⚠️ 소스코드 블록 삽입 실패: {e}")
            return False

    def logout(self):
        """로그아웃 및 브라우저 종료"""
        self.browser_manager.quit()
        self.is_logged_in = False
        self.driver = None
        logger.info("👋 네이버 로그아웃 완료")
