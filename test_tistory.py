"""티스토리 발행 테스트 - 이미지 포함"""
from src.publishers.tistory import TistoryPublisher
from src.ai.content_generator import ContentGenerator
import frontmatter
from pathlib import Path

# 기존 초안 사용 (새로 생성하지 않음)
gen = ContentGenerator()
drafts = gen.list_drafts()

# 맛집_광주_황금들판 초안 찾기
latest = None
for d in drafts:
    if '황금들판' in d['path'].name:
        latest = d
        break

if not latest:
    print('❌ 황금들판 초안을 찾을 수 없습니다.')
    exit()

post = frontmatter.load(latest['path'])
print(f'✅ 초안 로드: {latest["path"]}')

# 리라이팅 없이 원본 사용
title = post.get('title', '테스트 제목') + " (이미지테스트)"
content = post.content
print(f'📌 제목: {title}')
print(f'📌 카테고리: {post.get("category", "없음")}')

# 이미지 포함
input_dir = post.get('input_dir')
images = None
if input_dir:
    media_dir = Path(input_dir) / 'media'
    if media_dir.exists():
        images = [str(f) for f in sorted(media_dir.iterdir()) if f.is_file()][:2]  # 처음 2개만
        print(f'📷 이미지: {len(images)}개 - {[Path(i).name for i in images]}')

# 티스토리 발행
print('\n🚀 티스토리 발행 시작...')
publisher = TistoryPublisher(headless=False)
if publisher.login():
    print('✅ 로그인 성공')
    result = publisher.publish(
        title=title,
        content=content,
        category=post.get('category'),
        tags=post.get('keywords', []),
        images=images
    )
    print(f'📊 발행 결과: {result}')
    input('테스트 완료. Enter를 누르면 브라우저가 닫힙니다...')
    publisher.logout()
else:
    print('❌ 로그인 실패')
