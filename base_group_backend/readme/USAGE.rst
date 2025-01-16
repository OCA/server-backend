To use this module, add a user to the group "Backend user" or "Backend UI user" through the user's form page.

.. figure:: ../static/description/backend_ui.png
    :alt: Backend UI user

If you created a specific group with ``group_backend`` or ``group_backend_ui_users`` in its ``implied_ids``, you need to go through the group's form page in order to add the user to this specific group, because it won't be displayed on the user's form page (a specific group with its own category is displayed on user's form page only if the group inherits the "Internal user" group).

This module also **restricts the root menus** displayed to Backend users, so be sure to explicitly add your Backend group to all the necessary root menus for these users.