"""Pure date/slot auto-arrangement for inspection batches.

Used when an imported site list (schedule.xlsx) has no ``inspection_date``
column. The rule (product-specified):

- Cluster sites by **City**; cities are laid out as contiguous blocks across the
  batch date range so a city's sites fall within a span of days (minimizes travel).
- Within a city, sites sharing the same normalized **Address / mall** are placed
  on **consecutive AM/PM slots**, so co-located stores are visited back-to-back.
- Different addresses follow on subsequent slots, spreading them across dates.
- Capacity is one site per slot and ``slots_per_day`` slots per day (default 2:
  AM + PM). If the range cannot fit every site, ``ScheduleCapacityError`` is
  raised so the caller can widen the window instead of silently over-packing.

The function is dependency-free (no DB access) so it is trivially unit-testable.
"""
from collections import OrderedDict
from datetime import timedelta

# Slot labels mirror ``StoreInspection.Slot`` ('am' / 'pm').
SLOT_LABELS = ('am', 'pm')


class ScheduleCapacityError(ValueError):
    """Raised when the date range cannot accommodate every site at the given capacity."""


def _norm(value):
    """Normalize a clustering key: collapse whitespace, casefold, empty -> '_'."""
    text = ' '.join(str(value or '').split()).casefold()
    return text or '_'


def build_slot_sequence(start_date, end_date, slots_per_day=2):
    """Return the ordered [(date, slot)] grid for a date range."""
    labels = SLOT_LABELS[:slots_per_day]
    days = (end_date - start_date).days + 1
    if days <= 0:
        raise ScheduleCapacityError('end_date must be on or after start_date.')
    return [
        (start_date + timedelta(days=day), labels[slot_index])
        for day in range(days)
        for slot_index in range(len(labels))
    ]


def arrange(rows, start_date, end_date, slots_per_day=2):
    """Annotate each schedule row with an ``inspection_date`` and ``slot``.

    Args:
        rows: list of dicts; each should carry ``city`` and ``address`` keys
            (missing/blank values fall back to a single '_' cluster).
        start_date / end_date: the batch scheduling window.
        slots_per_day: slots per day (default 2 = AM + PM).

    Returns:
        A new list of dicts (same order as ``rows``) each augmented with
        ``inspection_date`` (datetime.date) and ``slot`` ('am'/'pm').

    Raises:
        ScheduleCapacityError: when len(rows) exceeds available slots.
    """
    if not rows:
        return []

    slot_seq = build_slot_sequence(start_date, end_date, slots_per_day)
    if len(rows) > len(slot_seq):
        raise ScheduleCapacityError(
            f'{len(rows)} sites do not fit in {(end_date - start_date).days + 1} day(s) '
            f'x {slots_per_day} slot(s) = {len(slot_seq)} slot(s). Widen the date range.'
        )

    # Group row indexes by city, preserving first-seen city order.
    city_groups = OrderedDict()
    for index, row in enumerate(rows):
        city_groups.setdefault(_norm(row.get('city')), []).append(index)

    assignments = [None] * len(rows)
    cursor = 0
    for city_indexes in city_groups.values():
        # Within a city, group by normalized address so co-located sites are consecutive.
        address_groups = OrderedDict()
        for index in city_indexes:
            address_groups.setdefault(_norm(rows[index].get('address')), []).append(index)
        for group in address_groups.values():
            for index in group:
                date, slot = slot_seq[cursor]
                cursor += 1
                assignments[index] = (date, slot)

    return [
        {**row, 'inspection_date': assignments[i][0], 'slot': assignments[i][1]}
        for i, row in enumerate(rows)
    ]
