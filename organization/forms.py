from django import forms
from django.contrib.auth import get_user_model
from organization.models import EmployeeProfile, Organization, JobPosition, OrganizationUnit, Location
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Submit, HTML
from django.utils.translation import gettext_lazy as _
from users.utils.notification_utils import create_notification, log_activity
from django.contrib.auth.models import Group, Permission
from django.conf import settings
from django.core.exceptions import ValidationError
import logging

logger = logging.getLogger(__name__)

User = get_user_model()

class EmployeeProfileForm(forms.ModelForm):
    first_name = forms.CharField(
        max_length=30,
        help_text=_("Enter the employee's first name.")
    )
    last_name = forms.CharField(
        max_length=30,
        help_text=_("Enter the employee's last name.")
    )
    email = forms.EmailField(
        help_text=_("Enter a valid email address. This will be used as the username.")
    )
    password = forms.CharField(
        widget=forms.PasswordInput(),
        help_text=_("Create a strong password for the employee's account.")
    )

    class Meta:
        model = EmployeeProfile
        fields = ['employee_id', 'job_position', 'organization_unit', 'manager', 'hire_date', 'is_active', 'work_phone', 'work_email']
        widgets = {
            'hire_date': forms.DateInput(attrs={'type': 'date'}),
        }
        help_texts = {
            'employee_id': _("Enter a unique identifier for the employee."),
            'job_position': _("Select the employee's job position."),
            'organization_unit': _("Select the unit where the employee will work."),
            'manager': _("Select the employee's direct manager."),
            'hire_date': _("Enter the date when the employee was hired."),
            'is_active': _("Check if the employee is currently active."),
            'work_phone': _("Enter the employee's work phone number."),
            'work_email': _("Enter the employee's work email address."),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        self.organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)
        if self.organization:
            self.fields['job_position'].queryset = JobPosition.objects.filter(organization=self.organization)
            self.fields['organization_unit'].queryset = OrganizationUnit.objects.filter(organization=self.organization)
            self.fields['manager'].queryset = User.objects.filter(employee_profile__organization=self.organization)

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Div('first_name', css_class='col-md-6'),
                Div('last_name', css_class='col-md-6'),
                css_class='row'
            ),
            Div(
                Div('email', css_class='col-md-6'),
                Div('password', css_class='col-md-6'),
                css_class='row'
            ),
            Div(
                Div('employee_id', css_class='col-md-6'),
                Div('job_position', css_class='col-md-6'),
                css_class='row'
            ),
            Div(
                Div('organization_unit', css_class='col-md-6'),
                Div('manager', css_class='col-md-6'),
                css_class='row'
            ),
            Div(
                Div('hire_date', css_class='col-md-6'),
                Div('work_phone', css_class='col-md-6'),
                css_class='row'
            ),
            Div(
                Div('work_email', css_class='col-md-6'),
                Div('is_active', css_class='col-md-6'),
                css_class='row'
            ),
            HTML("<div class='row'><div class='col-md-12'><hr></div></div>"),
            Div(
                Div(
                    HTML("""
                        <button type="submit" class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
                            Add Employee
                        </button>
                    """),
                    css_class='col-md-12 flex justify-end mt-6'
                ),
                css_class='row'
            )
        )

    def save(self, commit=True):
        user = User.objects.create_user(
            username=self.cleaned_data['email'],
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password'],
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name']
        )
        employee_profile = super().save(commit=False)
        employee_profile.user = user
        employee_profile.organization = self.organization
        if commit:
            employee_profile.save()

            notification_message = _(f"New employee {user.get_full_name()} has been added to the organization.")
            create_notification(self.request.user, notification_message, notification_type='INFO')

            activity_description = _(f"Added new employee: {user.get_full_name()} (ID: {employee_profile.employee_id})")
            log_activity(self.request.user, 'CREATE', activity_description)

        return employee_profile
    

class JobPositionForm(forms.ModelForm):
    title = forms.CharField(
        max_length=255,
        help_text=_("Enter the job title.")
    )
    code = forms.CharField(
        max_length=50,
        required=False,
        help_text=_("Enter the job code (optional).")
    )
    description = forms.CharField(
        widget=forms.Textarea,
        required=False,
        help_text=_("Enter a description for the job position (optional).")
    )
    is_manager_position = forms.BooleanField(
        required=False,
        help_text=_("Check if this is a managerial position.")
    )
    level = forms.IntegerField(
        help_text=_("Enter the level of the job position.")
    )
    parent = forms.ModelChoiceField(
        queryset=JobPosition.objects.none(),
        required=False,
        help_text=_("Select the parent job position (optional).")
    )

    class Meta:
        model = JobPosition
        fields = ['title', 'code', 'description', 'is_manager_position', 'level', 'parent']

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        self.organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)
        if self.organization:
            self.fields['parent'].queryset = JobPosition.objects.filter(organization=self.organization)

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Div('title', css_class='col-md-6'),
                Div('code', css_class='col-md-6'),
                css_class='row'
            ),
            Div(
                Div('description', css_class='col-md-12'),
                css_class='row'
            ),
            Div(
                Div('is_manager_position', css_class='col-md-6'),
                Div('level', css_class='col-md-6'),
                css_class='row'
            ),
            Div(
                Div('parent', css_class='col-md-12'),
                css_class='row'
            ),
            HTML("<div class='row'><div class='col-md-12'><hr></div></div>"),
            Div(
                Div(
                    HTML("""
                        <button type="submit" class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
                            Add Job Position
                        </button>
                    """),
                    css_class='col-md-12 flex justify-end mt-6'
                ),
                css_class='row'
            )
        )

    def save(self, commit=True):
        job_position = super().save(commit=False)
        job_position.organization = self.organization
        if commit:
            job_position.save()

            notification_message = _(f"New job position {job_position.title} has been added to the organization.")
            create_notification(self.request.user, notification_message, notification_type='INFO')

            activity_description = _(f"Added new job position: {job_position.title} (ID: {job_position.id})")
            log_activity(self.request.user, 'CREATE', activity_description)

        return job_position

class LocationForm(forms.ModelForm):
    name = forms.CharField(
        max_length=255,
        help_text=_("Enter the location name.")
    )
    address_line1 = forms.CharField(
        max_length=255,
        help_text=_("Enter the first line of the address.")
    )
    address_line2 = forms.CharField(
        max_length=255,
        required=False,
        help_text=_("Enter the second line of the address (optional).")
    )
    city = forms.CharField(
        max_length=100,
        help_text=_("Enter the city.")
    )
    state = forms.CharField(
        max_length=100,
        help_text=_("Enter the state.")
    )
    country = forms.CharField(
        max_length=100,
        help_text=_("Enter the country.")
    )
    postal_code = forms.CharField(
        max_length=20,
        help_text=_("Enter the postal code.")
    )
    latitude = forms.DecimalField(
        max_digits=9,
        decimal_places=6,
        required=False,
        help_text=_("Enter the latitude (optional).")
    )
    longitude = forms.DecimalField(
        max_digits=9,
        decimal_places=6,
        required=False,
        help_text=_("Enter the longitude (optional).")
    )
    is_headquarters = forms.BooleanField(
        required=False,
        help_text=_("Check if this is the headquarters.")
    )

    class Meta:
        model = Location
        fields = ['name', 'address_line1', 'address_line2', 'city', 'state', 'country', 'postal_code', 'latitude', 'longitude', 'is_headquarters']

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        self.organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Div('name', css_class='col-md-6'),
                Div('address_line1', css_class='col-md-6'),
                css_class='row'
            ),
            Div(
                Div('address_line2', css_class='col-md-6'),
                Div('city', css_class='col-md-6'),
                css_class='row'
            ),
            Div(
                Div('state', css_class='col-md-6'),
                Div('country', css_class='col-md-6'),
                css_class='row'
            ),
            Div(
                Div('postal_code', css_class='col-md-6'),
                Div('latitude', css_class='col-md-6'),
                css_class='row'
            ),
            Div(
                Div('longitude', css_class='col-md-6'),
                Div('is_headquarters', css_class='col-md-6'),
                css_class='row'
            ),
            HTML("<div class='row'><div class='col-md-12'><hr></div></div>"),
            Div(
                Div(
                    HTML("""
                        <button type="submit" class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
                            Add Location
                        </button>
                    """),
                    css_class='col-md-12 flex justify-end mt-6'
                ),
                css_class='row'
            )
        )

    def save(self, commit=True):
        location = super().save(commit=False)
        location.organization = self.organization
        if commit:
            location.save()

            notification_message = _(f"New location {location.name} has been added to the organization.")
            create_notification(self.request.user, notification_message, notification_type='INFO')

            activity_description = _(f"Added new location: {location.name} (ID: {location.id})")
            log_activity(self.request.user, 'CREATE', activity_description)

        return location


class OrganizationUnitForm(forms.ModelForm):
    organization = forms.ModelChoiceField(
        queryset=Organization.objects.all(),
        help_text=_("Select the organization for this unit.")
    )
    name = forms.CharField(
        max_length=255,
        help_text=_("Enter the unit name.")
    )
    unit_type = forms.ChoiceField(
        choices=OrganizationUnit.UNIT_TYPES,
        help_text=_("Select the unit type.")
    )
    code = forms.CharField(
        max_length=50,
        required=False,
        help_text=_("Enter the unit code (optional).")
    )
    parent = forms.ModelChoiceField(
        queryset=OrganizationUnit.objects.none(),
        required=False,
        help_text=_("Select the parent unit (optional).")
    )
    manager = forms.ModelChoiceField(
        queryset=User.objects.none(),
        required=False,
        help_text=_("Select the manager for this unit (optional).")
    )
    description = forms.CharField(
        widget=forms.Textarea,
        required=False,
        help_text=_("Enter a description for the unit (optional).")
    )
    is_active = forms.BooleanField(
        required=False,
        initial=True,
        help_text=_("Check if this unit is active.")
    )

    class Meta:
        model = OrganizationUnit
        fields = ['organization', 'name', 'unit_type', 'code', 'parent', 'manager', 'description', 'is_active']

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        
        try:
            self.fields['parent'].queryset = OrganizationUnit.objects.all()
            self.fields['manager'].queryset = User.objects.filter(groups__name__in=['administrator', 'supervisor'])

            self.helper = FormHelper()
            self.helper.layout = Layout(
                Div(
                    Div('organization', css_class='col-md-6'),
                    Div('name', css_class='col-md-6'),
                    css_class='row'
                ),
                Div(
                    Div('unit_type', css_class='col-md-6'),
                    Div('code', css_class='col-md-6'),
                    css_class='row'
                ),
                Div(
                    Div('parent', css_class='col-md-6'),
                    Div('manager', css_class='col-md-6'),
                    css_class='row'
                ),
                Div(
                    Div('description', css_class='col-md-12'),
                    css_class='row'
                ),
                Div(
                    Div('is_active', css_class='col-md-6'),
                    css_class='row'
                ),
                HTML("<div class='row'><div class='col-md-12'><hr></div></div>"),
                Div(
                    Div(
                        HTML("""
                            <button type="submit" class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
                                Add Unit
                            </button>
                        """),
                        css_class='col-md-12 flex justify-end mt-6'
                    ),
                    css_class='row'
                )
            )
        except Exception as e:
            logger.error(f"Error initializing OrganizationUnitForm: {str(e)}")
            raise

    def clean(self):
        cleaned_data = super().clean()
        organization = cleaned_data.get('organization')
        parent = cleaned_data.get('parent')

        if organization and parent and parent.organization != organization:
            raise ValidationError(_("Parent unit must belong to the same organization."))

        return cleaned_data

    def save(self, commit=True):
        try:
            unit = super().save(commit=False)
            if commit:
                unit.save()

                notification_message = _(f"New unit {unit.name} has been added to the organization.")
                create_notification(self.request.user, notification_message, notification_type='INFO')

                activity_description = _(f"Added new unit: {unit.name} (ID: {unit.id})")
                log_activity(self.request.user, 'CREATE', activity_description)

            return unit
        except Exception as e:
            logger.error(f"Error saving OrganizationUnit: {str(e)}")
            raise

class OrganizationGroupForm(forms.ModelForm):
    name = forms.CharField(
        max_length=150,
        help_text=_("Enter the group name.")
    )
    permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        help_text=_("Select the permissions for this group.")
    )

    class Meta:
        model = Group
        fields = ['name', 'permissions']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Div('name', css_class='col-md-6'),
                css_class='row'
            ),
            Div(
                Div('permissions', css_class='col-md-12 permissions-container'),
                css_class='row'
            ),
            HTML("<div class='row'><div class='col-md-12'><hr></div></div>"),
            Div(
                Div(
                    HTML("""
                        <button type="submit" class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
                            Add Group
                        </button>
                    """),
                    css_class='col-md-12 flex justify-end mt-6'
                ),
                css_class='row'
            )
        )