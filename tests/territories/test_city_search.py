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
            except Academy.DoesNotExist:
                academy = AcademyFactory.create(name="Académie de Lyon")

            try:
                department = Department.objects.get(code=42)
            except Department.DoesNotExist:
                department = DepartmentFactory.create(name="Loire", code=42, academy=academy)

            try:
                city = City.objects.get(name="Saint-Étienne")
            except City.DoesNotExist:
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
        ["Saint Etienne", "Saint-Etienne", "st etienne", "St-Étienne", "saint-etie", "st etie"],
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
    def test_city_search_matches_lucon(self, query):
        try:
            academy_vendee = Academy.objects.get(name="Académie de Vendée")
        except Academy.DoesNotExist:
            academy_vendee = AcademyFactory.create(name="Académie de Vendée")
        try:
            department_vendee = Department.objects.get(code=85)
        except Department.DoesNotExist:
            department_vendee = DepartmentFactory.create(name="Vendée", code=85, academy=academy_vendee)
        try:
            city_lucon = City.objects.get(name="Luçon")
        except City.DoesNotExist:
            city_lucon = CityFactory.create(name="Luçon", department=department_vendee)
        result = build_combined_territory_queryset(query)
        self._assert_single_match(result["cities"], city_lucon.name)

    def test_city_search_filters_all_tokens(self, territory_seed):
        other_city = CityFactory.create(name="Saint-Malo", department=territory_seed["department"])
        result = build_combined_territory_queryset("saint etienne")
        self._assert_single_match(result["cities"], territory_seed["city"].name)
        assert other_city.name not in result["cities"].values_list("name", flat=True)

    def test_city_search_for_oe_does_not_match_o(self, territory_seed):
        oeuilly = CityFactory.create(name="Œuilly", department=territory_seed["department"])
        other_city = CityFactory.create(name="Orléans", department=territory_seed["department"])

        result = build_combined_territory_queryset("oeuilly")

        names = list(result["cities"].values_list("name", flat=True))

        assert names == [oeuilly.name]
        assert other_city.name not in names

    def test_city_search_whitespace_query_returns_none(self):
        result = build_combined_territory_queryset("   ")
        assert list(result["cities"]) == []

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

    def test_city_search_prefix_rank(self, territory_seed):
        try:
            City.objects.get(name="Marseille")
        except City.DoesNotExist:
            CityFactory.create(name="Marseille", department=territory_seed["department"])

        try:
            City.objects.get(name="Famars")
        except City.DoesNotExist:
            CityFactory.create(name="Famars", department=territory_seed["department"])
        result = build_combined_territory_queryset("mars")

        assert result["cities"].first().rank == 1.0
        assert result["cities"].first().name == "Marseille"
        assert result["cities"].last().rank == 0.0
        assert result["cities"].last().name == "Famars"
