import pytest
from fontGit.utils import RepoCache
from fontGit import FontGit
import git
import os

os.chdir('tests')

@pytest.fixture
def sample_repo():
	r = RepoCache('test_repo')
	yield r

@pytest.fixture
def test_repo_font_1():
	f = FontGit.open_at_commit('test_repo/fonts/font_1.ufo')
	yield f
