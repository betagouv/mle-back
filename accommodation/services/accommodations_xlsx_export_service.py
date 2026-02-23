from __future__ import annotations

from pathlib import Path
from typing import Iterable

try:
    from openpyxl import Workbook
except ImportError as exc:  # pragma: no cover - runtime dependency guard
    raise ImportError("openpyxl is required for accommodations XLSX export") from exc


HEADERS = [
    "Nom de la résidence",
    "Nom du propriétaire",
    "Nombre d'appartements",
    "Code postal",
    "Département",
    "Académie",
    "Disponibilité affichée",
    "Crous",
]


def department_code_from_postal_code(postal_code: str) -> str:
    cleaned = postal_code.strip()
    if len(cleaned) < 2 or not cleaned.isdigit():
        return ""
    if len(cleaned) >= 3 and cleaned.startswith(("97", "98")):
        return cleaned[:3]
    return cleaned[:2]


def build_postal_code_geo_index(
    city_rows: Iterable[tuple[list[str], str, str]],
) -> dict[str, tuple[str, str]]:
    postal_code_to_geo: dict[str, tuple[str, str]] = {}
    for postal_codes, department_name, region_name in city_rows:
        for postal_code in postal_codes:
            postal_code_to_geo.setdefault(postal_code, (department_name, region_name or ""))
    return postal_code_to_geo


def resolve_department_and_region(
    postal_code: str,
    postal_code_to_geo: dict[str, tuple[str, str]],
    departments_by_code: dict[str, tuple[str, str]],
) -> tuple[str, str]:
    if postal_code in postal_code_to_geo:
        return postal_code_to_geo[postal_code]

    department_code = department_code_from_postal_code(postal_code)
    if not department_code:
        return ("", "")

    return departments_by_code.get(department_code, ("", ""))


def build_accommodation_export_rows(
    accommodation_rows: Iterable[
        tuple[
            str,
            str | None,
            int | None,
            str | None,
            int | None,
            int | None,
            int | None,
            int | None,
            int | None,
            int | None,
            int | None,
            int | None,
            str | None,
        ]
    ],
    postal_code_to_geo: dict[str, tuple[str, str]],
    departments_by_code: dict[str, tuple[str, str]],
) -> list[list[str | int | None]]:
    rows: list[list[str | int | None]] = []
    for (
        name,
        owner_name,
        nb_total_apartments,
        postal_code,
        nb_t1_available,
        nb_t1_bis_available,
        nb_t2_available,
        nb_t3_available,
        nb_t4_available,
        nb_t5_available,
        nb_t6_available,
        nb_t7_more_available,
        source,
    ) in accommodation_rows:
        department_name, region_name = resolve_department_and_region(
            postal_code=str(postal_code or ""),
            postal_code_to_geo=postal_code_to_geo,
            departments_by_code=departments_by_code,
        )
        total_availability = compute_total_availability(
            [
                nb_t1_available,
                nb_t1_bis_available,
                nb_t2_available,
                nb_t3_available,
                nb_t4_available,
                nb_t5_available,
                nb_t6_available,
                nb_t7_more_available,
            ]
        )
        rows.append(
            [
                name,
                owner_name or "",
                nb_total_apartments,
                postal_code,
                department_name,
                region_name,
                total_availability is not None,
                "Oui" if source == "crous" else "Non",
            ]
        )
    return rows


def compute_total_availability(values: Iterable[int | None]) -> int | None:
    non_null_values = [value for value in values if value is not None]
    if not non_null_values:
        return None
    return sum(non_null_values)


def export_accommodations_to_xlsx(output_path: str | Path, rows: Iterable[list[str | int | None]]) -> int:
    destination = Path(output_path)
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Accommodations"
    worksheet.append(HEADERS)

    count = 0
    for row in rows:
        worksheet.append(row)
        count += 1

    destination.parent.mkdir(parents=True, exist_ok=True)
    workbook.save(destination)
    return count
