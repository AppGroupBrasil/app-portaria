import base64
import io

import pytz
from PIL import Image
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.forms import modelformset_factory
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse

from info.forms import AddChecklistForm, AddTaskForm, AddTaskProblemForm, ViewTaskProblemForm
from info.models import CondominiumProfile, Task, Checklist, HowTo, UserLocation
from info.utils import get_condominium

FIXED_TZ = pytz.timezone("America/Sao_Paulo")


@login_required(login_url='info:sign-in')
def add_checklist(request):
    condominium = get_condominium(request)

    user = CondominiumProfile.objects.get(pk=int(request.user.id))
    ip_address = request.META.get('HTTP_X_FORWARDED_FOR') or request.META.get('HTTP_CLIENT_IP')

    if not ip_address:
        ip_address = '127.0.0.1'

    location = UserLocation.objects.filter(condominium=user, ip_address=ip_address).order_by('-created').first()

    form = AddChecklistForm(request.POST or None)

    TaskFormset = modelformset_factory(Task, form=AddTaskForm, extra=1)
    tasks_queryset = Task.objects.none()
    tasks_formset = TaskFormset(request.POST or None, queryset=tasks_queryset, prefix="task")

    context = {'form': form,
               'tasks_formset': tasks_formset,
               }

    if all([form.is_valid(), tasks_formset.is_valid()]):

        checklist = Checklist()
        checklist.condominium = condominium
        checklist.title = form.cleaned_data['title']
        checklist.location = location
        checklist.save()

        count_tasks = 0
        for task_form in tasks_formset:
            if task_form.has_changed():
                task = Task()
                task.checklist = checklist
                task.task_name = task_form.cleaned_data['task_name']

                task.save()
                count_tasks = count_tasks + 1

        if count_tasks > 0:
            messages.success(request, "Checklist Cadastrado!")
            return redirect('info:dashboard')
        else:
            checklist.delete()
            messages.error(request, "Checklist não cadastrado pois não tinha itens para checar")
            return redirect('info:dashboard')

    else:
        print(form.errors)
        print("tasks_formset")
        print(tasks_formset.errors)

    return render(request, "info/condominium/checklist/add_checklist.html", context=context)


@login_required(login_url='info:sign-in')
def edit_checklist(request, id):
    condominium = get_condominium(request)
    checklist = Checklist.objects.get(condominium=condominium, pk=id)

    if not checklist:
        messages.error(request, "Checklist não encontrado")
        return redirect('info:dashboard')

    tasks = Task.objects.filter(checklist=checklist)

    form = AddChecklistForm(instance=checklist)

    TaskFormset = modelformset_factory(Task, form=AddTaskForm, extra=0)
    tasks_queryset = tasks
    tasks_formset = TaskFormset(request.POST or None, queryset=tasks_queryset, prefix="task")

    context = {'form': form,
               'tasks_formset': tasks_formset,
               }

    if request.method == "POST":
        form = AddChecklistForm(request.POST)
        if all([form.is_valid(), tasks_formset.is_valid()]):

            checklist.title = form.cleaned_data['title'] or checklist.title
            checklist.save()

            for task in tasks:
                task.delete()

            count_tasks = 0
            for task_form in tasks_formset:
                if task_form.cleaned_data['task_name']:
                    task = Task()
                    task.checklist = checklist
                    task.task_name = task_form.cleaned_data['task_name']

                    task.save()
                    count_tasks = count_tasks + 1

            if count_tasks > 0:
                messages.success(request, "Checklist Atualizado!")
                return redirect('info:checklists')
            else:
                checklist.delete()
                messages.error(request, "Checklist não cadastrado pois não tinha itens para checar")
                return redirect('info:checklists')

        else:
            print(form.errors)
            print("tasks_formset")
            print(tasks_formset.errors)

    return render(request, "info/condominium/checklist/edit_checklist.html", context=context)


@login_required(login_url='info:sign-in')
def delete_checklist(request, id):
    condominium = get_condominium(request)
    checklist = Checklist.objects.get(condominium=condominium, pk=id)

    if not checklist:
        messages.error(request, "Checklist não encontrado")
        return redirect('info:dashboard')

    checklist.delete()
    messages.success(request, "Checklist apagado")
    return redirect('info:checklists')


@login_required(login_url='info:sign-in')
def view_checklist(request, id):
    condominium = get_condominium(request)
    checklist = Checklist.objects.get(condominium=condominium, pk=id)

    if not checklist:
        messages.error(request, "Checklist não encontrado")
        return redirect('info:dashboard')

    tasks = Task.objects.filter(checklist=checklist)

    context = {'checklist': checklist,
               'tasks': tasks,}

    return render(request, "info/condominium/checklist/view_checklist.html", context=context)


@login_required(login_url='info:sign-in')
def clear_checklist(request, id):
    condominium = get_condominium(request)
    checklist = Checklist.objects.get(condominium=condominium, pk=id)

    if not checklist:
        messages.error(request, "Checklist não encontrado")
        return redirect('info:dashboard')

    tasks = Task.objects.filter(checklist=checklist)

    for task in tasks:
        task.is_completed = False
        task.reported_problem = False
        task.problem_description = ""
        task.reported_problem_image = None
        task.save()

    messages.success(request, "Checklist limpo!")
    return redirect('info:checklists')


@login_required(login_url='info:sign-in')
def checklists(request):

    condominium = get_condominium(request)
    checklists = Checklist.objects.filter(condominium=condominium).order_by("-created")

    search_name = request.GET.get('checklist_name')
    search_created = request.GET.get('checklist_created')

    if search_name:
        checklists = checklists.filter(title__contains=search_name)

    if search_created:
        checklists = checklists.filter(created=search_created)

    checklists_list = []
    for checklist in checklists:
        checklist_item = {
            'id': checklist.id,
            'title': checklist.title,
            'created': checklist.created.astimezone(FIXED_TZ),
        }

        checklist_tasks = Task.objects.filter(checklist=checklist)

        if all(task.is_completed for task in checklist_tasks):
            checklist_item['status'] = "Verificado com sucesso!"

        elif any(task.reported_problem for task in checklist_tasks):
            checklist_item['status'] = "Problema reportado!"
        else:
            checklist_item['status'] = "Ainda não verificado!"

        checklists_list.append(checklist_item)

    context = {'checklists_list': checklists_list,
               'user': condominium,
               }

    how_to_checklist_list = HowTo.objects.get(name__exact="Checklist > Listagem")
    if how_to_checklist_list.kind == "Texto":
        context['how_to_checklist_text'] = how_to_checklist_list.value
    else:
        context['how_to_checklist_link'] = how_to_checklist_list.value

    return render(request, "info/condominium/checklist/checklists.html", context=context)


@login_required(login_url='info:sign-in')
def add_task_problem(request, id):
    condominium = get_condominium(request)

    user = CondominiumProfile.objects.get(pk=int(request.user.id))
    ip_address = request.META.get('HTTP_X_FORWARDED_FOR') or request.META.get('HTTP_CLIENT_IP')

    if not ip_address:
        ip_address = '127.0.0.1'

    location = UserLocation.objects.filter(condominium=user, ip_address=ip_address).order_by('-created').first()

    task = Task.objects.get(pk=id, checklist__condominium=condominium)

    if not task:
        messages.error(request, "Tarefa não encontrada")
        return redirect('info:dashboard')

    form = AddTaskProblemForm(instance=task)

    if request.method == "POST":
        form = AddTaskProblemForm(request.POST, files=request.FILES)

        if form.is_valid() and form.has_changed():
            task.reported_problem = True
            task.is_completed = False
            task.problem_description = form.cleaned_data['problem_description'] or ""
            if form.cleaned_data['reported_problem_image']:
                task.reported_problem_image = form.cleaned_data['reported_problem_image']

            elif form.cleaned_data['webimg']:
                pic = form.cleaned_data['webimg']
                image_data = pic.split(',')[1]  # Remove the data URI prefix
                image_bytes = base64.b64decode(image_data)
                image_file = io.BytesIO(image_bytes)
                Image.open(image_file)
                image_file.seek(0)
                task.reported_problem_image = InMemoryUploadedFile(
                    image_file, None, task.task_name + '.jpg', 'image/jpeg', len(image_bytes), None)

            task.location = location
            task.save()
            messages.success(request, "Problema reportado!")

            return redirect(reverse('info:view-checklist', args=[task.checklist.id]))

    context = {'form': form,
               }
    return render(request, "info/condominium/checklist/report-task-problem.html", context=context)


@login_required(login_url='info:sign-in')
def task_completed(request, id):
    condominium = get_condominium(request)
    task = get_object_or_404(Task, pk=id, checklist__condominium=condominium)

    user = CondominiumProfile.objects.get(pk=int(request.user.id))
    ip_address = request.META.get('HTTP_X_FORWARDED_FOR') or request.META.get('HTTP_CLIENT_IP')

    if not ip_address:
        ip_address = '127.0.0.1'

    location = UserLocation.objects.filter(condominium=user, ip_address=ip_address).order_by('-created').first()

    task.is_completed = True
    task.reported_problem = False
    task.location = location
    task.save()

    messages.success(request, "Tarefa verificada!")
    return redirect(request.META.get('HTTP_REFERER', '/'))


@login_required(login_url='info:sign-in')
def view_task_problem(request, id):
    condominium = get_condominium(request)
    task = Task.objects.get(pk=id, checklist__condominium=condominium)

    if not task:
        messages.error(request, "Tarefa não encontrada")
        return redirect('info:dashboard')

    form = ViewTaskProblemForm(instance=task)

    context = {'form': form, }

    if task.reported_problem_image:
        context['img'] = task.reported_problem_image

    return render(request, "info/condominium/checklist/view-task-problem.html", context=context)
