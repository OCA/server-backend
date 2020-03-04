# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models
from odoo.http import request


class Http(models.AbstractModel):
    _inherit = "ir.http"

    def session_info(self):  # pragma: no cover
        result = super().session_info()
        user = request.env.user
        allowed_profiles = [
            (profile.id, profile.name) for profile in user.profile_ids
        ]
        if len(allowed_profiles) > 1:
            current_profile = (user.profile_id.id, user.profile_id.name)
            result["user_profiles"] = {
                "current_profile": current_profile,
                "allowed_profiles": allowed_profiles,
            }
        else:
            result["user_profiles"] = False
        result["profile_id"] = (
            user.profile_id.id if request.session.uid else None
        )
        return result
