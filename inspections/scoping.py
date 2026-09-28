"""Shared query scoping for the inspections module.

Inspections and batches must be scoped by the *same* rule. Historically the
batch querysets filtered by ``user.get_accessible_companies()`` while
``User.get_assigned_inspections()`` hands superadmins and IT administrators
*every* inspection - so such a user could see inspections on the dashboard yet
see none of the batches those inspections belong to (the batch list looked
empty while the calendar was full).

Everything that scopes an inspections-module queryset should go through here so
the two stay in step.
"""
from django.db.models import Q

from inspections.models import InspectionBatch


def scoped_inspections(user):
    """Return the ``StoreInspection`` queryset the given user may see."""
    return user.get_assigned_inspections().select_related(
        'batch', 'company', 'division', 'location', 'engineer'
    )


def scoped_batches(user):
    """Return the ``InspectionBatch`` queryset the given user may see.

    Mirrors :func:`scoped_inspections`: users who see every inspection
    (superadmin, IT administrator) see every batch. Everyone else gets batches
    from companies they can access plus any batch that actually contains one of
    their own inspections - an engineer assigned to a store in a batch they do
    not administrate still needs to see that planning cycle.
    """
    if user.is_superadmin() or user.is_it_administrator():
        return InspectionBatch.objects.all()
    return InspectionBatch.objects.filter(
        Q(company__in=user.get_accessible_companies())
        | Q(inspections__in=user.get_assigned_inspections())
    ).distinct()


def unbatched_inspection_count(user):
    """How many inspections this user can see that belong to no batch.

    Used to explain an empty batch list: imported inspections only appear there
    once they are attached to a planning cycle.
    """
    return scoped_inspections(user).filter(batch__isnull=True).count()
