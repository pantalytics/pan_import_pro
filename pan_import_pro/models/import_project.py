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
            ('done', 'Done'),
        ],
        default='draft',
        required=True,
        tracking=True,
    )

    # --- Documents ---
    folder_id = fields.Many2one(
        'documents.document',
        string="Documents Folder",
        domain=[('type', '=', 'folder')],
    )

    # --- Surveys (questions for client, multiple rounds) ---
    survey_ids = fields.Many2many(
        'survey.survey',
        string="Questionnaires",
    )

    # --- Import plan ---
    plan_ids = fields.One2many(
        'pan.import.plan',
        'project_id',
        string="Import Plan",
    )

    # --- Import log ---
    log_ids = fields.One2many(
        'pan.import.log',
        'project_id',
        string="Import Log",
    )


    # --- Actions ---

    def action_start(self):
        """Start the project: create folder."""
        self.ensure_one()
        if not self.folder_id:
            self.folder_id = self.env['documents.document'].create({
                'name': self.name,
                'type': 'folder',
            })
            self.env['documents.document'].create({
                'name': 'Origineel',
                'type': 'folder',
                'folder_id': self.folder_id.id,
            })
        self.state = 'in_progress'

    def action_new_survey(self):
        """Create a new survey round and add it to the project."""
        self.ensure_one()
        round_nr = len(self.survey_ids) + 1
        survey = self.env['survey.survey'].create({
            'title': f'{self.name} — Ronde {round_nr}',
            'description': '<p>We hebben een aantal vragen over je data. '
                           'Beantwoord ze zodat we verder kunnen met de import.</p>',
            'description_done': '<p>Bedankt! We verwerken je antwoorden en komen bij je terug.</p>',
            'survey_type': 'survey',
            'access_mode': 'public',
            'questions_layout': 'one_page',
        })
        self.survey_ids = [fields.Command.link(survey.id)]
        # Open the survey form so the consultant can add questions
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'survey.survey',
            'res_id': survey.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_open_folder(self):
        """Open the Documents folder."""
        self.ensure_one()
        if not self.folder_id:
            return
        return {
            'type': 'ir.actions.act_url',
            'url': self.folder_id.access_url,
            'target': 'new',
        }

    def action_mark_done(self):
        self.ensure_one()
        self.state = 'done'

    def action_reopen(self):
        self.ensure_one()
        self.state = 'in_progress'


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
    notes = fields.Html(
        string="Notes",
        help="Mapping details, field decisions, or issues.",
    )


class ImportLog(models.Model):
    _name = 'pan.import.log'
    _description = 'Import Log'
    _inherit = ['mail.thread']
    _order = 'create_date desc'

    name = fields.Char(
        string="Title",
        compute='_compute_name',
        store=True,
    )
    project_id = fields.Many2one(
        'pan.import.project',
        required=True,
        ondelete='cascade',
    )
    model_name = fields.Char(string="Odoo Model")
    records_created = fields.Integer(string="Created")
    records_updated = fields.Integer(string="Updated")
    records_failed = fields.Integer(string="Failed")
    notes = fields.Html(
        string="Notes",
        help="Details of what was imported, issues encountered, etc.",
    )

    @api.depends('model_name', 'records_created', 'records_updated')
    def _compute_name(self):
        for log in self:
            parts = []
            if log.model_name:
                parts.append(log.model_name)
            counts = []
            if log.records_created:
                counts.append(f'{log.records_created} created')
            if log.records_updated:
                counts.append(f'{log.records_updated} updated')
            if log.records_failed:
                counts.append(f'{log.records_failed} failed')
            if counts:
                parts.append(', '.join(counts))
            log.name = ' — '.join(parts) if parts else _("New Log Entry")
