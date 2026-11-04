import json
import os
import shutil
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import TypedDict

import pytest

from repo_paths import REPO_ROOT

RUNNER_SKILLS = ("ask-codex", "groom", "review-diff", "review-swarm")
RUNNER = REPO_ROOT / f"plugins/claude/skills/{RUNNER_SKILLS[0]}/scripts/run-codex.sh"
PROMPT = "the prompt"
USAGE = "usage: run-codex.sh [--preset NAME] [--model SLUG] [--effort LEVEL] '<prompt>'"
LOOKUP_FAILED = "warning: codex model lookup failed - skipping the codex model catalog\n"
JQ_MISSING = "warning: jq not found - skipping the codex model catalog\n"
ALL_LEVELS = ("low", "medium", "high", "xhigh", "max")

FAKE_CODEX = """#!/bin/bash
if [ "$1" = debug ]; then
    echo "$*" >>"$FAKE_DEBUG_LOG"
    [ "$2" = models ] && [ -n "$FAKE_CATALOG" ] || exit 1
    cat "$FAKE_CATALOG"
    exit "${FAKE_DEBUG_EXIT:-0}"
fi
printf '%s\\n' "$@"
"""


class ReasoningLevel(TypedDict):
    effort: str


class ModelEntry(TypedDict, total=False):
    slug: str
    priority: int
    visibility: str
    supported_reasoning_levels: list[ReasoningLevel]


RunCodex = Callable[..., subprocess.CompletedProcess[str]]


@pytest.mark.parametrize(
    ("args", "env", "model", "effort"),
    [
        ([], {}, "gpt-6.10-sol", "medium"),
        (["--preset", "hard"], {}, "gpt-6-astra", "xhigh"),
        ([], {"CODEX_PRESET": "hard"}, "gpt-6-astra", "xhigh"),
        (["--preset", "default"], {"CODEX_PRESET": "hard"}, "gpt-6.10-sol", "medium"),
        (["--effort", "ultra"], {}, "gpt-6.10-sol", "ultra"),
        (["--model", "gpt-6-terra", "--preset", "hard"], {}, "gpt-6-terra", "medium"),
        (["--model", "gpt-6-luna", "--preset", "hard"], {}, "gpt-6-luna", None),
        (["--model", "gpt-6-nova", "--preset", "hard"], {}, "gpt-6-nova", "medium"),
        (["--model", "gpt-x", "--preset", "hard"], {}, "gpt-x", "xhigh"),
    ],
    ids=[
        "default-preset-newest-listed-sol",
        "hard-preset-astra",
        "preset-from-env",
        "preset-flag-beats-env",
        "explicit-effort-not-checked",
        "unsupported-effort-falls-back-to-medium",
        "unsupported-effort-without-medium-left-to-codex",
        "hidden-model-effort-checked",
        "model-not-in-catalog-keeps-preset-effort",
    ],
)
def test_run_codex__catalog_available__picks_model_and_effort(
    run_codex: RunCodex, debug_log: Path, args: list[str], env: dict[str, str], model: str, effort: str | None
) -> None:
    # act
    result = run_codex(*args, **env)

    # assert
    assert (result.returncode, result.stdout.splitlines(), result.stderr, debug_log.read_text()) == (
        0,
        expected_args(model, effort),
        model_line(model, effort),
        "debug models\n",
    )


def test_run_codex__family_not_in_catalog__uses_top_priority_model(
    run_codex: RunCodex, catalog_file: Path
) -> None:
    # arrange
    write_catalog(catalog_file, [model_entry("gpt-6.1-sol", 2), model_entry("gpt-6-luna", 1)])

    # act
    result = run_codex("--preset", "hard")

    # assert
    assert (result.returncode, result.stdout.splitlines(), result.stderr) == (
        0,
        expected_args("gpt-6-luna", "xhigh"),
        model_line("gpt-6-luna", "xhigh"),
    )


def test_run_codex__explicit_model_and_effort__skips_catalog(run_codex: RunCodex, debug_log: Path) -> None:
    # act
    result = run_codex("--model", "gpt-x", "--effort", "ultra")

    # assert
    assert (result.returncode, result.stdout.splitlines(), result.stderr, debug_log.exists()) == (
        0,
        expected_args("gpt-x", "ultra"),
        model_line("gpt-x", "ultra"),
        False,
    )


def test_run_codex__codex_debug_models_fails__leaves_model_to_codex(
    run_codex: RunCodex, catalog_file: Path
) -> None:
    # arrange
    catalog_file.unlink()

    # act
    result = run_codex("--preset", "hard")

    # assert
    assert (result.returncode, result.stdout.splitlines(), result.stderr) == (
        0,
        expected_args(None, "xhigh"),
        LOOKUP_FAILED + model_line(None, "xhigh"),
    )


def test_run_codex__codex_debug_models_fails_after_printing_catalog__leaves_model_to_codex(
    run_codex: RunCodex,
) -> None:
    # act
    result = run_codex("--preset", "hard", FAKE_DEBUG_EXIT="1")

    # assert
    assert (result.returncode, result.stdout.splitlines(), result.stderr) == (
        0,
        expected_args(None, "xhigh"),
        LOOKUP_FAILED + model_line(None, "xhigh"),
    )


def test_run_codex__explicit_model_without_listed_models__checks_effort(
    run_codex: RunCodex, catalog_file: Path
) -> None:
    # arrange
    write_catalog(catalog_file, [model_entry("gpt-6-nova", 1, levels=("low", "medium"), visibility="hide")])

    # act
    result = run_codex("--model", "gpt-6-nova", "--preset", "hard")

    # assert
    assert (result.returncode, result.stdout.splitlines(), result.stderr) == (
        0,
        expected_args("gpt-6-nova", "medium"),
        model_line("gpt-6-nova", "medium"),
    )


@pytest.mark.parametrize(
    "catalog_text",
    [
        "not json",
        json.dumps([{"slug": "gpt-6.1-sol", "visibility": "list"}]),
        json.dumps({"models": [{"slug": "gpt-6.1-sol", "visibility": "hide"}]}),
        json.dumps({"models": [{"visibility": "list"}]}),
    ],
    ids=["not-json", "top-level-list", "no-listed-models", "entry-without-slug"],
)
def test_run_codex__catalog_lookup_fails__leaves_model_to_codex(
    run_codex: RunCodex, catalog_file: Path, catalog_text: str
) -> None:
    # arrange
    catalog_file.write_text(catalog_text)

    # act
    result = run_codex("--preset", "hard")

    # assert
    assert (result.returncode, result.stdout.splitlines(), result.stderr) == (
        0,
        expected_args(None, "xhigh"),
        LOOKUP_FAILED + model_line(None, "xhigh"),
    )


def test_run_codex__jq_missing__leaves_model_to_codex(run_codex: RunCodex, bin_dir: Path) -> None:
    # act
    result = run_codex("--preset", "hard", PATH=str(bin_dir))

    # assert
    assert (result.returncode, result.stdout.splitlines(), result.stderr) == (
        0,
        expected_args(None, "xhigh"),
        JQ_MISSING + model_line(None, "xhigh"),
    )


def test_run_codex__model_without_reasoning_levels__keeps_preset_effort(
    run_codex: RunCodex, catalog_file: Path
) -> None:
    # arrange
    write_catalog(catalog_file, [{"slug": "gpt-6-astra", "priority": 1, "visibility": "list"}])

    # act
    result = run_codex("--preset", "hard")

    # assert
    assert (result.returncode, result.stdout.splitlines(), result.stderr) == (
        0,
        expected_args("gpt-6-astra", "xhigh"),
        model_line("gpt-6-astra", "xhigh"),
    )


@pytest.mark.parametrize(
    ("args", "stderr"),
    [
        (["--preset", "hard"], ""),
        (["--model", "gpt-x"], "warning: CODEX_NO_OVERRIDES=1 - ignoring --model\n"),
        (["--effort", "ultra"], "warning: CODEX_NO_OVERRIDES=1 - ignoring --effort\n"),
        (
            ["--model", "gpt-x", "--effort", "ultra"],
            "warning: CODEX_NO_OVERRIDES=1 - ignoring --model and --effort\n",
        ),
    ],
    ids=["preset-only", "explicit-model-warns", "explicit-effort-warns", "explicit-model-and-effort-warns"],
)
def test_run_codex__no_overrides__drops_all_config(
    run_codex: RunCodex, debug_log: Path, args: list[str], stderr: str
) -> None:
    # act
    result = run_codex(*args, CODEX_NO_OVERRIDES="1")

    # assert
    assert (result.returncode, result.stdout.splitlines(), result.stderr, debug_log.exists()) == (
        0,
        ["exec", "--sandbox", "read-only", PROMPT],
        stderr,
        False,
    )


@pytest.mark.parametrize(
    ("args", "stderr"),
    [
        (["--preset", "turbo", PROMPT], "error: unknown codex preset 'turbo' (known: default, hard)\n"),
        (["--model"], "error: --model needs a value\n"),
        (["--efort", "high", PROMPT], "error: unknown option --efort\n"),
        ([], f"error: {USAGE}\n"),
        ([""], f"error: {USAGE}\n"),
        ([PROMPT, "extra"], f"error: {USAGE}\n"),
    ],
    ids=["unknown-preset", "no-value", "unknown-option", "no-prompt", "empty-prompt", "extra-argument"],
)
def test_run_codex__bad_arguments__fails(run_codex_raw: RunCodex, args: list[str], stderr: str) -> None:
    # act
    result = run_codex_raw(*args)

    # assert
    assert (result.returncode, result.stdout, result.stderr) == (1, "", stderr)


def test_run_codex__all_copies__are_identical() -> None:
    # arrange
    copies = sorted(REPO_ROOT.glob("plugins/*/skills/*/scripts/run-codex.sh"))

    # act
    contents = {path.relative_to(REPO_ROOT).as_posix(): path.read_text() for path in copies}

    # assert
    assert contents == dict.fromkeys(
        [f"plugins/claude/skills/{skill}/scripts/run-codex.sh" for skill in RUNNER_SKILLS],
        RUNNER.read_text(),
    )


def model_entry(slug: str, priority: int, levels: tuple[str, ...] = ALL_LEVELS, visibility: str = "list") -> ModelEntry:
    return {
        "slug": slug,
        "priority": priority,
        "visibility": visibility,
        "supported_reasoning_levels": [{"effort": level} for level in levels],
    }


def default_catalog() -> list[ModelEntry]:
    return [
        model_entry("gpt-6.1-sol", 1),
        model_entry("gpt-6-astra", 2),
        model_entry("gpt-6.10-sol", 3),
        model_entry("gpt-6.9-sol", 4),
        model_entry("gpt-6.11-sol-mini", 5),
        model_entry("gpt-7-sol", 6, visibility="hide"),
        model_entry("gpt-6-luna", 7, levels=["low", "high"]),
        model_entry("gpt-6-terra", 8, levels=["low", "medium"]),
        model_entry("gpt-6-nova", 9, levels=["low", "medium"], visibility="hide"),
        model_entry("gpt-6-sol", 10),
    ]


def write_catalog(path: Path, models: list[ModelEntry]) -> None:
    path.write_text(json.dumps({"models": models}))


def model_line(model: str | None, effort: str | None) -> str:
    return f"codex: model {model or '<codex default>'}, effort {effort or '<codex default>'}\n"


def expected_args(model: str | None, effort: str | None) -> list[str]:
    args = ["exec", "--sandbox", "read-only"]
    if model:
        args += ["-c", f"model={model}"]
    if effort:
        args += ["-c", f"model_reasoning_effort={effort}"]
    return [
        *args,
        "-c",
        "stream_idle_timeout_ms=3600000",
        "-c",
        f"project_doc={os.environ['HOME']}/.claude/CLAUDE.md",
        "-c",
        "project_doc=./CLAUDE.md",
        PROMPT,
    ]


@pytest.fixture(name="catalog_file")
def catalog_file_fixture(tmp_path: Path) -> Path:
    path = tmp_path / "catalog.json"
    write_catalog(path, default_catalog())
    return path


@pytest.fixture(name="debug_log")
def debug_log_fixture(tmp_path: Path) -> Path:
    return tmp_path / "debug.log"


@pytest.fixture(name="bin_dir")
def bin_dir_fixture(tmp_path: Path) -> Path:
    path = tmp_path / "bin"
    path.mkdir()
    fake = path / "codex"
    fake.write_text(FAKE_CODEX)
    fake.chmod(0o755)
    return path


@pytest.fixture(name="run_codex_raw")
def run_codex_raw_fixture(bin_dir: Path, catalog_file: Path, debug_log: Path) -> RunCodex:
    bash = shutil.which("bash")
    assert bash is not None
    base_env = {key: value for key, value in os.environ.items() if key not in ("CODEX_PRESET", "CODEX_NO_OVERRIDES")}

    def run(*args: str, **env: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [bash, str(RUNNER), *args],
            capture_output=True,
            text=True,
            check=False,
            env={
                **base_env,
                "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
                "CODEX_SANDBOX": "read-only",
                "FAKE_CATALOG": str(catalog_file) if catalog_file.exists() else "",
                "FAKE_DEBUG_LOG": str(debug_log),
                **env,
            },
        )

    return run


@pytest.fixture(name="run_codex")
def run_codex_fixture(run_codex_raw: RunCodex) -> RunCodex:
    def run(*args: str, **env: str) -> subprocess.CompletedProcess[str]:
        return run_codex_raw(*args, PROMPT, **env)

    return run
