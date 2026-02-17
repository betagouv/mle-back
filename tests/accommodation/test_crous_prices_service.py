import pytest

from accommodation.crous_prices_service import get_data_by_residence
from accommodation.crous_prices_service import get_target_price_fields
from accommodation.crous_prices_service import import_crous_prices
from accommodation.crous_prices_service import normalize_type


@pytest.fixture(autouse=True)
def create_owners_group():
    # Override global DB fixture from conftest for pure unit tests in this module.
    return None


def test_normalize_type_removes_accents_and_uppercases():
    assert normalize_type("t1 bìs") == "T1 BÌS"
    assert normalize_type(" t1 bis ") == "T1 BIS"
    assert normalize_type("t2 étudiAnt") == "T2 ETUDIANT"


@pytest.mark.parametrize(
    ("housing_type", "expected_fields"),
    [
        ("t1 bis", ("price_min_t1_bis", "price_max_t1_bis")),
        ("studio", ("price_min_t1", "price_max_t1")),
        ("t2", ("price_min_t2", "price_max_t2")),
        ("T3", ("price_min_t3", "price_max_t3")),
        ("t4", ("price_min_t4", "price_max_t4")),
        ("T5", ("price_min_t5", "price_max_t5")),
        ("t6", ("price_min_t6", "price_max_t6")),
        ("t8", ("price_min_t7_more", "price_max_t7_more")),
        ("loft", None),
    ],
)
def test_get_target_price_fields(housing_type, expected_fields):
    assert get_target_price_fields(normalize_type(housing_type)) == expected_fields


def test_get_data_by_residence_groups_and_applies_defaults():
    rows = [
        {"Residence": "Residence A", "nom_lgt": "Studio", "loyer_min": "100", "loyer_max": "200"},
        {"Residence": "Residence A", "nom_lgt": "T2", "loyer_min": "300", "loyer_max": "400"},
        {"Residence": "Residence B", "nom_lgt": "T9", "loyer_min": "500", "loyer_max": "700"},
        {"Residence": "Residence B", "nom_lgt": "Loft", "loyer_min": "800", "loyer_max": "1000"},
    ]

    data_by_residence, unmapped_types = get_data_by_residence(rows)

    assert data_by_residence["Residence A"]["price_min_t1"] == "100"
    assert data_by_residence["Residence A"]["price_max_t1"] == "200"
    assert data_by_residence["Residence A"]["price_min_t2"] == "300"
    assert data_by_residence["Residence A"]["price_max_t2"] == "400"
    assert data_by_residence["Residence A"]["price_min_t3"] == 0

    assert data_by_residence["Residence B"]["price_min_t7_more"] == "500"
    assert data_by_residence["Residence B"]["price_max_t7_more"] == "700"

    assert unmapped_types == ["LOFT"]


def test_import_crous_prices_calls_find_and_apply(tmp_path):
    csv_file = tmp_path / "crous_prices.csv"
    csv_file.write_text(
        "Residence,nom_lgt,loyer_min,loyer_max\n"
        "Residence A,T1,100,200\n"
        "Residence B,T2,300,400\n"
        "Residence C,Loft,500,600\n",
        encoding="utf-8",
    )

    found = {"Residence A": object()}
    applied_calls = []

    def find_accommodation(name):
        return found.get(name)

    def apply_prices(accommodation, prices, dry_run):
        applied_calls.append((accommodation, prices, dry_run))

    result = import_crous_prices(
        csv_file_path=str(csv_file),
        find_accommodation=find_accommodation,
        apply_prices=apply_prices,
        dry_run=True,
    )

    assert result.total_updated == 1
    assert result.missing_accommodations == ["Residence B"]
    assert result.unmapped_types == ["LOFT"]

    assert len(applied_calls) == 1
    assert applied_calls[0][0] is found["Residence A"]
    assert applied_calls[0][1]["price_min_t1"] == "100"
    assert applied_calls[0][1]["price_max_t1"] == "200"
    assert applied_calls[0][2] is True
