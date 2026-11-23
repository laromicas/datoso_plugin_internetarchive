"""Internet Archive Repository."""
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from threading import Event, Thread

from internetarchive import Item, get_item
from rich.progress import Progress


@dataclass
class Archive:
    """Internet Archive Repository."""

    dat_folder: str = None
    item: str = None

class InternetArchive:
    """Internet Archive Wrapper."""

    dirs: set | None = None
    path: str = None
    allowed_extensions: list[str] = None
    excluded_patterns: list[str] = None
    latest_only: bool = False

    def __init__(self, url: str) -> None:
        """Initialize the InternetArchive object."""
        self.url = url
        self.get_item()

    def get_item(self) -> Item:
        """Get the item from InternetArchive."""
        self.item = get_item(self.url)
        return self.item

    def get_download_path(self) -> str:
        """Return the download path for files in InternetArchive item."""
        # self.path f"https://{self.item.item_metadata['d1']}{self.item.item_metadata['dir']}/"
        self.path = f'https://archive.org/download/{self.item.identifier}/'
        return self.path

    def download_file(
        self, file: str, destdir: str, progress: Progress | None = None, *, keep: bool = True,
    ) -> None:
        """Download a file of the item into destdir, showing it in ``progress`` if given."""
        if progress is None:
            self.item.download(file, no_directory=True, destdir=destdir)
            return
        target = Path(destdir) / file
        size = self.item.get_file(file).size or None
        task = progress.add_task(Path(file).name, total=size, file=True)
        done = Event()

        def watch() -> None:
            while not done.wait(0.5):
                progress.update(task, completed=target.stat().st_size if target.exists() else 0)

        watcher = Thread(target=watch, daemon=True)
        watcher.start()
        try:
            self.item.download(file, no_directory=True, destdir=destdir)
        finally:
            done.set()
            watcher.join()
        progress.update(task, completed=target.stat().st_size if target.exists() else 0)
        if not keep:
            progress.remove_task(task)

    @staticmethod
    def _matches_folder(file_name: str, folder: str) -> bool:
        """Return whether a file belongs to the requested folder."""
        return file_name.startswith(f'{folder}/') or (folder in ('', '/') and '/' not in file_name)

    @staticmethod
    def _file_sort_key(file: dict) -> tuple[float, str]:
        """Return a stable key that prefers the newest file metadata available."""
        for metadata_key in ('mtime', 'updatedate', 'created', 'addeddate', 'publicdate'):
            value = file.get(metadata_key)
            if value is None:
                continue
            if isinstance(value, int | float):
                return float(value), file['name']
            if isinstance(value, str):
                normalized_value = value.strip()
                if not normalized_value:
                    continue
                try:
                    return float(normalized_value), file['name']
                except ValueError:
                    try:
                        return datetime.fromisoformat(normalized_value).timestamp(), file['name']
                    except ValueError:
                        continue
        return 0.0, file['name']

    def files_from_folder(self, folder: str) -> Iterator[str]:
        """Return a list of files in a folder."""
        filtered_files = []
        for file in self.item.item_metadata['files']:
            if not self._matches_folder(file['name'], folder):
                continue
            if self.allowed_extensions and not any(file['name'].endswith(ext) for ext in self.allowed_extensions):
                continue
            if self.excluded_patterns and any(pattern in file['name'] for pattern in self.excluded_patterns):
                continue
            filtered_files.append(file)

        if self.latest_only and filtered_files:
            yield max(filtered_files, key=self._file_sort_key)
            return

        yield from filtered_files

    def folders(self) -> list:
        """Return a list of folders in InternetArchive item."""
        files = self.item.item_metadata['files']
        if self.dirs is None:
            self.dirs = set()
        for file in files:
            self.dirs.add(Path(file['name']).parent)
        return list(self.dirs)
