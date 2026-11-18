"""SQLite queries. This layer does not decide application or presentation rules."""


def _dict(row):
    return dict(row) if row is not None else None


class EquipmentRepository:
    def __init__(self, database):
        self.database = database

    def list_all(self):
        with self.database.read() as connection:
            rows = connection.execute(
                """SELECT id, name, description, total_stock, available_stock, created_at
                   FROM equipment ORDER BY name COLLATE NOCASE, id"""
            ).fetchall()
            return [_dict(row) for row in rows]

    def get_by_id(self, equipment_id):
        with self.database.read() as connection:
            row = connection.execute(
                """SELECT id, name, description, total_stock, available_stock, created_at
                   FROM equipment WHERE id = ?""",
                (equipment_id,),
            ).fetchone()
            return _dict(row)

    def create(self, name, description, total_stock):
        with self.database.transaction() as connection:
            cursor = connection.execute(
                """INSERT INTO equipment (name, description, total_stock, available_stock)
                   VALUES (?, ?, ?, ?)""",
                (name, description, total_stock, total_stock),
            )
            return cursor.lastrowid

    def update(self, equipment_id, name, description, total_stock):
        with self.database.transaction() as connection:
            cursor = connection.execute(
                """UPDATE equipment
                   SET name = ?, description = ?,
                       available_stock = available_stock + (? - total_stock),
                       total_stock = ?
                   WHERE id = ? AND total_stock - available_stock <= ?""",
                (name, description, total_stock, total_stock, equipment_id, total_stock),
            )
            return cursor.rowcount == 1

    def has_loan_history(self, equipment_id):
        with self.database.read() as connection:
            row = connection.execute(
                "SELECT 1 FROM loan_records WHERE equipment_id = ? LIMIT 1",
                (equipment_id,),
            ).fetchone()
            return row is not None

    def delete_if_without_history(self, equipment_id):
        with self.database.transaction() as connection:
            cursor = connection.execute(
                """DELETE FROM equipment
                   WHERE id = ? AND NOT EXISTS (
                       SELECT 1 FROM loan_records WHERE equipment_id = ?
                   )""",
                (equipment_id, equipment_id),
            )
            return cursor.rowcount == 1


class LoanRepository:
    _SELECT_COLUMNS = """l.id, l.equipment_id, e.name AS equipment_name,
        l.borrower_name, l.quantity, l.loaned_at, l.due_date, l.returned_at, l.status"""

    def __init__(self, database):
        self.database = database

    def list_all(self, include_returned=False):
        query = f"""SELECT {self._SELECT_COLUMNS}
                   FROM loan_records AS l
                   JOIN equipment AS e ON e.id = l.equipment_id"""
        if not include_returned:
            query += " WHERE l.status = 'active'"
        query += " ORDER BY l.id DESC"
        with self.database.read() as connection:
            rows = connection.execute(query).fetchall()
            return [_dict(row) for row in rows]

    def get_by_id(self, loan_id):
        with self.database.read() as connection:
            row = connection.execute(
                f"""SELECT {self._SELECT_COLUMNS}
                    FROM loan_records AS l
                    JOIN equipment AS e ON e.id = l.equipment_id
                    WHERE l.id = ?""",
                (loan_id,),
            ).fetchone()
            return _dict(row)

    def create_loan(self, equipment_id, borrower_name, quantity, due_date):
        with self.database.transaction() as connection:
            cursor = connection.execute(
                """UPDATE equipment SET available_stock = available_stock - ?
                   WHERE id = ? AND available_stock >= ?""",
                (quantity, equipment_id, quantity),
            )
            if cursor.rowcount != 1:
                return None
            cursor = connection.execute(
                """INSERT INTO loan_records
                   (equipment_id, borrower_name, quantity, due_date)
                   VALUES (?, ?, ?, ?)""",
                (equipment_id, borrower_name, quantity, due_date),
            )
            return cursor.lastrowid

    def return_loan(self, loan_id):
        with self.database.transaction() as connection:
            row = connection.execute(
                "SELECT equipment_id, quantity, status FROM loan_records WHERE id = ?",
                (loan_id,),
            ).fetchone()
            if row is None:
                return "not_found"
            if row["status"] != "active":
                return "already_returned"

            cursor = connection.execute(
                """UPDATE loan_records
                   SET status = 'returned', returned_at = CURRENT_TIMESTAMP
                   WHERE id = ? AND status = 'active'""",
                (loan_id,),
            )
            if cursor.rowcount != 1:
                return "already_returned"
            stock_cursor = connection.execute(
                """UPDATE equipment SET available_stock = available_stock + ?
                   WHERE id = ? AND available_stock + ? <= total_stock""",
                (row["quantity"], row["equipment_id"], row["quantity"]),
            )
            if stock_cursor.rowcount != 1:
                raise RuntimeError("Stok alat tidak konsisten saat pengembalian.")
            return "returned"
