# Copyright 2026 Ross Golder
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import uuid

from odoo import api, fields, models

from . import dav_identity

# Fields whose modification has to reach the device. Kept in sync with
# dav_server.vcard.
PARTNER_MAPPED_FIELDS = {
    "name",
    "parent_id",
    "ref",
    "lang",
    "tz",
    "email",
    "phone",
    "mobile",
    "website",
    "function",
    "title",
    "street",
    "street2",
    "zip",
    "city",
    "state_id",
    "country_id",
    "comment",
    "category_id",
    "type",
    "is_company",
    "image_1920",
    "image_1920_url",
    "company_name",
}


class DavResPartner(models.Model):
    # Not named ``ResPartner``; see models/dav_identity.py for why this model
    # declares its own ``dav_uid`` instead of using a mixin.
    _inherit = ["res.partner"]

    dav_uid = fields.Char(
        string="DAV UID",
        index=True,
        copy=False,
        readonly=True,
        default=lambda self: uuid.uuid4().hex,
        help="Stable identifier used as the DAV UID and as the resource href.",
    )

    def _dav_mapped_fields(self):
        return PARTNER_MAPPED_FIELDS

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        dav_identity.log_changes(records, "create")
        return records

    def write(self, vals):
        relevant = bool(set(vals) & self._dav_mapped_fields())
        result = super().write(vals)
        if relevant:
            dav_identity.log_changes(self, "write")
        return result

    def unlink(self):
        dav_identity.log_changes(self, "unlink")
        return super().unlink()