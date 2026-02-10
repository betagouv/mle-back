import pytest

from accommodation.services import fix_plus_in_url


@pytest.mark.django_db
class TestFixPlusInUrl:
    @pytest.mark.parametrize(
        ("input_url", "expected"),
        [
            (
                "https://example.com/a+b/c+d",
                "https://example.com/a%2Bb/c%2Bd",
            ),
            (
                "https://example.com/search?q=a+b+c",
                "https://example.com/search?q=a+b+c",
            ),
            (
                "https://example.com/a%2Bb?x=1+2",
                "https://example.com/a%2Bb?x=1+2",
            ),
            (
                "https://example.com/a+b#frag+plus",
                "https://example.com/a%2Bb#frag+plus",
            ),
        ],
    )
    def test_fix_plus_in_url(self, input_url, expected):
        assert fix_plus_in_url(input_url) == expected
