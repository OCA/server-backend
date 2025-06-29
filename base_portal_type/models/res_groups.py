# Copyright 2023 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

from lxml import etree

from odoo import api, fields, models

from odoo.addons.base.models.res_users import name_boolean_group, name_selection_groups


class ResGroups(models.Model):
    _inherit = "res.groups"

    portal = fields.Boolean("Is Portal Group")

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

        user_type_field_name = name_selection_groups(user_type_groups.ids)
        non_public_attrs = str(
            {
                "readonly": [
                    (
                        user_type_field_name,
                        "not in",
                        [internal_group.id, portal_group.id],
                    )
                ],
            }
        )

        portal_groups = (
            self.env["res.groups"]
            .search(
                [
                    "|",
                    (
                        "category_id",
                        "=",
                        self.env.ref("base_portal_type.category_portal_type").id,
                    ),
                    ("portal", "=", True),
                ]
            )
            .with_context(lang=None)
        )

        # during install/upgrade/uninstall, super()._update_user_groups_view() may return
        # a placeholder view without the field which has name=user_type_field_name added yet.
        # Making sure we received the real view here
        arch_root = arch.xpath("//field[@name='groups_id'][@position='replace']")
        if len(arch_root) and portal_groups:
            # as the original construction of the groups view makes all xml-groups
            # per application invisible, it is 'easier' to create another section for
            # portal users and append the whole section at the bottom of the view.
            # name attribute is given here to easily identify this group element in tests
            portal_group_elem = etree.SubElement(
                arch_root[0],
                "group",
                name="base_portal_type_extension",
                attrs=str(
                    {
                        "readonly": [(user_type_field_name, "!=", portal_group.id)],
                        "invisible": [(user_type_field_name, "!=", portal_group.id)],
                    }
                ),
            )
            for app_id, app_name in portal_groups.mapped("category_id").name_get() + [
                (False, "Other")
            ]:
                portal_groups_in_app = portal_groups.filtered(
                    lambda r: (r.category_id.id or False) == app_id
                )
                if not portal_groups_in_app:
                    continue
                app_group_elem = etree.SubElement(
                    portal_group_elem,
                    "group",
                    string=app_name,
                )
                for group in portal_groups_in_app:
                    field_name = name_boolean_group(group.id)
                    for field_node in arch.xpath("//field[@name='%s']" % field_name):
                        field_node.attrib["attrs"] = non_public_attrs
                    etree.SubElement(
                        app_group_elem,
                        "field",
                        name=field_name,
                        on_change="1",
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
                (
                    kind
                    if app.xml_id != "base_portal_type.category_portal_type"
                    else "boolean"
                ),
                groups,
                category,
            )
            for app, kind, groups, category in super().get_groups_by_application()
        ]
