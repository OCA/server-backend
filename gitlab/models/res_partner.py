from odoo import api, fields, models, tools


class ResPartner(models.Model):
    _inherit = "res.partner"

    gitlab_username = fields.Char()
    gitlab_email = fields.Char()

    @api.model
    @tools.ormcache("username")
    def get_by_gitlab_username(self, username):
        partner = self.search([("gitlab_username", "=", username)], limit=1)
        return partner.id if partner else None

    @api.model
    @tools.ormcache("email")
    def get_by_gitlab_email(self, email):
        partner = self.search([("gitlab_email", "=", email)], limit=1)
        return partner.id if partner else None

    def write(self, vals):
        self.env.registry.clear_cache()
        return super().write(vals)

    def unlink(self):
        self.env.registry.clear_cache()
        return super().unlink()

    @api.model_create_multi
    def create(self, vals_list):
        self.env.registry.clear_cache()
        return super().create(vals_list)
