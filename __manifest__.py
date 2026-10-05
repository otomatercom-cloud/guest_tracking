# -*- coding: utf-8 -*-
{
    'name': 'Guest & Visitor Tracking',
    'version': '19.0.1.0.0',
    'category': 'Operations/Reception',
    'summary': 'Multi-branch QR-based guest and visitor tracking for reception desks',
    'description': """
Guest & Visitor Tracking System
================================
Multi-branch reception visitor tracking via branch-specific QR codes.

* Public mobile-friendly QR registration form (no login required)
* Branch resolved securely from QR token — never trusted from the browser
* Automatic guest/visitor de-duplication by mobile number
* Configurable visit purposes, courses, interview positions
* Reception dashboard with live status workflow (Waiting -> Meeting -> Completed)
* Management analytics: branch, purpose, course and time-based reporting
* Printable branch QR report
""",
    'author': 'Otomater',
    'company': 'Otomater',
    'website': 'https://otomater.com',
    'license': 'OPL-1',
    'depends': ['base', 'mail', 'web'],
    'data': [
        'security/guest_security.xml',
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'data/default_data.xml',
        'views/otm_guest_branch_views.xml',
        'views/otm_guest_course_views.xml',
        'views/otm_guest_interview_position_views.xml',
        'views/otm_guest_category_views.xml',
        'views/otm_guest_qr_code_views.xml',
        'views/otm_guest_visitor_views.xml',
        'views/otm_guest_visit_views.xml',
        'views/otm_guest_dashboard_views.xml',
        'views/menus.xml',
        'reports/otm_guest_qr_report.xml',
        'reports/otm_guest_qr_templates.xml',
        'templates/otm_guest_registration_templates.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'guest_tracking/static/src/css/dashboard.css',
            'guest_tracking/static/src/js/reception_dashboard.js',
            'guest_tracking/static/src/xml/reception_dashboard.xml',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
