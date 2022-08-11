# Copyright 2014 ABF OSIELL <http://osiell.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
import datetime
import logging

from odoo import SUPERUSER_ID, api, fields, models

_logger = logging.getLogger(__name__)


class ResUsersRole(models.Model):
    _name = "res.users.role"
    _inherits = {"res.groups": "group_id"}
    _description = "User role"

    group_id = fields.Many2one(
        comodel_name="res.groups",
        required=True,
        ondelete="cascade",
        readonly=True,
        string="Associated group",
    )
    line_ids = fields.One2many(
        comodel_name="res.users.role.line", inverse_name="role_id", string="Role lines"
    )
    user_ids = fields.One2many(
        comodel_name="res.users", string="Users list", compute="_compute_user_ids"
    )
    group_category_id = fields.Many2one(
        related="group_id.category_id",
        default=lambda cls: cls.env.ref("base_user_role.ir_module_category_role").id,
        string="Associated category",
        help="Associated group's category",
        readonly=False,
    )

    @api.depends("line_ids.user_id")
    def _compute_user_ids(self):
        for role in self.sudo() if self._bypass_rules() else self:
            role.user_ids = role.line_ids.mapped("user_id")

    @api.model
    def _bypass_rules(self):
        # Run methods as super user to avoid problems by "Administrator/Access Right"
        return self._name == "res.users.role" and self.env.user.has_group(
            "base.group_erp_manager"
        )

    @api.model
    def create(self, vals):
        model = (self.sudo() if self._bypass_rules() else self).browse()
        new_record = super(ResUsersRole, model).create(vals)
        new_record.update_users()
        return new_record

    def read(self, fields=None, load="_classic_read"):
        recs = self.sudo() if self._bypass_rules() else self
        return super(ResUsersRole, recs).read(fields, load)

    def write(self, vals):
        recs = self.sudo() if self._bypass_rules() else self
        # Workaround to solve issue with broken code in odoo that clear the
        # cache during the write: see odoo/addons/base/models/res_users.py#L226
        groups_vals = {}
        for field in recs.group_id._fields:
            if field in vals:
                groups_vals[field] = vals.pop(field)
        if groups_vals:
            recs.group_id.write(groups_vals)
        res = super(ResUsersRole, recs).write(vals)
        recs.update_users()
        return res

    def unlink(self):
        users = self.mapped("user_ids")
        res = super(ResUsersRole, self).unlink()
        users.set_groups_from_roles(force=True)
        return res

    def update_users(self):
        """Update all the users concerned by the roles identified by `ids`."""
        users = self.mapped("user_ids")
        users.set_groups_from_roles()
        return True

    @api.model
    def cron_update_users(self):
        logging.info("Update user roles")
        self.search([]).update_users()


class ResUsersRoleLine(models.Model):
    _name = "res.users.role.line"
    _description = "Users associated to a role"

    active = fields.Boolean(related="user_id.active")
    role_id = fields.Many2one(
        comodel_name="res.users.role", required=True, string="Role", ondelete="cascade"
    )
    user_id = fields.Many2one(
        comodel_name="res.users",
        required=True,
        string="User",
        domain=[("id", "!=", SUPERUSER_ID)],
        ondelete="cascade",
    )
    date_from = fields.Date("From")
    date_to = fields.Date("To")
    is_enabled = fields.Boolean("Enabled", compute="_compute_is_enabled")
    _sql_constraints = [
        (
            "user_role_uniq",
            "unique (user_id,role_id)",
            "Roles can be assigned to a user only once at a time",
        )
    ]

    @api.depends("date_from", "date_to")
    def _compute_is_enabled(self):
        today = datetime.date.today()
        for role_line in self:
            role_line.is_enabled = True
            if role_line.date_from:
                date_from = role_line.date_from
                if date_from > today:
                    role_line.is_enabled = False
            if role_line.date_to:
                date_to = role_line.date_to
                if today > date_to:
                    role_line.is_enabled = False

    def unlink(self):
        users = self.mapped("user_id")
        res = super(ResUsersRoleLine, self).unlink()
        users.set_groups_from_roles(force=True)
        return res
