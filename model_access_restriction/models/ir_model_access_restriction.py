# Copyright 2025 Alberto Martínez <alberto.martinez@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, exceptions, fields, models
from odoo.exceptions import AccessError


class IrModelAccessRestriction(models.Model):
    _name = "ir.model.access.restriction"
    _description = "Model Access Restrictions. Not having one will disable access."

    _order = "model_id,name,id"

    name = fields.Char(index=True, required=True)
    active = fields.Boolean(
        default=True,
    )
    model_id = fields.Many2one(
        string="Model",
        comodel_name="ir.model",
        index=True,
        required=True,
        ondelete="cascade",
        domain=lambda self: [
            (
                "id",
                "!=",
                self.env.ref(
                    "model_access_restriction.model_ir_model_access_restriction"
                ).id,
            )
        ],
    )
    groups = fields.Many2many(
        string="Allowed Groups",
        comodel_name="res.groups",
        relation="model_access_restriction_group_rel",
        column1="model_access_restriction_id",
        column2="group_id",
        ondelete="restrict",
    )
    perm_read = fields.Boolean(string="Apply for Read")
    perm_write = fields.Boolean(string="Apply for Write", default=True)
    perm_create = fields.Boolean(string="Apply for Create", default=True)
    perm_unlink = fields.Boolean(string="Apply for Delete", default=True)

    def init(self):
        self.env.cr.execute(
            """
            CREATE INDEX IF NOT EXISTS ir_model_access_restriction_model_name_id_idx
            ON ir_model_access_restriction(model_id,name,id)
        """
        )

    def _raise_access_exception(self, model, operation, failed_restrictions):
        restriction_names = ", ".join(failed_restrictions.mapped("name"))
        operation_txt = {
            "read": _("access"),
            "write": _("modify"),
            "create": _("create"),
            "unlink": _("delete"),
        }[operation]
        msg = _(
            "You are not allowed to {operation} {model} "
            "due to the following model access restriction(s): {restrictions}",
        ).format(operation=operation_txt, model=model, restrictions=restriction_names)
        raise AccessError(msg)

    def _get_model_restrictions(self, model, operation):
        self._cr.execute(
            """ SELECT r.id
                FROM ir_model_access_restriction r JOIN ir_model m ON (r.model_id=m.id)
                WHERE m.model=%s AND r.active AND r.perm_{operation}
                ORDER BY r.id
            """.format(
                operation=operation
            ),
            (model,),
        )
        return self.browse(row[0] for row in self._cr.fetchall()).exists()

    def _get_passed_restrictions(self, model, operation):
        self._cr.execute(
            """ SELECT r.id
                FROM ir_model_access_restriction r
                    JOIN ir_model m ON (r.model_id=m.id)
                WHERE m.model=%s AND r.active AND r.perm_{operation}
                AND (r.id IN (
                    SELECT model_access_restriction_id
                    FROM model_access_restriction_group_rel rg
                    JOIN res_groups_users_rel gu ON (rg.group_id=gu.gid)
                    WHERE gu.uid=%s)
                )
                ORDER BY r.id
            """.format(
                operation=operation
            ),
            (model, self._uid),
        )
        return self.browse(row[0] for row in self._cr.fetchall()).exists()

    def check_restrictions(self, model, operation, raise_exception):
        model_restrictions = self._get_model_restrictions(model, operation)
        res = not model_restrictions or not (
            model_restrictions - self._get_passed_restrictions(model, operation)
        )
        if not res and raise_exception:
            failed_restrictions = model_restrictions - self._get_passed_restrictions(
                model, operation
            )
            self._raise_access_exception(model, operation, failed_restrictions)
        return res

    @api.constrains("groups")
    def _check_groups(self):
        if self.filtered(lambda r: not r.groups):
            raise exceptions.ValidationError(
                _("Restrictions must have at least one allowed group")
            )
