from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("summernote/", include("django_summernote.urls")),
    path("api/questions-answers/", include("qa.urls")),
    path("api/territories/", include("territories.urls")),
    path("api/institutions/", include("institution.urls")),
    path("api/accommodations/", include("accommodation.urls")),
    path("api/accounts/", include("account.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/schema/swagger-ui/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/schema/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    path("two_factor/", include(("admin_two_factor.urls", "admin_two_factor"), namespace="two_factor")),
]
