This module extends the ``base_import`` odoo module.

by default, in odoo, if a spreadsheet contains the value ' France ' in 
a column 'country_id' the according item (``base.fr``) will not be found
because Odoo realize a strict search.
This module 'strip' all the values before importing, and so fixes such
cases.