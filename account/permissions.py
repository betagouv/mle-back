GROUPS_PERMISSIONS = {
    "content-writer": {
        "permissions": [
            # accommodation app
            "change_accommodation",
            "view_accommodation",
            "view_owner",
            # django_summernote
            "add_attachment",
            "change_attachment",
            "delete_attachment",
            "view_attachment",
            # institution / educational institution
            "view_educationalinstitution",
            "change_educationalinstitution",
            # qa app
            "add_questionanswer",
            "change_questionanswer",
            "delete_questionanswer",
            "view_questionanswer",
            "add_questionanswerglobal",
            "change_questionanswerglobal",
            "view_questionanswerglobal",
            # territories
            "change_academy",
            "view_academy",
            "change_city",
            "view_city",
            "change_country",
            "view_country",
            "change_department",
            "view_department",
        ]
    },
    "bizdev": {
        "permissions": [
            # accommodation app
            "change_accommodation",
            "view_accommodation",
            "add_owner",
            "change_owner",
            "view_owner",
            # auth app
            "change_user",
            # django_summernote
            "add_attachment",
            "view_attachment",
            # institution / educational institution
            "view_educationalinstitution",
            # qa app
            "view_questionanswer",
            "view_questionanswerglobal",
            # territories
            "view_academy",
            "view_city",
            "view_country",
            "view_department",
        ]
    },
    "Owners": {
        "permissions": [
            # accommodation app
            "change_accommodation",
            "view_accommodation",
        ]
    },
}
