Extending the base_user_role module, this one adds the notion of profiles. Effectively profiles act as an additional filter to how the roles are used. Through the new widget, much in the same way that a user can switch companies when they are part of the multi company group, users have the possibility to change profiles when they are part of the multi profiles group.

This allows users to switch their permission groups dynamically. This can be useful for example to:
 - finer grain control on menu and model permissions (with record rules this becomes very flexible)
 - break down complicated menus into simpler ones
 - easily restrict users accidentally editing or creating records in O2M fields and in general misusing the interface, instead of excessively explaining things to them

When you define a role, you have the possibility to link it to a profile. Roles are applied to users in the following way:
  - Apply user's roles without profiles in any case
  - Apply user's roles that are linked to the currently selected profile

Note that this module assumes a multicompany environment
