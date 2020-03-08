import os
import json

from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

# Connection to CORS and database through flask framework
app = Flask(__name__)
setup_db(app)
CORS(app)


'''
    Get a short description of drink menu.
'''
@app.route('/drinks/results', methods=['GET'])
def get_info_drinks():
    drinks = Drink.query.all()
    drinks = [drink.short() for drink in drinks]
    result = {
        'success': True,
        'drinks': drinks
    }
    return jsonify(result)


'''
    Get a long description (detail) of drink menu
'''
@app.route('/drinks-detail', methods=['GET'])
@requires_auth('get:drinks-detail')
def get_details_info_drinks(payload):
    drinks = Drink.query.all()
    drinks = [drink.long() for drink in drinks]
    result = {
        'success': True,
        'drinks': drinks
    }
    return jsonify(result)


'''
    Add a drink in the database.
'''
@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def add_drink(payload):

    # Check to see whether drink's title and recipe are passed or not.
    try:
        # Get information from title and recipe forms in the frontend
        data = request.get_json()['title'] and request.get_json()['recipe']

        if not data:
            abort(400)
    except (TypeError, KeyError):
        abort(400)

    # Get existed titles
    get_title = request.get_json()['title']
    added_title = Drink.query.filter_by(title=get_title).first()

    # Check titles exist or not
    if added_title:
        abort(409)
    else:
        try:
            search_title = request.get_json()['title']
            search_recipe = json.dumps(request.get_json()['recipe'])
            drink = Drink(title=search_title, recipe=search_recipe)
            drink.insert()

            drink_info = Drink.query.filter_by(title=search_title).first()

            return jsonify({
                'success': True,
                'drinks': drink_info.long()
            }), 200
        except Exception:
            abort(422)


'''
    Update Drinks
'''
@app.route('/drinks/<id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def patch_drinks(payload, id):
    drink = Drink.query.filter_by(id=id).first()
    # Check to see whether or not drink is existed
    if not drink:
        abort(404)

    try:
        if not request.get_json()['title'] and request.get_json()['recipe']:
            abort(400)
    except (TypeError, KeyError):
        abort(400)

    # Check to see whether or not it
    search_title = request.get_json()['title']
    exist_drink = Drink.query.filter_by(title=search_title).first()
    if exist_drink:
        abort(409)

    try:
        get_title = request.get_json().get('title')
        get_recipe = request.get_json().get('recipe')
        # Check to see whether or not title and recipe exist.
        if get_title and get_recipe:
            # Assign title to Drink model
            drink.title = request.get_json()['title']

            # Assign recipe to Drink model
            drink.recipe = json.dumps(request.get_json()['recipe'])
        # Call a method from Drink model
        drink.update()
        return jsonify({
            'success': True,
            'drinks': [drink.long()]
        }), 200
    except Exception:
        abort(422)


'''
    Delete
'''
@app.route('/drinks/<id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drinks(payload, id):
    drink = Drink.query.filter_by(id=id).first()
    try:
        drink.delete()

        if not drink:
            abort(404)
        return jsonify({
            'success': True,
            'delete': id
        }), 200
    except Exception:
        abort(422)


'''
    Bad Request
'''
@app.errorhandler(400)
def bad_request(error):
    return jsonify({
        "success": False,
        "error": 400,
        "message": "Bad request"
    }), 400


'''
    Resource not found
'''
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": 404,
        "message": "Resource not found"
    }), 404


'''
    Title Already There
'''
@app.errorhandler(409)
def duplicate(error):
    return jsonify({
        "success": False,
        "error": 409,
        "message": "Title already exists"
    }), 409


'''
    Unprocessable
'''
@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "Unprocessable"
    }), 422


'''
    Authentication Error
'''
@app.errorhandler(AuthError)
def auth_error(error):
    return jsonify({
        "success": False,
        "error": error.status_code,
        "message": error.error
    }), error.status_code