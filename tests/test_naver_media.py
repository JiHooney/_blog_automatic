import frontmatter

from src.publishers.base import resolve_media_files
from src.publishers.naver import NaverPublisher


def test_media_name_normalization_matches_macos_nfd_and_markdown_nfc():
    nfc = "00_세련된입구.jpeg"
    nfd = "00_세련된입구.jpeg"

    assert NaverPublisher._normalize_media_name(nfc) == NaverPublisher._normalize_media_name(nfd)


def test_media_number_prefix_can_match_when_description_changed():
    path = "/tmp/09.jpeg"
    media_map = {"09_저희는 로얄룸이었습니다.jpeg": path}

    assert NaverPublisher._find_media_path(
        "09_저희는스위트룸이었습니다.jpeg", media_map
    ) == path


def test_resolve_media_files_uses_generated_draft_input_dir(tmp_path):
    input_dir = tmp_path / "input" / "post"
    media_dir = input_dir / "media"
    generated_dir = input_dir / "generated"
    media_dir.mkdir(parents=True)
    generated_dir.mkdir()
    image = media_dir / "사진.jpeg"
    image.write_bytes(b"image")

    draft = generated_dir / "draft.md"
    post = frontmatter.Post("본문", input_dir=str(input_dir), title="제목")
    draft.write_text(frontmatter.dumps(post), encoding="utf-8")

    assert resolve_media_files(draft) == [image]
