import json
import os
import logging

from django.http import JsonResponse, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from firebase_admin import messaging

from condominio_info import settings
from info.models import PushNotificationToken, CondominiumProfile, Notification


logger = logging.getLogger(__name__)


@csrf_exempt
@login_required
def save_push_token(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            token = data.get("token")
            device_type = data.get("device_type")

            if not token or not device_type:
                return JsonResponse({"error": "Invalid data"}, status=400)

            # Save or update the token
            PushNotificationToken.objects.update_or_create(
                user=request.user,
                token=token,
                defaults={"device_type": device_type},
            )

            return JsonResponse({"message": "Token saved successfully"})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    else:
        return JsonResponse({"error": "Invalid request method"}, status=405)


def send_push_notification(user, title, body, url):
    tokens = list(user.push_tokens.values_list("token", flat=True))
    if not tokens:
        print(f"No tokens found for user {user.condominium_name}")
        return False

    title = title or "Notificação da portaria"
    body = body or "Você recebeu uma nova notificação."

    # Create the message
    if not url:
        url = '/'

    message = messaging.MulticastMessage(
        notification=messaging.Notification(
            title=title,
            body=body
        ),
        data={
            'url': url  # The URL to open when the notification is clicked
        },
        tokens=tokens,
    )

    # Send the notification
    try:
        response = messaging.send_each_for_multicast(message)
    except Exception as exc:
        logger.warning(
            "Failed to send push notification to user %s: %s",
            user.pk,
            exc,
        )
        return False

    print(f"Successfully sent {response.success_count} messages, {response.failure_count} failed")
    return response.success_count > 0


def test_user_notification(request):
    condominium = CondominiumProfile.objects.get(pk=int(request.user.id))
    send_push_notification(condominium, "Teste de Mensagem", "isso é uma mensagem de teste", "https://google.com")
    return redirect(reverse('info:dashboard'))


def clear_push_not(request):
    for notification in Notification.objects.all():
        notification.read = True
        notification.save()
    return redirect(reverse('info:dashboard'))


data = 'importScripts("https://www.gstatic.com/firebasejs/9.23.0/firebase-app-compat.js");' \
       'importScripts("https://www.gstatic.com/firebasejs/9.23.0/firebase-messaging-compat.js");' \
       'const firebaseConfig = {' \
       'apiKey: "AIzaSyBHaa-SEqFVIaQQEAjyFsoJZBcNA2z-xRA",' \
       'authDomain: "appgroupnotification.firebaseapp.com",' \
       'projectId: "appgroupnotification",' \
       'storageBucket: "appgroupnotification.firebasestorage.app",' \
       'messagingSenderId: "603160314743",' \
       'appId: "1:603160314743:web:2132ecf89cf454c7e25772"' \
       '};' \
       'const app = firebase.initializeApp(firebaseConfig);' \
       'const messaging = firebase.messaging();' \
       'messaging.onBackgroundMessage((payload) => {' \
       'console.log("Received background message ", payload);' \
       'const notificationTitle = payload.notification.title;' \
       'const notificationOptions = {' \
       'body: payload.notification.body,' \
       'icon: "https://appsindico.com.br/static/img/pwa/Logo.png",' \
       'data: payload.data' \
       '};' \
       'self.registration.showNotification(notificationTitle, notificationOptions);' \
       '});' \
       'self.addEventListener("notificationclick", function(event) {' \
       'event.notification.close();' \
       'console.log("Notification clicked:", event.notification);' \
       'console.log("Notification Data:", event.notification.data);' \
       'const url = event.notification.data ? event.notification.data.url : null;' \
       'if (url) {' \
       'event.waitUntil(' \
       'clients.matchAll({ type: "window", includeUncontrolled: true }).then((clientList) => {' \
       'for (let client of clientList) {' \
       'if (client.url === url && "focus" in client) {' \
       'return client.focus();' \
       '}' \
       '}' \
       'return clients.openWindow(url);' \
       '})' \
       ');' \
       '} else {' \
       'event.waitUntil(' \
       'clients.openWindow("/")' \
       ');' \
       '}' \
       '});'


def return_firebase_worker(request):
    # return HttpResponse(data, content_type='text/javascript')
    file_path = os.path.join(settings.BASE_DIR, "static/js/firebase-messaging-sw.js")

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()
        return HttpResponse(content, content_type="application/javascript")
    except FileNotFoundError:
        return HttpResponse("// Service worker not found", content_type="application/javascript", status=404)
