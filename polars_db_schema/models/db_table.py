import base64
import io

import connectorx as cx
import polars as pl

from odoo import _, exceptions, fields, models


class DbTable(models.Model):
    _name = "db.table"
    _description = "Access to database tables"
    _order = "row_count DESC"

    name = fields.Char(required=True, help="Name of the table")
    row_count = fields.Integer(required=True, help="Number of rows contained in table")
    xlsx = fields.Binary(string="File", attachment=False, readonly=True)
    db_config_id = fields.Many2one(comodel_name="db.config")
    filename = fields.Char()
    sql = fields.Text(
        string="Significant Columns", help="Columns with variable data over rows"
    )
    uniques = fields.Text(
        string="Unique Values",
        help="Columns with the same value over rows.\n"
        "It could be useless to extract data from these columns,\n"
        "because they're probably unused by the application",
    )

    def get_metadata_info(self):
        self.ensure_one()
        query = f"SELECT * FROM {self.name}"
        connexion = self.db_config_id._get_connexion()
        df = cx.read_sql(connexion, query, return_type="polars")
        excluded_types = self.db_config_id.db_type_id.excluded_types.split("\n")
        cols = [x[0] for x in df.schema.items() if str(x[1]) not in excluded_types]
        new_cols = []
        uniques = {}
        for col in cols:
            # TODO improve it
            # Some database have dirty column names: :-(
            conditions = [x for x in (" ", "*", "-") if x in col]
            if any(conditions):
                continue
            query = f"SELECT distinct {col} FROM self"
            res = df.sql(query)
            if len(res) > 1:
                new_cols.append(col)
            else:
                # column has the same value whatever row
                uniques[col] = res.to_series()[0]
        self.uniques = f"{uniques}"
        if new_cols:
            self.sql = f"SELECT {', '. join(new_cols)}\nFROM {self.name};\n"

    # WARNING Thread <Thread(odoo.service.http.request.129007460812352,
    # started 129007460812352)> virtual real time limit (151/120s) reached.
    # Dumping stacktrace of limit exceeding threads before reloading

    def get_spreadsheet(self):
        self.ensure_one()
        if not self.sql:
            self.get_metadata_info()
        if not self.sql:
            raise exceptions.ValidationError(
                _(
                    "There is no column with varaiable data in this table: "
                    "check Uniques Values column"
                )
            )
        df = cx.read_sql(
            self.db_config_id._get_connexion(), self.sql, return_type="polars"
        )
        excel_stream = io.BytesIO()
        vals = {"workbook": excel_stream}
        vals.update(self.get_spreadsheet_settings())
        df.write_excel(**vals)
        excel_stream.seek(0)
        self.filename = f"{self.name}.xlsx"
        self.xlsx = base64.encodebytes(excel_stream.read())

    def get_spreadsheet_settings(self):
        return {
            "position": "A1",
            "table_style": "Table Style Light 16",
            "dtype_formats": {pl.Date: "dd/mm/yyyy"},
            "float_precision": 6,
            "header_format": {"bold": True, "font_color": "#702963"},
            "freeze_panes": "A2",
            "autofit": True,
        }
