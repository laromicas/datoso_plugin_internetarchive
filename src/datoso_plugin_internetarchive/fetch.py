#!/bin/env python3

from datetime import datetime
import os
from concurrent.futures import ThreadPoolExecutor
import zipfile
from pathlib import Path

from datoso_plugin_internetarchive.ia import Archive, InternetArchive
from datoso.helpers import downloader
from datoso.configuration.folder_helper import Folders
from datoso.configuration import config


MAIN_URL = 'http://archive.org'

def get_archive_item(url):
    return url.split('/')[-1]

def download_dats(archive, folder_helper, preffix):
    done = 0

    def download_dat(href):
        nonlocal done
        filename = Path(href).name
        href = href.replace(" ", "%20")
        local_filename = os.path.join(folder_helper.dats, filename)
        downloader(url=href, destination=local_filename, reporthook=None)

        with zipfile.ZipFile(local_filename, 'r') as zip_ref:
            zip_ref.extractall(folder_helper.dats)
        os.remove(local_filename)
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
            executor.submit(download_dat, os.path.join(ia.get_download_path(), file['name'])) for file in dats
        ]
        for future in futures:
            future.result()

    print('\nZipping files for backup')
    backup_daily_name = f'{preffix}-{datetime.now().strftime("%Y-%m-%d")}.zip'
    with zipfile.ZipFile(os.path.join(folder_helper.backup, backup_daily_name), 'w') as zip_ref:
        for root, dirs, files in os.walk(folder_helper.dats):
            for file in files:
                zip_ref.write(os.path.join(root, file), arcname=os.path.join(root.replace(folder_helper.dats, ''), file), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)



def fetch_helper(archive: Archive, folder_helper: Folders, preffix, extras=[]):
    download_dats(archive, folder_helper, preffix)
