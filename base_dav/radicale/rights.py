# Copyright 2018 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from radicale.rights import BaseRights

from odoo.http import request


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

        parts = [part for part in (path or "").strip("/").split("/") if part]

        if len(parts) == 1:
            return "RWrw" if user and user == parts[0] else ""

        if len(parts) < 2 or not parts[1].isdigit():
            return ""

        collection = request.env["dav.collection"].sudo().browse(int(parts[1]))
        if not collection.exists():
            return ""

        mode = collection.rights
        is_owner = bool(user) and user == parts[0]

        if mode == "authenticated":
            return "RWrw" if user else ""
        if mode == "owner_only":
            return "RWrw" if is_owner else ""
        if mode == "owner_write_only":
            return "RWrw" if is_owner else "Rr" if user else ""

        return ""
