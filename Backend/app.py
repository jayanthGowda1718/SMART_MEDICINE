import json
import os
import re
from functools import wraps
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from flask import Flask, jsonify, request, session
import mysql.connector
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from datetime import datetime, timedelta
from chatbot.chatbot_logic import load_chatbot_model, get_chatbot_reply

# Load variables from a local .env file (never commit this file)
load_dotenv()

app = Flask(__name__)

# CORS origins can be overridden via env var (comma-separated) for real deployments
_cors_origins = os.environ.get('CORS_ORIGINS', 'http://127.0.0.1:5500,http://localhost:5500')
CORS(app, supports_credentials=True, origins=[o.strip() for o in _cors_origins.split(',')])

# Secret key must come from the environment in real deployments.
# The fallback below only exists so local dev doesn't crash if .env is missing â€”
# it must NEVER be relied on outside your own machine.
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev-only-change-me')
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = True
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('SESSION_COOKIE_SECURE', 'False') == 'True'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)

DEBUG_MODE = os.environ.get('FLASK_DEBUG', 'False') == 'True'

db_config = {
    'host': os.environ.get('DB_HOST', '127.0.0.1'),
    'user': os.environ.get('DB_USER', 'root'),
    'password': os.environ.get('DB_PASSWORD', ''),
    'database': os.environ.get('DB_NAME', 'medreminder_db'),
    'port': int(os.environ.get('DB_PORT', 3306))
}

# --- Debugging helper: log incoming requests (origin header, path, method)
# Only runs when FLASK_DEBUG=True â€” real deployments shouldn't log full headers.
@app.before_request
def log_request_info():
    if not DEBUG_MODE:
        return
    origin = request.headers.get('Origin') or 'no-origin'
    print(f"[REQUEST] {request.method} {request.path}  Origin: {origin}")
    if request.method == 'OPTIONS':
        print(f"[OPTIONS HEADERS] {dict(request.headers)}")

def get_db_connection():
    return mysql.connector.connect(**db_config)

def close_db(cursor=None, conn=None):
    """Safely close cursor and database connection without raising UnboundLocalError."""
    if cursor:
        try:
            cursor.close()
        except Exception:
            pass
    if conn:
        try:
            conn.close()
        except Exception:
            pass



def table_has_column(table_name, column_name):
    """Return True if the given column exists in the table (checks INFORMATION_SCHEMA)."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s AND COLUMN_NAME = %s
        """, (db_config['database'], table_name, column_name))
        exists = cursor.fetchone()[0] > 0
        return exists
    except Exception:
        return False
    finally:
        try:
            cursor.close(); conn.close()
        except Exception:
            pass

def login_required(f):
    """Blocks any request that doesn't have a valid session â€” stops
    unauthenticated callers from hitting data endpoints directly."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            return {'error': 'Authentication required'}, 401
        return f(*args, **kwargs)
    return wrapper


def generate_local_medicine_answer(question, user_id=None):
    """Return a safe general medication answer without relying on an external AI key."""
    q = re.sub(r'[^a-z0-9\s]+', ' ', (question or '').lower()).strip()
    common_info = {
        'paracetamol': 'Paracetamol is commonly used to relieve pain and reduce fever. Take it only as directed on the label or by your doctor, and do not exceed the recommended dose.',
        'acetaminophen': 'Acetaminophen is the same medicine as paracetamol. It is commonly used to relieve pain and reduce fever; do not exceed the recommended dose.',
        'dolo 650': 'Dolo 650 contains paracetamol. It is usually used to relieve mild to moderate pain and reduce fever. Avoid taking other paracetamol-containing products at the same time.',
        'ibuprofen': 'Ibuprofen helps reduce pain, fever, and inflammation. Follow the label or your doctor’s directions and avoid it if you have stomach, kidney, or heart problems without medical advice.',
        'amoxicillin': 'Amoxicillin is an antibiotic used for some bacterial infections. It must be taken exactly as prescribed and the full course should be completed unless your doctor tells you otherwise.',
        'metformin': 'Metformin is commonly used to help control blood sugar in type 2 diabetes. Follow your doctor’s prescription and report any serious nausea, vomiting, or breathing trouble.',
        'vitamin d': 'Vitamin D helps your body absorb calcium and keeps bones and teeth healthy. Use supplements only as directed by your doctor or pharmacist.',
        'vitamin b12': 'Vitamin B12 supports healthy blood cells and nerves. Use it only as directed by your doctor or pharmacist.',
        'azithromycin': 'Azithromycin is an antibiotic used for certain bacterial infections. Use it only as prescribed and complete the course unless told otherwise.',
        'amlodipine': 'Amlodipine helps lower blood pressure by relaxing blood vessels. Use it carefully as prescribed and tell your doctor about dizziness or swelling.',
        'atorvastatin': 'Atorvastatin is used to lower cholesterol and reduce heart risk. Take it as prescribed and tell your doctor if you have muscle pain or weakness.',
    }

    for name, answer in common_info.items():
        if name in q:
            return answer

    if re.search(r'(next|upcoming|when.*dose|dose.*when)', q):
        if user_id:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT s.schedule_time, s.days_of_week, m.name, m.dosage
                    FROM Schedules s
                    JOIN Medicines m ON m.id = s.medicine_id
                    WHERE s.user_id = %s
                    ORDER BY s.schedule_time ASC
                    LIMIT 1
                """, (user_id,))
                row = cursor.fetchone()
                if row:
                    return f"Your next scheduled medicine appears to be {row[2]} at {row[0]} on {row[1]}. Please confirm the exact timing and dose with your doctor or pharmacist."
            except Exception:
                pass
            finally:
                try:
                    cursor.close(); conn.close()
                except Exception:
                    pass
        return 'I can help check your next medicine dose once your schedule is saved in the app. Please confirm the medicine name and timing with your doctor or pharmacist.'

    if re.search(r'(my medicine|saved medicine|medicine list|medicines)', q):
        if user_id:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM Medicines WHERE user_id=%s ORDER BY name", (user_id,))
                rows = cursor.fetchall()
                if rows:
                    names = ', '.join(row[0] for row in rows)
                    return f"Your saved medicines include: {names}. Ask about a specific medicine for general information and dosage guidance."
            except Exception:
                pass
            finally:
                try:
                    cursor.close(); conn.close()
                except Exception:
                    pass
        return 'You do not have any medicines saved in the current session. Add them on the Medicines page and ask again.'

    if re.search(r'(hello|hi|hey)', q):
        return 'Hello! I can give general medicine information, explain common uses, and help you review your saved medicines. Please always confirm medical advice with a doctor or pharmacist.'

    return 'I provide general medicine information only. Please tell me the medicine name, and I can explain its common use and safety notes. For personal medical advice, check with your doctor or pharmacist.'


def generate_ai_answer(question, user_id=None):
    """Prefer OpenAI if configured; otherwise fall back to the local medicine assistant."""
    api_key = os.environ.get('OPENAI_API_KEY')
    if api_key:
        system_prompt = (
            'You are a careful medical information assistant for a medicine reminder app. '
            'Provide general educational information only, not a diagnosis. Promote safety, '
            'urge users to confirm with a healthcare professional, and avoid giving a dose '
            'without a source or doctor instruction.'
        )
        payload = {
            'model': 'gpt-4o-mini',
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': question}
            ],
            'temperature': 0.3,
        }
        try:
            request = Request(
                'https://api.openai.com/v1/chat/completions',
                data=json.dumps(payload).encode('utf-8'),
                headers={
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json',
                },
                method='POST',
            )
            with urlopen(request, timeout=20) as response:
                result = json.loads(response.read().decode('utf-8'))
                choices = result.get('choices') or []
                if choices:
                    message_text = choices[0].get('message', {}).get('content', '').strip()
                    if message_text:
                        return message_text
        except (HTTPError, URLError, ValueError, KeyError, TypeError):
            pass

    return generate_local_medicine_answer(question, user_id=user_id)


def is_authorized_for_user(target_user_id):
    """True if the logged-in session user is allowed to see/act on
    target_user_id's data: either it's their own id, or target_user_id
    is a family member they created (created_by = session user)."""
    session_user_id = session.get('user_id')
    if session_user_id is None:
        return False
    try:
        target_user_id = int(target_user_id)
    except (TypeError, ValueError):
        return False
    if target_user_id == session_user_id:
        return True
    if not table_has_column('Users', 'created_by'):
        return False
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT created_by FROM Users WHERE id=%s", (target_user_id,))
        row = cursor.fetchone()
        return bool(row and row[0] == session_user_id)
    except Exception:
        return False
    finally:
        try:
            cursor.close(); conn.close()
        except Exception:
            pass


def validate_json(required_fields):
    if not request.is_json:
        return None, ({'error': 'Expected JSON body'}, 400)
    data = request.get_json(silent=True) or {}
    for field in required_fields:
        if field not in data:
            return None, ({'error': f'Missing field: {field}'}, 400)
    return data, None

@app.route('/')
def home():
    return {'message': 'Smart Medicine Reminder API', 'status': 'running'}

@app.route('/users')
def get_users():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, role, contact_info, email FROM Users;")
        users = [
            {'id': r[0], 'name': r[1], 'role': r[2], 'contact_info': r[3], 'email': r[4]}
            for r in cursor.fetchall()
        ]
        return jsonify(users)
    except Exception as e:
        return {'error': str(e)}, 500
    finally:
        cursor.close(); conn.close()

@app.route('/users', methods=['POST'])
def create_user():
    data, error = validate_json(['name', 'role', 'email', 'password'])
    if error: return error
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Never store the raw password â€” hash it first.
        hashed_password = generate_password_hash(data['password'])

        # If database has created_by column, include it; otherwise insert without created_by
        created_by = data.get('created_by', None)
        if created_by is not None and table_has_column('Users', 'created_by'):
            cursor.execute("""
                INSERT INTO Users (name, role, contact_info, email, password, created_by)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                data['name'],
                data['role'],
                data.get('contact_info'),
                data['email'],
                hashed_password,
                created_by
            ))
        else:
            cursor.execute("""
                INSERT INTO Users (name, role, contact_info, email, password)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                data['name'],
                data['role'],
                data.get('contact_info'),
                data['email'],
                hashed_password
            ))

        conn.commit()
        return {'message': 'User created', 'id': cursor.lastrowid}, 201
    except Exception as e:
        return {'error': str(e)}, 500
    finally:
        cursor.close(); conn.close()

@app.route('/users/<int:user_id>', methods=['PUT'])
@login_required
def update_user(user_id):
    if not is_authorized_for_user(user_id):
        return {'error': 'Forbidden: not your data'}, 403
    data, error = validate_json(['name', 'role', 'contact_info', 'email'])
    if error: return error
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE Users
            SET name=%s, role=%s, contact_info=%s, email=%s
            WHERE id=%s
        """, (data['name'], data['role'], data['contact_info'], data['email'], user_id))
        if cursor.rowcount == 0:
            return {'error': 'User not found'}, 404
        conn.commit()
        return {'message': 'User updated successfully'}
    except Exception as e:
        return {'error': str(e)}, 500
    finally:
        cursor.close(); conn.close()

@app.route('/users/<int:user_id>', methods=['DELETE'])
@login_required
def delete_user(user_id):
    if not is_authorized_for_user(user_id):
        return {'error': 'Forbidden: not your data'}, 403
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Users WHERE id=%s", (user_id,))
        if cursor.rowcount == 0:
            return {'error': 'User not found'}, 404
        conn.commit()
        return {'message': 'User deleted successfully'}
    except Exception as e:
        return {'error': str(e)}, 500
    finally:
        cursor.close(); conn.close()

if DEBUG_MODE:
    @app.route('/routes', methods=['GET'])
    def list_routes():
        return str([r.rule for r in app.url_map.iter_rules()])

@app.route('/medicines')
def get_medicines():
    user_id = request.args.get('user_id')
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        if user_id:
            cursor.execute("SELECT id, user_id, name, dosage, instructions FROM Medicines WHERE user_id=%s", (user_id,))
        else:
            cursor.execute("SELECT id, user_id, name, dosage, instructions FROM Medicines")
        medicines = [
            {'id': r[0], 'user_id': r[1], 'name': r[2], 'dosage': r[3], 'instructions': r[4]}
            for r in cursor.fetchall()
        ]
        return jsonify(medicines)
    except Exception as e:
        return {'error': str(e)}, 500
    finally:
        cursor.close(); conn.close()

@app.route('/medicines', methods=['POST'])
@login_required
def add_medicine():
    data, error = validate_json(['user_id', 'name', 'dosage', 'instructions'])
    if error: return error
    if not is_authorized_for_user(data['user_id']):
        return {'error': 'Forbidden: not your data'}, 403
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Medicines (user_id, name, dosage, instructions)
            VALUES (%s, %s, %s, %s)
        """, (data['user_id'], data['name'], data['dosage'], data['instructions']))
        conn.commit()
        return {'message': 'Medicine added successfully'}, 201
    except Exception as e:
        return {'error': str(e)}, 500
    finally:
        cursor.close(); conn.close()

@app.route('/medicines/<int:medicine_id>', methods=['PUT'])
@login_required
def update_medicine(medicine_id):
    data, error = validate_json(['name', 'dosage', 'instructions'])
    if error: return error
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT user_id FROM Medicines WHERE id=%s", (medicine_id,))
        row = cursor.fetchone()
        if not row:
            return {'error': 'Medicine not found'}, 404
        if not is_authorized_for_user(row[0]):
            return {'error': 'Forbidden: not your data'}, 403

        cursor.execute("""
            UPDATE Medicines
            SET name=%s, dosage=%s, instructions=%s
            WHERE id=%s
        """, (data['name'], data['dosage'], data['instructions'], medicine_id))
        if cursor.rowcount == 0:
            return {'error': 'Medicine not found'}, 404
        conn.commit()
        return {'message': 'Medicine updated successfully'}
    except Exception as e:
        return {'error': str(e)}, 500
    finally:
        cursor.close(); conn.close()

@app.route('/medicines/<int:medicine_id>', methods=['DELETE'])
@login_required
def delete_medicine(medicine_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT user_id FROM Medicines WHERE id=%s", (medicine_id,))
        row = cursor.fetchone()
        if not row:
            return {'error': 'Medicine not found'}, 404
        if not is_authorized_for_user(row[0]):
            return {'error': 'Forbidden: not your data'}, 403

        cursor.execute("DELETE FROM Medicines WHERE id=%s", (medicine_id,))
        if cursor.rowcount == 0:
            return {'error': 'Medicine not found'}, 404
        conn.commit()
        return {'message': 'Medicine deleted successfully'}
    except Exception as e:
        return {'error': str(e)}, 500
    finally:
        cursor.close(); conn.close()

if DEBUG_MODE:
    @app.route('/test', methods=['GET'])
    def test():
        return "Test route working!"

@app.route('/schedules')
def get_schedules():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, user_id, medicine_id, schedule_time, days_of_week, start_date, end_date
            FROM Schedules;
        """)
        schedules = [
            {'id': r[0], 'user_id': r[1], 'medicine_id': r[2],
            'schedule_time': str(r[3]), 'days_of_week': r[4],
            'start_date': str(r[5]), 'end_date': str(r[6]) if r[6] else None}
            for r in cursor.fetchall()
        ]
        return jsonify(schedules)
    except Exception as e:
        return {'error': str(e)}, 500
    finally:
        cursor.close(); conn.close()

@app.route('/schedules', methods=['POST'])
@login_required
def add_schedule():
    data, error = validate_json(['user_id', 'medicine_id', 'schedule_time', 'days_of_week', 'start_date'])
    if error: return error
    if not is_authorized_for_user(data['user_id']):
        return {'error': 'Forbidden: not your data'}, 403
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Schedules (user_id, medicine_id, schedule_time, days_of_week, start_date, end_date)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (data['user_id'], data['medicine_id'], data['schedule_time'],
              data['days_of_week'], data['start_date'], data.get('end_date')))
        conn.commit()
        return {'message': 'Schedule added successfully'}, 201
    except Exception as e:
        return {'error': str(e)}, 500
    finally:
        cursor.close(); conn.close()

@app.route('/schedules/<int:schedule_id>', methods=['PUT'])
@login_required
def update_schedule(schedule_id):
    data, error = validate_json(['schedule_time', 'days_of_week', 'start_date'])
    if error: return error
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT user_id FROM Schedules WHERE id=%s", (schedule_id,))
        row = cursor.fetchone()
        if not row:
            return {'error': 'Schedule not found'}, 404
        if not is_authorized_for_user(row[0]):
            return {'error': 'Forbidden: not your data'}, 403

        cursor.execute("""
            UPDATE Schedules
            SET schedule_time=%s, days_of_week=%s, start_date=%s, end_date=%s
            WHERE id=%s
        """, (data['schedule_time'], data['days_of_week'], data['start_date'],
              data.get('end_date'), schedule_id))
        conn.commit()
        if cursor.rowcount == 0:
            return {'error': 'Schedule not found'}, 404
        return {'message': 'Schedule updated successfully'}, 200
    except Exception as e:
        return {'error': str(e)}, 500
    finally:
        cursor.close(); conn.close()


@app.route('/schedules/<int:schedule_id>', methods=['DELETE'])
@login_required
def delete_schedule(schedule_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT user_id FROM Schedules WHERE id=%s", (schedule_id,))
        row = cursor.fetchone()
        if not row:
            return {'error': 'Schedule not found'}, 404
        if not is_authorized_for_user(row[0]):
            return {'error': 'Forbidden: not your data'}, 403

        cursor.execute("DELETE FROM Schedules WHERE id=%s", (schedule_id,))
        conn.commit()
        return {'message': 'Schedule deleted successfully'}, 200
    except Exception as e:
        return {'error': str(e)}, 500
    finally:
        cursor.close(); conn.close()


@app.route('/intake_logs')
def get_intake_logs():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, user_id, medicine_id, scheduled_time, actual_time, status
            FROM IntakeLogs;
        """)
        logs = [
            {'id': r[0], 'user_id': r[1], 'medicine_id': r[2],
            'scheduled_time': str(r[3]), 'actual_time': str(r[4]) if r[4] else None,
            'status': r[5]}
            for r in cursor.fetchall()
        ]
        return jsonify(logs)
    except Exception as e:
        return {'error': str(e)}, 500
    finally:
        cursor.close(); conn.close()

@app.route('/intake_logs', methods=['POST'])
@login_required
def add_intake_log():
    data, error = validate_json(['user_id', 'medicine_id', 'scheduled_time', 'status'])
    if error: return error
    if not is_authorized_for_user(data['user_id']):
        return {'error': 'Forbidden: not your data'}, 403
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO IntakeLogs (user_id, medicine_id, scheduled_time, actual_time, status)
            VALUES (%s, %s, %s, %s, %s)
        """, (data['user_id'], data['medicine_id'], data['scheduled_time'],
              data.get('actual_time'), data['status']))
        conn.commit()
        return {'message': 'Intake log added successfully'}, 201
    except Exception as e:
        return {'error': str(e)}, 500
    finally:
        cursor.close(); conn.close()


# ============================================================
# DOCTOR CONTACT FEATURE
# Contact-info only (no messaging): a patient/caregiver picks a
# doctor from a list, and the app shows that doctor's phone/email.
# ============================================================

@app.route('/doctors', methods=['GET'])
@login_required
def list_doctors():
    """All users with role='doctor' â€” used to populate the assign-a-doctor dropdown."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, contact_info, email
            FROM Users
            WHERE role = 'doctor'
            ORDER BY name
        """)
        doctors = [
            {'id': r[0], 'name': r[1], 'contact_info': r[2], 'email': r[3]}
            for r in cursor.fetchall()
        ]
        return jsonify(doctors)
    except Exception as e:
        return {'error': str(e)}, 500
    finally:
        cursor.close(); conn.close()


@app.route('/my-doctor', methods=['GET'])
@login_required
def get_my_doctor():
    """The doctor currently assigned to the given patient, with contact info."""
    patient_id = request.args.get('user_id')
    if not patient_id:
        return {'error': 'User ID required'}, 400
    if not is_authorized_for_user(patient_id):
        return {'error': 'Forbidden: not your data'}, 403
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.id, u.name, u.contact_info, u.email, l.assigned_at
            FROM PatientDoctorLinks l
            JOIN Users u ON u.id = l.doctor_id
            WHERE l.patient_id = %s
        """, (patient_id,))
        row = cursor.fetchone()
        if not row:
            return jsonify(None)
        return jsonify({
            'doctor_id': row[0], 'name': row[1],
            'contact_info': row[2], 'email': row[3],
            'assigned_at': str(row[4])
        })
    except Exception as e:
        return {'error': str(e)}, 500
    finally:
        cursor.close(); conn.close()


@app.route('/assign-doctor', methods=['POST'])
@login_required
def assign_doctor():
    data, error = validate_json(['patient_id', 'doctor_id'])
    if error: return error
    if not is_authorized_for_user(data['patient_id']):
        return {'error': 'Forbidden: not your data'}, 403
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Confirm doctor_id actually belongs to a doctor
        cursor.execute("SELECT id FROM Users WHERE id=%s AND role='doctor'", (data['doctor_id'],))
        if not cursor.fetchone():
            return {'error': 'Selected user is not a doctor'}, 400

        # One doctor per patient: replace any existing assignment
        cursor.execute("""
            INSERT INTO PatientDoctorLinks (patient_id, doctor_id)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE doctor_id = VALUES(doctor_id), assigned_at = CURRENT_TIMESTAMP
        """, (data['patient_id'], data['doctor_id']))
        conn.commit()
        return {'message': 'Doctor assigned successfully'}, 200
    except Exception as e:
        return {'error': str(e)}, 500
    finally:
        cursor.close(); conn.close()


@app.route('/notifications')
def get_notifications():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, user_id, message, sent_time, type FROM Notifications;")
        notifications = [
            {'id': r[0], 'user_id': r[1], 'message': r[2], 'sent_time': str(r[3]), 'type': r[4]}
            for r in cursor.fetchall()
        ]
        return jsonify(notifications)
    except Exception as e:
        return {'error': str(e)}, 500
    finally:
        cursor.close(); conn.close()

@app.route('/notifications', methods=['POST'])
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
    finally:
        cursor.close(); conn.close()

@app.route('/login', methods=['POST'])
def login():
    data, error = validate_json(['email', 'password'])
    if error: return error

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, role, email, password FROM Users
            WHERE email=%s
        """, (data['email'],))

        row = cursor.fetchone()
        cursor.close()
        conn.close()

        # Verify the submitted password against the stored hash.
        # check_password_hash returns False (not an error) for a bad password,
        # and also safely rejects rows whose stored value isn't a valid hash.
        user = None
        if row and check_password_hash(row[4], data['password']):
            user = row

        if user:
            session['user_id'] = user[0]
            session['user_name'] = user[1]
            session['user_role'] = user[2]
            session['user_email'] = user[3]
            session.permanent = True

            return {
                'message': 'Login successful',
                'user': {
                    'id': user[0],
                    'name': user[1],
                    'role': user[2],
                    'email': user[3]
                }
            }, 200
        else:
            return {'error': 'Invalid email or password'}, 401
    except Exception as e:
        return {'error': str(e)}, 500

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return {'message': 'Logged out successfully'}, 200

@app.route('/chatbot', methods=['POST'])
def chatbot_reply():
    data = request.get_json(silent=True) or {}
    message = (data.get('message') or '').strip()
    if not message:
        return {'error': 'Message is required'}, 400

    user_id = data.get('user_id') or session.get('user_id')
    reply = get_chatbot_reply(user_id, message, get_db_connection)
    return {'reply': reply}, 200

@app.route('/check-session', methods=['GET'])
def check_session():
    if 'user_id' in session:
        return {
            'logged_in': True,
            'user': {
                'id': session['user_id'],
                'name': session['user_name'],
                'role': session['user_role'],
                'email': session['user_email']
            }
        }, 200
    else:
        return {'logged_in': False}, 200

@app.route('/my-schedules', methods=['GET'])
@login_required
def get_my_schedules():
    user_id = request.args.get('user_id')
    if not user_id:
        return {'error': 'User ID required'}, 400
    if not is_authorized_for_user(user_id):
        return {'error': 'Forbidden: not your data'}, 403
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT s.id, s.user_id, s.medicine_id, s.schedule_time, s.days_of_week, s.start_date, s.end_date,
                   m.name, m.dosage, u.name
            FROM Schedules s
            JOIN Medicines m ON s.medicine_id = m.id
            JOIN Users u ON s.user_id = u.id
            WHERE s.user_id = %s
        """, (user_id,))
        schedules = [
            {
                'id': r[0], 'user_id': r[1], 'medicine_id': r[2],
                'schedule_time': str(r[3]), 'days_of_week': r[4],
                'start_date': str(r[5]), 'end_date': str(r[6]) if r[6] else None,
                'medicine_name': r[7], 'dosage': r[8], 'user_name': r[9]
            }
            for r in cursor.fetchall()
        ]
        return jsonify(schedules)
    except Exception as e:
        return {'error': str(e)}, 500
    finally:
        cursor.close(); conn.close()


@app.route('/my-medicines', methods=['GET'])
@login_required
def get_my_medicines():
    user_id = request.args.get('user_id')
    if not user_id:
        return {'error': 'User ID required'}, 400
    if not is_authorized_for_user(user_id):
        return {'error': 'Forbidden: not your data'}, 403
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, user_id, name, dosage, instructions
            FROM Medicines
            WHERE user_id=%s
        """, (user_id,))
        medicines = [
            {'id': r[0], 'user_id': r[1], 'name': r[2], 'dosage': r[3], 'instructions': r[4]}
            for r in cursor.fetchall()
        ]
        return jsonify(medicines)
    except Exception as e:
        return {'error': str(e)}, 500
    finally:
        cursor.close(); conn.close()

@app.route('/my-notifications', methods=['GET'])
@login_required
def get_my_notifications():
    user_id = request.args.get('user_id')
    if not user_id:
        return {'error': 'User ID required'}, 400
    if not is_authorized_for_user(user_id):
        return {'error': 'Forbidden: not your data'}, 403
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, user_id, message, sent_time, type
            FROM Notifications
            WHERE user_id=%s AND sent_time <= NOW()
            ORDER BY sent_time DESC
        """, (user_id,))
        notifications = [
            {'id': r[0], 'user_id': r[1], 'message': r[2], 'sent_time': str(r[3]), 'type': r[4]}
            for r in cursor.fetchall()
        ]
        return jsonify(notifications)
    except Exception as e:
        return {'error': str(e)}, 500
    finally:
        cursor.close(); conn.close()

@app.route('/my-intake-logs', methods=['GET'])
@login_required
def get_my_intake_logs():
    user_id = request.args.get('user_id')
    if not user_id:
        return {'error': 'User ID required'}, 400
    if not is_authorized_for_user(user_id):
        return {'error': 'Forbidden: not your data'}, 403
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, user_id, medicine_id, scheduled_time, actual_time, status
            FROM IntakeLogs
            WHERE user_id=%s
            ORDER BY scheduled_time DESC
        """, (user_id,))
        logs = [
            {
                'id': r[0], 'user_id': r[1], 'medicine_id': r[2],
                'scheduled_time': str(r[3]), 'actual_time': str(r[4]) if r[4] else None,
                'status': r[5]
            }
            for r in cursor.fetchall()
        ]
        return jsonify(logs)
    except Exception as e:
        return {'error': str(e)}, 500
    finally:
        cursor.close(); conn.close()

@app.route('/my-family', methods=['GET'])
@login_required
def get_my_family():
    user_id = request.args.get('user_id')
    if not user_id:
        return {'error': 'User ID required'}, 400
    if not is_authorized_for_user(user_id):
        return {'error': 'Forbidden: not your data'}, 403
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # If Users table has created_by column, return user + created family members
        if table_has_column('Users', 'created_by'):
            cursor.execute("""
                SELECT id, name, role, contact_info, email, created_by
                FROM Users
                WHERE id=%s OR created_by=%s
                ORDER BY id
            """, (user_id, user_id))
        else:
            # created_by column not present: return only the requesting user
            cursor.execute("""
                SELECT id, name, role, contact_info, email, NULL AS created_by
                FROM Users
                WHERE id=%s
            """, (user_id,))
        users = [
            {
                'id': r[0], 'name': r[1], 'role': r[2],
                'contact_info': r[3], 'email': r[4], 'created_by': r[5]
            }
            for r in cursor.fetchall()
        ]
        return jsonify(users)
    except Exception as e:
        return {'error': str(e)}, 500
    finally:
        cursor.close(); conn.close()


@app.route('/family-schedules', methods=['GET'])
@login_required
def get_family_schedules():
    """All schedules for the logged-in user AND everyone they've added
    as family (created_by = them) â€” so the Schedules table shows
    schedules you created for family members too, not just your own."""
    user_id = request.args.get('user_id')
    if not user_id:
        return {'error': 'User ID required'}, 400
    if not is_authorized_for_user(user_id):
        return {'error': 'Forbidden: not your data'}, 403
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        if table_has_column('Users', 'created_by'):
            cursor.execute("""
                SELECT s.id, s.user_id, s.medicine_id, s.schedule_time, s.days_of_week,
                       s.start_date, s.end_date, m.name, m.dosage, u.name
                FROM Schedules s
                JOIN Medicines m ON s.medicine_id = m.id
                JOIN Users u ON s.user_id = u.id
                WHERE s.user_id = %s OR s.user_id IN (
                    SELECT id FROM Users WHERE created_by = %s
                )
                ORDER BY s.id
            """, (user_id, user_id))
        else:
            cursor.execute("""
                SELECT s.id, s.user_id, s.medicine_id, s.schedule_time, s.days_of_week,
                       s.start_date, s.end_date, m.name, m.dosage, u.name
                FROM Schedules s
                JOIN Medicines m ON s.medicine_id = m.id
                JOIN Users u ON s.user_id = u.id
                WHERE s.user_id = %s
                ORDER BY s.id
            """, (user_id,))

        schedules = [
            {
                'id': r[0], 'user_id': r[1], 'medicine_id': r[2],
                'schedule_time': str(r[3]), 'days_of_week': r[4],
                'start_date': str(r[5]), 'end_date': str(r[6]) if r[6] else None,
                'medicine_name': r[7], 'dosage': r[8], 'user_name': r[9]
            }
            for r in cursor.fetchall()
        ]
        return jsonify(schedules)
    except Exception as e:
        return {'error': str(e)}, 500
    finally:
        cursor.close(); conn.close()


# ============================================================
# REAL-TIME REMINDER ENGINE
# ------------------------------------------------------------
# Replaces the old client-side setInterval polling in schedules.js,
# which only fired reminders while a browser tab was open and awake.
# This runs on the SERVER, once a minute, regardless of whether
# anyone has the site open â€” so reminders and missed-dose alerts
# are reliable instead of best-effort.
# ============================================================

GRACE_MINUTES = int(os.environ.get('MISSED_DOSE_GRACE_MINUTES', 30))

# Accepts "Wed", "wed", "Wednesday", "WEDNESDAY" â€” anything reasonable â€”
# and normalizes it to the canonical 3-letter form used for matching.
# This exists because the "Days of Week" field is free text, and a user
# typing the full day name would otherwise silently never match, with
# no error shown anywhere.
_DAY_NAME_MAP = {}
for _abbr, _full in [('Mon', 'Monday'), ('Tue', 'Tuesday'), ('Wed', 'Wednesday'),
                      ('Thu', 'Thursday'), ('Fri', 'Friday'), ('Sat', 'Saturday'),
                      ('Sun', 'Sunday')]:
    _DAY_NAME_MAP[_abbr.lower()] = _abbr
    _DAY_NAME_MAP[_full.lower()] = _abbr


def _normalize_day(raw):
    return _DAY_NAME_MAP.get(raw.strip().lower())


def _schedule_matches_today(days_of_week, today_abbr):
    normalized = {_normalize_day(d) for d in days_of_week.split(',')}
    return today_abbr in normalized


def _sweep_due_reminders():
    """Find schedules whose time is right now, and if we haven't
    already logged/notified for today's dose, create a pending
    IntakeLogs row + a 'reminder' Notification."""
    now = datetime.now()
    today_str = now.strftime('%Y-%m-%d')
    current_time_str = now.strftime('%H:%M')
    today_abbr = now.strftime('%a')  # 'Mon', 'Tue', ... matches frontend's toLocaleString weekday:'short'

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT s.id, s.user_id, s.medicine_id, s.schedule_time, s.days_of_week,
                   m.name AS medicine_name, m.dosage
            FROM Schedules s
            JOIN Medicines m ON m.id = s.medicine_id
            WHERE s.start_date <= %s
              AND (s.end_date IS NULL OR s.end_date >= %s)
              AND TIME_FORMAT(s.schedule_time, '%%H:%%i') = %s
        """, (today_str, today_str, current_time_str))
        due = cursor.fetchall()

        for row in due:
            _, user_id, medicine_id, schedule_time, days_of_week, medicine_name, dosage = row
            if not _schedule_matches_today(days_of_week, today_abbr):
                continue

            scheduled_dt = f"{today_str} {schedule_time}"

            # Skip if we've already created a log for this exact dose today
            cursor.execute("""
                SELECT id FROM IntakeLogs
                WHERE user_id=%s AND medicine_id=%s AND scheduled_time=%s
            """, (user_id, medicine_id, scheduled_dt))
            if cursor.fetchone():
                continue

            cursor.execute("""
                INSERT INTO IntakeLogs (user_id, medicine_id, scheduled_time, status)
                VALUES (%s, %s, %s, 'pending')
            """, (user_id, medicine_id, scheduled_dt))

            message = f"Time to take {medicine_name} ({dosage})" if dosage else f"Time to take {medicine_name}"
            cursor.execute("""
                INSERT INTO Notifications (user_id, message, type)
                VALUES (%s, %s, 'reminder')
            """, (user_id, message))

        conn.commit()
    except Exception as e:
        print(f"[reminder-engine] sweep_due_reminders error: {e}")
    finally:
        if conn:
            try:
                cursor.close(); conn.close()
            except Exception:
                pass


def _sweep_missed_doses():
    """Any 'pending' dose older than GRACE_MINUTES becomes 'missed',
    and alerts go to the patient AND their caregiver (if any)."""
    threshold = datetime.now() - timedelta(minutes=GRACE_MINUTES)
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT il.id, il.user_id, il.medicine_id, m.name, u.created_by
            FROM IntakeLogs il
            JOIN Medicines m ON m.id = il.medicine_id
            JOIN Users u ON u.id = il.user_id
            WHERE il.status = 'pending' AND il.scheduled_time <= %s
        """, (threshold,))
        missed = cursor.fetchall()

        for log_id, user_id, medicine_id, medicine_name, caregiver_id in missed:
            cursor.execute("UPDATE IntakeLogs SET status='missed' WHERE id=%s", (log_id,))

            cursor.execute("""
                INSERT INTO Notifications (user_id, message, type)
                VALUES (%s, %s, 'alert')
            """, (user_id, f"You missed your dose of {medicine_name}"))

            if caregiver_id:
                cursor.execute("""
                    INSERT INTO Notifications (user_id, message, type)
                    VALUES (%s, %s, 'alert')
                """, (caregiver_id, f"A family member missed their dose of {medicine_name}"))

        conn.commit()
    except Exception as e:
        print(f"[reminder-engine] sweep_missed_doses error: {e}")
    finally:
        if conn:
            try:
                cursor.close(); conn.close()
            except Exception:
                pass


def _reminder_engine_tick():
    _sweep_due_reminders()
    _sweep_missed_doses()


def start_reminder_engine():
    from apscheduler.schedulers.background import BackgroundScheduler
    scheduler = BackgroundScheduler(daemon=True)
    scheduler.add_job(_reminder_engine_tick, 'interval', seconds=60, id='reminder_engine_tick')
    scheduler.start()
    print("[reminder-engine] started â€” checking schedules every 60s")


# --- New endpoint: patient/caregiver confirms a dose was taken ---
@app.route('/intake_logs/<int:log_id>/confirm', methods=['PUT'])
@login_required
def confirm_intake_log(log_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM IntakeLogs WHERE id=%s", (log_id,))
        row = cursor.fetchone()
        if not row:
            return {'error': 'Log not found'}, 404
        if not is_authorized_for_user(row[0]):
            return {'error': 'Forbidden: not your data'}, 403

        cursor.execute("""
            UPDATE IntakeLogs SET status='taken', actual_time=%s
            WHERE id=%s AND status='pending'
        """, (datetime.now(), log_id))
        conn.commit()
        if cursor.rowcount == 0:
            return {'error': 'Log already resolved or not found'}, 409
        return {'message': 'Dose confirmed as taken'}, 200
    except Exception as e:
        return {'error': str(e)}, 500
    finally:
        cursor.close(); conn.close()



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
        close_db(cursor, conn)


# ============================================================
# SMART PILL BOX TELEMETRY & WEIGHT-BASED DETECTION
# (Aligns with Research Paper Flowchart & Load Cell Detection)
# ============================================================

@app.route('/api/telemetry/weight', methods=['POST'])
def process_weight_telemetry():
    """Receives weight telemetry from ESP32 / Load Cell sensor or web simulation.
    Calculates ΔW = weight_before - weight_after.
    If ΔW >= threshold: marks dose as 'taken' via 'weight_sensor'.
    Else: marks as 'missed' and triggers caregiver notification."""
    data, error = validate_json(['user_id', 'medicine_id', 'weight_before', 'weight_after'])
    if error: return error

    user_id = data['user_id']
    medicine_id = data['medicine_id']
    weight_before = float(data['weight_before'])
    weight_after = float(data['weight_after'])
    threshold = float(data.get('threshold', 0.5))  # Default 0.5g threshold
    delta_weight = weight_before - weight_after

    is_taken = delta_weight >= threshold
    status = 'taken' if is_taken else 'missed'
    verification = 'weight_sensor'

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Find medicine name
        cursor.execute("SELECT name FROM Medicines WHERE id=%s", (medicine_id,))
        med_row = cursor.fetchone()
        medicine_name = med_row[0] if med_row else "Medication"

        # Log telemetry intake event
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if table_has_column('IntakeLogs', 'delta_weight'):
            cursor.execute("""
                INSERT INTO IntakeLogs (user_id, medicine_id, scheduled_time, actual_time, status, weight_before, weight_after, delta_weight, verification_method)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (user_id, medicine_id, now_str, now_str if is_taken else None, status, weight_before, weight_after, delta_weight, verification))
        else:
            cursor.execute("""
                INSERT INTO IntakeLogs (user_id, medicine_id, scheduled_time, actual_time, status)
                VALUES (%s, %s, %s, %s, %s)
            """, (user_id, medicine_id, now_str, now_str if is_taken else None, status))

        # Send notification
        if is_taken:
            msg = f"🟢 Dose confirmed! {medicine_name} taken (Weight reduction: {delta_weight:.2f}g detected)."
            cursor.execute("INSERT INTO Notifications (user_id, message, type) VALUES (%s, %s, 'info')", (user_id, msg))
        else:
            msg = f"🔴 Alert: Missed dose of {medicine_name}. No weight reduction detected."
            cursor.execute("INSERT INTO Notifications (user_id, message, type) VALUES (%s, %s, 'alert')", (user_id, msg))
            
            # Notify caregiver if available
            cursor.execute("SELECT created_by FROM Users WHERE id=%s", (user_id,))
            user_row = cursor.fetchone()
            if user_row and user_row[0]:
                caregiver_id = user_row[0]
                cursor.execute("INSERT INTO Notifications (user_id, message, type) VALUES (%s, %s, 'alert')", 
                               (caregiver_id, f"🔴 Family Alert: Missed dose of {medicine_name}."))

        conn.commit()
        return jsonify({
            'message': 'Telemetry processed successfully',
            'status': status,
            'delta_weight': delta_weight,
            'verified': is_taken,
            'verification_method': verification
        }), 200
    except Exception as e:
        return {'error': str(e)}, 500
    finally:
        close_db(cursor, conn)


if __name__ == '__main__':
    load_chatbot_model()
    # Avoid starting two copies of the scheduler when Flask's debug
    # auto-reloader spawns a child process.
    if not DEBUG_MODE or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        start_reminder_engine()
    app.run(debug=DEBUG_MODE)

