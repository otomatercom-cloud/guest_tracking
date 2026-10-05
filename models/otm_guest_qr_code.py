# -*- coding: utf-8 -*-
import base64
import secrets
from io import BytesIO

from odoo import api, fields, models
from odoo.exceptions import UserError


def _generate_token():
    # 32 bytes -> 43-char urlsafe token, cryptographically secure, not derived from branch id
    return secrets.token_urlsafe(32)


class OtmGuestQrCode(models.Model):
    _name = 'otm.guest.qr.code'
    _description = 'Guest Tracking QR Code'
    _order = 'create_date desc'

    name = fields.Char(string='Name', required=True)
    branch_id = fields.Many2one('otm.guest.branch', string='Branch', required=True, index=True, ondelete='cascade')
    token = fields.Char(string='Token', copy=False, index=True)
    registration_url = fields.Char(string='Registration URL', compute='_compute_registration_url')
    qr_image = fields.Binary(string='QR Image', attachment=True)
    active = fields.Boolean(default=True)
    created_at = fields.Datetime(string='Created At', default=fields.Datetime.now, readonly=True)

    _token_uniq = models.Constraint('unique(token)', 'QR token must be unique.')

    @api.depends('token')
    def _compute_registration_url(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url') or ''
        for rec in self:
            rec.registration_url = f"{base_url}/guest/register/{rec.token}" if rec.token else False

    def _generate_qr_image(self):
        self.ensure_one()
        try:
            import qrcode
        except ImportError:
            raise UserError("The 'qrcode' Python library is required to generate QR images. "
                             "Please install it on the server (pip install qrcode).")
        qr = qrcode.QRCode(border=2, box_size=8)
        qr.add_data(self.registration_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color='black', back_color='white')
        buf = BytesIO()
        img.save(buf, format='PNG')
        self.qr_image = base64.b64encode(buf.getvalue())

    def action_generate_qr(self):
        for rec in self:
            if not rec.token:
                rec.token = _generate_token()
            rec._compute_registration_url()
            rec._generate_qr_image()
        return True

    def action_regenerate_token(self):
        """Regenerating invalidates the previous public URL immediately."""
        for rec in self:
            rec.token = _generate_token()
            rec._compute_registration_url()
            rec._generate_qr_image()
        return True

    def action_open_registration_page(self):
        self.ensure_one()
        if not self.token:
            self.action_generate_qr()
        return {
            'type': 'ir.actions.act_url',
            'url': self.registration_url,
            'target': 'new',
        }

    def action_print_qr(self):
        for rec in self:
            if not rec.token or not rec.qr_image:
                rec.action_generate_qr()
        return self.env.ref('guest_tracking.action_report_otm_guest_qr').report_action(self)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('token'):
                vals['token'] = _generate_token()
        records = super().create(vals_list)
        for rec in records:
            rec._generate_qr_image()
        return records
