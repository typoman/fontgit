from conftest import *

"""
469ee939e3ae29ac19046c27408009fa5946c874 (HEAD -> main)    add contours to C
19ddde762bbdb1de418355cbdabddc27b326d3c4    add test kerning group
2be04585caa365a8c779074c5fe4e91bc0ecd9d9    delete glyph E
3d1870b91b5a1ddc5a1f1f2b239525430d3aca1e    add three empty glyphs C D E
b42953aec7529942629c1d4f625cddb821aa5152    change glyph A contour
7b571c59947b42c26b0e00cf1d52fdf75fa746c7    change glyph B contour
eca88250ab5ebcba6d3f2377c418269ccc8284bc    add space glyph
ceb327135d0123a85d6d74415f7b5ed4b086e784    init
"""

def test_font_1_no_commit_hash():
	f = FontGit.open_at_commit('test_repo/fonts/font_1.ufo')
	assert f.commitHash is None, 'Font loaded directly from the file system without commit_sha should have commitHash as None.'

def test_font_1_commit_hash(sample_repo):
	commit = sample_repo.commits[-1] # init commit
	f = FontGit.open_at_commit('test_repo/fonts/font_1.ufo', commit)
	assert f.commitHash == commit

def test_font_1_commit_glyphs(sample_repo):
	commits = sample_repo.commits
	f = FontGit.open_at_commit('test_repo/fonts/font_1.ufo', commits[-1]) # init commit
	assert list(f.keys()) == ['A', 'B'], 'init commit for `font_1` has only glyphs A and B'
	f = FontGit.open_at_commit('test_repo/fonts/font_1.ufo', commits[0]) # last commit
	expected_glyphs = ['A', 'B', 'C', 'D', 'space']
	assert list(f.keys()) == expected_glyphs, f'last commit for `font_1` contains glyphs {expected_glyphs}'
	f = FontGit.open_at_commit('test_repo/fonts/font_1.ufo', commits[3]) # last commit	
	assert 'E' in f

def test_font_1_commit_glyph_contents(sample_repo):
	commits = sample_repo.commits
	f = FontGit.open_at_commit('test_repo/fonts/font_1.ufo', commits[1]) # before adding contours to `c`
	assert len(f['C']) == 0
	f = FontGit.open_at_commit('test_repo/fonts/font_1.ufo', commits[0]) # after adding contours to `c`
	assert len(f['C']) == 1

def test_font_1_commit_groups(sample_repo):
	commits = sample_repo.commits
	f = FontGit.open_at_commit('test_repo/fonts/font_1.ufo', commits[2]) # before adding groups
	assert f.groups == {}
	f = FontGit.open_at_commit('test_repo/fonts/font_1.ufo', commits[1]) # after adding groups
	assert f.groups == {'public.kern2.test': ['A', 'B']}

def test_font_1_diff_glyph_names_removed(sample_repo):
    commits = sample_repo.commits
    f = FontGit.open_at_commit('test_repo/fonts/font_1.ufo', commits[2])
    diff = f.diffGlyphNames()
    assert diff == {'removed': {'E'}}


def test_font_1_diff_glyph_names_modified(sample_repo):
    commits = sample_repo.commits
    f = FontGit.open_at_commit('test_repo/fonts/font_1.ufo', commits[0])
    diff = f.diffGlyphNames()
    assert diff == {"modified": {'C'}}

def test_font_1_diff_glyph_names_added(sample_repo):
    commits = sample_repo.commits
    f = FontGit.open_at_commit('test_repo/fonts/font_1.ufo', commits[3])
    diff = f.diffGlyphNames()
    assert diff == {"added": {'C', 'D', 'E'}}

def test_font_1_commits_messages_property():
    """
    Tests that the 'commitsMessages' property returns the correct commit messages.
    """
    f = FontGit.open_at_commit('test_repo/fonts/font_1.ufo')
    expected_messages = [
        "add contours to C\n",
        "add test kerning group\n",
        "delete glyph E\n",
        "add three empty glyphs C D E\n",
        "change glyph A contour\n",
        "change glyph B contour\n",
        "add space glyph\n",
        "init\n"
    ]
    assert f.commitsMessages == expected_messages
