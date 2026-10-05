# -*- coding: utf-8 -*-
from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestGuestVisit(TransactionCase):

    def setUp(self):
        super().setUp()
        self.branch = self.env['otm.guest.branch'].create({'name': 'Kochi', 'code': 'KCH1'})
        self.visitor = self.env['otm.guest.visitor'].create({'name': 'Rahul', 'mobile': '9876543210'})
        self.cat_admission = self.env.ref('guest_tracking.category_admission')
        self.cat_interview = self.env.ref('guest_tracking.category_interview')
        self.cat_other = self.env.ref('guest_tracking.category_other')
        self.course = self.env['otm.guest.course'].create({'name': 'CMA USA'})

    def test_branch_creation(self):
        self.assertTrue(self.branch.id)

    def test_qr_token_generation_and_uniqueness(self):
        Qr = self.env['otm.guest.qr.code']
        qr1 = Qr.create({'name': 'Kochi Reception QR', 'branch_id': self.branch.id})
        qr2 = Qr.create({'name': 'Second QR', 'branch_id': self.branch.id})
        self.assertTrue(qr1.token)
        self.assertNotEqual(qr1.token, qr2.token)
        self.assertNotIn(str(self.branch.id), qr1.token)

    def test_qr_regenerate_invalidates_old(self):
        qr = self.env['otm.guest.qr.code'].create({'name': 'QR', 'branch_id': self.branch.id})
        old_token = qr.token
        qr.action_regenerate_token()
        self.assertNotEqual(qr.token, old_token)

    def test_visit_sequence_generation(self):
        visit = self.env['otm.guest.visit'].create({
            'visitor_id': self.visitor.id,
            'branch_id': self.branch.id,
            'category_id': self.cat_admission.id,
            'course_id': self.course.id,
        })
        self.assertTrue(visit.visit_reference.startswith('GV/'))

    def test_admission_requires_course(self):
        with self.assertRaises(ValidationError):
            self.env['otm.guest.visit'].create({
                'visitor_id': self.visitor.id,
                'branch_id': self.branch.id,
                'category_id': self.cat_admission.id,
            })

    def test_interview_requires_position(self):
        with self.assertRaises(ValidationError):
            self.env['otm.guest.visit'].create({
                'visitor_id': self.visitor.id,
                'branch_id': self.branch.id,
                'category_id': self.cat_interview.id,
            })

    def test_other_requires_other_purpose(self):
        with self.assertRaises(ValidationError):
            self.env['otm.guest.visit'].create({
                'visitor_id': self.visitor.id,
                'branch_id': self.branch.id,
                'category_id': self.cat_other.id,
            })

    def test_status_workflow_and_duration(self):
        visit = self.env['otm.guest.visit'].create({
            'visitor_id': self.visitor.id,
            'branch_id': self.branch.id,
            'category_id': self.cat_admission.id,
            'course_id': self.course.id,
        })
        self.assertEqual(visit.status, 'waiting')
        visit.action_start_meeting()
        self.assertEqual(visit.status, 'meeting')
        self.assertTrue(visit.meeting_start_datetime)
        visit.action_complete_visit()
        self.assertEqual(visit.status, 'completed')
        self.assertTrue(visit.check_out_datetime)
        self.assertGreaterEqual(visit.duration, 0.0)

    def test_completed_cannot_reset_to_waiting(self):
        visit = self.env['otm.guest.visit'].create({
            'visitor_id': self.visitor.id,
            'branch_id': self.branch.id,
            'category_id': self.cat_admission.id,
            'course_id': self.course.id,
        })
        visit.action_start_meeting()
        visit.action_complete_visit()
        with self.assertRaises(UserError):
            visit.action_reset_to_waiting()

    def test_analytics_aggregation(self):
        self.env['otm.guest.visit'].create({
            'visitor_id': self.visitor.id,
            'branch_id': self.branch.id,
            'category_id': self.cat_admission.id,
            'course_id': self.course.id,
        })
        data = self.env['otm.guest.visit'].get_analytics_dashboard_data()
        self.assertGreaterEqual(data['kpi']['total_visits'], 1)
        self.assertTrue(any(row['label'] == self.branch.name for row in data['by_branch']))
