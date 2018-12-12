# Copyright 2019 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import fields, models


class DavCollectionFieldMapping(models.Model):
    _name = 'dav.collection.field_mapping'
    _description = 'A field mapping for a WebDAV collection'

    collection_id = fields.Many2one(
        'dav.collection', required=True, ondelete='cascade',
    )
    name = fields.Char(required=True)
    field_id = fields.Many2one('ir.model.fields', required=True)
