# Copyright (C) 2020 - Today: GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, fields, models
from odoo.exceptions import UserError


class IrActionsServer(models.Model):
    _inherit = "ir.actions.server"

    state = fields.Selection(
        selection_add=[("sort", "Sort")], ondelete={"sort": "set default"}
    )

    sort_line_ids = fields.One2many(
        comodel_name="ir.actions.server.sort.line",
        inverse_name="action_id",
        string="Sorting Criterias",
    )

    sort_field_id = fields.Many2one(
        comodel_name="ir.model.fields",
        string="Field to Sort",
        domain="[('model_id', '=', model_id), ('ttype', '=', 'one2many')]",
    )

    sort_field_id_model = fields.Char(
        string="Model of the Field to Sort", related="sort_field_id.relation"
    )

    def _run_action_sort_multi(self, eval_context=None):
        self.ensure_one()
        if len(self.sort_line_ids) == 0:
            raise UserError(
                _("The Action Server %s is not correctly set :\n" "No lines defined")
                % (self.name)
            )

        if eval_context is None:
            raise UserError(
                _(
                    "You can not run this Action Server that way.\n"
                    " Please use contextual 'Action' menu."
                )
            )

        order_list = []
        for line in self.sort_line_ids:
            order_list.append(
                line.desc and "%s desc" % line.field_id.name or line.field_id.name
            )
        order = ", ".join(order_list)

        One2manyModel = self.env[self.sort_field_id_model]
        parent_field = self.sort_field_id.relation_field

        for item in eval_context["records"]:
            # DB Query sort by the correct order
            lines = One2manyModel.search([(parent_field, "=", item.id)], order=order)

            # Write new sequence to sort lines
            sequence = 1
            for line in lines:
                line.sequence = sequence
                sequence += 1
