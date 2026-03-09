from django.conf import settings

from accommodation.gateways.sftp_downloaders import FakeSFTPDownloader, ParamikoSFTPDownloader
from accommodation.types import SFTPDownloader


def get_sftp_downloader(*, stdout, mode, fixture_file) -> SFTPDownloader:
    if mode == "fake":
        return FakeSFTPDownloader(stdout=stdout, fixture_file=fixture_file)

    host = getattr(settings, "FAC_HABITAT_SFTP_HOST", None)
    username = getattr(settings, "FAC_HABITAT_SFTP_USERNAME", None)
    port = int(getattr(settings, "FAC_HABITAT_SFTP_PORT", 22))
    password = getattr(settings, "FAC_HABITAT_SFTP_PASSWORD", None)
    private_key_path = getattr(settings, "FAC_HABITAT_SFTP_PRIVATE_KEY_PATH", None)
    known_hosts_path = getattr(settings, "FAC_HABITAT_SFTP_KNOWN_HOSTS_PATH", None)
    host_key_sha256 = getattr(settings, "FAC_HABITAT_SFTP_HOST_KEY_SHA256", None)

    if not host or not username:
        raise ValueError(
            "FAC_HABITAT_SFTP_HOST and FAC_HABITAT_SFTP_USERNAME must be configured for real SFTP downloads."
        )

    if not password and not private_key_path:
        raise ValueError(
            "Configure either FAC_HABITAT_SFTP_PASSWORD or FAC_HABITAT_SFTP_PRIVATE_KEY_PATH for real SFTP downloads."
        )

    return ParamikoSFTPDownloader(
        stdout=stdout,
        host=host,
        port=port,
        username=username,
        password=password,
        private_key_path=private_key_path,
        known_hosts_path=known_hosts_path,
        host_key_sha256=host_key_sha256,
    )
