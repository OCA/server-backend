# Copyright 2025 Tecnativa - David Bañón Gil
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models

from odoo.addons.base_external_dbsource_importer.models.base_external_dbsource import (
    BaseExternalModelImporter,
)


class BaseExternalModelImporterTest(BaseExternalModelImporter):
    _external_key = "test_ext_key"
    data = [
        {
            "id": 876,
            "name": "John Test",
            "email": "john@example.com",
            "is_company": False,
        },
        {
            "id": 877,
            "name": "Test INC.",
            "email": "test@example.com",
            "is_company": True,
        },
    ]

    def _get_external_records(self, table_name, fields="*", where=""):
        return self.data if table_name == "test_table" else []


# pylint: disable=consider-merging-classes-inherited
class BaseExternalDbsourceTest(models.Model):
    _inherit = "base.external.dbsource"

    connector = fields.Selection(
        selection_add=[("test", "Test")], ondelete={"test": "cascade"}
    )

    @property
    def test_importer(self):
        return BaseExternalModelImporterTest(dbsource=self)


# pylint: enable=consider-merging-classes-inherited
class ResPartnerWithMixin(models.Model):
    _inherit = ["res.partner", "dbsource.external.mixin"]
    _name = "res.partner"

    test_ext_key = fields.Char(copy=False)
