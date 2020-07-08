from flask_restful import Resource, reqparse
from models.usuario import UserModel
from flask_jwt_extended import create_access_token, jwt_required, get_raw_jwt
from werkzeug.security import safe_str_cmp
from blacklist import BLACKLIST
import traceback
from flask import make_response, render_template

atributos = reqparse.RequestParser()
atributos.add_argument('login', type=str, required=True, help='The field "login" cannot be left blank.')
atributos.add_argument('senha', type=str, required=True, help='The field "password" cannot be left blank.')
atributos.add_argument('email', type=str)
atributos.add_argument('ativado', type=bool)


class Usuario(Resource):
    def get(self, user_id):
        user = UserModel.find_user(user_id)
        if user:
            return user.json()
        return {'message': 'User not Found.'}, 404  # Not Found

    @jwt_required
    def delete(self, user_id):
        user = UserModel.find_user(user_id)
        if user:
            try:
                user.delete_user()
            except:
                return {'message': 'Erro ao deletar o usuário.'}, 500
            return {'message': 'Usuário deletado.'}
        return {'message': 'Usuário não encontrado.'}, 404


class UsuarioRegistro(Resource):
    def post(self):
        dados = atributos.parse_args()

        if not dados.get('email') or dados.get('email') is None:
            return {'message': 'Email field cannot be left blank'}, 400

        if UserModel.find_by_email(dados['email']):
            return {'message': 'This email already exists.'}

        if UserModel.find_by_login(dados['login']):
            return {'message': 'Usuário ja existe.'}

        user = UserModel(**dados)
        user.ativado = False
        try:
            user.save_user()
            user.send_confirmation_email()
        except:
            user.delete_user()
            traceback.print_exc()
            return {'message': 'An internal server error has curred.'}, 500
        return {'message': 'User created successfully'}, 201


class UsuarioLogin(Resource):
    @classmethod
    def post(cls):
        dados = atributos.parse_args()
        user = UserModel.find_by_login(dados['login'])

        if user and safe_str_cmp(user.senha, dados['senha']):
            if user.ativado:
                token_de_acesso = create_access_token(identity=user.user_id)
                return {'access_token': token_de_acesso}, 200
            return {'message': 'User not confirmed.'}, 400
        return {'message': 'The username or password is incorrect.'}, 401 # Unauthozired


class UsuarioLogout(Resource):
    @jwt_required
    def post(self):
        jwt_id = get_raw_jwt()['jti'] # J=JWT T=TOKEN I=IDENTIFIER
        BLACKLIST.add(jwt_id)
        return {'message': 'Logged out Successfully!'}, 200


class UsuarioConfirmacao(Resource):
    @classmethod
    def get(cls, user_id):
        user = UserModel.find_user(user_id)

        if not user:
            return {'message': 'User not found.'}, 404
        user.ativado = True
        user.save_user()
        headers = {'Content-Type': 'text/html'}
        return make_response(render_template('userconfirm.html', email=user.email, usuario=user.login), 200, headers)