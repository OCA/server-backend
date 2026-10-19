# Copyright 2026 Ross Golder
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

"""End-to-end checks against the real HTTP stack.

Exercises the verbs a phone or Thunderbird actually sends: HTTP Basic auth,
PROPFIND with a Depth header, REPORT with a sync-token, PUT with If-Match, and
DELETE. ``HttpCase.url_open`` cannot issue these verbs, so the requests go
through ``self.opener`` (a ``requests.Session``) directly.
"""

import base64
from datetime import datetime
from urllib.parse import quote

from lxml import etree

from odoo.tests import HttpCase, tagged
from odoo.tools import mute_logger

from ..multistatus import CALDAV_NS, CARDDAV_NS, DAV_NS

NS = {"D": DAV_NS, "C": CALDAV_NS, "A": CARDDAV_NS}

PROPFIND_ALLPROP = (
    '<?xml version="1.0" encoding="utf-8"?>'
    '<D:propfind xmlns:D="DAV:"><D:allprop/></D:propfind>'
)
XML_CONTENT_TYPE = 'application/xml; charset="utf-8"'


# NB: @mute_logger must NOT be used as a class decorator here. Its __call__
# wraps its argument in a plain function, so decorating a TestCase class
# replaces the class object; unittest's loadTestsFromModule then collects
# nothing at all and the whole class is skipped without any error being logged.
# It is applied per-method below, on the tests that deliberately provoke a
# 401/403/404 response.
@tagged("post_install", "-at_install")
class TestDavProtocol(HttpCase):
    PASSWORD = "dav-test-password-1"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = cls.env["res.users"].create(
            {
                "name": "Ross Golder",
                "login": "dav-http-tester",
                "email": "dav.http@example.com",
                "password": cls.PASSWORD,
                "tz": "Asia/Bangkok",
            }
        )
        cls.partner = cls.env["res.partner"].create(
            {"name": "Household", "email": "household@example.com"}
        )
        cls.calendar = cls.env["dav.collection"].create(
            {
                "name": "Ross Calendar",
                "dav_type": "calendar",
                "model_id": cls.env["ir.model"]._get("calendar.event").id,
                "domain": "[('user_id', '=', %d)]" % cls.user.id,
            }
        )
        cls.addressbook = cls.env["dav.collection"].create(
            {
                "name": "Family Contacts",
                "dav_type": "addressbook",
                "model_id": cls.env["ir.model"]._get("res.partner").id,
                "domain": "[('id', '=', %d)]" % cls.partner.id,
            }
        )

    # ==================================================================
    # Authentication
    # ==================================================================
    @mute_logger("dav_server")
    def test_unauthenticated_request_is_challenged(self):
        response = self._dav_request("PROPFIND", "/dav/", data=PROPFIND_ALLPROP)
        self.assertEqual(response.status_code, 401)
        self.assertIn("Basic", response.headers["WWW-Authenticate"])
        self.assertIn("calendar-access", response.headers["DAV"])

    @mute_logger("dav_server")
    def test_wrong_password_is_rejected(self):
        response = self._dav_request(
            "PROPFIND",
            "/dav/",
            data=PROPFIND_ALLPROP,
            headers=self._auth(self.user.login, "not-the-password"),
        )
        self.assertEqual(response.status_code, 401)

    @mute_logger("dav_server")
    @mute_logger("odoo.http")
    @mute_logger("odoo.addons.auth_oauth.models.res_users")
    def test_wrong_password_with_auth_oauth_installed(self):
        """A wrong password must stay a 401 even with auth_oauth overriding.

        auth_oauth overrides _check_credentials and reads env['interactive']
        from the wsgienv it is handed. Passing a bare WSGI environ through
        makes that lookup raise KeyError, which Odoo reports as a 500 -- so
        DAVx5 and Thunderbird see a server error instead of an auth challenge
        and cannot recover by re-prompting.
        """
        overridden = type(
            self.env["res.users"]
        )._check_credentials.__module__.startswith("odoo.addons.auth_oauth")
        if not overridden:
            self.skipTest("auth_oauth does not override _check_credentials")
        response = self._dav_request(
            "PROPFIND",
            "/dav/",
            data=PROPFIND_ALLPROP,
            headers=self._auth(self.user.login, "not-the-password"),
        )
        self.assertEqual(response.status_code, 401)
        self.assertIn("Basic", response.headers["WWW-Authenticate"])

    def test_options_advertises_dav_compliance(self):
        response = self._dav_request("OPTIONS", "/dav/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("calendar-access", response.headers["DAV"])
        self.assertIn("PROPFIND", response.headers["Allow"])

    def test_portal_user_is_refused(self):
        """Portal users reach the web client but must not enumerate records."""
        portal = self.env["res.users"].create(
            {
                "name": "Portal",
                "login": "dav-protocol-portal",
                "email": "portal.protocol@example.com",
                "password": self.PASSWORD,
                "groups_id": [(6, 0, [self.env.ref("base.group_portal").id])],
            }
        )
        self.assertFalse(portal.has_group("base.group_user"))
        response = self._dav_request(
            "PROPFIND",
            self._hrefs()["calendar_home"],
            data=PROPFIND_ALLPROP,
            headers=self._auth(portal.login, self.PASSWORD),
            depth=0,
        )
        self.assertEqual(response.status_code, 403)

    def test_well_known_caldav_redirects_to_service_root(self):
        response = self._dav_request("GET", "/.well-known/caldav")
        self.assertIn(response.status_code, (301, 302))
        self.assertTrue(response.headers["Location"].endswith("/dav/"))

    def test_well_known_carddav_redirects_to_service_root(self):
        response = self._dav_request("GET", "/.well-known/carddav")
        self.assertIn(response.status_code, (301, 302))
        self.assertTrue(response.headers["Location"].endswith("/dav/"))

    def test_well_known_webdav_still_points_at_the_files_endpoint(self):
        """The scanner's discovery path must keep working."""
        response = self._dav_request("GET", "/.well-known/webdav")
        self.assertIn(response.status_code, (301, 302))
        self.assertTrue(response.headers["Location"].endswith("/.dav"))

    # ==================================================================
    # Discovery
    # ==================================================================
    def test_principal_advertises_both_home_sets(self):
        document = self._propfind(self._principal_href(), depth=0)
        self.assertEqual(
            _text(document, "//C:calendar-home-set/D:href"),
            self._hrefs()["calendar_home"],
        )
        self.assertEqual(
            _text(document, "//A:addressbook-home-set/D:href"),
            self._hrefs()["addressbook_home"],
        )

    def test_calendar_home_lists_collections(self):
        document = self._propfind(self._hrefs()["calendar_home"], depth=1)
        hrefs = _hrefs_of(document)
        self.assertIn(self._collection_href(self.calendar, "calendar"), hrefs)

    def test_calendar_collection_advertises_sync_metadata(self):
        href = self._collection_href(self.calendar, "calendar")
        document = self._propfind(href, depth=0)
        self.assertTrue(_text(document, "//D:sync-token"))
        self.assertTrue(_text(document, "//D:getctag"))
        components = document.xpath(
            "//C:supported-calendar-component-set/C:comp", namespaces=NS
        )
        self.assertEqual(
            {element.get("name") for element in components},
            {"VEVENT", "VTODO", "VJOURNAL"},
        )

    def test_addressbook_collection_advertises_vcard_versions(self):
        href = self._collection_href(self.addressbook, "addressbook")
        document = self._propfind(href, depth=0)
        types = document.xpath(
            "//A:supported-address-data/A:address-data-type", namespaces=NS
        )
        self.assertEqual({element.get("version") for element in types}, {"3.0", "4.0"})

    # ==================================================================
    # Read
    # ==================================================================
    def test_propfind_depth_one_lists_events(self):
        event = self._event()
        document = self._propfind(
            self._collection_href(self.calendar, "calendar"), depth=1
        )
        hrefs = _hrefs_of(document)
        self.assertIn(self._uid_href(self.calendar, "calendar", event.dav_uid), hrefs)

    def test_propfind_depth_one_hides_other_users_events(self):
        other = self.env["res.users"].create(
            {
                "name": "Someone Else",
                "login": "dav-other-tester",
                "email": "other@example.com",
                "password": self.PASSWORD,
            }
        )
        hidden = self.env["calendar.event"].create(
            {
                "name": "Not Yours",
                "start": "2026-05-05 09:00:00",
                "stop": "2026-05-05 10:00:00",
                "user_id": other.id,
            }
        )
        document = self._propfind(
            self._collection_href(self.calendar, "calendar"), depth=1
        )
        hrefs = _hrefs_of(document)
        self.assertNotIn(
            self._uid_href(self.calendar, "calendar", hidden.dav_uid), hrefs
        )

    def test_get_event_returns_ics(self):
        event = self._event()
        href = self._uid_href(self.calendar, "calendar", event.dav_uid)
        response = self._dav_request("GET", href, headers=self._auth())
        self.assertEqual(response.status_code, 200)
        body = response.text
        self.assertIn("BEGIN:VCALENDAR", body)
        self.assertIn(f"UID:{event.dav_uid}", body)
        self.assertIn("SUMMARY:HTTP Test Event", body)

    def test_get_unknown_event_is_404(self):
        href = self._collection_href(self.calendar, "calendar") + "no-such-uid.ics"
        response = self._dav_request("GET", href, headers=self._auth())
        self.assertEqual(response.status_code, 404)

    def test_propfind_on_unknown_collection_is_404(self):
        response = self._dav_request(
            "PROPFIND",
            self._collection_href_by_slug(self.calendar, "calendar", "no-such-slug"),
            data=PROPFIND_ALLPROP,
            headers=self._auth(),
            depth=0,
        )
        self.assertEqual(response.status_code, 404)

    def test_calendar_query_time_range_filters_results(self):
        inside = self._event(start="2026-06-10 09:00:00", stop="2026-06-10 10:00:00")
        outside = self._event(
            name="July Event", start="2026-07-10 09:00:00", stop="2026-07-10 10:00:00"
        )
        document = self._report(
            self._collection_href(self.calendar, "calendar"),
            """<?xml version="1.0" encoding="utf-8"?>
            <C:calendar-query xmlns:D="DAV:" xmlns:C="urn:ietf:params:xml:ns:caldav">
              <D:prop><D:getetag/><C:calendar-data/></D:prop>
              <C:filter>
                <C:comp-filter name="VCALENDAR">
                  <C:comp-filter name="VEVENT">
                    <C:time-range start="20260601T000000Z" end="20260630T000000Z"/>
                  </C:comp-filter>
                </C:comp-filter>
              </C:filter>
            </C:calendar-query>""",
        )
        hrefs = _hrefs_of(document)
        self.assertIn(self._uid_href(self.calendar, "calendar", inside.dav_uid), hrefs)
        self.assertNotIn(
            self._uid_href(self.calendar, "calendar", outside.dav_uid), hrefs
        )

    def test_calendar_multiget_returns_calendar_data(self):
        event = self._event()
        href = self._uid_href(self.calendar, "calendar", event.dav_uid)
        document = self._report(
            self._collection_href(self.calendar, "calendar"),
            """<?xml version="1.0" encoding="utf-8"?>
            <C:calendar-multiget xmlns:D="DAV:" xmlns:C="urn:ietf:params:xml:ns:caldav">
              <D:prop><D:getetag/><C:calendar-data/></D:prop>
              <D:href>%s</D:href>
            </C:calendar-multiget>"""
            % href,
        )
        data = _text(document, "//C:calendar-data")
        self.assertIn("BEGIN:VCALENDAR", data)
        self.assertIn("SUMMARY:HTTP Test Event", data)
        self.assertTrue(_text(document, "//D:getetag"))

    def test_free_busy_query(self):
        self._event(start="2026-06-10 09:00:00", stop="2026-06-10 10:00:00")
        document = self._report(
            self._collection_href(self.calendar, "calendar"),
            """<?xml version="1.0" encoding="utf-8"?>
            <C:free-busy-query xmlns:D="DAV:" xmlns:C="urn:ietf:params:xml:ns:caldav">
              <C:time-range start="20260601T000000Z" end="20260630T000000Z"/>
            </C:free-busy-query>""",
        )
        free_busy = _text(document, "//C:free-busy")
        self.assertIn("BEGIN:VCALENDAR", free_busy)
        self.assertIn("DTSTART:20260610T090000Z", free_busy)

    def test_addressbook_multiget(self):
        href = self._uid_href(self.addressbook, "addressbook", self.partner.dav_uid)
        document = self._report(
            self._collection_href(self.addressbook, "addressbook"),
            """<?xml version="1.0" encoding="utf-8"?>
            <A:addressbook-multiget
              xmlns:D="DAV:" xmlns:A="urn:ietf:params:xml:ns:carddav">
              <D:prop><D:getetag/><A:address-data/></D:prop>
              <D:href>%s</D:href>
            </A:addressbook-multiget>"""
            % href,
        )
        address_data = _text(document, "//A:address-data")
        self.assertIn("BEGIN:VCARD", address_data)
        self.assertIn("household@example.com", address_data)

    # ==================================================================
    # Write
    # ==================================================================
    def test_put_creates_event(self):
        uid = "put-created-1"
        payload = self._ics(
            uid,
            "DTSTART:20260812T020000Z\r\nDTEND:20260812T030000Z\r\n",
            "Created Over DAV",
        )
        response = self._dav_request(
            "PUT",
            self._uid_href(self.calendar, "calendar", uid),
            data=payload,
            headers=self._auth(content_type="text/calendar"),
        )
        self.assertIn(response.status_code, (201, 204), response.text)
        self.assertIn("ETag", response.headers)
        event = self.env["calendar.event"].search([("dav_uid", "=", uid)])
        self.assertEqual(len(event), 1)
        self.assertEqual(event.name, "Created Over DAV")
        self.assertEqual(event.start, datetime(2026, 8, 12, 2, 0, 0))
        self.assertEqual(event.user_id, self.user)

    def test_put_updates_existing_event_without_duplicating(self):
        event = self._event()
        payload = self._ics(
            event.dav_uid,
            "DTSTART:20260105T020000Z\r\nDTEND:20260105T033000Z\r\n",
            "Updated Over DAV",
        )
        response = self._dav_request(
            "PUT",
            self._uid_href(self.calendar, "calendar", event.dav_uid),
            data=payload,
            headers=self._auth(content_type="text/calendar"),
        )
        self.assertIn(response.status_code, (201, 204), response.text)
        self.assertEqual(
            self.env["calendar.event"].search_count([("dav_uid", "=", event.dav_uid)]),
            1,
        )
        reloaded = self.env["calendar.event"].browse(event.id)
        self.assertEqual(reloaded.name, "Updated Over DAV")
        self.assertEqual(reloaded.stop, datetime(2026, 1, 5, 3, 30, 0))

    def test_put_with_stale_etag_is_rejected(self):
        event = self._event()
        payload = self._ics(
            event.dav_uid,
            "DTSTART:20260105T020000Z\r\nDTEND:20260105T040000Z\r\n",
            "Should Not Apply",
        )
        headers = self._auth(content_type="text/calendar")
        headers["If-Match"] = '"stale-etag-value"'
        response = self._dav_request(
            "PUT",
            self._uid_href(self.calendar, "calendar", event.dav_uid),
            data=payload,
            headers=headers,
        )
        self.assertEqual(response.status_code, 412, response.text)
        self.assertEqual(
            self.env["calendar.event"].browse(event.id).name, "HTTP Test Event"
        )

    def test_put_recurring_event_creates_a_series(self):
        uid = "put-recurring-1"
        payload = self._ics(
            uid,
            "DTSTART:20260902T020000Z\r\nDTEND:20260902T030000Z\r\n"
            "RRULE:FREQ=WEEKLY;BYDAY=WE;COUNT=4\r\n",
            "Weekly Sync",
        )
        self._dav_request(
            "PUT",
            self._uid_href(self.calendar, "calendar", uid),
            data=payload,
            headers=self._auth(content_type="text/calendar"),
        )
        event = self.env["calendar.event"].search([("dav_uid", "=", uid)])
        self.assertEqual(len(event), 1)
        self.assertTrue(event.recurrency)
        self.assertEqual(event.recurrence_id.rrule_type, "weekly")
        self.assertTrue(event.recurrence_id.wed)
        self.assertEqual(event.recurrence_id.count, 4)

    def test_put_payload_without_vevent_is_400(self):
        response = self._dav_request(
            "PUT",
            self._uid_href(self.calendar, "calendar", "bad-payload"),
            data="BEGIN:VCALENDAR\r\nVERSION:2.0\r\nEND:VCALENDAR\r\n",
            headers=self._auth(content_type="text/calendar"),
        )
        self.assertEqual(response.status_code, 400)

    def test_delete_event(self):
        event = self._event()
        response = self._dav_request(
            "DELETE",
            self._uid_href(self.calendar, "calendar", event.dav_uid),
            headers=self._auth(),
        )
        self.assertIn(response.status_code, (200, 204), response.text)
        self.assertFalse(self.env["calendar.event"].browse(event.id).exists())

    def test_delete_unknown_event_is_404(self):
        response = self._dav_request(
            "DELETE",
            self._uid_href(self.calendar, "calendar", "no-such-uid"),
            headers=self._auth(),
        )
        self.assertEqual(response.status_code, 404)

    def test_put_vcard_creates_contact(self):
        uid = "put-contact-1"
        payload = (
            "BEGIN:VCARD\r\nVERSION:3.0\r\n"
            f"UID:{uid}\r\nN:Newman;Alice;;;\r\nFN:Alice Newman\r\n"
            "EMAIL:alice.newman@example.com\r\nTEL;TYPE=CELL:+66 81 555 0000\r\n"
            "END:VCARD\r\n"
        )
        response = self._dav_request(
            "PUT",
            self._uid_href(self.addressbook, "addressbook", uid),
            data=payload,
            headers=self._auth(content_type="text/vcard"),
        )
        self.assertIn(response.status_code, (201, 204), response.text)
        created = self.env["res.partner"].search([("dav_uid", "=", uid)])
        self.assertEqual(len(created), 1)
        self.assertEqual(created.name, "Alice Newman")
        self.assertEqual(created.email, "alice.newman@example.com")

    def test_put_vcard_without_fn_is_400(self):
        response = self._dav_request(
            "PUT",
            self._uid_href(self.addressbook, "addressbook", "no-fn"),
            data="BEGIN:VCARD\r\nVERSION:3.0\r\nUID:no-fn\r\nEND:VCARD\r\n",
            headers=self._auth(content_type="text/vcard"),
        )
        self.assertEqual(response.status_code, 400)

    # ==================================================================
    # Sync
    # ==================================================================
    def test_sync_collection_reports_added_and_deleted(self):
        collection_href = self._collection_href(self.calendar, "calendar")
        token = self._sync_token(collection_href)

        untouched = self._report(collection_href, self._sync_body(token))
        self.assertEqual(len(untouched.xpath(".//D:response", namespaces=NS)), 0)

        added = self._event(name="Added Later")
        removed = self._event(name="Removed Later")
        removed_uid = removed.dav_uid
        removed.unlink()

        document = self._report(collection_href, self._sync_body(token))
        hrefs = _hrefs_of(document)
        self.assertIn(self._uid_href(self.calendar, "calendar", added.dav_uid), hrefs)
        # The deleted event must be reported by its original href with a 404 so
        # the client drops it rather than keeping a ghost.
        self.assertIn(self._uid_href(self.calendar, "calendar", removed_uid), hrefs)
        statuses = list(_hrefs_of(document, ".//D:response/D:status"))
        self.assertIn("HTTP/1.1 404 Not Found", statuses)

    def test_sync_collection_without_token_returns_everything(self):
        self._event()
        document = self._report(
            self._collection_href(self.calendar, "calendar"),
            """<?xml version="1.0" encoding="utf-8"?>
            <D:sync-collection xmlns:D="DAV:">
              <D:sync-level>1</D:sync-level>
              <D:prop><D:getetag/></D:prop>
            </D:sync-collection>""",
        )
        self.assertGreaterEqual(len(document.xpath(".//D:response", namespaces=NS)), 1)

    def test_unusable_sync_token_returns_409_with_valid_token(self):
        response = self._report_raw(
            self._collection_href(self.calendar, "calendar"),
            self._sync_body("http://dav.golder.lan/ns/sync/nonsense"),
        )
        self.assertEqual(response.status_code, 409)
        self.assertTrue(response.headers.get("valid-sync-token"))

    def test_unknown_report_is_403(self):
        response = self._report_raw(
            self._collection_href(self.calendar, "calendar"),
            '<?xml version="1.0" encoding="utf-8"?>'
            '<D:principal-property-search xmlns:D="DAV:"/>',
        )
        self.assertEqual(response.status_code, 403)

    # ==================================================================
    # Helpers
    # ==================================================================
    def _event(
        self,
        name="HTTP Test Event",
        start="2026-01-05 09:00:00",
        stop="2026-01-05 10:00:00",
    ):
        return self.env["calendar.event"].create(
            {
                "name": name,
                "start": start,
                "stop": stop,
                "event_tz": "UTC",
                "user_id": self.user.id,
            }
        )

    def _ics(self, uid, body, summary):
        return (
            "BEGIN:VCALENDAR\r\nVERSION:2.0\r\nPRODID:-//test//EN\r\n"
            "BEGIN:VEVENT\r\n"
            f"UID:{uid}\r\n"
            "DTSTAMP:20260101T000000Z\r\n"
            f"SUMMARY:{summary}\r\n{body}"
            "END:VEVENT\r\nEND:VCALENDAR\r\n"
        )

    def _sync_body(self, token):
        return (
            '<?xml version="1.0" encoding="utf-8"?>'
            '<D:sync-collection xmlns:D="DAV:">'
            f"<D:sync-token>{token}</D:sync-token>"
            "<D:sync-level>1</D:sync-level>"
            "<D:prop><D:getetag/></D:prop>"
            "</D:sync-collection>"
        )

    def _sync_token(self, collection_href):
        document = self._propfind(collection_href, depth=0)
        token = _text(document, "//D:sync-token")
        self.assertTrue(token, "collection must advertise a sync-token")
        return token

    def _auth(self, login=None, password=None, content_type=None):
        credentials = base64.b64encode(
            f"{login or self.user.login}:{password or self.PASSWORD}".encode()
        ).decode("ascii")
        headers = {"Authorization": f"Basic {credentials}"}
        if content_type:
            headers["Content-Type"] = content_type
        return headers

    def _dav_request(self, method, href, data=None, headers=None, depth=None):
        headers = dict(headers or {})
        if depth is not None:
            headers["Depth"] = str(depth)
        return self.opener.request(
            method,
            self.base_url() + href,
            data=data,
            headers=headers,
            timeout=30,
            allow_redirects=False,
        )

    def _propfind(self, href, depth=0):
        response = self._dav_request(
            "PROPFIND",
            href,
            data=PROPFIND_ALLPROP,
            headers=self._auth(content_type=XML_CONTENT_TYPE),
            depth=depth,
        )
        self.assertEqual(response.status_code, 207, response.text)
        return etree.fromstring(response.content)

    def _report(self, href, body):
        response = self._report_raw(href, body)
        self.assertEqual(response.status_code, 207, response.text)
        return etree.fromstring(response.content)

    def _report_raw(self, href, body):
        return self._dav_request(
            "REPORT", href, data=body, headers=self._auth(content_type=XML_CONTENT_TYPE)
        )

    def _hrefs(self):
        segment = quote(self.user.login, safe="")
        return {
            "principal": f"/dav/principals/{segment}/",
            "calendar_home": f"/dav/caldav/{segment}/",
            "addressbook_home": f"/dav/carddav/{segment}/",
        }

    def _principal_href(self):
        return self._hrefs()["principal"]

    def _collection_href(self, collection, dav_type):
        return self._collection_href_by_slug(collection, dav_type, collection.dav_slug)

    def _collection_href_by_slug(self, collection, dav_type, slug):
        # Mirrors the controller's URL_SEGMENTS mapping.
        segment = quote(self.user.login, safe="")
        prefix = {"calendar": "caldav", "addressbook": "carddav"}[dav_type]
        return f"/dav/{prefix}/{segment}/{slug}/"

    def _uid_href(self, collection, dav_type, uid):
        suffix = ".ics" if dav_type == "calendar" else ".vcf"
        return f"{self._collection_href(collection, dav_type)}{uid}{suffix}"


def _hrefs_of(document, xpath=".//D:response/D:href"):
    """hrefs from a multistatus document.

    ``Element.findall`` uses ElementPath, which has no namespace support, so
    every prefixed query has to go through ``xpath`` with an explicit map.
    """
    return {element.text for element in document.xpath(xpath, namespaces=NS)}


def _text(document, xpath):
    """Concatenated text of an xpath match, or '' when nothing matches."""
    elements = document.xpath(xpath, namespaces=NS)
    return "".join(element.text or "" for element in elements)
