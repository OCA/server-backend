import base64
import io

import connectorx as cx
import polars as pl

from odoo import _, exceptions, fields, models


class DbTable(models.Model):
    _name = "db.table"
    _description = "Access to database tables"
    _order = "row_count DESC"

    name = fields.Char(required=True, readonly=True, help="Name of the table")
    row_count = fields.Integer(
        string="Count", readonly=True, help="Number of rows contained in the table"
    )
    xlsx = fields.Binary(string="File", attachment=False, readonly=True)
    db_config_id = fields.Many2one(
        comodel_name="db.config", required=True, readonly=True
    )
    filename = fields.Char(readonly=True)
    foreign_keys = fields.Text(readonly=True, help="Foreign keys towards other tables")
    alias = fields.Char(help="Used to make SQL query easier to read")
    odoo_model = fields.Char(help="Odoo matching model")
    display = fields.Char(
        help="Fields to combinate (separated by comma) to give a "
        "user friendly representation of the record"
    )
    sql = fields.Text(
        string="Relevant Columns",
        readonly=True,
        help="Columns with variable data over rows",
    )
    unique = fields.Text(
        string="Unique Values",
        readonly=True,
        help="Columns with the same value over rows.\n"
        "It could be useless to extract data from these columns,\n"
        "because they're probably unused by the application",
    )

    def get_metadata_info(self):
        self.ensure_one()
        query = f"SELECT * FROM {self.name}"
        connexion = self.db_config_id._get_connexion()
        df = cx.read_sql(connexion, query, return_type="polars")
        # i.e. Binary types should be ignored because of display considerations
        excluded_types = self.db_config_id.db_type_id.excluded_types.split("\n")
        cols = [x[0] for x in df.schema.items() if str(x[1]) not in excluded_types]
        relevant_cols = []
        unique = {}
        key_cols, relations = "", ""
        # Search columns with non unique value in rows
        for col in cols:
            # TODO improve it
            # Some database have dirty column names: :-(
            conditions = [x for x in (" ", "*", "-") if x in col]
            if any(conditions):
                continue
            query = f"SELECT distinct {col} FROM self"
            res = df.sql(query)
            if len(res) > 1:
                relevant_cols.append(f"{self.alias or self.name}.{col}")
            else:
                # column has the same value on any rows
                # we prefer ignore them
                unique[col] = res.to_series()[0]
        self.unique = f"{unique}"
        #
        if self.foreign_keys:
            # AR_Substitut = art.AR_Substitut
            # cbCL_No1 = cat.cbCL_No1
            # cbCL_No2 = cat.cbCL_No2
            # cbCL_No3 = cat.cbCL_No3
            # cbCL_No4 = cat.cbCL_No4
            joint = [
                x.split(".")[0].split(" = ")[1] for x in self.foreign_keys.split("\n")
            ]
            count = {x: joint.count(x) for x in set(joint)}
            # breakpoint()  # import pdb; pdb.set_trace()
            foreign_list = [
                # table, foreign=othertable.colname
                # x[0],  x[1][0]       x[1][1]
                (self.name, x.split(" = "))
                for x in self.foreign_keys.split("\n")
            ]
            count2 = count.copy()

            def aliascnt(val, var=count, decrease=False):
                if val in var and var[val] > 1:
                    res = f"{val}{var[val]}"
                    if decrease:
                        var[val] -= 1
                    return res
                return val

            key_cols = (
                ", ".join(
                    [
                        f"{aliascnt(x[1][1].split('.')[0], var=count2, decrease=True)}"
                        f".{x[1][1].split('.')[1]}"
                        for x in foreign_list
                    ]
                )
                + ","
            )
            aliases = self.db_config_id._get_aliases()
            aliases_rev = self.db_config_id._get_aliases(reverse=True)
            relations = "\n\t".join(
                [
                    f"LEFT JOIN {aliases_rev.get(x[1][1].split('.')[0], x[0])} "
                    f"{aliascnt(x[1][1].split('.')[0])} ON {aliases.get(x[0], x[0])}"
                    f".{x[1][0]} = {aliascnt(x[1][1].split('.')[0], decrease=True)}"
                    f".{x[1][1].split('.')[1]}"
                    for x in foreign_list
                ]
            )
        if relevant_cols:
            self.sql = f"""SELECT {key_cols} {', '. join(relevant_cols)}
FROM {self.name} {self.alias or ''}\n\t{relations};\n"""

    # WARNING Thread <Thread(odoo.service.http.request.129007460812352,
    # started 129007460812352)> virtual real time limit (151/120s) reached.
    # Dumping stacktrace of limit exceeding threads before reloading

    def write(self, vals):
        res = super().write(vals)
        if "odoo_model" in vals or "alias" in vals or "display" in vals:
            for conf in self.mapped("db_config_id"):
                conf._save_manually_entered_data()
        return res

    def get_spreadsheet(self):
        self.ensure_one()
        if not self.sql:
            self.get_metadata_info()
        if not self.sql:
            raise exceptions.ValidationError(
                _(
                    "There is no column with variable data in this table: "
                    "check Uniques Values column"
                )
            )
        df = cx.read_sql(
            self.db_config_id._get_connexion(), self.sql, return_type="polars"
        )
        excel_stream = io.BytesIO()
        vals = {"workbook": excel_stream}
        vals.update(self._get_spreadsheet_settings())
        df.write_excel(**vals)
        excel_stream.seek(0)
        self.filename = f"{self.name}.xlsx"
        self.xlsx = base64.encodebytes(excel_stream.read())

    def _get_spreadsheet_settings(self):
        return {
            "position": "A1",
            "table_style": "Table Style Light 16",
            "dtype_formats": {pl.Date: "dd/mm/yyyy"},
            "float_precision": 6,
            "header_format": {"bold": True, "font_color": "#702963"},
            "freeze_panes": "A2",
            "autofit": True,
        }
