# -*- coding: utf-8 -*-
import re

from odoo.tests.common import HttpCase, tagged


@tagged('post_install', '-at_install')
class TestGuestRegistration(HttpCase):

    def setUp(self):
        super().setUp()
        self.branch = self.env['otm.guest.branch'].create({'name': 'Kochi', 'code': 'KCHX'})
        self.qr = self.env['otm.guest.qr.code'].create({'name': 'QR', 'branch_id': self.branch.id})
        self.category = self.env.ref('guest_tracking.category_course_enquiry')

    def test_invalid_token_rejected(self):
        res = self.url_open('/guest/register/does-not-exist')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Link Not Available', res.content)

    def test_inactive_qr_rejected(self):
        self.qr.active = False
        res = self.url_open('/guest/register/%s' % self.qr.token)
        self.assertIn(b'Link Not Available', res.content)

    def test_valid_qr_form_loads(self):
        res = self.url_open('/guest/register/%s' % self.qr.token)
        self.assertEqual(res.status_code, 200)
        self.assertIn(self.branch.name.encode(), res.content)

    def test_public_submission_creates_visitor_and_visit(self):
        Visitor = self.env['otm.guest.visitor']
        Visit = self.env['otm.guest.visit']
        before_visitors = Visitor.search_count([])
        before_visits = Visit.search_count([])

        # fetch the form first so the test session/cookies are established
        # and a real CSRF token can be extracted for the POST below.
        form_res = self.url_open('/guest/register/%s' % self.qr.token)
        self.assertEqual(form_res.status_code, 200)
        match = re.search(rb'name="csrf_token" value="([^"]+)"', form_res.content)
        self.assertTrue(match, 'CSRF token not found in rendered form')
        csrf_token = match.group(1).decode()

        data = {
            'name': 'Rahul',
            'mobile': '9876543210',
            'email': '',
            'place': '',
            'category_id': str(self.category.id),
            'csrf_token': csrf_token,
        }
        res = self.opener.post(
            self.base_url() + '/guest/register/%s' % self.qr.token, data=data)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(Visitor.search_count([]), before_visitors + 1)
        self.assertEqual(Visit.search_count([]), before_visits + 1)
