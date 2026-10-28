# Copyright 2018 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
import logging

from . import models
from . import controllers
from . import radicale


def _restore_odoo_runbot_level_name():
    """Restore odoo RUNBOT level display name after Radicale imports."""
    runbot_level = getattr(logging, "RUNBOT", 25)
    if logging.getLevelName(runbot_level) != "INFO":
        logging.addLevelName(runbot_level, "INFO")


_restore_odoo_runbot_level_name()
