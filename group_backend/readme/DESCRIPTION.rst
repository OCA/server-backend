This module was written to extend the standard functionality regarding users
and groups management by adding a new `Backend user` group that only gives access
to odoo backend (`/web`):

* no default access
* no default menu
* no default access rules
* no default actions
* no default views


The problem with the `Internal user` is when you want to gives access to the
backend to a really thin part of your business to some users, it's quite hard
to properly maintain those roles over the project life, a lot of models use
that group (`base.group_user`) by default which makes hard
to maintains.

So that helps creating well-defined user groups with more controls.

We suggest to use this module with its compagnon `base_user_role`
