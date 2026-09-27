from pathlib import Path

import frontmatter

from src.ai.content_generator import ContentGenerator
from src.ai.prompt_builder import PromptBuilder


def test_friendly_man_is_a_supported_persona():
    prompt = PromptBuilder.__new__(PromptBuilder)
    prompt.guidelines = {}

    result = prompt.build_system_prompt("friendly_man")

    assert "친근한 젊은 남자 스타일" in result
    assert "여성적인 애교체나 과도한 이모지는 사용하지 않습니다" in result


def test_rewrite_prompts_keep_selected_persona():
    prompt = PromptBuilder.__new__(PromptBuilder)
    prompt.guidelines = {}

    system = prompt.build_platform_rewrite_prompt("naver", "friendly_man")
    user = prompt.build_rewrite_prompt("본문", "naver", "제목", "friendly_man")

    assert "반드시 유지할 페르소나: friendly_man" in system
    assert "코드: friendly_man" in user


def test_generated_drafts_are_reused_only_for_matching_current_persona(tmp_path):
    post_dir = tmp_path / "post"
    generated_dir = post_dir / "generated"
    generated_dir.mkdir(parents=True)
    input_path = post_dir / "post.md"
    input_path.write_text("---\npersona: friendly_man\n---\n", encoding="utf-8")

    old_draft = generated_dir / "old.md"
    old_draft.write_text(
        frontmatter.dumps(frontmatter.Post("구 초안", persona="friendly_man")),
        encoding="utf-8",
    )
    woman_draft = generated_dir / "woman.md"
    woman_draft.write_text(
        frontmatter.dumps(
            frontmatter.Post(
                "여자 초안",
                persona="friendly_woman",
                persona_prompt_version=ContentGenerator.PERSONA_PROMPT_VERSION,
            )
        ),
        encoding="utf-8",
    )
    man_draft = generated_dir / "man.md"
    man_draft.write_text(
        frontmatter.dumps(
            frontmatter.Post(
                "남자 초안",
                persona="friendly_man",
                persona_prompt_version=ContentGenerator.PERSONA_PROMPT_VERSION,
            )
        ),
        encoding="utf-8",
    )

    generator = ContentGenerator.__new__(ContentGenerator)
    assert generator._get_generated_drafts(input_path, "friendly_man") == [man_draft]
    assert generator._get_generated_drafts(input_path, "friendly_woman") == [woman_draft]
