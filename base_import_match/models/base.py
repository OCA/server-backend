# Copyright 2017 Jairo Llopis <jairo.llopis@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging
from collections import defaultdict

import psycopg2

import odoo
from odoo import _, api, models, tools
from odoo.exceptions import UserError
from odoo.models import (
    convert_pgerror_constraint,
    convert_pgerror_not_null,
    convert_pgerror_unique,
    fix_import_export_id_paths,
)
from odoo.tools.lru import LRU

_logger = logging.getLogger(__name__)

PGERROR_TO_OE = defaultdict(  # shape of mapped converters
    lambda: (lambda model, fvg, info, pgerror: {"message": tools.ustr(pgerror)}),
    {
        "23502": convert_pgerror_not_null,
        "23505": convert_pgerror_unique,
        "23514": convert_pgerror_constraint,
    },
)


class Base(models.AbstractModel):
    _inherit = "base"

    @api.model
    def load(self, fields, data):
        if self.env["base_import.match"]._usable_rules(self._name, fields):
            self.env.flush_all()

            # determine values of mode, current_module and noupdate
            mode = self._context.get("mode", "init")
            current_module = self._context.get("module", "__import__")
            noupdate = self._context.get("noupdate", False)
            # add current module in context for the conversion of xml ids
            self = self.with_context(_import_current_module=current_module)

            cr = self._cr
            sp = cr.savepoint(flush=False)

            fields = [fix_import_export_id_paths(f) for f in fields]
            fg = self.fields_get()

            ids = []
            messages = []

            # list of (xid, vals, info) for records to be created in batch
            batch = []
            batch_xml_ids = set()
            # models in which we may have created / modified data, therefore might
            # require flushing in order to name_search: the root model and any
            # o2m
            creatable_models = {self._name}
            for field_path in fields:
                if field_path[0] in (None, "id", ".id"):
                    continue
                model_fields = self._fields
                if isinstance(model_fields[field_path[0]], odoo.fields.Many2one):
                    # this only applies for toplevel m2o (?) fields
                    if field_path[0] in (
                        self.env.context.get("name_create_enabled_fieds") or {}
                    ):
                        creatable_models.add(model_fields[field_path[0]].comodel_name)
                for field_name in field_path:
                    if field_name in (None, "id", ".id"):
                        break

                    if isinstance(model_fields[field_name], odoo.fields.One2many):
                        comodel = model_fields[field_name].comodel_name
                        creatable_models.add(comodel)
                        model_fields = self.env[comodel]._fields

            def flush(*, xml_id=None, model=None):
                if not batch:
                    return

                assert not (
                    xml_id and model
                ), "flush can specify *either* an external id or a model, not both"

                if xml_id and xml_id not in batch_xml_ids:
                    if xml_id not in self.env:
                        return
                if model and model not in creatable_models:
                    return

                data_list = [
                    dict(xml_id=xid, values=vals, info=info, noupdate=noupdate)
                    for xid, vals, info in batch
                ]
                batch.clear()
                batch_xml_ids.clear()

                # try to create in batch
                try:
                    with cr.savepoint():
                        recs = self._load_records(data_list, mode == "update")
                        ids.extend(recs.ids)
                    return
                except psycopg2.InternalError as e:
                    if not any(message["type"] == "error" for message in messages):
                        info = data_list[0]["info"]
                        messages.append(
                            dict(
                                info,
                                type="error",
                                message=_("Unknown database error: '%s'", e),
                            )
                        )
                    return
                except Exception:
                    pass

                errors = 0
                # try again, this time record by record
                for i, rec_data in enumerate(data_list, 1):
                    try:
                        with cr.savepoint():
                            rec = self._load_records([rec_data], mode == "update")
                            ids.append(rec.id)
                    except psycopg2.Warning as e:
                        info = rec_data["info"]
                        messages.append(dict(info, type="warning", message=str(e)))
                    except psycopg2.Error as e:
                        info = rec_data["info"]
                        messages.append(
                            dict(
                                info,
                                type="error",
                                **PGERROR_TO_OE[e.pgcode](self, fg, info, e),
                            )
                        )
                        # Failed to write, log to messages, rollback savepoint (to
                        # avoid broken transaction) and keep going
                        errors += 1
                    except UserError as e:
                        info = rec_data["info"]
                        messages.append(dict(info, type="error", message=str(e)))
                        errors += 1
                    except Exception as e:
                        _logger.debug("Error while loading record", exc_info=True)
                        info = rec_data["info"]
                        message = _("Unknown error during import:") + " {}: {}".format(
                            type(e),
                            e,
                        )
                        moreinfo = _("Resolve other errors first")
                        messages.append(
                            dict(info, type="error", message=message, moreinfo=moreinfo)
                        )
                        # Failed for some reason, perhaps due to invalid data supplied,
                        # rollback savepoint and keep going
                        errors += 1
                    if errors >= 10 and (errors >= i / 10):
                        messages.append(
                            {
                                "type": "warning",
                                "message": _(
                                    "Found more than 10 errors and more "
                                    "than one error per 10 records, "
                                    "interrupted to avoid showing too many errors."
                                ),
                            }
                        )
                        break

            # make 'flush' available to the methods below, in the case where XMLID
            # resolution fails, for instance
            flush_recordset = self.with_context(
                import_flush=flush, import_cache=LRU(1024)
            )

            # TODO: break load's API instead of smuggling via context?
            limit = self._context.get("_import_limit")
            if limit is None:
                limit = float("inf")
            extracted = flush_recordset._extract_records(
                fields, data, log=messages.append, limit=limit
            )

            converted = flush_recordset._convert_records(extracted, log=messages.append)

            info = {"rows": {"to": -1}}
            # Needed to match with converted data field names
            clean_fields = [f[0] for f in fields]
            for id, xid, record, info in converted:
                row = dict(zip(clean_fields, data[info["record"]]))
                match = self
                if self.env.context.get("import_file") and self.env.context.get(
                    "import_skip_records"
                ):
                    if any(
                        [
                            record.get(field) is None
                            for field in self.env.context["import_skip_records"]
                        ]
                    ):
                        continue
                if xid:
                    xid = xid if "." in xid else f"{current_module}.{xid}"
                    batch_xml_ids.add(xid)
                elif id:
                    record["id"] = id
                else:
                    # Store records that match a combination
                    match = self.env["base_import.match"]._match_find(self, record, row)
                # Give a valid XMLID to this row if a match was found
                # To generate externals IDS.

                # 123A47
                match.export_data(clean_fields)
                ext_id = match.get_external_id()
                record["id"] = ext_id[match.id] if match else row.get("id", "")
                batch.append((xid, record, info))

            flush()
            if any(message["type"] == "error" for message in messages):
                sp.rollback()
                ids = False
                # cancel all changes done to the registry/ormcache
                self.pool.reset_changes()
            sp.close(rollback=False)

            nextrow = info["rows"]["to"] + 1
            if nextrow < limit:
                nextrow = 0
            return {
                "ids": ids,
                "messages": messages,
                "nextrow": nextrow,
            }
        # Normal method handles the rest of the job
        return super().load(fields, data)

