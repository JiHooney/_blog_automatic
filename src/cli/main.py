"""
블로그 자동화 CLI
typer를 사용한 명령행 인터페이스
"""
import typer
from rich.console import Console
from rich.table import Table
from rich import box
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm
from pathlib import Path
from typing import Optional, List
from loguru import logger

from ..ai.client import AIClientError, AICreditBalanceError

app = typer.Typer(
    name="blog",
    help="🚀 블로그 자동 발행 시스템",
    add_completion=False,
    invoke_without_command=True
)

console = Console()


def _format_ai_error(error: Exception) -> str:
    """사용자에게 보여줄 AI 오류 메시지"""
    if isinstance(error, (AICreditBalanceError, AIClientError)):
        return str(error)
    return f"AI 처리 중 오류가 발생했습니다: {error}"


def _print_ai_error(error: Exception, indent: str = ""):
    console.print(f"{indent}❌ {_format_ai_error(error)}", style="red")


@app.callback()
def main(ctx: typer.Context):
    """🚀 블로그 자동 발행 시스템 - 인자 없이 실행하면 대화형 모드로 시작"""
    if ctx.invoked_subcommand is None:
        # 인자 없이 실행 시 대화형 모드
        interactive_mode()


# ============ Git 명령어 ============
git_app = typer.Typer(help="📂 Git 동기화 명령어")
app.add_typer(git_app, name="git")


@git_app.command("status")
def git_status():
    """Git 상태 확인"""
    from ..git.sync import GitSync
    
    git = GitSync()
    git.show_status()


@git_app.command("pull")
def git_pull():
    """원격 저장소에서 풀"""
    from ..git.sync import GitSync
    
    git = GitSync()
    if git.pull():
        console.print("✅ Pull 완료!", style="green")
    else:
        console.print("❌ Pull 실패", style="red")


@git_app.command("push")
def git_push(message: str = typer.Option("Auto commit", "-m", "--message", help="커밋 메시지")):
    """변경사항 커밋 및 푸시"""
    from ..git.sync import GitSync
    
    git = GitSync()
    if git.push(message):
        console.print("✅ Push 완료!", style="green")
    else:
        console.print("❌ Push 실패", style="red")


# ============ 서버 관리 명령어 ============
server_app = typer.Typer(help="🖥️ AI 서버 관리")
app.add_typer(server_app, name="server")


@server_app.command("start")
def server_start():
    """로컬 AI 서버 시작"""
    from ..utils.server_manager import get_server_manager

    console.print("🖥️ 로컬 AI 서버 시작 중...", style="cyan bold")

    manager = get_server_manager()
    if manager.start_server():
        console.print("✅ 서버 시작 완료!", style="green bold")
        console.print(f"📍 서버 URL: {manager.server_url}", style="dim")
        console.print("💡 다른 터미널에서 이 상태로 유지하세요.", style="yellow")
    else:
        console.print("❌ 서버 시작 실패", style="red bold")


@server_app.command("stop")
def server_stop():
    """로컬 AI 서버 중지"""
    from ..utils.server_manager import get_server_manager

    console.print("🖥️ 로컬 AI 서버 중지 중...", style="cyan bold")

    manager = get_server_manager()
    manager.stop_server()

    console.print("✅ 서버 중지 완료!", style="green bold")


@server_app.command("status")
def server_status():
    """서버 상태 확인"""
    from ..utils.server_manager import get_server_manager

    manager = get_server_manager()

    if manager.is_server_running():
        console.print("✅ 서버 실행 중", style="green bold")
        console.print(f"📍 URL: {manager.server_url}", style="dim")
    else:
        console.print("❌ 서버 중지됨", style="red bold")
        console.print("💡 시작하려면: python blog_cli.py server start", style="cyan")


# ============ 콘텐츠 명령어 ============
content_app = typer.Typer(help="📝 콘텐츠 생성 명령어")
app.add_typer(content_app, name="content")


@content_app.command("list")
def content_list(
    year: Optional[str] = typer.Option(None, "-y", "--year", help="연도 필터"),
    month: Optional[str] = typer.Option(None, "-m", "--month", help="월 필터")
):
    """입력 포스트 목록 조회"""
    from ..ai.content_generator import ContentGenerator
    
    gen = ContentGenerator()
    posts = gen.list_input_posts(year=year, month=month)
    
    if not posts:
        console.print("📭 입력 포스트가 없습니다.", style="yellow")
        return
    
    table = Table(title="📚 입력 포스트 목록")
    table.add_column("경로", style="cyan")
    table.add_column("제목", style="white")
    table.add_column("키워드", style="dim")
    table.add_column("미디어", justify="right")
    
    for post in posts:
        path = f"{post['year']}/{post['month']}/{post['folder_name']}"
        keywords = ", ".join(post['keywords'][:3]) + ("..." if len(post['keywords']) > 3 else "")
        table.add_row(path, post['title'], keywords, str(post['media_count']))
    
    console.print(table)


@content_app.command("generate")
def content_generate(
    path: Optional[str] = typer.Argument(None, help="특정 post.md 경로"),
    year: Optional[str] = typer.Option(None, "-y", "--year", help="연도 필터"),
    month: Optional[str] = typer.Option(None, "-m", "--month", help="월 필터"),
    all_posts: bool = typer.Option(False, "-a", "--all", help="모든 포스트 생성"),
    force: bool = typer.Option(False, "-f", "--force", help="기존 generated 초안 무시하고 재생성")
):
    """AI로 블로그 초안 생성 (발행하지 않음, generated 폴더에 저장)"""
    from ..ai.content_generator import ContentGenerator

    gen = ContentGenerator()

    if path:
        # 특정 파일 생성
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("AI 초안 생성 중...", total=None)

                if force:
                    # 강제 재생성 모드
                    import shutil
                    input_path = Path(path)
                    generated_dir = input_path.parent / "generated"
                    if generated_dir.exists():
                        shutil.rmtree(generated_dir)
                        console.print("🗑️ 기존 generated 폴더 삭제", style="yellow")

                draft_path = gen.generate_draft(path)
                progress.update(task, completed=True)

            console.print("✅ 초안 생성 완료!", style="green")
            console.print(f"📁 저장 위치: {draft_path}", style="dim")
            console.print("💡 발행하려면: python blog_cli.py publish all <초안경로>", style="cyan")
        except AIClientError as e:
            _print_ai_error(e)
    elif all_posts or year or month:
        # 여러 포스트 생성
        generated = gen.generate_all_drafts(year=year, month=month)
        console.print(f"✅ {len(generated)}개 초안 생성 완료!", style="green")
        console.print("💡 발행하려면: python blog_cli.py publish all <초안경로>", style="cyan")
    else:
        console.print("⚠️ 경로를 지정하거나 --all 옵션을 사용하세요.", style="yellow")


@content_app.command("drafts")
def content_drafts():
    """생성된 초안 목록 조회"""
    from ..ai.content_generator import ContentGenerator
    
    gen = ContentGenerator()
    drafts = gen.list_drafts()
    
    if not drafts:
        console.print("📭 초안이 없습니다.", style="yellow")
        return
    
    table = Table(title="📄 초안 목록")
    table.add_column("제목", style="white")
    table.add_column("생성일", style="cyan")
    table.add_column("상태", style="green")
    
    for draft in drafts[:10]:  # 최근 10개만
        table.add_row(
            draft['title'],
            draft['created_at'][:19] if draft['created_at'] else "N/A",
            draft['status']
        )
    
    console.print(table)


# ============ 발행 명령어 ============
publish_app = typer.Typer(help="🚀 블로그 발행 명령어")
app.add_typer(publish_app, name="publish")


@publish_app.command("naver")
def publish_naver(
    draft_path: str = typer.Argument(..., help="발행할 초안 파일 경로"),
    headless: bool = typer.Option(False, "--headless", help="헤드리스 모드")
):
    """네이버 블로그에 발행"""
    import frontmatter
    from ..publishers.naver import NaverPublisher
    
    # 초안 로드
    post = frontmatter.load(draft_path)
    
    console.print(f"📝 발행할 글: {post.get('title')}", style="cyan")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("네이버 블로그 발행 중...", total=None)
        
        publisher = NaverPublisher(headless=headless)
        if publisher.login():
            result = publisher.publish(
                title=post.get('title', '제목 없음'),
                content=post.content,
                tags=post.get('keywords', [])
            )
            publisher.logout()
            progress.update(task, completed=True)
            
            if result:
                console.print("✅ 네이버 발행 완료!", style="green")
            else:
                console.print("❌ 네이버 발행 실패", style="red")
        else:
            console.print("❌ 네이버 로그인 실패", style="red")


@publish_app.command("tistory")
def publish_tistory(
    draft_path: str = typer.Argument(..., help="발행할 초안 파일 경로"),
    headless: bool = typer.Option(False, "--headless", help="헤드리스 모드")
):
    """티스토리 블로그에 발행"""
    import frontmatter
    from ..publishers.tistory import TistoryPublisher
    
    # 초안 로드
    post = frontmatter.load(draft_path)
    
    console.print(f"📝 발행할 글: {post.get('title')}", style="cyan")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("티스토리 블로그 발행 중...", total=None)
        
        publisher = TistoryPublisher(headless=headless)
        if publisher.login():
            result = publisher.publish(
                title=post.get('title', '제목 없음'),
                content=post.content,
                tags=post.get('keywords', [])
            )
            publisher.logout()
            progress.update(task, completed=True)
            
            if result:
                console.print("✅ 티스토리 발행 완료!", style="green")
            else:
                console.print("❌ 티스토리 발행 실패", style="red")
        else:
            console.print("❌ 티스토리 로그인 실패", style="red")


@publish_app.command("all")
def publish_all(
    draft_path: str = typer.Argument(..., help="발행할 초안 파일 경로"),
    headless: bool = typer.Option(False, "--headless", help="헤드리스 모드")
):
    """모든 블로그에 발행 (네이버 + 티스토리)"""
    import frontmatter
    from ..publishers.naver import NaverPublisher
    from ..publishers.tistory import TistoryPublisher
    from ..ai.rewriter import PlatformRewriter
    
    # 초안 로드
    post = frontmatter.load(draft_path)
    title = post.get('title', '제목 없음')
    content = post.content
    tags = post.get('keywords', [])
    
    console.print(Panel(f"📝 {title}", title="발행할 글"))
    
    # 플랫폼별 리라이팅
    rewriter = PlatformRewriter()
    
    results = {}
    
    # 네이버 발행
    console.print("\n🟢 네이버 블로그 발행 중...", style="cyan")
    try:
        naver_title, naver_content = rewriter.rewrite_content(content, "naver", title)
        publisher = NaverPublisher(headless=headless)
        if publisher.login():
            results['naver'] = publisher.publish(title=naver_title, content=naver_content, tags=tags)
            publisher.logout()
        else:
            results['naver'] = False
    except AIClientError as e:
        _print_ai_error(e)
        results['naver'] = False
    except Exception as e:
        console.print(f"❌ 네이버 발행 오류: {e}", style="red")
        results['naver'] = False
    
    # 티스토리 발행
    console.print("\n🟠 티스토리 블로그 발행 중...", style="cyan")
    try:
        tistory_title, tistory_content = rewriter.rewrite_content(content, "tistory", title)
        publisher = TistoryPublisher(headless=headless)
        if publisher.login():
            results['tistory'] = publisher.publish(title=tistory_title, content=tistory_content, tags=tags)
            publisher.logout()
        else:
            results['tistory'] = False
    except AIClientError as e:
        _print_ai_error(e)
        results['tistory'] = False
    except Exception as e:
        console.print(f"❌ 티스토리 발행 오류: {e}", style="red")
        results['tistory'] = False
    
    # 결과 출력
    console.print("\n" + "="*50)
    console.print("📊 발행 결과:", style="bold")
    for platform, success in results.items():
        status = "✅ 성공" if success else "❌ 실패"
        console.print(f"  {platform}: {status}")


# ============ 전체 워크플로우 ============
@app.command("run")
def run_workflow(
    input_path: str = typer.Argument(..., help="입력 post.md 경로"),
    platforms: str = typer.Option("all", "-p", "--platforms", help="발행 플랫폼 (naver,tistory,all)"),
    skip_confirm: bool = typer.Option(False, "-y", "--yes", help="확인 없이 바로 발행"),
    headless: bool = typer.Option(False, "--headless", help="헤드리스 모드")
):
    """전체 워크플로우 실행 (생성 → 확인 → 발행)"""
    import frontmatter
    from ..ai.content_generator import ContentGenerator
    from ..ai.rewriter import PlatformRewriter
    from ..publishers.naver import NaverPublisher
    from ..publishers.tistory import TistoryPublisher
    
    console.print(Panel("🚀 블로그 자동 발행 시스템", style="bold blue"))
    
    # 1. 초안 생성
    console.print("\n[1/3] 📝 AI 초안 생성 중...", style="cyan bold")
    gen = ContentGenerator()
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Claude API 호출 중...", total=None)
        try:
            draft_path = gen.generate_draft(input_path)
            progress.update(task, completed=True)
        except AIClientError as e:
            progress.stop()
            _print_ai_error(e)
            return
    
    if not draft_path:
        console.print("❌ 초안 생성 실패", style="red")
        return
    
    post = frontmatter.load(draft_path)
    
    console.print(f"✅ 초안 준비 완료: {draft_path}", style="green")
    
    # 2. 사용자 확인
    if not skip_confirm:
        console.print("\n[2/3] 👀 초안 미리보기:", style="cyan bold")
        console.print(Panel(post.content[:500] + "..." if len(post.content) > 500 else post.content))
        
        confirm = typer.confirm("이 내용으로 발행하시겠습니까?")
        if not confirm:
            console.print("발행이 취소되었습니다.", style="yellow")
            return
    
    # 3. 발행
    console.print("\n[3/3] 🚀 블로그 발행 중...", style="cyan bold")
    
    original_title = post.get('title', '제목 없음')
    tags = post.get('keywords', [])
    category = post.get('category', None)  # 카테고리
    input_dir = post.get('input_dir', None)  # 이미지 경로용
    rewriter = PlatformRewriter()
    
    target_platforms = []
    if platforms == "all":
        target_platforms = ["naver", "tistory"]
    else:
        target_platforms = [p.strip() for p in platforms.split(",")]
    
    results = {}
    
    for platform in target_platforms:
        console.print(f"\n  📤 {platform} 발행 중...", style="dim")
        
        try:
            # 플랫폼별로 다른 제목과 내용 생성 (리라이팅)
            platform_title, platform_content = rewriter.rewrite_content(post.content, platform, original_title)
            console.print(f"    📝 {platform} 제목: {platform_title}", style="dim")
            
            if platform == "naver":
                publisher = NaverPublisher(headless=headless)
            elif platform == "tistory":
                publisher = TistoryPublisher(headless=headless)
            else:
                console.print(f"  ⚠️ 지원하지 않는 플랫폼: {platform}", style="yellow")
                continue
            
            if publisher.login():
                # 플랫폼별 다른 제목 사용, 이미지 경로 전달
                results[platform] = publisher.publish(
                    title=platform_title, 
                    content=platform_content, 
                    category=category,
                    tags=tags,
                    images=[str(f) for f in (Path(input_dir) / "media").iterdir()] if input_dir and (Path(input_dir) / "media").exists() else None
                )
                publisher.logout()
            else:
                results[platform] = False
                
        except Exception as e:
            console.print(f"  ❌ {platform} 오류: {e}", style="red")
            results[platform] = False
    
    # 결과 출력
    console.print("\n" + "="*50)
    console.print("📊 최종 결과:", style="bold")
    for platform, success in results.items():
        status = "✅ 성공" if success else "❌ 실패"
        console.print(f"  {platform}: {status}")
    
    success_count = sum(1 for v in results.values() if v)
    console.print(f"\n🎉 {success_count}/{len(results)} 블로그 발행 완료!", style="green bold")


@app.command("version")
def version():
    """버전 정보 출력"""
    console.print(Panel(
        "[bold]블로그 자동 발행 시스템[/bold]\n"
        "버전: 1.0.0\n"
        "지원 플랫폼: 네이버, 티스토리",
        title="ℹ️ 정보"
    ))


def interactive_mode():
    """대화형 모드 - 메뉴 선택"""
    console.print(Panel("🚀 블로그 자동 발행 시스템", style="bold blue"))
    
    # 메뉴 선택
    console.print("\n무엇을 하시겠습니까?", style="cyan bold")
    console.print("  [1] 📝 발행할 글 준비 (새 포스트 폴더 생성)")
    console.print("  [2] 🚀 블로그 발행 (AI 초안 생성 → 발행)")
    console.print("  [0] 종료")
    
    choice = Prompt.ask("\n선택", choices=["0", "1", "2"], default="2")
    
    if choice == "0":
        console.print("👋 종료합니다.", style="dim")
        return
    elif choice == "1":
        prepare_post_mode()
    elif choice == "2":
        publish_mode()


def prepare_post_mode():
    """발행할 글 준비 모드 - 새 포스트 폴더 생성"""
    from datetime import datetime
    import os
    
    console.print(Panel("📝 발행할 글 준비", style="bold green"))
    
    # 현재 날짜 기준으로 경로 생성
    now = datetime.now()
    year = now.strftime("%Y")
    month = now.strftime("%m")
    
    base_path = Path(__file__).parent.parent.parent / "input" / year / month
    
    # 디렉터리 생성 (없으면)
    if not base_path.exists():
        base_path.mkdir(parents=True)
        console.print(f"  📁 디렉터리 생성: input/{year}/{month}/", style="green")
    else:
        console.print(f"  📁 디렉터리 존재: input/{year}/{month}/", style="dim")
    
    # 디렉터리명 입력 안내
    console.print("\n📌 디렉터리명 형식:", style="cyan bold")
    console.print("  {구분1}_{구분2}_{구분3}")
    console.print("  예시: [dim]맛집_강남역_OO식당[/dim], [dim]숙박_제주도_OO호텔[/dim], [dim]여행_부산_해운대[/dim]")
    console.print("\n  ⚠️ [yellow]띄어쓰기 사용 불가![/yellow]", style="bold")
    
    # 디렉터리명 입력 (띄어쓰기 검증)
    while True:
        dir_name = Prompt.ask("\n  디렉터리명 입력")
        
        if not dir_name.strip():
            console.print("  ❌ 디렉터리명을 입력해주세요.", style="red")
            continue
        
        if " " in dir_name:
            console.print("  ❌ 띄어쓰기가 포함되어 있습니다. 다시 입력해주세요.", style="red")
            continue
        
        if "_" not in dir_name:
            console.print("  ⚠️ 형식이 올바르지 않습니다. {구분1}_{구분2}_{구분3} 형식으로 입력해주세요.", style="yellow")
            if not Confirm.ask("  그래도 계속하시겠습니까?"):
                continue
        
        break
    
    # 포스트 디렉터리 생성
    post_path = base_path / dir_name
    
    if post_path.exists():
        console.print(f"  ⚠️ 이미 존재하는 디렉터리입니다: {dir_name}", style="yellow")
        if not Confirm.ask("  덮어쓰시겠습니까?"):
            console.print("  취소되었습니다.", style="dim")
            return
    
    post_path.mkdir(parents=True, exist_ok=True)
    
    # media 디렉터리 생성
    media_path = post_path / "media"
    media_path.mkdir(exist_ok=True)
    
    # 카테고리 추출 (첫 번째 구분)
    category = dir_name.split("_")[0] if "_" in dir_name else ""
    
    # post.md 템플릿 생성
    post_md_content = f"""---
title: "{dir_name.replace('_', ' ')}"
keywords:
  - 키워드1
  - 키워드2
  - 키워드3
category: "{category}"
persona: "friendly_man"
---

## 방문 정보
- 위치: 
- 영업시간: 
- 주차: 

## 주요 내용
- 

## 사진 설명
<!-- media 폴더의 이미지 파일명과 설명을 작성하세요 -->
- 1.jpg: 
- 2.jpg: 
- 3.jpg: 
"""
    
    post_md_path = post_path / "post.md"
    with open(post_md_path, "w", encoding="utf-8") as f:
        f.write(post_md_content)
    
    # 결과 출력
    console.print("\n" + "="*50)
    console.print("✅ 포스트 폴더 생성 완료!", style="green bold")
    console.print(f"\n  📂 경로: input/{year}/{month}/{dir_name}/")
    console.print("  📄 post.md - 내용을 작성하세요")
    console.print("  📁 media/ - 이미지 파일을 넣으세요")
    console.print("\n💡 작성 완료 후 [cyan]python main.py[/cyan] → [cyan]블로그 발행[/cyan]을 선택하세요!")


def publish_mode():
    """블로그 발행 모드 - 기존 interactive_mode 로직"""
    import frontmatter
    from ..ai.content_generator import ContentGenerator
    from ..ai.rewriter import PlatformRewriter
    from ..publishers.naver import NaverPublisher
    from ..publishers.tistory import TistoryPublisher
    
    console.print(Panel("🚀 블로그 발행", style="bold blue"))
    
    # 1. 입력 포스트 목록 조회
    console.print("\n[1/3] 📚 입력 포스트 확인 중...", style="cyan bold")
    gen = ContentGenerator()
    posts = gen.list_input_posts()
    
    if not posts:
        console.print("  📭 발행할 포스트가 없습니다.", style="yellow")
        console.print("  💡 input/YYYY/MM/{카테고리}_{주제}/ 폴더에 post.md를 생성하세요.", style="dim")
        return
    
    # 최신 업데이트순 + 미발행 우선 정렬, 상위 10개만 표시
    def is_published_any(p: dict) -> bool:
        pub = p.get('published', {})
        return bool(pub.get('naver')) or bool(pub.get('tistory'))

    sorted_posts = sorted(
        posts,
        key=lambda p: (1 if is_published_any(p) else 0, -(p.get('updated_ts') or 0))
    )
    display_posts = sorted_posts[:10]

    # 테이블 출력 (고정 폭 + 줄바꿈 방지)
    def truncate(text: str, width: int) -> str:
        if text is None:
            return "-"
        text = str(text)
        return text if len(text) <= width else text[: max(0, width - 1)] + "…"

    table = Table(
        title="📚 입력 포스트 목록 (최신 10개)",
        box=box.SIMPLE_HEAVY,
        show_lines=False
    )
    table.add_column("번호", style="bold cyan", justify="right", no_wrap=True, max_width=4)
    table.add_column("업데이트", style="cyan", no_wrap=True, max_width=16)
    table.add_column("경로", style="white", no_wrap=True, overflow="ellipsis", max_width=18)
    table.add_column("제목/키워드", style="dim", no_wrap=True, overflow="ellipsis", max_width=24)
    table.add_column("카테고리", style="magenta", no_wrap=True, max_width=8)
    table.add_column("미디어", justify="right", no_wrap=True, max_width=6)
    table.add_column("발행", justify="center", no_wrap=True, max_width=6)

    for i, post in enumerate(display_posts, 1):
        path = f"{post['year']}/{post['month']}/{post['folder_name']}"
        keywords = ", ".join(post['keywords'][:2]) if post['keywords'] else post['title']
        category = post.get('category', '-')

        # 발행 상태 표시
        published = post.get('published', {})
        naver_pub = "N" if published.get('naver') else "-"
        tistory_pub = "T" if published.get('tistory') else "-"
        pub_status = f"[green]{naver_pub}[/green] [blue]{tistory_pub}[/blue]"

        table.add_row(
            str(i),
            truncate(post.get('updated_at', '-') or '-', 16),
            truncate(path, 18),
            truncate(keywords, 24),
            truncate(category, 8),
            str(post['media_count']),
            pub_status
        )

    console.print(table)
    console.print("  [dim]발행: N=네이버, T=티스토리, -=미발행[/dim]")
    
    # 2. 발행할 글 선택
    console.print("\n[2/3] 🎯 발행할 글 선택", style="cyan bold")
    console.print("  여러 개 선택: 1,2,3 또는 범위: 1-3 또는 전체: all", style="dim")
    
    selection = Prompt.ask("  발행할 글 번호", default="1")
    
    # 선택 파싱
    selected_indices: List[int] = []
    if selection.lower() == "all":
        selected_indices = list(range(len(posts)))
    elif "-" in selection:
        try:
            start, end = selection.split("-")
            selected_indices = list(range(int(start) - 1, int(end)))
        except:
            console.print("  ❌ 잘못된 입력입니다.", style="red")
            return
    else:
        try:
            selected_indices = [int(x.strip()) - 1 for x in selection.split(",")]
        except:
            console.print("  ❌ 잘못된 입력입니다.", style="red")
            return
    
    # 범위 검증
    selected_indices = [i for i in selected_indices if 0 <= i < len(display_posts)]
    if not selected_indices:
        console.print("  ❌ 선택된 글이 없습니다.", style="red")
        return
    
    selected_posts = [display_posts[i] for i in selected_indices]
    console.print(f"  ✅ {len(selected_posts)}개 글 선택됨", style="green")
    
    # 플랫폼 선택
    platform_choice = Prompt.ask(
        "  발행 플랫폼",
        choices=["all", "naver", "tistory"],
        default="all"
    )
    
    target_platforms = ["naver", "tistory"] if platform_choice == "all" else [platform_choice]
    
    # 이미 발행된 글 확인
    already_published = []
    for post_info in selected_posts:
        published = post_info.get('published', {})
        pub_platforms = []
        for platform in target_platforms:
            if published.get(platform):
                pub_platforms.append(f"{platform}({published[platform]})")
        if pub_platforms:
            already_published.append({
                'folder_name': post_info['folder_name'],
                'platforms': pub_platforms
            })
    
    # 이미 발행된 글이 있으면 경고
    if already_published:
        console.print("\n  ⚠️ 이미 발행된 글이 있습니다:", style="yellow bold")
        for item in already_published:
            console.print(f"    - {item['folder_name']}: {', '.join(item['platforms'])}", style="yellow")
        
        if not Confirm.ask("\n  이미 발행된 글을 다시 발행하시겠습니까?"):
            # 발행된 글 제외
            published_folders = {item['folder_name'] for item in already_published}
            selected_posts = [p for p in selected_posts if p['folder_name'] not in published_folders]
            
            if not selected_posts:
                console.print("  발행할 글이 없습니다.", style="yellow")
                return
            
            console.print(f"  ✅ {len(selected_posts)}개 미발행 글만 진행", style="green")
    
    # 최종 확인
    if not Confirm.ask(f"\n  {len(selected_posts)}개 글을 {platform_choice}에 발행하시겠습니까?"):
        console.print("  발행이 취소되었습니다.", style="yellow")
        return
    
    # 3. 발행 실행
    console.print("\n[3/3] 🚀 블로그 발행 중...", style="cyan bold")
    
    target_platforms = ["naver", "tistory"] if platform_choice == "all" else [platform_choice]
    rewriter = PlatformRewriter()
    
    total_results = {}
    
    for idx, post_info in enumerate(selected_posts, 1):
        console.print(f"\n  📝 [{idx}/{len(selected_posts)}] {post_info['folder_name']}", style="bold")
        
        # AI 초안 생성
        console.print("    🤖 AI 초안 생성 중...", style="dim")
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("    Claude API 호출 중...", total=None)
                draft_path = gen.generate_draft(post_info['path'])
                progress.update(task, completed=True)

            # generated 폴더의 초안 사용 여부 표시
            if draft_path and "generated" in str(draft_path):
                console.print("    ✅ generated 폴더의 기존 초안 사용", style="green dim")
        except AIClientError as e:
            _print_ai_error(e, indent="    ")
            total_results[f"{post_info['folder_name']}_draft"] = False
            continue
        
        if not draft_path:
            console.print("    ❌ 초안 생성 실패", style="red")
            continue
        
        post = frontmatter.load(draft_path)
        
        original_title = post.get('title', '제목 없음')
        tags = post.get('keywords', [])
        category = post.get('category', None)
        input_dir = post.get('input_dir', None)
        
        # 플랫폼별 발행
        for platform in target_platforms:
            console.print(f"    📤 {platform} 발행 중...", style="dim")
            
            try:
                platform_title, platform_content = rewriter.rewrite_content(
                    post.content, platform, original_title
                )
                
                if platform == "naver":
                    publisher = NaverPublisher(headless=False)
                elif platform == "tistory":
                    publisher = TistoryPublisher(headless=False)
                else:
                    continue
                
                if publisher.login():
                    success = publisher.publish(
                        title=platform_title,
                        content=platform_content,
                        category=category,
                        tags=tags,
                        images=[str(f) for f in (Path(input_dir) / "media").iterdir()] 
                            if input_dir and (Path(input_dir) / "media").exists() else None
                    )
                    publisher.logout()
                    
                    key = f"{post_info['folder_name']}_{platform}"
                    total_results[key] = success
                    
                    if success:
                        console.print(f"    ✅ {platform} 발행 성공", style="green")
                        # 발행 성공 시 기록
                        ContentGenerator.mark_as_published(post_info['dir'], platform)
                    else:
                        console.print(f"    ❌ {platform} 발행 실패", style="red")
                else:
                    total_results[f"{post_info['folder_name']}_{platform}"] = False
                    console.print(f"    ❌ {platform} 로그인 실패", style="red")
            except AIClientError as e:
                _print_ai_error(e, indent="    ")
                total_results[f"{post_info['folder_name']}_{platform}"] = False
            except Exception as e:
                console.print(f"    ❌ {platform} 오류: {e}", style="red")
                total_results[f"{post_info['folder_name']}_{platform}"] = False
    
    # 최종 결과
    console.print("\n" + "="*50)
    console.print("📊 최종 결과:", style="bold")
    
    success_count = sum(1 for v in total_results.values() if v)
    total_count = len(total_results)
    
    for key, success in total_results.items():
        status = "✅" if success else "❌"
        console.print(f"  {status} {key}")
    
    console.print(f"\n🎉 {success_count}/{total_count} 발행 완료!", style="green bold")


if __name__ == "__main__":
    app()
