from io import BytesIO

import pytz
from django.contrib.auth.decorators import login_required
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMultiAlternatives
from django.forms import formset_factory
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.html import strip_tags
from django.contrib import messages as info_messages

from info.forms import ResidentMessageForm, MessageFileForm, BlockMessageForm, MessageAllForm, ViewMessageForm
from info.models import Block, Apartment, Resident, HowTo, Message, MessageFileModel, CondominiumProfile, Signature, \
    Notification
from info.utils import get_condominium, add_signature_to_data, add_notification


FIXED_TZ = pytz.timezone("America/Sao_Paulo")


@login_required(login_url='info:sign-in')
def messages(request):
    condominium = get_condominium(request)
    context = {'user': condominium}
    how_to_attachments = HowTo.objects.get(name__exact="Mensagem > CHAT GPT")
    if how_to_attachments.kind == "Texto":
        context['how_to_chat_gpt_text'] = how_to_attachments.value
    else:
        context['how_to_chat_gpt_link'] = how_to_attachments.value
    return render(request, "info/condominium/messages/messages.html", context=context)


@login_required(login_url='info:sign-in')
def message_list(request):
    condominium = get_condominium(request)
    _messages = Message.objects.filter(condominium=condominium).order_by("-created")

    search_created = request.GET.get('message_created')
    search_block = request.GET.get('message_block')
    search_apartment = request.GET.get('message_apartment')

    if search_block:
        _messages = _messages.filter(block__contains=search_block)

    if search_apartment:
        _messages = _messages.filter(apartment__contains=search_apartment)

    if search_created:
        _messages = _messages.filter(created=search_created)

    context = {'messages': _messages,
               }

    return render(request, "info/condominium/messages/message_list.html", context=context)


@login_required(login_url='info:sign-in')
def message_resident(request):
    condominium = get_condominium(request)
    blocks = Block.objects.filter(condominium=condominium)
    form = ResidentMessageForm(request.POST or None, blocks=blocks)

    MessageFilesFormset = formset_factory(form=MessageFileForm, extra=0)
    files_formset = MessageFilesFormset(request.POST or None, files=request.FILES or None, prefix="files")

    if request.method == "POST":

        apartment = Apartment.objects.get(pk=int(request.POST.get('apartment')))
        residents = Resident.objects.filter(apartment=apartment)

        message = Message()
        message.condominium = condominium
        message.block = apartment.block.name
        message.apartment = str(apartment.number) + " " + apartment.complement
        message.kind = "Ao Morador"

        to_list = []
        for resident in residents:
            if resident.email:
                to_list.extend(resident.email.split(';'))

        subject = 'Comunicado do ' + condominium.condominium_name
        data = add_signature_to_data(request)
        data['message'] = request.POST.get('message')
        html_content = render_to_string(
            'info/condominium/messages/message.html',
            data
        )

        text_content = strip_tags(html_content)
        msg = EmailMultiAlternatives(subject, text_content, to=to_list)
        msg.attach_alternative(html_content, "text/html")
        message.set_to_list(to_list)
        message.message = request.POST.get('message')
        message.save()

        if files_formset.is_valid():
            for file_form in files_formset:
                if file_form.cleaned_data['attachment']:
                    attachment_file = file_form.cleaned_data['attachment']
                    attachment_content = attachment_file.read()
                    attachment_stream = BytesIO(attachment_content)
                    attachment_stream.seek(0)
                    msg.attach(filename=attachment_file.name, content=attachment_stream.read(),
                               mimetype=attachment_file.content_type)

                    file_model = MessageFileModel()
                    file_model.message = message
                    file_model.file = file_form.cleaned_data['attachment']
                    file_model.save()

        msg.send()

        add_notification(condominium, to_list, "Um email foi enviado para você, com o assunto: " + subject.upper() +
                         ". Verifique a sua caixa de entrada ou lixo eletrônico.")

        info_messages.success(request, "O morador foi notificado no email cadastrado")
        return redirect(reverse('info:dashboard'))

    context = {'form': form,
               'files_formset': files_formset,
               }

    how_to_attachments = HowTo.objects.get(name__exact="Mensagem > Anexos")
    if how_to_attachments.kind == "Texto":
        context['how_to_attachments_text'] = how_to_attachments.value
    else:
        context['how_to_attachments_link'] = how_to_attachments.value

    return render(request, "info/condominium/messages/message_resident.html", context=context)


@login_required(login_url='info:sign-in')
def message_block(request):
    request_user = request.user
    condominium = get_condominium(request)
    blocks = Block.objects.filter(condominium=condominium)
    form = BlockMessageForm(request.POST or None, blocks=blocks)

    MessageFilesFormset = formset_factory(form=MessageFileForm, extra=0)
    files_formset = MessageFilesFormset(request.POST or None, files=request.FILES or None, prefix="files")

    if request.method == "POST":
        block = Block.objects.get(pk=int(request.POST.get('block')))

        message = Message()
        message.condominium = condominium
        message.block = block.name
        message.apartment = "Todos"
        message.kind = "Ao Bloco"

        residents = Resident.objects.filter(apartment__block=block)

        to_list = []
        for resident in residents:
            if resident.email:
                to_list.extend(resident.email.split(';'))

        subject = 'Comunicado do ' + condominium.condominium_name
        data = add_signature_to_data(request)
        data['message'] = request.POST.get('message')
        html_content = render_to_string(
            'info/condominium/messages/message.html',
            data
        )

        text_content = strip_tags(html_content)
        msg = EmailMultiAlternatives(subject, text_content, to=to_list)
        msg.attach_alternative(html_content, "text/html")
        message.set_to_list(to_list)
        message.message = request.POST.get('message')
        message.save()

        if files_formset.is_valid():
            for file_form in files_formset:
                if file_form.cleaned_data['attachment']:
                    attachment_file = file_form.cleaned_data['attachment']
                    attachment_content = attachment_file.read()
                    attachment_stream = BytesIO(attachment_content)
                    attachment_stream.seek(0)
                    msg.attach(filename=attachment_file.name, content=attachment_stream.read(),
                               mimetype=attachment_file.content_type)

                    file_model = MessageFileModel()
                    file_model.message = message
                    file_model.file = file_form.cleaned_data['attachment']
                    file_model.save()

        msg.send()

        add_notification(condominium, to_list, "Um email foi enviado para você, com o assunto: " + subject.upper() +
                         ". Verifique a sua caixa de entrada ou lixo eletrônico.")

        info_messages.success(request, "Os moradores foram notificados no email cadastrado")
        return redirect(reverse('info:dashboard'))

    context = {'form': form,
               'files_formset': files_formset,
               }
    how_to_attachments = HowTo.objects.get(name__exact="Mensagem > Anexos")
    if how_to_attachments.kind == "Texto":
        context['how_to_attachments_text'] = how_to_attachments.value
    else:
        context['how_to_attachments_link'] = how_to_attachments.value

    return render(request, "info/condominium/messages/message_block.html", context=context)


@login_required(login_url='info:sign-in')
def message_all(request):
    condominium = get_condominium(request)

    form = MessageAllForm(request.POST or None)

    MessageFilesFormset = formset_factory(form=MessageFileForm, extra=0)
    files_formset = MessageFilesFormset(request.POST or None, files=request.FILES or None, prefix="files")

    if request.method == "POST":

        message = Message()
        message.condominium = condominium
        message.block = "Todos"
        message.apartment = "Todos"
        message.kind = "Ao Condomínio"

        residents = Resident.objects.filter(apartment__block__condominium=condominium)

        to_list = []
        for resident in residents:
            if resident.email:
                to_list.extend(resident.email.split(';'))

        subject = 'Comunicado do ' + condominium.condominium_name
        data = add_signature_to_data(request)
        data['message'] = request.POST.get('message')
        html_content = render_to_string(
            'info/condominium/messages/message.html',
            data
        )

        text_content = strip_tags(html_content)
        msg = EmailMultiAlternatives(subject, text_content, to=to_list)
        msg.attach_alternative(html_content, "text/html")
        message.set_to_list(to_list)
        message.message = request.POST.get('message')
        message.save()

        if files_formset.is_valid():
            for file_form in files_formset:
                if file_form.cleaned_data['attachment']:
                    attachment_file = file_form.cleaned_data['attachment']
                    attachment_content = attachment_file.read()
                    attachment_stream = BytesIO(attachment_content)
                    attachment_stream.seek(0)
                    msg.attach(filename=attachment_file.name, content=attachment_stream.read(),
                               mimetype=attachment_file.content_type)

                    file_model = MessageFileModel()
                    file_model.message = message
                    file_model.file = file_form.cleaned_data['attachment']
                    file_model.save()

        msg.send()

        add_notification(condominium, to_list, "Um email foi enviado para você, com o assunto: " + subject.upper() +
                         ". Verifique a sua caixa de entrada ou lixo eletrônico.")

        info_messages.success(request, "Os moradores foram notificados no email cadastrado")
        return redirect(reverse('info:dashboard'))

    context = {'form': form,
               'files_formset': files_formset,
               }

    how_to_attachments = HowTo.objects.get(name__exact="Mensagem > Anexos")
    if how_to_attachments.kind == "Texto":
        context['how_to_attachments_text'] = how_to_attachments.value
    else:
        context['how_to_attachments_link'] = how_to_attachments.value

    return render(request, "info/condominium/messages/message_all.html", context=context)


@login_required(login_url='info:sign-in')
def view_message(request, id):
    condominium = get_condominium(request)
    message = get_object_or_404(Message, pk=id, condominium=condominium)

    form = ViewMessageForm(instance=message)

    form.fields['sent'].initial = message.created.astimezone(FIXED_TZ).strftime('%Y-%m-%d %H:%M:%S')

    context = {'form': form,
               'id': message.id,
               }

    message_files = MessageFileModel.objects.filter(message=message)
    if len(message_files) > 0:
        files = []
        for file in message_files:
            files.append(file)

        context['files'] = files

    return render(request, "info/condominium/messages/view_message.html", context=context)


@login_required(login_url='info:sign-in')
def notify(request):
    condominium = get_condominium(request)
    context = {'user': condominium}

    how_to_message = HowTo.objects.get(name__exact="Dashboard > Comunicados")
    if how_to_message.kind == "Texto":
        context['how_to_message_text'] = how_to_message.value
    else:
        context['how_to_message_link'] = how_to_message.value
    return render(request, "info/condominium/messages/notify.html", context=context)


@login_required(login_url='info:sign-in')
def notification_list(request):
    condominium = get_condominium(request)
    _messages = Message.objects.filter(condominium=condominium, notify=True).order_by("-created")

    search_created = request.GET.get('message_created')
    search_block = request.GET.get('message_block')
    search_apartment = request.GET.get('message_apartment')

    if search_block:
        _messages = _messages.filter(block__contains=search_block)

    if search_apartment:
        _messages = _messages.filter(apartment__contains=search_apartment)

    if search_created:
        _messages = _messages.filter(created=search_created)

    context = {'messages': _messages,
               }

    how_to_message_list = HowTo.objects.get(name__exact="Mensagens > Listagem")
    if how_to_message_list.kind == "Texto":
        context['how_to_message_list_text'] = how_to_message_list.value
    else:
        context['how_to_message_list_link'] = how_to_message_list.value

    return render(request, "info/condominium/messages/notification_list.html", context=context)


@login_required(login_url='info:sign-in')
def notify_resident(request):
    condominium = get_condominium(request)
    blocks = Block.objects.filter(condominium=condominium)
    form = ResidentMessageForm(request.POST or None, blocks=blocks)

    MessageFilesFormset = formset_factory(form=MessageFileForm, extra=0)
    files_formset = MessageFilesFormset(request.POST or None, files=request.FILES or None, prefix="files")

    if request.method == "POST":
        apartment = Apartment.objects.get(pk=int(request.POST.get('apartment')))
        resident_choice = request.POST.get('resident')

        message = Message()
        message.condominium = condominium
        message.block = apartment.block.name
        message.apartment = str(apartment.number) + " " + apartment.complement

        to_list = []
        if resident_choice == 'all':
            message.resident = 'all'
            residents = Resident.objects.filter(apartment=apartment)
            for resident in residents:
                if resident.email:
                    to_list.extend(resident.email.split(';'))
        else:
            resident = Resident.objects.get(pk=int(resident_choice))
            message.resident = resident.name
            if resident.email:
                to_list.extend(resident.email.split(';'))

        message.kind = "Ao Morador"
        message.message = request.POST.get('message')
        message.set_to_list(to_list)
        message.notify = True
        message.save()

        subject = 'Notificação do ' + condominium.condominium_name
        data = add_signature_to_data(request)
        data['message'] = request.POST.get('message')
        html_content = render_to_string(
            'info/condominium/messages/notification.html',
            data
        )

        text_content = strip_tags(html_content)
        msg = EmailMultiAlternatives(subject, text_content, to=to_list)
        msg.attach_alternative(html_content, "text/html")

        if files_formset.is_valid():
            for file_form in files_formset:
                if file_form.cleaned_data['attachment']:
                    attachment_file = file_form.cleaned_data['attachment']
                    attachment_content = attachment_file.read()
                    attachment_stream = BytesIO(attachment_content)
                    attachment_stream.seek(0)
                    msg.attach(filename=attachment_file.name, content=attachment_stream.read(),
                               mimetype=attachment_file.content_type)

                    file_model = MessageFileModel()
                    file_model.message = message
                    file_model.file = file_form.cleaned_data['attachment']
                    file_model.save()

        msg.send()

        add_notification(condominium, to_list, "Uma notificação foi enviada para você, com o assunto: " + subject.upper() +
                         ". Verifique a sua caixa de entrada ou lixo eletrônico.")

        info_messages.success(request, "O morador foi notificado no email cadastrado")
        return redirect(reverse('info:dashboard'))

    context = {
        'form': form,
        'files_formset': files_formset,
    }

    how_to_attachments = HowTo.objects.get(name__exact="Mensagem > Anexos")
    if how_to_attachments.kind == "Texto":
        context['how_to_attachments_text'] = how_to_attachments.value
    else:
        context['how_to_attachments_link'] = how_to_attachments.value

    return render(request, "info/condominium/messages/notify_resident.html", context=context)


@login_required(login_url='info:sign-in')
def notify_block(request):
    request_user = request.user
    condominium = get_condominium(request)
    blocks = Block.objects.filter(condominium=condominium)
    form = BlockMessageForm(request.POST or None, blocks=blocks)

    MessageFilesFormset = formset_factory(form=MessageFileForm, extra=0)
    files_formset = MessageFilesFormset(request.POST or None, files=request.FILES or None, prefix="files")

    if request.method == "POST":
        block = Block.objects.get(pk=int(request.POST.get('block')))

        message = Message()
        message.condominium = condominium
        message.block = block.name
        message.apartment = "Todos"
        message.kind = "Ao Bloco"

        residents = Resident.objects.filter(apartment__block=block)

        to_list = []
        for resident in residents:
            if resident.email:
                to_list.extend(resident.email.split(';'))

        subject = 'Notificação do ' + condominium.condominium_name
        data = add_signature_to_data(request)
        data['message'] = request.POST.get('message')
        html_content = render_to_string(
            'info/condominium/messages/notification.html',
            data
        )

        text_content = strip_tags(html_content)
        msg = EmailMultiAlternatives(subject, text_content, to=to_list)
        msg.attach_alternative(html_content, "text/html")
        message.set_to_list(to_list)
        message.message = request.POST.get('message')
        message.notify = True
        message.save()

        if files_formset.is_valid():
            for file_form in files_formset:
                if file_form.cleaned_data['attachment']:
                    attachment_file = file_form.cleaned_data['attachment']
                    attachment_content = attachment_file.read()
                    attachment_stream = BytesIO(attachment_content)
                    attachment_stream.seek(0)
                    msg.attach(filename=attachment_file.name, content=attachment_stream.read(),
                               mimetype=attachment_file.content_type)

                    file_model = MessageFileModel()
                    file_model.message = message
                    file_model.file = file_form.cleaned_data['attachment']
                    file_model.save()

        msg.send()

        add_notification(condominium, to_list, "Uma notificação foi enviada para você, com o assunto: " + subject.upper() +
                         ". Verifique a sua caixa de entrada ou lixo eletrônico.")

        info_messages.success(request, "Os moradores foram notificados no email cadastrado")
        return redirect(reverse('info:dashboard'))

    context = {'form': form,
               'files_formset': files_formset,
               }
    how_to_attachments = HowTo.objects.get(name__exact="Mensagem > Anexos")
    if how_to_attachments.kind == "Texto":
        context['how_to_attachments_text'] = how_to_attachments.value
    else:
        context['how_to_attachments_link'] = how_to_attachments.value

    return render(request, "info/condominium/messages/notify_block.html", context=context)


@login_required(login_url='info:sign-in')
def notify_all(request):
    condominium = get_condominium(request)

    form = MessageAllForm(request.POST or None)

    MessageFilesFormset = formset_factory(form=MessageFileForm, extra=0)
    files_formset = MessageFilesFormset(request.POST or None, files=request.FILES or None, prefix="files")

    if request.method == "POST":

        message = Message()
        message.condominium = condominium
        message.block = "Todos"
        message.apartment = "Todos"
        message.kind = "Ao Condomínio"

        residents = Resident.objects.filter(apartment__block__condominium=condominium)

        to_list = []
        for resident in residents:
            if resident.email:
                to_list.extend(resident.email.split(';'))

        subject = 'Notificação do ' + condominium.condominium_name
        data = add_signature_to_data(request)
        data['message'] = request.POST.get('message')
        html_content = render_to_string(
            'info/condominium/messages/notification.html',
            data
        )

        text_content = strip_tags(html_content)
        msg = EmailMultiAlternatives(subject, text_content, to=to_list)
        msg.attach_alternative(html_content, "text/html")
        message.set_to_list(to_list)
        message.message = request.POST.get('message')
        message.notify = True
        message.save()

        if files_formset.is_valid():
            for file_form in files_formset:
                if file_form.cleaned_data['attachment']:
                    attachment_file = file_form.cleaned_data['attachment']
                    attachment_content = attachment_file.read()
                    attachment_stream = BytesIO(attachment_content)
                    attachment_stream.seek(0)
                    msg.attach(filename=attachment_file.name, content=attachment_stream.read(),
                               mimetype=attachment_file.content_type)

                    file_model = MessageFileModel()
                    file_model.message = message
                    file_model.file = file_form.cleaned_data['attachment']
                    file_model.save()

        msg.send()

        add_notification(condominium, to_list, "Uma notificação foi enviada para você, com o assunto: " + subject.upper() +
                         ". Verifique a sua caixa de entrada ou lixo eletrônico.")

        info_messages.success(request, "Os moradores foram notificados no email cadastrado")
        return redirect(reverse('info:dashboard'))

    context = {'form': form,
               'files_formset': files_formset,
               }

    how_to_attachments = HowTo.objects.get(name__exact="Mensagem > Anexos")
    if how_to_attachments.kind == "Texto":
        context['how_to_attachments_text'] = how_to_attachments.value
    else:
        context['how_to_attachments_link'] = how_to_attachments.value

    return render(request, "info/condominium/messages/notify_all.html", context=context)


@login_required(login_url='info:sign-in')
def view_notification(request, id):
    condominium = get_condominium(request)
    message = get_object_or_404(Message, pk=id, condominium=condominium)

    form = ViewMessageForm(instance=message)

    form.fields['sent'].initial = message.created.astimezone(FIXED_TZ).strftime('%Y-%m-%d %H:%M:%S')

    context = {'form': form,
               'id': message.id,
               }

    message_files = MessageFileModel.objects.filter(message=message)
    if len(message_files) > 0:
        files = []
        for file in message_files:
            files.append(file)

        context['files'] = files

    return render(request, "info/condominium/messages/view_notification.html", context=context)
