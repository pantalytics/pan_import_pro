# -*- coding: utf-8 -*-
from odoo import http
from odoo.exceptions import AccessError, MissingError
from odoo.http import request
from odoo.addons.portal.controllers import portal


class ImportPortal(portal.CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if 'import_project_count' in counters:
            values['import_project_count'] = request.env[
                'pan.import.project'
            ].search_count([]) if request.env['pan.import.project'].has_access('read') else 0
        return values

    @http.route(
        ['/my/imports', '/my/imports/page/<int:page>'],
        type='http', auth='user', website=True,
    )
    def portal_my_imports(self, **kw):
        projects = request.env['pan.import.project'].search([])
        values = self._prepare_portal_layout_values()
        values.update({
            'projects': projects,
            'page_name': 'imports',
        })
        return request.render('pan_import_pro.portal_my_imports', values)

    @http.route(
        '/my/import/<int:project_id>',
        type='http', auth='user', website=True,
    )
    def portal_import_project(self, project_id, **kw):
        try:
            project = request.env['pan.import.project'].browse(project_id)
            project.check_access('read')
        except (AccessError, MissingError):
            return request.redirect('/my')

        values = self._prepare_portal_layout_values()
        values.update({
            'project': project,
            'page_name': 'import_project',
        })
        return request.render('pan_import_pro.portal_import_project', values)

    @http.route(
        '/my/import/<int:project_id>/answer',
        type='http', auth='user', website=True, methods=['POST'],
    )
    def portal_answer_questions(self, project_id, **kw):
        try:
            project = request.env['pan.import.project'].browse(project_id)
            project.check_access('write')
        except (AccessError, MissingError):
            return request.redirect('/my')

        for question in project.question_ids:
            if question.question_type == 'multi':
                # Collect checked checkbox values
                selected = []
                for i, option in enumerate(question._get_options_list()):
                    if kw.get(f'answer_{question.id}_{i}'):
                        selected.append(kw[f'answer_{question.id}_{i}'])
                answer = ' | '.join(selected)
            else:
                answer = kw.get(f'answer_{question.id}', '').strip()

            if answer != (question.answer or ''):
                question.sudo().write({'answer': answer})

        return request.redirect(f'/my/import/{project_id}')
