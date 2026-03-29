from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.forms import modelformset_factory
from django.shortcuts import redirect, render
from django.urls import reverse

from info.forms import AddTimelineForm, AddTimelinePhaseForm
from info.models import CondominiumProfile, Timeline, TimelinePhase
from info.utils import get_condominium


@login_required(login_url='info:sign-in')
def add_timeline(request):
    condominium = get_condominium(request)
    user = CondominiumProfile.objects.get(pk=int(request.user.id))

    form = AddTimelineForm(request.POST or None)

    context = {'form': form,
               }

    if form.is_valid():
        timeline = Timeline()
        timeline.condominium = condominium
        timeline.user = user
        timeline.title = form.cleaned_data['title']
        timeline.description = form.cleaned_data['description'] or ""
        timeline.start_date = form.cleaned_data['start_date']
        timeline.end_date = form.cleaned_data['end_date']
        timeline.save()

        messages.success(request, "Linha do tempo criada, você pode adicionar etapas selecionando-a")
        return redirect('info:timelines')

    else:
        print(form.errors)

    return render(request, "info/condominium/timeline/add_timeline.html", context=context)


@login_required(login_url='info:sign-in')
def timelines(request):
    condominium = get_condominium(request)
    timeline_list = Timeline.objects.filter(condominium=condominium).order_by("-created")
    context = {'timelines': timeline_list,
               'user': condominium
               }
    return render(request, "info/condominium/timeline/timelines.html", context=context)


@login_required(login_url='info:sign-in')
def view_timeline(request, id):
    timeline = Timeline.objects.get(pk=int(id))
    phases = TimelinePhase.objects.filter(timeline=timeline).order_by('-end_date')
    context = {'timeline': timeline,
               'phases': phases,
               'id': id
               }
    return render(request, "info/condominium/timeline/view_timeline.html", context=context)


@login_required(login_url='info:sign-in')
def export_timeline(request, id):
    condominium = get_condominium(request)
    timeline = Timeline.objects.get(pk=int(id))
    phases = TimelinePhase.objects.filter(timeline=timeline).order_by('-end_date')
    context = {'condominium': condominium,
               'timeline': timeline,
               'phases': phases,
               'id': id
               }
    return render(request, "info/condominium/report/timeline_pdf.html", context=context)


@login_required(login_url='info:sign-in')
def add_phase(request, id):
    timeline = Timeline.objects.get(pk=int(id))

    TimelinePhaseFormset = modelformset_factory(TimelinePhase, form=AddTimelinePhaseForm, extra=1)
    queryset = TimelinePhase.objects.none()
    formset = TimelinePhaseFormset(request.POST or None, files=request.FILES or None, queryset=queryset, prefix="phase")

    if request.method == "POST":
        if all([formset.is_valid()]):

            for added in formset:
                if added.has_changed():
                    phase = TimelinePhase()
                    phase.timeline = timeline
                    phase.title = added.cleaned_data['title']
                    phase.description = added.cleaned_data['description'] or ""
                    phase.end_date = added.cleaned_data['end_date']
                    if added.cleaned_data['image']:
                        phase.image = added.cleaned_data['image']
                    phase.link = added.cleaned_data['link'] or ""
                    phase.save()
            messages.success(request, "Etapas adicionadas!")
            return redirect(reverse('info:timelines'))
        else:
            print(formset.errors)
    context = {'formset': formset,
               }
    return render(request, "info/condominium/timeline/add_phase.html", context=context)


@login_required(login_url='info:sign-in')
def delete_timeline(request, id):
    timeline = Timeline.objects.get(pk=int(id))
    timeline.delete()
    messages.success(request, "Linha do tempo removida")
    return redirect(reverse('info:timelines'))


@login_required(login_url='info:sign-in')
def update_timeline(request, id):
    timeline = Timeline.objects.get(pk=id)

    form = AddTimelineForm(instance=timeline)

    if request.method == "POST":

        form = AddTimelineForm(request.POST)
        if form.is_valid():
            timeline.title = form.cleaned_data['title']
            timeline.description = form.cleaned_data['description'] or ""
            timeline.start_date = form.cleaned_data['start_date']
            timeline.end_date = form.cleaned_data['end_date']
            timeline.save()

        messages.success(request, "Timeline atualizada!")

        return redirect(reverse('info:timelines'))
    else:
        print(form.errors)

    context = {'form': form,
               }
    return render(request, "info/condominium/timeline/edit_timeline.html", context=context)
