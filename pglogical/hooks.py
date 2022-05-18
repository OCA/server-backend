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
DDL_KEYWORDS = ("CREATE", "ALTER", "DROP", "TRUNCATE")


def schema_qualify(parsed_query, schema="public"):
    """
    Yield tokens and add a schema to objects if there's none
    """
    token_iterator = parsed_query.flatten()
    Name = sqlparse.tokens.Name
    Punctuation = sqlparse.tokens.Punctuation
    is_qualified = False
    for token in token_iterator:
        yield token
        if not is_qualified and token.is_keyword and token.normalized in DDL_KEYWORDS:
            # we check if the name coming after {create,drop,alter} object keywords
            # is schema qualified, and if not, add the schema we got passed
            next_token = False
            while True:
                try:
                    next_token = token_iterator.__next__()
                except StopIteration:
                    # this is invalid sql
                    next_token = False
                    break
                if not (next_token.is_whitespace or next_token.is_keyword):
                    break
                yield next_token
            if not next_token:
                continue
            if next_token.ttype != Name:
                yield next_token
                continue

            object_name_or_schema = next_token
            needs_schema = False
            next_token = False
            try:
                next_token = token_iterator.__next__()
                needs_schema = str(next_token) != '.'
            except StopIteration:
                needs_schema = True

            if needs_schema:
                yield sqlparse.sql.Token(Name, schema)
                yield sqlparse.sql.Token(Punctuation, '.')

            yield object_name_or_schema

            if next_token:
                yield next_token

            is_qualified = True


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
        if query[:6] not in ("SELECT", "UPDATE"):
            parsed_queries = sqlparse.parse(query)
            if any(
                    parsed_query.get_type() in DDL_KEYWORDS
                    for parsed_query in parsed_queries
            ) and not any(
                    token.is_keyword and token.normalized in
                    # don't replicate constraints, triggers, indexes
                    ("CONSTRAINT", "TRIGGER", "INDEX")
                    for parsed in parsed_queries for token in parsed.tokens[1:]
            ):
                qualified_query = ''.join(
                    ''.join(str(token) for token in schema_qualify(parsed_query))
                    for parsed_query in parsed_queries
                )
                mogrified = self.mogrify(qualified_query, params).decode("utf8")
                query = "SELECT pglogical.replicate_ddl_command(%s, %s)"
                params = (mogrified, execute.replication_sets)
        return execute.origin(self, query, params=params, log_exceptions=log_exceptions)

    execute.origin = execute_org
    execute.replication_sets = replication_sets

    Cursor.execute = execute
