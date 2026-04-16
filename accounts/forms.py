"""
Forms for HengJi Asset Management System - Accounts App.
This module defines forms for authentication, user management, and profile handling.
Includes 2FA forms, multi-language support, and validation.
"""

import secrets
import string
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate
from django_otp.plugins.otp_totp.models import TOTPDevice

from .models import User


LANGUAGE_PREFERENCE_CHOICES = [
    ('en-us', _('English (US)')),
    ('zh-cn', _('Simplified Chinese')),
]


class CustomLoginForm(AuthenticationForm):
    """
    Custom login form with enhanced styling and validation.
    """
    username = forms.CharField(
        max_length=254,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Username'),
            'autofocus': True,
        }),
        label=_('Username')
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': _('Password'),
        }),
        label=_('Password')
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove the default error messages from parent class
        self.error_messages = {
            'invalid_login': _('Please enter correct username and password.'),
            'inactive': _('This account is inactive.'),
        }


class UserRegistrationForm(UserCreationForm):
    """
    Form for creating new users with additional fields and validation.
    """
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': _('Email Address'),
        }),
        label=_('Email Address')
    )
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('First Name'),
        }),
        label=_('First Name')
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Last Name'),
        }),
        label=_('Last Name')
    )
    admin_role = forms.ChoiceField(
        choices=User.AdminRole.choices,
        widget=forms.Select(attrs={
            'class': 'form-control',
        }),
        label=_('Administrator Role'),
        help_text=_('Select the administrator role and permissions level')
    )
    phone_number = forms.CharField(
        max_length=17,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Phone Number (optional)'),
        }),
        label=_('Phone Number'),
        help_text=_('Format: +1234567890')
    )
    language_preference = forms.ChoiceField(
        choices=LANGUAGE_PREFERENCE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-control',
        }),
        label=_('Language Preference'),
        initial='en-us'
    )
    
    # Password generation options
    use_random_password = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'id': 'use_random_password'
        }),
        label=_('Generate Random Password'),
        help_text=_('Generate a secure random password instead of manual entry')
    )
    
    must_change_password = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'id': 'must_change_password'
        }),
        label=_('Require Password Change on First Login'),
        help_text=_('User must change password when they first log in')
    )
    
    class Meta:
        model = User
        fields = (
            'username', 'email', 'first_name', 'last_name', 
            'password1', 'password2', 'admin_role', 'phone_number', 
            'language_preference', 'use_random_password', 'must_change_password'
        )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add CSS classes to default fields
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': _('Username')
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': _('Password')
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': _('Confirm Password')
        })
        
        # Update labels
        self.fields['username'].label = _('Username')
        self.fields['password1'].label = _('Password')
        self.fields['password2'].label = _('Confirm Password')
        
        # Make password fields not required when using random password
        self.fields['password1'].required = False
        self.fields['password2'].required = False
        
        # Add help text for random password
        self.fields['password1'].help_text = _('Leave blank to use random password')
        self.fields['password2'].help_text = _('Leave blank to use random password')
    
    def generate_random_password(self, length=12):
        """Generate a secure random password."""
        # Include uppercase, lowercase, digits, and some safe special characters
        characters = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(secrets.choice(characters) for _ in range(length))
    
    def clean(self):
        cleaned_data = super().clean()
        use_random_password = cleaned_data.get('use_random_password')
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        
        if not use_random_password:
            # If not using random password, require manual password entry
            if not password1:
                raise ValidationError(_('Password is required when not using random password generation.'))
            if not password2:
                raise ValidationError(_('Password confirmation is required when not using random password generation.'))
            if password1 != password2:
                raise ValidationError(_('Passwords do not match.'))
        else:
            # Generate random password
            random_password = self.generate_random_password()
            cleaned_data['password1'] = random_password
            cleaned_data['password2'] = random_password
            # Store the generated password for later use
            self.generated_password = random_password
        
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.admin_role = self.cleaned_data['admin_role']
        user.phone_number = self.cleaned_data['phone_number']
        user.language_preference = self.cleaned_data['language_preference']
        user.must_change_password = self.cleaned_data['must_change_password']
        
        if commit:
            user.save()
        return user


class SuperuserUserForm(UserCreationForm):
    """
    Enhanced form for superusers to create/edit users with full access to all fields.
    """
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': _('Email Address'),
        }),
        label=_('Email Address')
    )
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('First Name'),
        }),
        label=_('First Name')
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Last Name'),
        }),
        label=_('Last Name')
    )
    employee_id = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Employee ID (optional)'),
        }),
        label=_('Employee ID'),
        help_text=_('Unique employee identification number')
    )
    phone_number = forms.CharField(
        max_length=17,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Phone Number (optional)'),
        }),
        label=_('Phone Number'),
        help_text=_('Format: +1234567890')
    )
    department = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Department (optional)'),
        }),
        label=_('Department')
    )
    job_title = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Job Title (optional)'),
        }),
        label=_('Job Title')
    )
    
    # Company association fields
    company = forms.ModelChoiceField(
        queryset=None,  # Will be set in __init__
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control',
        }),
        label=_('Company'),
        help_text=_('Company this user belongs to')
    )
    division = forms.ModelChoiceField(
        queryset=None,  # Will be set in __init__
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control',
        }),
        label=_('Division'),
        help_text=_('Division this user belongs to')
    )
    manager = forms.ModelChoiceField(
        queryset=None,  # Will be set in __init__
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control',
        }),
        label=_('Manager'),
        help_text=_('Direct supervisor for this user')
    )
    
    # Admin role and permissions
    admin_role = forms.ChoiceField(
        choices=User.AdminRole.choices,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control',
        }),
        label=_('Administrator Role'),
        help_text=_('Select the administrator role and permissions level')
    )
    managed_company = forms.ModelChoiceField(
        queryset=None,  # Will be set in __init__
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control',
        }),
        label=_('Managed Company'),
        help_text=_('Company this IT administrator has access to')
    )
    managed_divisions = forms.ModelMultipleChoiceField(
        queryset=None,  # Will be set in __init__
        required=False,
        widget=forms.SelectMultiple(attrs={
            'class': 'form-control',
            'size': '5',
        }),
        label=_('Managed Divisions'),
        help_text=_('Divisions this IT administrator has access to (hold Ctrl/Cmd for multiple)')
    )
    managed_locations = forms.ModelMultipleChoiceField(
        queryset=None,  # Will be set in __init__
        required=False,
        widget=forms.SelectMultiple(attrs={
            'class': 'form-control',
            'size': '5',
        }),
        label=_('Managed Locations'),
        help_text=_('Locations this viewer has read-only access to (hold Ctrl/Cmd for multiple)')
    )
    
    # Additional settings
    language_preference = forms.ChoiceField(
        choices=LANGUAGE_PREFERENCE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-control',
        }),
        label=_('Language Preference'),
        initial='en-us'
    )
    timezone = forms.CharField(
        max_length=50,
        initial='UTC',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'UTC',
        }),
        label=_('Timezone')
    )
    is_active = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        }),
        label=_('Active'),
        help_text=_('User can log in and access the system')
    )
    is_staff = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        }),
        label=_('Staff Status'),
        help_text=_('User can access Django admin interface')
    )
    
    # Password generation options
    use_random_password = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'id': 'use_random_password'
        }),
        label=_('Generate Random Password'),
        help_text=_('Generate a secure random password instead of manual entry')
    )
    must_change_password = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        }),
        label=_('Require Password Change on First Login'),
        help_text=_('User must change password when they first log in')
    )
    
    class Meta:
        model = User
        fields = (
            'username', 'email', 'first_name', 'last_name', 'employee_id',
            'phone_number', 'department', 'job_title', 'company', 'division', 'manager',
            'admin_role', 'managed_company', 'managed_divisions', 'managed_locations',
            'language_preference', 'timezone', 'is_active', 'is_staff',
            'password1', 'password2', 'use_random_password', 'must_change_password'
        )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Import here to avoid circular imports
        from companies.models import Company, Division, Location
        
        # Set up querysets for foreign key fields
        self.fields['company'].queryset = Company.objects.filter(status='active')
        self.fields['division'].queryset = Division.objects.filter(status='active')
        self.fields['manager'].queryset = User.objects.filter(is_active=True)
        self.fields['managed_company'].queryset = Company.objects.filter(status='active')
        self.fields['managed_divisions'].queryset = Division.objects.filter(status='active')
        self.fields['managed_locations'].queryset = Location.objects.filter(status='active')
        
        # Add CSS classes to default fields
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': _('Username')
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': _('Password')
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': _('Confirm Password')
        })
        
        # Update labels
        self.fields['username'].label = _('Username')
        self.fields['password1'].label = _('Password')
        self.fields['password2'].label = _('Confirm Password')
        
        # Make password fields not required when using random password
        self.fields['password1'].required = False
        self.fields['password2'].required = False
        
        # Add help text for random password
        self.fields['password1'].help_text = _('Leave blank to use random password')
        self.fields['password2'].help_text = _('Leave blank to use random password')
    
    def generate_random_password(self, length=12):
        """Generate a secure random password."""
        characters = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(secrets.choice(characters) for _ in range(length))
    
    def clean(self):
        cleaned_data = super().clean()
        use_random_password = cleaned_data.get('use_random_password')
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        
        if not use_random_password:
            # If not using random password, require manual password entry
            if not password1:
                raise ValidationError(_('Password is required when not using random password generation.'))
            if not password2:
                raise ValidationError(_('Password confirmation is required when not using random password generation.'))
            if password1 != password2:
                raise ValidationError(_('Passwords do not match.'))
        else:
            # Generate random password
            random_password = self.generate_random_password()
            cleaned_data['password1'] = random_password
            cleaned_data['password2'] = random_password
            # Store the generated password for later use
            self.generated_password = random_password
        
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        
        # Save all the additional fields
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.employee_id = self.cleaned_data.get('employee_id')
        user.phone_number = self.cleaned_data.get('phone_number', '')
        user.department = self.cleaned_data.get('department', '')
        user.job_title = self.cleaned_data.get('job_title', '')
        user.company = self.cleaned_data.get('company')
        user.division = self.cleaned_data.get('division')
        user.manager = self.cleaned_data.get('manager')
        user.admin_role = self.cleaned_data.get('admin_role')
        user.managed_company = self.cleaned_data.get('managed_company')
        user.language_preference = self.cleaned_data.get('language_preference', 'en-us')
        user.timezone = self.cleaned_data.get('timezone', 'UTC')
        user.is_active = self.cleaned_data.get('is_active', True)
        user.is_staff = self.cleaned_data.get('is_staff', False)
        user.must_change_password = self.cleaned_data.get('must_change_password', True)
        
        if commit:
            user.save()
            # Save many-to-many fields
            if 'managed_divisions' in self.cleaned_data:
                user.managed_divisions.set(self.cleaned_data['managed_divisions'])
            if 'managed_locations' in self.cleaned_data:
                user.managed_locations.set(self.cleaned_data['managed_locations'])
        
        return user


class UserProfileForm(forms.ModelForm):
    """
    Form for editing user profile information.
    """
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'email', 'phone_number', 
            'profile_image'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('First Name')
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Last Name')
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': _('Email Address')
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Phone Number')
            }),
            'profile_image': forms.FileInput(attrs={
                'class': 'form-control-file'
            }),
        }
        labels = {
            'first_name': _('First Name'),
            'last_name': _('Last Name'),
            'email': _('Email Address'),
            'phone_number': _('Phone Number'),
            'profile_image': _('Profile Image'),
        }
        help_texts = {
            'phone_number': _('Format: +1234567890'),
            'profile_image': _('Upload a profile image (optional)'),
        }


class UserSettingsForm(forms.ModelForm):
    """
    Form for user settings including language preference.
    """
    class Meta:
        model = User
        fields = ['language_preference']
        widgets = {
            'language_preference': forms.Select(attrs={
                'class': 'form-control'
            }),
        }
        labels = {
            'language_preference': _('Language Preference'),
        }


class TwoFactorSetupForm(forms.Form):
    """
    Form for setting up two-factor authentication.
    """
    token = forms.CharField(
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            'class': 'form-control text-center',
            'placeholder': '000000',
            'pattern': '[0-9]{6}',
            'maxlength': '6',
            'autocomplete': 'off',
        }),
        label=_('Verification Code'),
        help_text=_('Enter the 6-digit code from your authenticator app')
    )
    
    def clean_token(self):
        token = self.cleaned_data['token']
        if not token.isdigit():
            raise ValidationError(_('Token must be 6 digits'))
        if len(token) != 6:
            raise ValidationError(_('Token must be exactly 6 digits'))
        return token


class TwoFactorVerifyForm(forms.Form):
    """
    Form for verifying two-factor authentication during login.
    """
    token = forms.CharField(
        max_length=20,  # Allow backup tokens which are longer
        widget=forms.TextInput(attrs={
            'class': 'form-control text-center',
            'placeholder': _('6-digit code or backup token'),
            'autocomplete': 'off',
        }),
        label=_('Verification Code'),
        help_text=_('Enter the 6-digit code from your authenticator app or a backup token')
    )
    
    def clean_token(self):
        token = self.cleaned_data['token']
        # Allow both 6-digit TOTP codes and longer backup tokens
        if len(token) == 6:
            if not token.isdigit():
                raise ValidationError(_('6-digit code must contain only numbers'))
        elif len(token) < 6:
            raise ValidationError(_('Token is too short'))
        # Backup tokens can be alphanumeric and longer
        return token


class LanguageSwitchForm(forms.Form):
    """
    Simple form for language switching.
    """
    language = forms.ChoiceField(
        choices=LANGUAGE_PREFERENCE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-control form-control-sm',
            'onchange': 'this.form.submit();'
        }),
        label=''
    )


class UserSearchForm(forms.Form):
    """
    Form for searching users in admin interface.
    """
    search = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Search users by username, name, or email...'),
        }),
        label=''
    )


class CompanyAccessForm(forms.Form):
    """
    Form for managing user access to companies and divisions.
    """
    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # This will be implemented when we create the companies app
        # For now, just a placeholder
        pass
