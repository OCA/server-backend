# © 2015 Therp BV <http://therp.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo.tools import pycompat


class BaseSuspendSecurityUid(int):
    def __eq__(self, other):
        if isinstance(other, pycompat.integer_types):
            return False
        return super(BaseSuspendSecurityUid, self).__int__() == other

    def __hash__(self):
        return super(BaseSuspendSecurityUid, self).__hash__()

    def __iter__(self):
        yield super(BaseSuspendSecurityUid, self).__int__()
