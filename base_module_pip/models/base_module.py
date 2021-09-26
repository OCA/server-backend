# Copyright (C) 2021 Daniel Reis
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import subprocess
import sys

from odoo import api, models
from odoo.release import version_info


class BaseModule(models.Model):
    _inherit = "ir.module.module"

    def _get_pypi_package_name(self, module_name):
        server_version = version_info[0]
        return "odoo%d-addon-%s" % (server_version, module_name.replace("_", "-"))

    @api.model
    def action_pip_install(self, module_name):
        pkg_name = self._get_pypi_package_name(module_name)
        cmd = (sys.executable, "-m", "pip", "install", pkg_name)
        res = subprocess.run(
            *cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True
        )
        # TODO: find a way for res to have line breaks?
        return res
