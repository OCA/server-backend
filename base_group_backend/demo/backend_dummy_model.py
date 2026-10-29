from odoo import fields, models


class BackendDummyModel(models.Model):
    _name = "backend.dummy.model"
    _description = "Backend Dummy Model demo"

    my_value = fields.Char(name="Value", required=True)
    my_other_value = fields.Char(name="Other value", required=True)
    date_start = fields.Datetime(
        name="Date start", required=True, default=fields.Datetime.now
    )
    date_stop = fields.Datetime(
        name="Date stop", required=True, default=fields.Datetime.now
    )
