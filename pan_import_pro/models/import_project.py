# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ImportProject(models.Model):
    _name = 'pan.import.project'
    _description = 'Import Project'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(
        string="Project Name",
        required=True,
        tracking=True,
        default=lambda self: _("New Import"),
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('in_progress', 'In Progress'),
            ('review', 'Review'),
            ('approved', 'Approved'),
            ('importing', 'Importing'),
            ('done', 'Done'),
        ],
        default='draft',
        required=True,
        tracking=True,
    )

    # --- Company profile (related to res.company → res.partner) ---
    company_partner_id = fields.Many2one(
        related='company_id.partner_id',
        string="Company",
    )
    company_id = fields.Many2one(
        'res.company',
        default=lambda self: self.env.company,
        required=True,
    )
    company_website = fields.Char(
        related='company_partner_id.website',
        readonly=False,
        string="Website",
    )
    company_notes = fields.Html(
        related='company_partner_id.comment',
        readonly=False,
        string="Company Profile",
    )

    # --- Documents ---
    folder_id = fields.Many2one(
        'documents.document',
        string="Documents Folder",
        domain=[('type', '=', 'folder')],
    )
    import_document_ids = fields.One2many(
        'pan.import.document',
        'project_id',
        string="Documents",
    )
    source_file_count = fields.Integer(
        compute='_compute_source_file_count',
    )

    # --- Questions (Claude asks, client answers) ---
    question_ids = fields.One2many(
        'pan.import.question',
        'project_id',
        string="Questions",
    )
    open_question_count = fields.Integer(
        compute='_compute_open_question_count',
    )

    # --- Import plan ---
    line_ids = fields.One2many(
        'pan.import.line',
        'project_id',
        string="Import Lines",
    )
    records_to_create = fields.Integer(compute='_compute_stats')
    records_to_update = fields.Integer(compute='_compute_stats')
    records_to_skip = fields.Integer(compute='_compute_stats')

    color = fields.Integer()

    @api.depends('import_document_ids')
    def _compute_source_file_count(self):
        for project in self:
            project.source_file_count = len(project.import_document_ids)

    @api.depends('question_ids.state')
    def _compute_open_question_count(self):
        for project in self:
            project.open_question_count = len(
                project.question_ids.filtered(lambda q: q.state == 'open')
            )

    @api.depends('line_ids.action')
    def _compute_stats(self):
        for project in self:
            lines = project.line_ids
            project.records_to_create = len(lines.filtered(lambda l: l.action == 'create'))
            project.records_to_update = len(lines.filtered(lambda l: l.action == 'update'))
            project.records_to_skip = len(lines.filtered(lambda l: l.action == 'skip'))

    # --- Actions ---

    def action_start(self):
        self.ensure_one()
        if not self.folder_id:
            self.folder_id = self.env['documents.document'].create({
                'name': self.name,
                'type': 'folder',
            })
        self.state = 'in_progress'

    def action_open_documents(self):
        """Open the Documents folder for this project."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': f'/odoo/documents/{self.folder_id.access_token}',
            'target': 'new',
        }

    def action_sync_documents(self):
        """Sync documents from the folder into import_document_ids."""
        self.ensure_one()
        if not self.folder_id:
            return
        docs = self.env['documents.document'].search([
            ('folder_id', '=', self.folder_id.id),
            ('type', '!=', 'folder'),
        ])
        existing = self.import_document_ids.mapped('document_id')
        for doc in docs - existing:
            self.env['pan.import.document'].create({
                'project_id': self.id,
                'document_id': doc.id,
            })

    def action_submit_for_review(self):
        self.ensure_one()
        self.state = 'review'

    def action_approve(self):
        self.ensure_one()
        if not self.line_ids:
            raise UserError(_("No import lines to approve."))
        self.state = 'approved'

    def action_import(self):
        self.ensure_one()
        self.state = 'importing'
        for line in self.line_ids.filtered(lambda l: l.action in ('create', 'update')):
            line.state = 'done'
        self.state = 'done'
        self.message_post(body=_(
            "Import completed: %(created)s created, %(updated)s updated.",
            created=self.records_to_create,
            updated=self.records_to_update,
        ))

    def action_back_to_progress(self):
        self.ensure_one()
        self.state = 'in_progress'


class ImportDocument(models.Model):
    _name = 'pan.import.document'
    _description = 'Import Document'
    _order = 'name'

    project_id = fields.Many2one(
        'pan.import.project',
        required=True,
        ondelete='cascade',
    )
    document_id = fields.Many2one(
        'documents.document',
        required=True,
        ondelete='cascade',
    )
    name = fields.Char(
        related='document_id.name',
        string="File",
    )
    mimetype = fields.Char(
        related='document_id.attachment_id.mimetype',
        string="Type",
    )
    analysis = fields.Html(
        string="Analysis",
        help="What was found: record counts, data preview, quality issues.",
    )
    instructions = fields.Text(
        string="Instructions",
        help="How should this document be processed? Override AI decisions here.",
    )


class ImportQuestion(models.Model):
    _name = 'pan.import.question'
    _description = 'Import Question'
    _order = 'state desc, sequence, id'

    project_id = fields.Many2one(
        'pan.import.project',
        required=True,
        ondelete='cascade',
    )
    sequence = fields.Integer(default=10)
    question = fields.Text(
        string="Question",
        required=True,
    )
    answer = fields.Text(
        string="Answer",
    )
    source = fields.Char(
        string="Source",
        help="Where this question came from (file, sheet, field).",
    )
    state = fields.Selection(
        selection=[
            ('open', 'Open'),
            ('answered', 'Answered'),
        ],
        default='open',
        compute='_compute_state',
        store=True,
    )

    @api.depends('answer')
    def _compute_state(self):
        for question in self:
            question.state = 'answered' if question.answer else 'open'


class ImportLine(models.Model):
    _name = 'pan.import.line'
    _description = 'Import Line'
    _order = 'sequence, id'

    project_id = fields.Many2one(
        'pan.import.project',
        required=True,
        ondelete='cascade',
    )
    sequence = fields.Integer(default=10)
    model_name = fields.Char(string="Odoo Model")
    external_id = fields.Char(string="External ID")
    record_name = fields.Char(string="Record")
    action = fields.Selection(
        selection=[
            ('create', 'Create'),
            ('update', 'Update'),
            ('skip', 'Skip'),
        ],
    )
    state = fields.Selection(
        selection=[
            ('pending', 'Pending'),
            ('done', 'Done'),
            ('error', 'Error'),
        ],
        default='pending',
    )
    error_message = fields.Text()
    data_preview = fields.Text(string="Data")
