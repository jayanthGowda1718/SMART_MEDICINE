import io

path = "app.py"
with io.open(path, "r", encoding="utf-8") as f:
    content = f.read()

anchor = "if __name__ == '__main__':"

new_routes = '''
# ============================================================
# DOCTOR MESSAGING
# ============================================================

@app.route('/messages', methods=['GET'])
@login_required
def get_messages():
    other_user_id = request.args.get('with_user_id')
    if not other_user_id:
        return {'error': 'with_user_id required'}, 400
    session_user_id = session.get('user_id')
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id FROM PatientDoctorLinks
            WHERE (patient_id=%s AND doctor_id=%s) OR (patient_id=%s AND doctor_id=%s)
        """, (session_user_id, other_user_id, other_user_id, session_user_id))
        if not cursor.fetchone():
            return {'error': 'Forbidden: not linked to this user'}, 403

        cursor.execute("""
            SELECT id, sender_id, receiver_id, message, sent_at, is_read
            FROM Messages
            WHERE (sender_id=%s AND receiver_id=%s) OR (sender_id=%s AND receiver_id=%s)
            ORDER BY sent_at ASC
        """, (session_user_id, other_user_id, other_user_id, session_user_id))
        messages = [
            {'id': r[0], 'sender_id': r[1], 'receiver_id': r[2], 'message': r[3],
             'sent_at': str(r[4]), 'is_read': bool(r[5])}
            for r in cursor.fetchall()
        ]
        return jsonify(messages)
    except Exception as e:
        return {'error': str(e)}, 500
    finally:
        cursor.close(); conn.close()


@app.route('/messages', methods=['POST'])
@login_required
def send_message():
    data, error = validate_json(['receiver_id', 'message'])
    if error: return error
    session_user_id = session.get('user_id')
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id FROM PatientDoctorLinks
            WHERE (patient_id=%s AND doctor_id=%s) OR (patient_id=%s AND doctor_id=%s)
        """, (session_user_id, data['receiver_id'], data['receiver_id'], session_user_id))
        if not cursor.fetchone():
            return {'error': 'Forbidden: not linked to this user'}, 403

        cursor.execute("""
            INSERT INTO Messages (sender_id, receiver_id, message)
            VALUES (%s, %s, %s)
        """, (session_user_id, data['receiver_id'], data['message']))
        conn.commit()
        return {'message': 'Message sent'}, 201
    except Exception as e:
        return {'error': str(e)}, 500
    finally:
        cursor.close(); conn.close()


@app.route('/my-conversations', methods=['GET'])
@login_required
def get_my_conversations():
    session_user_id = session.get('user_id')
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.id, u.name, u.role
            FROM PatientDoctorLinks l
            JOIN Users u ON u.id = l.doctor_id
            WHERE l.patient_id = %s
            UNION
            SELECT u.id, u.name, u.role
            FROM PatientDoctorLinks l
            JOIN Users u ON u.id = l.patient_id
            WHERE l.doctor_id = %s
        """, (session_user_id, session_user_id))
        people = [{'id': r[0], 'name': r[1], 'role': r[2]} for r in cursor.fetchall()]
        return jsonify(people)
    except Exception as e:
        return {'error': str(e)}, 500
    finally:
        cursor.close(); conn.close()


# ============================================================
# APPOINTMENTS
# ============================================================

@app.route('/appointments', methods=['POST'])
@login_required
def request_appointment():
    data, error = validate_json(['patient_id', 'doctor_id', 'requested_date', 'requested_time'])
    if error: return error
    if not is_authorized_for_user(data['patient_id']):
        return {'error': 'Forbidden: not your data'}, 403
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM Users WHERE id=%s AND role='doctor'", (data['doctor_id'],))
        if not cursor.fetchone():
            return {'error': 'Selected user is not a doctor'}, 400

        cursor.execute("""
            INSERT INTO Appointments (patient_id, doctor_id, requested_date, requested_time, notes)
            VALUES (%s, %s, %s, %s, %s)
        """, (data['patient_id'], data['doctor_id'], data['requested_date'],
              data['requested_time'], data.get('notes')))
        conn.commit()
        return {'message': 'Appointment requested'}, 201
    except Exception as e:
        return {'error': str(e)}, 500
    finally:
        cursor.close(); conn.close()


@app.route('/my-appointments', methods=['GET'])
@login_required
def get_my_appointments():
    user_id = request.args.get('user_id')
    if not user_id:
        return {'error': 'User ID required'}, 400
    session_user_id = session.get('user_id')
    session_role = session.get('user_role')
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        if session_role == 'doctor' and int(user_id) == session_user_id:
            cursor.execute("""
                SELECT a.id, a.patient_id, a.doctor_id, a.requested_date, a.requested_time,
                       a.notes, a.status, p.name AS patient_name
                FROM Appointments a
                JOIN Users p ON p.id = a.patient_id
                WHERE a.doctor_id = %s
                ORDER BY a.requested_date, a.requested_time
            """, (user_id,))
        else:
            if not is_authorized_for_user(user_id):
                return {'error': 'Forbidden: not your data'}, 403
            cursor.execute("""
                SELECT a.id, a.patient_id, a.doctor_id, a.requested_date, a.requested_time,
                       a.notes, a.status, d.name AS doctor_name
                FROM Appointments a
                JOIN Users d ON d.id = a.doctor_id
                WHERE a.patient_id = %s
                ORDER BY a.requested_date, a.requested_time
            """, (user_id,))

        rows = cursor.fetchall()
        appts = [
            {
                'id': r[0], 'patient_id': r[1], 'doctor_id': r[2],
                'requested_date': str(r[3]), 'requested_time': str(r[4]),
                'notes': r[5], 'status': r[6], 'other_party_name': r[7]
            }
            for r in rows
        ]
        return jsonify(appts)
    except Exception as e:
        return {'error': str(e)}, 500
    finally:
        cursor.close(); conn.close()


@app.route('/appointments/<int:appointment_id>', methods=['PUT'])
@login_required
def update_appointment_status(appointment_id):
    data, error = validate_json(['status'])
    if error: return error
    if data['status'] not in ('accepted', 'declined'):
        return {'error': "status must be accepted or declined"}, 400
    session_user_id = session.get('user_id')
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT doctor_id FROM Appointments WHERE id=%s", (appointment_id,))
        row = cursor.fetchone()
        if not row:
            return {'error': 'Appointment not found'}, 404
        if row[0] != session_user_id:
            return {'error': 'Forbidden: only the assigned doctor can respond'}, 403

        cursor.execute("UPDATE Appointments SET status=%s WHERE id=%s", (data['status'], appointment_id))
        conn.commit()
        return {'message': f"Appointment {data['status']}"}, 200
    except Exception as e:
        return {'error': str(e)}, 500
    finally:
        cursor.close(); conn.close()


'''

if anchor not in content:
    print("ERROR: anchor line not found. Nothing changed.")
elif "def get_messages" in content:
    print("Already applied — messaging/appointments routes found. Nothing changed.")
else:
    content = content.replace(anchor, new_routes + anchor)
    with io.open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("SUCCESS: routes inserted before main block.")