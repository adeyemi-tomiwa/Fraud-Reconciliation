import random
import uuid
import psycopg2
from datetime import datetime, timedelta
from faker import Faker

fake = Faker()

DB_CONFIG = {
    "host": "localhost",
    "dbname": "Fraud Reconciliation",
    "user": "postgres",
    "password": "1234",
    "port": 5432,

}
CHANNELS = ["card", "transfer", "pos", "ussd"]
NUM_CUSTOMERS = 200
NUM_TRANSACTIONS = 5000

MISMATCH_RATE = 0.05
FRAUD_RATE = 0.03


def get_connection():
    return psycopg2.connect(**DB_CONFIG)


def seed_customers(conn, n):
    customer_ids = []
    with conn.cursor() as cur:
        for _ in range(n):
            cur.execute(
                """
                INSERT INTO customers (full_name, account_number, balance)
                VALUES (%s, %s, %s)
                RETURNING customer_id
                """,
                (fake.name(), fake.unique.bban(), round(random.uniform(5000, 500000), 2)),
            )
            customer_ids.append(cur.fetchone()[0])
    conn.commit()
    return customer_ids


def generate_transaction(customer_id, force_fraud=False):
    ref = str(uuid.uuid4())
    amount = round(random.uniform(500, 20000), 2)
    channel = random.choice(CHANNELS)
    txn_type = random.choice(["debit", "credit"])

    if force_fraud:
        # velocity-style fraud: many tiny debits in a burst
        amount = round(random.uniform(50, 500), 2)
        txn_type = "debit"

    return {
        "ref": ref,
        "customer_id": customer_id,
        "amount": amount,
        "type": txn_type,
        "channel": channel,
        "merchant": fake.company(),
    }


def insert_ledger(conn, txn):
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO internal_ledger
            (transaction_ref, customer_id, amount, transaction_type, channel, merchant)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (txn["ref"], txn["customer_id"], txn["amount"], txn["type"], txn["channel"], txn["merchant"]),
        )
    conn.commit()


def insert_gateway(conn, txn, mismatch=False):
    ref = txn["ref"]
    amount = txn["amount"]
    status = "success"

    if mismatch:
        outcome = random.choice(["drop", "duplicate", "amount_shift"])
        if outcome == "drop":
            return  # gateway never receives it
        elif outcome == "duplicate":
            with conn.cursor() as cur:
                for _ in range(2):
                    cur.execute(
                        """
                        INSERT INTO gateway_transactions (transaction_ref, amount, gateway_status)
                        VALUES (%s, %s, %s)
                        """,
                        (ref, amount, "success"),
                    )
            conn.commit()
            return
        elif outcome == "amount_shift":
            amount = round(amount + random.uniform(10, 100), 2)

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO gateway_transactions (transaction_ref, amount, gateway_status)
            VALUES (%s, %s, %s)
            """,
            (ref, amount, status),
        )
    conn.commit()


def main():
    conn = get_connection()
    customer_ids = seed_customers(conn, NUM_CUSTOMERS)

    for _ in range(NUM_TRANSACTIONS):
        customer_id = random.choice(customer_ids)
        force_fraud = random.random() < FRAUD_RATE
        mismatch = random.random() < MISMATCH_RATE

        txn = generate_transaction(customer_id, force_fraud)
        insert_ledger(conn, txn)
        insert_gateway(conn, txn, mismatch)

    conn.close()
    print(f"Inserted {NUM_TRANSACTIONS} transactions for {NUM_CUSTOMERS} customers.")


if __name__ == "__main__":
    main()

