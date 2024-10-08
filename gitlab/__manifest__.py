{
    "name": "Gitlab",
    "summary": "Base module for implementing gitlab related features",
    "category": "Technical",
    "version": "16.0.1.0.0",
    "author": "Onestein, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/server-backend",
    "license": "AGPL-3",
    "depends": ["base"],
    "external_dependencies": {"python": ["python-gitlab"]},
    "data": ["security/ir_model_access.xml", "views/gitlab_view.xml", "menuitems.xml"],
}
