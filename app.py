import os
import logging
from bson import ObjectId
from flask import Flask, request, abort, make_response
from flask import render_template
from flask import jsonify
from flask_cors import CORS
from pymongo import MongoClient
from urllib.parse import quote_plus
from dotenv import load_dotenv, dotenv_values
import jwt
from datetime import datetime, timedelta
from urllib.parse import quote_plus
from ClothingItem import ClothingItem

app = Flask(__name__)
CORS(app, origins=['http://localhost:3000', 'https://guopher.github.io/*'])
# load_dotenv()
# env_vars = dotenv_values()

# db_password = quote_plus(env_vars['DB_PASSWORD'])
# db_cluster = env_vars['DB_CLUSTER']
# db_name = env_vars['DB_NAME']
# token_secret = env_vars['TOKEN_SECRET']

db_password = quote_plus(os.environ['DB_PASSWORD'])
db_cluster = quote_plus(os.environ['DB_CLUSTER'])
db_name = quote_plus(os.environ['DB_NAME'])
token_secret = quote_plus(os.environ['TOKEN_SECRET'])
google_client_id = quote_plus(os.environ['GOOGLE_CLIENT_ID'])

uri = f'mongodb+srv://{db_cluster}:{db_password}@{db_cluster}.9tjxmbd.mongodb.net/?retryWrites=true&w=majority'

client = MongoClient(uri)
db = client[db_name]
collection = db['items']
users = db['users']

@app.route('/')
def index():
  return '🥭 Hello World'

@app.route('/api/config')
def config():
  return jsonify({
    'googleClientId': google_client_id
  })

# GET
# TODO: make this an actual call to MongoDB
# def get_item(item_id: int) -> Optional[dict]:
#   items = [obj['item_id'] for obj in clothes_db['clothes']]
#   if item_id not in items:
#     abort(404, 'item not found')

#   applicable_items = list(filter(lambda x: x['item_id'] == item_id, clothes_db['clothes']))
#   if len(applicable_items) > 1:
#     # TODO: this should be a log instead
#     print('error: there are multiple items')

#   return applicable_items[0]

def local_host_encode_cookie_implementation():
    token = 'fake_token'
    response = make_response(jsonify({
      'message': 'logged in successfully',
      'token': token
    }))
    expires = datetime.now() + timedelta(hours=24)
    response.set_cookie(key='token', 
                        value=token, 
                        expires=expires, 
                        domain='.localhost',
                        samesite='Lax',
                        path='/')
    return None


@app.route('/api/login', methods=['POST'])
def login():
  data = request.get_json()
  sub = data.get('sub')
  given_name = data.get('givenName')
  family_name = data.get('familyName')
  google_picture_url = data.get('picture')
  result = users.find_one({'sub': sub})
  payload = {
    'sub': sub,
    'iat': datetime.utcnow(),
    'exp': datetime.utcnow() + timedelta(hours=24),
  }
  token = jwt.encode(payload=payload, key=token_secret, algorithm='HS256')
  if result is None:
    # TODO: abstract this into one method to get the token
    users.insert_one({
      'sub': sub,
      'given_name': given_name,
      'family_name': family_name,
      'google_picture_url': google_picture_url,
    })
    return jsonify({
      'token': token,
    })
  else:
    # TODO: update user properties if we should
    users.update_one({'sub': sub}, {
      "$set": {
        'given_name': given_name,
        'family_name': family_name,
        'google_picture_url': google_picture_url,
      }
    })
    # TODO: do verification that the token they passed in is correct
    return jsonify({ 
      'message': 'verify existing user not implemented yet',
      'token': token,
    })

@app.route('/api/logout', methods=['POST'])
def logout():
  authorization = request.headers.get('Authorization')
  # TODO: make this only return items that have is_show as true
  try:
    token = authorization.split()[1]
    verified = jwt.decode(token, token_secret, algorithms=['HS256'])
    sub = verified.get('sub')
    result = users.find_one({'sub': sub})
    if result is None:
      print('user does not exist')
      # TODO: consult online to determine what to do if invalid access token is passed in
    else:
      # TODO: invalid the token/expire the token
      return jsonify({})
  except Exception as e:
    return jsonify({'error': str(e)})

@app.route('/api/get_user')
def get_user():
  authorization = request.headers.get('Authorization')
  # TODO: make this only return items that have is_show as true
  try:
    token = authorization.split()[1]
    verified = jwt.decode(token, token_secret, algorithms=['HS256'])
    sub = verified.get('sub')
    result = users.find_one({'sub': sub})
    if result is None:
      print('user does not exist')
    else:
      return jsonify({
        'givenName': result.get('given_name'),
        'familyName': result.get('family_name'),
        'google_picture_url': result.get('google_picture_url'),
      })
  except Exception as e:
    return jsonify({'error': str(e)}), 403

@app.route('/api/edit_user', methods=['POST'])
def edit_user():
  data = request.get_json()
  oauth_token = data.get('token')
  given_name = data.get('givenName')
  family_name = data.get('familyName')
  google_picture_url = data.get('picture')
  # TODO: probably do some server side validation on the information, they should pass their token in?
  result = users.find_one({'oauth_token': oauth_token})
  if result:
    users.update_one(
      filter={'oauth_token': oauth_token},
      update={ "$set": {
        "given_name": given_name,
        "family_name": family_name,
        "google_picture_url": google_picture_url,
      }}
    )
  else:
    # TODO: create 403 error handler to let user know they're unauthorized
    print('unauthorized')
  return jsonify({})

@app.route('/api/get_items', methods=['POST'])
def get_items():
  authorization = request.headers.get('Authorization')
  # TODO: make this only return items that have is_show as true
  try:
    token = authorization.split()[1]
    verified = jwt.decode(token, token_secret, algorithms=['HS256'])
    sub = verified.get('sub')
    cursor = collection.find({ 
      'sub': sub,
      'is_show': True,
    })
    result = []
    for doc in cursor:
      obj_id = doc['_id']
      doc['_id'] = ObjectId.__str__(obj_id)
      result.append(doc)
    return jsonify(result)
  except Exception as e:
    return jsonify({'error': str(e)}), 403

@app.errorhandler(404)
def item_not_found(error):
    return jsonify({
      "error": {
        "code": error.code,
        "description": error.description,
      }
    }), 404

@app.route('/api/add_wears', methods=['POST'])
def add_wears():
  data = request.get_json()
  item_id = data.get('item_id')
  new_num_wears = data.get('new_num_wears')
  # TODO: turn this into GET to DB to make sure item exists first

  # item = get_item(item_id)
  # if item is None:
  #   abort(404, "item not found")
  
  try:
    collection.update_one(
      filter={'_id': ObjectId(item_id)},
      update={ "$set": {"num_wears": new_num_wears}}
    )
  except Exception as e:
    print(e)
  return jsonify({})

@app.route('/api/pin_item', methods=['POST'])
def pin_item():
  data = request.get_json()
  item_id = data.get('item_id')
  is_pinned = data.get('is_pinned')
  try:
    collection.update_one(
      filter={'_id': ObjectId(item_id)},
      update={ "$set": {"is_pinned": is_pinned}}
    )
  except Exception as e:
    print(e)
  return jsonify({})

@app.route('/api/add_item', methods=['POST'])
def add_item():
  data = request.get_json()
  item_name = data.get('item_name')
  price_bought = data.get('price_bought')
  company = data.get('company')
  logging.info(f'item_name: ${item_name}, price_bought: ${price_bought}, company: ${company}')

  authorization = request.headers.get('Authorization')
  token = authorization.split()[1]
  verified = jwt.decode(token, token_secret, algorithms=['HS256'])
  sub = verified.get('sub')
  logging.info(f'sub: ${sub}')
  # TODO: do validation on header first before executing any code

  # items = [obj['item_name'] for obj in clothes_db['clothes']]
  # item_ids = [obj['item_id'] for obj in clothes_db['clothes']]
  # if item_name in items:
  #   # TODO: what is criteria for a duplicate item?
  #   return jsonify({
  #     'message': 'message already exists',
  #     })

  clothing_item = ClothingItem(sub=sub, item_name=item_name, price_bought=price_bought,
                    company=company, is_show=True)
  json_item = clothing_item.to_jsonn()
  logging.info('json_item')
  logging.info(json_item)
  try:
    result = collection.insert_one(json_item)
    inserted_id = ObjectId.__str__(result.inserted_id)
    logging.info(f'inserted_id: ${inserted_id}')
    return jsonify({'inserted_id': inserted_id})
  except Exception as e:
    logging.error(e)
    raise

# POST
@app.route('/api/delete_item', methods=['POST'])
def delete_item():
  data = request.get_json()
  item_id = data.get('item_id')
  is_show = data.get('is_show', False)
  # item = get_item(item_id)
  try:
    collection.update_one(
      filter={'_id': ObjectId(item_id)},
      update={ "$set": {"is_show": is_show}}
    )
    return jsonify({})
  except Exception as e:
    print(e)
    raise


if __name__ == '__main__':
  # Use the PORT environment variable if available, or default to 5000
  port = int(os.environ.get('PORT', 5000))
  app.run(host='0.0.0.0', port=port, debug=True)
  # app.run(debug=True)
