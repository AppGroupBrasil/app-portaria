import datetime
from datetime import date, timedelta

import pytz
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.sites.shortcuts import get_current_site
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse

from info.forms import ContractForm, ViewContractForm, EditContractForm, FolderForm, LocalFileForm
from info.models import CondominiumProfile, Contract, HowTo, Folder, LocalFile
from info.utils import get_condominium


FIXED_TZ = pytz.timezone("America/Sao_Paulo")


@login_required(login_url='info:sign-in')
def documents(request):
    condominium = get_condominium(request)
    folder_list = Folder.objects.filter(condominium=condominium, parent=None).order_by("name")

    folders = []
    for folder in folder_list:
        folder_obj = {'name': folder.name,
                      'id': folder.id,
                      'files': LocalFile.objects.filter(condominium=condominium, folder=folder).count() or 0,
                      'folders': Folder.objects.filter(condominium=condominium, parent=folder).count() or 0,
                      }
        folders.append(folder_obj)

    file_list = LocalFile.objects.filter(condominium=condominium, folder=None).order_by("name")
    files = []
    for file in file_list:
        last_slash_index = file.file.name.rfind('/')
        if last_slash_index != -1:
            name = file.file.name[last_slash_index + 1:]
        else:
            name = file.file.name
        file_obj = {'name': name,
                    'id': file.id,
                    'file': file.file,
                    'created': file.created.astimezone(FIXED_TZ),
                    }
        files.append(file_obj)

    context = {'folders': folders,
               'files': files,
               'condominium': condominium,
               'parent_id': 0,
               'page': 'documents',
               'name': '',
               }

    return render(request, "info/condominium/document/documents.html", context=context)


@login_required(login_url='info:sign-in')
def resident_documents(request):
    condominium = get_condominium(request)
    folder_list = Folder.objects.filter(condominium=condominium, parent=None).order_by("name")

    folders = []
    for folder in folder_list:
        folder_obj = {'name': folder.name,
                      'id': folder.id,
                      'files': LocalFile.objects.filter(condominium=condominium, folder=folder).count() or 0,
                      'folders': Folder.objects.filter(condominium=condominium, parent=folder).count() or 0,
                      }
        folders.append(folder_obj)

    file_list = LocalFile.objects.filter(condominium=condominium, folder=None).order_by("name")
    files = []
    for file in file_list:
        last_slash_index = file.file.name.rfind('/')
        if last_slash_index != -1:
            name = file.file.name[last_slash_index + 1:]
        else:
            name = file.file.name
        file_obj = {'name': name,
                    'id': file.id,
                    'file': file.file,
                    'created': file.created.astimezone(FIXED_TZ),
                    }
        files.append(file_obj)

    context = {'folders': folders,
               'files': files,
               'condominium': condominium,
               'parent_id': 0,
               'page': 'documents',
               'name': '',
               }

    return render(request, "info/condominium/document/resident_documents.html", context=context)


@login_required(login_url='info:sign-in')
def folder_detail(request, parent_id):
    condominium = get_condominium(request)
    parent = Folder.objects.get(id=int(parent_id))
    folder_list = Folder.objects.filter(condominium=condominium, parent=parent).order_by("name")

    folders = []
    for folder in folder_list:
        folder_obj = {'name': folder.name,
                      'id': folder.id,
                      'files': LocalFile.objects.filter(condominium=condominium, folder=folder).count() or 0,
                      'folders': Folder.objects.filter(condominium=condominium, parent=folder).count() or 0,
                      }
        folders.append(folder_obj)

    file_list = LocalFile.objects.filter(condominium=condominium, folder=parent).order_by("-created")
    files = []
    for file in file_list:
        last_slash_index = file.file.name.rfind('/')
        if last_slash_index != -1:
            name = file.file.name[last_slash_index + 1:]
        else:
            name = file.file.name
        file_obj = {'name': name,
                    'id': file.id,
                    'file': file.file,
                    'created': file.created.astimezone(FIXED_TZ),
                    }
        files.append(file_obj)

    context = {'folders': folders,
               'files': files,
               'condominium': condominium,
               'parent_id': int(parent_id),
               'page': 'folder.' + str(parent_id),
               'name': parent.name,
               }

    return render(request, "info/condominium/document/documents.html", context=context)


@login_required(login_url='info:sign-in')
def resident_folder_detail(request, parent_id):
    condominium = get_condominium(request)
    parent = Folder.objects.get(id=int(parent_id))
    folder_list = Folder.objects.filter(condominium=condominium, parent=parent).order_by("name")

    folders = []
    for folder in folder_list:
        folder_obj = {'name': folder.name,
                      'id': folder.id,
                      'files': LocalFile.objects.filter(condominium=condominium, folder=folder).count() or 0,
                      'folders': Folder.objects.filter(condominium=condominium, parent=folder).count() or 0,
                      }
        folders.append(folder_obj)

    file_list = LocalFile.objects.filter(condominium=condominium, folder=parent).order_by("-created")
    files = []
    for file in file_list:
        last_slash_index = file.file.name.rfind('/')
        if last_slash_index != -1:
            name = file.file.name[last_slash_index + 1:]
        else:
            name = file.file.name
        file_obj = {'name': name,
                    'id': file.id,
                    'file': file.file,
                    'created': file.created.astimezone(FIXED_TZ),
                    }
        files.append(file_obj)

    context = {'folders': folders,
               'files': files,
               'condominium': condominium,
               'parent_id': int(parent_id),
               'page': 'folder.' + str(parent_id),
               'name': parent.name,
               }

    return render(request, "info/condominium/document/resident_documents.html", context=context)


@login_required(login_url='info:sign-in')
def folder_back(request, parent_id):
    folder = Folder.objects.get(id=int(parent_id))
    back = folder.parent

    if back:
        return redirect(reverse('info:folder', args=[int(back.pk)]))

    return redirect(reverse('info:documents'))


@login_required(login_url='info:sign-in')
def folder_resident_back(request, parent_id):
    folder = Folder.objects.get(id=int(parent_id))
    back = folder.parent

    if back:
        return redirect(reverse('info:resident-folder', args=[int(back.pk)]))

    return redirect(reverse('info:resident-documents'))


@login_required(login_url='info:sign-in')
def delete_folder(request, id):
    condominium = get_condominium(request)
    folder = get_object_or_404(Folder, id=int(id), condominium=condominium)

    back = folder.parent

    if folder:
        folder.delete()
        messages.success(request, "Pasta e conteúdo removidos!")
    else:
        messages.error(request, "Pasta não encontrada!")

    if back:
        return redirect(reverse('info:folder', args=[int(back.pk)]))

    return redirect(reverse('info:documents'))


def add_folder(request, parent_id, page):
    condominium = get_condominium(request)
    form = FolderForm(request.POST or None)
    if request.method == 'POST':
        folder = Folder()
        folder.name = request.POST.get('name')
        folder.condominium = condominium
        if parent_id:
            folder.parent = Folder.objects.get(pk=int(parent_id))
        folder.save()
        messages.success(request, "Pasta adicionada!")

        last_dot_index = page.rfind('.')
        if last_dot_index != -1:
            _page = page[:last_dot_index]
            _id = page[last_dot_index + 1:]
            return redirect(reverse('info:' + _page, args=[int(_id)]))
        return redirect(reverse('info:' + page))

    context = {'form': form}

    return render(request, "info/condominium/document/add_folder.html", context=context)


@login_required(login_url='info:sign-in')
def edit_folder(request, id):
    condominium = get_condominium(request)
    instance = get_object_or_404(Folder, pk=int(id), condominium=condominium)
    form = FolderForm(instance=instance)
    if request.method == 'POST':
        form = FolderForm(request.POST)
        instance.name = request.POST.get('name')
        instance.save()
        messages.success(request, "Pasta atualizada!")

        back = instance.parent

        if back:
            return redirect(reverse('info:folder', args=[int(back.pk)]))

        return redirect(reverse('info:documents'))

    context = {'form': form}

    return render(request, "info/condominium/document/edit_folder.html", context=context)


def add_file(request, parent_id):
    condominium = get_condominium(request)
    form = LocalFileForm(request.POST or None, request.FILES or None)
    if request.method == 'POST':
        local_file = LocalFile()
        local_file.file = request.FILES.get('file')

        if local_file.file.size > 100 * 1024 * 1024:  # 100 MB
            messages.error(request, "Arquivo excede o limite de 100 MB de tamanho máximo!")
            context = {'form': form}
            return render(request, "info/condominium/document/add_file.html", context=context)

        local_file.condominium = condominium
        if parent_id:
            folder = Folder.objects.get(id=int(parent_id))
            local_file.folder = folder
        local_file.save()
        messages.success(request, "Arquivo adicionado!")

        if parent_id:
            return redirect(reverse('info:folder', args=[int(parent_id)]))

        return redirect(reverse('info:documents'))

    context = {'form': form}

    return render(request, "info/condominium/document/add_file.html", context=context)


@login_required(login_url='info:sign-in')
def delete_file(request, id):
    condominium = get_condominium(request)
    file = get_object_or_404(LocalFile, id=int(id), condominium=condominium)
    parent = file.folder
    if file:
        file.delete()
        messages.success(request, "Arquivo removido!")
    else:
        messages.error(request, "Arquivo não encontrado!")

    if parent:
        return redirect(reverse('info:folder', args=[int(parent.pk)]))

    return redirect(reverse('info:documents'))
