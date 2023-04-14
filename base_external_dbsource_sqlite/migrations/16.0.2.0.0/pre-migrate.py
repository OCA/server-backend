# Copyright 2023 Moduon Team S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)


def migrate(cr, version):
    """Rename sqlite connections to sqlalchemy."""
    cr.execute(
        """
        UPDATE base_external_dbsource
        SET connector = 'sqlalchemy'
        WHERE connector = 'sqlite'
        """
    )
