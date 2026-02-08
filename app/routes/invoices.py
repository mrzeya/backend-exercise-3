from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional

from app.database import get_db

router = APIRouter(prefix="/invoices", tags=["invoices"])


class InvoiceItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(..., gt=0)


class InvoiceCreate(BaseModel):
    # invoice_no should be optional; set default to None so Pydantic does not treat it as required
    invoice_no: Optional[str] = None
    issue_date: str
    due_date: str
    client_id: int
    address: Optional[str]
    items: List[InvoiceItemCreate]
    tax: float = 0.0


class InvoiceItemResponse(BaseModel):
    id: int
    product_id: int
    product_name: str
    quantity: int
    unit_price: float
    line_total: float


class InvoiceResponse(BaseModel):
    id: int
    invoice_no: str
    issue_date: str
    due_date: str
    client_id: int
    address: Optional[str]
    tax: float
    total: float
    items: List[InvoiceItemResponse]


def _generate_invoice_no(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(1) as cnt FROM invoices")
    row = cursor.fetchone()
    cnt = row["cnt"] if row else 0
    return f"INV-{cnt + 1:05d}"


@router.post("", status_code=201, response_model=InvoiceResponse)
def create_invoice(payload: InvoiceCreate):
    try:
        with get_db() as conn:
            cursor = conn.cursor()

            # Validate client exists
            cursor.execute("SELECT id FROM clients WHERE id = ?", (payload.client_id,))
            if cursor.fetchone() is None:
                raise HTTPException(status_code=400, detail="Client not found")

            invoice_no = payload.invoice_no or _generate_invoice_no(conn)

            # Insert invoice
            cursor.execute(
                "INSERT INTO invoices (invoice_no, issue_date, due_date, client_id, address, tax, total) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (invoice_no, payload.issue_date, payload.due_date, payload.client_id, payload.address, payload.tax, 0.0),
            )
            invoice_id = cursor.lastrowid

            total = 0.0
            items_resp = []

            for item in payload.items:
                # get product price
                cursor.execute("SELECT id, name, price FROM products WHERE id = ?", (item.product_id,))
                prod = cursor.fetchone()
                if prod is None:
                    raise HTTPException(status_code=400, detail=f"Product {item.product_id} not found")

                unit_price = float(prod["price"])
                line_total = unit_price * item.quantity
                total += line_total

                cursor.execute(
                    "INSERT INTO invoice_items (invoice_id, product_id, quantity, unit_price, line_total) VALUES (?, ?, ?, ?, ?)",
                    (invoice_id, item.product_id, item.quantity, unit_price, line_total),
                )
                item_id = cursor.lastrowid
                items_resp.append(
                    {
                        "id": item_id,
                        "product_id": prod["id"],
                        "product_name": prod["name"],
                        "quantity": item.quantity,
                        "unit_price": unit_price,
                        "line_total": line_total,
                    }
                )

            # apply tax
            total_with_tax = total + payload.tax

            cursor.execute("UPDATE invoices SET total = ? WHERE id = ?", (total_with_tax, invoice_id))

            return {
                "id": invoice_id,
                "invoice_no": invoice_no,
                "issue_date": payload.issue_date,
                "due_date": payload.due_date,
                "client_id": payload.client_id,
                "address": payload.address,
                "tax": payload.tax,
                "total": total_with_tax,
                "items": items_resp,
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("")
def list_invoices():
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, invoice_no, issue_date, due_date, client_id, address, tax, total FROM invoices ORDER BY id DESC"
            )
            rows = cursor.fetchall()
            invoices = []
            for row in rows:
                invoices.append(
                    {
                        "id": row["id"],
                        "invoice_no": row["invoice_no"],
                        "issue_date": row["issue_date"],
                        "due_date": row["due_date"],
                        "client_id": row["client_id"],
                        "address": row["address"],
                        "tax": row["tax"],
                        "total": row["total"],
                    }
                )
            return {"invoices": invoices}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/{invoice_id}", response_model=InvoiceResponse)
def get_invoice(invoice_id: int):
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, invoice_no, issue_date, due_date, client_id, address, tax, total FROM invoices WHERE id = ?",
                (invoice_id,),
            )
            inv = cursor.fetchone()
            if inv is None:
                raise HTTPException(status_code=404, detail="Invoice not found")

            cursor.execute(
                "SELECT ii.id, ii.product_id, p.name as product_name, ii.quantity, ii.unit_price, ii.line_total FROM invoice_items ii JOIN products p ON ii.product_id = p.id WHERE ii.invoice_id = ?",
                (invoice_id,),
            )
            items = [
                {
                    "id": r["id"],
                    "product_id": r["product_id"],
                    "product_name": r["product_name"],
                    "quantity": r["quantity"],
                    "unit_price": r["unit_price"],
                    "line_total": r["line_total"],
                }
                for r in cursor.fetchall()
            ]

            return {
                "id": inv["id"],
                "invoice_no": inv["invoice_no"],
                "issue_date": inv["issue_date"],
                "due_date": inv["due_date"],
                "client_id": inv["client_id"],
                "address": inv["address"],
                "tax": inv["tax"],
                "total": inv["total"],
                "items": items,
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.delete("/{invoice_id}", status_code=204)
def delete_invoice(invoice_id: int):
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM invoices WHERE id = ?", (invoice_id,))
            if cursor.fetchone() is None:
                raise HTTPException(status_code=404, detail="Invoice not found")

            cursor.execute("DELETE FROM invoice_items WHERE invoice_id = ?", (invoice_id,))
            cursor.execute("DELETE FROM invoices WHERE id = ?", (invoice_id,))
            return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/products")
def list_products():
    """List seeded products (helper for testing)."""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, price FROM products ORDER BY id")
            rows = cursor.fetchall()
            products = [{"id": r["id"], "name": r["name"], "price": r["price"]} for r in rows]
            return {"products": products}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/clients")
def list_clients():
    """List seeded clients (helper for testing)."""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, address, registration_no FROM clients ORDER BY id")
            rows = cursor.fetchall()
            clients = [
                {"id": r["id"], "name": r["name"], "address": r["address"], "registration_no": r["registration_no"]}
                for r in rows
            ]
            return {"clients": clients}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
