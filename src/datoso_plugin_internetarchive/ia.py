"""Internet Archive Repository."""
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from internetarchive import Item, get_item


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

    def download_file(self, file: str, destdir: str) -> str:
        """Return the download path for a file in InternetArchive item."""
        return self.item.download(file, no_directory=True, destdir=destdir)

    def files_from_folder(self, folder: str) -> Iterator[str]:
        """Return a list of files in a folder."""
        files = self.item.item_metadata['files']
        for file in files:
            if file['name'].startswith(f'{folder}/') or (folder in ('','/') and '/' not in file['name']):
                if self.allowed_extensions and not any(file['name'].endswith(ext) for ext in self.allowed_extensions):
                    continue
                yield file

    def folders(self) -> list:
        """Return a list of folders in InternetArchive item."""
        files = self.item.item_metadata['files']
        if self.dirs is None:
            self.dirs = set()
        for file in files:
            self.dirs.add(Path(file['name']).parent)
        return list(self.dirs)
