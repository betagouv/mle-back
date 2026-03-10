from django.urls import path

from dossier_facile.views import (
    ApplicationsPerOwnerListView,
    ApplyForHousingView,
    DossierFacileCallbackView,
    DossierFacileConnectUrlView,
    DossierFacileSyncView,
    DossierFacileWebhookView,
)


urlpatterns = [
    path("apply/", ApplyForHousingView.as_view(), name="dossier-facile-apply-for-housing"),
    path("applications/", ApplicationsPerOwnerListView.as_view(), name="dossier-facile-applications-per-owner"),
    path("connect-url/", DossierFacileConnectUrlView.as_view(), name="dossier-facile-connect-url"),
    path("callback/", DossierFacileCallbackView.as_view(), name="dossier-facile-callback"),
    path("sync/", DossierFacileSyncView.as_view(), name="dossier-facile-sync"),
    path("webhook/", DossierFacileWebhookView.as_view(), name="dossier-facile-webhook"),
]
