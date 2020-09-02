# Copyright 2017 LasLabs Inc.
# Copyright 2020 Therp BV <https://therp.nl>.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from contextlib import contextmanager

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from ..lib_systems.external_system_adapter import ExternalSystemAdapter


def get_all_subclasses(cls):
    """Helper function to get all the subclasses of a class."""
    cls.__subclasses__()
    subclasses = set()
    check_these = [cls]
    while check_these:
        parent = check_these.pop()
        for child in parent.__subclasses__():
            if child not in subclasses:
                subclasses.add(child)
                check_these.append(child)
    return subclasses


def is_concrete(cls):
    return not bool(getattr(cls, "__abstractmethods__", False))


def get_adapter(system_type):
    """Get the concrete adapter implementing a system type."""
    system_adapters = get_all_subclasses(ExternalSystemAdapter)
    for adapter in system_adapters:
        if adapter._name == system_type:
            return adapter
    raise UserError(_("No external system adapter named %s") % system_type)


class ExternalSystem(models.Model):

    _name = "external.system"
    _description = "External System"

    def get_system_type_selection(self):
        """Selection will be based on concrete external system classes."""
        system_adapters = get_all_subclasses(ExternalSystemAdapter)
        return [
            (subclass._name, subclass._description)
            for subclass in system_adapters
            if is_concrete(subclass)
        ]

    name = fields.Char(
        required=True, help="This is the canonical (humanized) name for the system.",
    )
    host = fields.Char(
        help="This is the domain or IP address that the system can be reached " "at.",
    )
    port = fields.Integer(
        help="This is the port number that the system is listening on.",
    )
    username = fields.Char(
        help="This is the username that is used for authenticating to this "
        "system, if applicable.",
    )
    password = fields.Char(
        help="This is the password that is used for authenticating to this "
        "system, if applicable.",
    )
    private_key = fields.Text(
        help="This is the private key that is used for authenticating to "
        "this system, if applicable.",
    )
    private_key_password = fields.Text(
        help="This is the password to unlock the private key that was "
        "provided for this sytem.",
    )
    fingerprint = fields.Text(
        help="This is the fingerprint that is advertised by this system in "
        "order to validate its identity.",
    )
    ignore_fingerprint = fields.Boolean(
        default=True,
        help="Set this to `True` in order to ignore an invalid/unknown "
        "fingerprint from the system.",
    )
    remote_path = fields.Char(
        help="Restrict to this directory path on the remote, if applicable.",
    )
    remote_path_ids = fields.One2many(
        comodel_name="external.system.path",
        inverse_name="system_id",
        string="Remote system path's and resources",
        help="Link for multiple resources/path's on external system.",
    )
    company_ids = fields.Many2many(
        string="Companies",
        comodel_name="res.company",
        required=True,
        default=lambda s: [(6, 0, s.env.user.company_id.ids)],
        help="Access to this system is restricted to these companies.",
    )
    system_type = fields.Selection(selection=get_system_type_selection, required=True,)
    state = fields.Selection(
        selection=[("draft", "Not Confirmed"), ("done", "Confirmed")],
        default="draft",
        readonly=True,
        required=True,
    )

    _sql_constraints = [
        ("name_uniq", "UNIQUE(name)", "Connection name must be unique."),
    ]

    @api.constrains("fingerprint", "ignore_fingerprint")
    def check_fingerprint_ignore_fingerprint(self):
        """Do not allow a blank fingerprint if not set to ignore."""
        for record in self:
            if not record.ignore_fingerprint and not record.fingerprint:
                raise ValidationError(
                    _(
                        "Fingerprint cannot be empty when Ignore Fingerprint is "
                        "not checked.",
                    )
                )

    @contextmanager
    def client(self):
        """Client object usable as a context manager to include destruction.

        Yields the result from ``get_client``, then calls ``destroy_client``
            to cleanup the client.

        Yields:
            mixed: An object representing the client connection to the remote system.
        """
        client = self.make_instance()
        with client.client() as client:
            yield client

    def action_test_connection(self):
        """Test the connection to the external system."""
        try:
            system = self.make_instance()
            system.test_connection()
            self.state = "done"
        except Exception:
            self.state = "draft"
            raise

    def make_instance(self):
        """Create concrete instance for this object."""
        self.ensure_one()
        adapter = get_adapter(self.system_type)
        system = adapter(self)
        return system
