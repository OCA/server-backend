# Copyright 2018 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
try:
    from radicale.rights import OwnerOnlyRights
except ImportError:
    OwnerOnlyRights = None


class Rights(OwnerOnlyRights):
    def authorized(self, user, path, permission):
        if path == '/':
            return True
        return super(Rights, self).authorized(user, path, permission)
