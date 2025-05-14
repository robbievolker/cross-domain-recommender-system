from app.models import *
def get_item(item_id, item_type):
    if item_type == "book":
        item = Books.query.filter_by(id=item_id).first()
    elif item_type == "film":
        item = Films.query.filter_by(id=item_id).first()
    else:
        item = Games.query.filter_by(id=item_id).first()
    return item

def get_item_tags(item_id, item_type):
    tag_dict = {}
    item_tags = ItemTags.query.filter_by(item_id=item_id, item_type=item_type).all()
    for tag in item_tags:
        tag_dict[tag.tag_id] = tag.count
    return tag_dict

