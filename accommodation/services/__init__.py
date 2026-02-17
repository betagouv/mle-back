from urllib.parse import urlsplit, urlunsplit

from accommodation.services.accommodations_xlsx_export_service import HEADERS as HEADERS
from accommodation.services.accommodations_xlsx_export_service import (
    build_accommodation_export_rows as build_accommodation_export_rows,
)
from accommodation.services.accommodations_xlsx_export_service import (
    build_postal_code_geo_index as build_postal_code_geo_index,
)
from accommodation.services.accommodations_xlsx_export_service import (
    compute_total_availability as compute_total_availability,
)
from accommodation.services.accommodations_xlsx_export_service import (
    department_code_from_postal_code as department_code_from_postal_code,
)
from accommodation.services.accommodations_xlsx_export_service import (
    export_accommodations_to_xlsx as export_accommodations_to_xlsx,
)
from accommodation.services.accommodations_xlsx_export_service import (
    resolve_department_and_region as resolve_department_and_region,
)

__all__ = [
    "HEADERS",
    "build_accommodation_export_rows",
    "build_postal_code_geo_index",
    "compute_total_availability",
    "department_code_from_postal_code",
    "export_accommodations_to_xlsx",
    "fix_plus_in_url",
    "resolve_department_and_region",
]


def fix_plus_in_url(url: str) -> str:
    """
    Replace raw '+' by '%2B' in URL paths only.
    Avoid touching query params or already-encoded values.
    """
    parts = urlsplit(url)
    fixed_path = parts.path.replace("+", "%2B")
    return urlunsplit(
        (
            parts.scheme,
            parts.netloc,
            fixed_path,
            parts.query,
            parts.fragment,
        )
    )
