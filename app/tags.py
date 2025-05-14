from app.models import *
from flask_login import current_user, login_user, logout_user, login_required
import time
from flask import flash
from profanity_check import predict

def add_tags(data, id, type):
    """
    This function handles adding multiple tags to an item. This function is used by the 'add_book/film/game' endpoints
    when the user submits a form requesting to add new items and tags. This function is also used when a user uses the
    TagsForm on the 'search_results.html' page to add new tags to an item that already exists in the database.
    :param data: The contents of the form containing the tags the user wishes to add.
    :param id: The item ID the user wishes to add the tags to.
    :param type: The item type the user wishes to add the tags to.
    :return cant_add: Returns a list of tags that the system failed to add due to them already existing or the user
    having added them already.
    """

    #Break the contents of the form into individual tags.
    tags = data['tags'].split()
    cant_add = []
    added = []
    offensive = []
    predictions = predict(tags)
    if any(predictions):
        flash(f'The system has detected profanity in the tags you are trying to add. Please remove the profanity and try again', 'danger')
        return
    #Iterate through the tags.
    for tag in tags:

        db_tag = Tags.query.filter_by(tag=tag).first()

        #If the tag does not already exist in the Tags table, add it. Create a record that the user has added the tag.
        if not db_tag:
            db_tag = add_tag(tag)
        item_tag = ItemTags.query.filter_by(item_id=id, item_type=type, tag_id=db_tag.tag_id).first()
        user_tagged = UserUpvotes.query.filter_by(user_id=current_user.user_id, item_type=type, tag_id=db_tag.tag_id,
                                                  item_id=id).first()

        #If the user has not already added this tag, create a new record in ItemTags and UserUpvotes.
        if not item_tag:
            new_item_tag = ItemTags(item_id=id, item_type=type, tag_id=db_tag.tag_id, count=1)
            db.session.add(new_item_tag)
            new_user_tag = UserUpvotes(user_id=current_user.user_id, item_type=type, tag_id=db_tag.tag_id, item_id=id,
                                       timestamp=int(time.time()))
            db.session.add(new_user_tag)
            added.append(tag)
        else:
            if not user_tagged:
                item_tag.count += 1
                new_user_tag = UserUpvotes(user_id=current_user.user_id, item_type=type, tag_id=db_tag.tag_id, item_id=id,
                                           timestamp=int(time.time()))
                db.session.add(new_user_tag)
                added.append(tag)
            else:
                cant_add.append(tag)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash(f'An error was encountered trying to add the tags {e}. Please try again.', 'danger')
            return

    #Prepare the added and cant_add lists to strings which can be flashed to the user, specifying which tags could and could not be added.
    if len(cant_add) > 0:
        cant_str = ", ".join(cant_add)
        if len(added) > 0:
            added_str = ", ".join(added)
        else: added_str = "None"
        flash(f'Failed to add the tags: "{cant_str}". You may have already upvoted/added these. The new tags added are: "{added_str}"',
            'warning')
    if len(offensive) > 0:
        offensive_str = ", ".join(offensive)
        flash(f'The following tags were deemed offensive: {offensive_str}. They were therefore not allowed to be added', 'danger')
    else:
        flash(f'Tags added successfully!', 'success')
    print(added)
    print(cant_add)
    return cant_add

def add_tag(tag_name):
    """
    A helper function to add a new tag to the Tags table of the database.
    :param tag_name: The text of the tag.
    :return new_tag: Returns the new Tag object that was added to the database.
    """
    new_tag = Tags(tag=tag_name)
    db.session.add(new_tag)
    try:
        db.session.commit()
    except:
        db.rollback()
    return new_tag
