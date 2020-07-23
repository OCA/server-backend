# Copyright 2020 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import csv
from io import StringIO

from odoo import SUPERUSER_ID, api
from odoo.modules.module import get_resource_path
from odoo.tests import common

IMPORT_PATH = get_resource_path(
    "easy_massive_translation",
    "tests/files",
    "test_import_easy_massive_translation.csv",
)
IMPORT_PATH_2 = get_resource_path(
    "easy_massive_translation",
    "tests/files",
    "test_import_easy_massive_translation_2.csv",
)
IMPORT_PATH_3 = get_resource_path(
    "easy_massive_translation",
    "tests/files",
    "test_import_easy_massive_translation_3.csv",
)
IMPORT_PATH_4 = get_resource_path(
    "easy_massive_translation",
    "tests/files",
    "test_import_easy_massive_translation_4.csv",
)
IMPORT_PATH_5 = get_resource_path(
    "easy_massive_translation",
    "tests/files",
    "test_import_easy_massive_translation_5.csv",
)


@common.tagged("post_install", "-at_install")
class TestEasyMassiveTranslation(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestEasyMassiveTranslation, cls).setUpClass()
        wizard = cls.env["base.language.install"].create(
            {"lang": "es_ES", "overwrite": True}
        )
        wizard.lang_install()
        module = cls.env["ir.module.module"].search(
            [("name", "=", "product"), ("state", "=", "uninstalled")], limit=1
        )
        if module:
            module.button_immediate_install()
            api.Environment.reset()
            cls.env = api.Environment(cls.cr, SUPERUSER_ID, {})
        cls.product1 = cls.env.ref("product.product_product_25_product_template")

    @classmethod
    def create_translation(cls, path):
        # Import translation
        import_model = cls.env["ir.model"].search(
            [("model", "=", "product.template")], limit=1
        )
        with open(path, "rb") as template:
            content = template.read()
        file = base64.b64encode(content)
        cls.wizard_template = cls.env["import.massive.translation"].create(
            {"data": file, "translated_model": import_model.id}
        )
        cls.wizard_template.action_import()
        cls.product1.flush()
        cls.product1.invalidate_cache()

    def prepare_export_data(self, show_translated):
        export_model = self.env["ir.model"].search([("model", "=", "product.template")])
        export_languages = self.env["res.lang"].search(
            [("code", "in", ["en_US", "es_ES"])]
        )
        # Fields to be translated by external ID
        template_fields = (
            self.env.ref("product.field_product_template__description")
            + self.env.ref("product.field_product_template__description_purchase")
            + self.env.ref("product.field_product_template__description_sale")
            + self.env.ref("product.field_product_template__name")
        )
        # Create Wizard
        # Paraneter show_translated indicates whether fully translated terms
        # need to be added to the template
        wizard_template = self.env["export.massive.translation"].create(
            {
                "languages": [(6, 0, export_languages.ids)],
                "translated_model": export_model.id,
                "translated_fields": [(6, 0, template_fields.ids)],
                "show_translated": show_translated,
                "record_selection": "all",
            }
        )
        return_vals = wizard_template.get_file()
        document = self.env["export.massive.translation"].search(
            [("id", "=", return_vals.get("res_id"))]
        )
        # CSV file is created
        data = base64.b64decode(document.data).decode("utf-8")
        file_input = StringIO(data)
        file_input.seek(0)
        reader_info = []
        reader = csv.DictReader(file_input, delimiter=",", lineterminator="\r\n",)
        reader_info.extend(reader)
        return reader, reader_info

    def test_import_template(self):
        # Import translation
        self.create_translation(IMPORT_PATH)
        # Translation has been created
        self.assertEqual(
            "Bloque de pantallas acústicas - Test",
            self.product1.with_context(lang="es_ES").name,
        )
        # Origin term has not changed
        self.assertEqual("Acoustic Bloc Screens", self.product1.name)

    def test_update_translation(self):
        # Import translation
        self.create_translation(IMPORT_PATH)
        # Check current translation
        self.assertEqual(
            "Bloque de pantallas acústicas - Test",
            self.product1.with_context(lang="es_ES").name,
        )
        # Import new translation
        self.create_translation(IMPORT_PATH_2)
        # Check new translation
        self.assertNotEqual(
            "Bloque de pantallas acústicas - Test",
            self.product1.with_context(lang="es_ES").name,
        )
        self.assertEqual(
            "Bloque de pantallas acústicas - Modified",
            self.product1.with_context(lang="es_ES").name,
        )
        # Origin term has not changed
        self.assertEqual("Acoustic Bloc Screens", self.product1.name)

    def test_change_origin(self):
        # Import translation
        self.create_translation(IMPORT_PATH)
        # Check current translation and origin
        self.assertEqual(
            "Bloque de pantallas acústicas - Test",
            self.product1.with_context(lang="es_ES").name,
        )
        self.assertEqual("Acoustic Bloc Screens", self.product1.name)
        # Import new origin
        self.create_translation(IMPORT_PATH_3)
        # Check new origin (translation has not changed)
        self.assertNotEqual(
            "Acoustic Bloc Screens", self.product1.with_context(lang="es_ES").name
        )
        self.assertEqual("Acoustic Bloc Screens - New Name", self.product1.name)
        self.assertEqual(
            "Bloque de pantallas acústicas - Test",
            self.product1.with_context(lang="es_ES").name,
        )

    def test_change_translation_origin(self):
        # Import translation
        self.create_translation(IMPORT_PATH)
        # Check current translation and origin
        self.assertEqual(
            "Bloque de pantallas acústicas - Test",
            self.product1.with_context(lang="es_ES").name,
        )
        self.assertEqual("Acoustic Bloc Screens", self.product1.name)
        # Import new origin and translation
        self.create_translation(IMPORT_PATH_4)
        # Check new origin and translation
        self.assertNotEqual(
            "Bloque de pantallas acústicas - Test",
            self.product1.with_context(lang="es_ES").name,
        )
        self.assertEqual("Acoustic Bloc Screens - New Origin", self.product1.name)
        self.assertNotEqual(
            "Acoustic Bloc Screens", self.product1.with_context(lang="es_ES").name
        )
        self.assertEqual(
            "Bloque de pantallas acústicas - New Translation",
            self.product1.with_context(lang="es_ES").name,
        )

    def test_export_all_records(self):
        reader, reader_info = self.prepare_export_data(True)

        # The number of elements in the csv file should be the number of
        # records in the recordset
        num_lines = self.env["product.template"].search_count([])
        self.assertEqual(len(reader_info), num_lines)

        # Tu number of columns should be (num_languages + 1) * num_fields + 2
        # num_languages + 1 = 2 + 1 (1 is added as there is an origin column per field)
        # num_fields = 4
        # 2 is added as there are an id column and a reference column
        self.assertEqual(len(reader.fieldnames), 14)

    def test_export_not_translated(self):
        # Import translation of all fields
        self.create_translation(IMPORT_PATH_5)
        reader, reader_info = self.prepare_export_data(False)
        # The number of elements in the csv file should be the number of
        # records in the recordset - 1, as one record is already fully
        # translated
        num_lines = self.env["product.template"].search_count([])
        self.assertEqual(len(reader_info), num_lines - 1)
