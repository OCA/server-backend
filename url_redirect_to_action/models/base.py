from odoo import api, models


class Base(models.AbstractModel):
    _inherit = 'base'

    @api.model
    def _redirect_to_action_from_url(self, action_name, values):
        action = self.env.ref(action_name, raise_if_not_found=False)
        if action:
            action = action._get_action_dict()
            # TODO no effect for now
            return action
