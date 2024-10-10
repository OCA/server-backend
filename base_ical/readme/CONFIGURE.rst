To configure this module, you need to:

#. Go to Settings/Technical/iCalendars
#. Create a iCalendar, fill in the model you want to expose and possibly a domain to restrict records. You can use the ``user`` variable to restrict things relative to the user using the iCalendar
#. A iCalendar is only available to the allowed users. Use the `Allow automatically` to make the iCalendar available to all users
#. See the examples below for a start

Examples
~~~~~~~~

Simple example, for model ``calendar.event``, you'd fill in ``record.allday and record.start_date or record.start`` as `DTSTART` and ``record.allday and record.stop_date or record.stop`` as `DTEND`.

Advanced example, for model ``calendar.event``, you'd use ``calendar = record._get_ics_file()`` in the code.

Advanced example, for model ``hr.leave``, you can use the following code and ``[("employee_id.user_id", "=", user.id)]`` in the `domain` to export the own time offs. This is a bit more complex because of the way Odoo handles the begin and end times of leaves, and you'll want the extra day as most clients interpret the end date as non-inclusive.:

.. code-block:: python

   confirmed = ("validate", "validate1")
   if record.request_unit_half or record.request_unit_hours:
      event = {
         "dtstart": event["dtstart"].date(),
         "dtend": event["dtend"].date() + timedelta(days=1),
      }
   else:
     event = {
         "dtstart": record.date_from,
         "dtend": record.date_to,
      }

   event["summary"] = record.name
   event["status"] = "CONFIRMED" if record.state in confirmed else "TENTATIVE"

Advanced example, for model ``mail.activity``, you can use the following code and ``[("user_id", "=", user.id)]`` and `domain` to export all user activities.

.. code-block:: python

   todo = {
      "summary": record.display_name,
      "due": record.date_deadline,
      "description": html2plaintext(record.note) if record.note else ""
   }
