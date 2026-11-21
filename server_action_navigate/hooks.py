def uninstall_hook(env):
    env["ir.actions.server.navigate.line"].search([]).unlink()
    env["ir.actions.server"].search([("state", "=", "navigate")]).unlink()
