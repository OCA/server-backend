# Copyright 2018 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from .collection import Collection

try:
    from radicale.rights import (
        AuthenticatedRights,
        OwnerOnlyRights,
        OwnerWriteRights,
    )
except ImportError:
    AuthenticatedRights = OwnerOnlyRights = OwnerWriteRights = None


class Rights:
    def __init__(self, configuration):
        self.configuration = configuration
        self._owner_only = OwnerOnlyRights(configuration) if OwnerOnlyRights else None
        self._owner_write = (
            OwnerWriteRights(configuration) if OwnerWriteRights else None
        )
        self._authenticated = (
            AuthenticatedRights(configuration) if AuthenticatedRights else None
        )

    def authorized(self, user, path, permission):
        if path == "/" or not path:
            return True

        collection = Collection(path)
        if not collection.collection:
            return False

        rights = collection.collection.sudo().rights
        cls = {
            "owner_only": self._owner_only,
            "owner_write_only": self._owner_write,
            "authenticated": self._authenticated,
        }.get(rights)
        if not cls:
            return False
        return cls.authorized(user, path, permission)
