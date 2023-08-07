from odoo.tools import config

if not config["without_demo"]:
    from . import backend_dummy_model
