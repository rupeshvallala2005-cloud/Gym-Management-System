from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
from datetime import datetime, date


app = FastAPI()


# ---------------- CORS ----------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------- DATABASE ----------------

DATABASE = "gym_management.db"


def get_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def create_tables():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL UNIQUE,
            joining_date TEXT NOT NULL,
            monthly_fee REAL NOT NULL,
            status TEXT DEFAULT 'Pending'
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            member_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            payment_date TEXT NOT NULL,
            status TEXT DEFAULT 'Paid',
            FOREIGN KEY (member_id) REFERENCES members(id)
        )
    """)

    connection.commit()
    connection.close()


create_tables()


# ---------------- MODELS ----------------

class Member(BaseModel):
    name: str
    phone: str
    joining_date: str
    monthly_fee: float


class Payment(BaseModel):
    phone: str
    amount: float


# ---------------- VALIDATION ----------------

def validate_phone(phone):

    phone = str(phone).strip()

    if not phone.isdigit() or len(phone) != 10:
        raise HTTPException(
            status_code=400,
            detail="Invalid mobile number. Please enter exactly 10 digits."
        )

    return phone


def validate_date(joining_date):

    try:
        return datetime.strptime(
            joining_date,
            "%d-%m-%Y"
        ).date()

    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid date. Please use DD-MM-YYYY format."
        )


# ---------------- PAYMENT CALCULATION ----------------

def calculate_member_payment(member_id, joining_date, monthly_fee):

    joining = validate_date(joining_date)
    today = date.today()

    # Calculate completed months since joining
    months_completed = (
        (today.year - joining.year) * 12
        + (today.month - joining.month)
    )

    # If the monthly anniversary has not arrived yet,
    # the current month is not completed.
    if today.day < joining.day:
        months_completed -= 1

    # A member starts with the first month's fee
    months_due = max(1, months_completed + 1)

    total_due = months_due * monthly_fee

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT COALESCE(SUM(amount), 0)
        FROM payments
        WHERE member_id = ?
    """, (member_id,))

    total_paid = cursor.fetchone()[0]

    connection.close()

    pending_amount = max(0, total_due - total_paid)

    if pending_amount <= 0:
        status = "Paid"
    elif total_paid > 0:
        status = "Partially Paid"
    else:
        status = "Pending"

    return {
        "months_due": months_due,
        "total_due": round(total_due, 2),
        "total_paid": round(total_paid, 2),
        "pending_amount": round(pending_amount, 2),
        "status": status
    }


# ---------------- HOME ----------------

@app.get("/")
def home():

    return {
        "message": "Gym Management API is running"
    }


# ---------------- DASHBOARD ----------------

@app.get("/dashboard")
def dashboard():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, joining_date, monthly_fee
        FROM members
    """)

    members = cursor.fetchall()
    connection.close()

    total_members = len(members)

    total_due = 0
    total_paid = 0
    total_pending = 0
    pending_members = 0

    for member in members:

        payment_info = calculate_member_payment(
            member["id"],
            member["joining_date"],
            member["monthly_fee"]
        )

        total_due += payment_info["total_due"]
        total_paid += payment_info["total_paid"]
        total_pending += payment_info["pending_amount"]

        if payment_info["pending_amount"] > 0:
            pending_members += 1

    return {
        "total_members": total_members,
        "total_due": round(total_due, 2),
        "total_collection": round(total_paid, 2),
        "total_pending": round(total_pending, 2),
        "pending_members": pending_members
    }


# ---------------- ADD MEMBER ----------------

@app.post("/members")
def add_member(member: Member):

    phone = validate_phone(member.phone)
    validate_date(member.joining_date)

    if not member.name.strip():
        raise HTTPException(
            status_code=400,
            detail="Member name cannot be empty."
        )

    if member.monthly_fee <= 0:
        raise HTTPException(
            status_code=400,
            detail="Monthly fee must be greater than zero."
        )

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute("""
            INSERT INTO members
            (name, phone, joining_date, monthly_fee, status)
            VALUES (?, ?, ?, ?, ?)
        """, (
            member.name.strip(),
            phone,
            member.joining_date,
            member.monthly_fee,
            "Pending"
        ))

        connection.commit()

    except sqlite3.IntegrityError:

        connection.close()

        raise HTTPException(
            status_code=400,
            detail="A member with this mobile number already exists."
        )

    connection.close()

    return {
        "message": "Member added successfully"
    }


# ---------------- VIEW ALL MEMBERS ----------------

@app.get("/members")
def get_members():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, name, phone, joining_date, monthly_fee
        FROM members
        ORDER BY id DESC
    """)

    rows = cursor.fetchall()
    connection.close()

    members = []

    for row in rows:

        payment_info = calculate_member_payment(
            row["id"],
            row["joining_date"],
            row["monthly_fee"]
        )

        members.append({
            "id": row["id"],
            "name": row["name"],
            "phone": row["phone"],
            "joining_date": row["joining_date"],
            "monthly_fee": row["monthly_fee"],
            "months_due": payment_info["months_due"],
            "total_due": payment_info["total_due"],
            "total_paid": payment_info["total_paid"],
            "pending_amount": payment_info["pending_amount"],
            "status": payment_info["status"]
        })

    return members


# ---------------- SEARCH MEMBER ----------------

@app.get("/members/search/{phone}")
def search_member(phone: str):

    phone = validate_phone(phone)

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, name, phone, joining_date, monthly_fee
        FROM members
        WHERE phone = ?
    """, (phone,))

    row = cursor.fetchone()
    connection.close()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Member not found."
        )

    payment_info = calculate_member_payment(
        row["id"],
        row["joining_date"],
        row["monthly_fee"]
    )

    return {
        "id": row["id"],
        "name": row["name"],
        "phone": row["phone"],
        "joining_date": row["joining_date"],
        "monthly_fee": row["monthly_fee"],
        "months_due": payment_info["months_due"],
        "total_due": payment_info["total_due"],
        "total_paid": payment_info["total_paid"],
        "pending_amount": payment_info["pending_amount"],
        "status": payment_info["status"]
    }


# ---------------- EDIT MEMBER ----------------

@app.put("/members/{member_id}")
def update_member(member_id: int, member: Member):

    phone = validate_phone(member.phone)
    validate_date(member.joining_date)

    if not member.name.strip():
        raise HTTPException(
            status_code=400,
            detail="Member name cannot be empty."
        )

    if member.monthly_fee <= 0:
        raise HTTPException(
            status_code=400,
            detail="Monthly fee must be greater than zero."
        )

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        "SELECT id FROM members WHERE id = ?",
        (member_id,)
    )

    if cursor.fetchone() is None:

        connection.close()

        raise HTTPException(
            status_code=404,
            detail="Member not found."
        )

    cursor.execute("""
        SELECT id FROM members
        WHERE phone = ? AND id != ?
    """, (phone, member_id))

    if cursor.fetchone() is not None:

        connection.close()

        raise HTTPException(
            status_code=400,
            detail="Another member already uses this mobile number."
        )

    cursor.execute("""
        UPDATE members
        SET name = ?,
            phone = ?,
            joining_date = ?,
            monthly_fee = ?
        WHERE id = ?
    """, (
        member.name.strip(),
        phone,
        member.joining_date,
        member.monthly_fee,
        member_id
    ))

    connection.commit()
    connection.close()

    return {
        "message": "Member updated successfully"
    }


# ---------------- RECORD PAYMENT ----------------

@app.post("/payments")
def add_payment(payment: Payment):

    phone = validate_phone(payment.phone)

    if payment.amount <= 0:
        raise HTTPException(
            status_code=400,
            detail="Payment amount must be greater than zero."
        )

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, joining_date, monthly_fee
        FROM members
        WHERE phone = ?
    """, (phone,))

    member = cursor.fetchone()

    if member is None:

        connection.close()

        raise HTTPException(
            status_code=404,
            detail="Member not found."
        )

    member_id = member["id"]

    payment_info = calculate_member_payment(
        member_id,
        member["joining_date"],
        member["monthly_fee"]
    )

    # Do not allow payment more than the pending amount
    if payment.amount > payment_info["pending_amount"]:

        connection.close()

        raise HTTPException(
            status_code=400,
            detail=(
                f"Payment is greater than the pending amount "
                f"(₹{payment_info['pending_amount']})."
            )
        )

    today = date.today().strftime("%d-%m-%Y")

    cursor.execute("""
        INSERT INTO payments
        (member_id, amount, payment_date, status)
        VALUES (?, ?, ?, ?)
    """, (
        member_id,
        payment.amount,
        today,
        "Paid"
    ))

    connection.commit()
    connection.close()

    # Calculate the new balance after payment
    new_payment_info = calculate_member_payment(
        member_id,
        member["joining_date"],
        member["monthly_fee"]
    )

    return {
        "message": "Payment recorded successfully",
        "total_due": new_payment_info["total_due"],
        "total_paid": new_payment_info["total_paid"],
        "pending_amount": new_payment_info["pending_amount"],
        "status": new_payment_info["status"]
    }


# ---------------- PAYMENT HISTORY ----------------

@app.get("/payments/{phone}")
def payment_history(phone: str):

    phone = validate_phone(phone)

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, joining_date, monthly_fee
        FROM members
        WHERE phone = ?
    """, (phone,))

    member = cursor.fetchone()

    if member is None:

        connection.close()

        raise HTTPException(
            status_code=404,
            detail="Member not found."
        )

    cursor.execute("""
        SELECT amount, payment_date, status
        FROM payments
        WHERE member_id = ?
        ORDER BY id DESC
    """, (member["id"],))

    rows = cursor.fetchall()
    connection.close()

    payment_info = calculate_member_payment(
        member["id"],
        member["joining_date"],
        member["monthly_fee"]
    )

    payments = []

    for row in rows:

        payments.append({
            "amount": row["amount"],
            "payment_date": row["payment_date"],
            "status": row["status"]
        })

    return {
        "payments": payments,
        "months_due": payment_info["months_due"],
        "total_due": payment_info["total_due"],
        "total_paid": payment_info["total_paid"],
        "pending_amount": payment_info["pending_amount"],
        "status": payment_info["status"]
    }


# ---------------- PENDING PAYMENTS ----------------

@app.get("/pending-payments")
def get_pending_payments():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, name, phone, joining_date, monthly_fee
        FROM members
        ORDER BY id DESC
    """)

    rows = cursor.fetchall()
    connection.close()

    members = []

    for row in rows:

        payment_info = calculate_member_payment(
            row["id"],
            row["joining_date"],
            row["monthly_fee"]
        )

        if payment_info["pending_amount"] > 0:

            members.append({
                "id": row["id"],
                "name": row["name"],
                "phone": row["phone"],
                "joining_date": row["joining_date"],
                "monthly_fee": row["monthly_fee"],
                "months_due": payment_info["months_due"],
                "total_due": payment_info["total_due"],
                "total_paid": payment_info["total_paid"],
                "pending_amount": payment_info["pending_amount"],
                "status": payment_info["status"]
            })

    return members