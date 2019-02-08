To configure this module, you need to:

#. Go to *Settings > Technical > Database Structure > Import Match*.
#. *Create*.
#. Choose a *Model*.
#. Choose the *Fields* that conform a unique key in that model.
#. If the rule must be used only for certain imported values, check
   *Conditional* and enter the **exact string** that is going to be imported
   in *Imported value*.

   #. Keep in mind that the match here is evaluated as a case sensitive
      **text string** always. If you enter e.g. ``True``, it will match that
      string, but will not match ``1`` or ``true``.
#. *Save*.

In that list view, you can sort rules by drag and drop.
