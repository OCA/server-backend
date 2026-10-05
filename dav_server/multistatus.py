# Copyright 2026 Ross Golder
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

"""Builders for WebDAV multistatus responses (RFC 4918 section 13).

CalDAV and CardDAV both express discovery and listing results as a
``DAV:multistatus`` document, so everything XML-shaped lives in one place.
"""

from lxml import etree

DAV_NS = "DAV:"
CALDAV_NS = "urn:ietf:params:xml:ns:caldav"
CARDDAV_NS = "urn:ietf:params:xml:ns:carddav"

NSMAP = {"D": DAV_NS, "C": CALDAV_NS, "A": CARDDAV_NS}

STATUS_OK = "HTTP/1.1 200 OK"
STATUS_NOT_FOUND = "HTTP/1.1 404 Not Found"


def qname(namespace, tag):
    return f"{{{namespace}}}{tag}"


def dav(tag):
    return qname(DAV_NS, tag)


def caldav(tag):
    return qname(CALDAV_NS, tag)


def carddav(tag):
    return qname(CARDDAV_NS, tag)


class PropSet:
    """An ordered bag of DAV properties.

    Each entry becomes one child element of the enclosing ``DAV:prop``. Values
    are declared by kind so that nested structures (``DAV:resourcetype`` with a
    child, ``C:calendar-home-set`` with an ``DAV:href``) stay readable at the
    call site.
    """

    def __init__(self):
        self._entries = []

    def text(self, name, value):
        self._entries.append(("text", name, str(value)))
        return self

    def attrs(self, name, attributes):
        self._entries.append(("attrs", name, attributes))
        return self

    def children(self, name, children):
        """``children`` is an iterable of ``(qname, attributes)`` pairs."""
        self._entries.append(("children", name, tuple(children)))
        return self

    def hrefs(self, name, *values):
        """A property whose children are ``DAV:href`` elements, e.g. a home set."""
        self._entries.append(("hrefs", name, tuple(values)))
        return self

    def resourcetype(self, *child_names):
        return self.children(dav("resourcetype"), [(name, {}) for name in child_names])

    def add_to(self, prop_element):
        for kind, name, value in self._entries:
            element = etree.SubElement(prop_element, name)
            if kind == "text":
                element.text = value
            elif kind == "attrs":
                for key, attribute_value in value.items():
                    element.set(key, attribute_value)
            elif kind == "hrefs":
                for href in value:
                    child = etree.SubElement(element, dav("href"))
                    child.text = href
            elif kind == "children":
                for child_name, attributes in value:
                    child = etree.SubElement(element, child_name)
                    for key, attribute_value in attributes.items():
                        child.set(key, attribute_value)
        return prop_element

    def __len__(self):
        return len(self._entries)


class Multistatus:
    def __init__(self):
        self.root = etree.Element(dav("multistatus"), nsmap=NSMAP)

    def add_response(self, href):
        response = etree.SubElement(self.root, dav("response"))
        element = etree.SubElement(response, dav("href"))
        element.text = href
        return response

    def add_propstat(self, response, props, status=STATUS_OK):
        propstat = etree.SubElement(response, dav("propstat"))
        prop_element = etree.SubElement(propstat, dav("prop"))
        props.add_to(prop_element)
        status_element = etree.SubElement(propstat, dav("status"))
        status_element.text = status
        return propstat

    def add_status(self, response, status):
        """Report a whole response as failed (404 for vanished resources)."""
        status_element = etree.SubElement(response, dav("status"))
        status_element.text = status
        return response

    def tobytes(self):
        return etree.tostring(
            self.root, xml_declaration=True, encoding="utf-8", pretty_print=False
        )
