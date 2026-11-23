"""Tests for downloading Internet Archive files with a rich progress bar."""

import time
from pathlib import Path
from types import SimpleNamespace

from rich.progress import Progress

from datoso_plugin_internetarchive.ia import InternetArchive


class FakeItem:
    """Writes the file in chunks, like internetarchive.Item.download."""

    def __init__(self, files: dict, delay: float = 0) -> None:
        self.files, self.delay, self.calls = files, delay, []

    def get_file(self, name):
        return SimpleNamespace(size=len(self.files[name]))

    def download(self, name, *, no_directory, destdir):
        self.calls.append((name, no_directory, destdir))
        data = self.files[name]
        with (Path(destdir) / name).open('wb') as fh:
            for start in range(0, len(data), 4):
                fh.write(data[start:start + 4])
                fh.flush()
                time.sleep(self.delay)


def archive(item: FakeItem) -> InternetArchive:
    ia = InternetArchive.__new__(InternetArchive)
    ia.item = item
    return ia


def test_download_without_progress(tmp_path):
    item = FakeItem({'a.zip': b'abcdef'})
    archive(item).download_file('a.zip', str(tmp_path))
    assert item.calls == [('a.zip', True, str(tmp_path))]
    assert (tmp_path / 'a.zip').read_bytes() == b'abcdef'


def test_progress_follows_the_file_on_disk(tmp_path):
    item = FakeItem({'pack.zip': b'0123456789' * 40}, delay=0.02)  # ~2 s, so the watcher polls mid-download
    seen = []
    with Progress(disable=True) as progress:
        original = progress.update
        progress.update = lambda task, **kw: (seen.append(kw.get('completed')), original(task, **kw))[1]
        archive(item).download_file('pack.zip', str(tmp_path), progress)
        [task] = progress.tasks
        assert (task.description, task.completed, task.total, task.finished) == ('pack.zip', 400, 400, True)
    assert any(0 < value < 400 for value in seen)  # partial sizes were shown while downloading


def test_finished_task_removed_when_not_kept(tmp_path):
    with Progress(disable=True) as progress:
        archive(FakeItem({'a.zip': b'12345678'})).download_file('a.zip', str(tmp_path), progress, keep=False)
        assert progress.tasks == []
    assert (tmp_path / 'a.zip').stat().st_size == 8
