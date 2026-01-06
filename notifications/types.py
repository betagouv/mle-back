from typing import Protocol


class EmailGateway(Protocol):
    def send_magic_link(
        self,
        *,
        to_email: str,
        to_name: str,
        magic_link: str,
    ) -> None: ...

    def send_account_validation(
        self,
        *,
        to_email: str,
        to_name: str,
        validation_link: str,
    ) -> None: ...

    def send_reset_password(
        self,
        *,
        to_email: str,
        to_name: str,
        reset_link: str,
    ) -> None: ...
