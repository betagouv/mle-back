def is_owner(user):
    return user.groups.filter(name="Owners").exists()


def is_superuser_or_bizdev(user):
    return user.is_superuser or user.groups.filter(name="bizdev").exists()
