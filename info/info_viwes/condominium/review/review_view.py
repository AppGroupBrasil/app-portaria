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
from django.db.models import Avg
from django.forms import modelformset_factory
from django.shortcuts import redirect, render, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes, force_str
from django.utils.html import strip_tags
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode

from info.forms import ReviewForm, ReviewAnswerForm, AddedReviewItemForm, ViewReviewAnswerForm
from info.models import CondominiumProfile, Review, Resident, ReviewAnswer, HowTo, Block, ReviewItem, Apartment
from info.utils import get_condominium, add_signature_to_data, add_notification, add_manager_notification


FIXED_TZ = pytz.timezone("America/Sao_Paulo")


@login_required(login_url='info:sign-in')
def add_review(request):
    condominium = get_condominium(request)
    blocks = Block.objects.filter(condominium=condominium)
    form = ReviewForm(blocks=blocks)

    ReviewItemFormset = modelformset_factory(ReviewItem, form=AddedReviewItemForm, extra=1)
    queryset = ReviewItem.objects.none()
    formset = ReviewItemFormset(request.POST or None, queryset=queryset, prefix="review_item")

    if request.method == "POST":
        print(request.POST)

        # # review = Review.objects.get(pk=2)
        send_to = request.POST.get('send_to')
        residents = []
        if send_to == "MORADORES":
            if request.POST.get('block') == 'ALL':
                residents = Resident.objects.filter(apartment__block__condominium=condominium)
            elif request.POST.get('apartments') == 'ALL':
                residents = Resident.objects.filter(apartment__block=int(request.POST.get('block')))
            else:
                residents = Resident.objects.filter(apartment__block__condominium=condominium,
                                                    apartment=int(request.POST.get('apartments')))

        else:
            residents = CondominiumProfile.objects.filter(work_for=condominium)

        if len(residents):

            review = Review()
            review.condominium = condominium

            # review.service = request.POST.get('service')
            # review.provider = request.POST.get('provider') or ""

            review.save()
            services = ""
            descriptions = ""
            if all([formset.is_valid(), ]):
                counter = 0
                for added in formset:
                    if added.has_changed():
                        reviewItem = ReviewItem()
                        reviewItem.service = added.cleaned_data['service']
                        reviewItem.provider = added.cleaned_data['provider'] or ""
                        reviewItem.is_link = added.cleaned_data['is_link'] or False
                        reviewItem.review = review
                        reviewItem.image = request.FILES.get('review_item-' + str(counter) + '-image') or None
                        reviewItem.save()
                        services = services + reviewItem.service + " / "
                        descriptions = descriptions + reviewItem.provider + " / "
                        counter += 1

            review.service = services
            review.provider = descriptions
            review.save()

            to_list = []
            for resident in residents:
                if resident.email:
                    to_list.extend(resident.email.split(';'))

            for email in to_list:
                try:
                    user = CondominiumProfile.objects.get(email=email)
                    review.allowed_users.add(user)
                    review.save()
                except CondominiumProfile.DoesNotExist:
                    pass

            subject = 'Solicitação de Avaliação no ' + condominium.condominium_name
            data = add_signature_to_data(request)
            data['service'] = services[:-3]
            data['domain'] = get_current_site(request).domain
            data['uid'] = urlsafe_base64_encode(force_bytes(review.pk))
            html_content = render_to_string(
                'info/condominium/review/review_message.html',
                data
            )

            text_content = strip_tags(html_content)
            msg = EmailMultiAlternatives(subject, text_content, to=to_list)
            msg.attach_alternative(html_content, "text/html")
            msg.send()

            add_notification(condominium, to_list, "Uma avaliação sobre " + services[:-3].upper() +
                             " foi solicitada a você. Verifique na sua aplicação ou sua caixa de entrada ou lixo eletrônico.", None, "/my-reviews")

            messages.success(request, "Avaliação solicitada!")
            return redirect(reverse('info:dashboard'))
        else:
            form = ReviewForm(request.POST, blocks=blocks)
            messages.error(request, "Nenhum morador reside no apartamento selecionado!")

    context = {'form': form,
               'formset': formset
               }

    how_to_add_review = HowTo.objects.get(name__exact="Avaliação > Solicitar")
    print(how_to_add_review.kind)
    if how_to_add_review.kind == "Texto":
        context['how_to_add_review_text'] = how_to_add_review.value
    else:
        context['how_to_add_review_link'] = how_to_add_review.value

    return render(request, "info/condominium/review/add_review.html", context=context)


@login_required(login_url='info:sign-in')
def reviews(request):
    condominium = get_condominium(request)
    reviews = Review.objects.filter(condominium=condominium).order_by('created')

    reviews_list = []
    for review in reviews:
        review_obj = {
            'id': review.id,
            'created': review.created.astimezone(FIXED_TZ),
            'rate': ReviewAnswer.objects.filter(review=review, is_valid=True).aggregate(avg_score=Avg('rate'))[
                'avg_score'],
        }

        if review.service:
            review_obj['service'] = review.service or ""

        if review.provider:
            review_obj['provider'] = review.provider or ""

        review_item = ReviewItem.objects.filter(review=review)
        if len(review_item):
            services = ""
            item_list = []
            for item in review_item:
                review_item = {
                    'service': item.service,
                    'provider': item.provider,
                    'rate': ReviewAnswer.objects.filter(item=item, is_valid=True).aggregate(avg_score=Avg('rate'))[
                        'avg_score']
                }
                item_list.append(review_item)
                services = services + item.service + " / "
            review_obj['items'] = item_list
            review_obj['services'] = services[:-3]

        reviews_list.append(review_obj)

    context = {'reviews': reviews_list,
               'user': condominium
               }

    how_to_review_list = HowTo.objects.get(name__exact="Avaliações > Listagem")
    if how_to_review_list.kind == "Texto":
        context['how_to_review_list_text'] = how_to_review_list.value
    else:
        context['how_to_review_list_link'] = how_to_review_list.value

    return render(request, "info/condominium/review/reviews.html", context=context)


def my_review(request):
    condominium = get_condominium(request)
    reviews = Review.objects.filter(condominium=condominium).order_by('created')

    my_review_list = []

    for review in reviews:
        if request.user in review.allowed_users.all():
            review_obj = {
                'id': review.id,
                'created': review.created.astimezone(FIXED_TZ),
                'uid': urlsafe_base64_encode(force_bytes(review.pk))
            }

            if review.service:
                review_obj['service'] = review.service

            if review.provider:
                review_obj['provider'] = review.provider

            review_item = ReviewItem.objects.filter(review=review)
            if len(review_item):
                services = ""
                item_list = []
                for item in review_item:
                    review_item = {
                        'service': item.service,
                        'provider': item.provider,
                    }
                    item_list.append(review_item)
                    services = services + item.service + " / "
                review_obj['items'] = item_list
                review_obj['services'] = services[:-3]

            my_review_list.append(review_obj)
    context = {}
    if len(my_review_list):
        context['reviews'] = my_review_list

    return render(request, "info/condominium/review/my_reviews.html", context=context)


def add_answer(request, uidb64):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        review = Review.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError,
            Review.DoesNotExist):
        messages.error(request, "A avaliação solicitada não está mais disponível")
        return render(request, "info/condominium/review/thank_you.html")

    if request.method == "POST":
        print(request.POST)
        print(request.FILES)

        # form = ReviewAnswerForm(request.POST, files=request.FILES)
        review_item = ReviewItem.objects.filter(review=review)
        if len(review_item):
            for item in review_item:
                answer = ReviewAnswer()
                answer.item = item
                answer.review = item.review
                answer.name = request.POST.get('name')
                answer.email = request.POST.get('email') or ""

                kind = request.POST.get('kind')
                if kind == "FUNCIONÁRIO":
                    answer.address = "FUNCIONÁRIO"
                else:
                    apartment = Apartment.objects.get(pk=int(request.POST.get('apartment')))
                    answer.address = apartment.block.name + "/" + str(apartment.number) + " " + apartment.complement

                answer.message = request.POST.get('item_' + str(item.pk)) or ""
                answer.rate = int(request.POST.get('item_rate_' + str(item.pk))) or 0
                if request.FILES.get('item_image_' + str(item.pk)):
                    answer.image = request.FILES.get('item_image_' + str(item.pk))
                answer_pic = request.POST.get(
                    'webimg')  # src is the name of input attribute in your html file, this src value is set in javascript code
                if answer_pic:
                    image_data = answer_pic.split(',')[1]  # Remove the data URI prefix
                    image_bytes = base64.b64decode(image_data)
                    image_file = io.BytesIO(image_bytes)
                    Image.open(image_file)
                    image_file.seek(0)
                    answer.answer_pic = InMemoryUploadedFile(
                        image_file, None, answer.name + '.jpg', 'image/jpeg', len(image_bytes), None)
                answer.save()
                add_manager_notification(review.condominium,
                                         "NOVO VOTO RECEBIDO PARA A PESQUISA " + item.service.upper() + ","
                                                                                                        "faça a validação do voto nos detalhes da pesquisa.")
        else:
            # if form.is_valid():
            answer = ReviewAnswer()
            answer.review = review
            answer.name = request.POST.get('name')
            answer.email = request.POST.get('email') or ""
            kind = request.POST.get('kind')
            if kind == "FUNCIONÁRIO":
                answer.address = "FUNCIONÁRIO"
            else:
                apartment = Apartment.objects.get(pk=int(request.POST.get('apartment')))
                answer.address = apartment.block.name + "/" + str(apartment.number) + " " + apartment.complement
            answer.message = request.POST.get('message') or ""
            answer.rate = int(request.POST.get('rate')) or 0
            if request.FILES.get('image'):
                answer.image = request.FILES.get('image')
            answer.save()

            add_manager_notification(review.condominium,
                                     "NOVO VOTO RECEBIDO PARA A PESQUISA " + review.service.upper() + ","
                                                                                                      "faça a validação do voto nos detalhes da pesquisa.")

        messages.success(request, "Avalidação recebida!")
        return render(request, "info/condominium/review/thank_you.html")

    blocks = Block.objects.filter(condominium=review.condominium)
    form = ReviewAnswerForm(request.POST or None, blocks=blocks)

    review_item = ReviewItem.objects.filter(review=review)
    context = {'form': form,
               }
    if review.service:
        context['service'] = review.service

    if review.provider:
        context['provider'] = review.provider

    if len(review_item):
        context['items'] = review_item

    return render(request, "info/condominium/review/add_answer.html", context=context)


@login_required(login_url='info:sign-in')
def answers(request, id):
    review = Review.objects.get(pk=id)
    answers = ReviewAnswer.objects.filter(review=review, is_valid=True).order_by("-created")

    context = {
        'answers': answers,
        'id': review.id,
    }

    if review.service:
        context['service'] = review.service
    else:
        review_item = ReviewItem.objects.filter(review=review)
        services = ""
        for item in review_item:
            services = services + item.service + " / "

        context['service'] = services[:-3]

    return render(request, "info/condominium/review/review_detail.html", context=context)


@login_required(login_url='info:sign-in')
def approve_answers(request, id):
    review = Review.objects.get(pk=id)

    answers_to_approve = ReviewAnswer.objects.filter(review=review, is_valid=False).order_by("-created")
    if not answers_to_approve:
        answers_to_approve = ReviewAnswer.objects.filter(item__review=review, is_valid=False).order_by("-created")

    context = {
        'answers': answers_to_approve,
    }

    if review.service:
        context['service'] = review.service
    else:
        review_item = ReviewItem.objects.filter(review=review)
        services = ""
        for item in review_item:
            services = services + item.service + " / "

        context['service'] = services[:-3]

    return render(request, "info/condominium/survey/approve_answers.html", context=context)


@login_required(login_url='info:sign-in')
def answer_detail(request, id):
    answer = ReviewAnswer.objects.get(pk=id)
    item = ReviewItem.objects.get(pk=answer.item.pk)
    context = {'service': answer.service,
               'item': item,
               'answers': answers,
               }
    return render(request, "info/condominium/review/review_detail.html", context=context)


@login_required(login_url='info:sign-in')
def view_answer(request, id):
    answer = get_object_or_404(ReviewAnswer, pk=id)
    form = ViewReviewAnswerForm()

    form.fields['name'].disabled = True
    form.fields['name'].required = False
    form.fields['name'].initial = answer.name
    form.fields['email'].disabled = True
    form.fields['email'].required = False
    form.fields['email'].initial = answer.email
    form.fields['address'].disabled = True
    form.fields['address'].required = False

    form.fields['address'].initial = answer.address
    form.fields['message'].disabled = True
    form.fields['message'].required = False
    form.fields['message'].initial = answer.message
    form.fields['rate'].disabled = True
    form.fields['rate'].required = False
    form.fields['rate'].initial = answer.rate
    # form.fields.pop('image')

    service = ""
    if answer.item:
        service = answer.item.service
    else:
        service = answer.review.service

    context = {'form': form,
               'service': service,
               'id': answer.id,
               'valid': answer.is_valid,
               'item': answer.item,
               }
    if answer.answer_pic:
        context['pic'] = answer.answer_pic

    if answer.image:
        context['img'] = answer.image

    return render(request, 'info/condominium/review/view_answer.html', context=context)


def approve_answer(request, id):
    answer = get_object_or_404(ReviewAnswer, pk=id)
    answer.is_valid = True
    answer.save()

    messages.success(request, "Voto Aprovado!")

    review_id = answer.review.pk

    return redirect(reverse('info:approve-answers', args=[int(review_id)]))


@login_required(login_url='info:sign-in')
def reprove_answer(request, id):
    answer = get_object_or_404(ReviewAnswer, pk=id)
    answer.delete()

    messages.success(request, "Voto Impugnado!")
    review_id = answer.review.pk

    return redirect(reverse('info:approve-answers', args=[int(review_id)]))


def valid_all_votes(request):
    answers = ReviewAnswer.objects.all()

    for answer in answers:
        answer.is_valid = True
        answer.save()

    messages.success(request, "Votos Aprovados!")
    return redirect(reverse('info:reviews'))


@login_required(login_url='info:sign-in')
def delete_review(request, id):
    condominium = get_condominium(request)
    review = get_object_or_404(Review, pk=id, condominium=condominium)
    if review:
        review.delete()
        messages.success(request, "Avaliação Removida!")
        return redirect('info:reviews')
    else:
        messages.error(request, "Avaliação não encontrada!")
        return redirect('info:dashboard')
