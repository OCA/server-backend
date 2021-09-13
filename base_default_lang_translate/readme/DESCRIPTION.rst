This modules allows to select a default language which is used for source terms in translations.
Any update done with this default_language will be taken as source in translations
and written in object directly.
Also when updating a translatable term, all existing translations (but default language) will be set to to_translate

This module is useless in case your main language is en_US or in case you have only 1 language installed
(in thoses cases, Odoo performs correctly).
