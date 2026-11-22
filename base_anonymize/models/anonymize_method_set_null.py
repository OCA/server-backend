# Copyright 2025 Hunki Enterprises BV
# Copyright 2026 Globalist Technology SRL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

from odoo import models
from odoo.tools import SQL

# fields of ir.attachment computed from the content, not stored as columns
ATTACHMENT_CONTENT_FIELDS = ("datas", "raw")


class AnonymizeMethodSetNull(models.AbstractModel):
    _inherit = "anonymize.method"
    _name = "anonymize.method.set.null"
    _description = "Set null"

    def _run(self, field):
        if (
            field.model_name == "ir.attachment"
            and field.field_name in ATTACHMENT_CONTENT_FIELDS
        ):
            return self._clear_attachments(field)
        if not self._is_stored(field):
            records = self._get_model(field).search(field._get_domain())
            records.write({field.field_name: False})
            return len(records)
        return self._update(field, SQL("NULL"))

    def _clear_attachments(self, field):
        """Empty the selected attachments in a single UPDATE, with the values
        ir.attachment._set_attachment_data writes for empty content: through
        the ORM it is one write per attachment, minutes on large databases.
        The files are marked for the garbage collection that ends the run."""
        attachment = self._get_model(field)
        self.env.flush_all()
        self.env.cr.execute(
            SQL(
                """
                UPDATE ir_attachment
                SET db_datas = NULL, store_fname = NULL, file_size = 0,
                    checksum = %s, index_content = NULL
                FROM (
                    SELECT id, store_fname FROM ir_attachment WHERE id IN %s
                ) AS old
                WHERE ir_attachment.id = old.id
                    AND (old.store_fname IS NOT NULL
                        OR ir_attachment.db_datas IS NOT NULL)
                RETURNING old.store_fname
                """,
                attachment._compute_checksum(b""),
                self._get_query(field).subselect(),
            )
        )
        rows = self.env.cr.fetchall()
        for fname in {fname for (fname,) in rows if fname}:
            attachment._file_delete(fname)
        return len(rows)
