import os, django
os.environ['DJANGO_SETTINGS_MODULE'] = 'condominio_info.settings'
django.setup()

from firebase_admin import messaging

# Try sending a dry-run message to test Firebase auth
try:
    message = messaging.Message(
        notification=messaging.Notification(title="test", body="test"),
        token="fake_token_for_test",
    )
    response = messaging.send(message, dry_run=True)
    print("Firebase OK:", response)
except Exception as e:
    error_str = str(e)
    if "not a valid FCM registration token" in error_str or "INVALID_ARGUMENT" in error_str or "not found" in error_str.lower():
        print("Firebase AUTH OK (token invalido mas auth funcionou)")
    else:
        print("Firebase AUTH FAILED:", type(e).__name__, "-", e)
