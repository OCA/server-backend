from odoo import SUPERUSER_ID, api


def uninstall_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    env["ir.actions.server.navigate.line"].search([]).unlink()
    env["ir.actions.server"].search([("state", "=", "navigate")]).unlink()
