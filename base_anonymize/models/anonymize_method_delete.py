# Copyright 2026 Globalist Technology SRL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

from odoo import models
from odoo.tools import SQL


class AnonymizeMethodDelete(models.AbstractModel):
    _inherit = "anonymize.method"
    _name = "anonymize.method.delete"
    _description = "Delete records"

    def _run(self, field):
        """Delete the selected records in SQL, the field is ignored: for queues
        like mail.mail that hold copies of personal data and nothing else."""
        model = self._get_model(field)
        table = SQL.identifier(model._table)
        self.env.flush_all()
        self.env.cr.execute(
            SQL(
                "DELETE FROM %s WHERE %s.id IN %s",
                table,
                table,
                self._get_query(field).subselect(),
            )
        )
        return self.env.cr.rowcount
