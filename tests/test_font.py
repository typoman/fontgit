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

def test_font_1_no_commit_hash(sample_repo):
	f = FontGit.open_at_commit('test_repo/fonts/font_1.ufo')
	assert f.commitHash == sample_repo.commits[0], 'if commit_sha is not given, last commit should be used.'

def test_font_1_commit_hash(sample_repo, test_repo_font_1):
	commit = sample_repo.commits[-1] # init commit
	f = FontGit.open_at_commit('test_repo/fonts/font_1.ufo', commit)
	assert f.commitHash == commit

def test_font_1_commit_glyphs(sample_repo, test_repo_font_1):
	commits = sample_repo.commits
	f = FontGit.open_at_commit('test_repo/fonts/font_1.ufo', commits[-1]) # init commit
	assert list(f.keys()) == ['A', 'B'], 'init commit for `font_1` has only glyphs A and B'
	f = FontGit.open_at_commit('test_repo/fonts/font_1.ufo', commits[0]) # last commit
	expected_glyphs = ['A', 'B', 'C', 'D', 'space']
	assert list(f.keys()) == expected_glyphs, f'last commit for `font_1` contains glyphs {expected_glyphs}'
	f = FontGit.open_at_commit('test_repo/fonts/font_1.ufo', commits[3]) # last commit	
	assert 'E' in f

def test_font_1_commit_glyph_contents(sample_repo, test_repo_font_1):
	commits = sample_repo.commits
	f = FontGit.open_at_commit('test_repo/fonts/font_1.ufo', commits[1]) # before adding contours to `c`
	assert len(f['C']) == 0
	f = FontGit.open_at_commit('test_repo/fonts/font_1.ufo', commits[0]) # after adding contours to `c`
	assert len(f['C']) == 1

def test_font_1_commit_groups(sample_repo, test_repo_font_1):
	commits = sample_repo.commits
	f = FontGit.open_at_commit('test_repo/fonts/font_1.ufo', commits[2]) # before adding groups
	assert f.groups == {}
	f = FontGit.open_at_commit('test_repo/fonts/font_1.ufo', commits[1]) # after adding groups
	assert f.groups == {'public.kern2.test': ['A', 'B']}
