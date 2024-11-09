from odoo import fields, models

MODULE = __name__[12 : __name__.index(".", 13)]

HELP = """Supported files: .xlsx and .sql
Sql files may contains a comment on first line captured by File Parameters field
to be mapped automatically with related objects, i.e:\n
{'map': 'my_delivery_address', 'db_conf': mydb, 'where': ['']}

-- {'model': 'product.product', 'db_conf': mydb, 'code': 'my_delivery_address'}
"""

PARAMS = """{'model': False, 'code': False, 'db_conf': False}
# 'model/code' to guess model.map', db_conf' name to guess db.config
"""


class DfQuery(models.Model):
    _name = "df.query"
    _inherit = ["upsert.mixin"]
    _description = "Sql query"

    name = fields.Char(help=HELP)
    query = fields.Text(help="Sql query")
    params = fields.Char(
        string="File Parameters",
        default=PARAMS,
        readonly=True,
        help="Coming from sql files",
    )
    db_conf_id = fields.Many2one(
        comodel_name="db.config", required=True, help="Database Configuration"
    )
