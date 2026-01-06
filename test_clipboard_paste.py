"""티스토리 이미지 업로드 테스트 - 클립보드 붙여넣기 방식"""
from src.publishers.tistory import TistoryPublisher
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
from pathlib import Path
import subprocess
import platform

# 테스트 이미지
image_path = "/Users/jihoon/study/blog/input/2026/01/맛집_광주_황금들판/media/1.메뉴.jpg"

def copy_image_to_clipboard(image_path: str) -> bool:
    """이미지를 클립보드에 복사 (macOS)"""
    if platform.system() != 'Darwin':
        print('❌ macOS만 지원됩니다.')
        return False
    
    # osascript를 사용해서 이미지를 클립보드에 복사
    script = f'''
    set theFile to POSIX file "{image_path}"
    set theImage to read theFile as JPEG picture
    set the clipboard to theImage
    '''
    
    try:
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            print(f'✅ 클립보드에 이미지 복사 완료: {Path(image_path).name}')
            return True
        else:
            print(f'❌ 클립보드 복사 실패: {result.stderr}')
            return False
    except Exception as e:
        print(f'❌ 에러: {e}')
        return False

print('🚀 티스토리 이미지 업로드 테스트 - 클립보드 붙여넣기...')
publisher = TistoryPublisher(headless=False)

if publisher.login():
    print('✅ 로그인 성공')
    
    # 글쓰기 페이지로 이동
    publisher.driver.get(f"https://{publisher.blog_name}.tistory.com/manage/newpost")
    time.sleep(3)
    
    # 저장된 글 알림 처리
    try:
        from selenium.webdriver.common.alert import Alert
        alert = Alert(publisher.driver)
        print(f'⚠️ 알림: {alert.text}')
        alert.dismiss()
        time.sleep(2)
    except:
        pass
    
    print('\n📝 에디터에 이미지 붙여넣기 시도...')
    
    try:
        # 1. 이미지를 클립보드에 복사
        if not copy_image_to_clipboard(image_path):
            raise Exception("클립보드 복사 실패")
        
        # 2. 에디터 iframe으로 전환
        iframe = publisher.driver.find_element(By.CSS_SELECTOR, "#editor-tistory_ifr, iframe[id*='ifr']")
        publisher.driver.switch_to.frame(iframe)
        
        # 3. 에디터 body에 포커스
        editor_body = publisher.driver.find_element(By.TAG_NAME, "body")
        editor_body.click()
        time.sleep(0.5)
        
        # 4. Cmd+V로 붙여넣기 (macOS)
        from selenium.webdriver.common.action_chains import ActionChains
        actions = ActionChains(publisher.driver)
        actions.key_down(Keys.COMMAND).send_keys('v').key_up(Keys.COMMAND).perform()
        print('📋 Cmd+V 붙여넣기 실행')
        
        time.sleep(5)  # 업로드 대기
        
        # 5. 에디터 내 이미지 확인
        imgs = publisher.driver.find_elements(By.TAG_NAME, "img")
        print(f'\n📷 에디터 내 이미지: {len(imgs)}개')
        
        for img in imgs:
            src = img.get_attribute("src") or ""
            if src:
                print(f'  ✅ 이미지: {src[:80]}...' if len(src) > 80 else f'  ✅ 이미지: {src}')
        
        publisher.driver.switch_to.default_content()
        
        if imgs:
            answer = input('\n이미지 삽입 성공! 발행 테스트? (y/n): ')
            
            if answer.lower() == 'y':
                # 제목 입력
                title_input = publisher.driver.find_element(By.CSS_SELECTOR, "#post-title-inp")
                title_input.clear()
                title_input.send_keys("클립보드 이미지 테스트")
                
                # 발행
                publish_btn = publisher.driver.find_element(By.CSS_SELECTOR, "#publish-layer-btn")
                publish_btn.click()
                time.sleep(1)
                
                public_btn = publisher.driver.find_element(By.CSS_SELECTOR, "#publish-btn")
                public_btn.click()
                time.sleep(5)
                
                # 에러 확인
                try:
                    error = publisher.driver.find_element(By.CSS_SELECTOR, ".layer_popup")
                    if '실패' in error.text:
                        print(f'❌ 발행 실패: {error.text}')
                    else:
                        print('📤 발행 완료!')
                except:
                    print('📤 발행 완료!')
        else:
            print('❌ 이미지 삽입 실패')
        
    except Exception as e:
        print(f'❌ 에러: {e}')
        import traceback
        traceback.print_exc()
        publisher.driver.switch_to.default_content()
    
    input('\n테스트 완료. Enter를 누르면 브라우저가 닫힙니다...')
    publisher.logout()
else:
    print('❌ 로그인 실패')
