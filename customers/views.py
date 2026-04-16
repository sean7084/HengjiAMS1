"""
Views for Customers app.
"""
from django.shortcuts import get_object_or_404, render
from django.urls import reverse_lazy
from django.contrib import messages
from django.views.generic import ListView, DetailView, UpdateView, CreateView

from companies.models import Company
from .models import CustomerProfile
from .forms import CustomerProfileForm


class CustomerProfileListView(ListView):
    """List view for customer profiles."""
    model = CustomerProfile
    template_name = 'customers/profile_list.html'
    context_object_name = 'profiles'
    paginate_by = 20

    def get_queryset(self):
        return CustomerProfile.objects.select_related('company').all()


class CustomerProfileDetailView(DetailView):
    """Detail view for customer profile."""
    model = CustomerProfile
    template_name = 'customers/profile_detail.html'
    context_object_name = 'profile'

    def get_object(self):
        company_id = self.kwargs.get('company_id')
        profile = get_object_or_404(CustomerProfile, company_id=company_id)
        return profile

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['company'] = self.object.company
        return context


class CustomerProfileCreateView(CreateView):
    """Create view for customer profile."""
    model = CustomerProfile
    form_class = CustomerProfileForm
    template_name = 'customers/profile_form.html'

    def get_initial(self):
        company_id = self.kwargs.get('company_id')
        return {'company': get_object_or_404(Company, pk=company_id)}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company_id = self.kwargs.get('company_id')
        context['company'] = get_object_or_404(Company, pk=company_id)
        return context

    def get_success_url(self):
        return reverse_lazy('customers:profile_detail', kwargs={'company_id': self.object.company_id})

    def form_valid(self, form):
        company_id = self.kwargs.get('company_id')
        company = get_object_or_404(Company, pk=company_id)
        form.instance.company = company
        messages.success(self.request, 'Customer profile created successfully.')
        return super().form_valid(form)


class CustomerProfileUpdateView(UpdateView):
    """Update view for customer profile."""
    model = CustomerProfile
    form_class = CustomerProfileForm
    template_name = 'customers/profile_form.html'

    def get_object(self):
        company_id = self.kwargs.get('company_id')
        return get_object_or_404(CustomerProfile, company_id=company_id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['company'] = self.object.company
        return context

    def get_success_url(self):
        return reverse_lazy('customers:profile_detail', kwargs={'company_id': self.object.company_id})

    def form_valid(self, form):
        messages.success(self.request, 'Customer profile updated successfully.')
        return super().form_valid(form)
