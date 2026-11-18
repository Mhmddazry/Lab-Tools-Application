"""Application rules and validation. No HTTP or SQL belongs in this layer."""

from datetime import date

from business_logic.entities import Equipment, Loan


class BusinessRuleError(ValueError):
    """Raised when a request conflicts with a system rule or input constraint."""


class NotFoundError(LookupError):
    """Raised when an equipment item or loan does not exist."""


def _positive_id(value, label):
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        raise BusinessRuleError(f"{label} tidak valid.") from None
    if parsed <= 0:
        raise BusinessRuleError(f"{label} tidak valid.")
    return parsed


def _stock_value(value):
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        raise BusinessRuleError("Stok harus berupa bilangan bulat.") from None
    if parsed < 0:
        raise BusinessRuleError("Stok tidak boleh negatif.")
    return parsed


def _quantity_value(value):
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        raise BusinessRuleError("Jumlah pinjam harus berupa bilangan bulat.") from None
    if parsed <= 0:
        raise BusinessRuleError("Jumlah pinjam minimal 1.")
    return parsed


class EquipmentService:
    def __init__(self, repository):
        self.repository = repository

    def list_equipment(self):
        return [Equipment(**row) for row in self.repository.list_all()]

    def get_equipment(self, equipment_id):
        equipment_id = _positive_id(equipment_id, "ID alat")
        row = self.repository.get_by_id(equipment_id)
        return Equipment(**row) if row else None

    def add_equipment(self, name, description, total_stock):
        name = (name or "").strip()
        description = (description or "").strip()
        if not name:
            raise BusinessRuleError("Nama alat wajib diisi.")
        if len(name) > 100:
            raise BusinessRuleError("Nama alat maksimal 100 karakter.")
        if len(description) > 500:
            raise BusinessRuleError("Deskripsi maksimal 500 karakter.")
        total_stock = _stock_value(total_stock)
        equipment_id = self.repository.create(name, description, total_stock)
        return self.get_equipment(equipment_id)

    def update_equipment(self, equipment_id, name, description, total_stock):
        equipment_id = _positive_id(equipment_id, "ID alat")
        current = self.repository.get_by_id(equipment_id)
        if not current:
            raise NotFoundError("Alat tidak ditemukan.")

        name = (name or "").strip()
        description = (description or "").strip()
        if not name:
            raise BusinessRuleError("Nama alat wajib diisi.")
        if len(name) > 100:
            raise BusinessRuleError("Nama alat maksimal 100 karakter.")
        if len(description) > 500:
            raise BusinessRuleError("Deskripsi maksimal 500 karakter.")
        total_stock = _stock_value(total_stock)
        borrowed_stock = current["total_stock"] - current["available_stock"]
        if total_stock < borrowed_stock:
            raise BusinessRuleError(
                f"Stok total tidak boleh kurang dari jumlah yang sedang dipinjam ({borrowed_stock})."
            )

        updated = self.repository.update(equipment_id, name, description, total_stock)
        if not updated:
            latest = self.repository.get_by_id(equipment_id)
            if not latest:
                raise NotFoundError("Alat tidak ditemukan.")
            raise BusinessRuleError("Stok berubah saat data disimpan. Muat ulang halaman lalu coba lagi.")
        return self.get_equipment(equipment_id)

    def delete_equipment(self, equipment_id):
        equipment_id = _positive_id(equipment_id, "ID alat")
        if not self.repository.get_by_id(equipment_id):
            raise NotFoundError("Alat tidak ditemukan.")
        if self.repository.has_loan_history(equipment_id):
            raise BusinessRuleError("Alat yang memiliki riwayat peminjaman tidak dapat dihapus.")
        if not self.repository.delete_if_without_history(equipment_id):
            if not self.repository.get_by_id(equipment_id):
                raise NotFoundError("Alat tidak ditemukan.")
            raise BusinessRuleError("Alat memiliki riwayat peminjaman dan tidak dapat dihapus.")


class LoanService:
    def __init__(self, loan_repository, equipment_repository):
        self.repository = loan_repository
        self.equipment_repository = equipment_repository

    def list_loans(self, include_returned=False):
        rows = self.repository.list_all(include_returned=include_returned)
        return [Loan(**row) for row in rows]

    def create_loan(self, equipment_id, borrower_name, quantity, due_date):
        equipment_id = _positive_id(equipment_id, "Alat")
        borrower_name = (borrower_name or "").strip()
        if not borrower_name:
            raise BusinessRuleError("Nama peminjam wajib diisi.")
        if len(borrower_name) > 100:
            raise BusinessRuleError("Nama peminjam maksimal 100 karakter.")
        quantity = _quantity_value(quantity)
        equipment = self.equipment_repository.get_by_id(equipment_id)
        if not equipment:
            raise NotFoundError("Alat yang dipilih tidak ditemukan.")
        if equipment["available_stock"] < quantity:
            raise BusinessRuleError(
                f"Stok {equipment['name']} tidak mencukupi. Tersedia: {equipment['available_stock']}."
            )

        due_date = (due_date or "").strip()
        try:
            parsed_due_date = date.fromisoformat(due_date)
        except ValueError:
            raise BusinessRuleError("Tanggal jatuh tempo tidak valid.") from None
        if parsed_due_date < date.today():
            raise BusinessRuleError("Tanggal jatuh tempo tidak boleh sebelum hari ini.")

        loan_id = self.repository.create_loan(equipment_id, borrower_name, quantity, due_date)
        if loan_id is None:
            # The repository also checks stock atomically in case another request
            # borrowed the last available item after the service's validation.
            latest = self.equipment_repository.get_by_id(equipment_id)
            available = latest["available_stock"] if latest else 0
            raise BusinessRuleError(
                f"Stok tidak mencukupi. Tersedia saat ini: {available}."
            )
        return self.get_loan(loan_id)

    def return_loan(self, loan_id):
        loan_id = _positive_id(loan_id, "ID peminjaman")
        result = self.repository.return_loan(loan_id)
        if result == "not_found":
            raise NotFoundError("Data peminjaman tidak ditemukan.")
        if result == "already_returned":
            raise BusinessRuleError("Alat pada transaksi ini sudah dikembalikan.")
        return self.get_loan(loan_id)

    def get_loan(self, loan_id):
        row = self.repository.get_by_id(loan_id)
        if not row:
            raise NotFoundError("Data peminjaman tidak ditemukan.")
        return Loan(**row)
