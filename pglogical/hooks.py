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
DDL_KEYWORDS = set(["CREATE", "ALTER", "DROP", "TRUNCATE"])
QUALIFY_KEYWORDS = DDL_KEYWORDS | set(["FROM", "INHERITS", "JOIN"])
NO_QUALIFY_KEYWORDS = set(["AS", "COLUMN", "ON", "RETURNS", "SELECT"])
TEMPORARY = set(["TEMP", "TEMPORARY"])


def schema_qualify(tokens, temp_tables, keywords=None, schema="public"):
    """
    Add tokens to add a schema to objects if there's none, but record and
    exclude temporary tables
    """
    Identifier = sqlparse.sql.Identifier
    Name = sqlparse.tokens.Name
    Punctuation = sqlparse.tokens.Punctuation
    Token = sqlparse.sql.Token
    Statement = sqlparse.sql.Statement
    Function = sqlparse.sql.Function
    Parenthesis = sqlparse.sql.Parenthesis
    keywords = list(keywords or [])

    for token in tokens.tokens:
        if token.is_keyword:
            keywords.append(token.normalized)
            continue
        elif token.is_whitespace:
            continue
        elif token.__class__ == Identifier and not token.is_wildcard():
            str_token = str(token)
            needs_qualification = "." not in str_token
            # qualify tokens that are direct children of a statement as in ALTER TABLE
            if token.parent.__class__ == Statement:
                pass
            # or of an expression parsed as function as in CREATE TABLE table
            # but not within brackets
            if token.parent.__class__ == Function:
                needs_qualification &= not token.within(Parenthesis)
            elif token.parent.__class__ == Parenthesis:
                needs_qualification &= (
                    keywords and (keywords[-1] in QUALIFY_KEYWORDS) or False
                )
            # but not if the identifier is ie a column name
            if set(keywords) & NO_QUALIFY_KEYWORDS:
                needs_qualification &= (
                    keywords and (keywords[-1] in QUALIFY_KEYWORDS) or False
                )
            # and also not if this is a temporary table
            if needs_qualification:
                if len(keywords) > 1 and keywords[-2] in TEMPORARY:
                    needs_qualification = False
                    temp_tables.append(str_token)
                elif str_token in temp_tables:
                    needs_qualification = False
                    temp_tables.remove(str_token)
            if needs_qualification:
                token.insert_before(0, Token(Punctuation, "."))
                token.insert_before(0, Token(Name, schema))
                keywords = []
        elif token.is_group:
            schema_qualify(token, temp_tables, keywords=keywords, schema=schema)

    return tokens.tokens


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
            temp_tables = getattr(self, "__temp_tables", [])
            parsed_queries = sqlparse.parse(query)
            if any(
                parsed_query.get_type() in DDL_KEYWORDS
                for parsed_query in parsed_queries
            ) and not any(
                token.is_keyword and token.normalized in
                # don't replicate constraints, triggers, indexes
                ("CONSTRAINT", "TRIGGER", "INDEX")
                for parsed in parsed_queries
                for token in parsed.tokens[1:]
            ):
                qualified_query = "".join(
                    "".join(
                        str(token)
                        for token in schema_qualify(
                            parsed_query,
                            temp_tables,
                        )
                    )
                    for parsed_query in parsed_queries
                )
                mogrified = self.mogrify(qualified_query, params).decode("utf8")
                query = "SELECT pglogical.replicate_ddl_command(%s, %s)"
                params = (mogrified, execute.replication_sets)
            setattr(self, "__temp_tables", temp_tables)
        return execute.origin(self, query, params=params, log_exceptions=log_exceptions)

    execute.origin = execute_org
    execute.replication_sets = replication_sets

    Cursor.execute = execute
