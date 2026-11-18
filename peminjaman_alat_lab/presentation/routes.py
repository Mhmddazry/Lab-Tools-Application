"""HTTP routes: translate requests into service calls and render responses."""

from datetime import date

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from business_logic.services import BusinessRuleError, NotFoundError


def create_blueprint(equipment_service, loan_service):
    blueprint = Blueprint(
        "presentation", __name__, template_folder="templates", static_folder="static"
    )

    @blueprint.get("/")
    def home():
        return redirect(url_for("presentation.equipment_list"))

    @blueprint.get("/alat")
    def equipment_list():
        equipment = equipment_service.list_equipment()
        return render_template("equipment_list.html", equipment=equipment)

    @blueprint.post("/alat/tambah")
    def add_equipment():
        try:
            equipment_service.add_equipment(
                request.form.get("name"),
                request.form.get("description"),
                request.form.get("total_stock"),
            )
            flash("Alat berhasil ditambahkan.", "success")
        except BusinessRuleError as error:
            flash(str(error), "error")
        return redirect(url_for("presentation.equipment_list"))

    @blueprint.get("/alat/<int:equipment_id>/ubah")
    def edit_equipment_form(equipment_id):
        equipment = equipment_service.get_equipment(equipment_id)
        if equipment is None:
            abort(404)
        return render_template("equipment_form.html", equipment=equipment)

    @blueprint.post("/alat/<int:equipment_id>/ubah")
    def edit_equipment(equipment_id):
        try:
            equipment_service.update_equipment(
                equipment_id,
                request.form.get("name"),
                request.form.get("description"),
                request.form.get("total_stock"),
            )
            flash("Data alat berhasil diperbarui.", "success")
            return redirect(url_for("presentation.equipment_list"))
        except NotFoundError:
            abort(404)
        except BusinessRuleError as error:
            flash(str(error), "error")
            return redirect(url_for("presentation.edit_equipment_form", equipment_id=equipment_id))

    @blueprint.post("/alat/<int:equipment_id>/hapus")
    def delete_equipment(equipment_id):
        try:
            equipment_service.delete_equipment(equipment_id)
            flash("Alat berhasil dihapus.", "success")
        except NotFoundError:
            abort(404)
        except BusinessRuleError as error:
            flash(str(error), "error")
        return redirect(url_for("presentation.equipment_list"))

    @blueprint.get("/peminjaman")
    def loan_list():
        show_all = request.args.get("view") == "all"
        equipment = equipment_service.list_equipment()
        loans = loan_service.list_loans(include_returned=show_all)
        return render_template(
            "loan_list.html",
            equipment=equipment,
            loans=loans,
            show_all=show_all,
            today=date.today().isoformat(),
        )

    @blueprint.post("/peminjaman/tambah")
    def add_loan():
        try:
            loan_service.create_loan(
                request.form.get("equipment_id"),
                request.form.get("borrower_name"),
                request.form.get("quantity"),
                request.form.get("due_date"),
            )
            flash("Peminjaman berhasil dicatat dan stok tersedia telah diperbarui.", "success")
        except (BusinessRuleError, NotFoundError) as error:
            flash(str(error), "error")
        return redirect(url_for("presentation.loan_list"))

    @blueprint.post("/peminjaman/<int:loan_id>/kembalikan")
    def return_loan(loan_id):
        try:
            loan_service.return_loan(loan_id)
            flash("Pengembalian berhasil dicatat dan stok tersedia telah diperbarui.", "success")
        except (BusinessRuleError, NotFoundError) as error:
            flash(str(error), "error")
        return redirect(url_for("presentation.loan_list"))

    return blueprint
