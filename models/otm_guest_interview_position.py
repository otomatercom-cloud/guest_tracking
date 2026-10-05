# -*- coding: utf-8 -*-
from odoo import fields, models


class OtmGuestInterviewPosition(models.Model):
    _name = 'otm.guest.interview.position'
    _description = 'Guest Tracking Interview Position'
    _order = 'sequence, name'

    name = fields.Char(string='Position Name', required=True, index=True)
    code = fields.Char(string='Position Code')
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)
