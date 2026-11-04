import re
from pathlib import Path

from repo_paths import REPO_ROOT

PLUGIN_SKILL_ROOTS = sorted(REPO_ROOT.glob("plugins/*/skills"))
HARDCODED_PATH = b".claude/skills/"
# mkskill names the user's own skill folders on purpose
HARDCODED_PATH_ALLOWED = (REPO_ROOT / "plugins/claude/skills/mkskill/SKILL.md",)
PLACEHOLDERS = ("SKILL_DIR/", "SKILLS_ROOT/")
SKILL_DIR_REF = re.compile(r"\bSKILL_DIR/([\w.*/<>-]+)")
SKILLS_ROOT_REF = re.compile(r"\bSKILLS_ROOT/([\w.*/<>-]+)")


def test_skill_files__outside_allowlist__have_no_hardcoded_skills_path() -> None:
    # act
    offenders = [
        str(path.relative_to(REPO_ROOT))
        for path in skill_files()
        if path not in HARDCODED_PATH_ALLOWED and HARDCODED_PATH in path.read_bytes()
    ]

    # assert
    assert offenders == []


def test_skill_files__path_references__point_to_existing_files() -> None:
    # act
    missing = [
        f"{source.relative_to(REPO_ROOT)}: {reference}"
        for source, base, reference in path_references()
        if not any(base.glob(reference))
    ]

    # assert
    assert missing == []


def test_skill_files__path_references__are_found() -> None:
    # arrange
    skills_with_placeholders = {
        skill_dir_of(doc).name
        for doc in skill_docs()
        if any(placeholder in doc.read_text() for placeholder in PLACEHOLDERS)
    }

    # act
    sources = {skill_dir_of(source).name for source, _, _ in path_references()}

    # assert
    assert sources == skills_with_placeholders


def skill_files() -> list[Path]:
    return [path for skills_dir in PLUGIN_SKILL_ROOTS for path in sorted(skills_dir.rglob("*")) if path.is_file()]


def skill_docs() -> list[Path]:
    return [doc for skills_dir in PLUGIN_SKILL_ROOTS for doc in sorted(skills_dir.rglob("*.md"))]


def skill_dir_of(doc: Path) -> Path:
    skills_dir = next(root for root in PLUGIN_SKILL_ROOTS if doc.is_relative_to(root))
    return skills_dir / doc.relative_to(skills_dir).parts[0]


def path_references() -> list[tuple[Path, Path, str]]:
    references: list[tuple[Path, Path, str]] = []
    for doc in skill_docs():
        skill_dir = skill_dir_of(doc)
        text = doc.read_text()
        for pattern, base in ((SKILL_DIR_REF, skill_dir), (SKILLS_ROOT_REF, skill_dir.parent)):
            references.extend(
                (doc, base, ref)
                for ref in (match.rstrip("./") for match in pattern.findall(text))
                if "<" not in ref
            )
    return references
