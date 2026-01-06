"""티스토리 이미지 업로드 폴링 방식 테스트"""
from src.publishers.tistory import TistoryPublisher
from pathlib import Path
import logging

logging.basicConfig(level=logging.DEBUG)

# 이미지 찾기
media_dir = Path("input/2026/01/맛집_광주_황금들판/media")
images = [str(f) for f in media_dir.iterdir() if f.is_file()] if media_dir.exists() else []
print(f"📷 테스트 이미지: {len(images)}개")

# 발행 테스트
publisher = TistoryPublisher(headless=False)
if publisher.login():
    print("✅ 로그인 성공")
    
    result = publisher.publish(
        title="[테스트] 이미지 업로드 폴링 테스트",
        content="<p>이미지 업로드 폴링 방식 테스트입니다.</p>",
        images=images
    )
    print(f"📊 결과: {result}")
    input("Enter를 누르면 종료...")
    publisher.logout()
else:
    print("❌ 로그인 실패")
