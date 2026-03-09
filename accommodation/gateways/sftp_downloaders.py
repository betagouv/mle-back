import base64
import hashlib
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


class PinnedHostKeyPolicy:
    def __init__(self, paramiko_module, *, expected_sha256):
        self.paramiko_module = paramiko_module
        self.expected_sha256 = expected_sha256

    @staticmethod
    def _fingerprint_sha256(server_key):
        digest = hashlib.sha256(server_key.asbytes()).digest()
        return base64.b64encode(digest).decode("ascii").rstrip("=")

    def missing_host_key(self, client, hostname, key):
        remote_fingerprint = self._fingerprint_sha256(key)
        if remote_fingerprint != self.expected_sha256:
            raise self.paramiko_module.SSHException(
                "SFTP host key fingerprint mismatch for "
                f"{hostname}. Expected SHA256:{self.expected_sha256}, "
                f"got SHA256:{remote_fingerprint}."
            )

        client.get_host_keys().add(hostname, key.get_name(), key)


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
        known_hosts_path=None,
        host_key_sha256=None,
    ):
        self.stdout = stdout
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.private_key_path = Path(private_key_path).expanduser() if private_key_path else None
        self.known_hosts_path = Path(known_hosts_path).expanduser() if known_hosts_path else None
        self.host_key_sha256 = self._normalize_sha256_fingerprint(host_key_sha256)

    @staticmethod
    def _normalize_sha256_fingerprint(fingerprint):
        if not fingerprint:
            return None
        normalized = fingerprint.strip()
        if normalized.startswith("SHA256:"):
            normalized = normalized.split("SHA256:", 1)[1]
        return normalized.rstrip("=")

    @staticmethod
    def _fingerprint_sha256(server_key):
        digest = hashlib.sha256(server_key.asbytes()).digest()
        return base64.b64encode(digest).decode("ascii").rstrip("=")

    def _assert_expected_fingerprint(self, client, paramiko_module):
        if not self.host_key_sha256:
            return

        transport = client.get_transport()
        if not transport:
            raise RuntimeError("Unable to validate SFTP host key fingerprint: transport is not available.")

        server_key = transport.get_remote_server_key()
        remote_fingerprint = self._fingerprint_sha256(server_key)
        if remote_fingerprint != self.host_key_sha256:
            raise paramiko_module.SSHException(
                "SFTP host key fingerprint mismatch for "
                f"{self.host}:{self.port}. Expected SHA256:{self.host_key_sha256}, "
                f"got SHA256:{remote_fingerprint}."
            )

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
        if self.known_hosts_path:
            if not self.known_hosts_path.exists():
                raise FileNotFoundError(f"SFTP known_hosts file not found: {self.known_hosts_path}")
            client.load_host_keys(str(self.known_hosts_path))
        if self.host_key_sha256:
            client.set_missing_host_key_policy(
                PinnedHostKeyPolicy(paramiko_module=paramiko, expected_sha256=self.host_key_sha256)
            )
        else:
            client.set_missing_host_key_policy(paramiko.RejectPolicy())

        try:
            client.connect(**self._build_connect_kwargs())
            self._assert_expected_fingerprint(client, paramiko)
            with client.open_sftp() as sftp:
                try:
                    sftp.stat(remote_path)
                except FileNotFoundError as exc:
                    cwd = sftp.normalize(".")
                    sample_entries = []
                    try:
                        sample_entries = sorted(sftp.listdir(cwd))[:20]
                    except Exception:
                        sample_entries = []
                    entries_hint = (
                        f" Available entries in '{cwd}' (first 20): {', '.join(sample_entries)}."
                        if sample_entries
                        else ""
                    )
                    raise FileNotFoundError(
                        f"SFTP remote file not found: '{remote_path}'. Current remote directory: '{cwd}'.{entries_hint}"
                    ) from exc
                sftp.get(remote_path, str(local_path))
        except paramiko.SSHException as exc:
            if local_path.exists():
                local_path.unlink()
            raise paramiko.SSHException(
                f"{exc}. For non-standard ports, known_hosts must contain '[{self.host}]:{self.port}', "
                "or configure FAC_HABITAT_SFTP_HOST_KEY_SHA256 to pin the server key."
            ) from exc
        except FileNotFoundError:
            if local_path.exists():
                local_path.unlink()
            raise
        except Exception:
            if local_path.exists():
                local_path.unlink()
            raise
        finally:
            client.close()

        self.stdout.write(f"SFTP download from {remote_path} completed into {local_path}.")
        return local_path
