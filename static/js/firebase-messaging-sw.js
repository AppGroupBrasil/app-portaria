importScripts('https://www.gstatic.com/firebasejs/9.23.0/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/9.23.0/firebase-messaging-compat.js');

const firebaseConfig = {
    apiKey: "AIzaSyBHaa-SEqFVIaQQEAjyFsoJZBcNA2z-xRA",
    authDomain: "appgroupnotification.firebaseapp.com",
    projectId: "appgroupnotification",
    storageBucket: "appgroupnotification.firebasestorage.app",
    messagingSenderId: "603160314743",
    appId: "1:603160314743:web:3cfa5d8bdc05ec93e25772"
};

const app = firebase.initializeApp(firebaseConfig);
const messaging = firebase.messaging();

messaging.onBackgroundMessage((payload) => {
    console.log('Received background message ', payload);

    self.registration.getNotifications().then(notifications => {
        notifications.forEach(notification => notification.close());
    }).then(() => {
        return self.registration.showNotification(payload.notification.title, {
            body: payload.notification.body,
            icon: '/static/img/pwa/Logo.png',
            data: payload.data
        });
    });
});

self.addEventListener('notificationclick', function (event) {
    event.notification.close();
    console.log("Notification clicked:", event.notification);
    console.log("Notification Data:", event.notification.data);

    const url = event.notification.data ? event.notification.data.url : null; // Get the URL passed in the notification data


    if (url) {
        event.waitUntil(
            clients.matchAll({type: "window", includeUncontrolled: true}).then((clientList) => {
                for (let client of clientList) {
                    if (client.url === url && "focus" in client) {
                        return client.focus();
                    }
                }
                return clients.openWindow(url);
            })
        );
    } else {
        // Fallback: you can open a default page or just do nothing
        event.waitUntil(
            clients.openWindow('/')  // Default page (home page)
        );
    }
});
