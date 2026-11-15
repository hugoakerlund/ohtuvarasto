import math
import os
from functools import partial

from flask import Flask, flash, redirect, render_template, request, url_for

from varasto import Varasto


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = (
        os.environ.get("FLASK_SECRET_KEY") or os.urandom(32)
    )
    varastot = []
    app.extensions["varastot"] = varastot

    rekisteroi_reitit(app, varastot)
    return app


def rekisteroi_reitit(app, varastot):
    app.add_url_rule("/", view_func=partial(index, varastot), endpoint="index")
    app.add_url_rule(
        "/varastot",
        view_func=partial(luo_varasto, varastot),
        methods=["POST"],
        endpoint="create_warehouse",
    )
    app.add_url_rule(
        "/varastot/<int:varasto_id>/lisaa",
        view_func=partial(lisaa_tuotteita, varastot),
        methods=["POST"],
        endpoint="add_items",
    )
    app.add_url_rule(
        "/varastot/<int:varasto_id>/ota",
        view_func=partial(ota_tuotteita, varastot),
        methods=["POST"],
        endpoint="take_items",
    )


def index(varastot):
    return render_template("index.html", varastot=varastot)


def luo_varasto(varastot):
    name = request.form.get("name", "").strip()
    capacity = lue_luku("capacity")
    virhe = tarkista_varasto(name, capacity, varastot)
    if virhe:
        flash(virhe, "error")
    else:
        varastot.append(Varasto(capacity, nimi=name))
        flash(f"Varasto {name} luotiin.", "success")

    return redirect(url_for("index"))


def lisaa_tuotteita(varastot, varasto_id):
    return paivita_saldo(varastot, varasto_id, "lisaa")


def ota_tuotteita(varastot, varasto_id):
    return paivita_saldo(varastot, varasto_id, "ota")


def paivita_saldo(varastot, varasto_id, toiminto):
    varasto = hae_varasto(varastot, varasto_id)
    quantity = lue_luku("quantity")
    if varasto is None:
        return redirect(url_for("index"))
    if not luku_on_positiivinen(quantity):
        flash("Määrän on oltava positiivinen luku.", "error")
        return redirect(url_for("index"))

    if toiminto == "lisaa":
        lisaa_varastoon(varasto, quantity)
    else:
        ota_varastosta(varasto, quantity)

    return redirect(url_for("index"))


def hae_varasto(varastot, varasto_id):
    if varasto_id >= len(varastot):
        flash("Varastoa ei löytynyt.", "error")
        return None
    return varastot[varasto_id]


def lisaa_varastoon(varasto, quantity):
    if quantity > varasto.paljonko_mahtuu():
        flash(f"Varastossa {varasto.nimi} ei ole tarpeeksi tilaa.", "error")
    else:
        varasto.lisaa_varastoon(quantity)
        flash(f"Lisättiin {quantity:g} varastoon {varasto.nimi}.", "success")


def ota_varastosta(varasto, quantity):
    if quantity > varasto.saldo:
        flash(f"Varastossa {varasto.nimi} ei ole tarpeeksi tuotteita.", "error")
    else:
        varasto.ota_varastosta(quantity)
        flash(f"Varastosta {varasto.nimi} otettiin {quantity:g}.", "success")


def lue_luku(kentta):
    try:
        return float(request.form.get(kentta, "").strip())
    except ValueError:
        return 0


def tarkista_varasto(name, capacity, varastot):
    if not name:
        return "Anna varaston nimi."
    if any(
        warehouse.nimi.casefold() == name.casefold() for warehouse in varastot
    ):
        return "Samanniminen varasto on jo olemassa."
    if not luku_on_positiivinen(capacity):
        return "Tilavuuden on oltava positiivinen luku."
    return None


def luku_on_positiivinen(value):
    return math.isfinite(value) and value > 0


if __name__ == "__main__":
    create_app().run(debug=True)
