from django.urls import path

from institution.views import EducationalInstitutionListView

urlpatterns = [
    path("educational-institutions/", EducationalInstitutionListView.as_view(), name="institution-list"),
]
