from collections import defaultdict

import polars as pl

from odoo import exceptions, fields, models
from odoo.tools.safe_eval import safe_eval


class DbConfig(models.Model):
    _inherit = "db.config"

    db_type_id = fields.Many2one(comodel_name="db.type")
    db_table_ids = fields.One2many(comodel_name="db.table", inverse_name="db_config_id")
    row_count_query = fields.Text(related="db_type_id.row_count_query")
    table_exclude = fields.Char(
        help="Remove tables with a name matching like sql expression"
    )
    table_sort = fields.Char()
    manually_entries = fields.Text(
        readonly=True,
        help="Odoo matching models, alias and display. " "Can be backup in your module",
    )

    def get_db_metadata(self):
        self.ensure_one()
        foreign, entries = {}, {}
        if self.db_type_id.foreign_key_query:
            foreign = self._get_foreign_keys(self._get_aliases())
        if self.row_count_query:
            sql = self.row_count_query
            if self.table_exclude:
                sql = sql.replace(
                    "WHERE", f"WHERE name NOT like '{self.table_exclude}' AND"
                )
            df = self._read_sql(sql)
            if self.db_type_id.code == "sqlite":
                # Sqlite has weird information schema structure
                # we need a little hack
                df = sqlite(df)
            df = df.filter(pl.col("row_count") > 0).with_columns(
                # add m2o foreign key
                db_config_id=pl.lit(self.id)
            )
            df = self._filter_df(df)
            self.env["db.table"].search(
                ["|", ("db_config_id", "=", False), ("db_config_id", "=", self.id)]
            ).unlink()
            if self.manually_entries:
                entries = safe_eval(self.manually_entries)
            vals_list = []
            for row in df.to_dicts():
                name = row.get("name")
                if name in foreign:
                    row["foreign_keys"] = "\n".join(foreign[name])
                if entries:
                    if name in entries.get("odoo_model"):
                        row["odoo_model"] = entries["odoo_model"][name]
                    if name in entries.get("alias"):
                        row["alias"] = entries["alias"][name]
                vals_list.append(row)
            self.env["db.table"].create(vals_list)

    def _get_foreign_keys(self, aliases):
        foreign = defaultdict(list)
        df = self._read_sql(self.db_type_id.foreign_key_query)
        mdicts = df.to_dicts()
        cols = ["primary_table", "foreign_table", "fk_column_name"]
        if mdicts and any([x for x in cols if x not in mdicts[0].keys()]):
            raise exceptions.ValidationError(
                f"Missing one of these columns {cols} in the query"
            )
        for mdict in mdicts:
            primary_table = aliases.get(mdict["primary_table"])
            primary_table = (
                aliases.get(mdict["primary_table"]) or mdict["primary_table"]
            )
            foreign[mdict["foreign_table"]].append(
                f"{mdict['fk_column_name']} = {primary_table}.{mdict['pk_column_name']}"
            )
        return foreign

    def _get_aliases(self, reverse=False):
        self.ensure_one()
        aliases = {x.name: x.alias for x in self.db_table_ids if x.alias}
        if reverse:
            return {value: key for key, value in aliases.items()}
        return aliases

    def _save_manually_entered_data(self):
        def get_dict_format(column):
            res = ", ".join(
                [f"'{x.name}': '{x[column]}'" for x in self.db_table_ids if x[column]]
            )
            if res:
                return safe_eval(f"{ {res} }".replace('"', ""))
            return

        mdict = {}
        for mvar in ("odoo_model", "alias", "display"):
            sub_dict = get_dict_format(mvar)
            if sub_dict:
                mdict[mvar] = sub_dict
        self.manually_entries = str(mdict).replace("}, '", "},\n'")

    def _filter_df(self, df):
        "You may want ignore some tables: inherit me"
        return df


def sqlite(df):
    "Extract row_count info from 'stat' column"

    def extract_first_part(value):
        values = value.split(" ")
        return values and int(values[0]) or int(value)

    return (
        df.with_columns(
            pl.col("stat").map_elements(extract_first_part, return_dtype=pl.Int32)
        )
        # rename columns
        .rename({"stat": "row_count"})
        # stat columns store extra info leading to duplicate lines,
        # then make it unique
        .unique(maintain_order=True)
    )
