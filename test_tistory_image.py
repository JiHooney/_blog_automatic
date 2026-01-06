"""티스토리 이미지 업로드 테스트 - 첨부 패널 분석"""
from src.publishers.tistory import TistoryPublisher
from selenium.webdriver.common.by import By
import time

print('🚀 티스토리 첨부 패널 분석...')
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
    
    print('\n� 페이지 구조 분석...')
    
    # 첨부 관련 요소 찾기
    attach_keywords = ['attach', 'file', 'upload', 'image', '첨부', '파일', '이미지', 'photo', 'media']
    
    # 버튼 및 클릭 가능한 요소 분석
    clickables = publisher.driver.find_elements(By.CSS_SELECTOR, 
        "button, [role='button'], .btn, a[href='#'], [onclick]")
    print(f'🔘 클릭 가능한 요소: {len(clickables)}개')
    
    for el in clickables:
        text = el.text.strip()
        title = el.get_attribute('title') or ''
        cls = el.get_attribute('class') or ''
        aria = el.get_attribute('aria-label') or ''
        
        # 첨부 관련 키워드 포함 여부
        combined = (text + title + cls + aria).lower()
        if any(kw in combined for kw in attach_keywords):
            print(f'  📎 {el.tag_name}: text="{text[:30]}" class="{cls[:50]}" title="{title}"')
    
    # file input 찾기
    file_inputs = publisher.driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
    print(f'\n📂 file input 요소: {len(file_inputs)}개')
    for fi in file_inputs:
        accept = fi.get_attribute('accept') or ''
        name = fi.get_attribute('name') or ''
        fid = fi.get_attribute('id') or ''
        print(f'  📄 id="{fid}" name="{name}" accept="{accept}"')
    
    # 패널/사이드바 분석
    panels = publisher.driver.find_elements(By.CSS_SELECTOR, 
        "[class*='panel'], [class*='sidebar'], [class*='attach'], [class*='file']")
    print(f'\n📦 패널/사이드바: {len(panels)}개')
    for p in panels[:10]:
        cls = p.get_attribute('class') or ''
        print(f'  📦 class="{cls[:60]}"')
    
    input('\n분석 완료. Enter를 누르면 브라우저가 닫힙니다...')
    publisher.logout()
else:
    print('❌ 로그인 실패')
