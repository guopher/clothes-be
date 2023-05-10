from typing import Optional

class ClothingItem:
  def __init__(self, item_name: str, price_bought: int, 
      company: Optional[str] = None, num_wears: Optional[int] = 0, is_show: Optional[bool] = True, 
      num_washes: Optional[int] = 0):
    self.item_name = item_name
    self.price_bought = price_bought
    self.company = company
    self.num_wears = num_wears
    self.is_show = is_show
    self.num_washes = num_washes

  def to_jsonn(self) -> dict:
    return {
      "item_name": self.item_name,
      "price_bought": self.price_bought,
      "company": self.company,
      "num_wears": self.num_wears,
      "is_show": self.is_show,
      "num_washes": self.num_washes,
    }