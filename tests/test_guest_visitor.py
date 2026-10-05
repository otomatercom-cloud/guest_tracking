# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestGuestVisitor(TransactionCase):

    def test_find_or_create_new(self):
        visitor = self.env['otm.guest.visitor'].find_or_create('Rahul', '9876543210')
        self.assertTrue(visitor.id)
        self.assertEqual(visitor.mobile_normalized, '9876543210')

    def test_find_or_create_dedup(self):
        Visitor = self.env['otm.guest.visitor']
        v1 = Visitor.find_or_create('Rahul', '9876543210')
        v2 = Visitor.find_or_create('Rahul K', '98765 43210')
        self.assertEqual(v1.id, v2.id, 'Same normalized mobile must resolve to the same visitor')
        self.assertEqual(Visitor.search_count([('mobile_normalized', '=', '9876543210')]), 1)

    def test_repeat_visitor_multiple_visits(self):
        Visitor = self.env['otm.guest.visitor']
        Visit = self.env['otm.guest.visit']
        branch = self.env['otm.guest.branch'].create({'name': 'Kochi', 'code': 'KCH'})
        category = self.env.ref('guest_tracking.category_admission')
        course = self.env['otm.guest.course'].create({'name': 'CMA USA'})

        visitor = Visitor.find_or_create('Rahul', '9876543210')
        for _i in range(3):
            Visit.create({
                'visitor_id': visitor.id,
                'branch_id': branch.id,
                'category_id': category.id,
                'course_id': course.id,
            })
        self.assertEqual(Visitor.search_count([('mobile_normalized', '=', '9876543210')]), 1)
        self.assertEqual(visitor.visit_count, 3)
