from bson import ObjectId
from flask import Flask, request, abort
from flask import render_template
from flask import jsonify
from flask_cors import CORS
from pymongo import MongoClient
from urllib.parse import quote_plus
from dotenv import load_dotenv, dotenv_values

from ClothingItem import ClothingItem

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000"])
load_dotenv()
env_vars = dotenv_values()

db_password = quote_plus(env_vars['DB_PASSWORD'])
db_cluster = env_vars['DB_CLUSTER']
db_name = env_vars['DB_NAME']

uri = f'mongodb+srv://{db_cluster}:{db_password}@{db_cluster}.9tjxmbd.mongodb.net/?retryWrites=true&w=majority'

client = MongoClient(uri)
db = client[db_name]
collection = db['items']
users = db['users']

@app.route('/')
def index():
  return render_template('index.html')

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

@app.route('/api/login', methods=['POST'])
def login():
  data = request.get_json()
  oauth_token = data.get('oauth_token')
  result = users.find_one({'oauth_token': oauth_token})
  if result is None:
    users.insert_one({
      'oauth_token': oauth_token,
    })
  return jsonify({})

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

# GET
@app.route('/api/get_items')
def get_items():
  # TODO: make this only return items that have is_show as true
  try:
    cursor = collection.find({})
    result = []
    for doc in cursor:
      obj_id = doc['_id']
      doc['_id'] = ObjectId.__str__(obj_id)
      result.append(doc)
  except Exception as e:
    print(e)
  return jsonify(result)

@app.errorhandler(404)
def item_not_found(error):
    return jsonify({
      "error": {
        "code": error.code,
        "description": error.description,
      }
    }), 404

# POST
@app.route('/api/add_wears', methods=['POST'])
def add_wears(): #item_id: int, num_wears: Optional[int] = 1): # -> int:
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

# POST
@app.route('/api/add_item', methods=['POST'])
def add_item():
  data = request.get_json()
  item_name = data.get('item_name')
  price_bought = data.get('price_bought')
  company = data.get('company')

  # items = [obj['item_name'] for obj in clothes_db['clothes']]
  # item_ids = [obj['item_id'] for obj in clothes_db['clothes']]
  # if item_name in items:
  #   # TODO: what is criteria for a duplicate item?
  #   return jsonify({
  #     'message': 'message already exists',
  #     })

  clothing_item = ClothingItem(item_name=item_name, price_bought=price_bought,
                    company=company, is_show=True)
  json_item = clothing_item.to_jsonn()
  try:
    result = collection.insert_one(json_item)
    inserted_id = ObjectId.__str__(result.inserted_id)
    return jsonify({'inserted_id': inserted_id})
  except Exception as e:
    print(e)
    raise

# POST
@app.route('/api/delete_item', methods=['POST'])
def delete_item():
  data = request.get_json()
  item_id = data.get('item_id')
  # item = get_item(item_id)
  try:
    collection.update_one(
      filter={'_id': ObjectId(item_id)},
      update={ "$set": {"is_show": False}}
    )
    return jsonify({})
  except Exception as e:
    print(e)
    raise


if __name__ == '__main__':
  app.run(debug=True)
