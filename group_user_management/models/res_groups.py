#  Copyright (c) 2024- Le Filament (https://le-filament.com)
#  License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from lxml import etree

from odoo import api, models

from odoo.addons.base.models.res_users import name_selection_groups


class ResGroups(models.Model):
    _inherit = "res.groups"

    @api.model
    def _update_user_groups_view(self):
        """
        Modify the view with xmlid ``base.user_groups_view``, which inherits
        the user form view, and introduces the reified group fields.
        """
        res = super()._update_user_groups_view()
        view = self.env.ref("base.user_groups_view")
        arch = etree.fromstring(view.arch)

        modified = False

        # Get xpath to add group_erp_manager to Admin category
        admin_categories = [
            category
            for category in self.get_groups_by_application()
            if category[0].xml_id
            == "base.module_category_administration_administration"
        ]
        for _app, _kind, gs, _category_name in admin_categories:
            field_name = name_selection_groups(gs.ids)
            xpath_expr = "//group[field[@name='%s']]" % field_name
            for group in arch.xpath(xpath_expr):
                group.attrib["groups"] = "base.group_erp_manager"
                modified = True

        # Only rewrite view if changes were made
        if modified:
            view_context = dict(view._context, lang=None)
            view_context.pop("install_filename", None)
            view.with_context(**view_context).write(
                {"arch": etree.tostring(arch, pretty_print=True, encoding="unicode")}
            )

        return res
