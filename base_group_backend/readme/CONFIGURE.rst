To allow `group_backend` to interact with a model you can either add access rules to the group
or you can add `implied_ids` to `group_backend`.

.. note::

   Be aware users can only belong to one group from the user type category
   (`base.module_category_user_type`). So your other groups can't inherit both
   internal users and backend users.
