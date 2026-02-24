from account.models import Student
from accommodation.models import Accommodation
from dossier_facile.models import DossierFacileApplication, DossierFacileTenant


def apply_for_housing(
    student: Student, accommodation: Accommodation, appartment_type: Accommodation.APARTMENT_TYPE_CHOICES
):
    # get dossier facile tenant for the student
    dossier_facile_tenant = DossierFacileTenant.objects.filter(student=student).first()
    if not dossier_facile_tenant:
        raise ValueError("Dossier facile tenant not found")

    # verify if the tenant is verified
    if dossier_facile_tenant.status != DossierFacileTenant.DossierFacileTenantStatus.VERIFIED:
        raise ValueError("Dossier facile tenant is not verified")

    # verify that the accommodation contains the appartment type
    if accommodation.get_number_of_appartment_by_type(appartment_type) == 0:
        raise ValueError("Accommodation does not contain the appartment type")

    # apply for the housing
    dossier_facile_application = DossierFacileApplication.objects.create(
        student=student,
        tenant=dossier_facile_tenant,
        appartment_type=appartment_type,
        accommodation=accommodation,
    )
    return dossier_facile_application
