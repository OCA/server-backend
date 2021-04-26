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


Limitations
~~~~~~~~~~~

As the time of writing Odoo use `has_group("base.group_user")` to gives the
backend access.
This module is only overloading that method to try if user is in the
`group_backend.group_backend` group (in case of `base.group_user`
is requested and return `False`) to let access to the odoo backend.

This avoid to overwrite a lot of overwrite in different controllers from
different modules ('portal', 'web', 'base', 'website') with hard coded statements
that check if user is part of the `base.group_user` group.

.. warning::

    Using this module and grant a user with `group_backend`'s group is
    equivalent to grant `group_user`'s group everywhere `has_group`
    has been used.
