from __future__ import annotations

import csv
from collections import defaultdict
from dataclasses import dataclass
from typing import Callable


DEFAULT_PRICE_VALUES = {
    "price_min_t1": 0,
    "price_max_t1": 0,
    "price_min_t1_bis": 0,
    "price_max_t1_bis": 0,
    "price_min_t2": 0,
    "price_max_t2": 0,
    "price_min_t3": 0,
    "price_max_t3": 0,
    "price_min_t4": 0,
    "price_max_t4": 0,
    "price_min_t5": 0,
    "price_max_t5": 0,
    "price_min_t6": 0,
    "price_max_t6": 0,
    "price_min_t7_more": 0,
    "price_max_t7_more": 0,
}


@dataclass
class ImportResult:
    total_updated: int
    missing_accommodations: list[str]
    unmapped_types: list[str]


def normalize_type(raw_type: str) -> str:
    return raw_type.strip().upper().replace("É", "E").replace("È", "E")


def get_target_price_fields(normalized_type: str) -> tuple[str, str] | None:
    if "T1 BIS" in normalized_type:
        return ("price_min_t1_bis", "price_max_t1_bis")

    if any(token in normalized_type for token in ["T1", "STUDIO", "STUDETTE", "APPART", "CHAMBRE"]):
        return ("price_min_t1", "price_max_t1")
    if "T2" in normalized_type:
        return ("price_min_t2", "price_max_t2")
    if "T3" in normalized_type:
        return ("price_min_t3", "price_max_t3")
    if "T4" in normalized_type:
        return ("price_min_t4", "price_max_t4")
    if "T5" in normalized_type:
        return ("price_min_t5", "price_max_t5")
    if "T6" in normalized_type:
        return ("price_min_t6", "price_max_t6")
    if any(token in normalized_type for token in ["T7", "T8", "T9"]):
        return ("price_min_t7_more", "price_max_t7_more")
    return None


def get_data_by_residence(rows: list[dict[str, str]]) -> tuple[dict[str, dict[str, str | int]], list[str]]:
    data_by_residence: dict[str, dict[str, str | int]] = defaultdict(lambda: dict(DEFAULT_PRICE_VALUES))
    unmapped_types: list[str] = []

    for row in rows:
        residence_name = row["nom_residence"].strip()
        normalized_type = normalize_type(row["nom_lgt"])
        target_fields = get_target_price_fields(normalized_type)

        if target_fields is None:
            unmapped_types.append(normalized_type)
            continue

        min_field, max_field = target_fields
        entry = data_by_residence[residence_name]
        entry[min_field] = row["loyer_min"]
        entry[max_field] = row["loyer_max"]

    return dict(data_by_residence), unmapped_types


def read_csv_rows(csv_file_path: str) -> list[dict[str, str]]:
    with open(csv_file_path, newline="", encoding="utf-8-sig") as csv_file:
        return list(csv.DictReader(csv_file, delimiter=";"))


def import_crous_prices(
    csv_file_path: str,
    find_accommodation: Callable[[str], object | None],
    apply_prices: Callable[[object, dict[str, str | int], bool], None],
    dry_run: bool = False,
) -> ImportResult:
    rows = read_csv_rows(csv_file_path)
    data_by_residence, unmapped_types = get_data_by_residence(rows)

    total_updated = 0
    missing_accommodations: list[str] = []

    for name, prices in data_by_residence.items():
        accommodation = find_accommodation(name)
        if accommodation is None:
            missing_accommodations.append(name)
            continue

        apply_prices(accommodation, prices, dry_run)
        total_updated += 1

    return ImportResult(
        total_updated=total_updated,
        missing_accommodations=missing_accommodations,
        unmapped_types=unmapped_types,
    )
