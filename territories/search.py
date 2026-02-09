from django.db.models import FloatField, Func, F, Value, When, Case
from django.db.models.functions import Greatest
from django.contrib.postgres.search import (
    SearchVector,
    SearchQuery,
    SearchRank,
)

import re
import unicodedata
from django.db.models import QuerySet
from territories.models import Academy, City, Department
from unidecode import unidecode


class ImmutableUnaccent(Func):
    function = "immutable_unaccent"
    template = "%(function)s(%(expressions)s)"


def normalize_city_search(term: str) -> str:
    term = term.replace("œ", "oe").replace("æ", "ae")

    term = unicodedata.normalize("NFKD", term)
    term = "".join(c for c in term if not unicodedata.combining(c))
    term = term.lower()
    term = re.sub(r"\b(st|ste)\b", "saint", term)
    term = re.sub(r"[-_]", " ", term)
    term = re.sub(r"\s+", " ", term)
    return term.strip()


def build_city_queryset(raw_query: str) -> QuerySet:
    if not raw_query or not raw_query.strip():
        return City.objects.none()

    normalized = normalize_city_search(raw_query)
    tokens = [t for t in normalized.split() if len(t) >= 2]

    if not tokens:
        return City.objects.none()

    # --- FTS for ranking only ---
    vector = SearchVector(ImmutableUnaccent("name"), config="simple")
    query = SearchQuery(
        normalized,
        config="simple",
        search_type="plain",
    )

    qs = City.objects.annotate(
        fts_rank=SearchRank(vector, query),
        prefix_rank=Case(
            When(name__istartswith=normalized, then=Value(1.0)),
            default=Value(0.0),
            output_field=FloatField(),
        ),
        rank=Greatest(
            F("prefix_rank"),
            F("fts_rank"),
        ),
    )

    # --- Accent-insensitive AND filtering ---
    where_clauses = []
    params = []

    for token in tokens:
        where_clauses.append("immutable_unaccent(name) ILIKE %s")
        params.append(f"%{token}%")

    qs = qs.extra(
        where=where_clauses,
        params=params,
    )

    return qs.order_by("-rank", "name")


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
