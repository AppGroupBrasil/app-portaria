import json
import uuid
from urllib.parse import unquote

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.forms import modelformset_factory, formset_factory
from django.http import JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse

from info.forms import AddInformativeForm, AddFunctionForm, AddFunctionItemForm, AddImageForm, AddFunctionItemFileForm, \
    AddFunctionItemLinkVideoForm, AddInformativeKindForm, \
    AddActivityForm
from info.models import CondominiumProfile, Function, FunctionItem, ImageModel, Informative, FunctionItemFileModel, \
    HowTo, FunctionItemVideoLink, InformativeKind, UserLocation, ActivityFunction
from info.utils import get_condominium


@login_required(login_url='info:sign-in')
def add_informative(request):
    condominium = get_condominium(request)
    user = CondominiumProfile.objects.get(pk=int(request.user.id))
    ip_address = request.META.get('HTTP_X_FORWARDED_FOR') or request.META.get('HTTP_CLIENT_IP')

    if not ip_address:
        ip_address = '127.0.0.1'

    location = UserLocation.objects.filter(condominium=user, ip_address=ip_address).order_by('-created').first()

    informative_kind = InformativeKind.objects.filter(condominium=condominium).order_by('name')
    form = AddInformativeForm(request.POST or None, informative_kind=informative_kind)

    FunctionFormset = modelformset_factory(Function, form=AddFunctionForm, extra=0)
    function_queryset = Function.objects.none()
    function_formset = FunctionFormset(request.POST or None, queryset=function_queryset, prefix="function")

    FunctionItemsset = modelformset_factory(FunctionItem, form=AddFunctionItemForm, extra=0)
    items_queryset = FunctionItem.objects.none()
    items_formset = FunctionItemsset(request.POST or None, queryset=items_queryset, prefix="item")

    ItemImagesset = modelformset_factory(ImageModel, form=AddImageForm, extra=0)
    images_queryset = ImageModel.objects.none()
    images_formset = ItemImagesset(request.POST or None, files=request.FILES or None, queryset=images_queryset,
                                   prefix="image")

    ItemFilesset = modelformset_factory(FunctionItemFileModel, form=AddFunctionItemFileForm, extra=0)
    files_queryset = FunctionItemFileModel.objects.none()
    files_formset = ItemFilesset(request.POST or None, files=request.FILES or None, queryset=files_queryset,
                                 prefix="file")

    ItemVideosset = modelformset_factory(FunctionItemVideoLink, form=AddFunctionItemLinkVideoForm, extra=0)
    videos_queryset = FunctionItemVideoLink.objects.none()
    videos_formset = ItemVideosset(request.POST or None, queryset=videos_queryset, prefix="video")

    context = {'form': form,
               'function_formset': function_formset,
               'items_formset': items_formset,
               'images_formset': images_formset,
               'files_formset': files_formset,
               'videos_formset': videos_formset,
               }
    how_to_function = HowTo.objects.get(name__exact="Informativo > Funções")
    if how_to_function.kind == "Texto":
        context['how_to_function_text'] = how_to_function.value
    else:
        context['how_to_function_link'] = how_to_function.value
    how_to_item = HowTo.objects.get(name__exact="Informativo > Item")
    if how_to_item.kind == "Texto":
        context['how_to_item_text'] = how_to_item.value
    else:
        context['how_to_item_link'] = how_to_item.value
    how_to_image = HowTo.objects.get(name__exact="Informativo > Imagens")
    if how_to_image.kind == "Texto":
        context['how_to_image_text'] = how_to_image.value
    else:
        context['how_to_image_link'] = how_to_image.value
    how_to_file = HowTo.objects.get(name__exact="Informativo > Arquivos")
    if how_to_file.kind == "Texto":
        context['how_to_file_text'] = how_to_file.value
    else:
        context['how_to_file_link'] = how_to_file.value
    how_to_video = HowTo.objects.get(name__exact="Informativo > Vídeos")
    if how_to_video.kind == "Texto":
        context['how_to_video_text'] = how_to_video.value
    else:
        context['how_to_video_link'] = how_to_video.value

    if all([form.is_valid(), function_formset.is_valid(), items_formset.is_valid(), images_formset.is_valid(),
            files_formset.is_valid(), videos_formset.is_valid()]):

        informative = Informative()
        informative.condominium = condominium
        informative.title = form.cleaned_data['title']
        informative.description = form.cleaned_data['description'] or ""
        informative.kind = form.cleaned_data['kind'].name
        informative.location = location

        informative.save()

        functions_instances = []
        for function_form in function_formset:
            function = Function()
            function.title = function_form.cleaned_data['title']
            function.informative = informative
            function.save()
            functions_instances.append(function)

        item_instances = []
        for item_form in items_formset:

            item = FunctionItem()
            item.title = item_form.cleaned_data['title']
            for functions_instance in functions_instances:
                if functions_instance.title == item_form.cleaned_data['funcao']:
                    item.function = functions_instance
                    break
            item.save()
            item_instances.append(item)

        for image_form in images_formset:
            for item in item_instances:
                if item.title == image_form.cleaned_data['item_name']:
                    image_model = ImageModel()
                    image_model.function_item = item
                    image_model.image = image_form.cleaned_data['image']
                    image_model.save()
                    break

        for file_form in files_formset:
            for item in item_instances:
                if item.title == file_form.cleaned_data['item_name']:
                    file_model = FunctionItemFileModel()
                    file_model.function_item = item
                    file_model.file = file_form.cleaned_data['file']
                    file_model.save()
                    break

        for video_form in videos_formset:
            if video_form.has_changed():
                for item in item_instances:
                    if item.title == video_form.cleaned_data['item_name']:
                        video_model = FunctionItemVideoLink()
                        video_model.function_item = item
                        video_model.link = video_form.cleaned_data['link']
                        video_model.save()
                        break

        messages.success(request, "Informativo Cadastrados!")
        return redirect('info:dashboard')

    else:
        print(form.errors)
        print("function_formset")
        print(function_formset.errors)
        print("items_formset")
        print(items_formset.errors)
        print("image_formset")
        print(images_formset.errors)
        print("files_formset")
        print(files_formset.errors)
        print("video_formset")
        print(videos_formset.errors)

    return render(request, "info/condominium/informative/add_informative.html", context=context)


@login_required(login_url='info:sign-in')
def delete_all_informatives(request):
    condominium = get_condominium(request)
    informatives = Informative.objects.filter(condominium=condominium)

    for informative in informatives:
        informative.delete()


def add_activity(request):
    condominium = get_condominium(request)
    user = CondominiumProfile.objects.get(pk=int(request.user.id))
    ip_address = request.META.get('HTTP_X_FORWARDED_FOR') or request.META.get('HTTP_CLIENT_IP')

    if not ip_address:
        ip_address = '127.0.0.1'

    location = UserLocation.objects.filter(condominium=user, ip_address=ip_address).order_by('-created').first()

    informative_kind = InformativeKind.objects.filter(condominium=condominium).order_by('name')
    form = AddInformativeForm(request.POST or None, informative_kind=informative_kind)

    ActivityFunctionFormset = formset_factory(AddActivityForm, extra=1)
    formset = ActivityFunctionFormset(request.POST or None, files=request.FILES or None,
                                      prefix="activity")

    if all([form.is_valid(), formset.is_valid()]):

        informative = Informative()
        informative.condominium = condominium
        informative.title = form.cleaned_data['title']
        informative.kind = form.cleaned_data['kind'].name
        informative.location = location

        informative.save()

        for function_form in formset:
            function = ActivityFunction()
            function.title = function_form.cleaned_data['title']
            function.desctiption = function_form.cleaned_data['description'] or ""
            function.informative = informative
            if function_form.cleaned_data['link']:
                function.link = function_form.cleaned_data['link']
            function.save()

            images = function_form.cleaned_data["images"]
            if images:
                for image in images:

                    image_model = ImageModel()
                    image_model.function_item = function
                    image_model.image = image
                    image_model.save()

            files = function_form.cleaned_data["files"]
            if files:
                for file in files:
                    file_model = FunctionItemFileModel()
                    file_model.function_item = function
                    file_model.file = file
                    file_model.save()

        messages.success(request, "Atividade Cadastrada!")
        return redirect('info:dashboard')

    context = {'form': form,
               'activity_function_formset': formset,
               }

    how_to_add_activity = HowTo.objects.get(name__exact="Atividade > Adição")
    if how_to_add_activity.kind == "Texto":
        context['how_to_add_activity_text'] = how_to_add_activity.value
    else:
        context['how_to_add_activity_link'] = how_to_add_activity.value

    return render(request, "info/condominium/informative/add_activity.html", context=context)


@login_required(login_url='info:sign-in')
def export_informative_to_pdf(request, id):
    condominium = get_condominium(request)
    informative = get_object_or_404(Informative, pk=id, condominium=condominium)
    context = {
        'informative': informative,
    }

    functions = ActivityFunction.objects.filter(informative=informative)

    card_list = []
    for func in functions:
        card = {
            'title': func.title,
            'description': func.description,
        }

        files = FunctionItemFileModel.objects.filter(function_item=func)

        file_list = []
        if len(files) > 0:
            for file in files:
                file_list.append(file.file.url)
            card['files'] = file_list

        if func.link:
            card['video'] = func.link

        images = ImageModel.objects.filter(function_item=func)

        if len(images) > 0:
            for image in images:
                card_cp = card.copy()
                card_cp['img'] = image.image.url
                card_list.append(card_cp)
        else:
            card_list.append(card)

    context["functions"] = functions
    context["card_list"] = card_list

    how_to_export = HowTo.objects.get(name__exact="Informativo > Exportação")
    if how_to_export.kind == "Texto":
        context['how_to_export_text'] = how_to_export.value
    else:
        context['how_to_export_link'] = how_to_export.value
    context['test'] = informative.condominium.is_testing

    return render(request, 'info/condominium/report/informative.html', context=context)


@login_required(login_url='info:sign-in')
def informative(request):
    condominium = get_condominium(request)
    informative_list = Informative.objects.filter(condominium=condominium).order_by("-created")

    search_name = request.GET.get('informative_name')
    search_created = request.GET.get('informative_created')

    if search_name:
        informative_list = informative_list.filter(title__contains=search_name)

    if search_created:
        print(search_created)
        informative_list = informative_list.filter(created__date=search_created)

    context = {'informative_list': informative_list,
               'user': condominium
               }

    how_to_informative_list = HowTo.objects.get(name__exact="Atividades > Listagem")
    if how_to_informative_list.kind == "Texto":
        context['how_to_informative_list_text'] = how_to_informative_list.value
    else:
        context['how_to_informative_list_link'] = how_to_informative_list.value

    return render(request, "info/condominium/informative/informative.html", context=context)


@login_required(login_url='info:sign-in')
def edit_informative(request, id):
    condominium = get_condominium(request)
    user = CondominiumProfile.objects.get(pk=int(request.user.id))
    ip_address = request.META.get('HTTP_X_FORWARDED_FOR') or request.META.get('HTTP_CLIENT_IP')

    if not ip_address:
        ip_address = '127.0.0.1'

    location = UserLocation.objects.filter(condominium=user, ip_address=ip_address).order_by('-created').first()

    informative_kind = InformativeKind.objects.filter(condominium=condominium).order_by('name')
    informative = get_object_or_404(Informative, pk=id, condominium=condominium)

    if informative:
        form = AddInformativeForm(instance=informative, informative_kind=informative_kind)

        ActivityFunctionFormset = formset_factory(AddActivityForm, extra=0)
        function_queryset = ActivityFunction.objects.filter(informative=informative)

        initial_data = []
        for function in function_queryset:
            data = {
                'title': function.title,
                'description': function.description,
                'link': function.link
            }
            files = FunctionItemFileModel.objects.filter(function_item=function)
            if len(files):
                files_list = []
                for file in files:
                    files_list.append(file.file)
                data['files'] = files_list

            images = ImageModel.objects.filter(function_item=function)
            if len(images):
                images_list = []
                for image in images:
                    images_list.append(image.image.path)
                data['images'] = images_list

            initial_data.append(data)
        if len(initial_data):
            function_formset = ActivityFunctionFormset(initial=initial_data, prefix="activity")
        else:
            function_formset = ActivityFunctionFormset(prefix="activity")

        context = {'form': form,
                   'function_formset': function_formset,
                   }

        how_to_function = HowTo.objects.get(name__exact="Informativo > Funções")
        if how_to_function.kind == "Texto":
            context['how_to_function_text'] = how_to_function.value
        else:
            context['how_to_function_link'] = how_to_function.value
        how_to_item = HowTo.objects.get(name__exact="Informativo > Item")
        if how_to_item.kind == "Texto":
            context['how_to_item_text'] = how_to_item.value
        else:
            context['how_to_item_link'] = how_to_item.value
        how_to_image = HowTo.objects.get(name__exact="Informativo > Imagens")
        if how_to_image.kind == "Texto":
            context['how_to_image_text'] = how_to_image.value
        else:
            context['how_to_image_link'] = how_to_image.value
        how_to_file = HowTo.objects.get(name__exact="Informativo > Arquivos")
        if how_to_file.kind == "Texto":
            context['how_to_file_text'] = how_to_file.value
        else:
            context['how_to_file_link'] = how_to_file.value
        how_to_video = HowTo.objects.get(name__exact="Informativo > Vídeos")
        if how_to_video.kind == "Texto":
            context['how_to_video_text'] = how_to_video.value
        else:
            context['how_to_video_link'] = how_to_video.value

        if request.method == 'POST':
            print(request.POST)
            print(request.FILES)
            form = AddInformativeForm(request.POST, request.FILES)
            print("BEFORE")
            if request.POST:
                print("AFTER")

                informative.title = request.POST.get('title')
                informative.description = request.POST.get('description') or ""
                informative.kind = informative_kind.get(id=int(request.POST.get('kind'))).name
                informative.location = location
                informative.save()

                for function in function_queryset:
                    function.delete()

                total_forms = int(request.POST.get('activity-TOTAL_FORMS'))
                for count in range(0, total_forms, 1):

                    print("AFTERR")
                    if request.POST.get('activity-' + str(count) + '-title'):
                        function = ActivityFunction()
                        function.title = request.POST.get('activity-' + str(count) + '-title')
                        function.description = request.POST.get('activity-' + str(count) + '-description') or ""
                        function.informative = informative
                        if request.POST.get('activity-' + str(count) + '-link'):
                            function.link = request.POST.get('activity-' + str(count) + '-link')
                        function.save()

                        images_data = request.FILES.getlist('activity-' + str(count) + '-images')  # Assuming 'images' is the field name
                        if images_data:
                            # Iterate through the list of uploaded files
                            for image_data in images_data:
                                image_model = ImageModel()
                                image_model.function_item = function
                                image_model.image = image_data
                                image_model.save()

                        files = request.FILES.getlist('activity-' + str(count) + '-files')
                        if files:
                            for file in files:
                                file_model = FunctionItemFileModel()
                                file_model.function_item = function
                                file_model.file = file
                                file_model.save()

                messages.success(request, "Informativo Atualizado!")
                return redirect('info:informative')
            else:
                print("form")
                print(form.errors)
                print("function_formset")
                print(function_formset.errors)

        return render(request, 'info/condominium/informative/edit_informative.html', context=context)
    else:
        messages.error(request, "Informativo não encontrado!")
        return redirect('info:dashboard')


@login_required(login_url='info:sign-in')
def clone_informative(request, id):
    condominium = get_condominium(request)
    informative = get_object_or_404(Informative, pk=id, condominium=condominium)
    if informative:

        clone_informative = Informative()
        clone_informative.condominium = informative.condominium
        clone_informative.title = "cópia_de_" + informative.title
        clone_informative.description = informative.description or ""
        clone_informative.kind = informative.kind
        clone_informative.save()

        for function in ActivityFunction.objects.filter(informative=informative):
            clone_function = ActivityFunction()
            clone_function.informative = clone_informative
            clone_function.title = function.title
            clone_function.description = function.description
            clone_function.link = function.link
            clone_function.save()

            for image in ImageModel.objects.filter(function_item=function):
                clone_image = ImageModel()
                clone_image.function_item = clone_function
                clone_image.image = image.image
                clone_image.save()

            for file in FunctionItemFileModel.objects.filter(function_item=function):
                clone_file = FunctionItemFileModel()
                clone_file.function_item = clone_function
                clone_file.file = file.file
                clone_file.save()

        messages.success(request, "Informativo Copiado!")
        return redirect('info:informative')
    else:
        messages.error(request, "Informativo não encontrado!")
        return redirect('info:dashboard')


@login_required(login_url='info:sign-in')
def delete_informative(request, id):
    condominium = get_condominium(request)
    informative = get_object_or_404(Informative, pk=id, condominium=condominium)
    if informative:
        informative.delete()
        messages.success(request, "Informativo Removido!")
        return redirect('info:informative')
    else:
        messages.error(request, "Informativo não encontrado!")
        return redirect('info:dashboard')


@login_required(login_url='info:sign-in')
def view_informative(request, id):
    condominium = get_condominium(request)
    informative = get_object_or_404(Informative, pk=id, condominium=condominium)
    form = AddInformativeForm(instance=informative)
    form.fields['title'].disabled = True
    form.fields['title'].required = False
    form.fields['description'].disabled = True
    form.fields['description'].required = False
    form.fields['kind'].disabled = True
    form.fields['kind'].required = False

    ActivityFunctionFormset = modelformset_factory(ActivityFunction, form=AddActivityForm, extra=0)
    function_queryset = ActivityFunction.objects.filter(informative=informative)
    function_formset = ActivityFunctionFormset(request.POST or None, queryset=function_queryset, prefix="activity")

    for function_form in function_formset.forms:
        function_form.fields['title'].widget.attrs['disabled'] = 'disabled'
        function_form.fields['description'].widget.attrs['disabled'] = 'disabled'
        function_form.fields['link'].widget.attrs['disabled'] = 'disabled'

    # FunctionItemsset = modelformset_factory(FunctionItem, form=ViewFunctionItemForm, extra=0)
    # items_queryset = FunctionItem.objects.filter(function__informative=informative)
    # items_formset = FunctionItemsset(request.POST or None, queryset=items_queryset, prefix="item")
    #
    images_queryset = ImageModel.objects.filter(function_item__informative=informative)
    files_queryset = FunctionItemFileModel.objects.filter(function_item__informative=informative)
    #
    # for item_form in items_formset.forms:
    #     item_form.fields['function'].widget.attrs['disabled'] = 'disabled'
    #     item_form.fields['title'].widget.attrs['disabled'] = 'disabled'

    context = {'form': form,
               'function_formset': function_formset,
               'files_formset': files_queryset,
               'images_formset': images_queryset,
               }

    return render(request, 'info/condominium/informative/view_informative.html', context=context)


def delete_function_from_informative(request):
    function_id = request.GET.get('function_id')
    if function_id:

        function = get_object_or_404(Function, pk=int(function_id))
        function.delete()

        data = {'message': 'Function removed'}
    else:
        data = {'message': 'Nothing to do'}

    return JsonResponse(data, safe=False)


def delete_item_from_informative(request):
    item_id = request.GET.get('item_id')
    if item_id:

        item = get_object_or_404(FunctionItem, pk=int(item_id))
        item.delete()

        data = {'message': 'Function item removed'}
    else:
        data = {'message': 'Nothing to do'}

    return JsonResponse(data, safe=False)


def delete_image_from_informative(request):
    image_id = request.GET.get('image_id')
    if image_id:

        image = get_object_or_404(ImageModel, pk=int(image_id))
        image.delete()

        data = {'message': 'Image removed'}
    else:
        data = {'message': 'Nothing to do'}

    return JsonResponse(data, safe=False)


def delete_file_from_informative(request):
    file_id = request.GET.get('file_id')
    if file_id:

        file = get_object_or_404(FunctionItemFileModel, pk=int(file_id))
        file.delete()

        data = {'message': 'File removed'}
    else:
        data = {'message': 'Nothing to do'}

    return JsonResponse(data, safe=False)


def delete_video_from_informative(request):
    video_id = request.GET.get('video_id')
    if video_id:
        video = get_object_or_404(FunctionItemVideoLink, pk=int(video_id))
        video.delete()

        data = {'message': 'Video removed'}
    else:
        data = {'message': 'Nothing to do'}

    return JsonResponse(data, safe=False)


@login_required(login_url='info:sign-in')
def add_informative_kind(request):
    condominium = get_condominium(request)
    form = AddInformativeKindForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():

            kind = InformativeKind()
            kind.condominium = condominium
            kind.name = form.cleaned_data['name']
            kind.save()

        messages.success(request, "Tipo adicionado!")

        return redirect(reverse('info:add-informative'))

    context = {'form': form,
               }
    return render(request, "info/condominium/informative/add_informative_kind.html", context=context)


@login_required(login_url='info:sign-in')
def remove_kind(request):
    condominium = get_condominium(request)
    kind = request.GET.get('kind_id')
    if kind:
        kind_db = InformativeKind.objects.get(pk=kind)
        informatives = Informative.objects.filter(kind__exact=kind_db.name, condominium=condominium)
        for informative in informatives:
            informative.delete()
        kind_db.delete()

        kinds = InformativeKind.objects.filter(condominium=condominium).order_by('name')
        data = [{'id': kind_obj.id, 'name': kind_obj.name} for kind_obj in kinds]
    else:
        data = []
    return JsonResponse(data, safe=False)


def store_image(request):
    if request.method == 'POST':
        # Parse JSON data from request body
        data = json.loads(request.body.decode('utf-8'))

        # Get the image source from the parsed JSON data
        image_src = data.get('imageSrc', '')

        # Store the image source in the session
        request.session['preview_image_src'] = image_src

        # Return a JSON response with a success message
        return JsonResponse({'message': 'Image source stored successfully'})
    else:
        # Return a 405 Method Not Allowed response if the request method is not POST
        return JsonResponse({'error': 'Method Not Allowed'}, status=405)


def edit_image(request, unique_id):
    image_src = request.session.get('preview_image_src', '')

    return render(request, 'info/condominium/informative/edit_image.html', {'image_src': image_src})


def add_default_activity_kinds(request):

    default_kind = ['Manutenção', 'Notificações', 'Ocorrências', 'Vistorias']

    for kind in default_kind:
        for user in CondominiumProfile.objects.all():
            try:
                InformativeKind.objects.get(condominium=user, name__iexact=str(kind))
            except InformativeKind.DoesNotExist:
                info_kind = InformativeKind()
                info_kind.condominium = user
                info_kind.name = str(kind)
                info_kind.save()

    return redirect(reverse('info:dashboard'))
