import pytest
from territories.search import build_combined_territory_queryset
from tests.territories.factories import AcademyFactory, CityFactory, DepartmentFactory


@pytest.mark.django_db
class TestCityFTSSearch:
    @pytest.fixture(scope="class")
    def territory_seed(self, django_db_setup, django_db_blocker):
        with django_db_blocker.unblock():
            academy = AcademyFactory.create(name="Académie de Lyon")
            department = DepartmentFactory.create(name="Loire", code=42, academy=academy)
            city = CityFactory.create(name="Saint-Étienne", department=department)
            return {
                "academy": academy,
                "department": department,
                "city": city,
            }

    def _assert_single_match(self, queryset, expected_name):
        assert list(queryset.values_list("name", flat=True)) == [expected_name]

    @pytest.mark.parametrize(
        "query",
        [
            "Saint Etienne",
            "Saint-Etienne",
            "st etienne",
            "St-Étienne",
        ],
    )
    def test_city_search_matches_hyphen_space_and_abbrev(self, territory_seed, query):
        result = build_combined_territory_queryset(query)
        self._assert_single_match(result["cities"], territory_seed["city"].name)

    @pytest.mark.parametrize(
        "query",
        [
            "saint etienne",
            "SAINT ETIENNE",
            "saint étienne",
        ],
    )
    def test_city_search_is_case_and_accent_insensitive(self, territory_seed, query):
        result = build_combined_territory_queryset(query)
        self._assert_single_match(result["cities"], territory_seed["city"].name)

    @pytest.mark.parametrize(
        "query",
        [
            "Academie de Lyon",
            "académie de lyon",
            "ACADEMIE",
        ],
    )
    def test_academy_search_is_case_and_accent_insensitive(self, territory_seed, query):
        result = build_combined_territory_queryset(query)
        self._assert_single_match(result["academies"], territory_seed["academy"].name)

    @pytest.mark.parametrize(
        "query",
        [
            "loire",
            "Loire",
            "LOIRE",
        ],
    )
    def test_department_search_is_case_and_accent_insensitive(self, territory_seed, query):
        result = build_combined_territory_queryset(query)
        self._assert_single_match(result["departments"], territory_seed["department"].name)
