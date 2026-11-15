import unittest

from app import create_app
from varasto import Varasto


class TestWarehouseApp(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.warehouses = self.app.extensions["warehouses"]

    def test_index_displays_empty_state(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"No warehouses yet", response.data)
        self.assertIn(b"Create a warehouse", response.data)

    def test_create_warehouse_and_display_capacity(self):
        response = self.client.post(
            "/warehouses", data={"name": "North depot", "capacity": "25"}
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(self.warehouses), 1)
        self.assertEqual(self.warehouses[0].nimi, "North depot")
        self.assertEqual(self.warehouses[0].tilavuus, 25)
        page = self.client.get("/")
        self.assertIn(b"North depot", page.data)
        self.assertIn(b"25", page.data)

    def test_reject_invalid_duplicate_and_non_finite_warehouse_capacity(self):
        for name, capacity in (("", "10"), ("Depot", "0"), ("Depot", "NaN")):
            with self.subTest(name=name, capacity=capacity):
                self.client.post("/warehouses", data={"name": name, "capacity": capacity})
        self.client.post("/warehouses", data={"name": "Depot", "capacity": "10"})
        self.client.post("/warehouses", data={"name": " depot ", "capacity": "20"})

        self.assertEqual(len(self.warehouses), 1)
        page = self.client.get("/")
        self.assertIn(b"greater than zero", page.data)
        self.assertIn(b"already exists", page.data)

    def test_add_and_take_items_within_available_stock(self):
        self.warehouses.append(Varasto(10, nimi="Depot"))

        add_response = self.client.post("/warehouses/0/add", data={"quantity": "6"})
        self.assertEqual(add_response.status_code, 302)
        self.assertEqual(self.warehouses[0].saldo, 6)

        take_response = self.client.post("/warehouses/0/take", data={"quantity": "2"})
        self.assertEqual(take_response.status_code, 302)
        self.assertEqual(self.warehouses[0].saldo, 4)

    def test_reject_addition_over_capacity_and_take_over_stock(self):
        self.warehouses.append(Varasto(5, 3, "Depot"))
        self.client.post("/warehouses/0/add", data={"quantity": "3"})
        self.assertEqual(self.warehouses[0].saldo, 3)
        self.client.post("/warehouses/0/take", data={"quantity": "4"})
        self.assertEqual(self.warehouses[0].saldo, 3)
        page = self.client.get("/")
        self.assertIn(b"Not enough capacity", page.data)
        self.assertIn(b"Not enough items", page.data)

    def test_reject_invalid_quantities_and_unknown_warehouse(self):
        self.warehouses.append(Varasto(5, nimi="Depot"))
        self.client.post("/warehouses/0/add", data={"quantity": "invalid"})
        self.client.post("/warehouses/0/take", data={"quantity": "NaN"})
        self.client.post("/warehouses/3/add", data={"quantity": "1"})

        self.assertEqual(self.warehouses[0].saldo, 0)
        page = self.client.get("/")
        self.assertIn(b"Quantity must be a number", page.data)
        self.assertIn(b"Warehouse not found", page.data)


if __name__ == "__main__":
    unittest.main()
