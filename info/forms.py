import pytz
from django.contrib.auth.forms import PasswordResetForm, PasswordChangeForm
from django.contrib.auth.models import User
from django import forms

from .models import CondominiumProfile, Apartment, Block, Informative, Function, FunctionItem, ImageModel, Order, \
    Resident, FunctionItemFileModel, Review, ReviewAnswer, SurveyModel, Contract, Checklist, Task, HowTo, Message, \
    FunctionItemVideoLink, Signature, Visitant, Product, StorageEntry, InformativeKind, ReviewItem, SurveyAnswerModel, \
    Timeline, TimelinePhase, ResidentActivity, ResidentActivityAnswer, Place, ReservationTime, \
    CondominiumReservationLimits, BlockedDay, Reservation, Folder, LocalFile, ReportLogo, Pedestrian, Vehicle, \
    MessagesInformation, MessagesPayment, ResidentActivityImage, ResidentActivityFile


FIXED_TZ = pytz.timezone("America/Sao_Paulo")


class UserForm(forms.Form):
    condominium_name = forms.CharField(max_length=60, required=True, label="Nome do Condomínio", widget=forms.TextInput(
        attrs={'placeholder': '*Nome do Condomínio..',
               'class': 'form-control'}))
    email = forms.EmailField(max_length=254, required=True, label="Email para receber a senha", widget=forms.TextInput(
        attrs={'placeholder': '*Email..',
               'class': 'form-control'}))
    cnpj = forms.CharField(max_length=18, required=False, label="CNPJ", widget=forms.TextInput(
        attrs={'placeholder': 'CNPJ..',
               'class': 'form-control cnpj'}))
    address = forms.CharField(max_length=200, required=False, label="Endereço", widget=forms.TextInput(
        attrs={'placeholder': 'Endereço..',
               'class': 'form-control'}))
    liquidator_name = forms.CharField(max_length=60, required=False, label="Porteiro/Responsável",
                                      widget=forms.TextInput(
                                          attrs={'placeholder': 'Nome do Responsável..',
                                                 'class': 'form-control'}))

    whatsapp = forms.CharField(max_length=15, required=False, label="Whatsapp", widget=forms.TextInput(
        attrs={'placeholder': 'Whatsapp..',
               'class': 'form-control'}))

    # admin_name = forms.CharField(max_length=60, required=False, label="Nome da Administradora", widget=forms.TextInput(
    #     attrs={'placeholder': 'Nome da Administradora..',
    #            'class': 'form-control'}))
    # site = forms.CharField(max_length=60, required=False, label="Site", widget=forms.TextInput(
    #     attrs={'placeholder': 'Site..',
    #            'class': 'form-control'}))
    class Meta:
        model = CondominiumProfile
        fields = ("condominium_name", "email", "address", "cnpj", "liquidator_name", "whatsapp",)
        # exclude = ("admin_name", "site")


class UserEmailForm(forms.Form):
    email = forms.EmailField(max_length=254, required=True, widget=forms.TextInput(
        attrs={'placeholder': '*Email..',
               'class': 'form-control'}))

    class Meta:
        model = User
        fields = ('email',)


class UserUpdateForm(forms.ModelForm):
    condominium_name = forms.CharField(max_length=60, required=True, label="Nome do Condomínio",
                                       widget=forms.TextInput(
                                           attrs={'placeholder': '*Nome do Condomínio..',
                                                  'class': 'form-control'}))

    cnpj = forms.CharField(max_length=18, required=False, label="CNPJ", widget=forms.TextInput(
        attrs={'placeholder': 'CNPJ..',
               'class': 'form-control cnpj'}))
    address = forms.CharField(max_length=200, required=False, label="Endereço", widget=forms.TextInput(
        attrs={'placeholder': 'Endereço..',
               'class': 'form-control'}))
    liquidator_name = forms.CharField(max_length=60, required=False, label="Síndico/Responsável",
                                      widget=forms.TextInput(
                                          attrs={'placeholder': 'Nome do Síndico..',
                                                 'class': 'form-control'}))

    whatsapp = forms.CharField(max_length=15, required=False, label="Whatsapp", widget=forms.TextInput(
        attrs={'placeholder': 'Whatsapp..',
               'class': 'form-control'}))

    admin_name = forms.CharField(max_length=60, required=False, label="Nome da Administradora", widget=forms.TextInput(
        attrs={'placeholder': 'Nome da Administradora..',
               'class': 'form-control'}))
    site = forms.CharField(max_length=60, required=False, label="Site", widget=forms.TextInput(
        attrs={'placeholder': 'Site..',
               'class': 'form-control'}))

    class Meta:
        model = CondominiumProfile
        fields = ("condominium_name", "cnpj", "address", "liquidator_name", "whatsapp", "admin_name", "site",)


class UserResidentUpdateForm(forms.ModelForm):
    condominium_name = forms.CharField(max_length=60, required=True, label="Seu nome",
                                       widget=forms.TextInput(
                                           attrs={'placeholder': '*Nome do Morador..',
                                                  'class': 'form-control'}))

    whatsapp = forms.CharField(max_length=15, required=False, label="Telefone/Whatsapp (Interfone)",
                               widget=forms.TextInput(
                                   attrs={'placeholder': 'Whatsapp..',
                                          'class': 'form-control'}))

    class Meta:
        model = CondominiumProfile
        fields = ("condominium_name", "whatsapp",)


class ViewUserForm(forms.ModelForm):
    condominium_name = forms.CharField(max_length=60, required=True, label="Nome do Condomínio", widget=forms.TextInput(
        attrs={'class': 'form-control',
               'readonly': 'readonly'}))
    email = forms.EmailField(max_length=254, required=True, label="Email para receber a senha", widget=forms.TextInput(
        attrs={'class': 'form-control',
               'readonly': 'readonly'}))

    whatsapp = forms.CharField(max_length=15, required=False, label="Whatsapp", widget=forms.TextInput(
        attrs={'class': 'form-control', 'readonly': 'readonly'}))

    class Meta:
        model = CondominiumProfile
        fields = ("condominium_name", "email", "whatsapp",)


class AuthForm(forms.Form):
    email = forms.EmailField(max_length=254, required=True, label='Email', widget=forms.TextInput(
        attrs={'placeholder': '*Email..',
               'class': 'form-control form-control-lg'}))
    password = forms.CharField(max_length=4, required=True, label="Senha", widget=forms.PasswordInput(
        attrs={'placeholder': '*Senha..',
               'class': 'form-control form-control-lg password',
               'id': 'password-input'}))

    class Meta:
        model = CondominiumProfile
        fields = ('email', 'password',)


class UserProfileForm(forms.ModelForm):
    condominium_name = forms.CharField(max_length=60, required=True, label="Condomínio", widget=forms.TextInput(
        attrs={'placeholder': '*Nome do Condomínio..',
               'class': 'form-control',
               'readonly': 'readonly'}))
    email = forms.EmailField(max_length=254, required=True, label='Email', widget=forms.TextInput(
        attrs={'placeholder': '*Email..',
               'class': 'form-control form-control-lg',
               'readonly': 'readonly'}))
    cnpj = forms.CharField(max_length=18, required=False, label="CNPJ", widget=forms.TextInput(
        attrs={'placeholder': 'CNPJ..',
               'class': 'form-control cnpj',
               'readonly': 'readonly'}))

    class Meta:
        model = CondominiumProfile
        fields = ('condominium_name', 'email', 'cnpj', 'plan_expiration', 'is_active',)


class RequestPasswordForm(PasswordResetForm):
    email = forms.EmailField(max_length=254, required=True, widget=forms.TextInput(
        attrs={'placeholder': '*Email..',
               'class': 'form-control form-control-lg'}))

    class Meta:
        model = User
        fields = ('email',)


class ForgottenPasswordForm(forms.Form):
    new_password1 = forms.CharField(max_length=4, required=True, label='Senha', widget=forms.PasswordInput(
        attrs={'placeholder': '*Nova senha numérica..',
               'class': 'form-control form-control-lg password', 'id': 'password-input'}))
    new_password2 = forms.CharField(max_length=4, required=True, label='Confirme a senha', widget=forms.PasswordInput(
        attrs={'placeholder': '*Confirme nova senha..',
               'class': 'form-control form-control-lg password'}))

    class Meta:
        model = CondominiumProfile
        fields = ('password1', 'password2',)


class ChangePasswordForm(PasswordChangeForm):
    old_password = forms.CharField(max_length=4, required=True, label="Senha antiga", widget=forms.PasswordInput(
        attrs={'placeholder': '*Senha antiga..',
               'class': 'form-control form-control-lg password'}))
    new_password1 = forms.CharField(max_length=4, required=True, label="Nova Senha", widget=forms.PasswordInput(
        attrs={'placeholder': '*Nova Senha..',
               'class': 'form-control form-control-lg password'}))
    new_password2 = forms.CharField(max_length=4, required=True, label="Confirme a senha", widget=forms.PasswordInput(
        attrs={'placeholder': '*Confirme a senha..',
               'class': 'form-control form-control-lg password'}))

    class Meta:
        model = User
        fields = ('password1', 'password2',)


class AddBlockForm(forms.ModelForm):
    class Meta:
        model = Block
        fields = ("name",)


class AddApartmentForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        blocks = kwargs.pop('blocks', None)
        super().__init__(*args, **kwargs)

        if blocks:
            self.fields['block'].queryset = blocks

        self.fields['block'].choices = [('', 'Selecione o bloco do apartamento')] + list(
            self.fields['block'].choices)[1:]

    class Meta:
        model = Apartment
        fields = "__all__"


class AddedApartmentForm(forms.ModelForm):
    class Meta:
        model = Apartment
        fields = ('number', 'complement',)


class AddResidentForm(forms.ModelForm):
    KINDS = [
        ('Proprietário', 'Proprietário'),
        ('Inquilino', 'Inquilino'),
        ('Procurador', 'Procurador'),
        ('Depedente', 'Dependente'),
        ('Cônjuge', 'Cônjuge'),
        ('Funcionário', 'Funcionário'),
        ('Outro', 'Outro'),
    ]

    block = forms.ModelChoiceField(queryset=Block.objects.none(), label="Bloco")
    apartment = forms.ModelChoiceField(queryset=Apartment.objects.none(), label="Apartamento")
    kind = forms.CharField(max_length=13, widget=forms.Select(choices=KINDS), label="Tipo")
    name = forms.CharField(max_length=60, required=True, label="Nome do Morador", widget=forms.TextInput(
        attrs={'placeholder': '*Nome..',
               'class': 'form-control'}))
    email = forms.EmailField(max_length=254, required=True, label="Email para contato", widget=forms.TextInput(
        attrs={'placeholder': '*Email..',
               'class': 'form-control form-control-lg'}))
    whatsapp = forms.CharField(max_length=15, required=False, label="Whatsapp", widget=forms.TextInput(
        attrs={'placeholder': 'Whatsapp..',
               'class': 'form-control'}))

    image = forms.ImageField(label="Foto do morador", required=False, )

    def __init__(self, *args, **kwargs):
        blocks = kwargs.pop('blocks', None)
        super().__init__(*args, **kwargs)

        if blocks:
            self.fields['block'].queryset = blocks

        self.fields['block'].choices = [('', 'Selecione o bloco do apartamento')] + list(
            self.fields['block'].choices)[1:]

    class Meta:
        model = Apartment
        fields = ('block', 'apartment', 'name', 'kind', 'email', 'whatsapp', 'image')


class AddManagerResidentForm(forms.ModelForm):
    block = forms.ModelChoiceField(queryset=Block.objects.none(), label="Bloco")
    apartment = forms.ModelChoiceField(queryset=Apartment.objects.none(), label="Apartamento")

    def __init__(self, *args, **kwargs):
        blocks = kwargs.pop('blocks', None)
        super().__init__(*args, **kwargs)

        if blocks:
            self.fields['block'].queryset = blocks

        self.fields['block'].choices = [('', 'Selecione o bloco do apartamento')] + list(
            self.fields['block'].choices)[1:]

    class Meta:
        model = Apartment
        fields = ('block', 'apartment',)


class UpdateResidentForm(forms.ModelForm):
    KINDS = [
        ('Proprietário', 'Proprietário'),
        ('Inquilino', 'Inquilino'),
        ('Procurador', 'Procurador'),
        ('Depedente', 'Dependente'),
        ('Cônjuge', 'Cônjuge'),
        ('Funcionário', 'Funcionário'),
        ('Outro', 'Outro'),
    ]

    name = forms.CharField(max_length=60, required=True, widget=forms.TextInput(
        attrs={'placeholder': '*Nome..',
               'class': 'form-control'}))
    email = forms.EmailField(max_length=254, required=True, label="Email para contato", widget=forms.TextInput(
        attrs={'placeholder': '*Email..',
               'class': 'form-control form-control-lg'}))
    kind = forms.CharField(max_length=13, widget=forms.Select(choices=KINDS), label="Tipo")
    whatsapp = forms.CharField(max_length=15, required=False, label="Whatsapp", widget=forms.TextInput(
        attrs={'placeholder': 'Whatsapp..',
               'class': 'form-control'}))

    class Meta:
        model = Resident
        fields = ('name', 'email', 'kind', 'whatsapp')


class AddInformativeForm(forms.ModelForm):
    kind = forms.ModelChoiceField(queryset=InformativeKind.objects.none(), label="SELECIONE O TIPO DE ATIVIDADE")

    # description = forms.CharField(max_length=140, required=False, label="Descrição", widget=forms.Textarea(
    #     attrs={
    #         'class': 'form-control',
    #         'rows': 4, }))

    def __init__(self, *args, **kwargs):
        informative_kind = kwargs.pop('informative_kind', None)
        super().__init__(*args, **kwargs)

        if informative_kind:
            self.fields['kind'].queryset = informative_kind
            self.fields['kind'].choices = [('', 'TIPO DE ATIVIDADE')] + list(
                self.fields['kind'].choices)[1:]

    class Meta:
        model = Informative
        fields = ('kind', 'title',)


class AddInformativeKindForm(forms.ModelForm):
    class Meta:
        model = InformativeKind
        fields = ('name',)


class EditInformativeForm(forms.ModelForm):
    kind = forms.CharField(max_length=25, required=False, label="Tipo da Função", widget=forms.TextInput(
        attrs={'class': 'form-control',
               'readonly': 'readonly'}))

    description = forms.CharField(max_length=140, required=False, label="Descrição", widget=forms.Textarea(
        attrs={
            'class': 'form-control',
            'rows': 4, }))

    class Meta:
        model = Informative
        fields = ('kind', 'title', 'description',)


class AddFunctionForm(forms.ModelForm):
    title = forms.CharField(max_length=200, required=False, label="Nome da função", widget=forms.TextInput(
        attrs={'placeholder': 'Digite um nome para poder adicionar descrições',
               'class': 'form-control'}))

    class Meta:
        model = Function
        fields = ('title',)


class EditFunctionForm(forms.ModelForm):
    title = forms.CharField(max_length=200, required=False, label="Nome da função", widget=forms.TextInput(
        attrs={'placeholder': '*Função..',
               'class': 'form-control',
               'readonly': 'readonly'}))

    class Meta:
        model = Function
        fields = ('title',)


class AddFunctionItemForm(forms.ModelForm):
    funcao = forms.CharField(max_length=60, required=False, label="", widget=forms.TextInput(
        attrs={'placeholder': '*Função..',
               'class': 'form-control hidden',
               'readonly': 'readonly'}))
    title = forms.CharField(max_length=200, required=False, label="Descrição", widget=forms.TextInput(
        attrs={'placeholder': 'Digite a descrição para poder adicionar arquivos',
               'class': 'form-control'}))

    class Meta:
        model = FunctionItem
        fields = ('funcao', 'title',)


class EditFunctionItemForm(forms.ModelForm):
    funcao = forms.CharField(max_length=60, required=False, label="Função", widget=forms.TextInput(
        attrs={'placeholder': '*Função..',
               'class': 'form-control',
               'readonly': 'readonly'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get('instance')
        if instance:
            self.fields['funcao'].initial = instance.function.title

    class Meta:
        model = FunctionItem
        fields = ('funcao', 'title',)


class ViewFunctionItemForm(forms.ModelForm):
    class Meta:
        model = FunctionItem
        fields = ('function', 'title',)


class AddImageForm(forms.ModelForm):
    item_name = forms.CharField(max_length=60, required=False, label="Item", widget=forms.TextInput(
        attrs={'placeholder': '*Item de função..',
               'class': 'form-control',
               'readonly': 'readonly'}))

    class Meta:
        model = ImageModel
        fields = ('item_name', 'image',)
        exclude = ('function_item',)


class EditImageForm(forms.ModelForm):
    item_name = forms.CharField(max_length=60, required=False, label="Item", widget=forms.TextInput(
        attrs={'placeholder': '*Item de função..',
               'class': 'form-control',
               'readonly': 'readonly'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get('instance')
        if instance:
            self.fields['item_name'].initial = instance.function_item.title

    class Meta:
        model = ImageModel
        fields = ('item_name', 'image',)
        exclude = ('function_item',)


class AddFunctionItemFileForm(forms.ModelForm):
    item_name = forms.CharField(max_length=60, required=False, label="Item", widget=forms.TextInput(
        attrs={'class': 'form-control',
               'readonly': 'readonly'}))

    class Meta:
        model = FunctionItemFileModel
        fields = ('item_name', 'file',)
        exclude = ('function_item',)


class EditFunctionItemFileForm(forms.ModelForm):
    item_name = forms.CharField(max_length=60, required=False, label="Item", widget=forms.TextInput(
        attrs={'class': 'form-control',
               'readonly': 'readonly'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get('instance')
        if instance:
            self.fields['item_name'].initial = instance.function_item.title

    class Meta:
        model = FunctionItemFileModel
        fields = ('item_name', 'file',)
        exclude = ('function_item',)


class AddFunctionItemLinkVideoForm(forms.ModelForm):
    item_name = forms.CharField(max_length=60, required=False, label="Item", widget=forms.TextInput(
        attrs={'class': 'form-control',
               'readonly': 'readonly'}))

    class Meta:
        model = FunctionItemVideoLink
        fields = ('item_name', 'link',)
        exclude = ('function_item',)


class EditFunctionItemLinkVideoForm(forms.ModelForm):
    item_name = forms.CharField(max_length=60, required=False, label="Item", widget=forms.TextInput(
        attrs={'class': 'form-control',
               'readonly': 'readonly'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get('instance')
        if instance:
            self.fields['item_name'].initial = instance.function_item.title

    class Meta:
        model = FunctionItemVideoLink
        fields = ('item_name', 'link',)
        exclude = ('function_item',)


class ExcelUploadForm(forms.Form):
    excel_file = forms.FileField(label='Selecione arquivo Excel para cadastrar')


class OrderNotificationForm(forms.ModelForm):
    KINDS = [
        ('CORRESPONDÊNCIA', 'CORRESPONDÊNCIA'),
        ('ENCOMENDA', 'ENCOMENDA'),
        ('ENVELOPE', 'ENVELOPE'),
        ('SEDEX', 'SEDEX'),
        ('ALIMENTAÇÃO', 'ALIMENTAÇÃO'),
        ('DEMAIS ENCOMENDAS', 'DEMAIS ENCOMENDAS'),
    ]

    block = forms.ModelChoiceField(queryset=Block.objects.none(), label="Bloco")
    apartment = forms.ModelChoiceField(queryset=Apartment.objects.none(), label="Apartamento", required=False)
    name = forms.CharField(max_length=25, widget=forms.Select(choices=KINDS),
                           label="Selecione o tipo da correspondência")

    description = forms.CharField(max_length=140, required=False, label="Descrição", widget=forms.Textarea(
        attrs={
            'class': 'form-control',
            'rows': 4, }))

    addressee = forms.ModelChoiceField(
        queryset=Resident.objects.none(), label="Destinatário", required=False
    )

    def __init__(self, *args, **kwargs):
        blocks = kwargs.pop('blocks', None)
        super().__init__(*args, **kwargs)

        if blocks:
            self.fields['block'].queryset = blocks

        self.fields['block'].choices = [('', 'Selecione o bloco do apartamento')] + list(
            self.fields['block'].choices)[1:]

    class Meta:
        model = Order
        fields = ('received_by', 'name', 'description', 'block', 'apartment', "addressee", 'image')


class UpdateOrderNotificationForm(forms.ModelForm):
    received_by = forms.CharField(max_length=50, required=False, label="Recebido por", widget=forms.TextInput(
        attrs={'class': 'form-control',
               'readonly': 'readonly'}))

    name = forms.CharField(max_length=200, required=False, label="Correspondência recebida", widget=forms.TextInput(
        attrs={'class': 'form-control',
               'readonly': 'readonly'}))

    description = forms.CharField(max_length=250, required=False, label="Descrição", widget=forms.Textarea(
        attrs={
            'class': 'form-control',
            'rows': 4,
            'readonly': 'readonly'}))

    block = forms.CharField(max_length=100, required=False, label="Bloco", widget=forms.TextInput(
        attrs={'class': 'form-control',
               'readonly': 'readonly'}))

    apt = forms.CharField(max_length=30, required=False, label="Apartamento", widget=forms.TextInput(
        attrs={'class': 'form-control',
               'readonly': 'readonly'}))
    code = forms.CharField(max_length=8, required=False, label="Código", widget=forms.TextInput(
        attrs={'class': 'form-control',
               'readonly': 'readonly'}))

    def __init__(self, *args, **kwargs):
        block = kwargs.pop('block', None)
        apartment = kwargs.pop('apartment', None)
        super().__init__(*args, **kwargs)

        if block:
            self.fields['block'].initial = block.name

        if apartment:
            self.fields['apt'].initial = str(apartment.number) + " " + apartment.complement

    class Meta:
        model = Order
        fields = ('received_by', 'name', 'description', 'block', 'apt', 'code', 'delivered_by', 'collected_by',)


class ViewOrderNotificationForm(forms.ModelForm):
    received_by = forms.CharField(max_length=50, required=False, label="Recebido por", widget=forms.TextInput(
        attrs={'class': 'form-control',
               'readonly': 'readonly'}))

    name = forms.CharField(max_length=200, required=False, label="Correspondência recebida", widget=forms.TextInput(
        attrs={'class': 'form-control',
               'readonly': 'readonly'}))

    description = forms.CharField(max_length=250, required=False, label="Descrição", widget=forms.Textarea(
        attrs={
            'class': 'form-control',
            'rows': 4,
            'readonly': 'readonly'}))

    block = forms.CharField(max_length=100, required=False, label="Bloco", widget=forms.TextInput(
        attrs={'class': 'form-control',
               'readonly': 'readonly'}))

    apt = forms.CharField(max_length=30, required=False, label="Apartamento", widget=forms.TextInput(
        attrs={'class': 'form-control',
               'readonly': 'readonly'}))
    code = forms.CharField(max_length=8, required=False, label="Código", widget=forms.TextInput(
        attrs={'class': 'form-control',
               'readonly': 'readonly'}))

    received = forms.CharField(max_length=30, required=False, label="Aviso enviado em", widget=forms.TextInput(
        attrs={'class': 'form-control',
               'readonly': 'readonly'}))

    delivered_by = forms.CharField(max_length=50, required=False, label="Entregue por", widget=forms.TextInput(
        attrs={'class': 'form-control',
               'readonly': 'readonly'}))

    collected_by = forms.CharField(max_length=50, required=False, label="Retirado por", widget=forms.TextInput(
        attrs={'class': 'form-control',
               'readonly': 'readonly'}))

    def __init__(self, *args, **kwargs):
        block = kwargs.pop('block', None)
        apartment = kwargs.pop('apartment', None)
        super().__init__(*args, **kwargs)

        if block:
            self.fields['block'].initial = block.name

        if apartment:
            self.fields['apt'].initial = str(apartment.number) + " " + apartment.complement

    class Meta:
        model = Order
        fields = ('received_by', 'name', 'description', 'block', 'apt', 'code', 'received', 'delivered_by',
                  'collected_by', 'delivered')


class ResidentMessageForm(forms.Form):
    block = forms.ModelChoiceField(queryset=Block.objects.none(), label="Bloco")
    apartment = forms.ModelChoiceField(queryset=Apartment.objects.none(), label="Apartamento", required=False)
    message = forms.CharField(label='Comunicado', widget=forms.Textarea(
        attrs={
            'class': 'form-control',
            'rows': 4,
        }))

    def __init__(self, *args, **kwargs):
        blocks = kwargs.pop('blocks', None)
        super().__init__(*args, **kwargs)

        if blocks:
            self.fields['block'].queryset = blocks

        self.fields['block'].choices = [('', 'Selecione o bloco do apartamento')] + list(
            self.fields['block'].choices)[1:]


class ResidentSentdLinkForm(forms.Form):
    block = forms.ModelChoiceField(queryset=Block.objects.none(), label="Bloco")
    apartment = forms.ModelChoiceField(queryset=Apartment.objects.none(), label="Apartamento", required=False)

    def __init__(self, *args, **kwargs):
        blocks = kwargs.pop('blocks', None)
        super().__init__(*args, **kwargs)

        if blocks:
            self.fields['block'].queryset = blocks

        self.fields['block'].choices = [('', 'Selecione o bloco do apartamento')] + list(
            self.fields['block'].choices)[1:]


class MessageFileForm(forms.Form):
    attachment = forms.FileField(label='Anexar Arquivo', required=False)


class BlockMessageForm(forms.Form):
    block = forms.ModelChoiceField(queryset=Block.objects.none(), label="Bloco")
    message = forms.CharField(label='Comunicado', widget=forms.Textarea(
        attrs={
            'class': 'form-control',
            'rows': 4,
        }))

    def __init__(self, *args, **kwargs):
        blocks = kwargs.pop('blocks', None)
        super().__init__(*args, **kwargs)

        if blocks:
            self.fields['block'].queryset = blocks

        self.fields['block'].choices = [('', 'Selecione o bloco do apartamento')] + list(
            self.fields['block'].choices)[1:]


class BlockLinkForm(forms.Form):
    block = forms.ModelChoiceField(queryset=Block.objects.none(), label="Bloco")

    def __init__(self, *args, **kwargs):
        blocks = kwargs.pop('blocks', None)
        super().__init__(*args, **kwargs)

        if blocks:
            self.fields['block'].queryset = blocks

        self.fields['block'].choices = [('', 'Selecione o bloco do apartamento')] + list(
            self.fields['block'].choices)[1:]


class EmailLinkForm(forms.Form):
    email = forms.EmailField(max_length=254, required=True, label='Email do destinatário',
                             widget=forms.TextInput(
                                 attrs={'placeholder': '*Email..',
                                        'class': 'form-control form-control-lg'}))


class MessageAllForm(forms.Form):
    message = forms.CharField(label='Comunicado', widget=forms.Textarea(
        attrs={
            'class': 'form-control',
            'rows': 4,
        }))


class ReviewForm(forms.Form):
    # service = forms.CharField(max_length=50, required=True, label="Item a ser avaliado")
    # provider = forms.CharField(max_length=50, required=False, label="Descrição")
    SEND_TO = [
        ('', 'SELECIONE'),
        ('MORADORES', 'MORADORES'),
        ('FUNCIONÁRIOS', 'FUNCIONÁRIOS'),
    ]

    send_to = forms.CharField(max_length=13, widget=forms.Select(choices=SEND_TO), label="Enviar para", required=True)

    block = forms.ModelChoiceField(queryset=Block.objects.none(), label="Enviar para Bloco", required=False)

    def __init__(self, *args, **kwargs):
        blocks = kwargs.pop('blocks', None)
        super().__init__(*args, **kwargs)

        if blocks:
            self.fields['block'].queryset = blocks
            self.fields['block'].choices = [('', 'Selecione o bloco do apartamento'), ('ALL', 'TODOS')] + list(
                self.fields['block'].choices)[1:]


class AddedReviewItemForm(forms.ModelForm):
    image = forms.ImageField(
        label="Ou selecione uma imagem",
        required=False,
        widget=forms.ClearableFileInput(attrs={"class": "form-control mt-3"}),
    )

    class Meta:
        model = ReviewItem
        fields = (
            "service",
            "is_link",
            "provider",
            "image"
        )


class ReviewAnswerForm(forms.Form):
    name = forms.CharField(max_length=50, required=True, label="Seu Nome", widget=forms.TextInput(
        attrs={
            'class': 'form-control',
        }))
    email = forms.CharField(max_length=50, required=False, label="Seu Email", widget=forms.TextInput(
        attrs={
            'class': 'form-control',
        }))

    KIND = [
        ('', 'SELECIONE'),
        ('MORADOR', 'MORADOR'),
        ('FUNCIONÁRIO', 'FUNCIONÁRIO'),
    ]

    kind = forms.CharField(max_length=13, widget=forms.Select(choices=KIND, attrs={'class': 'form-control', }),
                           label="Sou", required=True)

    block = forms.ModelChoiceField(queryset=Block.objects.none(), label="Seu Bloco",
                                   widget=forms.Select(attrs={'class': 'form-control'}), required=False)
    apartment = forms.ModelChoiceField(queryset=Apartment.objects.none(), label="Seu Apartamento",
                                       widget=forms.Select(attrs={'class': 'form-control'}), required=False)

    message = forms.CharField(max_length=500, label='Comentário', widget=forms.Textarea(
        attrs={
            'class': 'form-control',
            'rows': 8,
        }))

    rate = forms.IntegerField(label="", widget=forms.TextInput(
        attrs={'class': 'hidden', }))

    def __init__(self, *args, **kwargs):
        blocks = kwargs.pop('blocks', None)
        apartments = kwargs.pop('apartments', None)
        super().__init__(*args, **kwargs)

        if blocks:
            self.fields['block'].queryset = blocks
            self.fields['block'].choices = [('', 'Selecione o bloco do apartamento')] + list(
                self.fields['block'].choices)[1:]

        if apartments:
            self.fields['apartment'].queryset = apartments
            self.fields['apartment'].choices = [('', 'Selecione o apartamento')] + list(
                self.fields['apartment'].choices)[1:]


class ViewReviewAnswerForm(forms.Form):
    name = forms.CharField(max_length=50, required=True, label="Seu Nome", widget=forms.TextInput(
        attrs={
            'class': 'form-control',
        }))
    email = forms.CharField(max_length=50, required=False, label="Seu Email", widget=forms.TextInput(
        attrs={
            'class': 'form-control',
        }))

    address = forms.CharField(max_length=50, required=False, label="Bloco/Apartamento", widget=forms.TextInput(
        attrs={
            'class': 'form-control',
        }))

    message = forms.CharField(max_length=500, label='Comentário', widget=forms.Textarea(
        attrs={
            'class': 'form-control',
            'rows': 8,
        }))

    rate = forms.IntegerField(label="", widget=forms.TextInput(
        attrs={'class': 'hidden', }))


class SurveyAnswerForm(forms.Form):
    answer = forms.CharField(label='Opção de resposta', required=False, widget=forms.TextInput(
        attrs={'class': 'form-control my-3'}))
    is_link = forms.BooleanField(required=False, label="É um link?")
    image = forms.ImageField(label="Ou selecione uma imagem", required=False,
                             widget=forms.ClearableFileInput(attrs={'class': 'form-control mt-3'}))


class SurveyForm(forms.ModelForm):
    SEND_TO = [
        ('MORADORES', 'MORADORES'),
        ('FUNCIONÁRIOS', 'FUNCIONÁRIOS'),
        ('TODOS', 'TODOS'),
    ]

    send_to = forms.CharField(max_length=13, widget=forms.Select(choices=SEND_TO), label="Enviar para")

    class Meta:
        model = SurveyModel
        fields = ('send_to', 'question',)


class SurveyAddAnswerForm(forms.Form):
    KIND = [
        ('', 'SELECIONE'),
        ('MORADOR', 'MORADOR'),
        ('FUNCIONÁRIO', 'FUNCIONÁRIO'),
    ]

    kind = forms.CharField(max_length=13, widget=forms.Select(choices=KIND), label="Sou", required=True)

    block = forms.ModelChoiceField(queryset=Block.objects.none(), label="Seu Bloco", required=False)
    apartment = forms.ModelChoiceField(queryset=Apartment.objects.none(), label="Seu Apartamento", required=False)

    def __init__(self, *args, **kwargs):
        blocks = kwargs.pop('blocks', None)
        apartments = kwargs.pop('apartments', None)
        super().__init__(*args, **kwargs)

        if blocks:
            self.fields['block'].queryset = blocks
            self.fields['block'].choices = [('', 'Selecione o bloco do apartamento')] + list(
                self.fields['block'].choices)[1:]

        if apartments:
            self.fields['apartment'].queryset = apartments
            self.fields['apartment'].choices = [('', 'Selecione o apartamento')] + list(
                self.fields['apartment'].choices)[1:]


class SurveyAnswerModelForm(forms.ModelForm):
    name = forms.CharField(max_length=50, required=True, label="Seu Nome", widget=forms.TextInput(
        attrs={
            'class': 'form-control',
            'readonly': 'readonly'
        }))
    email = forms.CharField(max_length=50, required=False, label="Seu Email", widget=forms.TextInput(
        attrs={
            'class': 'form-control',
            'readonly': 'readonly'
        }))
    block = forms.CharField(max_length=50, required=False, label="Bloco", widget=forms.TextInput(
        attrs={
            'class': 'form-control',
            'readonly': 'readonly'
        }))
    apartment = forms.CharField(max_length=50, required=False, label="Apartamento", widget=forms.TextInput(
        attrs={
            'class': 'form-control',
            'readonly': 'readonly'
        }))

    class Meta:
        model = SurveyAnswerModel
        fields = ('name', 'email', 'block', 'apartment', 'survey', 'option',)


class ContractForm(forms.ModelForm):
    DAYS = [
        (1, '1 dia'),
        (7, '7 dias'),
        (15, '15 dias'),
        (30, '30 dias'),
        (31, '1, 7, 15 e 30 dias')
    ]

    last_maintenance = forms.DateField(label="Última manutenção", widget=forms.DateInput(attrs={'type': 'date'}))
    next_maintenance = forms.DateField(label="Próxima manutenção", widget=forms.DateInput(attrs={'type': 'date'}))
    days_to_notify = forms.ChoiceField(label="Selecione número de dias para o vencimento para notificar", choices=DAYS,
                                       widget=forms.Select(attrs={'class': 'form-control'}))

    description = forms.CharField(max_length=140, required=False, label="Descrição", widget=forms.Textarea(
        attrs={
            'class': 'form-control',
            'rows': 4, }))

    class Meta:
        model = Contract
        fields = ('item', 'description', 'image', 'last_maintenance', 'next_maintenance', 'to_email', 'days_to_notify')


class ViewContractForm(forms.ModelForm):
    item = forms.CharField(max_length=50, required=False, label="Nome do item", widget=forms.TextInput(
        attrs={'class': 'form-control',
               'readonly': 'readonly'}))

    description = forms.CharField(max_length=140, required=False, label="Descrição", widget=forms.Textarea(
        attrs={
            'class': 'form-control',
            'rows': 4,
            'readonly': 'readonly', }))

    last_maintenance = forms.CharField(max_length=30, required=False, label="Última manutenção", widget=forms.TextInput(
        attrs={'class': 'form-control',
               'readonly': 'readonly'}))

    next_maintenance = forms.CharField(max_length=30, required=False, label="Última manutenção", widget=forms.TextInput(
        attrs={'class': 'form-control',
               'readonly': 'readonly'}))

    to_email = forms.CharField(max_length=140, required=False, label="Email de quem será notificado",
                               widget=forms.TextInput(
                                   attrs={'class': 'form-control',
                                          'readonly': 'readonly'}))

    notify_day = forms.CharField(max_length=30, required=False, label="Data da notificação", widget=forms.TextInput(
        attrs={'class': 'form-control',
               'readonly': 'readonly'}))

    class Meta:
        model = Contract
        fields = ('item', 'description', 'last_maintenance', 'next_maintenance', 'to_email', 'notify_day')


class EditContractForm(forms.ModelForm):
    last_maintenance = forms.DateField(label="Última manutenção", widget=forms.DateInput(attrs={'type': 'date'}))
    next_maintenance = forms.DateField(label="Próxima manutenção", widget=forms.DateInput(attrs={'type': 'date'}))
    notify_day = forms.DateField(label="Próxima manutenção", widget=forms.DateInput(attrs={'type': 'date'}))

    description = forms.CharField(max_length=140, required=False, label="Descrição", widget=forms.Textarea(
        attrs={
            'class': 'form-control',
            'rows': 4, }))

    class Meta:
        model = Contract
        fields = ('item', 'description', 'last_maintenance', 'next_maintenance', 'to_email', 'notify_day', 'image')


class AddChecklistForm(forms.ModelForm):
    class Meta:
        model = Checklist
        fields = ('title',)


class AddTaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ('task_name',)


class AddTaskProblemForm(forms.ModelForm):
    problem_description = forms.CharField(label='Descrição do problema', widget=forms.Textarea(
        attrs={
            'class': 'form-control',
            'rows': 4,
        }))
    webimg = forms.CharField(widget=forms.HiddenInput, required=False)

    class Meta:
        model = Task
        fields = ('task_name', 'problem_description', 'reported_problem_image', 'webimg')


class ViewTaskProblemForm(forms.ModelForm):
    task_name = forms.CharField(max_length=30, required=False, label="O que foi verificado", widget=forms.TextInput(
        attrs={'class': 'form-control',
               'readonly': 'readonly'}))

    problem_description = forms.CharField(label='Descrição do problema', widget=forms.Textarea(
        attrs={
            'class': 'form-control',
            'readonly': 'readonly',
            'rows': 4,
        }))

    class Meta:
        model = Task
        fields = ('task_name', 'problem_description',)


class EditHowToForm(forms.ModelForm):
    KINDS = [
        ('Texto', 'Texto'),
        ('Link', 'Link'),
    ]

    kind = forms.CharField(max_length=13, widget=forms.Select(choices=KINDS), label="Tipo")
    name = forms.CharField(max_length=60, required=True, widget=forms.TextInput(
        attrs={'placeholder': '*Local..',
               'class': 'form-control',
               'readonly': 'readonly'}))
    value = forms.CharField(max_length=500, required=True, widget=forms.Textarea(
        attrs={'placeholder': '*Texto ou link completo da ajuda..',
               'class': 'form-control form-control-lg',
               'rows': 4, }))

    class Meta:
        model = HowTo
        fields = ('name', 'value', 'kind',)


class CheckinForm(forms.Form):
    page = forms.CharField()

    def __init__(self, *args, **kwargs):
        next_page = kwargs.pop('page', None)
        super().__init__(*args, **kwargs)

        if next_page:
            self.fields['page'] = next_page


class confirmDeleteForm(forms.Form):
    next = forms.CharField()
    previous = forms.CharField()

    def __init__(self, *args, **kwargs):
        next_page = kwargs.pop('next', None)
        previous_page = kwargs.pop('previous', None)
        super().__init__(*args, **kwargs)

        if next_page:
            self.fields['next'] = next_page
        if previous_page:
            self.fields['previous'] = previous_page


class ViewMessageForm(forms.ModelForm):
    kind = forms.CharField(max_length=15, required=False, label="Bloco", widget=forms.TextInput(
        attrs={'class': 'form-control',
               'readonly': 'readonly'}))

    block = forms.CharField(max_length=16, required=False, label="Bloco", widget=forms.TextInput(
        attrs={'class': 'form-control',
               'readonly': 'readonly'}))

    apartment = forms.CharField(max_length=16, required=False, label="Bloco", widget=forms.TextInput(
        attrs={'class': 'form-control',
               'readonly': 'readonly'}))

    message = forms.CharField(max_length=250, required=False, label="Mensagem", widget=forms.TextInput(
        attrs={'class': 'form-control',
               'readonly': 'readonly'}))

    sent = forms.CharField(max_length=30, required=False, label="Enviado em", widget=forms.TextInput(
        attrs={'class': 'form-control',
               'readonly': 'readonly'}))

    class Meta:
        model = Message
        fields = ('kind', 'block', 'apartment', 'message', 'sent',)


class AddEmployeeForm(forms.Form):
    employee_name = forms.CharField(max_length=60, required=True, label="Nome do Funcionário", widget=forms.TextInput(
        attrs={'placeholder': '*Nome do Funcionário..',
               'class': 'form-control'}))
    email = forms.EmailField(max_length=254, required=True, label="Email do funcionário", widget=forms.TextInput(
        attrs={'placeholder': '*Email que o funcionário receberá a senha',
               'class': 'form-control'}))


class GeneralReportForm(forms.Form):
    initial = forms.DateField(label="Realizadas de", widget=forms.DateInput(
        attrs={'type': 'date', 'class': "my-2"}))
    until = forms.DateField(label="Até", widget=forms.DateInput(
        attrs={'type': 'date', 'class': "my-2"}))


class ActivityReportForm(GeneralReportForm):
    # KINDS = [
    #     ('TODAS', 'TODAS'),
    #     ('ACHADOS E PERDIDOS', 'ACHADOS E PERDIDOS'),
    #     ('ACOMPANHAMENTO DE OBRA', 'ACOMPANHAMENTO DE OBRA'),
    #     ('ANTES E DEPOIS', 'ANTES E DEPOIS'),
    #     ('INFORMATIVO', 'INFORMATIVO'),
    #     ('MANUTENÇÃO', 'MANUTENÇÃO'),
    #     ('OCORRÊNCIAS', 'OCORRÊNCIAS'),
    #     ('VISTORIA', 'VISTORIA'),
    #     ('OUTRAS ATIVIDADES', 'OUTRAS ATIVIDADES'),
    # ]
    #
    # kind = forms.CharField(max_length=25, widget=forms.Select(choices=KINDS, attrs={'class': 'form-control'}), label="Tipo da Atividade")

    kind = forms.ModelChoiceField(queryset=InformativeKind.objects.none(), label="Tipo da Atividade")

    def __init__(self, *args, **kwargs):
        informative_kind = kwargs.pop('informative_kind', None)
        super().__init__(*args, **kwargs)

        if informative_kind:
            self.fields['kind'].queryset = informative_kind
            self.fields['kind'].choices = [('TODAS', 'TODAS')] + list(
                self.fields['kind'].choices)[1:]


class MessageReportForm(GeneralReportForm):
    KINDS = [
        ('TODOS', 'TODOS'),
        ('AO CONDOMÍNIO', 'AO CONDOMÍNIO'),
        ('AO BLOCO', 'AO BLOCO'),
        ('AO MORADOR', 'AO MORADOR'),
    ]

    kind = forms.CharField(max_length=25, widget=forms.Select(choices=KINDS, attrs={'class': 'form-control'}),
                           label="Enviadas")


class ChecklistReportForm(GeneralReportForm):
    KINDS = [
        ('TODAS', 'TODAS'),
        ('FORAM VERIFICADOS', 'FORAM VERIFICADOS'),
        ('ESTÃO COM PROBLEMAS', 'ESTÃOCOM PROBLEMAS'),
        ('FALTAM VERIFICAÇÃO', 'FALTAM VERIFICAÇÃO'),
    ]

    kind = forms.CharField(max_length=25, widget=forms.Select(choices=KINDS, attrs={'class': 'form-control'}),
                           label="Com situação igual a")


class AddResidentLinkForm(forms.Form):
    KINDS = [
        ('Proprietário', 'Proprietário'),
        ('Inquilino', 'Inquilino'),
        ('Procurador', 'Procurador'),
        ('Depedente', 'Dependente'),
        ('Cônjuge', 'Cônjuge'),
        ('Funcionário', 'Funcionário'),
        ('Outro', 'Outro'),
    ]

    kind = forms.CharField(max_length=13, widget=forms.Select(choices=KINDS), label="Vocé é")
    resident_name = forms.CharField(max_length=60, required=True, label="Seu nome", widget=forms.TextInput(
        attrs={'placeholder': '*Nome completo..',
               'class': 'form-control'}))
    email = forms.EmailField(max_length=254, required=True, label="Seu melhor email", widget=forms.TextInput(
        attrs={'placeholder': '*Email que receberá a senha',
               'class': 'form-control'}))
    whatsapp = forms.CharField(max_length=15, required=False, label="Seu Whatsapp", widget=forms.TextInput(
        attrs={'placeholder': 'Whatsapp..',
               'class': 'form-control'}))
    block = forms.ModelChoiceField(queryset=Block.objects.none(), label="Seu Bloco")
    apartment = forms.ModelChoiceField(queryset=Apartment.objects.none(), label="Seu Apartamento")
    webimg = forms.CharField(widget=forms.HiddenInput, required=False)

    def __init__(self, *args, **kwargs):
        blocks = kwargs.pop('blocks', None)
        apartments = kwargs.pop('apartments', None)
        super().__init__(*args, **kwargs)

        if blocks:
            self.fields['block'].queryset = blocks
            self.fields['block'].choices = [('', 'Selecione o bloco do apartamento')] + list(
                self.fields['block'].choices)[1:]

        if apartments:
            self.fields['apartment'].queryset = apartments
            self.fields['apartment'].choices = [('', 'Selecione o apartamento')] + list(
                self.fields['apartment'].choices)[1:]


class SignatureForm(forms.ModelForm):
    # definir espaçamento entre campos e cor vermelha na imagem
    name = forms.CharField(max_length=150, required=True, label="Nome Completo", widget=forms.TextInput(
        attrs={'class': 'form-control my-2', }))

    whatsapp = forms.CharField(max_length=15, required=False, label="Seu Whatsapp", widget=forms.TextInput(
        attrs={'placeholder': 'Whatsapp..',
               'class': 'form-control my-2'}))

    email = forms.EmailField(max_length=254, required=True, label="Email", widget=forms.TextInput(
        attrs={'placeholder': '*Email..',
               'class': 'form-control my-2'}))
    image = forms.ImageField()

    def __init__(self, *args, **kwargs):
        email = kwargs.pop('email', None)
        whatsapp = kwargs.pop('whatsapp', None)
        name = kwargs.pop('name', None)
        super().__init__(*args, **kwargs)

        if email:
            self.fields['email'].initial = email

        if whatsapp:
            self.fields['whatsapp'].initial = whatsapp

        if name:
            self.fields['name'].initial = name

        self.fields['image'].widget.attrs.update({'class': 'icon-minus'})

    class Meta:
        model = Signature
        fields = ('name', 'whatsapp', 'email', 'image')


class ReportLogoForm(forms.ModelForm):
    # definir espaçamento entre campos e cor vermelha na imagem
    image = forms.ImageField(label="Selecione o seu logo que será exibido no cabeçalho dos relatórios", required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['image'].widget.attrs.update({'class': 'icon-minus'})

    class Meta:
        model = ReportLogo
        fields = ('image',)


class AddVisitantForm(forms.ModelForm):
    name = forms.CharField(max_length=150, required=True, label="Nome",
                           widget=forms.TextInput(
                               attrs={'class': 'form-control'}))
    until = forms.DateTimeField(
        required=False,
        input_formats=["%Y-%m-%dT%H:%M"],
        label="Liberado até",
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local',
                                          'class': "form-control my-2"})
    )
    permanent = forms.BooleanField(required=False, label="Autorizar permanentemente")
    vehicle_plate = forms.CharField(max_length=8, required=False, label="Placa do veículo",
                                    widget=forms.TextInput(
                                        attrs={'class': 'form-control'}))
    comment = forms.CharField(max_length=250, required=False, label="Observações",
                              widget=forms.Textarea(
                                  attrs={'class': 'form-control',
                                         'rows': 4, }))
    delivery_code = forms.CharField(max_length=25, required=False, label="Código da entrega",
                                    widget=forms.TextInput(
                                        attrs={'class': 'form-control'}))

    class Meta:
        model = Visitant
        fields = ('name', 'until', 'permanent', 'vehicle_plate', 'comment', 'delivery_code', 'check_photo')

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get('permanent') and not cleaned_data.get('until'):
            self.add_error('until', 'Informe até quando a liberação é válida.')
        return cleaned_data


class AddVisitantSecurityForm(forms.Form):
    name = forms.CharField(max_length=150, label="Nome",
                           widget=forms.TextInput(
                               attrs={'class': 'form-control my-2'}))
    block = forms.ModelChoiceField(queryset=Block.objects.none(), label="Autorizado para o Bloco",
                                   widget=forms.Select(attrs={'class': 'form-control my-2'}))

    apartment = forms.ModelChoiceField(queryset=Apartment.objects.none(), label="Autorizado para o Apartamento",
                                       widget=forms.Select(attrs={'class': 'form-control my-2'}))

    until = forms.DateTimeField(required=True, input_formats=["%Y-%m-%dT%H:%M"], label="Liberado até",
                                widget=forms.DateTimeInput(attrs={'type': 'datetime-local',
                                                                  'class': "form-control my-2"}))
    comment = forms.CharField(max_length=250, required=False, label="Observações",
                              widget=forms.Textarea(
                                  attrs={'class': 'form-control',
                                         'rows': 4, }))

    document = forms.CharField(max_length=15, label="Número do documento do Visitante",
                               widget=forms.TextInput(
                                   attrs={'class': 'form-control'}))

    vehicle_model = forms.CharField(max_length=20, required=False, label="Modelo do Veículo",
                                    widget=forms.TextInput(
                                        attrs={'class': 'form-control'}))

    vehicle_plate = forms.CharField(max_length=8, required=False, label="Placa do Veículo",
                                    widget=forms.TextInput(
                                        attrs={'class': 'form-control'}))
    photo = forms.ImageField(required=False)

    webimg = forms.CharField(widget=forms.HiddenInput, required=False)

    def __init__(self, *args, **kwargs):
        blocks = kwargs.pop('blocks', None)
        apartments = kwargs.pop('apartments', None)
        super().__init__(*args, **kwargs)

        if blocks:
            self.fields['block'].queryset = blocks
            self.fields['block'].choices = [('', 'Selecione o bloco do apartamento')] + list(
                self.fields['block'].choices)[1:]

        if apartments:
            self.fields['apartment'].queryset = apartments
            self.fields['apartment'].choices = [('', 'Selecione o apartamento')] + list(
                self.fields['apartment'].choices)[1:]
        elif self.data.get('block'):
            try:
                selected_block_id = int(self.data.get('block'))
                apartments = Apartment.objects.filter(block_id=selected_block_id)
                self.fields['apartment'].queryset = apartments
                self.fields['apartment'].choices = [('', 'Selecione o apartamento')] + list(
                    self.fields['apartment'].choices)[1:]
            except (TypeError, ValueError):
                self.fields['apartment'].queryset = Apartment.objects.none()


class RegisterVisitant(forms.ModelForm):
    document = forms.CharField(max_length=15, required=True, label="Número do documento do Visitante",
                               widget=forms.TextInput(
                                   attrs={'class': 'form-control'}))

    vehicle_model = forms.CharField(max_length=20, required=False, label="Modelo do Veículo",
                                    widget=forms.TextInput(
                                        attrs={'class': 'form-control'}))

    vehicle_plate = forms.CharField(max_length=8, required=False, label="Placa do Veículo",
                                    widget=forms.TextInput(
                                        attrs={'class': 'form-control'}))
    webimg = forms.CharField(widget=forms.HiddenInput, required=False)

    def __init__(self, *args, **kwargs):
        instance = kwargs.pop('instance', None)

        super().__init__(*args, **kwargs)

        if instance:
            self.fields['document'].initial = instance.document
            self.fields['vehicle_model'].initial = instance.vehicle_model
            self.fields['vehicle_plate'].initial = instance.vehicle_plate

    class Meta:
        model = Visitant
        fields = ('document', 'vehicle_model', 'vehicle_plate', 'photo', 'security_name')


class VisitantReportForm(forms.Form):
    visits_from = forms.DateField(label="Visitas realizadas de", widget=forms.DateInput(
        attrs={'type': 'date', 'class': "my-2"}))
    visits_until = forms.DateField(label="Visitas realizadas até", widget=forms.DateInput(
        attrs={'type': 'date'}))
    CHOICES = [
        ('1', 'PDF'),
        ('2', 'Excel'),
    ]
    type = forms.ChoiceField(
        widget=forms.RadioSelect(attrs={'class': 'form-control my-3'}),
        choices=CHOICES,
        label="Tipo",
        required=True
    )

    block = forms.CharField(max_length=150, required=False, label="Bloco", widget=forms.TextInput(
        attrs={'class': 'form-control'}))


class AddProductForm(forms.ModelForm):
    description = forms.CharField(max_length=140, required=False, label="Descrição", widget=forms.Textarea(
        attrs={
            'class': 'form-control',
            'rows': 4, }))

    class Meta:
        model = Product
        fields = ('name', 'description', 'warning_quantity', 'image',)


class ViewProductForm(forms.ModelForm):
    name = forms.CharField(max_length=50, required=False, label="Nome do produto", widget=forms.TextInput(
        attrs={'class': 'form-control',
               'readonly': 'readonly'}))

    description = forms.CharField(max_length=140, required=False, label="Descrição", widget=forms.Textarea(
        attrs={
            'class': 'form-control',
            'rows': 4,
            'readonly': 'readonly'}))

    quantity = forms.IntegerField(required=False, label="Quantidade em estoque", widget=forms.TextInput(
        attrs={'class': 'form-control',
               'readonly': 'readonly'}))

    warning_quantity = forms.IntegerField(required=False, label="Quantidade mínima em estoque", widget=forms.TextInput(
        attrs={'class': 'form-control',
               'readonly': 'readonly'}))

    class Meta:
        model = Product
        fields = ('name', 'description', 'quantity', 'warning_quantity',)


class StorageEntryForm(forms.ModelForm):
    class Meta:
        model = StorageEntry
        fields = ('product', 'quantity', 'price',)


class StorageWithdrawForm(forms.ModelForm):
    class Meta:
        model = StorageEntry
        fields = ('product', 'quantity',)


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):

        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result


class SendBillsForm(forms.Form):
    files = MultipleFileField(label="Arquivos")


class AddTimelineForm(forms.ModelForm):
    start_date = forms.DateField(label="Data de ínicio", widget=forms.DateInput(attrs={'type': 'date',
                                                                                       'class': "my-2"}))
    end_date = forms.DateField(label="Data final", widget=forms.DateInput(attrs={'type': 'date',
                                                                                 'class': "my-2"}))
    description = forms.CharField(max_length=140, required=False, label="Descrição", widget=forms.Textarea(
        attrs={
            'class': 'form-control',
            'rows': 4, }))

    class Meta:
        model = Timeline
        fields = ('title', 'description', 'start_date', 'end_date',)


class AddTimelinePhaseForm(forms.ModelForm):
    end_date = forms.DateField(label="Data de entrega", widget=forms.DateInput(attrs={'type': 'date',
                                                                                      'class': "my-2"}))
    description = forms.CharField(max_length=140, required=False, label="Descrição", widget=forms.Textarea(
        attrs={
            'class': 'form-control',
            'rows': 4, }))

    class Meta:
        model = TimelinePhase
        fields = ('title', 'description', 'end_date', 'image', 'link')


class AddActivityForm(forms.Form):
    title = forms.CharField(max_length=200, required=True, label="Nome da função",
                            widget=forms.TextInput(
                                attrs={'class': 'form-control'}))
    description = forms.CharField(max_length=140, required=False, label="Descrição", widget=forms.Textarea(
        attrs={
            'class': 'form-control',
            'rows': 4, }))

    images = MultipleFileField(label="Imagens", required=False,
                               widget=MultipleFileInput(attrs={'class': 'form-control my-3'}))
    files = MultipleFileField(label="Arquivos", required=False,
                              widget=MultipleFileInput(attrs={'class': 'form-control my-3'}))
    link = forms.CharField(max_length=500, required=False, label="Link pro vídeo", widget=forms.TextInput(
        attrs={'class': 'form-control'}))


class ResidentActivityForm(forms.ModelForm):
    KINDS = [
        ('OCORRÊNCIA', 'OCORRÊNCIA'),
        ('PROBLEMA', 'PROBLEMA'),
        ('MANUTENÇÃO', 'MANUTENÇÃO'),
        ('SOLICITAÇÃO', 'SOLICITAÇÃO'),
        ('RECLAMAÇÃO', 'RECLAMAÇÃO'),
        ('OUTRO', 'OUTRO'),
    ]

    kind = forms.CharField(max_length=13, widget=forms.Select(choices=KINDS),
                           label="Selecione o tipo da atividade")

    title = forms.CharField(max_length=60, required=True, label="Título",
                            widget=forms.TextInput(
                                attrs={'class': 'form-control'}))
    description = forms.CharField(max_length=250, required=False, label="Descrição", widget=forms.Textarea(
        attrs={
            'class': 'form-control',
            'rows': 4, }))

    class Meta:
        model = ResidentActivity
        fields = ('kind', 'title', 'description', 'link', 'image')


class ViewResidentActivityForm(forms.ModelForm):
    kind = forms.CharField(max_length=13, widget=forms.TextInput(
        attrs={'class': 'form-control', 'readonly': 'readonly'}),
                           label="Tipo da atividade")
    protocol = forms.CharField(max_length=13, widget=forms.TextInput(
        attrs={'class': 'form-control', 'readonly': 'readonly'}),
                               label="Protocolo")

    title = forms.CharField(max_length=60, required=True, label="Título",
                            widget=forms.TextInput(
                                attrs={'class': 'form-control', 'readonly': 'readonly'}))
    description = forms.CharField(max_length=250, required=False, label="Descrição", widget=forms.Textarea(
        attrs={
            'class': 'form-control',
            'readonly': 'readonly',
            'rows': 4, }))
    resident = forms.CharField(max_length=150, widget=forms.TextInput(
        attrs={'class': 'form-control', 'readonly': 'readonly'}),
                               label="Aberta por")
    responsible = forms.CharField(max_length=150, widget=forms.TextInput(
        attrs={'class': 'form-control', 'readonly': 'readonly'}),
                                  label="Responsável")
    status = forms.CharField(max_length=13, widget=forms.TextInput(
        attrs={'class': 'form-control', 'readonly': 'readonly'}),
                             label="Situação")
    created_date = forms.CharField(max_length=20, widget=forms.TextInput(
        attrs={'class': 'form-control', 'readonly': 'readonly'}),
                                   label="Criada em")

    def __init__(self, *args, **kwargs):
        instance = kwargs.pop('instance', None)
        super().__init__(*args, **kwargs)

        if instance:
            self.fields['kind'].initial = instance.kind
            self.fields['protocol'].initial = instance.protocol
            self.fields['title'].initial = instance.title
            self.fields['description'].initial = instance.description
            self.fields['resident'].initial = instance.resident
            self.fields['responsible'].initial = instance.responsible or ""
            self.fields['status'].initial = instance.status
            self.fields['link'].initial = instance.link
            self.fields['created_date'].initial = instance.created.astimezone(FIXED_TZ).strftime('%d/%m/%Y - %H:%M:%S')

    class Meta:
        model = ResidentActivity
        fields = ('kind', 'protocol', 'title', 'description', 'resident', 'responsible', 'status', 'created_date',
                  'link')


class ResidentActivityAddAnswerForm(forms.ModelForm):
    message = forms.CharField(max_length=250, required=False, label="Descrição", widget=forms.Textarea(
        attrs={
            'class': 'form-control',
            'rows': 4, }))

    class Meta:
        model = ResidentActivityAnswer
        fields = ('message', 'link', 'image')


class ResidentActivityAnswerForm(forms.ModelForm):
    auteur = forms.CharField(max_length=60, required=True, label="Respondido por", widget=forms.TextInput(
        attrs={'class': 'form-control',
               'readonly': 'readonly'}))
    message = forms.CharField(max_length=250, required=False, label="Descrição", widget=forms.Textarea(
        attrs={
            'class': 'form-control',
            'readonly': 'readonly',
            'rows': 4, }))

    answer_date = forms.CharField(max_length=60, required=True, label="Respondido em", widget=forms.TextInput(
        attrs={'class': 'form-control',
               'readonly': 'readonly'}))

    def __init__(self, *args, **kwargs):
        instance = kwargs.pop('instance', None)
        super().__init__(*args, **kwargs)

        if instance:
            self.fields['auteur'].initial = instance.auteur
            self.fields['message'].initial = instance.message
            self.fields['link'].initial = instance.link
            self.fields['answer_date'].initial = instance.created.astimezone(FIXED_TZ).strftime('%d/%m/%Y - %H:%M:%S')

    class Meta:
        model = ResidentActivityAnswer
        fields = ('auteur', 'message', 'answer_date', 'link', 'image')


class ViewResidentActivityAnswerForm(forms.ModelForm):
    auteur = forms.CharField(max_length=60, required=True, label="Respondido por", widget=forms.TextInput(
        attrs={'class': 'form-control',
               'readonly': 'readonly'}))
    message = forms.CharField(max_length=250, required=False, label="Descrição", widget=forms.Textarea(
        attrs={
            'class': 'form-control',
            'readonly': 'readonly',
            'rows': 4, }))

    answer_date = forms.CharField(max_length=60, required=True, label="Respondido em", widget=forms.TextInput(
        attrs={'class': 'form-control',
               'readonly': 'readonly'}))

    def __init__(self, *args, **kwargs):
        instance = kwargs.pop('instance', None)
        super().__init__(*args, **kwargs)

        if instance:
            self.fields['auteur'].initial = instance.auteur
            self.fields['message'].initial = instance.message
            self.fields['link'].initial = instance.link
            self.fields['answer_date'].initial = instance.created.astimezone(FIXED_TZ).strftime('%d/%m/%Y - %H:%M:%S')

    class Meta:
        model = ResidentActivityAnswer
        fields = ('auteur', 'message', 'answer_date', 'link')


class AdministratorUserForm(forms.Form):
    admin_name = forms.CharField(max_length=60, required=True, label="Nome da Administradora", widget=forms.TextInput(
        attrs={'placeholder': '*Nome da Administradora..',
               'class': 'form-control'}))
    email = forms.EmailField(max_length=254, required=True, label="Email para receber a senha", widget=forms.TextInput(
        attrs={'placeholder': '*Email..',
               'class': 'form-control'}))
    cnpj = forms.CharField(max_length=18, required=False, label="CNPJ", widget=forms.TextInput(
        attrs={'placeholder': 'CNPJ..',
               'class': 'form-control cnpj'}))
    address = forms.CharField(max_length=200, required=False, label="Endereço", widget=forms.TextInput(
        attrs={'placeholder': 'Endereço..',
               'class': 'form-control'}))

    whatsapp = forms.CharField(max_length=15, required=False, label="Whatsapp", widget=forms.TextInput(
        attrs={'placeholder': 'Whatsapp..',
               'class': 'form-control'}))

    site = forms.CharField(max_length=60, required=False, label="Site", widget=forms.TextInput(
        attrs={'placeholder': 'Site..',
               'class': 'form-control'}))

    class Meta:
        model = CondominiumProfile
        fields = ("admin_name", "email", "address", "cnpj", "whatsapp", "site")


class AddPlaceForm(forms.ModelForm):
    description = forms.CharField(max_length=250, required=False, label="Descrição", widget=forms.Textarea(
        attrs={
            'class': 'form-control',
            'rows': 4, }))

    def __init__(self, *args, **kwargs):
        condominium = kwargs.pop('condominium', None)
        super(AddPlaceForm, self).__init__(*args, **kwargs)

        if condominium:
            self.fields['blocked_areas'].queryset = Place.objects.filter(condominium=condominium)

    class Meta:
        model = Place
        fields = ("name", "description", "capacity", "price", "image", "rules", "inspection", "minimum_days_to_reserve",
                  "maximum_days_to_booking", "minimum_days_to_cancel", "internal_regime", "acceptance_terms",
                  "maximum_unity_reservation_per_day", "maximum_resident_reservation_per_day",
                  "maximum_unity_reservation_per_week", "maximum_resident_reservation_per_week",
                  "maximum_unity_reservation_per_month", "maximum_resident_reservation_per_month",
                  "maximum_unity_reservation_per_year", "maximum_resident_reservation_per_year",
                  "minimum_days_to_reserve", "blocked_areas", "image")


class CondominiumReservationLimitsForm(forms.ModelForm):
    class Meta:
        model = CondominiumReservationLimits
        fields = ("maximum_unity_reservation_per_day", "maximum_resident_reservation_per_day",
                  "maximum_unity_reservation_per_week", "maximum_resident_reservation_per_week",
                  "maximum_unity_reservation_per_month", "maximum_resident_reservation_per_month",
                  "maximum_unity_reservation_per_year", "maximum_resident_reservation_per_year")


class AddReservationTime(forms.ModelForm):
    INTERVAL = [
        ("30", "30 mim"),
        ("45", "45 mim"),
        ("1", "1 hora"),
        ("90", "1h e 30 mim"),
        ("2", "2 horas"),
        ("3", "3 horas"),
        ("4", "4 horas"),
        ("6", "6 horas"),
        ("8", "8 horas"),
        ("10", "10 horas"),
        ("12", "12 horas"),
        ("24", "O dia todo"),
    ]

    init_time = forms.TimeField(label="Horário de início da reserva", widget=forms.TimeInput(attrs={'type':
                                                                                                        'time',
                                                                                                    'class': "form-control my-3"}))

    end_time = forms.TimeField(label="Horário de término da reserva", widget=forms.TimeInput(attrs={'type':
                                                                                                        'time',
                                                                                                    'class': "form-control my-3"}))

    interval = forms.ChoiceField(choices=INTERVAL, widget=forms.Select(attrs={'class': 'form-control my-3'}),
                                 label="Duração da reserva")

    class Meta:
        model = ReservationTime
        fields = ("init_time", "end_time", "interval",)
        widgets = {
            'repeat': forms.CheckboxInput(attrs={'class': 'my-3'}),
            'selected_days': forms.CheckboxSelectMultiple(attrs={'class': 'my-3'}),
            'place': forms.Select(attrs={'class': 'my-3'}),
        }


class BlockedDateForm(forms.Form):
    blocked_day = forms.DateField(label="Bloquear dia:", widget=forms.DateInput(attrs={'type': 'date'}))
    init_time = forms.TimeField(required=False, label="Bloqueado de", widget=forms.TimeInput(attrs={'type':
                                                                                                        'time',
                                                                                                    'class': "my-3"}))

    end_time = forms.TimeField(required=False, label="Até", widget=forms.TimeInput(attrs={'type':
                                                                                              'time',
                                                                                          'class': "my-3"}))


class BlockedDateModelForm(forms.ModelForm):
    blocked_day = forms.DateField(label="Bloquear dia:", widget=forms.DateInput(attrs={'type': 'date:d/m/Y'}))
    init_time = forms.TimeField(required=False, label="Bloqueado de", widget=forms.TimeInput(attrs={'type':
                                                                                                        'time',
                                                                                                    'class': "my-3"}))

    end_time = forms.TimeField(required=False, label="Até", widget=forms.TimeInput(attrs={'type':
                                                                                              'time',
                                                                                          'class': "my-3"}))

    class Meta:
        model = BlockedDay
        fields = ("blocked_day", "init_time", "end_time",)


class CustomDateInput(forms.DateInput):
    def __init__(self, attrs=None, day_status=None):
        super().__init__(attrs=attrs)
        self.day_status = day_status


class DatePickerWidget(forms.TextInput):
    class Media:
        css = {
            'all': ('https://code.jquery.com/ui/1.12.1/themes/base/jquery-ui.css',)
        }
        js = ('https://code.jquery.com/jquery-3.6.4.min.js', 'https://code.jquery.com/ui/1.12.1/jquery-ui.js')

    def __init__(self, attrs=None):
        attrs = {'class': 'datepicker'}  # Add 'datepicker' class for initialization
        super().__init__(attrs=attrs)


class BookingForm(forms.Form):
    date = forms.DateField(label="Calendário para reserva", widget=DatePickerWidget())
    #     attrs={'type': 'date', 'class': "form-control datetimepicker-input", 'data-target': '#datetimepicker1'}, format="%Y-%m-%d"))
    # date = forms.DateField(label="Data para reserva", widget=forms.DateInput(
    #     attrs={'type': 'date', 'class': "form-control datetimepicker-input", 'data-target': '#datetimepicker1'}, format="%Y-%m-%d"))
    # all_day = forms.BooleanField(required=False, label="Bloquear dia inteiro?")


class ViewBookingForm(forms.ModelForm):
    link = forms.CharField(max_length=500, required=False, label="Link para cobrança", widget=forms.TextInput(
        attrs={'placeholder': 'Link..',
               'class': 'form-control my-2'}))

    class Meta:
        model = Reservation
        fields = ("link", "bill")


class PayBookingForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ("payment",)


class FolderForm(forms.ModelForm):
    class Meta:
        model = Folder
        fields = ("name",)


class LocalFileForm(forms.ModelForm):
    class Meta:
        model = LocalFile
        fields = ("file",)


class AddPedestrianForm(forms.ModelForm):
    name = forms.CharField(max_length=60, required=True, label="Nome",
                           widget=forms.TextInput(attrs={'class': 'form-control my-3'}))
    document = forms.CharField(max_length=20, required=True, label="Documento",
                               widget=forms.TextInput(attrs={'class': 'form-control my-3'}))
    document_file = forms.FileField(widget=forms.ClearableFileInput(attrs={'class': 'form-control my-3'}), label="Anexar documento")
    block = forms.ModelChoiceField(queryset=Block.objects.none(), label="Bloco", required=True,
                                   widget=forms.Select(attrs={'class': 'form-control my-3'}))
    apartment = forms.ModelChoiceField(queryset=Apartment.objects.none(), label="Apartamento", required=True,
                                       widget=forms.Select(attrs={'class': 'form-control my-3'}))
    authorized_by = forms.CharField(max_length=50, required=True, label="Autorizado por",
                                    widget=forms.TextInput(attrs={'class': 'form-control my-3'}))
    obs = forms.CharField(max_length=200, required=True, label="Observação",
                          widget=forms.Textarea(
                              attrs={
                                  'class': 'form-control my-3',
                                  'rows': 4,
                              }))

    webimg = forms.CharField(widget=forms.HiddenInput, required=False)

    def __init__(self, *args, **kwargs):
        blocks = kwargs.pop('blocks', None)
        super().__init__(*args, **kwargs)

        if blocks:
            self.fields['block'].queryset = blocks

        block_id = self.data.get('block') or self.initial.get('block')
        if block_id:
            try:
                self.fields['apartment'].queryset = Apartment.objects.filter(block_id=int(block_id)).order_by('number')
            except (TypeError, ValueError):
                self.fields['apartment'].queryset = Apartment.objects.none()

        self.fields['block'].choices = [('', 'Selecione o bloco do apartamento')] + list(
            self.fields['block'].choices)[1:]
        self.fields['apartment'].choices = [('', 'Selecione o apartamento')] + list(
            self.fields['apartment'].choices)[1:]

    class Meta:
        model = Pedestrian
        fields = ("name", "document", "document_file", "authorized_by", "obs", "webimg")


class ViewPedestrianForm(forms.ModelForm):
    protocol = forms.CharField(max_length=5, required=False, label="Protocolo", widget=forms.TextInput(
        attrs={'class': 'form-control my-3',
               'readonly': 'readonly'}))

    name = forms.CharField(max_length=60, required=False, label="Nome", widget=forms.TextInput(
        attrs={'class': 'form-control my-3',
               'readonly': 'readonly'}))

    document = forms.CharField(max_length=20, required=False, label="Documento", widget=forms.TextInput(
        attrs={'class': 'form-control my-3',
               'readonly': 'readonly'}))

    obs = forms.CharField(max_length=200, required=False, label="Observações", widget=forms.Textarea(
        attrs={
            'class': 'form-control my-3',
            'rows': 4,
            'readonly': 'readonly'}))

    destination = forms.CharField(max_length=50, required=False, label="Vai para onde", widget=forms.TextInput(
        attrs={'class': 'form-control my-3',
               'readonly': 'readonly'}))

    authorized_by = forms.CharField(max_length=50, required=False, label="Autorizado por", widget=forms.TextInput(
        attrs={'class': 'form-control my-3',
               'readonly': 'readonly'}))


    class Meta:
        model = Pedestrian
        fields = ("protocol", "name", "document", "destination", "authorized_by", "obs")


class AddVehicleForm(forms.ModelForm):
    name = forms.CharField(max_length=60, required=True, label="Nome",
                           widget=forms.TextInput(attrs={'class': 'form-control my-3'}))
    document = forms.CharField(max_length=20, required=True, label="Documento",
                               widget=forms.TextInput(attrs={'class': 'form-control my-3'}))
    document_file = forms.FileField(widget=forms.ClearableFileInput(attrs={'class': 'form-control my-3'}), label="Anexar documento")
    block = forms.ModelChoiceField(queryset=Block.objects.none(), label="Bloco", required=True,
                                   widget=forms.Select(attrs={'class': 'form-control my-3'}))
    apartment = forms.ModelChoiceField(queryset=Apartment.objects.none(), label="Apartamento", required=True,
                                       widget=forms.Select(attrs={'class': 'form-control my-3'}))
    authorized_by = forms.CharField(max_length=50, required=True, label="Autorizado por",
                                    widget=forms.TextInput(attrs={'class': 'form-control my-3'}))
    obs = forms.CharField(max_length=200, required=True, label="Observação",
                          widget=forms.Textarea(
                              attrs={
                                  'class': 'form-control my-3',
                                  'rows': 4,
                              }))

    vehicle = forms.CharField(max_length=20, required=False, label="Veículo",
                                    widget=forms.TextInput(
                                        attrs={'class': 'form-control my-3'}))

    vehicle_plate = forms.CharField(max_length=8, required=False, label="Placa",
                                    widget=forms.TextInput(
                                        attrs={'class': 'form-control my-3'}))

    webimg = forms.CharField(widget=forms.HiddenInput, required=False)

    def __init__(self, *args, **kwargs):
        blocks = kwargs.pop('blocks', None)
        super().__init__(*args, **kwargs)

        if blocks:
            self.fields['block'].queryset = blocks

        block_id = self.data.get('block') or self.initial.get('block')
        if block_id:
            try:
                self.fields['apartment'].queryset = Apartment.objects.filter(block_id=int(block_id)).order_by('number')
            except (TypeError, ValueError):
                self.fields['apartment'].queryset = Apartment.objects.none()

        self.fields['block'].choices = [('', 'Selecione o bloco do apartamento')] + list(
            self.fields['block'].choices)[1:]
        self.fields['apartment'].choices = [('', 'Selecione o apartamento')] + list(
            self.fields['apartment'].choices)[1:]

    class Meta:
        model = Vehicle
        fields = ("name", "document", "document_file", "vehicle", "vehicle_plate", "authorized_by", "obs", "webimg")


class ViewVehicleForm(forms.ModelForm):
    protocol = forms.CharField(max_length=5, required=False, label="Protocolo", widget=forms.TextInput(
        attrs={'class': 'form-control my-3',
               'readonly': 'readonly'}))

    name = forms.CharField(max_length=60, required=False, label="Nome", widget=forms.TextInput(
        attrs={'class': 'form-control my-3',
               'readonly': 'readonly'}))

    document = forms.CharField(max_length=20, required=False, label="Documento", widget=forms.TextInput(
        attrs={'class': 'form-control my-3',
               'readonly': 'readonly'}))

    obs = forms.CharField(max_length=200, required=False, label="Observações", widget=forms.Textarea(
        attrs={
            'class': 'form-control my-3',
            'rows': 4,
            'readonly': 'readonly'}))

    vehicle = forms.CharField(max_length=20, required=False, label="Veículo", widget=forms.TextInput(
        attrs={'class': 'form-control my-3',
               'readonly': 'readonly'}))

    vehicle_plate = forms.CharField(max_length=8, required=False, label="Veículo", widget=forms.TextInput(
        attrs={'class': 'form-control my-3',
               'readonly': 'readonly'}))

    destination = forms.CharField(max_length=50, required=False, label="Vai para onde", widget=forms.TextInput(
        attrs={'class': 'form-control my-3',
               'readonly': 'readonly'}))

    authorized_by = forms.CharField(max_length=50, required=False, label="Autorizado por", widget=forms.TextInput(
        attrs={'class': 'form-control my-3',
               'readonly': 'readonly'}))

    class Meta:
        model = Vehicle
        fields = ("protocol", "name", "document", "vehicle", "vehicle_plate", "destination", "authorized_by", "obs")


class ConfigureMessagesForm(forms.ModelForm):
    class Meta:
        model = MessagesInformation
        fields = ("messages_limit", "price")


class MessageBillForm(forms.ModelForm):
    class Meta:
        model = MessagesPayment
        fields = ("bill", "payment")


class CondoMaintenanceActivityForm(forms.ModelForm):


    title = forms.CharField(
        max_length=60,
        required=True,
        label="Título",
        widget=forms.TextInput(attrs={"class": "form-control my-3"}),
    )
    description = forms.CharField(
        max_length=250,
        required=False,
        label="Descrição",
        widget=forms.Textarea(
            attrs={
                "class": "form-control my-3",
                "rows": 4,
            }
        ),
    )

    worker_responsible = forms.ModelChoiceField(
        queryset=CondominiumProfile.objects.none(),
        widget=forms.Select(attrs={"class": "form-control my-3"}),
        label="Funcionário Responsável",
        required=False
    )

    resident_responsible = forms.ModelChoiceField(
        queryset=CondominiumProfile.objects.none(),
        widget=forms.Select(attrs={"class": "form-control my-3"}),
        label="Morador Responsável",
        required=False
    )

    def __init__(self, *args, **kwargs):
        workers = kwargs.pop("workers", None)
        residents = kwargs.pop("residents", None)
        super().__init__(*args, **kwargs)

        if workers:
            self.fields["worker_responsible"].queryset = workers
            self.fields["worker_responsible"].choices = [("", "Selecione o Funcionário")] + list(
                self.fields["worker_responsible"].choices
            )[1:]

        if residents:
            self.fields["resident_responsible"].queryset = residents
            self.fields["resident_responsible"].choices = [("", "Selecione o Morador")] + list(
                self.fields["resident_responsible"].choices
            )[1:]

    class Meta:
        model = ResidentActivity
        fields = (
            "title",
            "description",
            "worker_responsible",
            "resident_responsible",
        )


class AddResidentActivityImageForm(forms.ModelForm):

    class Meta:
        model = ResidentActivityImage
        fields = (
            "image",
        )


class AddResidentActivityFileForm(forms.ModelForm):

    class Meta:
        model = ResidentActivityFile
        fields = (
            "file",
        )
