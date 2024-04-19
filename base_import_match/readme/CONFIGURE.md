To configure this module, you need to:

1.  Go to *Settings \> Technical \> Database Structure \> Import Match*.
2.  *Create*.
3.  Choose a *Model*.
4.  Choose the *Fields* that conform a unique key in that model.
5.  If the rule must be used only for certain imported values, check
    *Conditional* and enter the **exact string** that is going to be
    imported in *Imported value*.
    1.  Keep in mind that the match here is evaluated as a case
        sensitive **text string** always. If you enter e.g. `True`, it
        will match that string, but will not match `1` or `true`.
6.  *Save*.

In that list view, you can sort rules by drag and drop.
