import os
import json
def add_recent(item):
    """
    Keeps a JSON file containing the 4 most recently added items to the database. These are then rendered on the "Recently Added"
    section of the page. Items added are appended to the front of the JSON list, and the last item is removed. This ensures that 
    the most recent item is rendered at the top of the list on the application.
    :param item: The information for the item containing hte title, url for the cover, year of release and timestamp it was added.
    """
    #Get the filepath for the JSON file.
    filepath = os.path.join(os.getcwd(), 'app', 'static', 'recently_added.json')
    try:
        with open(filepath, "r") as file:
            data=json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        data = []

    #Format the new item as JSON to write it to the JSON file.
    new_item = {
        "title": item[0],
        "year": item[1],
        "cover": item[2],
        "timestamp": item[3]
    }

    #Append our new item to the list which will be written to the JSON file.
    data.insert(0, new_item)

    #Remove the oldest item if the length is too long.
    if len(data) > 4:
        data.pop()

    #Write the changes to the JSON file.
    with open(filepath, "w") as file:
        json.dump(data, file, indent=4)