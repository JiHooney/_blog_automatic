"""
티스토리 자동화
Selenium을 사용하여 티스토리에 글 발행
"""
import os
import time
from pathlib import Path
from typing import Optional
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


class TistoryPublisher(BasePublisher):
    """티스토리 발행자"""
    
    PLATFORM_NAME = "tistory"
    
    # 티스토리 URL
    LOGIN_URL = "https://www.tistory.com/auth/login"
    BLOG_WRITE_URL = "https://{blog_name}.tistory.com/manage/newpost"  # 블로그별 글쓰기 URL
    
    def __init__(self, headless: bool = None):
        """
        Args:
            headless: 헤드리스 모드 여부
        """
        super().__init__()
        self.browser_manager = BrowserManager(headless=headless)
        self.tistory_id = os.getenv("TISTORY_ID")
        self.tistory_password = os.getenv("TISTORY_PASSWORD")
        self.blog_name = os.getenv("TISTORY_BLOG_NAME")
        
        if not self.tistory_id or not self.tistory_password:
            raise ValueError("TISTORY_ID 또는 TISTORY_PASSWORD가 설정되지 않았습니다.")
        if not self.blog_name:
            raise ValueError("TISTORY_BLOG_NAME이 설정되지 않았습니다.")
    
    def login(self) -> bool:
        """티스토리 로그인 (카카오 계정)
        
        Returns:
            로그인 성공 여부
        """
        try:
            self.driver = self.browser_manager.create_driver()
            self.driver.get(self.LOGIN_URL)
            time.sleep(2)
            
            logger.info("🔐 티스토리 로그인 시도 중...")
            
            # 카카오 로그인 버튼 클릭
            kakao_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".btn_login.link_kakao_id"))
            )
            kakao_btn.click()
            time.sleep(2)
            
            # 카카오 로그인 페이지에서 로그인
            # 이메일/비밀번호 입력
            try:
                email_input = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='loginId']"))
                )
                email_input.clear()
                email_input.send_keys(self.tistory_id)
                time.sleep(0.5)
                
                password_input = self.driver.find_element(By.CSS_SELECTOR, "input[name='password']")
                password_input.clear()
                password_input.send_keys(self.tistory_password)
                time.sleep(0.5)
                
                # 로그인 버튼 클릭
                login_btn = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
                login_btn.click()
                time.sleep(3)
                
            except TimeoutException:
                logger.warning("⚠️ 카카오 로그인 페이지를 찾을 수 없습니다.")
            
            # 2차 인증 확인 및 대기
            time.sleep(2)
            
            # 2차 인증이 필요한 경우 (URL에 auth 또는 인증 관련 페이지가 있는지 확인)
            current_url = self.driver.current_url
            if "auth" in current_url or "verify" in current_url or "accounts.kakao" in current_url:
                logger.warning("⚠️ 2차 인증이 필요합니다!")
                logger.info("📱 카카오톡 또는 이메일로 인증을 완료해주세요. (60초 대기)")
                
                # 60초 동안 로그인 완료 대기
                for i in range(60):
                    time.sleep(1)
                    current_url = self.driver.current_url
                    # 티스토리로 리다이렉트되면 성공
                    if "tistory.com" in current_url and "accounts.kakao" not in current_url:
                        logger.info("✅ 2차 인증 완료 감지!")
                        break
                    if i % 10 == 0:
                        logger.info(f"⏳ 대기 중... ({60 - i}초 남음)")
            
            # 카카오 계정 선택 화면 처리 ("계속하기" 버튼)
            time.sleep(1)
            current_url = self.driver.current_url
            if "kauth.kakao.com" in current_url or "oauth" in current_url:
                logger.info("📋 카카오 계정 선택 화면 감지")
                try:
                    # "계속하기" 버튼 클릭
                    continue_btn = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '계속하기')]"))
                    )
                    continue_btn.click()
                    logger.info("✅ '계속하기' 버튼 클릭")
                    time.sleep(2)
                except:
                    # 다른 셀렉터 시도
                    try:
                        continue_btn = self.driver.find_element(By.CSS_SELECTOR, "button.btn_confirm")
                        continue_btn.click()
                        logger.info("✅ '계속하기' 버튼 클릭 (대체 셀렉터)")
                        time.sleep(2)
                    except:
                        logger.warning("⚠️ '계속하기' 버튼을 찾을 수 없습니다.")
            
            # 로그인 성공 확인 - 티스토리 메인으로 이동 시도
            time.sleep(2)
            self.driver.get("https://www.tistory.com")
            time.sleep(2)
            
            # 블로그 관리 페이지로 이동하여 세션 확립
            self.driver.get(f"https://{self.blog_name}.tistory.com/manage")
            time.sleep(2)
            
            # 다시 로그인 페이지로 리다이렉트되면 쿠키 문제
            if "auth/login" in self.driver.current_url:
                logger.warning("⚠️ 블로그 관리 페이지 접근을 위해 추가 인증이 필요합니다.")
                logger.info("📱 카카오톡으로 인증을 완료해주세요. (60초 대기)")
                
                for i in range(60):
                    time.sleep(1)
                    if "manage" in self.driver.current_url and "auth" not in self.driver.current_url:
                        logger.info("✅ 블로그 관리 페이지 접근 성공!")
                        break
            
            # 로그인 상태 확인
            if self.blog_name in self.driver.current_url or "tistory.com" in self.driver.current_url:
                self.is_logged_in = True
                logger.success("✅ 티스토리 로그인 성공")
                return True
            else:
                logger.error("❌ 로그인 실패")
                return False
                
        except Exception as e:
            logger.error(f"❌ 티스토리 로그인 실패: {e}")
            return False
    
    def publish(
        self,
        title: str,
        content: str,
        category: Optional[str] = None,
        tags: Optional[list] = None,
        images: Optional[list] = None
    ) -> bool:
        """티스토리에 글 발행
        
        Args:
            title: 글 제목
            content: 글 내용
            category: 카테고리
            tags: 태그 목록
            images: 이미지 파일 경로 목록
        
        Returns:
            발행 성공 여부
        """
        if not self.is_logged_in:
            if not self.login():
                return False
        
        try:
            # 글쓰기 페이지로 이동 (블로그 이름 포함)
            write_url = self.BLOG_WRITE_URL.format(blog_name=self.blog_name)
            logger.info(f"📝 글쓰기 페이지로 이동: {write_url}")
            self.driver.get(write_url)
            time.sleep(3)
            
            # 임시저장 글 알림창 처리
            try:
                alert = self.driver.switch_to.alert
                logger.info(f"📋 알림창 감지: {alert.text[:50]}...")
                # "취소" 클릭 - 새 글 작성
                alert.dismiss()
                time.sleep(1)
            except:
                pass  # 알림창이 없으면 무시
            
            logger.info(f"📝 티스토리 글 작성 중: {title}")
            
            # 이미지 파일 매핑 생성
            image_map = {}
            if images:
                for img_path in images:
                    img_name = Path(img_path).name.lower()
                    image_map[img_name] = img_path
                logger.info(f"📷 이미지 {len(image_map)}개 로드: {list(image_map.keys())}")
            
            # 제목에서 BMP 외 문자(이모지) 제거 - ChromeDriver 호환성
            clean_title = ''.join(c for c in title if ord(c) <= 0xFFFF)
            
            # 제목 입력
            title_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#post-title-inp"))
            )
            title_input.clear()
            title_input.send_keys(clean_title)
            time.sleep(1)
            
            # 이미지 먼저 업로드 (본문 입력 전에)
            uploaded_images = {}  # {파일명: 업로드된 이미지 URL}
            if image_map:
                uploaded_images = self._upload_images(image_map)
            
            # 본문 입력 - 티스토리 TinyMCE 에디터 처리
            editor_found = False
            
            # 티스토리는 TinyMCE iframe 에디터 사용 (id: editor-tistory_ifr)
            try:
                # TinyMCE iframe 찾기
                iframe = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "#editor-tistory_ifr, iframe[id*='ifr']"))
                )
                
                # TinyMCE HTML 변환 (업로드된 이미지 포함)
                tinymce_html = self._markdown_to_tinymce_html(content, uploaded_images)
                
                # 방법 1: TinyMCE API 사용 (가장 확실한 방법)
                # 메인 프레임에서 TinyMCE API 호출
                self.driver.execute_script("""
                    // TinyMCE 에디터 인스턴스 가져오기
                    if (typeof tinymce !== 'undefined' && tinymce.activeEditor) {
                        var editor = tinymce.activeEditor;
                        // 내용 설정
                        editor.setContent(arguments[0]);
                        // 변경사항 저장 (폼 데이터에 반영)
                        editor.save();
                        console.log('TinyMCE API로 내용 설정 완료');
                    } else if (typeof tinyMCE !== 'undefined' && tinyMCE.activeEditor) {
                        var editor = tinyMCE.activeEditor;
                        editor.setContent(arguments[0]);
                        editor.save();
                        console.log('tinyMCE API로 내용 설정 완료');
                    } else {
                        // API 사용 불가시 hidden textarea에 직접 입력
                        var textarea = document.querySelector('#editor-tistory');
                        if (textarea) {
                            textarea.value = arguments[0];
                            console.log('textarea에 직접 입력');
                        }
                    }
                """, tinymce_html)
                
                time.sleep(1)
                
                # 에디터 내용이 제대로 들어갔는지 확인
                # iframe으로 전환해서 확인
                self.driver.switch_to.frame(iframe)
                body_content = self.driver.execute_script("return document.body.innerHTML;")
                self.driver.switch_to.default_content()
                
                if len(body_content) > 50:  # 내용이 있으면 성공
                    editor_found = True
                    logger.info(f"✅ 본문 입력 완료 (TinyMCE API) - {len(body_content)}자")
                else:
                    logger.debug("TinyMCE API 방식 실패 - 내용 없음")
                
            except Exception as e:
                logger.debug(f"TinyMCE API 방식 실패: {e}")
                try:
                    self.driver.switch_to.default_content()
                except:
                    pass
            
            # 방법 2: iframe 직접 수정 + save 호출
            if not editor_found:
                try:
                    iframe = self.driver.find_element(By.CSS_SELECTOR, "#editor-tistory_ifr, iframe[id*='ifr']")
                    self.driver.switch_to.frame(iframe)
                    
                    tinymce_html = self._markdown_to_tinymce_html(content)
                    self.driver.execute_script("""
                        document.body.innerHTML = arguments[0];
                    """, tinymce_html)
                    
                    self.driver.switch_to.default_content()
                    
                    # TinyMCE save 호출
                    self.driver.execute_script("""
                        if (typeof tinymce !== 'undefined' && tinymce.activeEditor) {
                            tinymce.activeEditor.save();
                        } else if (typeof tinyMCE !== 'undefined' && tinyMCE.activeEditor) {
                            tinyMCE.activeEditor.save();
                        }
                        // 또는 triggerSave
                        if (typeof tinymce !== 'undefined') {
                            tinymce.triggerSave();
                        }
                    """)
                    
                    editor_found = True
                    logger.info("✅ 본문 입력 완료 (iframe + save)")
                    
                except Exception as e:
                    logger.debug(f"iframe 직접 수정 실패: {e}")
                    try:
                        self.driver.switch_to.default_content()
                    except:
                        pass
            
            # 방법 3: 키보드 입력 방식 (최후의 수단)
            if not editor_found:
                try:
                    from selenium.webdriver.common.action_chains import ActionChains
                    
                    # iframe으로 다시 전환
                    iframe = self.driver.find_element(By.CSS_SELECTOR, "iframe[id*='ifr']")
                    self.driver.switch_to.frame(iframe)
                    
                    # body 클릭
                    body = self.driver.find_element(By.TAG_NAME, "body")
                    body.click()
                    time.sleep(0.3)
                    
                    # 기존 내용 삭제
                    body.clear()
                    
                    # 키보드로 직접 입력
                    actions = ActionChains(self.driver)
                    plain_text = content.replace('**', '').replace('## ', '').replace('### ', '').replace('# ', '')
                    for line in plain_text.split('\n'):
                        if line.strip():
                            actions.send_keys(line)
                        actions.send_keys(Keys.ENTER)
                    actions.perform()
                    
                    self.driver.switch_to.default_content()
                    editor_found = True
                    logger.info("✅ 본문 입력 완료 (키보드 입력)")
                except Exception as e:
                    logger.warning(f"⚠️ 모든 에디터 입력 방식 실패: {e}")
                    self.driver.switch_to.default_content()
            
            if not editor_found:
                # 마크다운 모드 또는 기본 textarea 시도
                try:
                    textarea = self.driver.find_element(By.CSS_SELECTOR, "textarea")
                    textarea.clear()
                    textarea.send_keys(content)
                    logger.info("✅ 본문 입력 완료 (textarea)")
                    editor_found = True
                except:
                    logger.warning("⚠️ 에디터를 찾을 수 없습니다. 수동 입력이 필요할 수 있습니다.")
            
            time.sleep(2)
            
            # 카테고리 선택
            if category:
                self._select_category(category)
            
            # 태그 입력
            if tags:
                self._add_tags(tags)
            
            # 발행 버튼 클릭
            self._click_publish_button()
            
            time.sleep(3)
            logger.success(f"✅ 티스토리 발행 완료: {title}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 티스토리 발행 실패: {e}")
            # 스크린샷 저장
            try:
                self.driver.save_screenshot("tistory_error.png")
                logger.info("📸 에러 스크린샷 저장: tistory_error.png")
            except:
                pass
            return False
    
    def _input_content_to_editor(self, editor, content: str):
        """에디터에 콘텐츠 입력"""
        # 줄 단위로 입력
        lines = content.split('\n')
        
        for line in lines:
            if line.strip():
                editor.send_keys(line)
            editor.send_keys(Keys.ENTER)
            time.sleep(0.1)
    
    def _markdown_to_html(self, markdown_text: str) -> str:
        """마크다운을 HTML로 변환
        
        Args:
            markdown_text: 마크다운 텍스트
        
        Returns:
            HTML 문자열
        """
        import re
        
        html_lines = []
        lines = markdown_text.split('\n')
        
        for line in lines:
            stripped = line.strip()
            
            if not stripped:
                continue
            
            # 헤딩 처리
            if stripped.startswith('### '):
                html_lines.append(f'<h3>{stripped[4:]}</h3>')
            elif stripped.startswith('## '):
                html_lines.append(f'<h2>{stripped[3:]}</h2>')
            elif stripped.startswith('# '):
                html_lines.append(f'<h1>{stripped[2:]}</h1>')
            elif stripped.startswith('- ') or stripped.startswith('* '):
                # 리스트 아이템
                html_lines.append(f'<p>• {stripped[2:]}</p>')
            elif stripped.startswith('[IMAGE:'):
                # 이미지 마커 - 플레이스홀더로 표시
                match = re.match(r'\[IMAGE:\s*([^\]]+)\]', stripped)
                if match:
                    html_lines.append(f'<p>[사진: {match.group(1)}]</p>')
            else:
                # 일반 문단
                # 볼드 처리
                text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', stripped)
                html_lines.append(f'<p>{text}</p>')
        
        return ''.join(html_lines)
    
    def _markdown_to_tinymce_html(self, markdown_text: str, uploaded_images: dict = None) -> str:
        """마크다운을 티스토리 TinyMCE 형식 HTML로 변환
        
        티스토리 에디터는 data-ke-size 속성이 필요
        
        Args:
            markdown_text: 마크다운 텍스트
            uploaded_images: 업로드된 이미지 {파일명: URL} 딕셔너리
        
        Returns:
            TinyMCE 형식 HTML 문자열
        """
        import re
        
        uploaded_images = uploaded_images or {}
        html_lines = []
        lines = markdown_text.split('\n')
        
        for line in lines:
            stripped = line.strip()
            
            if not stripped:
                # 빈 줄도 유지
                html_lines.append('<p data-ke-size="size16">&nbsp;</p>')
                continue
            
            # 헤딩 처리 (티스토리 스타일)
            if stripped.startswith('### '):
                text = stripped[4:]
                html_lines.append(f'<h3 data-ke-size="size23">{text}</h3>')
            elif stripped.startswith('## '):
                text = stripped[3:]
                html_lines.append(f'<h2 data-ke-size="size26">{text}</h2>')
            elif stripped.startswith('# '):
                text = stripped[2:]
                html_lines.append(f'<h1 data-ke-size="size36">{text}</h1>')
            elif stripped.startswith('- ') or stripped.startswith('* '):
                # 리스트 아이템
                text = stripped[2:]
                html_lines.append(f'<p data-ke-size="size16">• {text}</p>')
            elif stripped.startswith('[IMAGE:'):
                # 이미지 마커 처리
                match = re.match(r'\[IMAGE:\s*([^\]]+)\]', stripped)
                if match:
                    image_name = match.group(1).strip()
                    image_name_lower = image_name.lower()
                    
                    # 업로드된 이미지에서 URL 찾기
                    image_url = None
                    
                    # 1. 정확한 파일명 매칭 시도
                    for name, url in uploaded_images.items():
                        if name.lower() == image_name_lower:
                            image_url = url
                            break
                    
                    # 2. 정확한 매칭 실패시 부분 매칭 (번호 포함 우선)
                    if not image_url:
                        # 파일명에서 숫자 추출 (예: "1.카페클램로고.jpg" -> "1")
                        image_num_match = re.match(r'^(\d+)\.', image_name)
                        image_num = image_num_match.group(1) if image_num_match else None
                        
                        for name, url in uploaded_images.items():
                            name_num_match = re.match(r'^(\d+)\.', name)
                            name_num = name_num_match.group(1) if name_num_match else None
                            
                            # 숫자가 일치하면 매칭
                            if image_num and name_num and image_num == name_num:
                                image_url = url
                                break
                    
                    # 3. 여전히 없으면 부분 문자열 매칭
                    if not image_url:
                        for name, url in uploaded_images.items():
                            if image_name_lower in name.lower() or name.lower() in image_name_lower:
                                image_url = url
                                break
                    
                    if image_url:
                        # 티스토리 이미지 형식
                        html_lines.append(f'''<figure class="imageblock alignCenter" data-ke-mobilestyle="widthOrigin" data-origin-width="0" data-origin-height="0">
<span data-url="{image_url}" data-lightbox="lightbox">
<img src="{image_url}" data-ke-size="size16">
</span>
</figure>''')
                    else:
                        # 업로드 안된 경우 플레이스홀더
                        html_lines.append(f'<p data-ke-size="size16">[사진: {image_name}]</p>')
            else:
                # 일반 문단
                # 볼드 처리
                text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', stripped)
                html_lines.append(f'<p data-ke-size="size16">{text}</p>')
        
        return ''.join(html_lines)
    
    def _upload_images(self, image_map: dict) -> dict:
        """이미지 업로드
        
        Args:
            image_map: {파일명: 경로} 딕셔너리
        
        Returns:
            {파일명: 업로드된 URL} 딕셔너리
        """
        uploaded = {}
        
        for name, path in image_map.items():
            try:
                if not Path(path).exists():
                    logger.warning(f"⚠️ 이미지 파일 없음: {path}")
                    continue
                
                logger.info(f"📷 이미지 업로드 시도: {name}")
                
                # 티스토리 에디터에서 이미지 업로드
                # 방법 1: 툴바의 이미지 버튼 클릭 후 파일 선택
                try:
                    # 이미지 삽입 버튼 찾기 (여러 셀렉터 시도)
                    image_btn_selectors = [
                        "button.btn-insert-image",
                        "[data-command='image']",
                        ".mce-ico.mce-i-image",
                        "button[aria-label*='이미지']",
                        ".editor-toolbar button:nth-child(3)",  # 대략적인 위치
                    ]
                    
                    image_btn = None
                    for selector in image_btn_selectors:
                        try:
                            image_btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                            if image_btn and image_btn.is_displayed():
                                break
                        except:
                            continue
                    
                    if image_btn:
                        image_btn.click()
                        time.sleep(1)
                except:
                    pass
                
                # 파일 input 찾기 (숨겨진 input도 포함)
                file_input = None
                
                # JavaScript로 숨겨진 file input도 찾기
                file_inputs = self.driver.execute_script("""
                    return document.querySelectorAll('input[type="file"]');
                """)
                
                if file_inputs and len(file_inputs) > 0:
                    file_input = file_inputs[0]
                
                if not file_input:
                    # 직접 셀렉터로 시도
                    file_input_selectors = [
                        "input[type='file']",
                        "input[accept*='image']",
                        "#file-upload",
                        ".file-input"
                    ]
                    
                    for selector in file_input_selectors:
                        try:
                            file_input = self.driver.find_element(By.CSS_SELECTOR, selector)
                            if file_input:
                                break
                        except:
                            continue
                
                if file_input:
                    # JavaScript로 input을 visible하게 만들기
                    self.driver.execute_script("""
                        arguments[0].style.display = 'block';
                        arguments[0].style.visibility = 'visible';
                        arguments[0].style.opacity = '1';
                    """, file_input)
                    
                    # 파일 경로 전송
                    file_input.send_keys(str(Path(path).absolute()))
                    time.sleep(3)  # 업로드 대기
                    
                    # 업로드 완료 후 이미지 URL 가져오기
                    try:
                        iframe = self.driver.find_element(By.CSS_SELECTOR, "#editor-tistory_ifr, iframe[id*='ifr']")
                        self.driver.switch_to.frame(iframe)
                        imgs = self.driver.find_elements(By.TAG_NAME, "img")
                        if imgs:
                            img_url = imgs[-1].get_attribute("src")
                            if img_url and img_url.startswith("http"):
                                uploaded[name] = img_url
                                logger.info(f"✅ 이미지 업로드 완료: {name}")
                        self.driver.switch_to.default_content()
                    except Exception as e:
                        self.driver.switch_to.default_content()
                        logger.debug(f"이미지 URL 추출 실패: {e}")
                else:
                    # 파일 input이 없으면 JavaScript로 생성해서 시도
                    logger.debug("파일 input 없음 - JavaScript로 생성 시도")
                    
                    # TinyMCE에 직접 이미지 삽입 시도 (base64)
                    try:
                        import base64
                        with open(path, 'rb') as f:
                            img_data = base64.b64encode(f.read()).decode('utf-8')
                        
                        # 이미지 확장자 확인
                        ext = Path(path).suffix.lower()
                        mime_type = {
                            '.jpg': 'image/jpeg',
                            '.jpeg': 'image/jpeg',
                            '.png': 'image/png',
                            '.gif': 'image/gif',
                            '.webp': 'image/webp'
                        }.get(ext, 'image/jpeg')
                        
                        data_url = f"data:{mime_type};base64,{img_data}"
                        uploaded[name] = data_url
                        logger.info(f"✅ 이미지 base64 변환 완료: {name}")
                    except Exception as e:
                        logger.warning(f"⚠️ base64 변환 실패: {e}")
                    
            except Exception as e:
                logger.warning(f"⚠️ 이미지 업로드 실패 ({name}): {e}")
        
        return uploaded
    
    def _select_category(self, category: str):
        """카테고리 선택"""
        try:
            # 카테고리 버튼 클릭하여 드롭다운 열기
            category_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "#category-btn"))
            )
            category_btn.click()
            time.sleep(0.5)
            
            # 카테고리 목록에서 해당 카테고리 찾기
            category_list = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#category-list"))
            )
            
            # 카테고리 항목들 찾기 (div.mce-menu-item)
            items = category_list.find_elements(By.CSS_SELECTOR, "div.mce-menu-item")
            
            logger.info(f"🔍 찾는 카테고리: '{category}', 총 {len(items)}개 항목")
            
            for item in items:
                # 카테고리 이름 확인 (span.mce-text 안에 있음)
                try:
                    txt_span = item.find_element(By.CSS_SELECTOR, "span.mce-text")
                    item_text = txt_span.text.strip()
                    
                    # 정확히 일치하거나, "- 맛집" 형태에서 맛집만 비교
                    clean_text = item_text.lstrip('- ').strip()
                    if item_text == category or clean_text == category:
                        # 스크롤하여 해당 항목이 보이도록
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", item)
                        time.sleep(0.2)
                        item.click()
                        logger.info(f"📁 카테고리 선택: {category} ('{item_text}')")
                        time.sleep(0.5)
                        return
                except Exception as e:
                    continue
            
            logger.warning(f"⚠️ 카테고리를 찾을 수 없음: {category}")
            # 드롭다운 닫기
            category_btn.click()
            
        except Exception as e:
            logger.warning(f"⚠️ 카테고리 선택 실패: {e}")
    
    def _add_tags(self, tags: list):
        """태그 추가"""
        try:
            # 태그 입력 영역 찾기
            tag_input = self.driver.find_element(By.CSS_SELECTOR, "#tagText")
            
            for tag in tags[:10]:  # 최대 10개
                tag_input.send_keys(tag)
                tag_input.send_keys(",")  # 쉼표로 구분
                time.sleep(0.2)
            
            logger.info(f"🏷️ 태그 추가: {', '.join(tags[:10])}")
        except Exception as e:
            logger.warning(f"⚠️ 태그 추가 실패: {e}")
    
    def _click_publish_button(self):
        """발행 버튼 클릭"""
        try:
            # 발행 버튼 찾기
            publish_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "#publish-layer-btn"))
            )
            publish_btn.click()
            time.sleep(1)
            
            # 공개 발행 확인
            confirm_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "#publish-btn"))
            )
            confirm_btn.click()
            
        except Exception as e:
            logger.warning(f"⚠️ 발행 버튼 클릭 실패: {e}")
            # 대체 셀렉터 시도
            try:
                alt_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), '발행')]")
                alt_btn.click()
            except:
                pass
    
    def logout(self):
        """로그아웃 및 브라우저 종료"""
        self.browser_manager.quit()
        self.is_logged_in = False
        self.driver = None
        logger.info("👋 티스토리 로그아웃 완료")
