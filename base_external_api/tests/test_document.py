# Copyright (C) 2022 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo.tests import common


class TestDocument(common.TransactionCase):
    def setUp(self):
        super().setUp()
        APIDoc = self.env["apicli.document"]
        View = self.env["ir.ui.view"]
        self.template = View.create(
            {
                "name": "Partner Message",
                "type": "qweb",
                "arch": """
                <t t-name="dummy">
                  <root>
                    <t t-foreach="doc" t-as="rec">
                      <partner>
                        <t t-out="rec.display_name" />
                      </partner>
                    </t>
                  </root>
                </t>
                """,
            }
        )
        self.doc = APIDoc.create(
            {
                "name": "Contacts Test Template",
                "model_id": self.env.ref("base.model_res_partner").id,
                "file_type": "xml",
                "endpoint": "company/{{o.ids}}/create",
                "template_view_id": self.template.id,
            }
        )

    def test_render(self):
        partners = self.env["res.partner"].search([], limit=3)
        self.doc.render(partners)  # TODO: complete tests
