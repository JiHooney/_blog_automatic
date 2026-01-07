"""
티스토리 자동화
Selenium을 사용하여 티스토리에 글 발행
"""
import os
import sys
import time
import subprocess
import platform
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
            
            # 발행 결과 확인 (에러 팝업 감지)
            time.sleep(3)
            
            # 에러 팝업 확인
            try:
                # 티스토리 에러 팝업: "게시글을 작성하는데 실패했습니다"
                error_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), '실패')]")
                if error_elements:
                    logger.error("❌ 티스토리 발행 실패: 에러 팝업 감지됨")
                    # 확인 버튼 클릭
                    try:
                        confirm_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), '확인')]")
                        confirm_btn.click()
                    except:
                        pass
                    return False
            except:
                pass
            
            # URL 변경 확인 (발행 성공 시 글 페이지로 이동)
            current_url = self.driver.current_url
            if "newpost" in current_url or "manage" in current_url:
                # 아직 작성 페이지에 있으면 실패 가능성
                time.sleep(2)
                current_url = self.driver.current_url
                if "newpost" in current_url:
                    logger.warning("⚠️ 발행 후에도 작성 페이지에 머물러 있음 - 실패 가능성")
            
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
    
    def _copy_image_to_clipboard(self, image_path: str) -> bool:
        """이미지를 클립보드에 복사 (OS별 분기)
        
        Args:
            image_path: 이미지 파일 경로
            
        Returns:
            복사 성공 여부
        """
        current_os = platform.system()
        
        if current_os == "Darwin":  # macOS
            return self._copy_image_clipboard_macos(image_path)
        elif current_os == "Windows":
            return self._copy_image_clipboard_windows(image_path)
        elif current_os == "Linux":
            return self._copy_image_clipboard_linux(image_path)
        else:
            logger.error(f"❌ 지원하지 않는 OS: {current_os}")
            return False
    
    def _copy_image_clipboard_macos(self, image_path: str) -> bool:
        """macOS: osascript로 이미지 클립보드 복사"""
        script = f'''
        set theFile to POSIX file "{image_path}"
        set theImage to read theFile as JPEG picture
        set the clipboard to theImage
        '''
        
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            logger.warning(f"⚠️ macOS 클립보드 복사 실패: {result.stderr}")
            return False
        return True
    
    def _copy_image_clipboard_windows(self, image_path: str) -> bool:
        """Windows: PowerShell로 이미지 클립보드 복사"""
        try:
            # 방법 1: PowerShell의 System.Windows.Forms.Clipboard 사용
            ps_script = f'''
            Add-Type -AssemblyName System.Windows.Forms
            $image = [System.Drawing.Image]::FromFile("{image_path}")
            [System.Windows.Forms.Clipboard]::SetImage($image)
            '''
            
            result = subprocess.run(
                ['powershell', '-Command', ps_script],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return True
            
            # 방법 2: Python의 win32clipboard 모듈 시도
            try:
                import io
                import win32clipboard
                
                # 이미지를 BMP 형식으로 변환
                img = self._load_image_with_exif_orientation(image_path)
                output = io.BytesIO()
                img.save(output, 'BMP')
                data = output.getvalue()[14:]  # BMP 헤더 제거
                output.close()
                
                win32clipboard.OpenClipboard()
                win32clipboard.EmptyClipboard()
                win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
                win32clipboard.CloseClipboard()
                return True
                
            except ImportError:
                logger.warning("⚠️ win32clipboard 미설치. PowerShell 실패 시 'pip install pywin32' 필요")
                return False
                
        except Exception as e:
            logger.warning(f"⚠️ Windows 클립보드 복사 실패: {e}")
            return False
    
    def _copy_image_clipboard_linux(self, image_path: str) -> bool:
        """Linux: xclip으로 이미지 클립보드 복사"""
        try:
            # xclip 사용
            result = subprocess.run(
                ['xclip', '-selection', 'clipboard', '-t', 'image/png', '-i', image_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return True
            
            # xsel 대안 시도
            result = subprocess.run(
                ['xsel', '--clipboard', '--input', '--type', 'image/png'],
                input=open(image_path, 'rb').read(),
                capture_output=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return True
                
            logger.warning("⚠️ Linux 클립보드 복사 실패. 'apt install xclip' 또는 'apt install xsel' 필요")
            return False
            
        except FileNotFoundError:
            logger.warning("⚠️ xclip/xsel 미설치. 'apt install xclip' 필요")
            return False
        except Exception as e:
            logger.warning(f"⚠️ Linux 클립보드 복사 실패: {e}")
            return False

    def _load_image_with_exif_orientation(self, image_path: str):
        """EXIF 방향 정보를 반영해 이미지를 로드한 뒤 파일 핸들을 닫은 상태로 반환"""
        from PIL import Image, ImageOps

        with Image.open(image_path) as img:
            try:
                img = ImageOps.exif_transpose(img)
            except Exception:
                pass
            return img.convert('RGB').copy()  # copy()로 파일 핸들 분리
    
    def _get_paste_key(self):
        """OS별 붙여넣기 키 반환"""
        if platform.system() == "Darwin":
            return Keys.COMMAND
        else:  # Windows, Linux
            return Keys.CONTROL
    
    def _close_modal_if_exists(self):
        """TinyMCE 모달 오버레이가 있으면 닫기"""
        from selenium.webdriver.common.action_chains import ActionChains
        from selenium.webdriver.common.keys import Keys
        
        try:
            self.driver.switch_to.default_content()
            
            # mce-modal-block 오버레이 확인 및 제거
            modal_blocks = self.driver.find_elements(By.CSS_SELECTOR, "#mce-modal-block, .mce-modal-block")
            if modal_blocks:
                for modal in modal_blocks:
                    try:
                        self.driver.execute_script("arguments[0].remove();", modal)
                    except:
                        pass
                logger.debug("모달 오버레이 제거됨")
            
            # mce-dragh (에디터 리사이즈 핸들러) 제거
            dragh_elements = self.driver.find_elements(By.CSS_SELECTOR, ".mce-dragh, #mceu_29-dragh")
            for elem in dragh_elements:
                try:
                    self.driver.execute_script("arguments[0].style.display = 'none';", elem)
                except:
                    pass
            
            # mce-window (팝업 창) 닫기
            mce_windows = self.driver.find_elements(By.CSS_SELECTOR, ".mce-window")
            for win in mce_windows:
                try:
                    close_btn = win.find_elements(By.CSS_SELECTOR, ".mce-close, button[aria-label='Close']")
                    if close_btn:
                        close_btn[0].click()
                    else:
                        self.driver.execute_script("arguments[0].remove();", win)
                except:
                    pass
            
            # ESC 키로 모달 닫기 시도
            try:
                actions = ActionChains(self.driver)
                actions.send_keys(Keys.ESCAPE).perform()
                time.sleep(0.3)
            except:
                pass
                
        except Exception as e:
            logger.debug(f"모달 닫기 중 오류 (무시): {e}")
    
    def _upload_images(self, image_map: dict) -> dict:
        """이미지 업로드 - 클립보드 붙여넣기 방식 (macOS)
        
        이미지를 클립보드에 복사한 후 에디터에 Cmd+V로 붙여넣기하여 업로드합니다.
        업로드 후 이미지 URL만 수집하고, 에디터 내용은 비웁니다.
        (본문 입력 시 HTML에 이미지 URL을 포함하여 설정)
        
        Args:
            image_map: {파일명: 경로} 딕셔너리
        
        Returns:
            {파일명: 업로드된 URL} 딕셔너리
        """
        import subprocess
        from selenium.webdriver.common.action_chains import ActionChains
        
        uploaded = {}
        
        current_os = platform.system()
        if current_os not in ('Darwin', 'Windows', 'Linux'):
            logger.warning(f"⚠️ 클립보드 이미지 업로드는 {current_os}를 지원하지 않습니다.")
            return uploaded
        
        logger.info(f"🖥️ OS 감지: {current_os}")
        
        # 첫 이미지 업로드 전 에디터 준비 - 반드시 에디터에 포커스가 있어야 함
        try:
            self.driver.switch_to.default_content()
            
            # TinyMCE 에디터 포커스
            self.driver.execute_script("""
                if (typeof tinymce !== 'undefined' && tinymce.activeEditor) {
                    tinymce.activeEditor.focus();
                }
            """)
            time.sleep(0.5)
            
            # iframe 내부에서 클릭하여 에디터 활성화
            iframe = self.driver.find_element(By.CSS_SELECTOR, "#editor-tistory_ifr, iframe[id*='ifr']")
            self.driver.switch_to.frame(iframe)
            editor_body = self.driver.find_element(By.TAG_NAME, "body")
            editor_body.click()
            time.sleep(0.5)
            self.driver.switch_to.default_content()
            
            logger.debug("에디터 준비 완료")
        except Exception as e:
            logger.debug(f"에디터 준비 중 오류 (계속 진행): {e}")
        
        for name, path in image_map.items():
            try:
                if not Path(path).exists():
                    logger.warning(f"⚠️ 이미지 파일 없음: {path}")
                    continue
                
                logger.info(f"📷 이미지 업로드 시도: {name}")
                
                # 모달이 있으면 닫기 (이전 업로드에서 남아있을 수 있음)
                self._close_modal_if_exists()
                
                # 0. 이미지 크기 확인 + EXIF 방향 보정 + 필요시 리사이즈
                image_path = Path(path)
                temp_image_path = None
                file_size_mb = image_path.stat().st_size / (1024 * 1024)
                needs_resize = file_size_mb > 4  # 4MB 이상이면 리사이즈
                needs_orientation_fix = False
                
                try:
                    from PIL import Image, ImageOps
                    import tempfile

                    with Image.open(path) as img:
                        orientation = None
                        exif = img.getexif()
                        if exif:
                            orientation = exif.get(274)
                            if orientation and orientation != 1:
                                needs_orientation_fix = True
                        
                        img = ImageOps.exif_transpose(img)
                        
                        # 최대 크기 제한 (가로 1800px) - 리사이즈 조건일 때만 적용
                        max_width = 1800
                        if needs_resize and img.width > max_width:
                            ratio = max_width / img.width
                            new_size = (max_width, int(img.height * ratio))
                            img = img.resize(new_size, Image.LANCZOS)
                        
                        if needs_resize or needs_orientation_fix:
                            temp_fd, temp_path = tempfile.mkstemp(suffix='.jpg')
                            os.close(temp_fd)
                            img.convert('RGB').save(temp_path, 'JPEG', quality=85)
                            temp_image_path = temp_path
                            path = temp_path
                            
                            new_size_mb = Path(temp_path).stat().st_size / (1024 * 1024)
                            if needs_resize:
                                logger.debug(f"이미지 리사이즈: {file_size_mb:.1f}MB → {new_size_mb:.1f}MB")
                            if needs_orientation_fix and not needs_resize:
                                logger.debug("이미지 EXIF 방향 보정 후 임시 저장")
                except Exception as e:
                    logger.warning(f"이미지 전처리 실패(회전/리사이즈): {e}")
                
                # 1. 이미지를 클립보드에 복사 (OS별 분기)
                if not self._copy_image_to_clipboard(path):
                    # 임시 파일 정리
                    if temp_image_path and Path(temp_image_path).exists():
                        try:
                            os.remove(temp_image_path)
                        except:
                            pass
                    continue
                
                # 임시 파일 정리
                if temp_image_path and Path(temp_image_path).exists():
                    try:
                        os.remove(temp_image_path)
                    except:
                        pass
                
                logger.debug(f"클립보드에 이미지 복사 완료: {name}")
                
                # 2. 에디터 iframe으로 전환 및 붙여넣기
                try:
                    self.driver.switch_to.default_content()
                    
                    # JavaScript로 TinyMCE 에디터에 포커스
                    self.driver.execute_script("""
                        if (typeof tinymce !== 'undefined' && tinymce.activeEditor) {
                            tinymce.activeEditor.focus();
                        }
                    """)
                    time.sleep(0.3)
                    
                    iframe = self.driver.find_element(By.CSS_SELECTOR, "#editor-tistory_ifr, iframe[id*='ifr']")
                    self.driver.switch_to.frame(iframe)
                    
                    # 3. 붙여넣기 전 이미지 개수 확인
                    imgs_before = self.driver.find_elements(By.TAG_NAME, "img")
                    count_before = len(imgs_before)
                    
                    # 4. JavaScript로 body에 포커스 및 붙여넣기
                    self.driver.execute_script("document.body.focus();")
                    time.sleep(0.2)
                    
                    actions = ActionChains(self.driver)
                    paste_key = self._get_paste_key()
                    actions.key_down(paste_key).send_keys('v').key_up(paste_key).perform()
                    
                    self.driver.switch_to.default_content()
                    
                    # 5. 이미지 업로드 완료 대기 (iframe 내 이미지 개수 + CDN URL 확인)
                    max_wait = 60
                    poll_interval = 1
                    elapsed = 0
                    img_url = None
                    
                    while elapsed < max_wait:
                        time.sleep(poll_interval)
                        elapsed += poll_interval
                        
                        try:
                            # iframe으로 전환하여 이미지 확인
                            self.driver.switch_to.default_content()
                            iframe = self.driver.find_element(By.CSS_SELECTOR, "#editor-tistory_ifr, iframe[id*='ifr']")
                            self.driver.switch_to.frame(iframe)
                            
                            imgs_after = self.driver.find_elements(By.TAG_NAME, "img")
                            
                            if len(imgs_after) > count_before:
                                new_img = imgs_after[-1]
                                src = new_img.get_attribute("src")
                                
                                if src and src.startswith("http") and "kakaocdn" in src:
                                    img_url = src
                                    logger.info(f"✅ 이미지 업로드 완료 ({elapsed:.1f}초): {name}")
                                    self.driver.switch_to.default_content()
                                    break
                                else:
                                    logger.debug(f"이미지 처리 중... ({elapsed:.1f}초) - src: {src[:50] if src else 'None'}...")
                            else:
                                logger.debug(f"이미지 대기 중... ({elapsed:.1f}초)")
                            
                            self.driver.switch_to.default_content()
                        except Exception as e:
                            try:
                                self.driver.switch_to.default_content()
                            except:
                                pass
                            logger.debug(f"확인 중 오류: {e}")
                    
                    if img_url:
                        uploaded[name] = img_url
                    else:
                        # 타임아웃 - 마지막으로 한번 더 확인
                        try:
                            self.driver.switch_to.default_content()
                            iframe = self.driver.find_element(By.CSS_SELECTOR, "#editor-tistory_ifr, iframe[id*='ifr']")
                            self.driver.switch_to.frame(iframe)
                            imgs_final = self.driver.find_elements(By.TAG_NAME, "img")
                            
                            # 새 이미지가 있는지 확인
                            if len(imgs_final) > count_before:
                                new_img = imgs_final[-1]
                                src = new_img.get_attribute("src")
                                if src and src.startswith("http"):
                                    uploaded[name] = src
                                    logger.info(f"✅ 이미지 업로드 완료 (타임아웃 직전): {name}")
                                else:
                                    logger.warning(f"⚠️ 이미지 업로드 타임아웃: {name} - src: {src[:30] if src else 'None'}")
                            else:
                                logger.warning(f"⚠️ 이미지 업로드 타임아웃: {name} (이미지 없음)")
                            
                            self.driver.switch_to.default_content()
                        except Exception as e:
                            try:
                                self.driver.switch_to.default_content()
                            except:
                                pass
                            logger.warning(f"⚠️ 이미지 업로드 타임아웃: {name}")
                    
                    # 모달 닫기 (업로드 완료 후 모달이 있을 수 있음)
                    self._close_modal_if_exists()
                    
                except Exception as e:
                    try:
                        self.driver.switch_to.default_content()
                    except:
                        pass
                    logger.warning(f"⚠️ 붙여넣기 실패: {e}")
                    
            except Exception as e:
                logger.warning(f"⚠️ 이미지 업로드 실패 ({name}): {e}")
        
        # 모든 이미지 업로드 완료 후 에디터 내용 비우기
        # (본문 입력 시 HTML로 다시 설정할 것이므로)
        if uploaded:
            try:
                self.driver.execute_script("""
                    if (typeof tinymce !== 'undefined' && tinymce.activeEditor) {
                        tinymce.activeEditor.setContent('');
                    }
                """)
                logger.debug("에디터 내용 초기화 완료")
            except:
                pass
        
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
