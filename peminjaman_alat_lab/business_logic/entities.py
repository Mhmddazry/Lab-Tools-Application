"""Domain entities shared with the presentation layer."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Equipment:
    id: int
    name: str
    description: str
    total_stock: int
    available_stock: int
    created_at: str


@dataclass(frozen=True)
class Loan:
    id: int
    equipment_id: int
    equipment_name: str
    borrower_name: str
    quantity: int
    loaned_at: str
    due_date: str
    returned_at: str | None
    status: str
