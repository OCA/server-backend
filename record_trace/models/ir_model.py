from odoo import fields, models

class IrModel(models.Model):
    _inherit = "ir.model"

    track_deletions = fields.Boolean(
        string="Trace Deletions",
        help="If enabled, deletions of records of this model are logged.",
    )
