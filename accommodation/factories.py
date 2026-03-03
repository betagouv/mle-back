from django.conf import settings

from accommodation.gateways.sftp_downloaders import FakeSFTPDownloader, ParamikoSFTPDownloader
from accommodation.types import SFTPDownloader


def get_sftp_downloader(*, stdout, mode, fixture_file) -> SFTPDownloader:
    if mode == "fake":
        return FakeSFTPDownloader(stdout=stdout, fixture_file=fixture_file)

    host = getattr(settings, "MLE_SFTP_HOST", None)
    username = getattr(settings, "MLE_SFTP_USERNAME", None)
    port = int(getattr(settings, "MLE_SFTP_PORT", 22))
    password = getattr(settings, "MLE_SFTP_PASSWORD", None)
    private_key_path = getattr(settings, "MLE_SFTP_PRIVATE_KEY_PATH", None)

    if not host or not username:
        raise ValueError("MLE_SFTP_HOST and MLE_SFTP_USERNAME must be configured for real SFTP downloads.")

    if not password and not private_key_path:
        raise ValueError("Configure either MLE_SFTP_PASSWORD or MLE_SFTP_PRIVATE_KEY_PATH for real SFTP downloads.")

    return ParamikoSFTPDownloader(
        stdout=stdout,
        host=host,
        port=port,
        username=username,
        password=password,
        private_key_path=private_key_path,
    )
