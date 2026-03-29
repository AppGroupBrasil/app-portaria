from django.contrib import admin
from django.contrib.auth.models import Permission, User

# Register your models here.
from .models import *

admin.site.register(CondominiumProfile)
admin.site.register(Block)
admin.site.register(Apartment)
admin.site.register(Resident)
admin.site.register(ImageModel)
admin.site.register(Function)
admin.site.register(FunctionItem)
admin.site.register(Informative)
admin.site.register(HowTo)
admin.site.register(Contract)
admin.site.register(Permission)
admin.site.register(SurveyModel)
admin.site.register(SurveyOptionModel)
admin.site.register(SurveyAnswerModel)
admin.site.register(ResidentActivity)
admin.site.register(Place)
admin.site.register(Review)
