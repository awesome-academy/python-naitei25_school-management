from django import forms
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

# Import constants
from utils.constant import (
    ADMIN_USERNAME_MAX_LENGTH,
    ADMIN_USERNAME_MIN_LENGTH,
    ADMIN_PASSWORD_MIN_LENGTH,
    FORM_CONTROL_CLASS,
    USERNAME_FIELD_ID,
    PASSWORD_FIELD_ID,
    REQUIRED_ATTRIBUTE,
    ADMIN_USERNAME_MIN_LENGTH_ERROR,
    ADMIN_PASSWORD_MIN_LENGTH_ERROR,
    ADMIN_INVALID_CREDENTIALS_ERROR,
    ADMIN_INACTIVE_ACCOUNT_ERROR,
    ADMIN_NO_PERMISSION_ERROR,
    USERNAME_PLACEHOLDER,
    PASSWORD_PLACEHOLDER,
    USERNAME_LABEL,
    PASSWORD_LABEL,
    # Form field constants
    STUDENT_USN_MAX_LENGTH, USER_NAME_MAX_LENGTH, USER_SEX_MAX_LENGTH,
    USER_ADDRESS_MAX_LENGTH, USER_PHONE_MAX_LENGTH, TEACHER_ID_MAX_LENGTH,
    SEX_CHOICES, DEFAULT_SEX,
)

# Import models
from students.models import Student
from teachers.models import Teacher
from admins.models import User, Dept, Class


class AdminLoginForm(forms.Form):
    """
    Custom admin login form with data validation and cleaning
    """
    username = forms.CharField(
        max_length=ADMIN_USERNAME_MAX_LENGTH,
        widget=forms.TextInput(attrs={
            'class': FORM_CONTROL_CLASS,
            'id': USERNAME_FIELD_ID,
            'placeholder': _(USERNAME_PLACEHOLDER),
            'required': REQUIRED_ATTRIBUTE
        }),
        label=_(USERNAME_LABEL)
    )

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': FORM_CONTROL_CLASS,
            'id': PASSWORD_FIELD_ID,
            'placeholder': _(PASSWORD_PLACEHOLDER),
            'required': REQUIRED_ATTRIBUTE
        }),
        label=_(PASSWORD_LABEL)
    )

    def __init__(self, request=None, *args, **kwargs):
        """
        Initialize form with request object for authentication
        """
        self.request = request
        self.user_cache = None
        super().__init__(*args, **kwargs)

    def clean_username(self):
        """
        Clean and validate username field
        """
        username = self.cleaned_data.get('username')
        if username:
            username = username.strip().lower()
            if len(username) < ADMIN_USERNAME_MIN_LENGTH:
                raise ValidationError(
                    _(ADMIN_USERNAME_MIN_LENGTH_ERROR.format(ADMIN_USERNAME_MIN_LENGTH)))
        return username

    def clean_password(self):
        """
        Clean and validate password field
        """
        password = self.cleaned_data.get('password')
        if password:
            if len(password) < ADMIN_PASSWORD_MIN_LENGTH:
                raise ValidationError(
                    _(ADMIN_PASSWORD_MIN_LENGTH_ERROR.format(ADMIN_PASSWORD_MIN_LENGTH)))
        return password

    def clean(self):
        """
        Validate the entire form and authenticate user
        """
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')

        if username and password:
            # Authenticate user
            self.user_cache = authenticate(
                self.request,
                username=username,
                password=password
            )

            if self.user_cache is None:
                raise ValidationError(_(ADMIN_INVALID_CREDENTIALS_ERROR))

            if not self.user_cache.is_active:
                raise ValidationError(_(ADMIN_INACTIVE_ACCOUNT_ERROR))

            if not self.user_cache.is_superuser:
                raise ValidationError(
                    _(ADMIN_NO_PERMISSION_ERROR))

        return cleaned_data

    def get_user(self):
        """
        Return authenticated user
        """
        return self.user_cache


class AddStudentForm(forms.ModelForm):
    """
    Form for adding new students
    """
    # User account fields
    username = forms.CharField(
        max_length=ADMIN_USERNAME_MAX_LENGTH,
        widget=forms.TextInput(attrs={
            'class': FORM_CONTROL_CLASS,
            'placeholder': _('Enter username'),
            'required': True
        }),
        label=_('Username')
    )

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': FORM_CONTROL_CLASS,
            'placeholder': _('Enter email address'),
            'required': True
        }),
        label=_('Email')
    )

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': FORM_CONTROL_CLASS,
            'placeholder': _('Enter password'),
            'required': True
        }),
        label=_('Password'),
        min_length=ADMIN_PASSWORD_MIN_LENGTH
    )

    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': FORM_CONTROL_CLASS,
            'placeholder': _('Confirm password'),
            'required': True
        }),
        label=_('Confirm Password')
    )

    # Student profile fields
    USN = forms.CharField(
        max_length=STUDENT_USN_MAX_LENGTH,
        widget=forms.TextInput(attrs={
            'class': FORM_CONTROL_CLASS,
            'placeholder': _('Enter USN'),
            'required': True
        }),
        label=_('USN')
    )

    name = forms.CharField(
        max_length=USER_NAME_MAX_LENGTH,
        widget=forms.TextInput(attrs={
            'class': FORM_CONTROL_CLASS,
            'placeholder': _('Enter full name'),
            'required': True
        }),
        label=_('Full Name')
    )

    sex = forms.ChoiceField(
        choices=SEX_CHOICES,
        widget=forms.Select(attrs={
            'class': FORM_CONTROL_CLASS,
            'required': True
        }),
        label=_('Gender'),
        initial=DEFAULT_SEX
    )

    DOB = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': FORM_CONTROL_CLASS,
            'type': 'date',
            'required': True
        }),
        label=_('Date of Birth')
    )

    address = forms.CharField(
        max_length=USER_ADDRESS_MAX_LENGTH,
        widget=forms.Textarea(attrs={
            'class': FORM_CONTROL_CLASS,
            'placeholder': _('Enter address'),
            'rows': 3
        }),
        label=_('Address'),
        required=False
    )

    phone = forms.CharField(
        max_length=USER_PHONE_MAX_LENGTH,
        widget=forms.TextInput(attrs={
            'class': FORM_CONTROL_CLASS,
            'placeholder': _('Enter phone number')
        }),
        label=_('Phone Number'),
        required=False
    )

    class_id = forms.ModelChoiceField(
        queryset=Class.objects.all(),
        widget=forms.Select(attrs={
            'class': FORM_CONTROL_CLASS,
            'required': True
        }),
        label=_('Class'),
        empty_label=_('Select a class')
    )

    class Meta:
        model = Student
        fields = ['USN', 'name', 'sex', 'DOB', 'address', 'phone', 'class_id']

    def clean_password_confirm(self):
        password = self.cleaned_data.get('password')
        password_confirm = self.cleaned_data.get('password_confirm')

        if password and password_confirm and password != password_confirm:
            raise ValidationError(_('Passwords do not match'))
        return password_confirm

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError(_('Username already exists'))
        return username

    def clean_USN(self):
        usn = self.cleaned_data.get('USN')
        if Student.objects.filter(USN=usn).exists():
            raise ValidationError(_('USN already exists'))
        return usn

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError(_('Email already exists'))
        return email


class AddTeacherForm(forms.ModelForm):
    """
    Form for adding new teachers
    """
    # User account fields
    username = forms.CharField(
        max_length=ADMIN_USERNAME_MAX_LENGTH,
        widget=forms.TextInput(attrs={
            'class': FORM_CONTROL_CLASS,
            'placeholder': _('Enter username'),
            'required': True
        }),
        label=_('Username')
    )

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': FORM_CONTROL_CLASS,
            'placeholder': _('Enter email address'),
            'required': True
        }),
        label=_('Email')
    )

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': FORM_CONTROL_CLASS,
            'placeholder': _('Enter password'),
            'required': True
        }),
        label=_('Password'),
        min_length=ADMIN_PASSWORD_MIN_LENGTH
    )

    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': FORM_CONTROL_CLASS,
            'placeholder': _('Confirm password'),
            'required': True
        }),
        label=_('Confirm Password')
    )

    # Teacher profile fields
    id = forms.CharField(
        max_length=TEACHER_ID_MAX_LENGTH,
        widget=forms.TextInput(attrs={
            'class': FORM_CONTROL_CLASS,
            'placeholder': _('Enter teacher ID'),
            'required': True
        }),
        label=_('Teacher ID')
    )

    name = forms.CharField(
        max_length=USER_NAME_MAX_LENGTH,
        widget=forms.TextInput(attrs={
            'class': FORM_CONTROL_CLASS,
            'placeholder': _('Enter full name'),
            'required': True
        }),
        label=_('Full Name')
    )

    sex = forms.ChoiceField(
        choices=SEX_CHOICES,
        widget=forms.Select(attrs={
            'class': FORM_CONTROL_CLASS,
            'required': True
        }),
        label=_('Gender'),
        initial=DEFAULT_SEX
    )

    DOB = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': FORM_CONTROL_CLASS,
            'type': 'date',
            'required': True
        }),
        label=_('Date of Birth')
    )

    address = forms.CharField(
        max_length=USER_ADDRESS_MAX_LENGTH,
        widget=forms.Textarea(attrs={
            'class': FORM_CONTROL_CLASS,
            'placeholder': _('Enter address'),
            'rows': 3
        }),
        label=_('Address'),
        required=False
    )

    phone = forms.CharField(
        max_length=USER_PHONE_MAX_LENGTH,
        widget=forms.TextInput(attrs={
            'class': FORM_CONTROL_CLASS,
            'placeholder': _('Enter phone number')
        }),
        label=_('Phone Number'),
        required=False
    )

    dept = forms.ModelChoiceField(
        queryset=Dept.objects.all(),
        widget=forms.Select(attrs={
            'class': FORM_CONTROL_CLASS,
            'required': True
        }),
        label=_('Department'),
        empty_label=_('Select a department')
    )

    class Meta:
        model = Teacher
        fields = ['id', 'name', 'sex', 'DOB', 'address', 'phone', 'dept']

    def clean_password_confirm(self):
        password = self.cleaned_data.get('password')
        password_confirm = self.cleaned_data.get('password_confirm')

        if password and password_confirm and password != password_confirm:
            raise ValidationError(_('Passwords do not match'))
        return password_confirm

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError(_('Username already exists'))
        return username

    def clean_id(self):
        teacher_id = self.cleaned_data.get('id')
        if Teacher.objects.filter(id=teacher_id).exists():
            raise ValidationError(_('Teacher ID already exists'))
        return teacher_id

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError(_('Email already exists'))
        return email
