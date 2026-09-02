"""
Training data for the Smart Medicine Reminder chatbot.
Each intent has a list of example phrases a user might type.
Add more examples over time to make the model more accurate —
15-30 varied examples per intent is a reasonable starting point.
"""

TRAINING_DATA = [
    # greeting
    ("hi", "greeting"),
    ("hello", "greeting"),
    ("hey there", "greeting"),
    ("good morning", "greeting"),
    ("good evening", "greeting"),
    ("hi there", "greeting"),
    ("hello bot", "greeting"),

    # check_schedule
    ("when do I take my medicine", "check_schedule"),
    ("what is my next dose", "check_schedule"),
    ("show my schedule", "check_schedule"),
    ("what time is my medicine", "check_schedule"),
    ("when is my next reminder", "check_schedule"),
    ("what medicines are scheduled today", "check_schedule"),
    ("tell me my medicine timings", "check_schedule"),
    ("do I have a dose today", "check_schedule"),
    ("what is on my schedule", "check_schedule"),

    # check_medicines
    ("what medicines do I have", "check_medicines"),
    ("list my medicines", "check_medicines"),
    ("show my medicines", "check_medicines"),
    ("what pills am I taking", "check_medicines"),
    ("show all my medications", "check_medicines"),
    ("what medicine am I on", "check_medicines"),

    # doctor_contact
    ("who is my doctor", "doctor_contact"),
    ("doctor contact", "doctor_contact"),
    ("how do I contact my doctor", "doctor_contact"),
    ("give me my doctors phone number", "doctor_contact"),
    ("what is my doctors email", "doctor_contact"),
    ("I need to reach my doctor", "doctor_contact"),

    # missed_dose_help
    ("I missed my dose", "missed_dose_help"),
    ("what if I miss a dose", "missed_dose_help"),
    ("I forgot to take my medicine", "missed_dose_help"),
    ("I skipped my medicine today", "missed_dose_help"),
    ("what should I do if I missed a pill", "missed_dose_help"),

    # thanks
    ("thank you", "thanks"),
    ("thanks a lot", "thanks"),
    ("thanks", "thanks"),
    ("appreciate it", "thanks"),

    # goodbye
    ("bye", "goodbye"),
    ("goodbye", "goodbye"),
    ("see you later", "goodbye"),
    ("talk to you later", "goodbye"),
]