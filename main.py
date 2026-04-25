"""
멀티 블로그 자동 포스팅 시스템 - 메인 실행 파일

사용법:
    python main.py                    : 대화형 모드 (추천)
    python main.py --help             : 도움말 표시
    python main.py git status         : Git 상태 확인
    python main.py git pull           : 원격에서 풀
    python main.py git push -m "msg"  : 푸시
    python main.py content list       : 입력 포스트 목록
    python main.py content generate   : AI 초안 생성
    python main.py publish all        : 블로그 발행
"""
from src.cli.main import app

if __name__ == "__main__":
    app()
