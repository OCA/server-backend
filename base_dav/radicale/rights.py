# Copyright 2018 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from radicale.rights import BaseRights

from odoo.http import request


def load(configuration):
    """Create Radicale rights backend instance.

    This function is used by Radicale to initialize
    the rights/authorization plugin.

    :param configuration: Radicale configuration object
    :type configuration: Any

    :return: Rights backend instance
    :rtype: Rights
    """
    return Rights(configuration)


def _split(path):
    """Split DAV path into clean components.

    Removes leading/trailing slashes and empty segments.

    :param path: Raw DAV path, defaults to None
    :type path: str | None

    :return: List of path components
    :rtype: List[str]
    """
    return [p for p in (path or "").strip("/").split("/") if p]


class Rights(BaseRights):
    def authorization(self, user, path):
        """Determine access rights for DAV resource.

        Authorization logic:
          - Root path: full access
          - Principal path: requires authentication
          - Collection path: depends on collection.rights
            (authenticated / owner_only / owner_write_only)

        :param user: Authenticated username or None
        :type user: str | None
        :param path: Requested DAV path
        :type path: str | None

        :return: Access mode string.
          - "R" means read access.
          - "W" means write access.
          - Uppercase letters apply to collections.
          - Lowercase letters apply to items.
          - Empty string means no access.
        :rtype: str
        """
        if not path or path == "/":
            return "RWrw" if user else ""

        parts = _split(path)

        if len(parts) == 1:
            return "RWrw" if user else ""

        if len(parts) >= 2 and (parts[1] or "").isdigit():
            collection = request.env["dav.collection"].sudo().browse(int(parts[1]))
            if not collection.exists():
                return ""

            mode = collection.rights
            is_owner = bool(user) and (user == parts[0])

            if mode == "authenticated":
                return "RWrw" if user else ""
            if mode == "owner_only":
                return "RWrw" if is_owner else ""
            if mode == "owner_write_only":
                if is_owner:
                    return "RWrw"
                return "Rr" if user else ""

        return ""
