from pathlib import Path

from odoo import fields, models
from odoo.exceptions import ValidationError
from odoo.modules.module import get_module_path
from odoo.tools.safe_eval import safe_eval

from odoo.addons.polars_process import slug_me

MODULE = __name__[12 : __name__.index(".", 13)]

HELP = """Supported: .xlsx  files and .sql
Sql files may contains a comment on first line captured by File Parameters field
to be mapped automatically with related objects, i.e:\n
{'map_model': 'my_delivery_address', 'db_conf': mydb, 'where': [{''}]}

"""


class DfSource(models.Model):
    _inherit = "df.source"

    name = fields.Char(help=HELP)
    query = fields.Text(string="Base query", related="query_id.query")
    where = fields.Char(help="Sql where condition")
    db_conf_id = fields.Many2one(
        comodel_name="db.config", help="Database Configuration"
    )
    query_id = fields.Many2one(comodel_name="df.query", help="Dataframe Query")

    def _reset_process(self):
        res = super()._reset_process()
        mapp = self.model_map_id
        if mapp and mapp.action == "import":
            mapp._remove_uidstring_related_records()
        return res

    def _file_hook(self, initial_vals, file, db_confs, model_map):
        "Map sql file with the right Odoo model via model_map and the right db.config"
        vals = super()._file_hook(initial_vals, file, db_confs, model_map)
        if ".sql" in file and model_map:
            content = self._get_file(file).decode("utf-8")
            contents = content.split("\n")
            meta, sql = [], []
            if contents:
                meta_end = False
                for content in contents:
                    if content[:2] == "--" and not meta_end:
                        # collect first lines prefixed by '--'
                        meta.append(content.replace("--", ""))
                    else:
                        # collect other lines
                        meta_end = True
                        sql.append(content)
                if meta and sql:
                    meta = safe_eval(" ".join(meta))
                    # {'map_code': chinook customers', 'db_conf': Chinook}
                    keys = ("model_code", "db_conf", "name")
                    if [x for x in keys if x not in meta]:
                        raise ValidationError(
                            f"At least one of these keys {keys} is not in params"
                        )
                    model_map_id = (model_map.get(meta["model_code"]),)
                    qvals = {
                        "db_conf_id": db_confs.get(meta["db_conf"]),
                        "params": meta,
                        "query": "\n".join(sql),
                        "name": meta["name"],
                    }
                    xml_id = slug_me(meta["name"])
                    self._upsert_record("df.query", xml_id, qvals, module="df_query")
                    query = self.env.ref(f"df_query.{xml_id}")
                    src = 0
                    for source in meta.get("where"):
                        xml_id = slug_me(initial_vals["name"])
                        if src > 0:
                            xml_id = f"{xml_id}_{src}"
                        svals = {
                            "where": source,
                            "model_map_id": model_map_id,
                            "query_id": query.id,
                            "name": initial_vals["name"],
                        }
                        src += 1
                        self._upsert_record(
                            "df.source", xml_id, svals, module="df_source"
                        )
        return vals

    def _get_db_confs(self):
        return {x.name: x.id for x in self.env["db.config"].search([])}

    def _populate(self):
        chinook = self.env.ref(f"{MODULE}.sqlite_chinook")
        if chinook:
            # TODO fix
            # Demo behavior only
            path = Path(get_module_path(MODULE)) / "data/chinook.sqlite"
            chinook.string_connexion = f"sqlite://{str(path)}"
        return super()._populate()

    def _get_modules_w_df_files(self):
        res = super()._get_modules_w_df_files()
        res.update(
            {
                "polars_db_process": {
                    "xmlid": "polars_db_process.contact_chinook",
                }
            }
        )
        return res
