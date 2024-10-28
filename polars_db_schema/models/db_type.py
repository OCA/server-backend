from odoo import fields, models


class DbType(models.Model):
    _name = "db.type"
    _description = "Constant parameters about database"

    name = fields.Char(required=True)
    code = fields.Char(required=True)
    row_count_query = fields.Text(
        required=True, help="SQL code to find how many records contains each table"
    )
    excluded_types = fields.Text(
        help="Column types to ignore for better introspection (set 1 data by line)"
    )
