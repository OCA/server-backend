# Copyright 2026 Ross Golder
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

"""CalDAV / CardDAV endpoints served directly by Odoo.

Layout::

    /dav/                                        service root (discovery)
    /dav/principals/<login>/                     principal properties
    /dav/caldav/<login>/                         calendar home set
    /dav/caldav/<login>/<slug>/                  calendar collection
    /dav/caldav/<login>/<slug>/<uid>.ics         event resource
    /dav/carddav/<login>/                        address book home set
    /dav/carddav/<login>/<slug>/                 address book collection
    /dav/carddav/<login>/<slug>/<uid>.vcf        contact resource

The files-only endpoint at ``/.dav`` is deliberately *not* handled here: it is
owned by the ``bureaucracy`` scanner upload controller, which shares the
``dav.collection`` model with this module.

Access control is delegated to Odoo's record rules. Every request is
authenticated first, then the collection's domain is evaluated with ``user``
bound to that authenticated user and the search runs under their access rights.
A collection's URL therefore never grants more than the user's Odoo rights do.

Every route passes ``readonly=False``. It is ignored by Odoo 17 (which commits
any request that does not raise) but required from 18.0 onwards, where
``auth="none"`` routes are otherwise treated as read-only and a PUT would be
silently rolled back.
"""

import logging
from datetime import datetime, timedelta, timezone
from urllib.parse import quote, unquote, urlparse

import werkzeug
from lxml import etree

from odoo import http
from odoo.http import request

from .. import ical, vcard
from ..multistatus import Multistatus, PropSet, caldav, carddav, dav
from . import auth

_logger = logging.getLogger(__name__)

DAV_METHODS = ["GET", "HEAD", "OPTIONS", "PROPFIND", "REPORT", "PUT", "DELETE"]
WELL_KNOWN_METHODS = ["GET", "HEAD", "OPTIONS", "PROPFIND", "REPORT"]

DAV_COMPLIANCE = "1, 2, 3, calendar-access, addressbook, extended-mkcol"
ALLOW_METHODS = "OPTIONS, GET, HEAD, PROPFIND, REPORT, PUT, DELETE"

NOT_FOUND = 404
METHOD_NOT_ALLOWED = 405
CONFLICT = 409
PRECONDITION_FAILED = 412

# The URL segment differs from dav_type: CalDAV lives under /dav/caldav and
# CardDAV under /dav/carddav. Building hrefs straight from dav_type yields
# URLs the router never matches, so every advertised collection href 404s.
URL_SEGMENTS = {"calendar": "caldav", "addressbook": "carddav"}

XML_CONTENT_TYPE = 'application/xml; charset="utf-8"'
CALENDAR_CONTENT_TYPE = 'text/calendar; charset="utf-8"; component=vevent'
VCARD_CONTENT_TYPE = 'text/vcard; charset="utf-8"'

SUPPORTED_REPORTS = (
    "calendar-multiget",
    "calendar-query",
    "free-busy-query",
    "sync-collection",
    "addressbook-multiget",
    "addressbook-query",
)

# Writes that originate on a device must not fan out Odoo invitation mails or
# chatter entries: the client already knows about its own change.
IMPORT_CONTEXT = {
    "dont_notify": True,
    "mail_notrack": True,
    "no_reset_password": True,
    "tracking_disable": True,
    "mail_create_nolog": True,
    "mail_notify": False,
}

RFC_FORMAT = "%a, %d %b %Y %H:%M:%S GMT"
ICAL_STAMP = "%Y%m%dT%H%M%SZ"
UTC = timezone.utc


class DavController(http.Controller):
    # ------------------------------------------------------------------
    # Routing
    # ------------------------------------------------------------------
    @http.route(
        ["/dav", "/dav/"],
        type="http",
        auth="none",
        csrf=False,
        readonly=False,
        methods=DAV_METHODS,
    )
    def dav_service_root(self, **kwargs):
        return self._handle("root")

    @http.route(
        "/dav/principals/<string:login>",
        type="http",
        auth="none",
        csrf=False,
        readonly=False,
        methods=DAV_METHODS,
    )
    def dav_principal(self, login, **kwargs):
        return self._handle("principal", login=unquote(login))

    @http.route(
        "/dav/caldav/<string:login>",
        type="http",
        auth="none",
        csrf=False,
        readonly=False,
        methods=DAV_METHODS,
    )
    def dav_calendar_home(self, login, **kwargs):
        return self._handle("calendar_home", login=unquote(login))

    @http.route(
        "/dav/caldav/<string:login>/<string:slug>",
        type="http",
        auth="none",
        csrf=False,
        readonly=False,
        methods=DAV_METHODS,
    )
    def dav_calendar_collection(self, login, slug, **kwargs):
        return self._handle(
            "calendar_collection", login=unquote(login), slug=unquote(slug)
        )

    @http.route(
        "/dav/caldav/<string:login>/<string:slug>/<string:resource>",
        type="http",
        auth="none",
        csrf=False,
        readonly=False,
        methods=DAV_METHODS,
    )
    def dav_calendar_resource(self, login, slug, resource, **kwargs):
        return self._handle(
            "calendar_resource",
            login=unquote(login),
            slug=unquote(slug),
            resource=unquote(resource),
        )

    @http.route(
        "/dav/carddav/<string:login>",
        type="http",
        auth="none",
        csrf=False,
        readonly=False,
        methods=DAV_METHODS,
    )
    def dav_addressbook_home(self, login, **kwargs):
        return self._handle("addressbook_home", login=unquote(login))

    @http.route(
        "/dav/carddav/<string:login>/<string:slug>",
        type="http",
        auth="none",
        csrf=False,
        readonly=False,
        methods=DAV_METHODS,
    )
    def dav_addressbook_collection(self, login, slug, **kwargs):
        return self._handle(
            "addressbook_collection", login=unquote(login), slug=unquote(slug)
        )

    @http.route(
        "/dav/carddav/<string:login>/<string:slug>/<string:resource>",
        type="http",
        auth="none",
        csrf=False,
        readonly=False,
        methods=DAV_METHODS,
    )
    def dav_addressbook_resource(self, login, slug, resource, **kwargs):
        return self._handle(
            "addressbook_resource",
            login=unquote(login),
            slug=unquote(slug),
            resource=unquote(resource),
        )

    @http.route(
        ["/.well-known/caldav", "/.well-known/carddav"],
        type="http",
        auth="none",
        csrf=False,
        readonly=False,
        methods=WELL_KNOWN_METHODS,
    )
    def dav_well_known(self, **kwargs):
        """RFC 6764 service discovery.

        ``base_dav`` also answers ``/.well-known/*`` and has been narrowed to
        ``webdav`` only (for the scanner), so exactly one module owns each
        discovery path.
        """
        if request.httprequest.method.upper() in ("PROPFIND", "REPORT"):
            try:
                auth.authenticate()
            except auth.Unauthorized as error:
                return self._unauthorized(error)
        return werkzeug.utils.redirect("/dav/", code=301)

    # ------------------------------------------------------------------
    # Dispatch
    # ------------------------------------------------------------------
    def _handle(self, target, login=None, slug=None, resource=None):
        method = request.httprequest.method.upper()
        if method == "OPTIONS":
            # Answered before authentication: clients probe capabilities
            # unauthenticated while discovering an account.
            return self._options()
        try:
            user = auth.authenticate()
        except auth.Unauthorized as error:
            return self._unauthorized(error)

        if not user.has_group("base.group_user"):
            # Portal users reach the web client but must not enumerate records.
            return self._forbidden("DAV access is restricted to internal users")

        handlers = {
            "root": self._root,
            "principal": self._principal,
            "calendar_home": self._calendar_home,
            "calendar_collection": self._calendar_collection,
            "calendar_resource": self._calendar_resource,
            "addressbook_home": self._addressbook_home,
            "addressbook_collection": self._addressbook_collection,
            "addressbook_resource": self._addressbook_resource,
        }
        return handlers[target](
            method=method, user=user, login=login, slug=slug, resource=resource
        )

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------
    def _root(self, method, user, login, slug, resource):
        hrefs = self._hrefs(login)
        if method in ("GET", "HEAD"):
            return self._text(DAV_COMPLIANCE)
        if method != "PROPFIND":
            return self._method_not_allowed(method)
        props = PropSet()
        props.resourcetype(dav("collection"))
        props.text(dav("displayname"), "Odoo DAV")
        props.hrefs(dav("current-user-principal"), hrefs["principal"])
        props.hrefs(caldav("calendar-home-set"), hrefs["calendar_home"])
        props.hrefs(carddav("addressbook-home-set"), hrefs["addressbook_home"])
        props.children(
            dav("supported-report-set"),
            [
                (dav("supported-report"), {"report": report})
                for report in SUPPORTED_REPORTS
            ],
        )
        document = Multistatus()
        document.add_propstat(document.add_response("/dav/"), props)
        return self._multistatus(document, method)

    def _principal(self, method, user, login, slug, resource):
        hrefs = self._hrefs(login)
        if method in ("GET", "HEAD"):
            return self._text(DAV_COMPLIANCE)
        if method != "PROPFIND":
            return self._method_not_allowed(method)
        props = PropSet()
        props.resourcetype(dav("principal"))
        props.text(dav("displayname"), user.display_name or login)
        props.hrefs(dav("principal-URL"), hrefs["principal"])
        props.hrefs(dav("current-user-principal"), hrefs["principal"])
        props.hrefs(caldav("calendar-home-set"), hrefs["calendar_home"])
        props.hrefs(carddav("addressbook-home-set"), hrefs["addressbook_home"])
        document = Multistatus()
        document.add_propstat(document.add_response(hrefs["principal"]), props)
        return self._multistatus(document, method)

    def _calendar_home(self, method, user, login, slug, resource):
        return self._home(method, user, login, "calendar")

    def _addressbook_home(self, method, user, login, slug, resource):
        return self._home(method, user, login, "addressbook")

    def _home(self, method, user, login, dav_type):
        hrefs = self._hrefs(login)
        home_href = hrefs[f"{dav_type}_home"]
        if method in ("GET", "HEAD"):
            return self._text(DAV_COMPLIANCE)
        if method != "PROPFIND":
            return self._method_not_allowed(method)

        props = PropSet()
        props.resourcetype(dav("collection"))
        props.text(
            dav("displayname"),
            "Calendars" if dav_type == "calendar" else "Address books",
        )
        document = Multistatus()
        document.add_propstat(document.add_response(home_href), props)

        if self._depth() > 0:
            builder = (
                self._calendar_collection_props
                if dav_type == "calendar"
                else self._addressbook_collection_props
            )
            for collection in request.env["dav.collection"]._dav_visible_collections(
                dav_type
            ):
                document.add_propstat(
                    document.add_response(
                        self._collection_href(login, collection, dav_type)
                    ),
                    builder(collection),
                )
        return self._multistatus(document, method)

    # ------------------------------------------------------------------
    # Calendar
    # ------------------------------------------------------------------
    def _calendar_collection(self, method, user, login, slug, resource):
        collection = self._collection("calendar", slug)
        if not collection:
            return self._not_found()
        href = self._collection_href(login, collection, "calendar")

        if method in ("GET", "HEAD"):
            return self._text(DAV_COMPLIANCE)
        if method == "PROPFIND":
            document = Multistatus()
            document.add_propstat(
                document.add_response(href), self._calendar_collection_props(collection)
            )
            if self._depth() > 0:
                self._add_resource_responses(
                    document, collection, self._master_events(collection), login, True
                )
            return self._multistatus(document, method)
        if method == "REPORT":
            return self._calendar_report(collection, login)
        return self._method_not_allowed(method)

    def _calendar_resource(self, method, user, login, slug, resource):
        collection = self._collection("calendar", slug)
        if not collection:
            return self._not_found()
        uid = self._uid_from_resource(resource, ".ics")
        if uid is None:
            return self._not_found()
        event = collection._dav_record_by_uid(uid)
        href = self._resource_href(login, collection, "calendar", resource)

        if method in ("GET", "HEAD"):
            if not event:
                return self._not_found()
            return self._payload(
                ical.event_to_ical(event),
                content_type=CALENDAR_CONTENT_TYPE,
                method=method,
            )
        if method == "PROPFIND":
            document = Multistatus()
            child = document.add_response(href)
            if event:
                document.add_propstat(
                    child, self._resource_props(self._etag(event), calendar=True)
                )
            else:
                document.add_status(child, "HTTP/1.1 404 Not Found")
            return self._multistatus(document, method)
        if method == "PUT":
            return self._put_event(collection, event, uid)
        if method == "DELETE":
            if not event:
                return self._not_found()
            event.with_context(**IMPORT_CONTEXT).unlink()
            return http.Response(status=204)
        return self._method_not_allowed(method)

    def _put_event(self, collection, event, uid):
        payload = request.httprequest.get_data()
        if not payload:
            return http.Response(status=400)
        try:
            values = ical.ical_to_event_values(payload, request.env.user)
        except ical.UnsupportedPayload as error:
            _logger.info(
                "dav_server: rejected PUT of %s: %s", request.httprequest.path, error
            )
            return self._bad_request(str(error))

        is_update = bool(event)
        if is_update and not self._etag_matches(event):
            return self._precondition_failed()

        organizer_email = values.pop("_organizer_email", "")
        values["dav_uid"] = uid
        # Only meaningful on a recurring series, and Odoo rejects it otherwise.
        if not values.get("recurrency"):
            values.pop("recurrence_update", None)

        if is_update:
            event.with_context(**IMPORT_CONTEXT).write(values)
            record = event
        else:
            organiser = self._organiser_user_id(organizer_email)
            values["user_id"] = organiser or request.env.user.id
            record = (
                request.env["calendar.event"]
                .with_context(**IMPORT_CONTEXT)
                .create(values)
            )

        response = http.Response(status=204 if is_update else 201)
        response.headers["ETag"] = self._etag(record)
        return response

    def _organiser_user_id(self, email):
        """Resolve an ORGANIZER address onto an internal user, if any."""
        if not email:
            return None
        partner = (
            request.env["res.partner"].sudo().search([("email", "=", email)], limit=1)
        )
        return partner.user_id.id or None

    def _calendar_report(self, collection, login):
        root = self._xml_body()
        if root is None:
            return self._bad_request("malformed or empty REPORT body")
        name = etree.QName(root).localname
        events = self._master_events(collection)

        if name == "calendar-multiget":
            return self._data_report(
                self._select_by_hrefs(collection, root, events), login, collection, True
            )
        if name == "calendar-query":
            return self._data_report(
                self._filter_events(root, events), login, collection, True
            )
        if name == "sync-collection":
            return self._sync_report(collection, root, login, True)
        if name == "free-busy-query":
            return self._free_busy_report(collection, root, login)
        return self._forbidden(f"unsupported REPORT {name}")

    def _filter_events(self, root, events):
        """Apply the comp-filter / time-range subset real clients send."""
        comp_filter = root.find(f".//{caldav('comp-filter')}")
        if comp_filter is not None and comp_filter.get("name") not in (
            None,
            "VCALENDAR",
        ):
            return events.browse()

        time_range = root.find(f".//{caldav('time-range')}")
        if time_range is None:
            return events
        window = self._time_window(time_range)
        if not window:
            return events
        start, end = window
        return events.filtered(lambda event: event.stop > start and event.start < end)

    def _free_busy_report(self, collection, root, login):
        time_range = root.find(f".//{caldav('time-range')}")
        if time_range is None:
            return self._bad_request("free-busy-query requires a time-range")
        window = self._time_window(time_range)
        if not window:
            return self._bad_request("free-busy-query has an unparsable time-range")
        start, end = window

        busy = self._master_events(collection).filtered(
            lambda event: event.show_as != "free"
            and event.stop > start
            and event.start < end
        )
        lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            f"PRODID:{ical.PRODID}",
            "METHOD:REPLY",
        ]
        for event in busy:
            lines += [
                "BEGIN:VEVENT",
                f"UID:{event.dav_uid}",
                f"DTSTAMP:{_stamp(event.write_date)}",
                f"DTSTART:{_stamp(event.start)}",
                f"DTEND:{_stamp(event.stop)}",
                "END:VEVENT",
            ]
        lines.append("END:VCALENDAR")

        document = Multistatus()
        href = self._collection_href(login, collection, "calendar")
        child = document.add_response(href)
        props = PropSet()
        props.text(caldav("free-busy"), "\r\n".join(lines))
        document.add_propstat(child, props)
        return self._multistatus(document, request.httprequest.method.upper())

    # ------------------------------------------------------------------
    # Address book
    # ------------------------------------------------------------------
    def _addressbook_collection(self, method, user, login, slug, resource):
        collection = self._collection("addressbook", slug)
        if not collection:
            return self._not_found()
        href = self._collection_href(login, collection, "addressbook")
        partners = collection._dav_records()

        if method in ("GET", "HEAD"):
            return self._text(DAV_COMPLIANCE)
        if method == "PROPFIND":
            document = Multistatus()
            document.add_propstat(
                document.add_response(href),
                self._addressbook_collection_props(collection),
            )
            if self._depth() > 0:
                self._add_resource_responses(
                    document, collection, partners, login, False
                )
            return self._multistatus(document, method)
        if method == "REPORT":
            root = self._xml_body()
            if root is None:
                return self._bad_request("malformed or empty REPORT body")
            name = etree.QName(root).localname
            if name == "addressbook-multiget":
                partners = self._select_by_hrefs(collection, root, partners)
            elif name == "addressbook-query":
                pass  # no supported filter subset; return the whole collection
            elif name == "sync-collection":
                return self._sync_report(collection, root, login, False)
            else:
                return self._forbidden(f"unsupported REPORT {name}")
            return self._data_report(partners, login, collection, False)
        return self._method_not_allowed(method)

    def _addressbook_resource(self, method, user, login, slug, resource):
        collection = self._collection("addressbook", slug)
        if not collection:
            return self._not_found()
        uid = self._uid_from_resource(resource, ".vcf")
        if uid is None:
            return self._not_found()
        partner = collection._dav_record_by_uid(uid)
        href = self._resource_href(login, collection, "addressbook", resource)

        if method in ("GET", "HEAD"):
            if not partner:
                return self._not_found()
            return self._payload(
                vcard.partner_to_vcard(partner),
                content_type=VCARD_CONTENT_TYPE,
                method=method,
            )
        if method == "PROPFIND":
            document = Multistatus()
            child = document.add_response(href)
            if partner:
                document.add_propstat(
                    child, self._resource_props(self._etag(partner), calendar=False)
                )
            else:
                document.add_status(child, "HTTP/1.1 404 Not Found")
            return self._multistatus(document, method)
        if method == "PUT":
            return self._put_partner(collection, partner, uid)
        if method == "DELETE":
            if not partner:
                return self._not_found()
            partner.with_context(**IMPORT_CONTEXT).unlink()
            return http.Response(status=204)
        return self._method_not_allowed(method)

    def _put_partner(self, collection, partner, uid):
        payload = request.httprequest.get_data()
        if not payload:
            return http.Response(status=400)
        try:
            values = vcard.vcard_to_partner_values(payload, request.env.user)
        except vcard.UnsupportedPayload as error:
            return self._bad_request(str(error))

        is_update = bool(partner)
        if is_update and not self._etag_matches(partner):
            return self._precondition_failed()
        values["dav_uid"] = uid

        if is_update:
            partner.with_context(**IMPORT_CONTEXT).write(values)
        else:
            partner = (
                request.env["res.partner"].with_context(**IMPORT_CONTEXT).create(values)
            )
        response = http.Response(status=204 if is_update else 201)
        response.headers["ETag"] = self._etag(partner)
        return response

    # ------------------------------------------------------------------
    # REPORT helpers
    # ------------------------------------------------------------------
    def _select_by_hrefs(self, collection, root, candidates):
        """Resolve the hrefs a multiget asked for against readable records."""
        wanted = {
            self._uid_from_href(str(element.text or ""))
            for element in root.iter(dav("href"))
        }
        wanted.discard(None)
        return candidates.filtered(
            lambda record: (record.dav_uid or str(record.id)) in wanted
        )

    def _data_report(self, records, login, collection, calendar):
        payload = ical.event_to_ical if calendar else vcard.partner_to_vcard
        data_qname = caldav("calendar-data") if calendar else carddav("address-data")
        content_type = CALENDAR_CONTENT_TYPE if calendar else VCARD_CONTENT_TYPE
        builder = self._event_href if calendar else self._contact_href
        document = Multistatus()
        for record in records:
            child = document.add_response(builder(login, collection, record))
            props = self._resource_props(self._etag(record), calendar=calendar)
            props.text(data_qname, _as_text(payload(record)))
            props.text(dav("getcontenttype"), content_type)
            document.add_propstat(child, props)
        return self._multistatus(document, request.httprequest.method.upper())

    def _sync_report(self, collection, root, login, calendar):
        changes = request.env["dav.sync.change"].sudo()
        element = root.find(dav("sync-token"))
        supplied = (element.text or "").strip() if element is not None else ""
        change_id = changes.parse_token(collection, supplied)

        if supplied and (
            change_id is None or not changes.token_is_usable(collection, change_id)
        ):
            _logger.info(
                "dav_server: stale sync-token for collection %s: %r (parsed=%r, "
                "valid token is %s)",
                collection.id,
                supplied,
                change_id,
                changes.token_for(collection),
            )
            # RFC 6578: tell the client its token is stale so it re-lists.
            response = http.Response(status=CONFLICT)
            response.headers["DAV"] = DAV_COMPLIANCE
            response.headers["valid-sync-token"] = changes.token_for(collection)
            return response

        deleted_hrefs = []
        if not supplied:
            records = (
                self._master_events(collection)
                if calendar
                else collection._dav_records()
            )
        else:
            rows = changes.changes_since(collection, change_id)
            records, deleted = collection._dav_records_changed_since(rows)
            if calendar:
                records = records.filtered(lambda event: not event.recurrence_id)
            deleted_hrefs = [
                self._resource_href(
                    login,
                    collection,
                    "calendar" if calendar else "addressbook",
                    f"{row.dav_uid}.{self._suffix(calendar)}",
                )
                for row in rows
                if row.action == "unlink" and row.res_id in deleted
            ]

        payload = ical.event_to_ical if calendar else vcard.partner_to_vcard
        data_qname = caldav("calendar-data") if calendar else carddav("address-data")
        builder = self._event_href if calendar else self._contact_href

        document = Multistatus()
        for record in records:
            child = document.add_response(builder(login, collection, record))
            props = self._resource_props(self._etag(record), calendar=calendar)
            props.text(data_qname, _as_text(payload(record)))
            document.add_propstat(child, props)
        for href in deleted_hrefs:
            document.add_status(document.add_response(href), "HTTP/1.1 404 Not Found")

        response = self._multistatus(document, request.httprequest.method.upper())
        response.headers["valid-sync-token"] = changes.token_for(collection)
        return response

    def _add_resource_responses(self, document, collection, records, login, calendar):
        for record in records:
            child = document.add_response(
                self._event_href(login, collection, record)
                if calendar
                else self._contact_href(login, collection, record)
            )
            document.add_propstat(
                child, self._resource_props(self._etag(record), calendar=calendar)
            )

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------
    def _calendar_collection_props(self, collection):
        changes = request.env["dav.sync.change"].sudo()
        props = PropSet()
        props.resourcetype(dav("collection"), caldav("calendar"))
        props.text(dav("displayname"), collection.name)
        props.text(dav("getcontenttype"), "text/calendar; charset=utf-8")
        props.text(dav("getctag"), self._ctag(collection))
        props.text(dav("sync-token"), changes.token_for(collection))
        props.children(
            caldav("supported-calendar-component-set"),
            [
                (caldav("comp"), {"name": name})
                for name in ("VEVENT", "VTODO", "VJOURNAL")
            ],
        )
        props.children(
            dav("current-user-privilege-set"),
            [
                (dav("privilege"), {})
                for _name in (
                    "read",
                    "read-current-user-privilege-set",
                    "write",
                    "write-properties",
                    "write-content",
                    "bind",
                    "unbind",
                )
            ],
        )
        return props

    def _addressbook_collection_props(self, collection):
        changes = request.env["dav.sync.change"].sudo()
        props = PropSet()
        props.resourcetype(dav("collection"), carddav("addressbook"))
        props.text(dav("displayname"), collection.name)
        props.text(dav("getcontenttype"), VCARD_CONTENT_TYPE)
        props.text(dav("getctag"), self._ctag(collection))
        props.text(dav("sync-token"), changes.token_for(collection))
        props.children(
            carddav("supported-address-data"),
            [
                (
                    carddav("address-data-type"),
                    {"content-type": "text/vcard", "version": version},
                )
                for version in ("3.0", "4.0")
            ],
        )
        return props

    def _resource_props(self, etag, calendar=True):
        props = PropSet()
        props.resourcetype()
        props.text(dav("getetag"), etag)
        props.text(
            dav("getcontenttype"),
            CALENDAR_CONTENT_TYPE if calendar else VCARD_CONTENT_TYPE,
        )
        return props

    def _ctag(self, collection):
        changes = request.env["dav.sync.change"].sudo()
        return f"{collection.id}-{changes.current_ctag(collection)}"

    # ------------------------------------------------------------------
    # Responses
    # ------------------------------------------------------------------
    def _multistatus(self, document, method):
        return self._payload(
            document.tobytes(),
            content_type=XML_CONTENT_TYPE,
            status=207,
            method=method,
        )

    def _payload(self, body, content_type, status=200, method=None):
        data = body.encode("utf-8") if isinstance(body, str) else body
        if method == "HEAD":
            data = b""
        response = http.Response(data, status=status)
        response.headers["Content-Type"] = content_type
        response.headers["DAV"] = DAV_COMPLIANCE
        return response

    def _text(self, body):
        return self._payload(body, content_type="text/plain")

    def _options(self):
        response = http.Response(status=200)
        response.headers["DAV"] = DAV_COMPLIANCE
        response.headers["Allow"] = ALLOW_METHODS
        response.headers["MS-Author-Via"] = "DAV"
        response.headers["Content-Length"] = "0"
        return response

    def _unauthorized(self, error):
        _logger.info("dav_server: 401 %s (%s)", request.httprequest.path, error)
        response = http.Response(status=401)
        response.headers[
            "WWW-Authenticate"
        ] = f'Basic realm="{auth.REALM}", charset="UTF-8"'
        response.headers["DAV"] = DAV_COMPLIANCE
        return response

    def _forbidden(self, message):
        return http.Response(message, status=403)

    def _not_found(self):
        return http.Response(status=404)

    def _bad_request(self, message):
        return http.Response(message, status=400)

    def _precondition_failed(self):
        return http.Response(status=412)

    def _method_not_allowed(self, method):
        _logger.debug(
            "dav_server: %s not allowed on %s", method, request.httprequest.path
        )
        response = http.Response(status=METHOD_NOT_ALLOWED)
        response.headers["Allow"] = ALLOW_METHODS
        return response

    # ------------------------------------------------------------------
    # Records, hrefs, etags
    # ------------------------------------------------------------------
    def _collection(self, dav_type, slug):
        collection = request.env["dav.collection"]._dav_find_by_slug(slug, dav_type)
        if not collection or not collection._dav_user_can_read():
            return None
        return collection

    def _master_events(self, collection):
        """Recurring events are exported as one VEVENT with an RRULE."""
        return collection._dav_records().filtered(lambda event: not event.recurrence_id)

    def _hrefs(self, login):
        segment = quote(login, safe="")
        return {
            "principal": f"/dav/principals/{segment}/",
            "calendar_home": f"/dav/caldav/{segment}/",
            "addressbook_home": f"/dav/carddav/{segment}/",
        }

    def _collection_href(self, login, collection, dav_type):
        segment = quote(login, safe="")
        prefix = URL_SEGMENTS[dav_type]
        return f"/dav/{prefix}/{segment}/{collection.dav_slug}/"

    def _event_href(self, login, collection, event):
        return self._resource_href(
            login, collection, "calendar", f"{event.dav_uid or event.id}.ics"
        )

    def _contact_href(self, login, collection, partner):
        return self._resource_href(
            login, collection, "addressbook", f"{partner.dav_uid or partner.id}.vcf"
        )

    def _resource_href(self, login, collection, dav_type, resource):
        return f"{self._collection_href(login, collection, dav_type)}{resource}"

    def _suffix(self, calendar):
        return "ics" if calendar else "vcf"

    def _uid_from_resource(self, resource, suffix):
        if not resource.endswith(suffix):
            return None
        return resource[: -len(suffix)] or None

    def _uid_from_href(self, href):
        name = urlparse(href).path.rsplit("/", 1)[-1]
        for suffix in (".ics", ".vcf"):
            if name.endswith(suffix):
                return name[: -len(suffix)] or None
        return None

    def _etag(self, record):
        stamp = int(record.write_date.timestamp()) if record.write_date else 0
        return f'"{record._name}-{record.id}-{stamp}"'

    def _etag_matches(self, record):
        supplied = request.httprequest.headers.get("If-Match")
        if not supplied:
            return True
        candidates = {token.strip() for token in supplied.split(",")}
        return "*" in candidates or self._etag(record) in candidates

    def _depth(self):
        raw = (request.httprequest.headers.get("Depth") or "0").strip()
        if raw.lower() == "infinity":
            return 2
        try:
            return max(0, min(2, int(raw)))
        except ValueError:
            return 0

    def _xml_body(self):
        raw = request.httprequest.get_data()
        if not raw:
            return None
        try:
            return etree.fromstring(raw)
        except etree.XMLSyntaxError as error:
            _logger.warning("dav_server: malformed XML body: %s", error)
            return None

    def _time_window(self, time_range):
        start = _parse_ical_time(time_range.get("start"))
        end = _parse_ical_time(time_range.get("end"))
        if not start or not end:
            return None
        # Odoo stores UTC and returns naive datetimes; widen by a second on each
        # side so events touching the boundary are still returned.
        return start - timedelta(seconds=1), end + timedelta(seconds=1)


def _as_text(value):
    """Serialisers are inconsistent: icalendar returns bytes, vobject str."""
    return value.decode("utf-8") if isinstance(value, bytes) else value


def _parse_ical_time(value):
    if not value:
        return None
    text = value.strip()
    for pattern in ("%Y%m%dT%H%M%SZ", "%Y%m%dT%H%M%S", "%Y%m%d"):
        try:
            return datetime.strptime(text, pattern)
        except ValueError:
            continue
    _logger.info("dav_server: unparsable iCal time %r", text)
    return None


def _stamp(value):
    if not value:
        return datetime.now(UTC).strftime(ICAL_STAMP)
    return value.strftime(ICAL_STAMP)
