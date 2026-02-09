from django.db.models import Func, Case, Value, FloatField, F, Q, When
from django.contrib.postgres.search import (
    SearchVector,
    SearchQuery,
    SearchRank,
)
from django.db.models.functions import Greatest

import re
import unicodedata
from django.db.models import QuerySet
from territories.models import Academy, City, Department
from unidecode import unidecode


class ImmutableUnaccent(Func):
    function = "immutable_unaccent"
    template = "%(function)s(%(expressions)s)"


def normalize_city_search(term: str) -> str:
    term = unicodedata.normalize("NFKD", term)
    term = "".join(c for c in term if not unicodedata.combining(c))
    term = term.lower()
    term = re.sub(r"\b(st|ste)\b", "saint", term)
    term = re.sub(r"[-_]", " ", term)
    term = re.sub(r"\s+", " ", term)
    return term.strip()


def build_city_queryset(raw_query: str) -> QuerySet:
    normalized = normalize_city_search(raw_query)

    # --- Full-Text Search ---
    vector = SearchVector(ImmutableUnaccent("name"), config="simple")
    query = SearchQuery(
        normalized,
        config="simple",
        search_type="websearch",
    )

    qs = (
        City.objects.annotate(
            # FTS rank (réel)
            fts_rank=SearchRank(vector, query),
            # icontains rank (artificiel mais contrôlé)
            icontains_rank=Case(
                When(name__istartswith=normalized, then=Value(0.3)),
                When(name__icontains=normalized, then=Value(0.15)),
                default=Value(0.0),
                output_field=FloatField(),
            ),
            # Rank final
            rank=Greatest(
                F("fts_rank"),
                F("icontains_rank"),
            ),
        )
        .filter(Q(fts_rank__gt=0) | Q(name__icontains=normalized))
        .order_by("-rank", "name")
    )

    return qs


def build_combined_territory_queryset(raw_query: str) -> dict[str, QuerySet]:
    academies = Academy.objects.all()
    departments = Department.objects.all()
    cities = City.objects.all()

    if raw_query:
        decoded_query = unidecode(raw_query)
        academies = Academy.objects.annotate(name_unaccent=ImmutableUnaccent("name")).filter(
            name_unaccent__icontains=decoded_query
        )
        departments = Department.objects.annotate(name_unaccent=ImmutableUnaccent("name")).filter(
            name_unaccent__icontains=decoded_query
        )
        cities = build_city_queryset(raw_query)

    return {
        "academies": academies,
        "departments": departments,
        "cities": cities,
    }
