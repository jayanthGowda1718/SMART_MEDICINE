"""Sanity test for _sweep_repeat_alerts exact-message dedupe."""
import os
import sys
from datetime import datetime, timedelta

# 1-min realert window for this test run
os.environ["REMINDER_REALERT_INTERVAL_MINUTES"] = "1"
os.environ["MISSED_DOSE_GRACE_MINUTES"] = "30"

from app import get_db_connection, _sweep_repeat_alerts, REALERT_INTERVAL_MINUTES, GRACE_MINUTES

TEST_PREFIX = "__dedupe_test__"


def count_reminders(cursor, user_id, message=None):
    if message:
        cursor.execute(
            """
            SELECT COUNT(*) FROM Notifications
            WHERE user_id=%s AND type='reminder' AND message=%s
            """,
            (user_id, message),
        )
    else:
        cursor.execute(
            """
            SELECT COUNT(*) FROM Notifications
            WHERE user_id=%s AND type='reminder' AND message LIKE %s
            """,
            (user_id, f"{TEST_PREFIX}%"),
        )
    return cursor.fetchone()[0]


def cleanup(cursor, conn, user_id):
    cursor.execute(
        "DELETE FROM Notifications WHERE user_id=%s AND message LIKE %s",
        (user_id, f"Reminder: please take {TEST_PREFIX}%"),
    )
    cursor.execute(
        "DELETE FROM IntakeLogs WHERE user_id=%s AND medicine_id IN "
        "(SELECT id FROM Medicines WHERE name LIKE %s)",
        (user_id, f"{TEST_PREFIX}%"),
    )
    cursor.execute("DELETE FROM Medicines WHERE user_id=%s AND name LIKE %s", (user_id, f"{TEST_PREFIX}%"))
    conn.commit()


def main():
    print(f"REALERT_INTERVAL_MINUTES={REALERT_INTERVAL_MINUTES}, GRACE_MINUTES={GRACE_MINUTES}")
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM Users LIMIT 1")
    row = cursor.fetchone()
    if not row:
        print("FAIL: no Users row in DB — create a user first")
        sys.exit(1)
    user_id = row[0]

    cleanup(cursor, conn, user_id)

    meds = [
        (f"{TEST_PREFIX}Metformin", "500mg"),
        (f"{TEST_PREFIX}Metformin XR", "750mg"),
    ]
    med_ids = []
    for name, dosage in meds:
        cursor.execute(
            "INSERT INTO Medicines (user_id, name, dosage) VALUES (%s, %s, %s)",
            (user_id, name, dosage),
        )
        med_ids.append(cursor.lastrowid)

    scheduled = datetime.now() - timedelta(minutes=2)
    for mid in med_ids:
        cursor.execute(
            """
            INSERT INTO IntakeLogs (user_id, medicine_id, scheduled_time, status)
            VALUES (%s, %s, %s, 'pending')
            """,
            (user_id, mid, scheduled),
        )
    conn.commit()

    msg_a = f"Reminder: please take {TEST_PREFIX}Metformin (500mg)"
    msg_b = f"Reminder: please take {TEST_PREFIX}Metformin XR (750mg)"

    # Tick 1: both pending doses should each get a re-alert
    _sweep_repeat_alerts()
    n1_a = count_reminders(cursor, user_id, msg_a)
    n1_b = count_reminders(cursor, user_id, msg_b)
    print(f"After tick 1: Metformin={n1_a}, Metformin XR={n1_b}")

    # Tick 2 (within 1-min window): dedupe — no new rows
    _sweep_repeat_alerts()
    n2_a = count_reminders(cursor, user_id, msg_a)
    n2_b = count_reminders(cursor, user_id, msg_b)
    print(f"After tick 2: Metformin={n2_a}, Metformin XR={n2_b}")

    # Expire only Metformin XR's recent notification (>1 min ago)
    cursor.execute(
        """
        UPDATE Notifications SET sent_time=%s
        WHERE user_id=%s AND message=%s
        ORDER BY sent_time DESC LIMIT 1
        """,
        (datetime.now() - timedelta(minutes=2), user_id, msg_b),
    )
    conn.commit()

    # Tick 3: Metformin still deduped; Metformin XR should fire again
    _sweep_repeat_alerts()
    n3_a = count_reminders(cursor, user_id, msg_a)
    n3_b = count_reminders(cursor, user_id, msg_b)
    print(f"After tick 3: Metformin={n3_a}, Metformin XR={n3_b}")

    cleanup(cursor, conn, user_id)
    cursor.close()
    conn.close()

    ok = (
        n1_a == 1 and n1_b == 1
        and n2_a == 1 and n2_b == 1
        and n3_a == 1 and n3_b == 2
    )
    if ok:
        print("\nPASS: exact-message dedupe works; similar names do not collide.")
        sys.exit(0)
    else:
        print("\nFAIL: unexpected notification counts — see above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
