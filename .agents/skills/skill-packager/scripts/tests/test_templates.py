"""Tests for skill_packager.templates."""
import json

from skill_packager.templates import (
    BUILD_ZIP_PY,
    BUMP_VERSION_PY,
    CHANGELOG_STUB,
    CLAUDE_PLUGIN_JSON,
    CURSOR_PLUGIN_JSON,
    DEPLOY_PAGES_YML,
    INSTALL_HTML,
    LICENSE_MIT,
    MARKETPLACE_JSON,
    README_STUB,
    RELEASE_YML,
    VERSIONING_MD,
)


def _sample_vars():
    return {
        "skill_name": "proof-engine",
        "skill_description": "Create formal proofs",
        "plugin_name": "proof-engine",
        "marketplace_name": "proof-engine-marketplace",
        "display_name": "Proof Engine",
        "version": "1.0.0",
        "author_name": "Test Author",
        "author_email": "test@example.com",
        "github_owner": "test-owner",
        "github_repo": "proof-engine-skill",
        "license": "MIT",
        "keywords_json": '["proof", "verification"]',
        "category": "development",
        "repo_url": "https://github.com/test-owner/proof-engine-skill",
        "zip_filename": "proof-engine-skill.zip",
        "year": "2026",
        "date": "2026-04-07",
    }


# ---- JSON templates render to valid JSON with correct fields ----


class TestClaudePluginJson:
    def test_valid_json(self):
        rendered = CLAUDE_PLUGIN_JSON.format(**_sample_vars())
        data = json.loads(rendered)
        assert data["name"] == "proof-engine"
        assert data["version"] == "1.0.0"
        assert data["description"] == "Create formal proofs"
        assert data["author"]["name"] == "Test Author"
        assert data["author"]["email"] == "test@example.com"
        assert data["repository"] == "https://github.com/test-owner/proof-engine-skill"
        assert data["license"] == "MIT"
        assert data["keywords"] == ["proof", "verification"]
        assert data["skills"] == "./skills"


class TestMarketplaceJson:
    def test_valid_json(self):
        rendered = MARKETPLACE_JSON.format(**_sample_vars())
        data = json.loads(rendered)
        assert data["name"] == "proof-engine-marketplace"
        assert data["owner"]["name"] == "Test Author"
        assert data["metadata"]["version"] == "1.0.0"
        assert data["metadata"]["pluginRoot"] == "./proof-engine"
        assert data["plugins"][0]["name"] == "proof-engine"
        assert data["plugins"][0]["category"] == "development"
        assert data["plugins"][0]["tags"] == ["proof", "verification"]


class TestCursorPluginJson:
    def test_valid_json(self):
        rendered = CURSOR_PLUGIN_JSON.format(**_sample_vars())
        data = json.loads(rendered)
        assert data["name"] == "proof-engine"
        assert data["displayName"] == "Proof Engine"
        assert data["version"] == "1.0.0"
        assert data["skills"] == "./proof-engine/skills"
        assert data["keywords"] == ["proof", "verification"]


# ---- YAML workflow templates ----


class TestReleaseYml:
    def test_contains_build_zip(self):
        rendered = RELEASE_YML.format(**_sample_vars())
        assert "python3 tools/build-zip.py" in rendered

    def test_contains_gh_release_action(self):
        rendered = RELEASE_YML.format(**_sample_vars())
        assert "softprops/action-gh-release" in rendered

    def test_contains_zip_filename(self):
        rendered = RELEASE_YML.format(**_sample_vars())
        assert "proof-engine-skill.zip" in rendered

    def test_version_extraction_uses_shell_expansion(self):
        rendered = RELEASE_YML.format(**_sample_vars())
        assert "${GITHUB_REF#refs/tags/v}" in rendered

    def test_awk_uses_single_braces(self):
        rendered = RELEASE_YML.format(**_sample_vars())
        assert "{found=1; next}" in rendered
        assert "{{found=1; next}}" not in rendered


class TestDeployPagesYml:
    def test_contains_install_html(self):
        rendered = DEPLOY_PAGES_YML.format(**_sample_vars())
        assert "install-claude-desktop.html" in rendered

    def test_contains_deploy_pages_action(self):
        rendered = DEPLOY_PAGES_YML.format(**_sample_vars())
        assert "actions/deploy-pages" in rendered


# ---- HTML template ----


class TestInstallHtml:
    def test_contains_deep_link(self):
        rendered = INSTALL_HTML.format(**_sample_vars())
        assert "claude://" in rendered

    def test_contains_display_name(self):
        rendered = INSTALL_HTML.format(**_sample_vars())
        assert "Proof Engine" in rendered

    def test_contains_repo_link(self):
        rendered = INSTALL_HTML.format(**_sample_vars())
        assert "https://github.com/test-owner/proof-engine-skill" in rendered


# ---- License ----


class TestLicenseMit:
    def test_contains_author_and_year(self):
        rendered = LICENSE_MIT.format(**_sample_vars())
        assert "Test Author" in rendered
        assert "2026" in rendered

    def test_contains_mit_text(self):
        rendered = LICENSE_MIT.format(**_sample_vars())
        assert "MIT License" in rendered
        assert "WITHOUT WARRANTY" in rendered


# ---- Versioning doc ----


class TestVersioningMd:
    def test_references_bump_version_py(self):
        rendered = VERSIONING_MD.format(**_sample_vars())
        assert "bump-version.py" in rendered

    def test_references_plugin_name(self):
        rendered = VERSIONING_MD.format(**_sample_vars())
        assert "proof-engine" in rendered

    def test_references_meta_json(self):
        rendered = VERSIONING_MD.format(**_sample_vars())
        assert "meta.json" in rendered


# ---- Python script templates compile ----


class TestBumpVersionPy:
    def test_compiles(self):
        rendered = BUMP_VERSION_PY.format(**_sample_vars())
        compile(rendered, "bump-version.py", "exec")

    def test_contains_meta_json_read(self):
        rendered = BUMP_VERSION_PY.format(**_sample_vars())
        assert "meta.json" in rendered


class TestBuildZipPy:
    def test_compiles(self):
        rendered = BUILD_ZIP_PY.format(**_sample_vars())
        compile(rendered, "build-zip.py", "exec")

    def test_contains_skill_dir_stripping(self):
        rendered = BUILD_ZIP_PY.format(**_sample_vars())
        assert "CLAUDE_SKILL_DIR" in rendered


# ---- Stubs ----


class TestReadmeStub:
    def test_contains_marker(self):
        rendered = README_STUB.format(**_sample_vars())
        assert "<!-- SKILL_PACKAGER: REPLACE THIS -->" in rendered

    def test_contains_display_name(self):
        rendered = README_STUB.format(**_sample_vars())
        assert "Proof Engine" in rendered


class TestChangelogStub:
    def test_contains_marker(self):
        rendered = CHANGELOG_STUB.format(**_sample_vars())
        assert "<!-- SKILL_PACKAGER: REPLACE THIS -->" in rendered

    def test_contains_version_and_date(self):
        rendered = CHANGELOG_STUB.format(**_sample_vars())
        assert "[1.0.0] - 2026-04-07" in rendered


# ---- Catch-all: every template renders without KeyError ----


class TestAllTemplatesRender:
    def test_no_key_error(self):
        v = _sample_vars()
        templates = [
            CLAUDE_PLUGIN_JSON,
            MARKETPLACE_JSON,
            CURSOR_PLUGIN_JSON,
            RELEASE_YML,
            DEPLOY_PAGES_YML,
            INSTALL_HTML,
            LICENSE_MIT,
            VERSIONING_MD,
            BUMP_VERSION_PY,
            BUILD_ZIP_PY,
            README_STUB,
            CHANGELOG_STUB,
        ]
        for tmpl in templates:
            # Should not raise KeyError
            rendered = tmpl.format(**v)
            assert len(rendered) > 0
