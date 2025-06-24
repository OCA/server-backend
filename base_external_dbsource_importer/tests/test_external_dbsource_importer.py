from odoo_test_helper import FakeModelLoader

from odoo import Command
from odoo.tests import tagged

from odoo.addons.base.tests.common import BaseCommon


@tagged("post_install", "-at_install")
class TestExternalDBSource(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Load a test model using odoo_test_helper
        cls.loader = FakeModelLoader(cls.env, cls.__module__)
        cls.loader.backup_registry()
        from .models import BaseExternalDbsourceTest, ResPartnerWithMixin

        cls.loader.update_registry((BaseExternalDbsourceTest,))
        cls.loader.update_registry((ResPartnerWithMixin,))
        cls.dbsource = cls.dbsource = cls.env["base.external.dbsource"].create(
            {
                "connector": "test",
                "name": "Test data loader",
            }
        )

    @classmethod
    def tearDownClass(cls):
        cls.loader.restore_registry()
        super().tearDownClass()

    def _import_data(self):
        ext_records, records, records_dic = self.dbsource.test_importer.load_data(
            "res.partner", "test_table"
        )
        for record in ext_records:
            self.dbsource.test_importer.upsert(
                str(record["id"]),
                records,
                records_dic,
                {
                    "name": record["name"],
                    "email": record["email"],
                    "is_company": record["is_company"],
                    "test_ext_key": record["id"],
                },
            )

    def test_import(self):
        self._import_data()
        partner = self.env["res.partner"].search([("name", "=", "John Test")], limit=1)
        self.assertTrue(partner, "Contact 'John Test' was not created in Odoo")
        self.assertEqual(partner.email, self.dbsource.test_importer.data[0]["email"])
        # We now change source data
        imported_partner_email = partner.email
        imported_partner_id = partner.id
        new_email = "new_email@example.com"
        new_name = "John Doe Test"
        self.dbsource.test_importer.data[0]["email"] = new_email
        self.dbsource.test_importer.data[0]["name"] = new_name
        # But only want want to update name, not email
        self.dbsource.write(
            {
                "fields_to_update_ids": [
                    Command.create(
                        {
                            "model_id": self.env.ref("base.model_res_partner").id,
                            "field_ids": [
                                Command.set(
                                    [
                                        self.env.ref("base.field_res_partner__name").id,
                                    ],
                                )
                            ],
                        },
                    ),
                ]
            }
        )
        self._import_data()
        partner = self.env["res.partner"].browse(imported_partner_id)
        partner2 = self.env["res.partner"].search([("name", "=", "Test INC.")])
        self.assertEqual(
            len(partner2), 1, "Records should not be duplicated when importing again"
        )

        self.assertTrue(partner, "Partner should still exist")
        self.assertEqual(
            partner.email,
            imported_partner_email,
            "Email got updated when it wasn't in 'fields_to_update_ids'",
        )
        self.assertEqual(
            partner.name,
            new_name,
            "Name didn't get updated when it was in 'fields_to_update_ids'",
        )
