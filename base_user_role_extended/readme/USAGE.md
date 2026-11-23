To use this module, you need to:

1.  Install this module which depends on `base_user_role`.
2.  Go to **Settings \> Users & Companies \> Roles**.
3.  Create or configure a role by assigning the necessary standard Odoo
    groups to it.
4.  Assign the configured role to a user and ensure it is enabled.
5.  The user's CRUD access to models will now be strictly constrained to
    only the permissions explicitly granted by their active roles,
    ignoring any other direct group memberships.
