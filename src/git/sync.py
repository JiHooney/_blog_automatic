"""
GitLab 동기화 모듈
- git pull: 작업 시작 전 최신 상태 동기화
- git add/commit/push: 작업 완료 후 변경사항 업로드
"""
import os
from git import Repo, GitCommandError
from loguru import logger


class GitSync:
    """Git 저장소 동기화 클래스"""
    
    def __init__(self, repo_path: str = None):
        """
        Args:
            repo_path: Git 저장소 경로. None이면 현재 디렉터리 사용
        """
        self.repo_path = repo_path or os.getcwd()
        self.repo = None
        self._init_repo()
    
    def _init_repo(self):
        """Git 저장소 초기화"""
        try:
            self.repo = Repo(self.repo_path)
            logger.info(f"Git 저장소 연결됨: {self.repo_path}")
        except Exception as e:
            logger.error(f"Git 저장소를 찾을 수 없습니다: {e}")
            raise
    
    def pull(self) -> bool:
        """원격 저장소에서 최신 변경사항 가져오기"""
        try:
            origin = self.repo.remotes.origin
            origin.pull()
            logger.success("✅ Git pull 완료")
            return True
        except GitCommandError as e:
            logger.error(f"❌ Git pull 실패: {e}")
            return False
    
    def push(self, commit_message: str = None) -> bool:
        """변경사항을 원격 저장소에 푸시
        
        Args:
            commit_message: 커밋 메시지. None이면 자동 생성
        """
        try:
            # 변경된 파일이 있으면 커밋
            if self.repo.is_dirty() or self.repo.untracked_files:
                # 모든 변경사항 스테이징
                self.repo.git.add(A=True)
                
                # 커밋 메시지 생성
                if commit_message is None:
                    from datetime import datetime
                    commit_message = f"Auto commit: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                
                # 커밋
                self.repo.index.commit(commit_message)
                logger.info(f"커밋 완료: {commit_message}")
            
            # 원격과 비교하여 푸시할 커밋이 있는지 확인
            origin = self.repo.remotes.origin
            
            # fetch하여 원격 정보 업데이트
            origin.fetch()
            
            # 로컬과 원격 비교
            local_commit = self.repo.head.commit
            try:
                remote_commit = self.repo.refs[f'origin/{self.repo.active_branch.name}'].commit
                commits_ahead = list(self.repo.iter_commits(f'origin/{self.repo.active_branch.name}..HEAD'))
                
                if not commits_ahead:
                    logger.info("원격 저장소와 동기화 상태입니다.")
                    return True
                    
                logger.info(f"푸시할 커밋: {len(commits_ahead)}개")
            except (IndexError, KeyError):
                # 원격 브랜치가 없는 경우 (새 브랜치)
                logger.info("원격 브랜치가 없습니다. 새로 푸시합니다.")
            
            # 푸시
            origin.push()
            logger.success("✅ Git push 완료")
            return True
            
        except GitCommandError as e:
            logger.error(f"❌ Git push 실패: {e}")
            return False
    
    def status(self) -> dict:
        """현재 Git 상태 확인"""
        result = {
            "branch": self.repo.active_branch.name,
            "is_dirty": self.repo.is_dirty(),
            "untracked_files": self.repo.untracked_files,
            "modified_files": [item.a_path for item in self.repo.index.diff(None)],
            "staged_files": [],
        }
        
        # HEAD가 있을 때만 staged_files 확인 (첫 커밋 전에는 HEAD가 없음)
        try:
            result["staged_files"] = [item.a_path for item in self.repo.index.diff("HEAD")]
        except Exception:
            pass
        
        return result
    
    def show_status(self):
        """Git 상태를 보기 좋게 출력"""
        status = self.status()
        logger.info(f"📌 브랜치: {status['branch']}")
        
        if status['modified_files']:
            logger.info(f"📝 수정된 파일: {', '.join(status['modified_files'])}")
        if status['untracked_files']:
            logger.info(f"➕ 추적되지 않은 파일: {', '.join(status['untracked_files'])}")
        if status['staged_files']:
            logger.info(f"✅ 스테이징된 파일: {', '.join(status['staged_files'])}")
        
        if not status['is_dirty'] and not status['untracked_files']:
            logger.info("✨ 작업 디렉터리가 깨끗합니다.")
