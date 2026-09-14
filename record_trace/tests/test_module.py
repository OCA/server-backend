from odoo.tests import TransactionCase


class TestRecordTrace(TransactionCase):
    def _track(self, model):
        ir_model = self.env["ir.model"].search([("model", "=", model)])
        if ir_model:
            ir_model.track_deletions = True

    def _create_and_unlink(self, model="res.partner.category", vals=None, **kwargs):
        env = self.env[model].with_context(**kwargs)
        rec = env.create(vals or {"name": "Trace Test"})
        env.browse([rec.id]).unlink()
        return rec.id

    def test_unlink_creates_trace(self):
        """Deleting a tracked record leaves one trace."""
        self._track("res.partner.category")
        res_id = self._create_and_unlink()
        trace = self.env["record.trace"].search(
            [("model", "=", "res.partner.category"), ("res_id", "=", res_id)]
        )
        self.assertEqual(len(trace), 1)
        self.assertEqual(trace.name, "Trace Test")
        self.assertTrue(trace.user_id)

    def test_batch_unlink_traces_every_record(self):
        """One trace per record of a batch unlink."""
        self._track("res.partner.category")
        model = self.env["res.partner.category"]
        recs = model.create([{"name": "Batch A"}, {"name": "Batch B"}])
        ids = recs.ids
        model.browse(ids).unlink()
        traces = self.env["record.trace"].search(
            [
                ("model", "=", "res.partner.category"),
                ("res_id", "in", ids),
            ]
        )
        self.assertEqual(len(traces), 2)

    def test_no_trace_if_model_not_tracked(self):
        """A model without track_deletions is not traced."""
        res_id = self._create_and_unlink()
        trace = self.env["record.trace"].search(
            [("model", "=", "res.partner.category"), ("res_id", "=", res_id)]
        )
        self.assertFalse(trace)

    def test_no_trace_for_excluded_model(self):
        """Excluded technical models are not traced even if flagged."""
        self._track("res.users.log")
        log = self.env["res.users.log"].create({})
        self.env["res.users.log"].browse([log.id]).unlink()
        trace = self.env["record.trace"].search(
            [("model", "=", "res.users.log"), ("res_id", "=", log.id)]
        )
        self.assertFalse(trace)

    def test_no_trace_with_context_flag(self):
        """`no_record_trace` context disables the tracing."""
        self._track("res.partner.category")
        res_id = self._create_and_unlink(no_record_trace=True)
        trace = self.env["record.trace"].search(
            [("model", "=", "res.partner.category"), ("res_id", "=", res_id)]
        )
        self.assertFalse(trace)
