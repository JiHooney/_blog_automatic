#!/usr/bin/env python
"""
블로그 자동 발행 시스템 - CLI 진입점
"""
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
ROOT_DIR = Path(__file__).parent
sys.path.insert(0, str(ROOT_DIR))

from src.cli.main import app

if __name__ == "__main__":
    app()
