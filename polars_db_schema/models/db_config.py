import polars as pl

from odoo import fields, models


class DbConfig(models.Model):
    _inherit = "db.config"

    db_type_id = fields.Many2one(comodel_name="db.type")
    db_table_ids = fields.One2many(comodel_name="db.table", inverse_name="db_config_id")
    row_count_query = fields.Text(related="db_type_id.row_count_query")

    def get_db_metadata(self):
        self.ensure_one()
        if self.row_count_query:
            self._read_sql("SELECT 1")
            df = self._read_sql(self.row_count_query)
            if self.db_type_id.code == "sqlite":
                # https://docs.pola.rs/user-guide/expressions/user-defined-functions/#processing-individual-values-with-map_elements
                df = (
                    df.with_columns(
                        pl.col("stat").map_elements(sqlite, return_dtype=pl.Int32)
                    )
                    # rename columns
                    .rename({"tbl": "name", "stat": "row_count"})
                    # stat columns store extra info leading to duplicate lines,
                    # then make it unique
                    .unique(maintain_order=True)
                )
            df = df.filter(pl.col("row_count") > 0).with_columns(
                # add m2o foreign key
                db_config_id=pl.lit(self.id)
            )
            df = self._filter_df(df)
            self.env["db.table"].search([("db_config_id", "=", self.id)]).unlink()
            self.env["db.table"].create(df.to_dicts())

    def _filter_df(self, df):
        "You may want ignore some tables: inherit me"
        return df


def sqlite(value):
    "Extract row_count info from 'stat' column"
    values = value.split(" ")
    return values and int(values[0]) or int(value)
