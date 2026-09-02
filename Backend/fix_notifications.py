import io

path = "app.py"
with io.open(path, "r", encoding="utf-8") as f:
    content = f.read()

old_post = '''@app.route('/notifications', methods=['POST'])
def add_notification():
    data, error = validate_json(['user_id', 'message', 'type'])
    if error: return error
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Notifications (user_id, message, type)
            VALUES (%s, %s, %s)
        """, (data['user_id'], data['message'], data['type']))
        conn.commit()
        return {'message': 'Notification added successfully'}, 201
    except Exception as e:
        return {'error': str(e)}, 500
    finally:'''

new_post = '''@app.route('/notifications', methods=['POST'])
def add_notification():
    data, error = validate_json(['user_id', 'message', 'type'])
    if error: return error
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        if data.get('sent_time'):
            cursor.execute("""
                INSERT INTO Notifications (user_id, message, type, sent_time)
                VALUES (%s, %s, %s, %s)
            """, (data['user_id'], data['message'], data['type'], data['sent_time']))
        else:
            cursor.execute("""
                INSERT INTO Notifications (user_id, message, type)
                VALUES (%s, %s, %s)
            """, (data['user_id'], data['message'], data['type']))
        conn.commit()
        return {'message': 'Notification added successfully'}, 201
    except Exception as e:
        return {'error': str(e)}, 500
    finally:'''

old_get = '''        cursor.execute("""
            SELECT id, user_id, message, sent_time, type
            FROM Notifications
            WHERE user_id=%s
            ORDER BY sent_time DESC
        """, (user_id,))'''

new_get = '''        cursor.execute("""
            SELECT id, user_id, message, sent_time, type
            FROM Notifications
            WHERE user_id=%s AND sent_time <= NOW()
            ORDER BY sent_time DESC
        """, (user_id,))'''

changed = 0
if old_post in content:
    content = content.replace(old_post, new_post)
    changed += 1
    print("POST route: REPLACED")
else:
    print("POST route: NOT FOUND")

if old_get in content:
    content = content.replace(old_get, new_get)
    changed += 1
    print("GET route: REPLACED")
else:
    print("GET route: NOT FOUND")

if changed:
    with io.open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Saved app.py with {changed} change(s).")
else:
    print("Nothing changed.")