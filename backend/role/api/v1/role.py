from typing import List

from flask.views import MethodView
from flask_jwt_extended import jwt_required

from backend.role.domain import Role
from backend.role.schema.role import (

    RoleCreateSchema,
    RoleListSchema,
    RoleQueryArgSchema,
    RoleSchema,
    RoleUpdateSchema,
)
from backend.role.service import role_service
from kit.schema.base import RespSchema
from kit.util.blueprint import APIBlueprint

blp = APIBlueprint('roles', 'roles', url_prefix='/')


@blp.route('/')
class RoleAPI(MethodView):
    """角色管理API"""

    decorators = [jwt_required()]

    @blp.arguments(RoleQueryArgSchema, location='query')
    @blp.response(RoleListSchema)
    def get(self, args: dict):
        """角色管理 查看角色列表"""
        return role_service.list(args)

    @blp.arguments(RoleCreateSchema)
    @blp.response(RoleSchema)
    def post(self, role: Role):
        """角色管理 创建角色"""
        return role_service.create(role)

@blp.route('/role_list')
class RoleListAPI(MethodView):
    """角色管理API"""

    decorators = [jwt_required()]

    @blp.response()
    def get(self, ):
        """角色管理 查看角色列表"""
        return role_service.role_list()

@blp.route('/<int:role_id>')
class RoleByIDAPI(MethodView):
    decorators = [jwt_required()]

    @blp.response(RoleSchema)
    def get(self, role_id: int):
        """角色管理 查看角色详情"""
        return role_service.get(role_id)

    @blp.arguments(RoleUpdateSchema)
    @blp.response(RoleSchema)
    def put(self, role: Role, role_id: int):
        """角色管理 编辑角色"""
        return role_service.update(role_id, role)

    @blp.response(RespSchema)
    def delete(self, role_id: int):
        """角色管理 删除角色信息"""
        return role_service.delete(role_id)

