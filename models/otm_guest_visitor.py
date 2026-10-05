# -*- coding: utf-8 -*-
import re

from odoo import api, fields, models


def normalize_mobile(mobile):
    """Strip spaces, hyphens, parentheses and leading zeros/plus formatting noise
    while keeping the full number (including country code) intact."""
    if not mobile:
        return mobile
    cleaned = re.sub(r'[\s\-()]', '', mobile)
    return cleaned


class OtmGuestVisitor(models.Model):
    _name = 'otm.guest.visitor'
    _description = 'Guest / Visitor'
    _order = 'name'

    name = fields.Char(string='Name', required=True, index=True)
    mobile = fields.Char(string='Mobile', required=True, index=True)
    mobile_normalized = fields.Char(string='Mobile (Normalized)', compute='_compute_mobile_normalized',
                                     store=True, index=True)
    email = fields.Char(string='Email')
    place = fields.Char(string='Place')
    company = fields.Char(string='Company')
    notes = fields.Text(string='Notes')
    active = fields.Boolean(default=True)

    visit_ids = fields.One2many('otm.guest.visit', 'visitor_id', string='Visits')
    visit_count = fields.Integer(compute='_compute_visit_stats', store=True, string='Total Visits')
    admission_visit_count = fields.Integer(compute='_compute_visit_stats', store=True, string='Admission Visits')
    interview_visit_count = fields.Integer(compute='_compute_visit_stats', store=True, string='Interview Visits')
    enquiry_visit_count = fields.Integer(compute='_compute_visit_stats', store=True, string='Course Enquiries')
    first_visit_date = fields.Date(compute='_compute_visit_stats', store=True, string='First Visit')
    last_visit_date = fields.Date(compute='_compute_visit_stats', store=True, string='Last Visit')

    @api.depends('mobile')
    def _compute_mobile_normalized(self):
        for rec in self:
            rec.mobile_normalized = normalize_mobile(rec.mobile)

    @api.depends('visit_ids.visit_date', 'visit_ids.category_id.code')
    def _compute_visit_stats(self):
        for rec in self:
            visits = rec.visit_ids
            rec.visit_count = len(visits)
            rec.admission_visit_count = len(visits.filtered(lambda v: v.category_id.code == 'admission'))
            rec.interview_visit_count = len(visits.filtered(lambda v: v.category_id.code == 'interview'))
            rec.enquiry_visit_count = len(visits.filtered(lambda v: v.category_id.code == 'course_enquiry'))
            dates = visits.mapped('visit_date')
            rec.first_visit_date = min(dates) if dates else False
            rec.last_visit_date = max(dates) if dates else False

    @api.model
    def find_or_create(self, name, mobile, email=False, place=False):
        """Public-safe: normalize mobile, find existing visitor by it, else create.
        Never returns or exposes other visitors' data beyond the matched record."""
        normalized = normalize_mobile(mobile)
        visitor = self.sudo().search([('mobile_normalized', '=', normalized)], limit=1)
        if visitor:
            update_vals = {}
            if name and name != visitor.name:
                update_vals['name'] = name
            if email and email != visitor.email:
                update_vals['email'] = email
            if place and place != visitor.place:
                update_vals['place'] = place
            if update_vals:
                visitor.sudo().write(update_vals)
            return visitor
        return self.sudo().create({
            'name': name,
            'mobile': mobile,
            'email': email,
            'place': place,
        })

    def action_view_visits(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Visits',
            'res_model': 'otm.guest.visit',
            'view_mode': 'list,form',
            'domain': [('visitor_id', '=', self.id)],
            'context': {'default_visitor_id': self.id},
        }
