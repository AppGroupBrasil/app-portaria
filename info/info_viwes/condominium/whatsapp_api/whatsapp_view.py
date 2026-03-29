import json
import requests
from django.http import HttpResponseForbidden, HttpResponseBadRequest, JsonResponse, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse

from condominio_info import settings


def send_booking_message(condominium_name, place, resident, contact, template):
    message_params = [
        {
            "type": "body",
            "parameters": [
                {
                    "type": "text",
                    "text": f"{resident}"
                },
                {
                    "type": "text",
                    "text": f"{place}"
                }
            ]
        },
        {
            "type": "header",
            "parameters": [
                {
                    "type": "text",
                    "text": f"{condominium_name}"
                }
            ]
        }
    ]

    _send_info_message(contact.replace('(', '').replace(')', '').replace(' ', '').replace('-', '').replace('+', ''),
                       template, message_params)


def send_info_message(condominium_name, resident, contact, message, url=None):
    message_params = [
        {
            "type": "body",
            "parameters": [
                {
                    "type": "text",
                    "text": f"{resident}"
                },
                {
                    "type": "text",
                    "text": f"{message}"
                }
            ]
        },
        {
            "type": "header",
            "parameters": [
                {
                    "type": "text",
                    "text": f"{condominium_name}"
                }
            ]
        },
        {
            "type": "button",
            "sub_type": "url",
            "index": "0",
            "parameters": [
                {
                    "type": "text",
                    # Business Developer-defined dynamic URL suffix
                    "text": url if url else "https://appportaria.com"
                }
            ]
        },
    ]

    _send_info_message(contact.replace('(', '').replace(')', '').replace(' ', '').replace('-', '').replace('+', ''),
                       "info", message_params)


def send_order_message(condominium_name, resident, addressee, contact, code, image_url):
    message_params = [
        {
            "type": "header",
            "parameters": [
                {
                    "type": "image",
                    "image": {
                        "link": f"https://appportaria.com{image_url}"
                    }
                }
            ]
        },
        {
            "type": "body",
            "parameters": [
                {
                    "type": "text",
                    "text": f"{resident}"
                },
                {
                    "type": "text",
                    "text": f"{addressee}"
                },
                {
                    "type": "text",
                    "text": f"{code}"
                },
                {
                    "type": "text",
                    "text": f"{condominium_name}"
                }
            ]
        }

    ]

    _send_info_message(contact.replace('(', '').replace(')', '').replace(' ', '').replace('-', '').replace('+', ''),
                       "encomenda", message_params)


def _send_info_message(to, template, message_list):

    url = f"https://graph.facebook.com/v22.0/{settings.WABA_PHONE_ID}/messages"
    headers = {"Authorization": f"Bearer {settings.WABA_TOKEN}", "Content-type": "application/json"}
    data = {
        "messaging_product": "whatsapp",
        "to": f"55{to}",
        # "to": f"351936242540",
        "type": "template",
        "template": {
            "name": f"{template}",
            "language": {
                "code": "pt_BR"
            },
            "components": message_list
        }
    }

    json_string = json.dumps(data)
    response = requests.post(url, headers=headers, data=json_string)
    return response.json()


def msg_aux(request):
    send_info_message("Residencial Estrela",
                         "José das couves",
                         "936242540",
                         "Seu cadastro foi realizado com sucesso")

    return redirect(reverse("info:dashboard"))


def webhook(request):
    if request.method == 'GET':
        mode = request.GET.get("hub.mode")
        token = request.GET.get("hub.verify_token")
        challenge = request.GET.get("hub.challenge")
        if mode and token:
            # Check the mode and token sent are correct
            if mode == "subscribe" and token == settings.WABA_VERIFY_TOKEN:
                # Respond with 200 OK and challenge token from the request
                print("WEBHOOK_VERIFIED")
                return HttpResponse()
            else:
                # Responds with '403 Forbidden' if verify tokens do not match
                print("VERIFICATION_FAILED")
                return HttpResponseForbidden()
        else:
            # Responds with '400 Bad Request' if verify tokens do not match
            print("MISSING_PARAMETER")
            return HttpResponseBadRequest()

    elif request.method == 'POST':
        # Parse Request body in json format
        body = request.get_json()
        print(f"request body: {body}")

        return JsonResponse(body)

        # try:
        #     # info on WhatsApp text message payload:
        #     # https://developers.facebook.com/docs/whatsapp/cloud-api/webhooks/payload-examples#text-messages
        #     if body.get("object"):
        #         if (
        #                 body.get("entry")
        #                 and body["entry"][0].get("changes")
        #                 and body["entry"][0]["changes"][0].get("value")
        #                 and body["entry"][0]["changes"][0]["value"].get("messages")
        #                 and body["entry"][0]["changes"][0]["value"]["messages"][0]
        #         ):
        #             handle_whatsapp_message(body)
        #         return jsonify({"status": "ok"}), 200
        #     else:
        #         # if the request is not a WhatsApp API event, return an error
        #         return (
        #             jsonify({"status": "error", "message": "Not a WhatsApp API event"}),
        #             404,
        #         )
        # # catch all other errors and return an internal server error
        # except Exception as e:
        #     print(f"unknown error: {e}")
        #     return jsonify({"status": "error", "message": str(e)}), 500
