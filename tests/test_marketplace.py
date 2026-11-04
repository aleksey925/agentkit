import json
from typing import TypedDict

from repo_paths import REPO_ROOT

MARKETPLACE = REPO_ROOT / ".claude-plugin/marketplace.json"
RESERVED_PREFIX = "claude-"


class MarketplaceEntry(TypedDict):
    name: str
    source: str


class Marketplace(TypedDict):
    plugins: list[MarketplaceEntry]


class PluginManifest(TypedDict):
    name: str


def test_marketplace__entry_names__match_plugin_manifests() -> None:
    # arrange
    entries = marketplace_entries()

    # act
    manifest_names = [plugin_manifest(entry)["name"] for entry in entries]

    # assert
    assert manifest_names == [entry["name"] for entry in entries]


def test_marketplace__entry_names__avoid_reserved_prefix() -> None:
    # act
    reserved = [
        entry["name"]
        for entry in marketplace_entries()
        if entry["name"].startswith(RESERVED_PREFIX)
    ]

    # assert
    assert reserved == []


def marketplace_entries() -> list[MarketplaceEntry]:
    marketplace: Marketplace = json.loads(MARKETPLACE.read_text())
    return marketplace["plugins"]


def plugin_manifest(entry: MarketplaceEntry) -> PluginManifest:
    path = REPO_ROOT / entry["source"] / ".claude-plugin/plugin.json"
    manifest: PluginManifest = json.loads(path.read_text())
    return manifest
