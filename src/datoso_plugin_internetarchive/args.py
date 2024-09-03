"""Argument parser for FinalBurn Neo seed."""
from argparse import ArgumentParser, Namespace

from datoso.configuration import config


def seed_args(parser: ArgumentParser) -> ArgumentParser:
    """Add seed arguments to the parser."""
    download_parser = parser.add_mutually_exclusive_group()
    download_parser.add_argument('--use-ia', type=bool, help='Use Internet Archive downloader.', default=True)
    download_parser.add_argument('--use-internal', type=bool, help='Use default Downloader.', default=False)
    return parser

def post_parser(args: Namespace) -> None:
    """Post parser actions."""
    if getattr(args, 'use_ia', None):
        config.set('INTERNET_ARCHIVE', 'IADownloadUtility', True)  # noqa: FBT003
    elif getattr(args, 'use_internal', None):
        config.set('INTERNET_ARCHIVE', 'DownloadUtility', False)  # noqa: FBT003

def init_config() -> None:
    """Initialize the configuration."""
    default_values = {
        'IADownloadUtility': True,
    }
    if not config.has_section('INTERNET_ARCHIVE'):
        config['INTERNET_ARCHIVE'] = default_values

    for key, value in default_values.items():
        if not config.has_option('INTERNET_ARCHIVE', key):
            config.set('INTERNET_ARCHIVE', key, str(value))
