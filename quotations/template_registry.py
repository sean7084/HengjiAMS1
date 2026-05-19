from django.utils.translation import gettext_lazy as _

DEFAULT_QUOTATION_TEMPLATE = 'v2_full'

PROFILE_V2 = 'v2'
PROFILE_V1 = 'v1'

_TEMPLATE_DEFINITIONS = {
    'v2_full': {
        'code': 'v2_full',
        'label': _('V2 Full'),
        'template_path': 'quotations/template_v2_full.html',
        'profile': PROFILE_V2,
    },
    'v2_mini': {
        'code': 'v2_mini',
        'label': _('V2 Mini'),
        'template_path': 'quotations/template_v2_mini.html',
        'profile': PROFILE_V2,
    },
    'v1': {
        'code': 'v1',
        'label': _('V1'),
        'template_path': 'quotations/template_v1.html',
        'profile': PROFILE_V1,
    },
}

_FORM_PROFILE_DEFINITIONS = {
    PROFILE_V2: {
        'code': PROFILE_V2,
        'show_tax_input': True,
        'show_user_brand': True,
        'show_user_name': True,
        'item_headers': [
            {'key': 'item', 'label': _('Item')},
            {'key': 'quantity', 'label': _('Qty')},
            {'key': 'unit', 'label': _('Unit')},
            {'key': 'unit_price', 'label': _('Unit Price')},
            {'key': 'tax_rate', 'label': _('Tax %')},
            {'key': 'tax_amount', 'label': _('Tax')},
            {'key': 'line_total', 'label': _('Line Total')},
            {'key': 'user_brand', 'label': _('User Brand')},
            {'key': 'user_name', 'label': _('User')},
        ],
    },
    PROFILE_V1: {
        'code': PROFILE_V1,
        'show_tax_input': False,
        'show_user_brand': False,
        'show_user_name': False,
        'item_headers': [
            {'key': 'index', 'label': _('Item #')},
            {'key': 'part_no', 'label': _('Part No.')},
            {'key': 'brand_name', 'label': _('Brand')},
            {'key': 'description', 'label': _('Description')},
            {'key': 'unit', 'label': _('Unit')},
            {'key': 'price', 'label': _('Price')},
            {'key': 'quantity', 'label': _('Qty')},
            {'key': 'amount', 'label': _('Amount (RMB)')},
        ],
    },
}

QUOTATION_TEMPLATE_CHOICES = [
    (definition['code'], definition['label'])
    for definition in _TEMPLATE_DEFINITIONS.values()
]


def get_quotation_template_choices():
    return QUOTATION_TEMPLATE_CHOICES


def get_quotation_template_definition(template_code):
    if template_code in _TEMPLATE_DEFINITIONS:
        return _TEMPLATE_DEFINITIONS[template_code]
    return _TEMPLATE_DEFINITIONS[DEFAULT_QUOTATION_TEMPLATE]


def get_form_profile_definition(profile_code):
    return _FORM_PROFILE_DEFINITIONS[profile_code]


def get_form_profile_for_template(template_code):
    template_definition = get_quotation_template_definition(template_code)
    return get_form_profile_definition(template_definition['profile'])


def get_serializable_template_definitions():
    serialized = {}
    for template_code, definition in _TEMPLATE_DEFINITIONS.items():
        profile = get_form_profile_definition(definition['profile'])
        serialized[template_code] = {
            'code': template_code,
            'label': str(definition['label']),
            'template_path': definition['template_path'],
            'profile': profile['code'],
            'show_tax_input': profile['show_tax_input'],
            'show_user_brand': profile['show_user_brand'],
            'show_user_name': profile['show_user_name'],
            'item_headers': [
                {'key': header['key'], 'label': str(header['label'])}
                for header in profile['item_headers']
            ],
        }
    return serialized
