# Copyright 2023 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)


from lxml import etree

from odoo import api, models

from odoo.addons.base.models.res_users import name_boolean_group, name_selection_groups


class ResGroups(models.Model):
    _inherit = "res.groups"

    @api.model
    def _update_user_groups_view(self):
        result = super()._update_user_groups_view()
        view = self.env.ref("base.user_groups_view")
        arch = etree.fromstring(view.arch)
        user_type_groups = [
            groups
            for app, kind, groups, category in self.get_groups_by_application()
            if app.xml_id == "base.module_category_user_type"
        ][0]
        portal_group = self.env.ref("base.group_portal")
        internal_group = self.env.ref("base.group_user")
        portal_groups = (
            self.env["res.groups"]
            .with_context(lang=None)
            .search(
                [
                    (
                        "category_id",
                        "=",
                        self.env.ref("base_portal_type.category_portal_type").id,
                    ),
                ]
            )
        )
        user_type_field = name_selection_groups(user_type_groups.ids)
        for node in arch.xpath("//group/field[@name='%s']" % user_type_field):
            for group in portal_groups:
                field_name = name_boolean_group(group.id)
                for field_node in arch.xpath("//field[@name='%s']" % field_name):
                    field_node.attrib["attrs"] = str(
                        {
                            "readonly": [
                                (
                                    user_type_field,
                                    "not in",
                                    (portal_group + internal_group).ids,
                                )
                            ],
                        }
                    )
                node.addnext(
                    etree.Element(
                        "field",
                        {
                            "name": field_name,
                            "on_change": "1",
                            "attrs": str(
                                {
                                    "invisible": [
                                        (user_type_field, "!=", portal_group.id),
                                    ],
                                }
                            ),
                        },
                    )
                )
        view_context = dict(self.env.context, lang=None)
        view_context.pop("install_filename", None)
        # pylint: disable=context-overridden
        view.with_context(view_context).write(
            {"arch": etree.tostring(arch, pretty_print=True, encoding="unicode")}
        )
        return result

    @api.model
    def get_groups_by_application(self):
        return [
            (
                app,
                kind
                if app.xml_id != "base_portal_type.category_portal_type"
                else "boolean",
                groups,
                category,
            )
            for app, kind, groups, category in super().get_groups_by_application()
        ]
