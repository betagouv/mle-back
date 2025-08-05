from common.filters import BaseFilter
from institution.models import EducationalInstitution


class EducationalInstitutionFilter(BaseFilter):
    class Meta:
        model = EducationalInstitution
        fields = []
