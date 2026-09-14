{
    "name": "Record Trace",
    "summary": "Log record deletions (model, id, name, user, date) for kpiten parquet sync",
    "version": "18.0.1.0.0",
    "category": "Tools",
    "author": "Akretion",
    "license": "AGPL-3",
    "depends": ["base"],
    "data": [
        "security/ir.model.access.csv",
        "data/ir_config_parameter.xml",
        "data/ir_cron.xml",
        "views/record_trace_views.xml",
    ],
    "installable": True,
}
