# © 2015 Therp BV <http://therp.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import exceptions
from odoo.tests.common import TransactionCase


class TestBaseSuspendSecurity(TransactionCase):
    def test_base_suspend_security(self):
        user_id = self.env.ref('base.user_demo').id
        other_company = self.env['res.company'].create({
            'name': 'other company',
            # without this, a partner is created and mail's constraint on
            # notify_email kicks in
            'partner_id': self.env.ref('base.partner_demo').id,
        })
        # be sure what we try is forbidden
        with self.assertRaises(exceptions.AccessError):
            self.env.ref('base.user_root').sudo(user_id).name = 'test'
        with self.assertRaises(exceptions.AccessError):
            other_company.sudo(user_id).name = 'test'
        # this tests ir.model.access
        self.env.ref('base.user_root').sudo(user_id).suspend_security().write({
            'name': 'test'})
        self.assertEqual(self.env.ref('base.user_root').name, 'test')
        self.assertEqual(self.env.ref('base.user_root').write_uid.id, user_id)
        # this tests ir.rule
        other_company.sudo(user_id).suspend_security().write({'name': 'test'})
        self.assertEqual(other_company.name, 'test')
        self.assertEqual(other_company.write_uid.id, user_id)
        # this tests if _normalize_args conversion works
        self.env['res.users'].browse(
            self.env['res.users'].suspend_security().env.uid)

    def test_suspend_security_on_search(self):
        user_without_access = self.env["res.users"].create(
            dict(
                name="Testing Suspend Security",
                login="nogroups",
                email="nogroups@suspendsecurity.com",
                groups_id=[(5,)],
            )
        )
        model = self.env["ir.config_parameter"]
        # the search is forbidden
        with self.assertRaises(exceptions.AccessError):
            model.sudo(user_without_access).search([])
        # this tests the search
            model.sudo(user_without_access).suspend_security().search([])
