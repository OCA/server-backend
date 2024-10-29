from odoo import fields, models


class ModelMap(models.Model):
    _name = "model.map"
    _inherit = "mail.thread"
    _description = "File Configuration"
    _rec_name = "code"
    _rec_names_search = ["model_id", "code"]

    model_id = fields.Many2one(
        comodel_name="ir.model",
        required=True,
        copy=False,
        ondelete="cascade",
        tracking=True,
    )
    code = fields.Char(help="Allow to browse between several identical models")
    rename = fields.Boolean(help="Rename Dataframe fields")
    action = fields.Selection(
        selection=[
            ("display", "Display"),
            ("import", "Import data"),
        ],
        default="display",
        tracking=True,
        help="Some other behaviors can be implemented",
    )
    on_fail = fields.Selection(
        selection=[("stop", "Stop"), ("skip", "Skip record (TODO)")],
        default="stop",
        tracking=True,
        help="What should be the behavior in case of failure regarding constraint "
        "fields (required, format, etc)\n\n"
        " - Stop: stop the process by raising an exception\n"
        " - Skip record: current line'll be ignored from the next process",
    )
    field_ids = fields.One2many(
        comodel_name="df.field", inverse_name="model_map_id", copy=True
    )
