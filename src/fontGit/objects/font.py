import ufoLib2
from fontTools.ufoLib import UFOReader
from fontGit.utils import GitCommitFS, RepoCache
from fontGit.errors import Error
import os


class FontGit(ufoLib2.Font):
    """
    A subclass of ufoLib2.Font that integrates with Git repositories.

    This class extends ufoLib2.Font to enable opening and working with
    UFO fonts stored in Git repositories. It allows opening fonts at
    specific commits, accessing commit history, and diffing glyph
    information between commits.
    """

    @classmethod
    def open_at_commit(
        cls,
        path: str,
        commit_sha: str = None,
        lazy: bool = True,
        validate: bool = False,
    ) -> "FontGit":
        """
        Opens a FontGit instance of a UFO font at a specific Git commit.

        This class method allows opening a UFO font that is stored in a
        Git repository. It can open the font at a specific commit using
        the `commit_sha` parameter. If no `commit_sha` is provided, it
        defaults to opening the font at the latest commit. It utilizes
        `GitCommitFS` to access the font files at the specified commit
        within the Git repository.

        Args:
            path (str): Path to the Git repository containing the UFO font.
            commit_sha (str, optional): The commit SHA to open the font at.
                Defaults to None, which means the latest commit.
            lazy (bool, optional): Whether to load the font lazily.
                Defaults to True.
            validate (bool, optional): Whether to validate the UFO font.
                Defaults to False.

        Returns:
            FontGit: A FontGit instance representing the UFO font at the
                specified commit.
        """
        if commit_sha is not None:
            reader = UFOReader(GitCommitFS(path, commit_sha), validate=validate)
        else:
            reader = UFOReader(path, validate=validate)
        font = cls.read(reader, lazy=lazy)
        font._commit_sha = commit_sha
        font._repo = RepoCache(path)
        font._path = path
        if not lazy:
            reader.close()
        return font

    @property
    def commitHash(self):
        return self._commit_sha

    @property
    def repo(self):
        return self._repo

    def _fileChanges(self):
        return self._repo.get_changed_files_paths_by_commit_hash(self._commit_sha)

    def diffGlyphNames(self, layer_name=None):
        """
        Gets the names of added, removed, and modified glyphs.

        Compares the glyph names in the current commit to the previous
        commit to identify glyphs that have been added, removed, or
        modified.

        Args:
            layer_name (str, optional): The name of the layer to check.
                If None, the default layer is used. Defaults to None.

        Returns:
            dict: A dictionary with keys "added", "removed", and "modified",
                each containing a set of glyph names corresponding to the
                changes.
        """

        glyph_names = {}
        file_changes = self._fileChanges()
        layer = self.layers.get(layer_name, self.layers.defaultLayer)
        glif_to_glyph_map = layer._glyphSet.getReverseContents()

        if file_changes["removed"]:
            prev_font = self.previousFont
            prev_layer = prev_font.layers.get(layer_name, prev_font.layers.defaultLayer)
            prev_glyph_map = prev_layer._glyphSet.getReverseContents()

        for change_type in ["added", "removed", "modified"]:
            glif_paths = file_changes.get(change_type, [])
            for glif_path in glif_paths:
                glif_file_name = os.path.basename(glif_path).lower()
                glyph_map = glif_to_glyph_map
                if change_type == "removed":
                    glyph_map = prev_glyph_map

                if glif_file_name in glyph_map:
                    glyph_name = glyph_map[glif_file_name]
                    glyph_names.setdefault(change_type, set()).add(glyph_name)

        return glyph_names

    @property
    def previousFont(self):
        """
        Returns a FontGit instance of the font at the previous commit.

        This property retrieves and returns a FontGit object representing
        the font as it was in the commit immediately preceding the
        current commit.

        Returns:
            FontGit: A FontGit instance representing the font at the
                previous commit.
        """
        if not hasattr(self, "_previousFont"):
            prev_commit_index = 0
            commits = self._repo.commits
            if self._commit_sha is not None:
                prev_commit_index = commits.index(self._commit_sha) + 1
            prev_commit_sha = commits[prev_commit_index]
            self._previousFont = FontGit.open_at_commit(self.path, prev_commit_sha)
        return self._previousFont
    
    @property
    def commits(self):
        """Returns a list of all commit hashes for the repository."""
        return self._repo.commits

    @property
    def commitsMessages(self):
        """Returns a list of all commit messages for the repository."""
        messages = []
        for commit_hash in self.commits:
            commit_object = self._repo.get_commit_by_hash(commit_hash)
            messages.append(commit_object.message)
        return messages
