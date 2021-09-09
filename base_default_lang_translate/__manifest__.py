{
    "name": "Default Language Translation",
    "summary": """
        This modules allows to select a default language
        which is used for source terms in translations
        """,
    "version": "12.0.1.0.0",
    "development_status": "Beta",
    "category": "Uncategorized",
    "website": "https://github.com/OCA/server-backend",
    "author": "Le Filament, Mariano Ruiz, Odoo Community Association (OCA)",
    "maintainers": ["remi-filament"],
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "base",
    ],
    "data": [
        "views/res_lang_views.xml",
    ],
}
