import pytest

from accommodation.pricing import PricingAggregates
from tests.accommodation.factories import AccommodationFactory


@pytest.mark.django_db
def test_price_bounds_ignores_accommodations_without_prices():
    AccommodationFactory(price_min_t1=300, price_max_t1=450)
    AccommodationFactory(price_min_t2=200, price_max_t2=700)
    AccommodationFactory()  # no price fields set

    aggregates = PricingAggregates(AccommodationFactory._meta.model.objects.all())
    bounds = aggregates.price_bounds()

    assert bounds["min_price"] == 200
    assert bounds["max_price"] == 700


@pytest.mark.django_db
def test_price_bounds_uses_any_price_field_for_min_and_max():
    AccommodationFactory(price_max_t1=150)
    AccommodationFactory(price_min_t4=250)

    aggregates = PricingAggregates(AccommodationFactory._meta.model.objects.all())
    bounds = aggregates.price_bounds()

    assert bounds["min_price"] == 150
    assert bounds["max_price"] == 250


@pytest.mark.django_db
def test_price_bounds_returns_none_when_no_prices():
    AccommodationFactory()

    aggregates = PricingAggregates(AccommodationFactory._meta.model.objects.all())
    bounds = aggregates.price_bounds()

    assert bounds["min_price"] is None
    assert bounds["max_price"] is None


@pytest.mark.django_db
def test_price_bounds_returns_none_when_prices_are_zero():
    AccommodationFactory(price_min_t1=0, price_max_t1=0)
    AccommodationFactory(price_min_t2=0, price_max_t2=0)
    AccommodationFactory(price_min_t3=0, price_max_t3=0)
    AccommodationFactory(price_min_t4=0, price_max_t4=0)
    AccommodationFactory(price_min_t5=0, price_max_t5=0)
    AccommodationFactory(price_min_t6=0, price_max_t6=0)
    AccommodationFactory(price_min_t7_more=0, price_max_t7_more=0)

    aggregates = PricingAggregates(AccommodationFactory._meta.model.objects.all())
    bounds = aggregates.price_bounds()

    assert bounds["min_price"] is None
    assert bounds["max_price"] is None
