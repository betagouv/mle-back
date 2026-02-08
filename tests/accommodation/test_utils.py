import pytest

from accommodation.utils import upload_image_to_s3


def _boto3_client_should_not_be_called(*_args, **_kwargs):
    pytest.fail("boto3.client should not be called for invalid binary_data types")


@pytest.mark.django_db
@pytest.mark.parametrize(
    "bad_value",
    [
        "not-bytes",
        123,
        12.5,
        None,
        [1, 2, 3],
        {"a": 1},
        object(),
    ],
)
def test_upload_image_to_s3_rejects_non_bytes_like(monkeypatch, bad_value):
    monkeypatch.setattr("boto3.client", _boto3_client_should_not_be_called)

    with pytest.raises(TypeError, match=r"upload_image_to_s3 expects binary data"):
        upload_image_to_s3(bad_value)
