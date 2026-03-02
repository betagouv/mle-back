from django.urls import path

from dossier_facile.views import (
    DossierFacileCallbackView,
    DossierFacileConnectUrlView,
    DossierFacileSyncView,
    DossierFacileWebhookView,
)


urlpatterns = [
    path("connect-url/", DossierFacileConnectUrlView.as_view(), name="dossier-facile-connect-url"),
    path("callback/", DossierFacileCallbackView.as_view(), name="dossier-facile-callback"),
    path("sync/", DossierFacileSyncView.as_view(), name="dossier-facile-sync"),
    path("webhook/", DossierFacileWebhookView.as_view(), name="dossier-facile-webhook"),
]
