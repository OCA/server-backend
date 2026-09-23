from odoo.tools import config

if config["with_demo"]:
    from . import backend_dummy_model
