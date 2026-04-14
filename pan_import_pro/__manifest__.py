# -*- coding: utf-8 -*-
{
    'name': "Import Pro",
    'summary': "AI-powered data migration companion for Odoo",
    'description': """
Companion app for AI-driven data import. Tracks import projects,
stores document analyses, and provides approval workflow.
Works with Claude (Code/Co-work) via MCP.
""",
    'author': "Pantalytics",
    'website': "https://pantalytics.com",
    'support': "rutger@pantalytics.com",
    'category': 'Productivity',
    'version': '19.0.1.0.0',
    'license': 'LGPL-3',

    'depends': [
        'contacts',
        'documents',
        'mail',
        'survey',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/import_project_views.xml',
        'views/menu.xml',
    ],

    'installable': True,
    'application': True,
    'auto_install': False,
}
