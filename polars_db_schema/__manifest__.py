{
    "name": "Polars Db Schema",
    "version": "18.0.1.0.0",
    "author": "Akretion, Odoo Community Association (OCA)",
    "license": "GPL-3",
    "depends": [
        "polars_db_process",
    ],
    "external_dependencies": {"python": []},
    "data": [
        "security/ir.model.access.xml",
        "views/db_config.xml",
        "views/db_table.xml",
        "views/db_type.xml",
        "data/db_type.xml",
    ],
    "installable": True,
}
