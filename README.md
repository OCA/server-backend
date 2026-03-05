
[![Support the OCA](https://odoo-community.org/readme-banner-image)](https://odoo-community.org/get-involved?utm_source=repo-readme)

# server-backend
[![Runboat](https://img.shields.io/badge/runboat-Try%20me-875A7B.png)](https://runboat.odoo-community.org/builds?repo=OCA/server-backend&target_branch=16.0)
[![Pre-commit Status](https://github.com/OCA/server-backend/actions/workflows/pre-commit.yml/badge.svg?branch=16.0)](https://github.com/OCA/server-backend/actions/workflows/pre-commit.yml?query=branch%3A16.0)
[![Build Status](https://github.com/OCA/server-backend/actions/workflows/test.yml/badge.svg?branch=16.0)](https://github.com/OCA/server-backend/actions/workflows/test.yml?query=branch%3A16.0)
[![codecov](https://codecov.io/gh/OCA/server-backend/branch/16.0/graph/badge.svg)](https://codecov.io/gh/OCA/server-backend)
[![Translation Status](https://translation.odoo-community.org/widgets/server-backend-16-0/-/svg-badge.svg)](https://translation.odoo-community.org/engage/server-backend-16-0/?utm_source=widget)

<!-- /!\ do not modify above this line -->

Mainly base modules used by others

<!-- /!\ do not modify below this line -->

<!-- prettier-ignore-start -->

[//]: # (addons)

Available addons
----------------
addon | version | maintainers | summary
--- | --- | --- | ---
[base_external_dbsource](base_external_dbsource/) | 16.0.1.0.1 |  | External Database Sources
[base_external_dbsource_mssql](base_external_dbsource_mssql/) | 16.0.1.1.0 | <a href='https://github.com/anddago78'><img src='https://github.com/anddago78.png' width='32' height='32' style='border-radius:50%;' alt='anddago78'/></a> | External Database Source - MSSQL
[base_external_dbsource_mysql](base_external_dbsource_mysql/) | 16.0.1.0.0 |  | External Database Source - MySQL
[base_external_dbsource_sqlite](base_external_dbsource_sqlite/) | 16.0.1.0.2 | <a href='https://github.com/anddago78'><img src='https://github.com/anddago78.png' width='32' height='32' style='border-radius:50%;' alt='anddago78'/></a> | External Database Source - SQLite
[base_external_system](base_external_system/) | 16.0.1.0.0 |  | Data models allowing for connection to external systems.
[base_global_discount](base_global_discount/) | 16.0.1.1.0 |  | Base Global Discount
[base_group_backend](base_group_backend/) | 16.0.1.1.0 | <a href='https://github.com/FranzPoize'><img src='https://github.com/FranzPoize.png' width='32' height='32' style='border-radius:50%;' alt='FranzPoize'/></a> <a href='https://github.com/bealdav'><img src='https://github.com/bealdav.png' width='32' height='32' style='border-radius:50%;' alt='bealdav'/></a> | Group backend
[base_import_match](base_import_match/) | 16.0.1.1.0 |  | Try to avoid duplicates before importing
[base_portal_type](base_portal_type/) | 16.0.1.0.0 | <a href='https://github.com/hbrunn'><img src='https://github.com/hbrunn.png' width='32' height='32' style='border-radius:50%;' alt='hbrunn'/></a> | Base module to allow different types of portals
[base_user_effective_permissions](base_user_effective_permissions/) | 16.0.1.0.0 | <a href='https://github.com/hbrunn'><img src='https://github.com/hbrunn.png' width='32' height='32' style='border-radius:50%;' alt='hbrunn'/></a> | Inspect effective permissions applying to a user
[base_user_role](base_user_role/) | 16.0.1.4.4 | <a href='https://github.com/sebalix'><img src='https://github.com/sebalix.png' width='32' height='32' style='border-radius:50%;' alt='sebalix'/></a> <a href='https://github.com/jcdrubay'><img src='https://github.com/jcdrubay.png' width='32' height='32' style='border-radius:50%;' alt='jcdrubay'/></a> <a href='https://github.com/novawish'><img src='https://github.com/novawish.png' width='32' height='32' style='border-radius:50%;' alt='novawish'/></a> | User roles
[base_user_role_company](base_user_role_company/) | 16.0.1.2.2 |  | User roles by company
[base_user_role_history](base_user_role_history/) | 16.0.1.0.0 | <a href='https://github.com/ThomasBinsfeld'><img src='https://github.com/ThomasBinsfeld.png' width='32' height='32' style='border-radius:50%;' alt='ThomasBinsfeld'/></a> | This module allows to track the changes on users roles.
[server_action_navigate](server_action_navigate/) | 16.0.1.0.0 | <a href='https://github.com/legalsylvain'><img src='https://github.com/legalsylvain.png' width='32' height='32' style='border-radius:50%;' alt='legalsylvain'/></a> <a href='https://github.com/ashishhirpara'><img src='https://github.com/ashishhirpara.png' width='32' height='32' style='border-radius:50%;' alt='ashishhirpara'/></a> | Navigate between any items of any Odoo Models
[server_action_sort](server_action_sort/) | 16.0.1.0.0 | <a href='https://github.com/legalsylvain'><img src='https://github.com/legalsylvain.png' width='32' height='32' style='border-radius:50%;' alt='legalsylvain'/></a> | Sort any lines of any models by any criterias

[//]: # (end addons)

<!-- prettier-ignore-end -->

## Licenses

This repository is licensed under [AGPL-3.0](LICENSE).

However, each module can have a totally different license, as long as they adhere to Odoo Community Association (OCA)
policy. Consult each module's `__manifest__.py` file, which contains a `license` key
that explains its license.

----
OCA, or the [Odoo Community Association](http://odoo-community.org/), is a nonprofit
organization whose mission is to support the collaborative development of Odoo features
and promote its widespread use.
