# FontGit
FontGit is an experimental package that loads fonts from a specific commit in a git repo. You don't have to check out any commits, or reset the repo to a specific commit, fontgit loads everything lazily. This means only the requested parts of the fonts is loaded which makes the reading faster.

## Example

```python
from fontGit import FontGit

font_path = 'tests/test_repo/fonts/font_1.ufo' # font should be inside a repo with a commit history

# Open a font at latest commit
font = FontGit.open_at_commit(font_path)

# get list of all commit hashes in the repo
from fontGit.utils import RepoCache
sample_repo = RepoCache(font_path) # it will resolve to the repo root even if font path is given
commits = sample_repo.commits

# get a font at a spcific commit
font = FontGit.open_at_commit(font_path, commit_sha=commits[1])
```