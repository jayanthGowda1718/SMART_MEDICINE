import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import app  # noqa: E402
from chatbot.chatbot_logic import _safe_medication_reply


class ChatbotFeatureTests(unittest.TestCase):
    def setUp(self):
        os.environ.pop('OPENAI_API_KEY', None)
        self.client = app.app.test_client()

    def test_chatbot_route_returns_reply(self):
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
        response = self.client.post('/chatbot', json={'message': 'hello'})
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        payload = response.get_json()
        self.assertIn('reply', payload)
        self.assertTrue(len(payload['reply']) > 0)

    def test_chatbot_handles_next_reminder_question(self):
        reply = app.get_chatbot_reply(1, 'when is my next reminder', lambda: None)
        self.assertIn('upcoming reminder', reply.lower())
        self.assertIn('check the schedules page', reply.lower())

        tomorrow = __import__('datetime').datetime.now() + __import__('datetime').timedelta(days=1)
        future_time = tomorrow.strftime('%H:%M')
        with_schedules = _safe_medication_reply(
            'when is my next reminder',
            medicines=[],
            schedules=[{
                'medicine_name': 'Paracetamol',
                'schedule_time': future_time,
                'days_of_week': 'Mon,Tue,Wed,Thu,Fri,Sat,Sun',
                'start_date': '2026-08-26'
            }]
        )
        self.assertIn('paracetamol', with_schedules.lower())


if __name__ == '__main__':
    unittest.main()
