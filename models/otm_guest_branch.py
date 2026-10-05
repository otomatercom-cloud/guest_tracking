# -*- coding: utf-8 -*-
from odoo import api, fields, models


class OtmGuestBranch(models.Model):
    _name = 'otm.guest.branch'
    _description = 'Guest Tracking Branch'
    _order = 'sequence, name'

    name = fields.Char(string='Branch Name', required=True, index=True)
    code = fields.Char(string='Branch Code', required=True)
    address = fields.Text(string='Address')
    phone = fields.Char(string='Phone')
    email = fields.Char(string='Email')
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    qr_code_ids = fields.One2many('otm.guest.qr.code', 'branch_id', string='QR Code Lines')
    qr_code_count = fields.Integer(compute='_compute_qr_code_count', string='QR Codes')
    visit_count = fields.Integer(compute='_compute_visit_count', string='Visits')

    _code_uniq = models.Constraint('unique(code)', 'Branch code must be unique.')

    @api.depends('qr_code_ids')
    def _compute_qr_code_count(self):
        for branch in self:
            branch.qr_code_count = len(branch.qr_code_ids)

    def _compute_visit_count(self):
        grouped = self.env['otm.guest.visit']._read_group(
            [('branch_id', 'in', self.ids)], ['branch_id'], ['__count'])
        counts = {branch.id: count for branch, count in grouped}
        for branch in self:
            branch.visit_count = counts.get(branch.id, 0)

    def action_view_qr_codes(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'QR Codes',
            'res_model': 'otm.guest.qr.code',
            'view_mode': 'list,form',
            'domain': [('branch_id', '=', self.id)],
            'context': {'default_branch_id': self.id},
        }

    def action_view_visits(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Visits',
            'res_model': 'otm.guest.visit',
            'view_mode': 'list,form,graph,pivot',
            'domain': [('branch_id', '=', self.id)],
        }
