from flask import Flask, request, abort
from enum import Enum
from typing import Optional
from typing import Tuple
from flask import render_template
from flask import jsonify
from flask_cors import CORS
# from flask_cors import cross_origin

clothes_db = {
  "clothes": [
    {
      "item_id": 1,
      "item_name": "jacket",
      "price_bought": 120,
      "company": "Mountain Hardwear",
      "num_wears": 60,
      "is_show": True,
      "num_washes": 3,
    },
    {
      "item_id": 2,
      "item_name": "shirt",
      "price_bought": 120,
      "company": "Cotopaxi",
      "num_wears": 50,
      "is_show": True,
      "num_washes": 2,
    },
  ],
}

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000"])

@app.route('/')
def index():
  return render_template('index.html')

class ClothingItem:
  def __init__(self, item_id: int, item_name: str, price_bought: int, 
      company: Optional[str] = None, num_wears: Optional[int] = 0, is_show: Optional[bool] = True, 
      num_washes: Optional[int] = 0):
    self.item_id = item_id
    self.item_name = item_name
    self.price_bought = price_bought
    self.company = company
    self.num_wears = num_wears
    self.is_show = is_show
    self.num_washes = num_washes

  def to_jsonn(self) -> dict:
    return {
      "item_id": self.item_id,
      "item_name": self.item_name,
      "price_bought": self.price_bought,
      "company": self.company,
      "num_wears": self.num_wears,
      "is_show": self.is_show,
      "num_washes": self.num_washes,
    }

# GET
def get_item(item_id: int) -> Optional[dict]:
  items = [obj['item_id'] for obj in clothes_db['clothes']]
  if item_id not in items:
    abort(404, 'item not found')

  applicable_items = list(filter(lambda x: x['item_id'] == item_id, clothes_db['clothes']))
  if len(applicable_items) > 1:
    # TODO: this should be a log instead
    print('error: there are multiple items')

  return applicable_items[0]

# GET
@app.route('/api/get_items')
def get_items():
  return jsonify(clothes_db['clothes'])

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
  item = get_item(item_id)
  if item is None:
    abort(404, "item not found")
  
  # TODO: turn this into a real update with the DB system I'm using
  item['num_wears'] = item['num_wears'] + 1
  return jsonify(item)

# POST
@app.route('/api/add_item', methods=['POST'])
# @cross_origin(origin='localhost', headers=['Content-Type', 'Authorization'])
def add_item():
  data = request.get_json()
  item_name = data.get('item_name')
  price_bought = data.get('price_bought')
  company = data.get('company')

  # items = [obj['item_name'] for obj in clothes_db['clothes']]
  item_ids = [obj['item_id'] for obj in clothes_db['clothes']]
  # if item_name in items:
  #   # TODO: what is criteria for a duplicate item?
  #   return jsonify({
  #     'message': 'message already exists',
  #     })

  clothing_item = ClothingItem(item_id=max(item_ids) + 1, item_name=item_name, price_bought=price_bought,
                    company=company)
  json_item = clothing_item.to_jsonn()
  clothes_db['clothes'].append(json_item)
  return jsonify(json_item)

if __name__ == '__main__':
  app.run(debug=True)

# TODO: 
# FE can call get_item(), which calls BE, which calls DB before returning the actual item to FE
# figure out how the calculation for the price_bought/num_wears is going to be done, on the FE or BE?
