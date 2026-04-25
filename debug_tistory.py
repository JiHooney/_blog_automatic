"""티스토리 에디터 구조 분석"""
import os
import time
from dotenv import load_dotenv
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

load_dotenv()

from src.utils.browser import BrowserManager
from src.publishers.tistory import TistoryPublisher

# 티스토리 로그인
publisher = TistoryPublisher()
publisher.login()

# 글쓰기 페이지로 이동
blog_name = os.getenv("TISTORY_BLOG_NAME")
publisher.driver.get(f"https://{blog_name}.tistory.com/manage/newpost")
time.sleep(3)

# 알림창 처리
try:
    alert = publisher.driver.switch_to.alert
    print(f"알림창 감지: {alert.text}")
    alert.dismiss()  # "취소" 클릭 - 새 글 작성
    print("알림창 닫음")
    time.sleep(1)
except:
    print("알림창 없음")

# 에디터 구조 분석
print("\n=== 티스토리 에디터 구조 분석 ===\n")

# 1. 모든 iframe 확인
iframes = publisher.driver.find_elements(By.TAG_NAME, "iframe")
print(f"1. iframe 개수: {len(iframes)}")
for i, iframe in enumerate(iframes):
    print(f"   - iframe[{i}] id={iframe.get_attribute('id')}, class={iframe.get_attribute('class')}")

# 2. contenteditable 요소 확인
editables = publisher.driver.find_elements(By.CSS_SELECTOR, "[contenteditable='true']")
print(f"\n2. contenteditable 요소 개수: {len(editables)}")
for i, elem in enumerate(editables):
    print(f"   - [{i}] tag={elem.tag_name}, class={elem.get_attribute('class')[:50] if elem.get_attribute('class') else 'None'}")

# 3. 에디터 관련 요소 확인
editor_selectors = [
    "#editor-root",
    ".editor",
    "[class*='editor']",
    ".ProseMirror",
    "#content",
    "textarea"
]
print("\n3. 에디터 관련 요소:")
for selector in editor_selectors:
    try:
        elems = publisher.driver.find_elements(By.CSS_SELECTOR, selector)
        if elems:
            print(f"   - {selector}: {len(elems)}개 발견")
            for elem in elems[:2]:
                tag = elem.tag_name
                cls = elem.get_attribute('class')[:50] if elem.get_attribute('class') else 'None'
                print(f"      → tag={tag}, class={cls}")
    except:
        pass

# 4. iframe 내부 분석
print("\n4. iframe 내부 분석:")
for i, iframe in enumerate(iframes):
    try:
        publisher.driver.switch_to.frame(iframe)
        body = publisher.driver.find_element(By.TAG_NAME, "body")
        is_editable = body.get_attribute("contenteditable")
        body_class = body.get_attribute("class")
        body_html = body.get_attribute("innerHTML")[:200] if body.get_attribute("innerHTML") else "empty"
        print(f"   - iframe[{i}]: contenteditable={is_editable}, class={body_class}")
        print(f"     HTML: {body_html[:100]}...")
        publisher.driver.switch_to.default_content()
    except Exception as e:
        print(f"   - iframe[{i}]: 접근 실패 - {e}")
        publisher.driver.switch_to.default_content()

print("\n=== 분석 완료 ===")
print("\n브라우저를 확인하세요. 종료하려면 Enter를 누르세요...")
input()

publisher.logout()
