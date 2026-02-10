# Copyright 2018 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import logging

from .collection import Collection

try:
    from radicale.rights import (
        AuthenticatedRights, OwnerWriteRights, OwnerOnlyRights,
    )
except ImportError:
    AuthenticatedRights = OwnerOnlyRights = OwnerWriteRights = None

_LOGGER = logging.getLogger(__name__)


class Rights(OwnerOnlyRights, OwnerWriteRights, AuthenticatedRights):
    def authorized(self, user, path, perm):
        if path == '/':
            return True
        if path.endswith('/') and path != '/':
            path = path[:-1]
        components = list(filter(None, path.split('/')))
        if len(components) == 1:
            # Allow access to the principal path (e.g. /admin)
            if components[0] == user:
                return True
            # Some Radicale flows pass item hrefs relative to the collection
            # path (e.g. "10"). Resolve those under the authenticated user.
            path = f"/{user}/{components[0]}"
            components = list(filter(None, path.split('/')))

        collection = Collection(path)
        if not collection.collection:
            _LOGGER.info(
                "CardDAV Rights: denied path=%s perm=%s user=%s (no collection)",
                path,
                perm,
                user,
            )
            return False

        rights = collection.collection.sudo().rights
        cls = {
            "owner_only": OwnerOnlyRights,
            "owner_write_only": OwnerWriteRights,
            "authenticated": AuthenticatedRights,
        }.get(rights)
        if not cls:
            return False
        allowed = cls.authorized(self, user, path, perm)
        if not allowed:
            _LOGGER.info(
                "CardDAV Rights: denied path=%s perm=%s user=%s rights=%s",
                path,
                perm,
                user,
                rights,
            )
        return allowed
