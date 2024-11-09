import base64
from collections import defaultdict
from pathlib import Path

from odoo import _, exceptions, fields, models
from odoo.modules.module import get_module_path

from .. import slug_me

# You can store files .xlxs and .sql in this relative path of your module
DF_RELATIVE_SOURCE_DIR = "data/df"


class DfSource(models.Model):
    _name = "df.source"
    _inherit = ["upsert.mixin"]
    _description = "Dataframe data source"
    _rec_name = "name"
    _rec_names_search = ["name"]

    model_map_id = fields.Many2one(
        comodel_name="model.map", required=True, ondelete="cascade"
    )
    name = fields.Char(required=True, help="Supported files: .xlsx")
    sequence = fields.Integer()
    state = fields.Selection(
        selection=[("draft", "Draft"), ("ready", "Ready"), ("done", "Done")],
        default="draft",
    )
    rename = fields.Boolean(help="Display renamed Dataframe in wizard")
    template = fields.Binary(string="File", attachment=False)
    readonly = fields.Boolean(help="Imported records from module are readonly created")

    def start(self):
        self.ensure_one()
        vals = {
            "filename": self.name,
            "df_source_id": self.id,
            "model_map_id": self.model_map_id.id,
        }
        if ".xlsx" in self.name:
            vals["file"] = base64.b64encode(self._get_file())
        transient = self.env["df.process.wiz"].create(vals)
        action = self.env.ref("polars_process.df_process_wiz_action")._get_action_dict()
        action["res_id"] = transient.id
        self.state = "done"
        return action

    def reset_process(self):
        self.ensure_one()
        self._reset_process()

    def _reset_process(self):
        "Inherit me"
        self.state = "draft"

    def _populate(self):
        "Create/Update in current model, module files in DF_RELATIVE_SOURCE_DIR"

        def get_model_map():
            model_map = defaultdict(dict)
            for elm in self.env["model.map"].search([]):
                model_map.update({elm.code: elm.id})
            return model_map

        def update_file_vals(myfile, addon, idstring):
            with open(myfile, "rb") as f:
                name = f.name[f.name.find(addon) :]
                vals = {
                    "model_map_id": self.env.ref(idstring).id,
                    "name": name,
                    "readonly": True,
                }
                self._file_hook(vals, name, db_confs, model_map)
                self._upsert_record(
                    "df.source", f"{slug_me(name)}", vals, module="df_source"
                )

        paths = self._get_modules_w_df_files()
        db_confs = self._get_db_confs()
        model_map = get_model_map()
        for addon, data in paths.items():
            if "xmlid" not in data:
                raise exceptions.ValidationError(
                    _("Missing xmlid key in _get_modules_w_df_files()")
                )
            idstring = data["xmlid"]
            if self.env.ref(idstring):
                mpath = Path(get_module_path(addon)) / DF_RELATIVE_SOURCE_DIR
                for mfile in tuple(mpath.iterdir()):
                    update_file_vals(mfile, addon, idstring)
        action = self.env.ref("polars_process.df_source_action")._get_action_dict()
        return action

    def _get_db_confs(self):
        return {}

    def _get_file(self, name=None):
        # TODO Clean
        if self.template:
            return self.template
        name = self.name or name
        module = name[: name.find("/")]
        path = Path(get_module_path(module))
        path = path / DF_RELATIVE_SOURCE_DIR / name[name.rfind("/") + 1 :]
        with open(path, "rb") as f:
            return f.read()

    def _get_modules_w_df_files(self):
        """
        You may override if you want populate files in your module
        returns:
        {"module_name": {
            "xmlid": "model_map_xml_id"}
            }
        }
        """
        return {
            "polars_process": {
                "xmlid": "polars_process.model_map_contact",
            }
        }

    def _file_hook(self, initial_vals, file, db_confs, model_map):
        "Overide me in your own module"
        return {}
