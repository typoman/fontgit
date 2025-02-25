from conftest import *

def test_repo_singelton():
	repo_1 = RepoCache('test_repo')
	repo_2 = RepoCache('test_repo/fonts/font_1.ufo')
	assert repo_1 is repo_2

def test_commit_list_order(sample_repo):
    git_repo = git.Repo('test_repo')
    git_commits = [commit.hexsha for commit in git_repo.iter_commits(all=True)]
    cache_commits = sample_repo.commits
    assert cache_commits == git_commits, "Commits list is not in chronological order"

