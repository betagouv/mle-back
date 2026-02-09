import pytest
from territories.search import build_combined_territory_queryset, normalize_city_search
from tests.territories.factories import AcademyFactory, CityFactory, DepartmentFactory
from territories.models import Academy, Department, City


@pytest.mark.django_db
class TestCityFTSSearch:
    @pytest.fixture(scope="class")
    def territory_seed(self, django_db_setup, django_db_blocker):
        with django_db_blocker.unblock():
            try:
                academy = Academy.objects.get(name="Académie de Lyon")
                academy_vendee = Academy.objects.get(name="Académie de Vendée")
            except Academy.DoesNotExist:
                academy = AcademyFactory.create(name="Académie de Lyon")
                academy_vendee = AcademyFactory.create(name="Académie de Vendée")
            try:
                department = Department.objects.get(code=42)
                department_vendee = Department.objects.get(code=85)
            except Department.DoesNotExist:
                department = DepartmentFactory.create(name="Loire", code=42, academy=academy)
                department_vendee = DepartmentFactory.create(name="Vendée", code=85, academy=academy_vendee)
            try:
                city = City.objects.get(name="Saint-Étienne")
                city_lucon = City.objects.get(name="Luçon")
            except City.DoesNotExist:
                city = CityFactory.create(name="Saint-Étienne", department=department)
                city_lucon = CityFactory.create(name="Luçon", department=department_vendee)
            return {
                "academy": academy,
                "department": department,
                "city": city,
                "city_lucon": city_lucon,
                "department_vendee": department_vendee,
                "academy_vendee": academy_vendee,
            }

    def _assert_single_match(self, queryset, expected_name):
        assert list(queryset.values_list("name", flat=True)) == [expected_name]

    @pytest.mark.parametrize(
        "query",
        ["Saint Etienne", "Saint-Etienne", "st etienne", "St-Étienne", "saint-etiest etie"],
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

    @pytest.mark.parametrize(
        "query",
        [
            "lucon",
            "Luçon",
            "LUCON",
        ],
    )
    def test_city_search_matches_lucon(self, territory_seed, query):
        result = build_combined_territory_queryset(query)
        self._assert_single_match(result["cities"], territory_seed["city_lucon"].name)

    @pytest.mark.parametrize(
        "raw_query,expected",
        [
            ("Saint-Étienne", "saint etienne"),
            ("St Etienne", "saint etienne"),
            ("STE-ETIENNE", "saint etienne"),
            ("  Saint   Étienne  ", "saint etienne"),
            ("Évry-Courcouronnes", "evry courcouronnes"),
        ],
    )
    def test_normalize_city_search(self, raw_query, expected):
        assert normalize_city_search(raw_query) == expected
