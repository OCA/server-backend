from odoo.tests.common import TransactionCase


class TestModule(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.config = cls.env.ref("polars_db_process.sqlite_chinook")

    def test_connexion_sqlite_success(self):
        self.assertEqual(self.config.test_connexion()["params"]["type"], "success")

    def test_connexion_sqlite_fail(self):
        self.config.string_connexion = "sqlite"
        self.assertEqual(self.config.test_connexion()["params"]["type"], "warning")
