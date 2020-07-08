from flask_restful import Resource, reqparse
from models.hotel import HotelModel
from flask_jwt_extended import jwt_required
import sqlite3
from .filtros import consulta_com_cidade, consulta_sem_cidade, normalize_path_params
from models.site import SiteModel

path_params = reqparse.RequestParser()
path_params.add_argument('cidade', type=str)
path_params.add_argument('estrelas_min', type=float)
path_params.add_argument('estrelas_max', type=float)
path_params.add_argument('diaria_min', type=float)
path_params.add_argument('diaria_max', type=float)
path_params.add_argument('limit', type=int)
path_params.add_argument('offset', type=int)


class Hoteis(Resource):
    def get(self):
        connection = sqlite3.connect('flask.db')
        cursor = connection.cursor()

        dados = path_params.parse_args()
        dados_validos = {chave:dados[chave] for chave in dados if dados[chave] is not None}
        parametros = normalize_path_params(**dados_validos)
        if not parametros.get('cidade'):
            tupla = tuple([parametros[chave] for chave in parametros])
            resultado = cursor.execute(consulta_sem_cidade, tupla)
        else:
            tupla = tuple([parametros[chave] for chave in parametros])
            resultado = cursor.execute(consulta_com_cidade, tupla)

        hoteis = []
        for linha in resultado:
            hoteis.append({
                'hotel_id': linha[0],
                'nome': linha[1],
                'estrelas': linha[2],
                'valor_diaria': linha[3],
                'cidade': linha[4],
                'site_id': linha[5]
            })



        return {'hoteis': hoteis}


class Hotel(Resource):
    argumentos = reqparse.RequestParser()
    argumentos.add_argument('nome', type=str, required=True, help="O campo 'nome' precisa estar preenchido.")
    argumentos.add_argument('estrelas', type=int, required=True, help="O campo 'estrelas' precisa estar preenchido.")
    argumentos.add_argument('valor_diaria', type=float, required=True, help="O campo 'valor_diaria' precisa estar preenchido.")
    argumentos.add_argument('cidade', type=str, required=True, help="O campo 'cidade' precisa estar preenchido.")
    argumentos.add_argument('site_id', type=int, required=True, help='Este campo precisa ser preenchido')

    def get(self, hotel_id):
        hotel = HotelModel.find_hotel(hotel_id)
        if hotel:
            return hotel.json()
        return {'message': 'Hotel not Found.'}, 404 # Not Found

    @jwt_required
    def post(self, hotel_id):
        if HotelModel.find_hotel(hotel_id):
            return {'message': f'Hotel id {hotel_id} already exists.'}, 400
        dados = Hotel.argumentos.parse_args()
        hotel = HotelModel(hotel_id, **dados)

        if not SiteModel.find_by_id(dados.get('site_id')):
            return {'message': 'O hotel precisa estar associado a um site válido.'}, 400
        try:
            hotel.save_hotel()
        except:
            return {'message': 'Erro interno, não podemos salvar o hotel.'}, 500
        return hotel.json()

    @jwt_required
    def put(self, hotel_id):
        dados = Hotel.argumentos.parse_args()
        hotel_encontrado = HotelModel.find_hotel(hotel_id)

        if hotel_encontrado:
            hotel_encontrado.update_hotel(**dados)
            hotel_encontrado.save_hotel()
            return hotel_encontrado.json(), 200

        hotel = HotelModel(hotel_id, **dados)
        hotel.save_hotel()

        return hotel.json(), 201 # Created

    @jwt_required
    def delete(self, hotel_id):
        hotel = HotelModel.find_hotel(hotel_id)
        if hotel:
            try:
                hotel.delete_hotel()
            except:
                return {'message': 'Erro ao deletar o Hotel.'}, 500
            return {'message': 'Hotel Deleted.'}
        return {'message': 'Hotel not Found.'}, 404