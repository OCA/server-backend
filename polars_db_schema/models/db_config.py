import connectorx as cx
import polars as pl

from odoo import exceptions, fields, models


class DbConfig(models.Model):
    _inherit = "db.config"

    db_type_id = fields.Many2one(comodel_name="db.type")
    db_table_ids = fields.One2many(comodel_name="db.table", inverse_name="db_config_id")
    row_count_query = fields.Text(related="db_type_id.row_count_query")

    def get_metadata(self):
        self.ensure_one()
        connexion = self._get_connexion()
        if self.row_count_query:
            self.read_sql(connexion, "SELECT 1")
            df = self.read_sql(connexion, self.row_count_query)
            if self.db_type_id.code == "sqlite":
                # https://docs.pola.rs/user-guide/expressions/user-defined-functions/#processing-individual-values-with-map_elements
                df = df.with_columns(
                    pl.col("stat").map_elements(sqlite, return_dtype=pl.Int32)
                )
                df = df.rename({"tbl": "name", "stat": "row_count"})
                df = df.unique(maintain_order=True)
                # stat columns store extra info leading to duplicate lines,
                # then make it unique
            df = df.filter(pl.col("row_count") > 0).with_columns(
                db_config_id=pl.lit(self.id)
            )
            self.env["db.table"].search([("db_config_id", "=", self.id)]).unlink()
            self.env["db.table"].create(df.to_dicts())

    def read_sql(self, connexion, query):
        try:
            return cx.read_sql(connexion, query, return_type="polars")
        except RuntimeError as err:
            raise exceptions.ValidationError(err) from err
        except Exception as err:
            raise exceptions.ValidationError(err) from err


def sqlite(value):
    "Extract row_count info from 'stat' column"
    values = value.split(" ")
    return values and int(values[0]) or int(value)
