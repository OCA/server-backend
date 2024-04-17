# © 2024 FactorLibre - Aritz Olea <aritz.olea@factorlibre.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import api, fields, models, tools
from odoo.osv import expression
from odoo.tools import config
from odoo.tools.safe_eval import safe_eval


class IrRule(models.Model):
    _inherit = "ir.rule"

    and_restriction_for_groups = fields.Boolean(string="AND restriction for groups")

    @api.model
    @tools.conditional(
        "xml" not in config["dev_mode"],
        tools.ormcache(
            "self.env.uid",
            "self.env.su",
            "model_name",
            "mode",
            "tuple(self._compute_domain_context_values())",
        ),
    )
    def _compute_domain(self, model_name, mode="read"):
        if self.env.context.get("avoid_loop", False):
            return
        res = super()._compute_domain(model_name, mode=mode)
        rules = self._get_rules(model_name, mode=mode)
        eval_context = self.with_context(avoid_loop=True)._eval_context()
        restriction_domains = []
        for rule in rules.sudo():
            # evaluate the domain for the current user
            dom = (
                safe_eval(rule.domain_force, eval_context) if rule.domain_force else []
            )
            dom = expression.normalize_domain(dom)
            if rule.and_restriction_for_groups:
                restriction_domains.append(dom)
        return expression.AND(restriction_domains + [res])
