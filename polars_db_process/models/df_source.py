from pathlib import Path

from odoo import fields, models
from odoo.modules.module import get_module_path
from odoo.tools.safe_eval import safe_eval

MODULE = __name__[12 : __name__.index(".", 13)]

HELP = """Supported files: .xlsx and .sql
Sql files may contains a comment on first line
to be mapped automatically with model_map, i.e:\n
-- {'model_id': 'product.product', 'db_conf_id': mydb}
-- {'code': 'my_delivery_address', 'db_conf_id': mydb}
"""

PARAMS = """{'model': False, 'code': False, 'db_conf': False}
# 'model/code' to guess model.map', db_conf' name to guess db.config
"""


class DfSource(models.Model):
    _inherit = "df.source"

    name = fields.Char(help=HELP)
    query = fields.Char()
    params = fields.Char(
        string="File Parameters",
        default=PARAMS,
        readonly=True,
        help="Coming from sql files",
    )
    db_conf_id = fields.Many2one(
        comodel_name="db.config", help="Database Configuration"
    )

    def _reset_process(self):
        res = super()._reset_process()
        mapp = self.model_map_id
        if mapp and mapp.action == "import":
            mapp._remove_uidstring_related_records()
        return res

    # def tmp(self, file, vals=None):
    #     db_confs = {x.name: x.id for x in self.env['db.config'].search([])}
    #     if meta:
    #         vals['params'] = meta
    #     def guess_model_and_db():
    #         domain=[]
    #         if meta.get("model"):
    #             domain.append(("model_id.name", '=', meta.get("model")))
    #         if meta.get("code"):
    #             domain.append(("code", '=', meta.get("code")))
    #         if domain:
    #             res = self.env["model.map"].search(domain)
    #             vals["model_map_id"] = res and res[0].id
    #         vals["db_conf_id"] = db_confs.get(meta.get("db_conf"))
    #     guess_model_and_db()

    def _file_hook(self, file):
        "Map sql file with the right Odoo model via model_map and the right db.config"
        vals = super()._file_hook(file)
        if ".sql" in file:
            # TODO: improve
            content = self._get_file(file).decode("utf-8")
            contents = content.split("\n")
            if contents:
                # we only detect first line
                metadata = safe_eval(contents[0].replace("--", ""))
                model_name = metadata.get("model")
                model = self.env["ir.model"].search([("model", "=", model_name)])
                if model_name:
                    # we don't want to use these model_maps
                    model_maps = (
                        self.env["df.source"]
                        .search([])
                        .filtered(lambda s: not s.db_conf_id)
                        .mapped("model_map_id")
                    )
                    model_map = self.env["model.map"].search(
                        [
                            ("id", "not in", model_maps.ids),
                            ("model_id", "=", model_name),
                        ]
                    )
                    if model_map:
                        # TODO use first
                        vals["model_map_id"] = model_map[0].id
                        db_config = self.env["db.config"].search(
                            [("name", "ilike", metadata.get("db_conf_id"))]
                        )
                        vals["db_conf_id"] = db_config and db_config[0].id or False
                    else:
                        df = self.env["model.map"].create(
                            {"code": model.name, "model_id": model and model[0].id}
                        )
                        vals["model_map_id"] = df.id
            vals["query"] = content
        return vals

    def _populate(self):
        chinook = self.env.ref(f"{MODULE}.sqlite_chinook")
        if chinook:
            # Demo behavior only
            path = Path(get_module_path(MODULE)) / "data/chinook.sqlite"
            chinook.string_connexion = f"sqlite://{str(path)}"
        return super()._populate()

    def _get_test_file_paths(self):
        res = super()._get_test_file_paths()
        res.update(
            {
                "polars_db_process": {
                    "relative_path": "data/files",
                    "xmlid": "polars_db_process.contact_chinook",
                }
            }
        )
        return res
