from . import roles


def user_role(request):
    user = getattr(request, "user", None)
    role = roles.get_role(user)
    return {
        "user_role": role,
        "user_role_label": role.display_title if role else "",
        "is_site_admin": roles.is_admin(user),
        "can_moderate": roles.can_moderate(user),
    }
