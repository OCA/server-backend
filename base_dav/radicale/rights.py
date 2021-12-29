# Copyright 2018 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from .collection import Collection

try:
    from radicale.rights.owner_only import Rights as OwnerOnlyRights
    from radicale.rights.authenticated import Rights as AuthenticatedRights
    from radicale.rights.owner_write import Rights as OwnerWriteRights
except ImportError:
    AuthenticatedRights = OwnerOnlyRights = OwnerWriteRights = None


class Rights(OwnerOnlyRights, OwnerWriteRights, AuthenticatedRights):
    def authorization(self, user, path):
        if path == '/':
            return True

        collection = Collection(path)
        if not collection.collection:
            return ""

        rights = collection.collection.sudo().rights
        cls = {
            "owner_only": OwnerOnlyRights,
            "owner_write_only": OwnerWriteRights,
            "authenticated": AuthenticatedRights,
        }.get(rights)
        if not cls:
            return False
        return cls.authorization(self, user, path)
