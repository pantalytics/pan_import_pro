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
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('in_progress', 'In Progress'),
            ('review', 'Review'),
            ('done', 'Done'),
        ],
        default='draft',
        required=True,
        tracking=True,
    )
    notes = fields.Html(
        string="Notes",
        help="Free-form notes about this import project.",
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

    # --- Import plan (per model, not per record) ---
    plan_ids = fields.One2many(
        'pan.import.plan',
        'project_id',
        string="Import Plan",
    )

    # --- Import log (results) ---
    log_ids = fields.One2many(
        'pan.import.log',
        'project_id',
        string="Import Log",
    )

    @api.depends('question_ids.state')
    def _compute_open_question_count(self):
        for project in self:
            project.open_question_count = len(
                project.question_ids.filtered(lambda q: q.state == 'open')
            )

    # --- Actions ---

    def action_start(self):
        self.ensure_one()
        self.state = 'in_progress'

    def action_submit_for_review(self):
        self.ensure_one()
        if not self.plan_ids:
            raise UserError(_("Add an import plan before submitting for review."))
        self.state = 'review'

    def action_approve(self):
        self.ensure_one()
        if self.open_question_count:
            raise UserError(_(
                "Answer all open questions before approving. "
                "%(count)s question(s) still open.",
                count=self.open_question_count,
            ))
        self.state = 'done'

    def action_reopen(self):
        self.ensure_one()
        self.state = 'in_progress'


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
    question_type = fields.Selection(
        selection=[
            ('open', 'Open'),
            ('single', 'Single Choice'),
            ('multi', 'Multiple Choice'),
        ],
        default='open',
        required=True,
        string="Type",
    )
    question = fields.Text(
        string="Question",
        required=True,
    )
    options = fields.Text(
        string="Options",
        help="One option per line. Used for single/multiple choice questions.",
    )
    answer = fields.Text(
        string="Answer",
    )
    source_document_id = fields.Many2one(
        'documents.document',
        string="Source Document",
        ondelete='set null',
    )
    source = fields.Char(
        string="Source Detail",
        help="Additional context: sheet name, column, row range.",
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

    def _get_options_list(self):
        """Return options as a list of strings."""
        if not self.options:
            return []
        return [o.strip() for o in self.options.strip().split('\n') if o.strip()]

    @api.depends('answer')
    def _compute_state(self):
        for question in self:
            question.state = 'answered' if question.answer else 'open'


class ImportPlan(models.Model):
    _name = 'pan.import.plan'
    _description = 'Import Plan'
    _order = 'sequence, id'

    project_id = fields.Many2one(
        'pan.import.project',
        required=True,
        ondelete='cascade',
    )
    sequence = fields.Integer(default=10)
    model_name = fields.Char(
        string="Odoo Model",
        required=True,
        help="e.g. res.partner, product.template",
    )
    description = fields.Text(
        string="Description",
        help="What will be imported and from which source.",
    )
    record_count = fields.Integer(
        string="Records",
        help="How many records will be created or updated.",
    )
    action = fields.Selection(
        selection=[
            ('create', 'Create'),
            ('update', 'Update'),
            ('create_update', 'Create & Update'),
        ],
        default='create',
    )
    state = fields.Selection(
        selection=[
            ('planned', 'Planned'),
            ('done', 'Done'),
            ('error', 'Error'),
        ],
        default='planned',
    )
    notes = fields.Text(
        string="Notes",
        help="Mapping details, field decisions, or issues.",
    )


class ImportLog(models.Model):
    _name = 'pan.import.log'
    _description = 'Import Log'
    _order = 'create_date desc'

    project_id = fields.Many2one(
        'pan.import.project',
        required=True,
        ondelete='cascade',
    )
    model_name = fields.Char(string="Odoo Model")
    records_created = fields.Integer(string="Created")
    records_updated = fields.Integer(string="Updated")
    records_failed = fields.Integer(string="Failed")
    summary = fields.Text(
        string="Summary",
        help="What happened during this import batch.",
    )
    error_details = fields.Text(
        string="Errors",
        help="Details of any errors encountered.",
    )
