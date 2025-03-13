import ufoLib2
from fontTools.ufoLib import UFOReader
from fontGit.utils import GitCommitFS

class FontGit(ufoLib2.Font):

    @classmethod
    def open_at_commit(cls, path: str, commit_sha: str = None, lazy: bool = True, validate: bool = False) -> "FontGit":
        """
        Commit_sha is optional. If no commit hash is given, then the last commit will be used.
        """
        if commit_sha is not None:
            path = GitCommitFS(path, commit_sha)
        reader = UFOReader(path, validate=validate)
        font = cls.read(reader, lazy=lazy)
        font._commit_sha = commit_sha
        if not lazy:
            reader.close()
        return font

    @property
    def commitHash(self):
        return self._commit_sha

    def diff(self):
        # TODO: return a new font objc that only contains the changed parts
        pass