"""
멀티 블로그 자동 포스팅 시스템 - 메인 실행 파일
"""
# TODO: CLI 인터페이스 구현
# 
# 주요 명령어:
#
# [Git 동기화]
# - python main.py sync pull      : GitLab에서 최신 상태 pull
# - python main.py sync push      : 변경사항 GitLab에 push
#
# [글 작성]
# - python main.py new            : 새 글 작성 (input/ 폴더 기반으로 AI 초안 생성)
# - python main.py draft list     : 초안 목록 조회
# - python main.py draft preview  : 초안 미리보기
# - python main.py approve        : 초안 승인 → approved/ 폴더로 이동
#
# [플랫폼별 변환]
# - python main.py convert        : 원본 글 → 네이버/티스토리/워드프레스 버전 생성
# - python main.py convert --preview : 변환된 버전 미리보기
#
# [발행]
# - python main.py publish        : 모든 플랫폼에 발행
# - python main.py publish --platform naver   : 네이버에만 발행
# - python main.py publish --platform tistory : 티스토리에만 발행
# - python main.py publish --platform wordpress : 워드프레스에만 발행
