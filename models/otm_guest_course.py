# -*- coding: utf-8 -*-
from odoo import fields, models


class OtmGuestCourse(models.Model):
    _name = 'otm.guest.course'
    _description = 'Guest Tracking Course'
    _order = 'sequence, name'

    name = fields.Char(string='Course Name', required=True, index=True)
    code = fields.Char(string='Course Code')
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)
