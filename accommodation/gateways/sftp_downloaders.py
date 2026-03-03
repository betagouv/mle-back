import shutil
import tempfile
from pathlib import Path


class FakeSFTPDownloader:
    def __init__(self, stdout, fixture_file):
        self.stdout = stdout
        self.fixture_file = Path(fixture_file).expanduser()

    def download(self, remote_path):
        if not self.fixture_file.exists():
            raise FileNotFoundError(f"Fixture file not found: {self.fixture_file}")

        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as temp_file:
            shutil.copyfile(self.fixture_file, temp_file.name)

        self.stdout.write(f"Fake SFTP download from {remote_path} completed using local fixture {self.fixture_file}.")
        return Path(temp_file.name)


class ParamikoSFTPDownloader:
    def __init__(
        self,
        stdout,
        *,
        host,
        username,
        port=22,
        password=None,
        private_key_path=None,
    ):
        self.stdout = stdout
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.private_key_path = Path(private_key_path).expanduser() if private_key_path else None

    def _build_connect_kwargs(self):
        kwargs = {
            "hostname": self.host,
            "port": self.port,
            "username": self.username,
        }

        if self.private_key_path:
            kwargs["key_filename"] = str(self.private_key_path)
        elif self.password:
            kwargs["password"] = self.password

        return kwargs

    def download(self, remote_path):
        try:
            import paramiko
        except ImportError as exc:
            raise RuntimeError("paramiko is required to use the real SFTP downloader.") from exc

        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(remote_path).suffix or ".json") as temp_file:
            local_path = Path(temp_file.name)

        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.RejectPolicy())

        try:
            client.connect(**self._build_connect_kwargs())
            with client.open_sftp() as sftp:
                sftp.get(remote_path, str(local_path))
        finally:
            client.close()

        self.stdout.write(f"SFTP download from {remote_path} completed into {local_path}.")
        return local_path
