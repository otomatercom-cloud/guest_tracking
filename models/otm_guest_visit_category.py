# -*- coding: utf-8 -*-
from odoo import fields, models


class OtmGuestVisitCategory(models.Model):
    _name = 'otm.guest.visit.category'
    _description = 'Guest Tracking Visit Purpose'
    _order = 'sequence, name'

    name = fields.Char(string='Purpose', required=True, index=True)
    code = fields.Char(string='Code', required=True,
                        help='Internal code: admission / interview / course_enquiry / '
                             'business_meeting / vendor_partner / employee_meeting / other')
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)

    _code_uniq = models.Constraint('unique(code)', 'Purpose code must be unique.')
