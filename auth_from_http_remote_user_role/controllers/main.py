# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import http
from odoo.http import request

from odoo.addons.auth_from_http_remote_user.controllers import main

import logging

_logger = logging.getLogger(__name__)


class Home(main.Home):

    _REMOTE_USER_ROLE = 'HTTP_USER_ROLES'
    _REMOTE_USER_ROLE_SEPARATOR = ','

    def _get_http_role_codes(self):
        """Return role codes from HTTP header.

        Return in a list the user role codes found in the HTTP
        header using the field and separator predefined.
        """
        roles = []
        headers = http.request.httprequest.headers.environ
        roles_in_header = headers.get(self._REMOTE_USER_ROLE, None)
        if roles_in_header:
            roles = roles_in_header.split(self._REMOTE_USER_ROLE_SEPARATOR)
        return roles

    def logging_http_remote_user(self, env, user):
        """Update roles assigned to user

        Read roles codes from the http header and compare with the actual roles
        of the logging user. If there is a difference, changes are applied.
        """
        new_roles = set()
        existing_roles = set(user.role_line_ids.mapped('role_id').ids)
        role_codes = self._get_http_role_codes()
        if role_codes:
            new_roles = set(
                request.env['res.users.role'].sudo().search(
                    [('user_role_code', 'in', role_codes)]).ids)
        roles2add = list(new_roles.difference(existing_roles))
        roles2remove = list(existing_roles.difference(new_roles))
        role_lines = env['res.users.role.line']
        if roles2add:
            for role_id in roles2add:
                role_lines.create({'user_id': user.id, 'role_id': role_id})
        if roles2remove:
            role_lines.search([
                ('user_id', '=', user.id),
                ('role_id', 'in', roles2remove)]).unlink()
        return super().logging_http_remote_user(env, user)
