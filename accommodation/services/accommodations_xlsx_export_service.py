from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from typing import Iterable, Optional

from django.db.models import F, IntegerField
from django.db.models.functions import Coalesce, Greatest

from accommodation.models import Accommodation
from territories.models import City, Department

try:
    from openpyxl import Workbook
except ImportError as exc:  # pragma: no cover
    raise ImportError("openpyxl is required for accommodations XLSX export") from exc


HEADERS: tuple[str, ...] = (
    "Nom de la résidence",
    "Nom du propriétaire",
    "Nombre d'appartements",
    "Code postal",
    "Département",
    "Académie",
    "Disponibilité affichée",
    "Type de résidence",
    "Prix minimum",
    "Prix maximum",
)


@dataclass(frozen=True)
class AccommodationExportRow:
    name: str
    owner_name: str
    nb_total_apartments: Optional[int]
    postal_code: str
    department_name: str
    academy_name: str
    has_availability: bool
    residence_type: str
    price_min: Optional[int]
    price_max: Optional[int]

    def as_xlsx_row(self) -> list[str | int | bool | None]:
        # Important: exactement 8 colonnes, dans le même ordre que HEADERS
        return [
            self.name,
            self.owner_name,
            self.nb_total_apartments,
            self.postal_code,
            self.department_name,
            self.academy_name,
            self.has_availability,
            self.residence_type,
            self.price_min,
            self.price_max,
        ]


def department_code_from_postal_code(postal_code: str) -> str:
    cleaned = (postal_code or "").strip()
    if len(cleaned) < 2 or not cleaned.isdigit():
        return ""
    # DOM/TOM: 971..989
    if len(cleaned) >= 3 and cleaned.startswith(("97", "98")):
        return cleaned[:3]
    return cleaned[:2]


def compute_total_availability(values: Iterable[Optional[int]]) -> Optional[int]:
    total = 0
    has_any = False
    for v in values:
        if v is None:
            continue
        has_any = True
        total += v
    return total if has_any else None


def build_postal_code_geo_index(
    city_rows: Iterable[tuple[list[str], str, Optional[str]]],
) -> dict[str, tuple[str, str]]:
    """
    Map postal_code -> (department_name, academy_name)
    """
    postal_code_to_geo: dict[str, tuple[str, str]] = {}
    for postal_codes, department_name, academy_name in city_rows:
        academy_name = academy_name or ""
        for postal_code in postal_codes:
            # keep first occurrence to avoid random overwrites
            postal_code_to_geo.setdefault(postal_code, (department_name, academy_name))
    return postal_code_to_geo


def build_departments_by_code_index(
    department_rows: Iterable[tuple[str, str, Optional[str]]],
) -> dict[str, tuple[str, str]]:
    """
    Map department_code -> (department_name, academy_name)
    """
    return {code: (department_name, academy_name or "") for code, department_name, academy_name in department_rows}


def resolve_department_and_academy(
    postal_code: str,
    postal_code_to_geo: dict[str, tuple[str, str]],
    departments_by_code: dict[str, tuple[str, str]],
) -> tuple[str, str]:
    if postal_code in postal_code_to_geo:
        return postal_code_to_geo[postal_code]

    code = department_code_from_postal_code(postal_code)
    if not code:
        return ("", "")
    return departments_by_code.get(code, ("", ""))


# Tuple returned by Accommodation.values_list(...) below
AccommodationRawRow = tuple[
    str,  # name
    Optional[str],  # owner__name
    Optional[int],  # nb_total_apartments
    Optional[str],  # postal_code
    Optional[int],  # nb_t1_available
    Optional[int],  # nb_t1_bis_available
    Optional[int],  # nb_t2_available
    Optional[int],  # nb_t3_available
    Optional[int],  # nb_t4_available
    Optional[int],  # nb_t5_available
    Optional[int],  # nb_t6_available
    Optional[int],  # nb_t7_more_available
    Optional[str],  # residence_type
    Optional[int],  # price_min
    Optional[int],  # price_max
]


def build_accommodation_export_rows(
    accommodation_rows: Iterable[AccommodationRawRow],
    postal_code_to_geo: dict[str, tuple[str, str]],
    departments_by_code: dict[str, tuple[str, str]],
) -> list[AccommodationExportRow]:
    out: list[AccommodationExportRow] = []

    for (
        name,
        owner_name,
        nb_total_apartments,
        postal_code,
        nb_t1_av,
        nb_t1_bis_av,
        nb_t2_av,
        nb_t3_av,
        nb_t4_av,
        nb_t5_av,
        nb_t6_av,
        nb_t7_more_av,
        residence_type,
        price_min,
        price_max,
    ) in accommodation_rows:
        postal_code_str = (postal_code or "").strip()
        department_name, academy_name = resolve_department_and_academy(
            postal_code=postal_code_str,
            postal_code_to_geo=postal_code_to_geo,
            departments_by_code=departments_by_code,
        )

        total_availability = compute_total_availability(
            [
                nb_t1_av,
                nb_t1_bis_av,
                nb_t2_av,
                nb_t3_av,
                nb_t4_av,
                nb_t5_av,
                nb_t6_av,
                nb_t7_more_av,
            ]
        )

        out.append(
            AccommodationExportRow(
                name=name,
                owner_name=(owner_name or "").strip(),
                nb_total_apartments=nb_total_apartments,
                postal_code=postal_code_str,
                department_name=department_name,
                academy_name=academy_name,
                has_availability=(total_availability is not None and total_availability > 0),
                residence_type=(residence_type or "").strip(),
                price_min=price_min,
                price_max=price_max,
            )
        )

    return out


def export_accommodations_to_xlsx(rows: Iterable[AccommodationExportRow]) -> tuple[BytesIO, int]:
    buffer = BytesIO()
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Accommodations"

    worksheet.append(list(HEADERS))  # copy to avoid accidental mutation

    count = 0
    for row in rows:
        worksheet.append(row.as_xlsx_row())
        count += 1

    workbook.save(buffer)
    buffer.seek(0)
    return buffer, count


def build_rows_for_export() -> list[AccommodationExportRow]:
    postal_code_to_geo = build_postal_code_geo_index(
        City.objects.values_list(
            "postal_codes",
            "department__name",
            "department__academy__name",
        )
    )

    departments_by_code = build_departments_by_code_index(
        Department.objects.values_list(
            "code",
            "name",
            "academy__name",
        )
    )

    # IMPORTANT:
    # - évite sources__source ici: ça duplique les lignes si plusieurs sources
    # - si tu veux le type de résidence: utilise residence_type (déjà présent)
    raw_rows: Iterable[AccommodationRawRow] = (
        Accommodation.objects.annotate(
            price_max=Greatest(
                Coalesce(F("price_max_t1"), 0),
                Coalesce(F("price_max_t1_bis"), 0),
                Coalesce(F("price_max_t2"), 0),
                Coalesce(F("price_max_t3"), 0),
                Coalesce(F("price_max_t4"), 0),
                Coalesce(F("price_max_t5"), 0),
                Coalesce(F("price_max_t6"), 0),
                Coalesce(F("price_max_t7_more"), 0),
                output_field=IntegerField(),
            )
        )
        .order_by("id")
        .values_list(
            "name",
            "owner__name",
            "nb_total_apartments",
            "postal_code",
            "nb_t1_available",
            "nb_t1_bis_available",
            "nb_t2_available",
            "nb_t3_available",
            "nb_t4_available",
            "nb_t5_available",
            "nb_t6_available",
            "nb_t7_more_available",
            "residence_type",
            "price_min",
            "price_max",
        )
    )

    return build_accommodation_export_rows(
        accommodation_rows=raw_rows,
        postal_code_to_geo=postal_code_to_geo,
        departments_by_code=departments_by_code,
    )


def export_accommodations_to_xlsx_for_admin() -> tuple[BytesIO, int]:
    rows = build_rows_for_export()
    return export_accommodations_to_xlsx(rows)
