#!/bin/env python3

import os
import zipfile
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

from dateutil import tz

from datoso.configuration import config
from datoso.configuration.folder_helper import Folders
from datoso.helpers import RequestUtils
from datoso.helpers.download import downloader
from datoso_plugin_internetarchive.ia import Archive, InternetArchive

MAIN_URL = 'http://archive.org'

def get_archive_item(url):
    return url.split('/')[-1]

def download_dats(archive, folder_helper, prefix):
    done = 0

    def download_dat(href):
        nonlocal done
        filename = Path(href).name
        href = href.replace(' ', '%20')
        local_filename = folder_helper.dats / filename
        downloader(url=href, destination=local_filename, reporthook=None)

        with zipfile.ZipFile(local_filename, 'r') as zip_ref:
            zip_ref.extractall(folder_helper.dats)
        Path(local_filename).unlink()
        done += 1
        print_progress(done)

    print('Fetching Archive.org DAT files')
    ia = InternetArchive(archive.item)

    print('Downloading new dats')
    dats = list(ia.files_from_folder(archive.dat_folder))
    total_dats = len(dats)

    def print_progress(done):
        print(f'  {done}/{total_dats} ({round(done/total_dats*100, 2)}%)', end='\r')

    with ThreadPoolExecutor(max_workers=int(config.get('DOWNLOAD', 'Workers', fallback=10))) as executor:
        futures = [
            executor.submit(download_dat, RequestUtils.urljoin(ia.get_download_path(), file['name'])) for file in dats
        ]
        for future in futures:
            future.result()

    print('\nZipping files for backup')
    backup_daily_name = f'{preffx}-{datetime.now(tz.tzlocal()).strftime("%Y-%m-%d")}.zip'
    with zipfile.ZipFile(folder_helper.backup / backup_daily_name, 'w') as zip_ref:
        for root, _, files in os.walk(folder_helper.dats):
            for file in files:
                zip_ref.write(Path(root) / file, arcname=Path(root).relative_to(folder_helper.dats) / file, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)

def fetch_helper(archive: Archive, folder_helper: Folders, prefix, extras=None): # noqa: ARG001
    # TODO(laromicas): Add support for extras
    download_dats(archive, folder_helper, prefix)
