from django.urls import path

from dossier_facile.views import DossierFacileCallbackView, DossierFacileConnectUrlView, DossierFacileWebhookView


urlpatterns = [
    path("connect-url/", DossierFacileConnectUrlView.as_view(), name="dossier-facile-connect-url"),
    path("callback/", DossierFacileCallbackView.as_view(), name="dossier-facile-callback"),
    path("webhook/", DossierFacileWebhookView.as_view(), name="dossier-facile-webhook"),
]
