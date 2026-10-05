# -*- coding: utf-8 -*-
import logging
from datetime import timedelta

from odoo import http, fields
from odoo.http import request

_logger = logging.getLogger(__name__)

DEDUP_WINDOW_SECONDS = 60


class GuestRegistrationController(http.Controller):

    def _get_qr(self, token):
        """Resolve an active QR record from a public token. Never trust anything
        else supplied by the browser for branch resolution."""
        if not token:
            return None
        qr = request.env['otm.guest.qr.code'].sudo().search([
            ('token', '=', token),
            ('active', '=', True),
        ], limit=1)
        return qr or None

    def _config_data(self):
        env = request.env
        categories = env['otm.guest.visit.category'].sudo().search([]).read(['id', 'name', 'code'])
        courses = env['otm.guest.course'].sudo().search([]).read(['id', 'name'])
        positions = env['otm.guest.interview.position'].sudo().search([]).read(['id', 'name'])
        return categories, courses, positions

    @http.route(['/guest/register/<string:token>'], type='http', auth='public',
                website=False, csrf=True, methods=['GET'], sitemap=False)
    def guest_registration_form(self, token, **kw):
        qr = self._get_qr(token)
        if not qr:
            return request.render('guest_tracking.otm_guest_registration_invalid')

        categories, courses, positions = self._config_data()
        values = {
            'branch_name': qr.branch_id.name,
            'token': token,
            'categories': categories,
            'courses': courses,
            'positions': positions,
            'error': False,
            'form_values': {},
        }
        return request.render('guest_tracking.otm_guest_registration_form', values)

    @http.route(['/guest/register/<string:token>'], type='http', auth='public',
                website=False, csrf=True, methods=['POST'], sitemap=False)
    def guest_registration_submit(self, token, **post):
        qr = self._get_qr(token)
        if not qr:
            return request.render('guest_tracking.otm_guest_registration_invalid')

        categories, courses, positions = self._config_data()
        values = {
            'branch_name': qr.branch_id.name,
            'token': token,
            'categories': categories,
            'courses': courses,
            'positions': positions,
            'error': False,
            'form_values': post,
        }

        name = (post.get('name') or '').strip()
        mobile = (post.get('mobile') or '').strip()
        email = (post.get('email') or '').strip()
        place = (post.get('place') or '').strip()
        category_id = post.get('category_id')
        course_id = post.get('course_id')
        position_id = post.get('interview_position_id')
        other_purpose = (post.get('other_purpose') or '').strip()

        # Browser <select>/<input> values always arrive as strings — never
        # trust the type, always coerce ids defensively before browse/search.
        def to_int(val):
            try:
                return int(val)
            except (TypeError, ValueError):
                return False

        category_id = to_int(category_id)
        course_id = to_int(course_id)
        position_id = to_int(position_id)

        errors = []
        if not name:
            errors.append('Name is required.')
        if not mobile:
            errors.append('Mobile number is required.')
        category = request.env['otm.guest.visit.category'].sudo().browse(category_id) if category_id else None
        if not category or not category.exists():
            errors.append('Please select the purpose of your visit.')
            category = None
        if email and '@' not in email:
            errors.append('Please enter a valid email address.')

        if category:
            if category.code == 'admission' and not course_id:
                errors.append('Please select a course.')
            if category.code == 'interview' and not position_id:
                errors.append('Please select the interview position.')
            if category.code == 'other' and not other_purpose:
                errors.append('Please specify your purpose.')

        if errors:
            values['error'] = ' '.join(errors)
            return request.render('guest_tracking.otm_guest_registration_form', values)

        Visitor = request.env['otm.guest.visitor'].sudo()
        Visit = request.env['otm.guest.visit'].sudo()

        visitor = Visitor.find_or_create(name, mobile, email=email, place=place)

        # Prevent accidental double submission (e.g. double-tap / back button)
        window_start = fields.Datetime.now() - timedelta(seconds=DEDUP_WINDOW_SECONDS)
        recent = Visit.search([
            ('visitor_id', '=', visitor.id),
            ('qr_code_id', '=', qr.id),
            ('create_date', '>=', fields.Datetime.to_string(window_start)),
        ], limit=1, order='create_date desc')
        if recent:
            return request.render('guest_tracking.otm_guest_registration_success', {
                'reference': recent.visit_reference,
            })

        vals = {
            'visitor_id': visitor.id,
            'branch_id': qr.branch_id.id,
            'category_id': category.id,
            'course_id': course_id or False,
            'interview_position_id': position_id or False,
            'other_purpose': other_purpose or False,
            'source': 'qr_public',
            'qr_code_id': qr.id,
            'status': 'waiting',
        }
        visit = Visit.create(vals)

        return request.render('guest_tracking.otm_guest_registration_success', {
            'reference': visit.visit_reference,
        })
