# Copyright 2026 CIT Services (https://www.cit-services.eu).
# @author Solomon Prabu <s.prabu@cit-services.eu>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging

logger = logging.getLogger(__name__)


def post_init_hook(env):
    roles = env["res.users.role"].search([])
    if not roles:
        logger.info("No roles found")
        return
    roles._update_role_model_access()
    logger.info("Updated model access for %d roles", len(roles))
