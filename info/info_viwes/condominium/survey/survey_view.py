import base64
import io
import secrets

import pytz
from PIL import Image
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.sites.shortcuts import get_current_site
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.mail import EmailMultiAlternatives
from django.db.models import Sum
from django.forms import formset_factory
from django.shortcuts import redirect, render, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes, force_str
from django.utils.html import strip_tags
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode

from info.forms import SurveyForm, SurveyAnswerForm, SurveyAnswerModelForm, SurveyAddAnswerForm
from info.info_viwes.condominium.report.report_view import _survey_pdf
from info.info_viwes.condominium_view import send_link_to
from info.models import CondominiumProfile, SurveyModel, SurveyOptionModel, Resident, TokenModel, HowTo, \
    SurveyAnswerModel, UserLocation, Block, Apartment
from info.utils import get_condominium, add_signature_to_data, add_notification, add_manager_notification, \
    EmailVerificationTokenGenerator


FIXED_TZ = pytz.timezone("America/Sao_Paulo")


@login_required(login_url='info:sign-in')
def add_survey(request):
    condominium = get_condominium(request)

    user = CondominiumProfile.objects.get(pk=int(request.user.id))
    ip_address = request.META.get('HTTP_X_FORWARDED_FOR') or request.META.get('HTTP_CLIENT_IP')

    if not ip_address:
        ip_address = '127.0.0.1'

    location = UserLocation.objects.filter(condominium=user, ip_address=ip_address).order_by('-created').first()

    form = SurveyForm(request.POST or None)
    SurveyOptionFormset = formset_factory(form=SurveyAnswerForm, extra=0)
    options_formset = SurveyOptionFormset(request.POST or None, prefix="option")

    if request.method == "POST":

        if all([form.is_valid(), options_formset.is_valid()]):

            try:
                survey = SurveyModel.objects.get(condominium=condominium, question=form.cleaned_data['question'])
            except SurveyModel.DoesNotExist:

                survey = SurveyModel()
                survey.question = form.cleaned_data['question']
                survey.condominium = condominium
                survey.location = location
                survey.save()

            options = SurveyOptionModel.objects.filter(survey=survey)
            for opt in options:
                opt.delete()

            counter = 0
            for option_form in options_formset:
                option = SurveyOptionModel()
                option.survey = survey
                option.option = option_form.cleaned_data['answer'] if 'answer' in option_form.cleaned_data else ""
                option.is_link = option_form.cleaned_data['is_link'] if 'is_link' in option_form.cleaned_data else False
                option.image = request.FILES.get('option-' + str(counter) + '-image') or None
                option.save()
                counter += 1

        send_to = form.cleaned_data['send_to']
        receivers = []
        if send_to == "MORADORES":
            residents = Resident.objects.filter(apartment__block__condominium=condominium)
            for resident in residents:
                receivers.append(resident.email)
        elif send_to == "FUNCIONÁRIOS":
            residents = CondominiumProfile.objects.filter(work_for=condominium)
            for resident in residents:
                receivers.append(resident.email)
        else:
            residents = Resident.objects.filter(apartment__block__condominium=condominium)
            for resident in residents:
                receivers.append(resident.email)
            residents = CondominiumProfile.objects.filter(work_for=condominium)
            for resident in residents:
                receivers.append(resident.email)

        for receive in receivers:
            if receive:
                for email in receive.split(';'):
                    token = secrets.token_urlsafe(16)
                    email_token = TokenModel(email=email, token=token, survey=survey)
                    email_token.save()

                    subject = 'Nova Enquete do ' + condominium.condominium_name
                    data = add_signature_to_data(request)
                    data['question'] = survey.question
                    data['domain'] = get_current_site(request).domain
                    data['token'] = urlsafe_base64_encode(force_bytes(token))
                    data['survey_email'] = urlsafe_base64_encode(force_bytes(email))
                    data['uid'] = urlsafe_base64_encode(force_bytes(survey.pk))
                    html_content = render_to_string(
                        'info/condominium/survey/survey_message.html',
                        data
                    )

                    text_content = strip_tags(html_content)
                    msg = EmailMultiAlternatives(subject, text_content, to=[email])
                    msg.attach_alternative(html_content, "text/html")
                    msg.send()

                    try:
                        user = CondominiumProfile.objects.get(email=email, resident_in=condominium)
                        survey.allowed_users.add(user)
                        survey.save()
                    except CondominiumProfile.DoesNotExist:
                        continue

                    add_notification(condominium, [email], "Uma enquete sobre " + survey.question.upper() +
                                     " foi solicitada a você. Verifique sua caixa de entrada, lixo eletrônico ou no menu aplicação", None, "/my-surveys")

        messages.success(request, "Enquete enviada!")

        return redirect(reverse('info:dashboard'))

    context = {'form': form,
               'options_formset': options_formset,
               }

    how_to_answers = HowTo.objects.get(name__exact="Enquete > Respostas")
    if how_to_answers.kind == "Texto":
        context['how_to_answers_text'] = how_to_answers.value
    else:
        context['how_to_answers_link'] = how_to_answers.value

    return render(request, "info/condominium/survey/add_survey.html", context=context)


def my_survey(request):
    condominium = get_condominium(request)
    surveys = SurveyModel.objects.filter(condominium=condominium).order_by('created')

    survey_list = []

    for survey in surveys:
        if request.user in survey.allowed_users.all():
            survey_obj = {
                'id': survey.id,
                'question': survey.question,
                'is_ended': survey.is_ended
            }

            survey_list.append(survey_obj)

    context = {'surveys': survey_list,
               }

    how_to_survey_list = HowTo.objects.get(name__exact="Enquetes > Listagem")
    if how_to_survey_list.kind == "Texto":
        context['how_to_survey_list_text'] = how_to_survey_list.value
    else:
        context['how_to_survey_list_link'] = how_to_survey_list.value

    return render(request, "info/condominium/survey/my_surveys.html", context=context)


def add_survey_answer(request, uidb64, token, email):
    uid = force_str(urlsafe_base64_decode(uidb64))
    d_token = force_str(urlsafe_base64_decode(token))
    d_email = force_str(urlsafe_base64_decode(email))

    survey = SurveyModel.objects.get(pk=uid)

    if survey.is_ended:
        messages.success(request, "A Enquete já foi encerrada, Obrigado!")
        return render(request, "info/condominium/review/thank_you.html")

    try:
        resident = Resident.objects.get(email=d_email)
        if resident.defaulter:
            messages.error(request, "Acesso bloqueado!")
            messages.error(request, "Favor entrar em contato com sua administradora para maiores informações")
            return redirect(reverse('info:dashboard'))

        user = CondominiumProfile.objects.get(email=d_email, condominium_name=resident.name)
        if user.defaulter:
            messages.error(request, "Acesso bloqueado!")
            messages.error(request, "Favor entrar em contato com sua administradora para maiores informações")
            return redirect(reverse('info:dashboard'))

    except Resident.DoesNotExist:
        pass
    except CondominiumProfile.DoesNotExist:
        pass

    options = SurveyOptionModel.objects.filter(survey=survey)

    try:
        token_obj = TokenModel.objects.get(token=d_token, is_used=False, email=d_email)

        blocks = Block.objects.filter(condominium=survey.condominium)

        form = SurveyAddAnswerForm(request.POST or None, blocks=blocks)
        if request.method == "POST":
            token_obj.is_used = True
            token_obj.save()

            survey_option = SurveyOptionModel.objects.filter(survey=survey,
                                                             option=request.POST.get('optionsRadio')).first()
            answer = SurveyAnswerModel()
            answer.option = survey_option
            answer.survey = survey
            answer.name = request.POST.get('name') or ""

            kind = request.POST.get('kind')
            if kind == "FUNCIONÁRIO":
                answer.address = "FUNCIONÁRIO"
            else:
                apartment = Apartment.objects.get(pk=int(request.POST.get('apartment')))
                answer.address = apartment.block.name + "/" + str(apartment.number) + " " + apartment.complement

            answer.email = d_email

            answer_pic = request.POST.get('webimg')
            if answer_pic:
                image_data = answer_pic.split(',')[1]  # Remove the data URI prefix
                image_bytes = base64.b64decode(image_data)
                image_file = io.BytesIO(image_bytes)
                Image.open(image_file)
                image_file.seek(0)
                answer.answer_pic = InMemoryUploadedFile(
                    image_file, None, d_email + '.jpg', 'image/jpeg', len(image_bytes), None)

            answer.save()


            messages.success(request, "Resposta recebida com sucesso! Seu voto será validado por um administrador")
            add_manager_notification(survey.condominium,
                                     "NOVA RESPOSTA RECEBIDA PARA A ENQUETE " + survey.question.upper() +
                                     ". Faça a validação do voto nos detalhes da enquete.")

            return render(request, "info/condominium/review/thank_you.html")
    except TokenModel.DoesNotExist:
        messages.success(request, "Você já respondeu a essa enquete, Obrigado!")
        return render(request, "info/condominium/review/thank_you.html")

    context = {'question': survey.question,
               'options': options,
               'form': form
               }
    return render(request, "info/condominium/survey/add_survey_answer.html", context=context)


@login_required(login_url='info:sign-in')
def add_user_survey_answer(request, id):
    condominium = get_condominium(request)
    user = CondominiumProfile.objects.get(pk=int(request.user.id))

    if user.defaulter:
        messages.error(request, "Acesso bloqueado!")
        messages.error(request, "Favor entrar em contato com sua administradora para maiores informações")
        return redirect(reverse('info:dashboard'))

    resident = Resident.objects.get(name=user.condominium_name, email=user.email)
    survey = SurveyModel.objects.get(pk=id)

    if survey.is_ended:
        messages.success(request, "A Enquete já foi encerrada, Obrigado!")
        return render(request, "info/condominium/review/thank_you.html")
    options = SurveyOptionModel.objects.filter(survey=survey)

    try:
        tokens = TokenModel.objects.filter(is_used=False, email=user.email, survey=survey)
        if not len(tokens):
            messages.success(request, "Você já respondeu a essa enquete, Obrigado!")
            return render(request, "info/condominium/review/thank_you.html")

        token_obj = None
        for token in tokens:
            if not token_obj:
                token_obj = token
            else:
                token.delete()

        if request.method == "POST":
            token_obj.is_used = True
            token_obj.save()

            survey_option = SurveyOptionModel.objects.filter(survey=survey,
                                                             option=request.POST.get('optionsRadio')).first()
            answer = SurveyAnswerModel()
            answer.option = survey_option
            answer.survey = survey
            answer.name = request.POST.get('name') or ""
            answer.address = (resident.apartment.block.name + "/" + str(resident.apartment.number) + " " +
                              resident.apartment.complement)
            answer.email = user.email

            answer_pic = request.POST.get('webimg')
            if answer_pic:
                image_data = answer_pic.split(',')[1]  # Remove the data URI prefix
                image_bytes = base64.b64decode(image_data)
                image_file = io.BytesIO(image_bytes)
                Image.open(image_file)
                image_file.seek(0)
                answer.answer_pic = InMemoryUploadedFile(
                    image_file, None, user.condominium_name + '.jpg', 'image/jpeg', len(image_bytes), None)

            answer.save()

            messages.success(request, "Resposta recebida com sucesso! Seu voto será validado por um administrador")
            add_manager_notification(survey.condominium,
                                     "NOVA RESPOSTA RECEBIDA PARA A ENQUETE " + survey.question.upper() +
                                     ". Faça a validação do voto nos detalhes da enquete.")

            return render(request, "info/condominium/review/thank_you.html")
    except TokenModel.DoesNotExist:
        messages.success(request, "Você já respondeu a essa enquete, Obrigado!")
        return render(request, "info/condominium/review/thank_you.html")

    context = {'question': survey.question,
               'options': options,
               }
    return render(request, "info/condominium/survey/add_survey_answer.html", context=context)


@login_required(login_url='info:sign-in')
def add_anonimous_survey_answer(request, uidb64, token, email):

    uid = force_str(urlsafe_base64_decode(uidb64))
    # redirecionamento no caso do síndico clicar no link
    return redirect(reverse('info:survey-user-answer', args=[int(uid)]))


@login_required(login_url='info:sign-in')
def surveys(request):
    condominium = get_condominium(request)
    surveys = SurveyModel.objects.filter(condominium=condominium).order_by("-created")

    survey_list = []

    for survey in surveys:
        survey_obj = {
            'id': survey.id,
            'question': survey.question,
            'votes': SurveyOptionModel.objects.filter(survey=survey).aggregate(Sum('votes'))['votes__sum'] or 0,
        }

        survey_list.append(survey_obj)

    context = {'surveys': survey_list,
               'user': condominium
               }

    how_to_survey_list = HowTo.objects.get(name__exact="Enquetes > Listagem")
    if how_to_survey_list.kind == "Texto":
        context['how_to_survey_list_text'] = how_to_survey_list.value
    else:
        context['how_to_survey_list_link'] = how_to_survey_list.value

    return render(request, "info/condominium/survey/surveys.html", context=context)


@login_required(login_url='info:sign-in')
def survey_detail(request, id):
    condominium = get_condominium(request)
    survey = SurveyModel.objects.get(pk=id)
    options = SurveyOptionModel.objects.filter(survey=survey)
    context = {'survey': survey,
               'options': options,
               'total_votes': options.aggregate(Sum('votes'))['votes__sum'] or 0,
               'id': survey.id,
               'user': condominium
               }
    return render(request, "info/condominium/survey/survey_detail.html", context=context)


def end_survey(request, id):
    condominium = get_condominium(request)
    survey = SurveyModel.objects.get(pk=id)

    if request.method == 'POST':

        survey.is_ended = True
        survey.save()

        if request.POST.get("notify") is not None and request.POST.get("notify") == "on":
            receivers = []

            survey_answers = SurveyAnswerModel.objects.filter(survey=survey)

            for answer in survey_answers:
                receivers.append(answer.email)

            add_notification(condominium, receivers, "Resultado da enquete sobre " + survey.question.upper() +
                             " foi disponibilizado. Acesse através do menu Enquetes.", request, "/my-surveys")

        messages.success(request, "Enquete Encerrada!")
        return redirect(reverse('info:surveys'))
    return render(request, "info/condominium/survey/end_survey.html")


@login_required(login_url='info:sign-in')
def approve_answers(request, id):
    survey = SurveyModel.objects.get(pk=id)

    answers_to_approve = SurveyAnswerModel.objects.filter(survey=survey, is_valid=False).order_by("-created")

    search_resident = request.GET.get('search_resident')
    search_email = request.GET.get('search_email')
    search_block = request.GET.get('search_block')
    search_apartment = request.GET.get('search_apartment')

    if search_resident:
        answers_to_approve = answers_to_approve.filter(name__contains=search_resident)


    if search_email:
        answers_to_approve = answers_to_approve.filter(email__contains=search_email)

    answers_objs = []

    for answer in answers_to_approve:
        added = False
        slash_pos = answer.address.find('/')

        if search_block and answer.address[:int(slash_pos)].find(search_block) != -1:
            answer_obj = {
                "id": answer.id,
                "email": answer.email,
                "created": answer.created.astimezone(FIXED_TZ),
                "name": answer.name,
                "block": answer.address[:int(slash_pos)],
                "apartment": answer.address[int(slash_pos) + 1:]
            }
            answers_objs.append(answer_obj)
            added = True

        if search_apartment and answer.address[int(slash_pos)+1:].find(search_apartment) != -1 and not added:
            answer_obj = {
                "id": answer.id,
                "email": answer.email,
                "created": answer.created.astimezone(FIXED_TZ),
                "name": answer.name,
                "block": answer.address[:int(slash_pos)],
                "apartment": answer.address[int(slash_pos) + 1:]
            }
            answers_objs.append(answer_obj)

        if not search_block and not search_apartment:
            answer_obj = {
                "id": answer.id,
                "email": answer.email,
                "created": answer.created.astimezone(FIXED_TZ),
                "name": answer.name,
                "block": answer.address[:int(slash_pos)],
                "apartment": answer.address[int(slash_pos) + 1:]
            }
            answers_objs.append(answer_obj)

    context = {
        'answers': answers_objs,
        'question': survey.question,
        'survey_id': id
    }

    return render(request, "info/condominium/survey/approve_answers.html", context=context)


@login_required(login_url='info:sign-in')
def approve_all_answers(request, id):
    survey = SurveyModel.objects.get(pk=id)

    answers_to_approve = SurveyAnswerModel.objects.filter(survey=survey, is_valid=False).order_by("-created")

    for answer in answers_to_approve:
        answer.is_valid = True
        answer.save()
        option = SurveyOptionModel.objects.get(survey=answer.survey, option__iexact=answer.option.option)
        option.votes = option.votes + 1
        option.save()

    messages.success(request, "Votos Aprovados!")
    return redirect(reverse('info:approve-answers', args=[int(id)]))


@login_required(login_url='info:sign-in')
def reprove_all_answers(request, id):
    survey = SurveyModel.objects.get(pk=id)

    answers_to_approve = SurveyAnswerModel.objects.filter(survey=survey, is_valid=False).order_by("-created")

    for answer in answers_to_approve:
        answer.delete()

    messages.success(request, "Votos Impugnados, não serão considerados no resultado final!")
    return redirect(reverse('info:approve-answers', args=[int(id)]))


@login_required(login_url='info:sign-in')
def answer_detail(request, id):
    answer = SurveyAnswerModel.objects.get(pk=id)
    context = {'question': answer.survey.question,
               'answer': answer,
               }
    return render(request, "info/condominium/survey/view_answer.html", context=context)


def view_answer(request, id):
    answer = get_object_or_404(SurveyAnswerModel, pk=id)
    form = SurveyAnswerModelForm(instance=answer)
    form.fields['option'].disabled = True
    form.fields['option'].required = False
    form.fields['survey'].disabled = True
    form.fields['survey'].required = False
    form.fields['block'].disabled = True
    form.fields['block'].required = False
    slash_pos = answer.address.find('/')
    form.fields['block'].initial = answer.address[:int(slash_pos)]
    form.fields['apartment'].disabled = True
    form.fields['apartment'].required = False
    form.fields['apartment'].initial = answer.address[int(slash_pos) + 1:]

    context = {'form': form,
               'question': answer.survey.question,
               'id': answer.id,
               'valid': answer.is_valid,
               }
    if answer.answer_pic:
        context['pic'] = answer.answer_pic

    return render(request, 'info/condominium/survey/view_answer.html', context=context)


def approve_answer(request, id):
    answer = get_object_or_404(SurveyAnswerModel, pk=id)
    answer.is_valid = True
    answer.save()
    option = SurveyOptionModel.objects.get(survey=answer.survey, option__iexact=answer.option.option)
    option.votes = option.votes + 1
    option.save()

    messages.success(request, "Voto Aprovado!")

    survey_id = answer.survey.pk

    return redirect(reverse('info:approve-answers', args=[int(survey_id)]))

@login_required(login_url='info:sign-in')
def reprove_answer(request, id):
    answer = get_object_or_404(SurveyAnswerModel, pk=id)
    answer.delete()

    messages.success(request, "Voto Impugnado!")
    survey_id = answer.survey.pk

    return redirect(reverse('info:approve-answers', args=[int(survey_id)]))


def survey_result(request, id):
    condominium = get_condominium(request)
    user = CondominiumProfile.objects.get(pk=int(request.user.id))
    survey = SurveyModel.objects.get(pk=id)
    answer = None
    try:
        answer = SurveyAnswerModel.objects.get(survey=survey, email=user.email, is_valid=True)
    except SurveyAnswerModel.DoesNotExist:
        messages.error(request, "Você não respondeu a esta enquete!")

    survey = [survey]

    return _survey_pdf(request, condominium, survey, 0, 0, False, answer)


@login_required(login_url='info:sign-in')
def survey_link(request, id):
    condominium = get_condominium(request)
    survey = SurveyModel.objects.get(pk=id)
    if request.method == "POST":
        return send_link_to(request, request.POST.get("link"))

    email_verification_token = EmailVerificationTokenGenerator()
    token = secrets.token_urlsafe(16)
    email_token = TokenModel(email=condominium.email, token=token, survey=survey)
    email_token.save()
    current_site = get_current_site(request)

    context = {'domain': current_site.domain,
               'uid': urlsafe_base64_encode(force_bytes(survey.pk)),
               'token': urlsafe_base64_encode(force_bytes(token)),
               'survey_email': urlsafe_base64_encode(force_bytes(condominium.email))
               }
    # register_link = "http://" + current_site + {% url 'info:verification' uidb64=uid token=token %}
    return render(request, "info/condominium/survey/generate_anonimous.html", context=context)


@login_required(login_url='info:sign-in')
def delete_survey(request, id):
    condominium = get_condominium(request)
    survey = get_object_or_404(SurveyModel, pk=id, condominium=condominium)
    if survey:
        survey.delete()
        messages.success(request, "Enquete Removida!")
        return redirect('info:surveys')
    else:
        messages.error(request, "Enquete não encontrada!")
        return redirect('info:dashboard')
