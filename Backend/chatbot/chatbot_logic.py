import json
import os
import re
from datetime import date, datetime, timedelta
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def load_chatbot_model():
    """Initialize the chatbot model; the app uses a local RAG-style medicine context by default."""
    return {
        'status': 'ready',
        'provider': 'rag-local-medication-db',
        'model_name': 'smart-medicine-chatbot-rag'
    }


def _fetch_user_context(user_id, db_getter):
    if not user_id or db_getter is None:
        return {'medicines': [], 'schedules': []}

    conn = None
    cursor = None
    try:
        conn = db_getter()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id, user_id, name, dosage, instructions FROM Medicines WHERE user_id=%s ORDER BY name",
            (user_id,)
        )
        medicines = [
            {
                'id': row[0],
                'user_id': row[1],
                'name': row[2],
                'dosage': row[3],
                'instructions': row[4]
            }
            for row in cursor.fetchall()
        ]

        cursor.execute(
            """
            SELECT s.id, s.user_id, s.medicine_id, s.schedule_time, s.days_of_week,
                   s.start_date, s.end_date, m.name, m.dosage
            FROM Schedules s
            JOIN Medicines m ON m.id = s.medicine_id
            WHERE s.user_id=%s
            ORDER BY s.schedule_time ASC
            """,
            (user_id,)
        )
        schedules = [
            {
                'id': row[0],
                'user_id': row[1],
                'medicine_id': row[2],
                'schedule_time': str(row[3]),
                'days_of_week': row[4],
                'start_date': str(row[5]),
                'end_date': str(row[6]) if row[6] else None,
                'medicine_name': row[7],
                'dosage': row[8]
            }
            for row in cursor.fetchall()
        ]

        return {'medicines': medicines, 'schedules': schedules}
    except Exception:
        return {'medicines': [], 'schedules': []}
    finally:
        if cursor is not None:
            try:
                cursor.close()
            except Exception:
                pass
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass


def _find_next_reminder(schedules):
    if not schedules:
        return None

    now = datetime.now()
    day_aliases = {
        'monday': 'mon', 'mon': 'mon',
        'tuesday': 'tue', 'tue': 'tue', 'tues': 'tue',
        'wednesday': 'wed', 'wed': 'wed',
        'thursday': 'thu', 'thu': 'thu', 'thur': 'thu', 'thurs': 'thu',
        'friday': 'fri', 'fri': 'fri',
        'saturday': 'sat', 'sat': 'sat',
        'sunday': 'sun', 'sun': 'sun'
    }
    day_names = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
    candidates = []

    for schedule in schedules:
        days = {
            day_aliases.get(d.strip().lower(), d.strip().lower()[:3])
            for d in str(schedule.get('days_of_week') or '').split(',')
            if d.strip()
        }
        if not days:
            continue
        try:
            time_text = str(schedule.get('schedule_time') or '00:00')
            time_value = datetime.strptime(time_text, '%H:%M:%S')
        except ValueError:
            try:
                time_value = datetime.strptime(time_text, '%H:%M')
            except ValueError:
                continue

        try:
            start_date = date.fromisoformat(str(schedule.get('start_date'))) if schedule.get('start_date') else date.min
            end_date = date.fromisoformat(str(schedule.get('end_date'))) if schedule.get('end_date') else date.max
        except ValueError:
            continue

        for offset in range(0, 8):
            candidate_date = (now + timedelta(days=offset)).date()
            if candidate_date < start_date or candidate_date > end_date:
                continue
            day_name = day_names[candidate_date.weekday()]
            if day_name not in days:
                continue
            candidate = datetime.combine(candidate_date, time_value.time())
            if candidate <= now:
                continue
            candidates.append((candidate, schedule))
            break

    if not candidates:
        return None
    candidates.sort(key=lambda item: item[0])
    next_dt, schedule = candidates[0]
    return {
        'medicine_name': schedule.get('medicine_name') or 'Medicine',
        'schedule_time': schedule.get('schedule_time'),
        'datetime': next_dt
    }


def _find_today_reminders(schedules):
    now = datetime.now()
    today_name = now.strftime('%A').lower()[:3]
    reminders = []
    for schedule in schedules or []:
        days = str(schedule.get('days_of_week') or '').lower()
        if today_name not in days and now.strftime('%A').lower() not in days:
            continue
        try:
            start_date = date.fromisoformat(str(schedule.get('start_date'))) if schedule.get('start_date') else date.min
            end_date = date.fromisoformat(str(schedule.get('end_date'))) if schedule.get('end_date') else date.max
        except ValueError:
            continue
        if start_date <= now.date() <= end_date:
            reminders.append(schedule)
    return sorted(reminders, key=lambda item: str(item.get('schedule_time') or ''))


def _build_rag_context(message, medicines, schedules):
    context_lines = ['The user is asking about their medicine reminder system.']
    if medicines:
        context_lines.append('Saved medicines:')
        for med in medicines:
            context_lines.append(
                f"- {med.get('name')} | dosage: {med.get('dosage') or 'not provided'} | instructions: {med.get('instructions') or 'not provided'}"
            )
    else:
        context_lines.append('No saved medicines are present in the current user account.')

    if schedules:
        context_lines.append('Saved schedules:')
        for schedule in schedules:
            context_lines.append(
                f"- {schedule.get('medicine_name')} | time: {schedule.get('schedule_time')} | days: {schedule.get('days_of_week')} | start: {schedule.get('start_date')}"
            )
    else:
        context_lines.append('No active schedules were found for this user.')

    context_lines.append(f"Current user question: {message}")
    return '\n'.join(context_lines)


def _safe_medication_reply(message, medicines=None, schedules=None):
    text = (message or '').lower().strip()
    if not text:
        return 'Please ask a medicine or schedule question.'

    if 'hello' in text or 'hi' in text:
        return 'Hello! I can help with medicine reminders, general medication information, and schedule questions.'

    reminder_keywords = ['next reminder', 'next dose', 'next tablet', 'when is my next', 'next alert', 'reminder']
    if any(keyword in text for keyword in reminder_keywords):
        next_reminder = _find_next_reminder(schedules or [])
        if next_reminder:
            return (
                f"Your next reminder is {next_reminder['medicine_name']} at {next_reminder['schedule_time']} "
                f"on {next_reminder['datetime'].strftime('%A, %B %d')}."
            )
        return 'I do not see an active upcoming reminder in your current schedule. Please check the Schedules page or ask your doctor to confirm your plan.'

    if ('today' in text or 'this day' in text) and ('medicine' in text or 'dose' in text or 'tablet' in text or 'take' in text):
        today_reminders = _find_today_reminders(schedules or [])
        if today_reminders:
            details = ', '.join(
                f"{item.get('medicine_name') or 'Medicine'} at {item.get('schedule_time')}"
                for item in today_reminders
            )
            return f"Today you need to take: {details}. Please follow your prescribed instructions."
        return 'I do not see any active medicine scheduled for today. Please check the Schedules page or ask your doctor to confirm your plan.'

    if 'paracetamol' in text or 'acetaminophen' in text or 'dolo' in text:
        return 'Paracetamol is commonly used to relieve pain and reduce fever. Follow the label or your doctor\'s instructions and do not exceed the recommended dose.'

    if medicines:
        for med in medicines:
            med_name = (med.get('name') or '').lower()
            if med_name in text or text in med_name:
                return (
                    f"{med.get('name')} is saved with dosage {med.get('dosage') or 'not provided'} and "
                    f"instructions: {med.get('instructions') or 'not provided'}. Please follow your doctor or pharmacist instructions."
                )

    if 'medicine' in text or 'tablet' in text:
        return 'I can provide general medicine guidance. Please tell me the medicine name so I can explain its common use and safety notes.'

    if 'schedule' in text or 'reminder' in text:
        return 'Your reminder schedule is managed in the app. Add or update the schedule from the Schedules page, then ask again for the next dose.'

    return 'I can help with general medicine information and reminders. Try asking about a medicine name, your next dose, or your schedule.'


def _openai_rag_reply(message, medicines, schedules):
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        return None

    context = _build_rag_context(message, medicines, schedules)
    payload = {
        'model': 'gpt-4o-mini',
        'messages': [
            {
                'role': 'system',
                'content': (
                    'You are a careful medicine reminder assistant for a healthcare app. '
                    'Use only the patient schedule and medicine context provided. '
                    'Never diagnose or prescribe a dose. Always tell the user to confirm with a doctor or pharmacist.'
                )
            },
            {'role': 'user', 'content': context}
        ],
        'temperature': 0.2
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
                text_reply = choices[0].get('message', {}).get('content', '').strip()
                if text_reply:
                    return text_reply
    except (HTTPError, URLError, ValueError, KeyError, TypeError):
        pass
    return None


def get_chatbot_reply(user_id, message, db_getter=None):
    """Use RAG-style retrieval from the user’s medicine/schedule records before replying."""
    context = {'medicines': [], 'schedules': []}
    if db_getter is not None:
        context = _fetch_user_context(user_id, db_getter)

    openai_reply = _openai_rag_reply(message, context['medicines'], context['schedules'])
    if openai_reply:
        return openai_reply

    return _safe_medication_reply(message, medicines=context['medicines'], schedules=context['schedules'])
