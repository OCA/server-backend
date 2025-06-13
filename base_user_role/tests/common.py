from odoo.tests import new_test_user


def role_new_test_user(env, role, **kwargs):
    role = env.ref(role)
    kwargs["groups_id"] = role.group_id.ids
    return new_test_user(env, **kwargs)
