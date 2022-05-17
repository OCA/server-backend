# Copyright 2022 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging
from odoo.sql_db import Cursor
from odoo.tools import config

try:
    import sqlparse
except ImportError:
    sqlparse = None

SECTION_NAME = "pglogical"


def post_load():
    """
    Patch cursor to funnel DDL through pglogical.replicate_ddl_command if configured to
    do so
    """

    _logger = logging.getLogger("odoo.addons.pglogical")

    if SECTION_NAME not in config.misc:
        _logger.info("%s section missing in config, not doing anything", SECTION_NAME)
        return
    replication_sets = list(
        filter(None, config.misc[SECTION_NAME].get("replication_sets", "").split(","))
    )
    if not replication_sets:
        _logger.error("no replication sets defined, not doing anything")
        return
    if not sqlparse:
        _logger.error("DDL replication not supported - sqlparse is not available")
        return
    if config["test_enable"]:
        _logger.info("test mode enabled, not doing anything")
        return

    _logger.info("patching cursor to intercept ddl")
    execute_org = Cursor.execute

    def execute(self, query, params=None, log_exceptions=None):
        """Wrap DDL in pglogical.replicate_ddl_command"""
        # short circuit statements that must be as fast as possible
        if query[:6] != "SELECT":
            parsed_queries = sqlparse.parse(query)
            if any(
                    parsed_query.get_type() in ("CREATE", "ALTER", "DROP")
                    for parsed_query in parsed_queries
            ) and not any(
                    token.is_keyword and token.normalized in
                    # don't replicate constraints, triggers, indexes
                    ("CONSTRAINT", "TRIGGER", "INDEX")
                    for parsed in parsed_queries for token in parsed.tokens[1:]
            ):
                mogrified = self.mogrify(query, params).decode("utf8")
                query = "SELECT pglogical.replicate_ddl_command(%s, %s)"
                params = (mogrified, execute.replication_sets)
        return execute.origin(self, query, params=params, log_exceptions=log_exceptions)

    execute.origin = execute_org
    execute.replication_sets = replication_sets

    Cursor.execute = execute
