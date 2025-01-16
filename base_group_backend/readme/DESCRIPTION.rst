This module adds two "Backend User" groups (``group_backend`` and ``group_backend_ui_users``) with restricted access to odoo backend only (``/web``), with less and more controlled access than the native "Internal User" group.

  The problem with the "Internal User" group (``base.group_user``) is that it can be used by any new module added to your project, so you don't control clearly this group's accesses.

The UI access is provided only for ``group_backend_ui_users`` :

* minimal default access rules to access the user's own data:
    * users and partners
    * mail activity, notification and channel
    * presence
* minimal default menu to restrict the available ones:
    * notification
    * activities

Here is an example where a user from ``group_backend_ui_users`` can only access and use the Dummy App. No other application is available to this user (you may define your own application instead of the Dummy one).

.. figure:: ../static/description/dummy_app.png
    :alt: Dummy app for demo

We suggest to use this module with its companion ``base_user_role``.

Limitations
~~~~~~~~~~~

At the time of writing, Odoo uses ``user.share == False`` and ``user.has_group("base.group_user") == True`` to give the backend access to ``user``.

So technically, the module does 2 things :

* It sets the ``share`` parameter to ``False`` for ``group_backend`` users.
* It hijacks the ``has_group`` method of res.users by returning ``True`` for ``group_backend`` users when the requested group is ``base.group_user``


This avoids to write a lot of overwrite in different controllers from different modules ('portal', 'web', 'base', 'website') with hard coded statements that check if user is part of the ``base.group_user`` or ``share == False`` group.