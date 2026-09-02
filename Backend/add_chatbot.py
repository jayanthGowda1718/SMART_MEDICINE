import io

path = "app.py"
with io.open(path, "r", encoding="utf-8") as f:
    content = f.read()

changes = 0

# 1. Add the import
import_anchor = "from datetime import datetime, timedelta"
import_line = "from chatbot.chatbot_logic import load_chatbot_model, get_chatbot_reply\n"
if import_anchor in content and "chatbot_logic import" not in content:
    content = content.replace(import_anchor, import_anchor + "\n" + import_line, 1)
    changes += 1
    print("Import: ADDED")
else:
    print("Import: skipped (already present or anchor not found)")

# 2. Load the model when the server starts
start_anchor = "start_reminder_engine()"
if start_anchor in content and "load_chatbot_model()" not in content:
    content = content.replace(start_anchor, start_anchor + "\n        load_chatbot_model()", 1)
    changes += 1
    print("Model loader call: ADDED")
else:
    print("Model loader call: skipped (already present or anchor not found)")

# 3. Add the /chatbot route
main_anchor = "if __name__ == '__main__':"
route_code = '''
@app.route('/chatbot', methods=['POST'])
@login_required
def chatbot_reply():
    data, error = validate_json(['message'])
    if error: return error
    user_id = session.get('user_id')
    try:
        reply = get_chatbot_reply(user_id, data['message'], get_db_connection)
        return {'reply': reply}, 200
    except Exception as e:
        return {'error': str(e)}, 500


'''
if main_anchor in content and "def chatbot_reply" not in content:
    content = content.replace(main_anchor, route_code + main_anchor, 1)
    changes += 1
    print("Chatbot route: ADDED")
else:
    print("Chatbot route: skipped (already present or anchor not found)")

if changes:
    with io.open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"\nSaved app.py with {changes} change(s).")
else:
    print("\nNothing changed.")