"""
블로그 자동화 CLI
typer를 사용한 명령행 인터페이스
"""
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from pathlib import Path
from typing import Optional
from loguru import logger

app = typer.Typer(
    name="blog",
    help="🚀 블로그 자동 발행 시스템",
    add_completion=False
)

console = Console()


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
    if git.commit(message) and git.push():
        console.print("✅ Push 완료!", style="green")
    else:
        console.print("❌ Push 실패", style="red")


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
    all_posts: bool = typer.Option(False, "-a", "--all", help="모든 포스트 생성")
):
    """AI로 블로그 초안 생성"""
    from ..ai.content_generator import ContentGenerator
    
    gen = ContentGenerator()
    
    if path:
        # 특정 파일 생성
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("AI 초안 생성 중...", total=None)
            content = gen.generate_draft(path)
            progress.update(task, completed=True)
        
        console.print("✅ 초안 생성 완료!", style="green")
    elif all_posts or year or month:
        # 여러 포스트 생성
        generated = gen.generate_all_drafts(year=year, month=month)
        console.print(f"✅ {len(generated)}개 초안 생성 완료!", style="green")
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
        naver_content = rewriter.rewrite_content(content, "naver", title)
        publisher = NaverPublisher(headless=headless)
        if publisher.login():
            results['naver'] = publisher.publish(title=title, content=naver_content, tags=tags)
            publisher.logout()
        else:
            results['naver'] = False
    except Exception as e:
        console.print(f"❌ 네이버 발행 오류: {e}", style="red")
        results['naver'] = False
    
    # 티스토리 발행
    console.print("\n🟠 티스토리 블로그 발행 중...", style="cyan")
    try:
        tistory_content = rewriter.rewrite_content(content, "tistory", title)
        publisher = TistoryPublisher(headless=headless)
        if publisher.login():
            results['tistory'] = publisher.publish(title=title, content=tistory_content, tags=tags)
            publisher.logout()
        else:
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
        content = gen.generate_draft(input_path)
        progress.update(task, completed=True)
    
    # 최신 초안 가져오기
    drafts = gen.list_drafts()
    if not drafts:
        console.print("❌ 초안 생성 실패", style="red")
        return
    
    latest_draft = drafts[0]
    post = frontmatter.load(latest_draft['path'])
    
    console.print(f"✅ 초안 생성 완료: {latest_draft['path']}", style="green")
    
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


if __name__ == "__main__":
    app()
