# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class OtmGuestVisit(models.Model):
    _name = 'otm.guest.visit'
    _description = 'Guest Visit'
    _order = 'check_in_datetime desc'
    _inherit = ['mail.thread']

    visit_reference = fields.Char(string='Reference', copy=False, readonly=True, default=lambda self: _('New'))

    visitor_id = fields.Many2one('otm.guest.visitor', string='Visitor', required=True, index=True,
                                  ondelete='restrict')
    visitor_name = fields.Char(related='visitor_id.name', string='Visitor Name', store=True)
    visitor_mobile = fields.Char(related='visitor_id.mobile', string='Mobile', store=True)

    branch_id = fields.Many2one('otm.guest.branch', string='Branch', required=True, index=True,
                                 ondelete='restrict')

    visit_date = fields.Date(string='Visit Date', default=fields.Date.context_today, required=True, index=True)
    check_in_datetime = fields.Datetime(string='Check-in', default=fields.Datetime.now, required=True)
    meeting_start_datetime = fields.Datetime(string='Meeting Start')
    check_out_datetime = fields.Datetime(string='Check-out')
    duration = fields.Float(string='Duration (Hours)', compute='_compute_duration', store=True)

    status = fields.Selection([
        ('waiting', 'Waiting'),
        ('meeting', 'Meeting'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='waiting', required=True, index=True, tracking=True)

    category_id = fields.Many2one('otm.guest.visit.category', string='Purpose', required=True, index=True)
    category_code = fields.Char(related='category_id.code', string='Purpose Code', store=True)

    course_id = fields.Many2one('otm.guest.course', string='Course', index=True)
    interview_position_id = fields.Many2one('otm.guest.interview.position', string='Interview Position', index=True)
    other_purpose = fields.Char(string='Other Purpose (Details)')

    notes = fields.Text(string='Notes')
    receptionist_id = fields.Many2one('res.users', string='Receptionist', default=lambda self: self.env.user)
    source = fields.Selection([
        ('qr_public', 'QR / Public Registration'),
        ('backend', 'Backend Walk-in'),
    ], string='Source', default='backend', required=True)
    qr_code_id = fields.Many2one('otm.guest.qr.code', string='QR Code')

    company_id = fields.Many2one('res.company', related='branch_id.company_id', store=True, string='Company')

    # Future integration hook (per spec: do not build a duplicate admission/recruitment
    # system here, and do not add an unnecessary hard dependency on crm/hr_recruitment).
    # Kept as a free-text reference so a later, purpose-built integration module can
    # populate it once the actual target model is decided.
    external_lead_reference = fields.Char(
        string='Related Lead/Admission Reference',
        help='Optional reference to a future CRM lead or admission record, '
             'to be wired up by a dedicated integration module.')

    _reference_uniq = models.Constraint('unique(visit_reference)', 'Visit reference must be unique.')

    @api.depends('check_in_datetime', 'check_out_datetime')
    def _compute_duration(self):
        for rec in self:
            if rec.check_in_datetime and rec.check_out_datetime:
                delta = rec.check_out_datetime - rec.check_in_datetime
                rec.duration = round(delta.total_seconds() / 3600.0, 2)
            else:
                rec.duration = 0.0

    @api.constrains('category_id', 'course_id', 'interview_position_id', 'other_purpose')
    def _check_purpose_requirements(self):
        for rec in self:
            code = rec.category_id.code
            if code == 'admission' and not rec.course_id:
                raise ValidationError(_('Course is required when the purpose is Admission.'))
            if code == 'interview' and not rec.interview_position_id:
                raise ValidationError(_('Interview Position is required when the purpose is Interview.'))
            if code == 'other' and not rec.other_purpose:
                raise ValidationError(_('Please specify the purpose when Other is selected.'))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('visit_reference') or vals.get('visit_reference') == _('New'):
                vals['visit_reference'] = self.env['ir.sequence'].next_by_code('otm.guest.visit') or _('New')
        return super().create(vals_list)

    def action_start_meeting(self):
        for rec in self:
            if rec.status != 'waiting':
                raise UserError(_('Only a visit that is Waiting can be moved to Meeting.'))
            rec.write({
                'status': 'meeting',
                'meeting_start_datetime': fields.Datetime.now(),
            })

    def action_complete_visit(self):
        for rec in self:
            if rec.status not in ('waiting', 'meeting'):
                raise UserError(_('Only a Waiting or Meeting visit can be completed.'))
            rec.write({
                'status': 'completed',
                'check_out_datetime': fields.Datetime.now(),
            })

    def action_cancel_visit(self):
        for rec in self:
            if rec.status == 'completed':
                raise UserError(_('A completed visit cannot be cancelled.'))
            rec.status = 'cancelled'

    def action_reset_to_waiting(self):
        for rec in self:
            if rec.status == 'completed':
                raise UserError(_('A completed visit cannot be reverted to Waiting.'))
            rec.write({'status': 'waiting', 'meeting_start_datetime': False})

    # ---------------------------------------------------------------
    # Dashboard / analytics aggregation helpers (used by both the
    # reception dashboard client action and the analytics dashboard)
    # ---------------------------------------------------------------
    @api.model
    def get_reception_dashboard_data(self):
        today = fields.Date.context_today(self)
        domain = [('visit_date', '=', today)]
        visits = self.search(domain)
        kpi = {
            'today_total': len(visits),
            'waiting': len(visits.filtered(lambda v: v.status == 'waiting')),
            'meeting': len(visits.filtered(lambda v: v.status == 'meeting')),
            'completed': len(visits.filtered(lambda v: v.status == 'completed')),
            'admissions': len(visits.filtered(lambda v: v.category_code == 'admission')),
            'interviews': len(visits.filtered(lambda v: v.category_code == 'interview')),
            'course_enquiries': len(visits.filtered(lambda v: v.category_code == 'course_enquiry')),
            'other': len(visits.filtered(lambda v: v.category_code not in
                                          ('admission', 'interview', 'course_enquiry'))),
        }
        visitor_lines = []
        for v in visits.sorted(key=lambda r: r.check_in_datetime or fields.Datetime.now(), reverse=True):
            visitor_lines.append({
                'id': v.id,
                'time': fields.Datetime.to_string(v.check_in_datetime) if v.check_in_datetime else '',
                'visitor': v.visitor_name,
                'mobile': v.visitor_mobile,
                'branch': v.branch_id.name,
                'purpose': v.category_id.name,
                'course': v.course_id.name or '',
                'status': v.status,
                'receptionist': v.receptionist_id.name or '',
            })
        return {'kpi': kpi, 'visits': visitor_lines}

    @api.model
    def get_analytics_dashboard_data(self, date_from=False, date_to=False):
        domain = []
        if date_from:
            domain.append(('visit_date', '>=', date_from))
        if date_to:
            domain.append(('visit_date', '<=', date_to))
        visits = self.search(domain)
        avg_duration = 0.0
        completed = visits.filtered(lambda v: v.status == 'completed' and v.duration)
        if completed:
            avg_duration = round(sum(completed.mapped('duration')) / len(completed), 2)

        def count_by(field_name):
            result = {}
            field = self._fields[field_name]
            for v in visits:
                value = v[field_name]
                if field.type == 'many2one':
                    key = value.name if value else _('Undefined')
                elif field.type == 'selection':
                    key = dict(field.selection).get(value, value) if value else _('Undefined')
                else:
                    key = value or _('Undefined')
                result[key] = result.get(key, 0) + 1
            return [{'label': k, 'value': val} for k, val in sorted(result.items(), key=lambda x: -x[1])]

        return {
            'kpi': {
                'total_visitors': len(visits.mapped('visitor_id')),
                'total_visits': len(visits),
                'admissions': len(visits.filtered(lambda v: v.category_code == 'admission')),
                'interviews': len(visits.filtered(lambda v: v.category_code == 'interview')),
                'course_enquiries': len(visits.filtered(lambda v: v.category_code == 'course_enquiry')),
                'other': len(visits.filtered(lambda v: v.category_code not in
                                              ('admission', 'interview', 'course_enquiry'))),
                'avg_duration': avg_duration,
            },
            'by_branch': count_by('branch_id'),
            'by_purpose': count_by('category_id'),
            'by_course': count_by('course_id'),
            'by_status': count_by('status'),
        }
