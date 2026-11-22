# Copyright 2026 Globalist Technology SRL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

from faker import Faker

from odoo import _, models
from odoo.exceptions import UserError


class AnonymizeMethodFaker(models.AbstractModel):
    _inherit = "anonymize.method"
    _name = "anonymize.method.faker"
    _description = "Faker provider"

    # provider: a Faker method, like iban, or vat_id and ssn in it_IT, that
    # generates syntactically valid values; kwargs are passed to it, unique
    # avoids repeated values (for columns with a unique constraint)
    _default_options = {
        "provider": "pystr",
        "locale": "en_US",
        "kwargs": {},
        "unique": False,
    }

    def _run(self, field):
        options = field._get_options()
        try:
            # Faker raises AttributeError for unknown locales too
            fake = Faker(options["locale"])
            if options["unique"]:
                fake = fake.unique
            provider = getattr(fake, options["provider"])
        except AttributeError as e:
            raise UserError(
                _(
                    "Faker has no provider %(provider)s for locale %(locale)s",
                    provider=options["provider"],
                    locale=options["locale"],
                )
            ) from e
        kwargs = options["kwargs"]
        return self._update_values(field, lambda: provider(**kwargs))
