"""
Views for Companies app.
Provides company, division, location, and company user management.
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.db.models import Q
from .models import Company, Division, Location, CompanyUser
from .forms import CompanyForm, DivisionForm, LocationForm, CompanyUserForm
from accounts.models import User


class CompanyListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """
    View for listing companies.
    """
    model = Company
    template_name = 'companies/company_list.html'
    context_object_name = 'companies'
    paginate_by = 20
    
    def test_func(self):
        return self.request.user.can_manage_companies()
    
    def get_queryset(self):
        queryset = Company.objects.all()
        
        # Search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search)
            )
        
        return queryset.order_by('name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Company Management')
        context['search'] = self.request.GET.get('search', '')
        return context


class CompanyCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """
    View for creating new companies.
    """
    model = Company
    form_class = CompanyForm
    template_name = 'companies/company_form.html'
    success_url = reverse_lazy('companies:company_list')
    
    def test_func(self):
        return self.request.user.can_manage_companies()
    
    def form_valid(self, form):
        messages.success(self.request, _('Company created successfully.'))
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Create Company')
        context['action'] = _('Create')
        return context


class CompanyUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    View for updating companies.
    """
    model = Company
    form_class = CompanyForm
    template_name = 'companies/company_form.html'
    success_url = reverse_lazy('companies:company_list')
    
    def test_func(self):
        return self.request.user.can_manage_companies()
    
    def form_valid(self, form):
        messages.success(self.request, _('Company updated successfully.'))
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Edit Company')
        context['action'] = _('Update')
        return context


class CompanyDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """
    View for deleting companies.
    """
    model = Company
    template_name = 'companies/company_confirm_delete.html'
    success_url = reverse_lazy('companies:company_list')
    
    def test_func(self):
        return self.request.user.can_manage_companies()
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, _('Company deleted successfully.'))
        return super().delete(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Delete Company')
        return context


class DivisionListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """
    View for listing divisions.
    """
    model = Division
    template_name = 'companies/division_list.html'
    context_object_name = 'divisions'
    paginate_by = 20
    
    def test_func(self):
        return self.request.user.can_manage_companies()
    
    def get_queryset(self):
        queryset = Division.objects.select_related('company').all()
        
        # Search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search) |
                Q(company__name__icontains=search)
            )
        
        return queryset.order_by('company__name', 'name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Division Management')
        context['search'] = self.request.GET.get('search', '')
        return context


class DivisionCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """
    View for creating new divisions.
    """
    model = Division
    form_class = DivisionForm
    template_name = 'companies/division_form.html'
    success_url = reverse_lazy('companies:division_list')
    
    def test_func(self):
        return self.request.user.can_manage_companies()
    
    def form_valid(self, form):
        messages.success(self.request, _('Division created successfully.'))
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Create Division')
        context['action'] = _('Create')
        return context


class DivisionUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    View for updating divisions.
    """
    model = Division
    form_class = DivisionForm
    template_name = 'companies/division_form.html'
    success_url = reverse_lazy('companies:division_list')
    
    def test_func(self):
        return self.request.user.can_manage_companies()
    
    def form_valid(self, form):
        messages.success(self.request, _('Division updated successfully.'))
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Edit Division')
        context['action'] = _('Update')
        return context


class DivisionDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """
    View for deleting divisions.
    """
    model = Division
    template_name = 'companies/division_confirm_delete.html'
    success_url = reverse_lazy('companies:division_list')
    
    def test_func(self):
        return self.request.user.can_manage_companies()
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, _('Division deleted successfully.'))
        return super().delete(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Delete Division')
        return context


class LocationListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """
    View for listing locations.
    """
    model = Location
    template_name = 'companies/location_list.html'
    context_object_name = 'locations'
    paginate_by = 20
    
    def test_func(self):
        return self.request.user.can_manage_companies()
    
    def get_queryset(self):
        queryset = Location.objects.select_related('company', 'manager').all()
        
        # Search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(address_line1__icontains=search) |
                Q(address_line2__icontains=search) |
                Q(city__icontains=search) |
                Q(code__icontains=search) |
                Q(zone__icontains=search) |
                Q(rack__icontains=search) |
                Q(shelf__icontains=search) |
                Q(company__name__icontains=search) |
                Q(manager__first_name__icontains=search) |
                Q(manager__last_name__icontains=search)
            )
        
        return queryset.order_by('company__name', 'name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Location Management')
        context['search'] = self.request.GET.get('search', '')
        all_locations = context.get('locations')
        if all_locations is not None:
            warehouses = [location for location in all_locations if location.location_type == Location.LocationType.WAREHOUSE]
            context['warehouse_count'] = len(warehouses)
            context['slot_total'] = sum(location.get_slot_count() for location in warehouses)
        return context


class LocationCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """
    View for creating new locations.
    """
    model = Location
    form_class = LocationForm
    template_name = 'companies/location_form.html'
    success_url = reverse_lazy('companies:location_list')
    
    def test_func(self):
        return self.request.user.can_manage_companies()
    
    def form_valid(self, form):
        messages.success(self.request, _('Location created successfully.'))
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Create Location')
        context['action'] = _('Create')
        return context


class LocationUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    View for updating locations.
    """
    model = Location
    form_class = LocationForm
    template_name = 'companies/location_form.html'
    success_url = reverse_lazy('companies:location_list')
    
    def test_func(self):
        return self.request.user.can_manage_companies()
    
    def form_valid(self, form):
        messages.success(self.request, _('Location updated successfully.'))
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Edit Location')
        context['action'] = _('Update')
        return context


class LocationDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """
    View for deleting locations.
    """
    model = Location
    template_name = 'companies/location_confirm_delete.html'
    success_url = reverse_lazy('companies:location_list')
    
    def test_func(self):
        return self.request.user.can_manage_companies()
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, _('Location deleted successfully.'))
        return super().delete(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Delete Location')
        return context


class CompanyUserListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """
    View for listing company users.
    """
    model = CompanyUser
    template_name = 'companies/companyuser_list.html'
    context_object_name = 'company_users'
    paginate_by = 20
    
    def test_func(self):
        return self.request.user.can_manage_companies()
    
    def get_queryset(self):
        queryset = CompanyUser.objects.select_related('user', 'company', 'location').all()
        
        # Search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(user__username__icontains=search) |
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(user__email__icontains=search) |
                Q(company__name__icontains=search) |
                Q(location__name__icontains=search)
            )
        
        return queryset.order_by('company__name', 'user__username')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Company User Management')
        context['search'] = self.request.GET.get('search', '')
        return context


class CompanyUserCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """View for creating company user memberships."""
    model = CompanyUser
    form_class = CompanyUserForm
    template_name = 'companies/companyuser_form.html'
    success_url = reverse_lazy('companies:companyuser_list')

    def test_func(self):
        return self.request.user.can_manage_companies()

    def form_valid(self, form):
        messages.success(self.request, _('Company user added successfully.'))
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Add Company User')
        context['action'] = _('Create')
        return context


class CompanyUserUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """View for editing company user memberships."""
    model = CompanyUser
    form_class = CompanyUserForm
    template_name = 'companies/companyuser_form.html'
    success_url = reverse_lazy('companies:companyuser_list')

    def test_func(self):
        return self.request.user.can_manage_companies()

    def form_valid(self, form):
        messages.success(self.request, _('Company user updated successfully.'))
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Edit Company User')
        context['action'] = _('Update')
        return context
