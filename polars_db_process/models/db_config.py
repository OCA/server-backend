from pathlib import Path

import connectorx as cx

from odoo import _, exceptions, fields, models
from odoo.modules.module import get_module_path

MODULE = __name__[12 : __name__.index(".", 13)]
HELP = """
String connexion samples:

postgres://user:PASSWORD@server:port/database
mssql://user:PASSWORD@server:port/db.encrypt=true&trusted_connection=false
sqlite:///home/user/path/test.db
mysql://user:PASSWORD@server:port/database
oracle://user:PASSWORD@server:port/database
"""


class DbConfig(models.Model):
    _name = "db.config"
    _description = "External db.configuration"
    _rec_name = "name"
    _order = "name"
    _rec_names_search = ["name"]

    name = fields.Char(required=True)
    string_connexion = fields.Char(required=True, help=HELP)
    password = fields.Char(help="Not required for Sqlite")

    def _get_connexion(self):
        return self.string_connexion.replace("PASSWORD", self.password or "")

    def test_connexion(self):
        try:
            query = "SELECT 1"
            if "sqlite" in self.string_connexion:
                query = "SELECT tbl FROM sqlite_stat1"
            self._read_sql(query)
            message = _("Connexion OK !")
            kind = "success"
            emoji = ":-)"
        except Exception as error:
            emoji = ":-("
            kind = "warning"
            message = f"Something bad with connexion:\n\n'{error}'"
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": f"Test connexion {emoji}",
                "type": kind,  # warning/success
                "message": message,
                "sticky": True,  # True/False will display for few seconds if false
                "next": {"type": "ir.actions.act_window_close"},
            },
        }

    def _read_sql(self, query, return_type="polars"):
        try:
            return cx.read_sql(self._get_connexion(), query, return_type=return_type)
        except RuntimeError as err:
            raise exceptions.ValidationError(err) from err
        except TimeoutError as err:
            raise exceptions.ValidationError(err) from err
        except Exception as err:
            raise exceptions.ValidationError(err) from err

    def _set_uidstring_module_name(self):
        return "polars"

    def _update_sqlite_demo_file_path(self):
        "Only relative path is known in xml data, we need to recompute when inserted"
        chinook = self.env.ref(f"{MODULE}.sqlite_chinook")
        if chinook:
            chinook.string_connexion = (
                f"sqlite://{Path(get_module_path(MODULE)) / 'data/chinook.sqlite'}"
            )
