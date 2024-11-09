from odoo import fields, models


class FieldMap(models.Model):
    _name = "field.map"
    _description = "Field mapping"
    _order = "field_id ASC"
    _rec_name = "field_id"
    _rec_names_search = ["field_id"]

    model_map_id = fields.Many2one(
        comodel_name="model.map", required=True, ondelete="cascade"
    )
    sequence = fields.Integer()
    field_id = fields.Many2one(
        comodel_name="ir.model.fields",
        ondelete="cascade",
        required=True,
        domain="[('model_id', '=', model_id)]",
    )
    model_id = fields.Many2one(
        comodel_name="ir.model",
        related="model_map_id.model_id",
        readonly=True,
    )
    name = fields.Char(help="Name field in the source file (spreadsheet)")
    renamed = fields.Char(help="If specified, renamed in model_map")
    required = fields.Boolean(
        help="Prevent to import missing data if field is missing in some records",
    )
    check_type = fields.Boolean(
        help="Check data type is compatible",
    )
