import json
import pytz

from PIL import Image
from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.utils import timezone
import os

from django.template.defaultfilters import default

from .manager import *

FIXED_TZ = pytz.timezone("America/Sao_Paulo")


class CondominiumProfile(AbstractUser):
    username = None
    created = models.DateField(editable=False)
    condominium_name = models.CharField(max_length=60, null=True, blank=True)
    address = models.CharField(max_length=200, null=True, blank=True)
    liquidator_name = models.CharField(max_length=60, null=True, blank=True)
    admin_name = models.CharField(max_length=60, null=True, blank=True)
    whatsapp = models.CharField(max_length=15, null=True, blank=True)
    email_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    plan_expiration = models.DateField(null=True, blank=True)
    site = models.CharField(max_length=60, null=True, blank=True)
    email = models.EmailField(unique=True)
    is_staff = models.BooleanField(default=False)
    is_testing = models.BooleanField(default=True)
    is_administrator = models.BooleanField(default=False)
    cnpj = models.CharField(max_length=18, null=True, blank=True)
    work_for = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="employees",
    )
    resident_in = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="residents",
    )
    hide_contact = models.BooleanField(default=False)
    profile_pic = models.ImageField(
        upload_to="img/", verbose_name="Sua foto", null=True, blank=True
    )
    added_by_link = models.BooleanField(default=False)
    profile = models.CharField(max_length=15, null=True, blank=True, default="main")
    auto_approve = models.BooleanField(default=False)
    managed_by = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="administrator",
    )
    selected = models.IntegerField(default=0)
    use_tabs = models.BooleanField(default=False)
    defaulter = models.BooleanField(default=False)
    whatsapp_notification = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def get_boss(self):
        return self.work_for

    def get_employees(self):
        return self.employees.all()

    def get_reside_in(self):
        return self.resident_in

    def get_residents(self):
        return self.residents.all()

    def __str__(self):
        return self.condominium_name

    def save(self, *args, **kwargs):

        if not self.pk and not self.created:
            utc_now = timezone.now()
            self.created = utc_now.astimezone(FIXED_TZ).date()

        # Call the parent's save() method
        super().save(*args, **kwargs)

        # Open the uploaded image
        if self.profile_pic:
            try:
                file_path = self.profile_pic.path
                if not os.path.exists(file_path):
                    return
                image = Image.open(file_path)

                # Set the desired width and height for resizing
                max_width = 1280
                max_height = 720

                # Resize the image
                if image.width > max_width or image.height > max_height:
                    image.thumbnail((max_width, max_height))
                    image.save(file_path)
            except (FileNotFoundError, OSError):
                pass


@receiver(pre_delete, sender=CondominiumProfile)
def delete_image_file(sender, instance, **kwargs):
    # Delete the associated image file
    if instance.profile_pic:
        # Get the image file path
        file_path = instance.profile_pic.path
        # Delete the file from the file system
        if os.path.exists(file_path):
            os.remove(file_path)


class MessagesInformation(models.Model):
    condominium = models.ForeignKey(CondominiumProfile, on_delete=models.CASCADE)
    messages_limit = models.IntegerField(default=1000, verbose_name="Mensagens gratúitas")
    messages_used = models.IntegerField(default=0)
    price = models.FloatField(default=0.1, verbose_name="Preço por mensagem em R$")
    allow_charge = models.BooleanField(default=True)


class MessagesPayment(models.Model):
    condominium = models.ForeignKey(CondominiumProfile, on_delete=models.CASCADE)
    messages_used = models.IntegerField(default=0)
    price = models.FloatField(default=0.1, verbose_name="Preço por mensagem em R$")
    bill = models.FileField(upload_to="files/", verbose_name="Cobrança", blank=True, null=True)
    payment = models.FileField(upload_to="files/", verbose_name="Comprovante", blank=True, null=True)
    payed = models.BooleanField(default=False)

    def delete(self, *args, **kwargs):
        # Delete the file from storage
        if self.bill:
            file_path = self.bill.path
            if os.path.exists(file_path):
                os.remove(file_path)

        if self.payment:
            file_path = self.payment.path
            if os.path.exists(file_path):
                os.remove(file_path)


class Block(models.Model):
    condominium = models.ForeignKey(CondominiumProfile, on_delete=models.CASCADE)
    name = models.CharField(
        max_length=100,
        null=False,
        blank=False,
        verbose_name="Nome do Bloco/Quadra/Setor",
    )

    def __str__(self):

        return self.name or "Invalid"


class Apartment(models.Model):
    block = models.ForeignKey(Block, verbose_name="Bloco", on_delete=models.CASCADE)
    number = models.IntegerField(verbose_name="Número")
    complement = models.CharField(
        max_length=100, null=True, blank=True, verbose_name="Complemento", default=""
    )


class Resident(models.Model):
    apartment = models.ForeignKey(Apartment, on_delete=models.CASCADE)
    name = models.CharField(max_length=60, null=False, blank=False)
    kind = models.CharField(max_length=13, null=True, blank=True)
    email = models.EmailField()
    whatsapp = models.CharField(max_length=15, null=True, blank=True)
    hide_contact = models.BooleanField(default=False)
    defaulter = models.BooleanField(default=False)


class UserLocation(models.Model):
    condominium = models.ForeignKey(CondominiumProfile, on_delete=models.CASCADE)
    created = models.DateTimeField(editable=False)
    country = models.CharField(max_length=20, null=False, blank=False)
    latitude = models.CharField(max_length=30, null=False, blank=False)
    longitude = models.CharField(max_length=30, null=False, blank=False)
    ip_address = models.CharField(max_length=16, null=False, blank=False)
    address = models.CharField(max_length=100, null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.pk and not self.created:
            utc_now = timezone.now()
            self.created = utc_now.astimezone(FIXED_TZ)

        super().save(*args, **kwargs)


class Informative(models.Model):
    condominium = models.ForeignKey(CondominiumProfile, on_delete=models.CASCADE)
    title = models.CharField(
        max_length=200,
        null=False,
        blank=False,
        verbose_name="NOME OU LOCAL DA ATIVIDADE",
    )
    description = models.CharField(
        max_length=250, null=True, blank=True, verbose_name="DESCRIÇÃO"
    )
    created = models.DateTimeField(editable=False)
    kind = models.CharField(
        max_length=25, null=False, blank=False, default="Informativo"
    )
    location = models.ForeignKey(
        UserLocation, on_delete=models.CASCADE, null=True, blank=True
    )

    def save(self, *args, **kwargs):
        if not self.pk and not self.created:
            utc_now = timezone.now()
            self.created = utc_now.astimezone(FIXED_TZ)

        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class InformativeKind(models.Model):
    condominium = models.ForeignKey(CondominiumProfile, on_delete=models.CASCADE)
    name = models.CharField(
        max_length=200, null=False, blank=False, verbose_name="Tipo da Atividade"
    )

    def __str__(self):
        return self.name


class ActivityFunction(models.Model):
    informative = models.ForeignKey(Informative, on_delete=models.CASCADE)
    title = models.CharField(
        max_length=200, null=False, blank=False, verbose_name="Nome da função"
    )
    description = models.CharField(
        max_length=200, null=True, blank=True, verbose_name="Descrição"
    )
    link = models.CharField(
        max_length=500, null=True, blank=True, verbose_name="Link pro vídeo"
    )


class Function(models.Model):
    informative = models.ForeignKey(Informative, on_delete=models.CASCADE)
    title = models.CharField(
        max_length=200, null=False, blank=False, verbose_name="Nome da função"
    )

    # subtitle = models.CharField(max_length=200, null=True, blank=True, verbose_name="Subtítulo")
    # description = models.CharField(max_length=200, null=True, blank=True, verbose_name="Descrição")

    def __str__(self):
        return self.title


class FunctionItem(models.Model):
    function = models.ForeignKey(
        Function, on_delete=models.CASCADE, verbose_name="Função"
    )
    title = models.CharField(
        max_length=200, null=False, blank=False, verbose_name="Descrição"
    )
    # subtitle = models.CharField(max_length=200, null=True, blank=True, verbose_name="Subtitulo")
    # description = models.CharField(max_length=200, null=True, blank=True, verbose_name="Descrição")
    # images = models.ImageField(upload_to='img/')
    # files


class ImageModel(models.Model):
    function_item = models.ForeignKey(
        ActivityFunction, on_delete=models.CASCADE, blank=True
    )
    image = models.ImageField(upload_to="img/", verbose_name="Imagem do item")

    def save(self, *args, **kwargs):
        # Call the parent's save() method
        super().save(*args, **kwargs)

        # Open the uploaded image
        image = Image.open(self.image.path)

        # Set the desired width and height for resizing
        max_width = 1280
        max_height = 720

        # Resize the image
        if image.width > max_width or image.height > max_height:
            image.thumbnail((max_width, max_height))
            image.save(self.image.path)


@receiver(pre_delete, sender=ImageModel)
def delete_image_file(sender, instance, **kwargs):
    # Delete the associated image file
    if instance.image:
        # Get the image file path
        file_path = instance.image.path
        # Delete the file from the file system
        if os.path.exists(file_path):
            os.remove(file_path)


class FunctionItemFileModel(models.Model):
    function_item = models.ForeignKey(
        ActivityFunction, on_delete=models.CASCADE, blank=True
    )
    file = models.FileField(upload_to="files/", verbose_name="Arquivo")

    def __str__(self):
        return self.file.name

    def delete(self, *args, **kwargs):
        # Delete the file from storage
        file_path = self.file.path
        if os.path.exists(file_path):
            os.remove(file_path)
        super().delete(*args, **kwargs)


class FunctionItemVideoLink(models.Model):
    function_item = models.ForeignKey(
        ActivityFunction, on_delete=models.CASCADE, blank=True
    )
    link = models.CharField(
        max_length=500, null=True, blank=True, verbose_name="Link pro vídeo"
    )

    def __str__(self):
        return self.link


class Order(models.Model):
    received_by = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name="Funcionário que recebeu a correspondência",
    )
    apartment = models.ForeignKey(Apartment, on_delete=models.CASCADE)
    name = models.CharField(
        max_length=200, null=False, blank=False, verbose_name="Nome da correspondência"
    )
    description = models.CharField(
        max_length=250, null=True, blank=True, verbose_name="Descrição"
    )
    created = models.DateTimeField(editable=False, verbose_name="Recebido em")
    image = models.ImageField(
        upload_to="img/",
        verbose_name="Imagem da correspondência",
        null=True,
        blank=True,
    )
    delivered = models.DateTimeField(null=True, blank=True, verbose_name="Entregue em")
    delivered_by = models.CharField(
        max_length=50, null=True, blank=True, verbose_name="Entregue por"
    )
    collected_by = models.CharField(
        max_length=50, null=True, blank=True, verbose_name="Recebido por"
    )
    code = models.CharField(max_length=8, null=True, blank=True)
    qrcode = models.ImageField(upload_to="img/", null=True, blank=True)
    addressee = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        verbose_name="Morador destinatário",
        default="Não informado",
    )

    def save(self, *args, **kwargs):

        if not self.pk and not self.created:
            utc_now = timezone.now()
            self.created = utc_now.astimezone(FIXED_TZ)

        # Call the parent's save() method
        super().save(*args, **kwargs)

        # Open the uploaded image
        if self.image:
            image_file = Image.open(self.image.path)

            # Set the desired width and height for resizing
            max_width = 1280
            max_height = 720

            # Resize the image
            if image_file.width > max_width or image_file.height > max_height:
                image_file.thumbnail((max_width, max_height))
                image_file.save(self.image.path)

        qr_image_file = Image.open(self.qrcode.path)

        # Set the desired width and height for resizing
        max_width = 150
        max_height = 150

        # Resize the image
        if qr_image_file.width > max_width or qr_image_file.height > max_height:
            qr_image_file.thumbnail((max_width, max_height))
            qr_image_file.save(self.qrcode.path)

    def __str__(self):
        return self.name


@receiver(pre_delete, sender=Order)
def delete_image_file(sender, instance, **kwargs):
    # Delete the associated image file
    if instance.image:
        # Get the image file path
        file_path = instance.image.path
        # Delete the file from the file system
        if os.path.exists(file_path):
            os.remove(file_path)


class Review(models.Model):
    condominium = models.ForeignKey(CondominiumProfile, on_delete=models.CASCADE)
    service = models.CharField(
        max_length=50, null=True, blank=True, verbose_name="Item a ser avaliado"
    )
    provider = models.CharField(
        max_length=50, null=True, blank=True, verbose_name="Descrição"
    )
    created = models.DateTimeField(editable=False)
    allowed_users = models.ManyToManyField(
        CondominiumProfile, related_name="recipients"
    )

    def get_recipients(self):
        return self.recipients.all()

    def save(self, *args, **kwargs):
        if not self.pk and not self.created:
            utc_now = timezone.now()
            self.created = utc_now.astimezone(FIXED_TZ)

        super().save(*args, **kwargs)

    def __str__(self):
        return self.service or str(self.id)


class ReviewItem(models.Model):
    review = models.ForeignKey(Review, on_delete=models.CASCADE)
    service = models.CharField(
        max_length=50, null=False, blank=False, verbose_name="Item a ser avaliado"
    )
    is_link = models.BooleanField(default=False, verbose_name="É um link?")
    provider = models.CharField(
        max_length=50, null=True, blank=True, verbose_name="Descrição"
    )
    image = models.ImageField(
        upload_to="img/", verbose_name="Imagem", null=True, blank=True
    )

    def __str__(self):
        return self.service


class ReviewAnswer(models.Model):
    review = models.ForeignKey(Review, on_delete=models.CASCADE, null=True, blank=True)
    item = models.ForeignKey(
        ReviewItem, on_delete=models.CASCADE, null=True, blank=True
    )
    name = models.CharField(
        max_length=50, null=False, blank=False, verbose_name="Seu nome"
    )
    email = models.EmailField(null=True, blank=True)
    address = models.CharField(
        max_length=50, null=True, blank=True, verbose_name="Bloco/Apartamento"
    )
    message = models.CharField(
        max_length=500, null=True, blank=True, verbose_name="Comentário"
    )
    rate = models.IntegerField(default=0, verbose_name="")
    image = models.ImageField(
        upload_to="img/", verbose_name="Imagem", null=True, blank=True
    )
    created = models.DateField(editable=False)
    answer_pic = models.ImageField(
        upload_to="img/", verbose_name="Sua foto", null=True, blank=True
    )
    is_valid = models.BooleanField(default=True)

    def save(self, *args, **kwargs):

        if not self.pk and not self.created:
            utc_now = timezone.now()
            self.created = utc_now.astimezone(FIXED_TZ).date()

        # Call the parent's save() method
        super().save(*args, **kwargs)

        # Open the uploaded image
        if self.image:
            image_file = Image.open(self.image.path)

            # Set the desired width and height for resizing
            max_width = 1280
            max_height = 720

            # Resize the image
            if image_file.width > max_width or image_file.height > max_height:
                image_file.thumbnail((max_width, max_height))
                image_file.save(self.image.path)

        if self.answer_pic:
            image_file = Image.open(self.answer_pic.path)

            # Set the desired width and height for resizing
            max_width = 1280
            max_height = 720

            # Resize the image
            if image_file.width > max_width or image_file.height > max_height:
                image_file.thumbnail((max_width, max_height))
                image_file.save(self.answer_pic.path)


@receiver(pre_delete, sender=ReviewAnswer)
def delete_image_file(sender, instance, **kwargs):
    # Delete the associated image file
    if instance.image:
        # Get the image file path
        file_path = instance.image.path
        # Delete the file from the file system
        if os.path.exists(file_path):
            os.remove(file_path)

    if instance.answer_pic:
        # Get the image file path
        file_path = instance.answer_pic.path
        # Delete the file from the file system
        if os.path.exists(file_path):
            os.remove(file_path)


class SurveyModel(models.Model):
    condominium = models.ForeignKey(CondominiumProfile, on_delete=models.CASCADE)
    question = models.CharField(
        max_length=150, null=False, blank=False, verbose_name="Questão"
    )
    created = models.DateField(editable=False)
    allowed_users = models.ManyToManyField(
        CondominiumProfile, related_name="survey_recipients"
    )
    is_ended = models.BooleanField(default=False)
    location = models.ForeignKey(
        UserLocation, on_delete=models.CASCADE, null=True, blank=True
    )

    def save(self, *args, **kwargs):
        if not self.pk and not self.created:
            utc_now = timezone.now()
            self.created = utc_now.astimezone(FIXED_TZ).date()

        super().save(*args, **kwargs)

    def __str__(self):
        return self.question


class TokenModel(models.Model):
    token = models.CharField(max_length=50, null=False, blank=False)
    email = models.EmailField(null=True, blank=True)
    is_used = models.BooleanField(default=False)
    survey = models.ForeignKey(
        SurveyModel, on_delete=models.CASCADE, null=True, blank=True
    )


class SurveyOptionModel(models.Model):
    survey = models.ForeignKey(SurveyModel, on_delete=models.CASCADE)
    option = models.CharField(max_length=50, null=False, blank=False)
    image = models.ImageField(
        upload_to="img/", verbose_name="Sua foto", null=True, blank=True
    )
    is_link = models.BooleanField(default=False)
    votes = models.IntegerField(default=0, verbose_name="")

    def __str__(self):
        return self.option

    def save(self, *args, **kwargs):
        # Call the parent's save() method
        super().save(*args, **kwargs)

        if self.image:
            image_file = Image.open(self.image.path)

            # Set the desired width and height for resizing
            max_width = 1280
            max_height = 720

            # Resize the image
            if image_file.width > max_width or image_file.height > max_height:
                image_file.thumbnail((max_width, max_height))
                image_file.save(self.image.path)


@receiver(pre_delete, sender=SurveyOptionModel)
def delete_image_file(sender, instance, **kwargs):
    # Delete the associated image file
    if instance.image:
        # Get the image file path
        file_path = instance.image.path
        # Delete the file from the file system
        if os.path.exists(file_path):
            os.remove(file_path)


class SurveyAnswerModel(models.Model):
    survey = models.ForeignKey(
        SurveyModel, on_delete=models.CASCADE, verbose_name="Enquete"
    )
    option = models.ForeignKey(
        SurveyOptionModel, on_delete=models.CASCADE, verbose_name="Voto em"
    )
    name = models.CharField(
        max_length=50, null=False, blank=False, verbose_name="Seu nome"
    )
    email = models.EmailField(null=True, blank=True)
    address = models.CharField(
        max_length=50, null=True, blank=True, verbose_name="Bloco/Apartamento"
    )
    is_valid = models.BooleanField(default=False)
    answer_pic = models.ImageField(
        upload_to="img/", verbose_name="Sua foto", null=True, blank=True
    )
    created = models.DateField(editable=False)

    def save(self, *args, **kwargs):

        if not self.pk and not self.created:
            utc_now = timezone.now()
            self.created = utc_now.astimezone(FIXED_TZ).date()

        # Call the parent's save() method
        super().save(*args, **kwargs)

        if self.answer_pic:
            image_file = Image.open(self.answer_pic.path)

            # Set the desired width and height for resizing
            max_width = 1280
            max_height = 720

            # Resize the image
            if image_file.width > max_width or image_file.height > max_height:
                image_file.thumbnail((max_width, max_height))
                image_file.save(self.answer_pic.path)


@receiver(pre_delete, sender=SurveyAnswerModel)
def delete_image_file(sender, instance, **kwargs):
    # Delete the associated image file
    if instance.answer_pic:
        # Get the image file path
        file_path = instance.answer_pic.path
        # Delete the file from the file system
        if os.path.exists(file_path):
            os.remove(file_path)


class Contract(models.Model):
    condominium = models.ForeignKey(CondominiumProfile, on_delete=models.CASCADE)
    item = models.CharField(
        max_length=50, null=False, blank=False, verbose_name="Nome do item"
    )
    description = models.CharField(
        max_length=140, null=True, blank=True, verbose_name="Descrição"
    )
    image = models.ImageField(
        upload_to="img/", verbose_name="Foto", null=True, blank=True
    )
    last_maintenance = models.DateField(
        null=True, blank=True, verbose_name="Última manutenção"
    )
    next_maintenance = models.DateField(
        null=True, blank=True, verbose_name="Próxima manutenção"
    )
    to_email = models.EmailField(verbose_name="Email de quem será notificado")
    days_to_notify = models.IntegerField(default=1)
    domain = models.CharField(
        max_length=50, null=True, blank=True, verbose_name="domain"
    )
    notify_day = models.DateField(null=True, blank=True)
    created = models.DateField(editable=False)

    def save(self, *args, **kwargs):

        if not self.pk and not self.created:
            utc_now = timezone.now()
            self.created = utc_now.astimezone(FIXED_TZ).date()

        super().save(*args, **kwargs)

        if self.image:
            image_file = Image.open(self.image.path)

            max_width = 1280
            max_height = 720

            if image_file.width > max_width or image_file.height > max_height:
                image_file.thumbnail((max_width, max_height))
                image_file.save(self.image.path)


@receiver(pre_delete, sender=Contract)
def delete_image_file(sender, instance, **kwargs):
    # Delete the associated image file
    if instance.image:
        # Get the image file path
        file_path = instance.image.path
        # Delete the file from the file system
        if os.path.exists(file_path):
            os.remove(file_path)


class Checklist(models.Model):
    condominium = models.ForeignKey(CondominiumProfile, on_delete=models.CASCADE)
    title = models.CharField(
        max_length=200, null=False, blank=False, verbose_name="Nome da lista"
    )
    location = models.ForeignKey(
        UserLocation, on_delete=models.CASCADE, null=True, blank=True
    )
    created = models.DateField(editable=False)

    def save(self, *args, **kwargs):
        if not self.pk and not self.created:
            utc_now = timezone.now()
            self.created = utc_now.astimezone(FIXED_TZ).date()

        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class Task(models.Model):
    checklist = models.ForeignKey(Checklist, on_delete=models.CASCADE)
    task_name = models.CharField(
        max_length=30, null=False, blank=False, verbose_name="O que vai verificar"
    )
    is_completed = models.BooleanField(default=False)
    reported_problem = models.BooleanField(default=False)
    problem_description = models.CharField(max_length=100, null=True, blank=True)
    reported_problem_image = models.ImageField(
        upload_to="problem_images/",
        blank=True,
        verbose_name="Selecione uma foto da sua Galeria",
    )
    location = models.ForeignKey(
        UserLocation, on_delete=models.CASCADE, null=True, blank=True
    )

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.reported_problem_image:
            image_file = Image.open(self.reported_problem_image.path)

            max_width = 1280
            max_height = 720

            if image_file.width > max_width or image_file.height > max_height:
                image_file.thumbnail((max_width, max_height))
                image_file.save(self.reported_problem_image.path)


@receiver(pre_delete, sender=Task)
def delete_image_file(sender, instance, **kwargs):
    # Delete the associated image file
    if instance.reported_problem_image:
        # Get the image file path
        file_path = instance.reported_problem_image.path
        # Delete the file from the file system
        if os.path.exists(file_path):
            os.remove(file_path)


class HowTo(models.Model):
    name = models.CharField(max_length=150, null=False, blank=False)
    value = models.CharField(max_length=500, null=False, blank=False)
    kind = models.CharField(max_length=15, null=True, blank=True)


class Message(models.Model):
    condominium = models.ForeignKey(CondominiumProfile, on_delete=models.CASCADE)
    block = models.CharField(max_length=16, null=True, blank=True)
    apartment = models.CharField(max_length=16, null=True, blank=True)
    message = models.CharField(max_length=250, null=True, blank=True)
    kind = models.CharField(max_length=15, null=True, blank=True)
    to_list = models.TextField(blank=True, null=True)
    created = models.DateTimeField(editable=False)
    notify = models.BooleanField(default=False)

    def set_to_list(self, array):
        self.to_list = json.dumps(array)

    def get_to_list(self):
        return json.loads(self.to_list) if self.to_list else []

    def save(self, *args, **kwargs):
        if not self.pk and not self.created:
            utc_now = timezone.now()
            self.created = utc_now.astimezone(FIXED_TZ)

        super().save(*args, **kwargs)


class MessageFileModel(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE)
    file = models.FileField(upload_to="files/", verbose_name="Arquivo")

    def __str__(self):
        return self.file.name

    def delete(self, *args, **kwargs):
        # Delete the file from storage
        file_path = self.file.path
        if os.path.exists(file_path):
            os.remove(file_path)
        super().delete(*args, **kwargs)


class Signature(models.Model):
    condominium = models.ForeignKey(CondominiumProfile, on_delete=models.CASCADE)
    name = models.CharField(
        max_length=150, null=True, blank=True, verbose_name="Nome Completo"
    )
    whatsapp = models.CharField(max_length=15, null=True, blank=True)
    email = models.EmailField(unique=False)
    image = models.ImageField(
        upload_to="signature/",
        blank=True,
        verbose_name="Selecione a imagem da sua assinatura de email",
    )

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.image:
            image_file = Image.open(self.image.path)

            max_width = 150
            max_height = 150

            if image_file.width > max_width or image_file.height > max_height:
                image_file.thumbnail((max_width, max_height))
                image_file.save(self.image.path)


@receiver(pre_delete, sender=Signature)
def delete_image_file(sender, instance, **kwargs):
    # Delete the associated image file
    if instance.image:
        # Get the image file path
        file_path = instance.image.path
        # Delete the file from the file system
        if os.path.exists(file_path):
            os.remove(file_path)


class Visitant(models.Model):
    condominium = models.ForeignKey(CondominiumProfile, on_delete=models.CASCADE)
    block = models.CharField(
        max_length=16, null=True, blank=True, verbose_name="Autorizado para o Bloco"
    )
    apartment = models.CharField(
        max_length=16,
        null=True,
        blank=True,
        verbose_name="Autorizado para o Apartamento",
    )
    name = models.CharField(
        max_length=150,
        null=True,
        blank=True,
        verbose_name="Nome do Visitante ou Encomenda",
    )
    document = models.CharField(
        max_length=15,
        null=True,
        blank=True,
        verbose_name="Número do documento do Visitante",
    )
    comment = models.CharField(
        max_length=250, null=True, blank=True, verbose_name="Obcervações"
    )
    created = models.DateTimeField(editable=False)
    until = models.DateTimeField(null=True, blank=True, verbose_name="Autorizado até")
    allowed = models.BooleanField(default=True)
    security_name = models.CharField(
        max_length=150,
        null=True,
        blank=True,
        verbose_name="Nome do Porteiro que liberou",
    )
    visit_in = models.DateTimeField(
        null=True, blank=True, verbose_name="Liberado pela Portaria em"
    )
    leaves_in = models.DateTimeField(null=True, blank=True, verbose_name="Saída em")
    photo = models.ImageField(
        upload_to="visitants/", blank=True, verbose_name="Imagem do visitante"
    )
    check_photo = models.ImageField(
        upload_to="visitants/", blank=True, verbose_name="Foto/Documento do visitante"
    )
    vehicle_model = models.CharField(
        max_length=20, null=True, blank=True, verbose_name="Modelo do Veículo"
    )
    vehicle_plate = models.CharField(
        max_length=8, null=True, blank=True, verbose_name="Placa do Veículo"
    )
    resident = models.ForeignKey(
        CondominiumProfile,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="resident",
    )
    can_leave = models.BooleanField(default=False)
    leave_consent = models.BooleanField(default=False)
    arrived = models.BooleanField(default=False)
    visit_time = models.DurationField(null=True, blank=True)
    delivery_code = models.CharField(max_length=25, null=True, blank=True, default="")

    def save(self, *args, **kwargs):

        if not self.pk and not self.created:
            utc_now = timezone.now()
            self.created = utc_now.astimezone(FIXED_TZ)

        if self.visit_in and self.leaves_in:
            if timezone.is_naive(self.visit_in):
                self.visit_in = timezone.make_aware(self.visit_in, FIXED_TZ)
            if timezone.is_naive(self.leaves_in):
                self.leaves_in = timezone.make_aware(self.leaves_in, FIXED_TZ)
            self.visit_time = self.leaves_in - self.visit_in

        super().save(*args, **kwargs)

        if self.photo:
            image_file = Image.open(self.photo.path)

            max_width = 1280
            max_height = 720

            if image_file.width > max_width or image_file.height > max_height:
                image_file.thumbnail((max_width, max_height))
                image_file.save(self.photo.path)

        if self.check_photo:
            image_file = Image.open(self.check_photo.path)

            max_width = 1280
            max_height = 720

            if image_file.width > max_width or image_file.height > max_height:
                image_file.thumbnail((max_width, max_height))
                image_file.save(self.check_photo.path)


@receiver(pre_delete, sender=Visitant)
def delete_image_file(sender, instance, **kwargs):
    # Delete the associated image file
    if instance.photo:
        # Get the image file path
        file_path = instance.photo.path
        # Delete the file from the file system
        if os.path.exists(file_path):
            os.remove(file_path)

    if instance.check_photo:
        # Get the image file path
        file_path = instance.check_photo.path
        # Delete the file from the file system
        if os.path.exists(file_path):
            os.remove(file_path)


class VisitantReport(models.Model):
    condominium = models.ForeignKey(CondominiumProfile, on_delete=models.CASCADE)
    block = models.CharField(
        max_length=16, null=True, blank=True, verbose_name="Autorizado para o Bloco"
    )
    apartment = models.CharField(
        max_length=16,
        null=True,
        blank=True,
        verbose_name="Autorizado para o Apartamento",
    )
    name = models.CharField(
        max_length=150, null=False, blank=False, verbose_name="Nome do Visitante"
    )
    document = models.CharField(
        max_length=15,
        null=True,
        blank=True,
        verbose_name="Número do documento do Visitante",
    )
    comment = models.CharField(
        max_length=250, null=True, blank=True, verbose_name="Obcervações"
    )
    created = models.DateTimeField(editable=False)
    until = models.DateTimeField(null=True, blank=True, verbose_name="Autorizado até")
    allowed = models.BooleanField(default=True)
    security_name = models.CharField(
        max_length=150,
        null=True,
        blank=True,
        verbose_name="Nome do Porteiro que liberou",
    )
    visit_in = models.DateTimeField(
        null=True, blank=True, verbose_name="Liberado pela Portaria em"
    )
    leaves_in = models.DateTimeField(null=True, blank=True, verbose_name="Saída em")
    photo = models.ImageField(
        upload_to="report-visitants/", blank=True, verbose_name="Foto do visitante"
    )
    vehicle_model = models.CharField(
        max_length=20, null=True, blank=True, verbose_name="Modelo do Veículo"
    )
    vehicle_plate = models.CharField(
        max_length=8, null=True, blank=True, verbose_name="Placa do Veículo"
    )
    resident = models.ForeignKey(
        CondominiumProfile,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="report_resident",
    )

    def save(self, *args, **kwargs):

        if not self.pk and not self.created:
            utc_now = timezone.now()
            self.created = utc_now.astimezone(FIXED_TZ)

        super().save(*args, **kwargs)

        if self.photo:
            image_file = Image.open(self.photo.path)

            max_width = 1280
            max_height = 720

            if image_file.width > max_width or image_file.height > max_height:
                image_file.thumbnail((max_width, max_height))
                image_file.save(self.photo.path)


@receiver(pre_delete, sender=VisitantReport)
def delete_image_file(sender, instance, **kwargs):
    # Delete the associated image file
    if instance.photo:
        # Get the image file path
        file_path = instance.photo.path
        # Delete the file from the file system
        if os.path.exists(file_path):
            os.remove(file_path)


class Product(models.Model):
    condominium = models.ForeignKey(CondominiumProfile, on_delete=models.CASCADE)
    name = models.CharField(
        max_length=150, null=False, blank=False, verbose_name="Nome do Produto"
    )
    description = models.CharField(
        max_length=250, null=True, blank=True, verbose_name="Descrição"
    )
    image = models.ImageField(
        upload_to="report-visitants/", blank=True, verbose_name="Foto do produto"
    )
    quantity = models.IntegerField(default=0, verbose_name="Quantidade")
    warning_quantity = models.IntegerField(
        default=1, verbose_name="Avisar quando quantidade for menor que"
    )

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.image:
            image_file = Image.open(self.image.path)

            max_width = 300
            max_height = 300

            if image_file.width > max_width or image_file.height > max_height:
                image_file.thumbnail((max_width, max_height))
                image_file.save(self.image.path)


@receiver(pre_delete, sender=Product)
def delete_image_file(sender, instance, **kwargs):
    # Delete the associated image file
    if instance.image:
        # Get the image file path
        file_path = instance.image.path
        # Delete the file from the file system
        if os.path.exists(file_path):
            os.remove(file_path)


class StorageEntry(models.Model):
    condominium = models.ForeignKey(CondominiumProfile, on_delete=models.CASCADE)
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, verbose_name="Selecione o Produto"
    )
    type = models.CharField(max_length=8, null=True, blank=True)
    quantity = models.IntegerField(default=0, verbose_name="Quantidade")
    price = models.FloatField(default=0.0, verbose_name="Preço por unidade em R$:")
    created = models.DateTimeField(editable=False)
    worker = models.ForeignKey(
        CondominiumProfile, on_delete=models.CASCADE, related_name="worker"
    )

    def get_worker(self):
        return self.worker

    def save(self, *args, **kwargs):
        if not self.pk and not self.created:
            utc_now = timezone.now()
            self.created = utc_now.astimezone(FIXED_TZ)

        super().save(*args, **kwargs)


class Notification(models.Model):
    condominium = models.ForeignKey(CondominiumProfile, on_delete=models.CASCADE)
    message = models.CharField(max_length=250, null=True, blank=True)
    receiver = models.ForeignKey(
        CondominiumProfile, on_delete=models.CASCADE, related_name="receiver"
    )
    title = models.CharField(max_length=250, null=True, blank=True)
    url = models.CharField(max_length=750, null=True, blank=True)
    read = models.BooleanField(default=False)
    created = models.DateTimeField(editable=False)

    def get_receiver(self):
        return self.receiver

    def save(self, *args, **kwargs):
        if not self.pk and not self.created:
            utc_now = timezone.now()
            self.created = utc_now.astimezone(FIXED_TZ)

        super().save(*args, **kwargs)


class Bill(models.Model):
    condominium = models.ForeignKey(CondominiumProfile, on_delete=models.CASCADE)
    user = models.ForeignKey(
        CondominiumProfile, on_delete=models.CASCADE, related_name="resident_user"
    )
    file = models.FileField(upload_to="files/")
    sender = models.CharField(max_length=60, null=True, blank=True)
    created = models.DateTimeField(editable=False)

    def save(self, *args, **kwargs):
        if not self.pk and not self.created:
            utc_now = timezone.now()
            self.created = utc_now.astimezone(FIXED_TZ)

        super().save(*args, **kwargs)


class Timeline(models.Model):
    condominium = models.ForeignKey(CondominiumProfile, on_delete=models.CASCADE)
    title = models.CharField(
        max_length=60, null=False, blank=False, verbose_name="Título"
    )
    description = models.CharField(
        max_length=250, null=True, blank=True, verbose_name="Descrição"
    )
    start_date = models.DateField(
        null=False, blank=False, verbose_name="Data de ínicio"
    )
    end_date = models.DateField(null=False, blank=False, verbose_name="Data final")
    user = models.ForeignKey(
        CondominiumProfile, on_delete=models.CASCADE, related_name="timeline_user"
    )
    created = models.DateTimeField(editable=False)

    def save(self, *args, **kwargs):
        if not self.pk and not self.created:
            utc_now = timezone.now()
            self.created = utc_now.astimezone(FIXED_TZ)

        super().save(*args, **kwargs)


class TimelinePhase(models.Model):
    timeline = models.ForeignKey(Timeline, on_delete=models.CASCADE)
    title = models.CharField(
        max_length=60, null=False, blank=False, verbose_name="Título"
    )
    description = models.CharField(
        max_length=250, null=True, blank=True, verbose_name="Descrição"
    )
    end_date = models.DateField(null=False, blank=False, verbose_name="Data de entrega")
    image = models.ImageField(
        upload_to="timelines-phases/", blank=True, null=True, verbose_name="Imagem"
    )
    link = models.CharField(
        max_length=500, null=True, blank=True, verbose_name="Link pro vídeo"
    )
    created = models.DateTimeField(editable=False)

    def save(self, *args, **kwargs):

        if not self.pk and not self.created:
            utc_now = timezone.now()
            self.created = utc_now.astimezone(FIXED_TZ)

        super().save(*args, **kwargs)

        if self.image:
            image_file = Image.open(self.image.path)

            max_width = 1280
            max_height = 720

            if image_file.width > max_width or image_file.height > max_height:
                image_file.thumbnail((max_width, max_height))
                image_file.save(self.image.path)


@receiver(pre_delete, sender=TimelinePhase)
def delete_image_file(sender, instance, **kwargs):
    # Delete the associated image file
    if instance.image:
        # Get the image file path
        file_path = instance.image.path
        # Delete the file from the file system
        if os.path.exists(file_path):
            os.remove(file_path)


class ResidentActivity(models.Model):
    condominium = models.ForeignKey(CondominiumProfile, on_delete=models.CASCADE)
    kind = models.CharField(max_length=13, null=False, blank=False)
    protocol = models.CharField(max_length=13, null=False, blank=False)
    title = models.CharField(
        max_length=60, null=False, blank=False, verbose_name="Título"
    )
    description = models.CharField(
        max_length=250, null=False, blank=False, verbose_name="Descrição"
    )
    resident = models.CharField(
        max_length=150, null=True, blank=True, verbose_name="Morador"
    )
    apartment = models.ForeignKey(Apartment, on_delete=models.CASCADE, null=True, blank=True)
    responsible = models.CharField(
        max_length=150, null=True, blank=True, verbose_name="Responsável"
    )
    status = models.CharField(max_length=13, null=False, blank=False)
    created = models.DateTimeField(editable=False)
    link = models.CharField(
        max_length=500, null=True, blank=True, verbose_name="Link", default=""
    )
    image = models.FileField(
        upload_to="img/", verbose_name="Image", null=True, blank=True
    )

    def save(self, *args, **kwargs):
        if not self.pk and not self.created:
            utc_now = timezone.now()
            self.created = utc_now.astimezone(FIXED_TZ)

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Delete the file from storage
        image_path = self.image.path
        if os.path.exists(image_path):
            os.remove(image_path)

        super().delete(*args, **kwargs)


class ResidentActivityAnswer(models.Model):
    activity = models.ForeignKey(ResidentActivity, on_delete=models.CASCADE)
    message = models.CharField(
        max_length=250, null=False, blank=False, verbose_name="Mensagem"
    )
    auteur = models.CharField(
        max_length=150, null=True, blank=True, verbose_name="Autor"
    )
    created = models.DateTimeField(editable=False)
    link = models.CharField(
        max_length=500, null=True, blank=True, verbose_name="Link", default=""
    )
    image = models.FileField(
        upload_to="img/", verbose_name="Image", null=True, blank=True
    )

    def save(self, *args, **kwargs):
        if not self.pk and not self.created:
            utc_now = timezone.now()
            self.created = utc_now.astimezone(FIXED_TZ)

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Delete the file from storage
        image_path = self.image.path
        if os.path.exists(image_path):
            os.remove(image_path)

        super().delete(*args, **kwargs)


class Place(models.Model):

    condominium = models.ForeignKey(CondominiumProfile, on_delete=models.CASCADE)
    name = models.CharField(
        max_length=50, null=False, blank=False, verbose_name="Nome do Local"
    )
    description = models.TextField(
        max_length=250, null=False, blank=False, verbose_name="Descrição", default=""
    )
    capacity = models.IntegerField(default=0, verbose_name="Capacidade")
    price = models.FloatField(default=0, verbose_name="Preço da reserva")
    rules = models.FileField(
        upload_to="rules/", blank=True, null=True, verbose_name="Regras"
    )
    inspection = models.FileField(
        upload_to="inspections/",
        blank=True,
        null=True,
        verbose_name="Vistoria do espaço Reservado",
    )
    minimum_days_to_cancel = models.IntegerField(
        default=0, verbose_name="Quantidade mínima de dias para cancelar"
    )
    maximum_days_to_booking = models.IntegerField(
        default=60, verbose_name="Quantidade máxima de dias de antecedência"
    )
    internal_regime = models.FileField(
        upload_to="internal/", blank=True, null=True, verbose_name="Regime interno"
    )
    acceptance_terms = models.FileField(
        upload_to="acceptance/",
        blank=True,
        null=True,
        verbose_name="Termo de Aceitação",
    )
    maximum_unity_reservation_per_day = models.IntegerField(
        default=10, verbose_name="Máximo de reservas nesta área pela unidade por dia"
    )
    maximum_resident_reservation_per_day = models.IntegerField(
        default=10, verbose_name="Máximo de reservas nesta área pelo morador por dia"
    )
    maximum_unity_reservation_per_week = models.IntegerField(
        default=10, verbose_name="Máximo de reservas nesta área pela unidade por semana"
    )
    maximum_resident_reservation_per_week = models.IntegerField(
        default=10, verbose_name="Máximo de reservas nesta área pelo morador por semana"
    )
    maximum_unity_reservation_per_month = models.IntegerField(
        default=10, verbose_name="Máximo de reservas nesta área pela unidade por mês"
    )
    maximum_resident_reservation_per_month = models.IntegerField(
        default=10, verbose_name="Máximo de reservas nesta área pelo morador por mês"
    )
    maximum_unity_reservation_per_year = models.IntegerField(
        default=10, verbose_name="Máximo de reservas nesta área pela unidade por ano"
    )
    maximum_resident_reservation_per_year = models.IntegerField(
        default=10, verbose_name="Máximo de reservas nesta área pelo morador por ano"
    )
    minimum_days_to_reserve = models.IntegerField(
        default=0, verbose_name="Quantidade de dias de antecedência"
    )
    auto_confirmation = models.BooleanField(
        verbose_name="Confirmação automãtica?", default=False
    )
    blocked_areas = models.ManyToManyField(
        "self",
        null=True,
        blank=True,
        related_name="blocked_areas",
        verbose_name="Ãreas bloqueadas após reserva",
    )
    image = models.ImageField(
        upload_to="places/", blank=True, null=True, verbose_name="Imagem do local"
    )
    multi_reservations = models.BooleanField(
        verbose_name="Permite multiplas reservas?", default=False
    )
    hidden = models.BooleanField(verbose_name="Ocultar lugar?", default=False)
    allow_new_reservation = models.IntegerField(default=0)
    notification = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    def get_blocked_areas_choices(self):
        # Filter choices based on the current instance's condominium
        return Place.objects.filter(condominium=self.condominium).exclude(pk=self.pk)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        self.blocked_areas.set(self.get_blocked_areas_choices())

        if self.image:
            image_file = Image.open(self.image.path)

            max_width = 1280
            max_height = 720

            if image_file.width > max_width or image_file.height > max_height:
                image_file.thumbnail((max_width, max_height))
                image_file.save(self.image.path)

    def delete(self, *args, **kwargs):
        # Delete the file from storage
        if self.rules:
            file_path = self.rules.path
            if os.path.exists(file_path):
                os.remove(file_path)

        if self.inspection:
            file_path = self.inspection.path
            if os.path.exists(file_path):
                os.remove(file_path)

        if self.internal_regime:
            file_path = self.internal_regime.path
            if os.path.exists(file_path):
                os.remove(file_path)

        if self.acceptance_terms:
            file_path = self.acceptance_terms.path
            if os.path.exists(file_path):
                os.remove(file_path)

        if self.image:
            # Get the image file path
            image_path = self.image.path
            # Delete the file from the file system
            if os.path.exists(image_path):
                os.remove(image_path)

        super().delete(*args, **kwargs)


class ReservationTime(models.Model):
    init_time = models.TimeField(null=False, verbose_name="Início da Reserva")
    end_time = models.TimeField(null=False, verbose_name="Fim da Reserva")
    blocked = models.BooleanField(verbose_name="Horário Bloqueado?")
    day = models.CharField(
        max_length=57, null=True, blank=True, verbose_name="Dia da Semana"
    )
    condominium = models.ForeignKey(CondominiumProfile, on_delete=models.CASCADE)
    place = models.ForeignKey(
        Place, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Área"
    )


class BlockedDay(models.Model):
    condominium = models.ForeignKey(CondominiumProfile, on_delete=models.CASCADE)
    blocked_day = models.DateTimeField()
    init_time = models.TimeField(
        null=True, verbose_name="Início da Reserva", blank=True
    )
    end_time = models.TimeField(null=True, verbose_name="Fim da Reserva", blank=True)
    place = models.ForeignKey(Place, on_delete=models.CASCADE, null=True, blank=True)


class Reservation(models.Model):
    condominium = models.ForeignKey(
        CondominiumProfile, on_delete=models.CASCADE, null=False, blank=False
    )
    place = models.ForeignKey(Place, on_delete=models.CASCADE, null=False, blank=False)
    time = models.ForeignKey(
        ReservationTime, on_delete=models.CASCADE, null=False, blank=False
    )
    resident = models.ForeignKey(
        CondominiumProfile,
        on_delete=models.CASCADE,
        null=False,
        blank=False,
        related_name="reserved_by",
    )
    status = models.CharField(max_length=13, null=False, blank=False)
    guests = models.CharField(
        max_length=1500, null=True, blank=True, verbose_name="Lista de Convidados"
    )
    link = models.CharField(
        max_length=500, null=True, blank=True, verbose_name="Link para cobrança"
    )
    date = models.DateTimeField(null=False, blank=False)
    bill = models.FileField(
        upload_to="reservation_bill/",
        blank=True,
        null=True,
        verbose_name="Boleto de cobrança",
    )
    payment = models.FileField(
        upload_to="payments/",
        blank=True,
        null=True,
        verbose_name="Anexar comprovante de pagamento",
    )
    wait_payment = models.BooleanField(default=False)

    approved_by = models.CharField(max_length=50, null=True, blank=True, default="")
    canceled_by = models.CharField(max_length=50, null=True, blank=True, default="")
    removed_by_user = models.BooleanField(default=False)
    removed_by_manager = models.BooleanField(default=False)
    created = models.DateField(editable=False)

    def save(self, *args, **kwargs):
        if not self.pk and not self.created:
            utc_now = timezone.now()
            self.created = utc_now.astimezone(FIXED_TZ).date()

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Delete the file from storage
        if self.bill:
            file_path = self.bill.path
            if os.path.exists(file_path):
                os.remove(file_path)

        if self.payment:
            file_path = self.payment.path
            if os.path.exists(file_path):
                os.remove(file_path)

        super().delete(*args, **kwargs)


class CondominiumReservationLimits(models.Model):
    condominium = models.ForeignKey(
        CondominiumProfile, on_delete=models.CASCADE, null=False, blank=False
    )
    maximum_unity_reservation_per_day = models.IntegerField(
        default=10, verbose_name="Máximo de reservas pela unidade por dia"
    )
    maximum_resident_reservation_per_day = models.IntegerField(
        default=10, verbose_name="Máximo de reservas pelo morador por dia"
    )
    maximum_unity_reservation_per_week = models.IntegerField(
        default=10, verbose_name="Máximo de reservas pela unidade por semana"
    )
    maximum_resident_reservation_per_week = models.IntegerField(
        default=10, verbose_name="Máximo de reservas pelo morador por semana"
    )
    maximum_unity_reservation_per_month = models.IntegerField(
        default=10, verbose_name="Máximo de reservas pela unidade por mês"
    )
    maximum_resident_reservation_per_month = models.IntegerField(
        default=10, verbose_name="Máximo de reservas pelo morador por mês"
    )
    maximum_unity_reservation_per_year = models.IntegerField(
        default=10, verbose_name="Máximo de reservas pela unidade por ano"
    )
    maximum_resident_reservation_per_year = models.IntegerField(
        default=10, verbose_name="Máximo de reservas pelo morador por ano"
    )


class VisitantRequiredFields(models.Model):
    condominium = models.ForeignKey(
        CondominiumProfile, on_delete=models.CASCADE, null=False, blank=False
    )
    document = models.BooleanField(default=True)
    security_name = models.BooleanField(default=True)
    allow_vehicle = models.BooleanField(default=True)
    vehicle_model = models.BooleanField(default=False)
    vehicle_plate = models.BooleanField(default=False)
    photo = models.BooleanField(default=True, verbose_name="Enviar foto da galeria")
    pic = models.BooleanField(default=False, verbose_name="Tirar foto na hora")


class UserControl(models.Model):
    condominium = models.ForeignKey(CondominiumProfile, on_delete=models.CASCADE)
    user = models.ForeignKey(
        CondominiumProfile,
        on_delete=models.CASCADE,
        null=False,
        blank=False,
        related_name="checked_by",
    )
    created = models.DateTimeField(editable=False)
    country = models.CharField(max_length=20, null=False, blank=False)
    latitude = models.CharField(max_length=30, null=False, blank=False)
    longitude = models.CharField(max_length=30, null=False, blank=False)
    ip_address = models.CharField(max_length=16, null=False, blank=False)
    address = models.CharField(max_length=100, null=True, blank=True)
    check_in = models.DateTimeField(null=True, blank=True)
    check_out = models.DateTimeField(null=True, blank=True)
    session_time = models.DurationField(null=True, blank=True)

    def save(self, *args, **kwargs):

        if not self.pk and not self.created:
            utc_now = timezone.now()
            self.created = utc_now.astimezone(FIXED_TZ)

        if self.check_in and self.check_out:
            if timezone.is_naive(self.check_in):
                self.check_in = timezone.make_aware(self.check_in, FIXED_TZ)
            if timezone.is_naive(self.check_out):
                self.check_out = timezone.make_aware(self.check_out, FIXED_TZ)
            self.session_time = self.check_out - self.check_in

        super().save(*args, **kwargs)


class ResidentFeatures(models.Model):
    condominium = models.ForeignKey(
        CondominiumProfile, on_delete=models.CASCADE, null=False, blank=False
    )
    review = models.BooleanField(default=True)
    survey = models.BooleanField(default=True)
    bills = models.BooleanField(default=True)
    visitant = models.BooleanField(default=True)
    activity = models.BooleanField(default=True)
    booking = models.BooleanField(default=True)
    documents = models.BooleanField(default=True)
    permanent = models.BooleanField(default=True)


class Folder(models.Model):
    condominium = models.ForeignKey(
        CondominiumProfile, on_delete=models.CASCADE, null=False, blank=False
    )
    name = models.CharField(
        max_length=50, null=False, blank=False, verbose_name="Nome da pasta"
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="parent_folder",
    )

    def __str__(self):
        return self.name


class LocalFile(models.Model):
    condominium = models.ForeignKey(
        CondominiumProfile, on_delete=models.CASCADE, null=False, blank=False
    )
    name = models.CharField(
        max_length=200, null=False, blank=False, verbose_name="Nome da pasta"
    )
    folder = models.ForeignKey(Folder, on_delete=models.CASCADE, null=True, blank=True)
    file = models.FileField(upload_to="files/documents/", verbose_name="Arquivo")
    created = models.DateTimeField(editable=False)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.pk and not self.created:
            utc_now = timezone.now()
            self.created = utc_now.astimezone(FIXED_TZ)

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Delete the file from storage
        if self.file:
            file_path = self.file.path
            if os.path.exists(file_path):
                os.remove(file_path)

        super().delete(*args, **kwargs)


class ReportLogo(models.Model):
    condominium = models.ForeignKey(CondominiumProfile, on_delete=models.CASCADE)
    image = models.ImageField(
        upload_to="report/",
        blank=True,
        verbose_name="Selecione a imagem da sua assinatura de email",
    )

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.image:
            image_file = Image.open(self.image.path)

            max_width = 150
            max_height = 150

            if image_file.width > max_width or image_file.height > max_height:
                image_file.thumbnail((max_width, max_height))
                image_file.save(self.image.path)


class PushNotificationToken(models.Model):
    token = models.TextField(unique=False)
    user = models.ForeignKey(
        CondominiumProfile,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="push_tokens",
    )
    device_type = models.CharField(
        max_length=10, choices=(("web", "Web"), ("android", "Android"))
    )
    created_at = models.DateTimeField(editable=False)

    def save(self, *args, **kwargs):
        if not self.pk and not self.created_at:
            utc_now = timezone.now()
            self.created_at = utc_now.astimezone(FIXED_TZ)

        super().save(*args, **kwargs)


class Pedestrian(models.Model):
    condominium = models.ForeignKey(CondominiumProfile, on_delete=models.CASCADE)
    protocol = models.CharField(max_length=13, null=False, blank=False)
    name = models.CharField(max_length=60, null=False, blank=False)
    document = models.CharField(max_length=20, null=False, blank=False)
    photo = models.ImageField(upload_to="pedestrian/", blank=True, verbose_name="Foto")
    document_file = models.FileField(
        upload_to="pedestrian/", verbose_name="Anexar documento"
    )
    destination = models.CharField(
        max_length=50, null=False, blank=False, verbose_name="Vai para onde"
    )
    authorized_by = models.CharField(
        max_length=50, null=False, blank=False, verbose_name="Autorizado por"
    )
    obs = models.CharField(
        max_length=200, null=False, blank=False, verbose_name="Observação"
    )
    send_email = models.BooleanField(default=False)
    send_whatsapp = models.BooleanField(default=False)
    arrived = models.BooleanField(default=False)
    created = models.DateTimeField(editable=False)
    has_leaved = models.BooleanField(default=False)
    leaved_in = models.DateTimeField(null=True, blank=True, editable=False)

    def save(self, *args, **kwargs):

        if not self.pk and not self.created:
            utc_now = timezone.now()
            self.created = utc_now.astimezone(FIXED_TZ)

        super().save(*args, **kwargs)

        # Open the uploaded image
        if self.photo:
            image = Image.open(self.photo.path)

            # Set the desired width and height for resizing
            max_width = 1280
            max_height = 720

            # Resize the image
            if image.width > max_width or image.height > max_height:
                image.thumbnail((max_width, max_height))
                image.save(self.photo.path)

    def delete(self, *args, **kwargs):

        if self.photo:
            file_path = self.photo.path
            if os.path.exists(file_path):
                os.remove(file_path)

        if self.document_file:
            file_path = self.document_file.path
            if os.path.exists(file_path):
                os.remove(file_path)

        super().delete(*args, **kwargs)


class Vehicle(models.Model):
    condominium = models.ForeignKey(CondominiumProfile, on_delete=models.CASCADE)
    protocol = models.CharField(max_length=13, null=False, blank=False)
    name = models.CharField(max_length=60, null=False, blank=False)
    document = models.CharField(max_length=20, null=False, blank=False)
    photo = models.ImageField(upload_to="vehicle/", blank=True, verbose_name="Foto")
    document_file = models.FileField(
        upload_to="vehicle/", verbose_name="Anexar documento"
    )
    destination = models.CharField(
        max_length=50, null=False, blank=False, verbose_name="Vai para onde"
    )
    authorized_by = models.CharField(
        max_length=50, null=False, blank=False, verbose_name="Autorizado por"
    )
    obs = models.CharField(
        max_length=200, null=False, blank=False, verbose_name="Observação"
    )
    send_email = models.BooleanField(default=False)
    send_whatsapp = models.BooleanField(default=False)
    arrived = models.BooleanField(default=False)
    created = models.DateTimeField(editable=False)
    has_leaved = models.BooleanField(default=False)
    leaved_in = models.DateTimeField(null=True, blank=True, editable=False)
    vehicle = models.CharField(
        max_length=20, null=True, blank=True, verbose_name="Veículo"
    )
    vehicle_plate = models.CharField(
        max_length=8, null=True, blank=True, verbose_name="Placa"
    )

    def save(self, *args, **kwargs):

        if not self.pk and not self.created:
            utc_now = timezone.now()
            self.created = utc_now.astimezone(FIXED_TZ)

        super().save(*args, **kwargs)

        # Open the uploaded image
        if self.photo:
            image = Image.open(self.photo.path)

            # Set the desired width and height for resizing
            max_width = 1280
            max_height = 720

            # Resize the image
            if image.width > max_width or image.height > max_height:
                image.thumbnail((max_width, max_height))
                image.save(self.photo.path)

    def delete(self, *args, **kwargs):

        if self.photo:
            file_path = self.photo.path
            if os.path.exists(file_path):
                os.remove(file_path)

        if self.document_file:
            file_path = self.document_file.path
            if os.path.exists(file_path):
                os.remove(file_path)

        super().delete(*args, **kwargs)


class ResidentActivityKind(models.Model):
    condominium = models.ForeignKey(CondominiumProfile, on_delete=models.CASCADE)
    name = models.CharField(
        max_length=200, null=False, blank=False, verbose_name="Tipo da solicitação"
    )

    def __str__(self):
        return self.name


class ResidentActivityImage(models.Model):
    resident_activity = models.ForeignKey(
        ResidentActivity, on_delete=models.CASCADE, blank=True
    )
    image = models.ImageField(upload_to="img/", verbose_name="Imagem")

    def save(self, *args, **kwargs):
        # Call the parent's save() method
        super().save(*args, **kwargs)

        # Open the uploaded image
        image = Image.open(self.image.path)

        # Set the desired width and height for resizing
        max_width = 1280
        max_height = 720

        # Resize the image
        if image.width > max_width or image.height > max_height:
            image.thumbnail((max_width, max_height))
            image.save(self.image.path)

    def delete(self, *args, **kwargs):
        # Delete the file from storage
        if self.image:
            image_path = self.image.path
            if os.path.exists(image_path):
                os.remove(image_path)

        super().delete(*args, **kwargs)


class ResidentActivityFile(models.Model):
    resident_activity = models.ForeignKey(
        ResidentActivity, on_delete=models.CASCADE, blank=True
    )
    file = models.FileField(upload_to="files/resident_activities/", verbose_name="Arquivo")

    def delete(self, *args, **kwargs):
        # Delete the file from storage
        if self.file:
            file_path = self.file.path
            if os.path.exists(file_path):
                os.remove(file_path)

        super().delete(*args, **kwargs)
