import math

from flask import Flask, flash, redirect, render_template, request, url_for

# pylint: disable=too-many-statements,redefined-outer-name
try:
    from .varasto import Varasto
except ImportError:
    from varasto import Varasto


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "warehouse-app"
    warehouses = []
    app.extensions["warehouses"] = warehouses

    @app.get("/")
    def index():
        return render_template("index.html", warehouses=warehouses)

    @app.post("/warehouses")
    def create_warehouse():
        name = request.form.get("name", "").strip()
        capacity_text = request.form.get("capacity", "").strip()

        try:
            capacity = float(capacity_text)
        except ValueError:
            capacity = 0

        if not name:
            flash("Enter a warehouse name.", "error")
        elif any(
            warehouse.nimi.casefold() == name.casefold()
            for warehouse in warehouses
        ):
            flash("A warehouse with that name already exists.", "error")
        elif not math.isfinite(capacity) or capacity <= 0:
            flash("Capacity must be a number greater than zero.", "error")
        else:
            warehouses.append(Varasto(capacity, nimi=name))
            flash(f"{name} was created.", "success")

        return redirect(url_for("index"))

    @app.post("/warehouses/<int:warehouse_id>/add")
    def add_items(warehouse_id):
        return update_stock(warehouse_id, "add")

    @app.post("/warehouses/<int:warehouse_id>/take")
    def take_items(warehouse_id):
        return update_stock(warehouse_id, "take")

    def update_stock(warehouse_id, operation):
        if warehouse_id >= len(warehouses):
            flash("Warehouse not found.", "error")
            return redirect(url_for("index"))

        quantity_text = request.form.get("quantity", "").strip()
        try:
            quantity = float(quantity_text)
        except ValueError:
            quantity = 0

        if not math.isfinite(quantity) or quantity <= 0:
            flash("Quantity must be a number greater than zero.", "error")
            return redirect(url_for("index"))

        warehouse = warehouses[warehouse_id]
        if operation == "add":
            if quantity > warehouse.paljonko_mahtuu():
                flash(f"Not enough capacity in {warehouse.nimi}.", "error")
            else:
                warehouse.lisaa_varastoon(quantity)
                flash(f"Added {quantity:g} to {warehouse.nimi}.", "success")
        elif quantity > warehouse.saldo:
            flash(f"Not enough items in {warehouse.nimi}.", "error")
        else:
            warehouse.ota_varastosta(quantity)
            flash(f"Took {quantity:g} from {warehouse.nimi}.", "success")

        return redirect(url_for("index"))

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
