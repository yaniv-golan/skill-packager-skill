"""Pytest fixtures that delegate to helpers.py."""
import pytest
from tests.helpers import make_sample_meta, make_source_skill


@pytest.fixture
def sample_meta(tmp_path):
    make_source_skill(tmp_path)
    return make_sample_meta(tmp_path)
