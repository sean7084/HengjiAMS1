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
        queryset = Location.objects.select_related('company', 'division').all()
        
        # Search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(address__icontains=search) |
                Q(company__name__icontains=search) |
                Q(division__name__icontains=search)
            )
        
        return queryset.order_by('company__name', 'division__name', 'name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Location Management')
        context['search'] = self.request.GET.get('search', '')
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
        queryset = CompanyUser.objects.select_related('user', 'company', 'division', 'location').all()
        
        # Search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(user__username__icontains=search) |
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(user__email__icontains=search) |
                Q(company__name__icontains=search) |
                Q(division__name__icontains=search) |
                Q(location__name__icontains=search)
            )
        
        return queryset.order_by('company__name', 'user__username')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Company User Management')
        context['search'] = self.request.GET.get('search', '')
        return context
