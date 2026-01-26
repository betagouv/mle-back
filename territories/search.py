from django.db.models import Func
import re
import unicodedata
from django.db.models import QuerySet
from territories.models import Academy, City, Department
from django.contrib.postgres.search import SearchQuery, SearchVector
from unidecode import unidecode


class Unaccent(Func):
    function = "unaccent"
    template = "%(function)s(%(expressions)s)"


def normalize_city_search(term: str) -> str:
    term = unicodedata.normalize("NFKD", term)
    term = "".join(c for c in term if not unicodedata.combining(c))
    term = term.lower()
    term = re.sub(r"\b(st|ste)\b", "saint", term)
    term = re.sub(r"[-_]", " ", term)
    term = re.sub(r"\s+", " ", term)
    return term.strip()


def build_combined_territory_queryset(raw_query: str) -> dict[str, QuerySet]:
    academies = Academy.objects.all()
    departments = Department.objects.all()
    cities = City.objects.all()

    if raw_query:
        decoded_query = unidecode(raw_query)
        academies = Academy.objects.annotate(name_unaccent=Unaccent("name")).filter(
            name_unaccent__icontains=decoded_query
        )
        departments = Department.objects.annotate(name_unaccent=Unaccent("name")).filter(
            name_unaccent__icontains=decoded_query
        )
        normalized_query = normalize_city_search(decoded_query)
        cities = City.objects.annotate(
            search_vector=SearchVector(
                Unaccent("name"),
                config="simple",
            )
        ).filter(
            search_vector=SearchQuery(
                normalized_query,
                config="simple",
            )
        )

    return {
        "academies": academies,
        "departments": departments,
        "cities": cities,
    }
