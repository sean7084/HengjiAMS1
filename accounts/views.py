"""
Views for HengJi Asset Management System - Accounts App.
This module handles authentication, user management, and profile-related views.
Includes 2FA support, multi-language interface, and role-based access control.
"""

import qrcode
import io
import base64
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.views.generic import (
    TemplateView, FormView, ListView, DetailView, 
    CreateView, UpdateView, DeleteView
)
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse, HttpResponseRedirect
from django.utils.translation import gettext_lazy as _
from django.utils.translation import activate
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.db.models import Q
from django_otp.models import Device
from django_otp.plugins.otp_totp.models import TOTPDevice
from django_otp.plugins.otp_static.models import StaticDevice, StaticToken
from django_otp.util import random_hex
from django_otp.decorators import otp_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash

from .models import User, UserSession
from .forms import (
    CustomLoginForm, UserRegistrationForm, UserProfileForm, 
    UserSettingsForm, TwoFactorSetupForm, TwoFactorVerifyForm
)


class LoginView(FormView):
    """
    Custom login view with 2FA support and multi-language interface.
    """
    template_name = 'accounts/login.html'
    form_class = CustomLoginForm
    success_url = reverse_lazy('dashboard')
    
    def dispatch(self, request, *args, **kwargs):
        # Redirect if user is already logged in
        if request.user.is_authenticated:
            return redirect(self.success_url)
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        user = authenticate(self.request, username=username, password=password)
        
        if user is not None:
            if user.is_active:
                # Check if 2FA is required
                if user.force_2fa_setup or not user.is_2fa_enabled:
                    # Store user in session for 2FA setup
                    self.request.session['pre_2fa_user_id'] = user.id
                    messages.info(self.request, _('Please set up two-factor authentication.'))
                    return redirect('accounts:2fa_setup')
                else:
                    # Check if user has 2FA devices
                    totp_devices = TOTPDevice.objects.filter(user=user, confirmed=True)
                    if totp_devices.exists():
                        # Store user in session for 2FA verification
                        self.request.session['pre_2fa_user_id'] = user.id
                        return redirect('accounts:2fa_verify')
                    else:
                        # No 2FA devices, force setup
                        self.request.session['pre_2fa_user_id'] = user.id
                        messages.warning(self.request, _('Two-factor authentication is required.'))
                        return redirect('accounts:2fa_setup')
            else:
                messages.error(self.request, _('Your account is disabled.'))
        else:
            messages.error(self.request, _('Invalid username or password.'))
        
        return self.form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Login')
        context['login_page'] = True  # Flag for base template
        return context


class TwoFactorSetupView(FormView):
    """
    View for setting up two-factor authentication.
    """
    template_name = 'accounts/2fa_setup.html'
    form_class = TwoFactorSetupForm
    success_url = reverse_lazy('accounts:2fa_verify')
    
    def dispatch(self, request, *args, **kwargs):
        # Check if user is in pre-2FA state
        if 'pre_2fa_user_id' not in request.session:
            return redirect('accounts:login')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_id = self.request.session.get('pre_2fa_user_id')
        user = get_object_or_404(User, id=user_id)
        
        # Create or get TOTP device
        device, created = TOTPDevice.objects.get_or_create(
            user=user,
            name='default',
            defaults={'confirmed': False}
        )
        
        # Generate QR code
        qr_code_url = device.config_url
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_code_url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        qr_code_data = base64.b64encode(buffer.getvalue()).decode()
        
        context.update({
            'title': _('Set Up Two-Factor Authentication'),
            'qr_code_data': qr_code_data,
            'secret_key': device.key,
            'user': user,
        })
        return context
    
    def form_valid(self, form):
        user_id = self.request.session.get('pre_2fa_user_id')
        user = get_object_or_404(User, id=user_id)
        token = form.cleaned_data['token']
        
        # Verify the token
        device = TOTPDevice.objects.get(user=user, name='default')
        if device.verify_token(token):
            device.confirmed = True
            device.save()
            
            user.is_2fa_enabled = True
            user.force_2fa_setup = False
            user.save()
            
            # Generate backup tokens
            static_device, created = StaticDevice.objects.get_or_create(
                user=user,
                name='backup'
            )
            
            # Generate 10 backup tokens
            tokens = []
            for _ in range(10):
                token = StaticToken.random_token()
                StaticToken.objects.create(device=static_device, token=token)
                tokens.append(token)
            
            self.request.session['backup_tokens'] = tokens
            messages.success(self.request, _('Two-factor authentication has been set up successfully.'))
            return redirect('accounts:backup_tokens')
        else:
            messages.error(self.request, _('Invalid token. Please try again.'))
            return self.form_invalid(form)


class TwoFactorVerifyView(FormView):
    """
    View for verifying two-factor authentication during login.
    """
    template_name = 'accounts/2fa_verify.html'
    form_class = TwoFactorVerifyForm
    success_url = reverse_lazy('dashboard')
    
    def dispatch(self, request, *args, **kwargs):
        # Check if user is in pre-2FA state
        if 'pre_2fa_user_id' not in request.session:
            return redirect('accounts:login')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        user_id = self.request.session.get('pre_2fa_user_id')
        user = get_object_or_404(User, id=user_id)
        token = form.cleaned_data['token']
        
        # Try TOTP token first
        totp_devices = TOTPDevice.objects.filter(user=user, confirmed=True)
        for device in totp_devices:
            if device.verify_token(token):
                # Login successful
                login(self.request, user)
                del self.request.session['pre_2fa_user_id']
                
                # Log the session
                UserSession.objects.create(
                    user=user,
                    session_key=self.request.session.session_key,
                    ip_address=self.get_client_ip(),
                    user_agent=self.request.META.get('HTTP_USER_AGENT', '')
                )
                
                messages.success(self.request, _('Welcome back, {user}!').format(user=user.get_full_name_display()))
                return redirect(self.success_url)
        
        # Try backup tokens
        static_devices = StaticDevice.objects.filter(user=user)
        for device in static_devices:
            if device.verify_token(token):
                # Login successful with backup token
                login(self.request, user)
                del self.request.session['pre_2fa_user_id']
                
                # Log the session
                UserSession.objects.create(
                    user=user,
                    session_key=self.request.session.session_key,
                    ip_address=self.get_client_ip(),
                    user_agent=self.request.META.get('HTTP_USER_AGENT', '')
                )
                
                messages.warning(self.request, _('You used a backup token. Please generate new backup tokens.'))
                return redirect(self.success_url)
        
        messages.error(self.request, _('Invalid token. Please try again.'))
        return self.form_invalid(form)
    
    def get_client_ip(self):
        """Get client IP address from request."""
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Verify Two-Factor Authentication')
        return context


class BackupTokensView(LoginRequiredMixin, TemplateView):
    """
    View for displaying backup tokens after 2FA setup.
    """
    template_name = 'accounts/backup_tokens.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Backup Tokens')
        context['backup_tokens'] = self.request.session.get('backup_tokens', [])
        return context
    
    def post(self, request, *args, **kwargs):
        # Clear backup tokens from session after user acknowledges them
        if 'backup_tokens' in request.session:
            del request.session['backup_tokens']
        return redirect('dashboard')


class ProfileView(LoginRequiredMixin, DetailView):
    """
    View for displaying user profile.
    """
    template_name = 'accounts/profile.html'
    context_object_name = 'profile_user'
    
    def get_object(self):
        return self.request.user
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Profile')
        return context


class ProfileEditView(LoginRequiredMixin, UpdateView):
    """
    View for editing user profile.
    """
    template_name = 'accounts/profile_edit.html'
    form_class = UserProfileForm
    success_url = reverse_lazy('accounts:profile')
    
    def get_object(self):
        return self.request.user
    
    def form_valid(self, form):
        messages.success(self.request, _('Profile updated successfully.'))
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Edit Profile')
        return context


class UserSettingsView(LoginRequiredMixin, UpdateView):
    """
    View for user settings including language preference.
    """
    template_name = 'accounts/settings.html'
    form_class = UserSettingsForm
    success_url = reverse_lazy('accounts:settings')
    
    def get_object(self):
        return self.request.user
    
    def form_valid(self, form):
        response = super().form_valid(form)
        # Activate the selected language
        language = form.cleaned_data['language_preference']
        activate(language)
        messages.success(self.request, _('Settings updated successfully.'))
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Settings')
        return context


class ChangePasswordView(LoginRequiredMixin, FormView):
    """
    View for changing user password.
    """
    template_name = 'accounts/change_password.html'
    form_class = PasswordChangeForm
    success_url = reverse_lazy('accounts:profile')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        user = form.save()
        update_session_auth_hash(self.request, user)
        messages.success(self.request, _('Password changed successfully.'))
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Change Password')
        return context


# Admin-only views for user management
class UserListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """
    View for listing all users (admin only).
    """
    template_name = 'accounts/user_list.html'
    context_object_name = 'users'
    paginate_by = 20
    
    def test_func(self):
        return self.request.user.role in [User.UserRole.SUPER_ADMIN, User.UserRole.COMPANY_ADMIN]
    
    def get_queryset(self):
        queryset = User.objects.all().select_related().order_by('username')
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(username__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(email__icontains=search)
            )
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('User Management')
        context['search'] = self.request.GET.get('search', '')
        return context


class UserDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """
    View for displaying user details (admin only).
    """
    model = User
    template_name = 'accounts/user_detail.html'
    context_object_name = 'profile_user'
    
    def test_func(self):
        return self.request.user.role in [User.UserRole.SUPER_ADMIN, User.UserRole.COMPANY_ADMIN]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('User Details')
        return context


class UserCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """
    View for creating new users (admin only).
    """
    model = User
    form_class = UserRegistrationForm
    template_name = 'accounts/user_create.html'
    success_url = reverse_lazy('accounts:user_list')
    
    def test_func(self):
        return self.request.user.role in [User.UserRole.SUPER_ADMIN, User.UserRole.COMPANY_ADMIN]
    
    def form_valid(self, form):
        messages.success(self.request, _('User created successfully.'))
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Create User')
        return context


class UserEditView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    View for editing users (admin only).
    """
    model = User
    form_class = UserRegistrationForm
    template_name = 'accounts/user_edit.html'
    success_url = reverse_lazy('accounts:user_list')
    
    def test_func(self):
        return self.request.user.role in [User.UserRole.SUPER_ADMIN, User.UserRole.COMPANY_ADMIN]
    
    def form_valid(self, form):
        messages.success(self.request, _('User updated successfully.'))
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Edit User')
        return context


class UserToggleStatusView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    View for toggling user active status (admin only).
    """
    model = User
    fields = ['is_active']
    success_url = reverse_lazy('accounts:user_list')
    
    def test_func(self):
        return self.request.user.role in [User.UserRole.SUPER_ADMIN, User.UserRole.COMPANY_ADMIN]
    
    def post(self, request, *args, **kwargs):
        user = self.get_object()
        user.is_active = not user.is_active
        user.save()
        
        status = _('activated') if user.is_active else _('deactivated')
        messages.success(request, _('User {username} has been {status}.').format(
            username=user.username, status=status
        ))
        return redirect(self.success_url)


class SessionListView(LoginRequiredMixin, ListView):
    """
    View for listing user sessions.
    """
    template_name = 'accounts/session_list.html'
    context_object_name = 'sessions'
    paginate_by = 20
    
    def get_queryset(self):
        return UserSession.objects.filter(user=self.request.user, is_active=True).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Active Sessions')
        return context


class SessionTerminateView(LoginRequiredMixin, UpdateView):
    """
    View for terminating user sessions.
    """
    model = UserSession
    fields = ['is_active']
    success_url = reverse_lazy('accounts:session_list')
    
    def get_queryset(self):
        return UserSession.objects.filter(user=self.request.user)
    
    def post(self, request, *args, **kwargs):
        session = self.get_object()
        session.is_active = False
        session.save()
        
        messages.success(request, _('Session terminated successfully.'))
        return redirect(self.success_url)
