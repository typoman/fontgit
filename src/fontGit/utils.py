from typing import Dict, List, Optional, Union
from fs.base import FS
from fs.info import Info
from fs.errors import ResourceNotFound, ResourceReadOnly
import io
import ufoLib2
from threading import Lock
from fontTools.ufoLib import UFOReader
import logging
import git
import os

logger = logging.getLogger(__name__)

PATH_2_GITROOT = {}  # {path: gitRoot}
GITROOT_2_CACHED_REPO = {}  # {gitRoot: Repo}
_cache_lock = Lock()


class RepoCache:
    """
    A cache for efficiently accessing git repository contents and
    tracking changes across commits. Caches are based on the commit
    hashes.

    This class uses a singleton-like pattern to ensure that only one
    `RepoCache` instance exists per git repository root. It caches
    various git repository data such as commit hashes, file contents,
    changed files, commit objects, and tree objects to improve
    performance when accessing git history and file contents.

    The cache is thread-safe due to internal locking mechanisms.

    For example, to use the `RepoCache` to access a git repository
    and retrieve file contents:

    ```python
    from your_module import RepoCache  # Assuming RepoCache is in your_module

    # Instantiate RepoCache with a path inside the git repo
    repo_cache = RepoCache("/path/to/fil/in/git/repo/test.txt")

    # Get the latest commit hash
    latest_commit_hash = repo_cache.commits[0]

    # Get the contents of a file at the latest commit
    file_path = "/path/to/your/git/repo/your_file.txt"
    file_contents = repo_cache.get_file_contents_at_commit(
        latest_commit_hash, file_path
    )
    if file_contents:
        print(f"File contents at latest commit:\\n{file_contents.decode()}")

    # Check if a directory exists at a specific commit
    dir_path = "/path/to/your/git/repo/your_directory"
    exists = repo_cache.path_is_directory(latest_commit_hash, dir_path)
    print(f"Directory '{dir_path}' exists: {exists}")

    # List files in a directory at a specific commit
    if exists:
        files_in_dir = repo_cache.list_tree_paths(latest_commit_hash, dir_path)
        print(f"Files in '{dir_path}': {files_in_dir}")

    # Get changed files in the latest commit
    changed_files = repo_cache.get_changed_files_paths_by_commit_hash(
        latest_commit_hash
    )
    print(f"Changed files in latest commit: {changed_files}")
    ```

    Args:
        path (str): Path to a directory within the git repository. This
            can be any path within the working directory of the git
            repository. The class will automatically find the git root
            directory.

    Raises:
        Exception: If the git repository cannot be initialized at the
            given path or any parent directories.
    """

    def __new__(cls, path):
        with _cache_lock:
            root = PATH_2_GITROOT.get(path)
            if root is None:
                try:
                    repo = git.Repo(path, search_parent_directories=True)
                    root = repo.working_dir
                except Exception as e:
                    logger.error(f"Failed to initialize git repo at {path}: {e}")
                    raise

                if root not in GITROOT_2_CACHED_REPO:
                    cached_repo = super().__new__(cls)
                    cached_repo._repo = repo
                    cached_repo._root = root
                    GITROOT_2_CACHED_REPO[root] = cached_repo

                # Map the given path to the repository root
                PATH_2_GITROOT[path] = root

            return GITROOT_2_CACHED_REPO[root]

    def __init__(self, path: str):
        if hasattr(self, "_commits"):
            return
        self._commits: List[str] = []
        self._file_data: Dict[tuple, Optional[str]] = {}
        self._changed_files: Dict[Optional[str], Dict[str, List[str]]] = {}
        self._commit_cache: Dict[str, Commit] = {}
        self._latest_commit: Optional[str] = None
        self._tree_cache: Dict[str, git.Tree] = {}
        self._update_commits()

    @property
    def root(self) -> str:
        """Returns local root dir of the repo"""
        return self._root

    @property
    def commits(self) -> List[str]:
        """Returns the list of commit hashes in chronological order."""
        return self._commits

    def _update_commits(self) -> None:
        """Updates the internal commit list with any new commits."""
        try:
            latest_commit = next(self._repo.iter_commits(max_count=1)).hexsha
        except StopIteration:
            latest_commit = None

        if latest_commit != self._latest_commit:
            new_commits = []
            if self._latest_commit:
                # Get only commits since the last known commit
                for commit in self._repo.iter_commits(since=self._latest_commit):
                    new_commits.append(commit.hexsha)
                new_commits.reverse()
            else:
                # First time - get all commits
                new_commits = [
                    commit.hexsha for commit in self._repo.iter_commits(all=True)
                ]

            self._commits.extend(new_commits)
            self._latest_commit = latest_commit

    def _get_rel_path(self, abs_path: str):
        # Returns relative path to the root of the repo from the given asb path
        return os.path.relpath(abs_path, self._root)

    def get_file_contents_at_commit(
        self, commit_hash: str, file_path: str, is_abs_path=True
    ) -> Optional[bytes]:
        if is_abs_path:
            file_path = self._get_rel_path(file_path)

        key = (commit_hash, file_path)
        if key not in self._file_data:
            commit = self._repo.commit(commit_hash)
            try:
                obj = commit.tree / file_path
                if isinstance(obj, git.Blob):
                    self._file_data[key] = obj.data_stream.read()
                else:
                    self._file_data[key] = None  # It's a directory or another object
            except KeyError:
                self._file_data[key] = None
        return self._file_data[key]

    def path_is_directory(self, commit_hash: str, path: str, is_abs_path=True) -> bool:
        if is_abs_path:
            path = self._get_rel_path(path)
        tree = self.get_tree_by_commit_hash(commit_hash)
        try:
            obj = tree / path
            return isinstance(obj, git.Tree)
        except KeyError:
            return False

    def get_commit_by_hash(self, commit_hash: str) -> git.Commit:
        """Retrieves a git.Commit object by its hash, using cache if available."""
        if commit_hash not in self._commit_cache:
            self._commit_cache[commit_hash] = self._repo.commit(commit_hash)
        return self._commit_cache[commit_hash]

    def get_commit_by_index(self, index: int) -> git.Commit:
        """Retrieves a commit object by its index in the commit history."""
        self._update_commits()
        if 0 <= index < len(self.commits):
            commit_hash = self.commits[index]
            return self.get_commit_by_hash(commit_hash)
        raise IndexError(
            f"Commit index {index} out of range. There are {len(self.commits)} commits."
        )

    def get_changed_files_paths_by_commit_hash(
        self, commit_hash: Optional[str] = None
    ) -> Dict[str, List[str]]:
        """
        Returns paths for changed files categorized as added, removed, or modified.
        Paths are relative to the root of the repo.
        If commit_hash is None, returns uncommitted changes.
        """
        changes = {"added": [], "removed": [], "modified": []}

        if commit_hash is None:  # can't cache uncommitted changes.
            # Handle uncommitted changes
            diffs = self._repo.index.diff(None)
            for diff in diffs:
                if diff.new_file:
                    changes["added"].append(diff.b_path)
                elif diff.deleted_file:
                    changes["removed"].append(diff.a_path)
                else:
                    changes["modified"].append(diff.a_path)

        elif commit_hash not in self._changed_files:
            commit = self._repo.commit(commit_hash)
            parent = commit.parents[0] if commit.parents else None
            diffs = (
                parent.diff(commit, find_renames=True, find_copies=True)
                if parent
                else commit.tree.diff(git.Tree.NULL_TREE)
            )

            for diff in diffs:
                if diff.change_type == "A":
                    changes["added"].append(diff.b_path)
                elif diff.change_type == "D":
                    changes["removed"].append(diff.a_path)
                elif diff.change_type == "R":
                    changes["removed"].append(diff.a_path)
                    changes["added"].append(diff.b_path)
                else:
                    changes["modified"].append(diff.b_path or diff.a_path)

            self._changed_files[commit_hash] = changes

        return changes

    def get_tree_by_commit_hash(self, commit_hash: str) -> git.Tree:
        """Retrieves the tree object for a specific commit."""
        if commit_hash not in self._tree_cache:
            commit = self.get_commit_by_hash(commit_hash)
            self._tree_cache[commit_hash] = commit.tree
        return self._tree_cache[commit_hash]

    def list_tree_paths(
        self, commit_hash: str, path: str = "", is_abs_path=True
    ) -> List[str]:
        """Lists all items in a directory path at a specific commit."""
        if is_abs_path:
            path = self._get_rel_path(path)

        tree = self.get_tree_by_commit_hash(commit_hash)
        try:
            sub_tree = tree / path if path else tree
            return (
                [item.name for item in sub_tree]
                if isinstance(sub_tree, git.Tree)
                else []
            )
        except KeyError:
            return []

    def path_exists_in_tree(
        self, commit_hash: str, path: str, is_abs_path=True
    ) -> bool:
        """Checks if a path exists in the repository at a specific commit."""
        if is_abs_path:
            path = self._get_rel_path(path)

        tree = self.get_tree_by_commit_hash(commit_hash)
        try:
            tree / path
            return True
        except KeyError:
            return False


class GitCommitFS(FS):
    def __init__(self, path: str, commit_sha: str = None):
        super().__init__()
        self._base_path = path
        self._repo_cache = RepoCache(path)
        self._commit_sha = self._repo_cache._repo.commit(commit_sha).hexsha

    @property
    def commitsha(self):
        return self._commit_sha

    def getinfo(self, path, namespaces=None):
        namespaces = namespaces or ()
        full_path = os.path.join(self._base_path, path)
        try:
            blob_content = self._repo_cache.get_file_contents_at_commit(
                self._commit_sha, full_path, is_abs_path=True
            )
            if blob_content is not None:
                return Info(
                    {"basic": {"name": os.path.basename(path), "is_dir": False}}
                )
            else:
                if self._repo_cache.path_is_directory(
                    self._commit_sha, full_path, is_abs_path=True
                ):
                    return Info(
                        {"basic": {"name": os.path.basename(path), "is_dir": True}}
                    )
                else:
                    raise ResourceNotFound(full_path)
        except Exception as e:
            raise ResourceNotFound(full_path)

    def __str__(self):
        return f"<GitCommitFS base_path='{self._base_path}', commit_sha='{self._commit_sha}'>"

    def openbin(self, path, mode="r", **options):
        path = os.path.join(self._base_path, path)
        file_content = self._repo_cache.get_file_contents_at_commit(
            self._commit_sha, path, is_abs_path=True
        )
        if file_content is None:
            raise ResourceNotFound(path)

        return io.BytesIO(file_content)

    def opendir(
        self,  # type: _F
        path,  # type: Text
        factory=None,  # type: Optional[_OpendirFactory]
    ):
        # type: (...) -> SubFS[FS]
        from fs.subfs import (
            SubFS,
        )  # Import here to avoid circular import issues if SubFS is in the same module
        from fs import errors

        _factory = factory or SubFS  # Default factory to SubFS if none provided
        full_path = os.path.join(self._base_path, path)
        try:
            if not self.getinfo(path).is_dir:
                raise errors.DirectoryExpected(path=path)
        except errors.ResourceNotFound:
            raise errors.ResourceNotFound(path=path)
        return GitCommitFS(full_path, self._commit_sha)

    def listdir(self, path):
        path = os.path.join(self._base_path, path)
        try:
            return self._repo_cache.list_tree_paths(
                self._commit_sha, path, is_abs_path=True
            )
        except:
            raise ResourceNotFound(path)

    def makedir(self, path, permissions=None, recreate=False):
        raise ResourceReadOnly(path=path)

    def remove(self, path):
        raise ResourceReadOnly(path=path)

    def removedir(self, path):
        raise ResourceReadOnly(path=path)

    def setinfo(self, path, info):
        raise ResourceReadOnly(path=path)
