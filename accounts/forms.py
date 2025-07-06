"""
Forms for HengJi Asset Management System - Accounts App.
This module defines forms for authentication, user management, and profile handling.
Includes 2FA forms, multi-language support, and validation.
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate
from django_otp.plugins.otp_totp.models import TOTPDevice

from .models import User


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
    role = forms.ChoiceField(
        choices=User.UserRole.choices,
        widget=forms.Select(attrs={
            'class': 'form-control',
        }),
        label=_('Role'),
        help_text=_('Select the user role and permissions level')
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
        choices=[
            ('en', _('English')),
            ('zh-hans', _('Simplified Chinese')),
        ],
        widget=forms.Select(attrs={
            'class': 'form-control',
        }),
        label=_('Language Preference'),
        initial='en'
    )
    
    class Meta:
        model = User
        fields = (
            'username', 'email', 'first_name', 'last_name', 
            'password1', 'password2', 'role', 'phone_number', 
            'language_preference'
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
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.role = self.cleaned_data['role']
        user.phone_number = self.cleaned_data['phone_number']
        user.language_preference = self.cleaned_data['language_preference']
        
        if commit:
            user.save()
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
        choices=[
            ('en', _('English')),
            ('zh-hans', _('简体中文')),
        ],
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
