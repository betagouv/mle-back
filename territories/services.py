import sib_api_v3_sdk
from django.conf import settings

configuration = sib_api_v3_sdk.Configuration()
configuration.api_key["api-key"] = settings.BREVO_API_KEY
api_instance = sib_api_v3_sdk.ContactsApi(sib_api_v3_sdk.ApiClient(configuration))


def sync_newsletter_subscription_to_brevo(email, territory_type, territory_name):
    contact_data = {
        "attributes": {"TERRITORY_NAME": territory_name, "TERRITORY_TYPE": territory_type},
        "listIds": [1],  # TODO create the list on Brevo and copy the ID here
        "updateEnabled": True,
    }
    try:
        api_instance.get_contact_info(email)
        api_instance.update_contact(email, contact_data)
    except sib_api_v3_sdk.rest.ApiException as e:
        if e.status == 404:
            contact_data["email"] = email
            api_instance.create_contact(contact_data)
