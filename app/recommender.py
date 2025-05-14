from app.models import *
import Levenshtein
from app.get_info import *
import networkx as nx
import numpy
import math
import spacy

nlp_entity = spacy.load('en_core_web_sm')

def generate_graph(item_id, item_type, weighting, top_n):
    """
    This function generates a knowledge graph which will be passed to the 'visualise.html' template for rendering by
    the client using D3.js. This graph consists of nodes (items in the DB) and edges (the similarity score between two items).
    :param item_id: The ID of the initial node.
    :param item_type: The type of the initial node.
    :param weighting: The weighting specified by the user.
    :param top_n: The size of the graph specified by the user.
    :return graph: The networkx graph object.
    """
    graph = nx.Graph()
    weighting = float(weighting) / 10
    initial = f"{item_id} {item_type}"
    graph.add_node(initial)
    related = calculate_recommender(item_id, item_type, weighting)
    top_nodes = sorted(related.items(), key=lambda x: x[1], reverse=True)[:int(top_n)]
    top_node_ids = {f"{k[0]} {k[1]}" for k, v in top_nodes}

    graph.add_nodes_from(top_node_ids)

    for node1 in top_node_ids:
        for node2 in top_node_ids:
            if node1 != node2:
                similarity = compare_nodes(node1, node2)
                if similarity >= float(weighting) * 10:
                    graph.add_edge(node1, node2, weight=round(similarity))
    return graph


def calculate_recommender(item_id, item_type, weighting):
    """
    This function creates a list of items that will form part of the knowledge graph. This is done by querying the database,
    calculating the similarity score for each item and appending it to related should the weighting of the item exceed the
    threshold specified by the user.
    :param item_id: The ID of the initial node.
    :param item_type: The type of the initial node.
    :param weighting: The weighting threshold specified by the user.
    :return related: A dictionary of nodes to be added to the knowledge graph.
    """

    #Create the related dictionary and get info about the initial node.
    related = {}
    initial_item = get_item(item_id, item_type)
    initial_tags = get_item_tags(item_id, item_type)

    #Query the Books, Films and Games table and calculate the similarity score between items.
    for book in Books.query.all():
        book_tags = get_item_tags(book.id, "book")
        similarity = calculate_similarity(initial_item.title, book.title, initial_tags, book_tags)
        if similarity >= float(weighting):
            related[book.id, "book"] = similarity
    for film in Films.query.all():
        film_tags = get_item_tags(film.id, "film")
        similarity = calculate_similarity(initial_item.title, film.title, initial_tags, film_tags)
        if similarity >= float(weighting):
            related[film.id, "film"] = similarity
    for game in Games.query.all():
        game_tags = get_item_tags(game.id, "game")
        similarity= calculate_similarity(initial_item.title, game.title, initial_tags, game_tags)
        if similarity >= float(weighting):
            related[game.id, "game"] = similarity
    return related


def calculate_similarity(title1, title2, tags1, tags2):
    """
    Calculates the similarity between two nodes in the networkx graph. This is used to determine the strength of the
    similarity between the two nodes.
    :param title1: The title of the first node.
    :param title2: The title of the second node.
    :param tags1: The tags of the first node.
    :param tags2: The tags of the second node.
    :return: 0 if no similarity is detected or one of the items is incomplete, otherwise a value between 0 and 1 which is
    the similarity score. A higher value indicates a stronger similarity.
    """

    #Extract entities associated with the two titles.
    entities_title1 = extract_entities(title1)
    entities_title2 = extract_entities(title2)

    #Calcualte title similarity, cosine similarity and entity similarity.
    title_similarity = float(title_sum(title1, title2))
    tags_similarity = float(cosine_similarity(tags1, tags2))
    entity_similarity = float(entities_similarity(entities_title1, entities_title2))

    score = round(float((title_similarity * 0.3) +(tags_similarity * 0.6) + (entity_similarity * 0.1)), 2) * 10
    return 0 if math.isnan(score) else score


def compare_nodes(node1, node2):
    """
    Compares the similarity of two nodes in the graph by gathering the required parts used to calculate similarity.
    Then passes this to the calculate similarity function to generate a similarity score which is returned to the
    user.
    :param node1: The first node of the graph.
    :param node2: The second node of the graph.
    :return: Returns the value of the calculate_similarity function when applied to the two nodes.
    """
    # Extract IDs and types from the nodes
    id1, type1 = node1.split()
    id2, type2 = node2.split()

    # Get the items and their tags
    item1 = get_item(id1, type1)
    item2 = get_item(id2, type2)
    tags1 = get_item_tags(id1, type1)
    tags2 = get_item_tags(id2, type2)

    # Calculate similarity using the same logic
    return calculate_similarity(item1.title, item2.title, tags1, tags2)


def cosine_similarity(initial_tags, other_tags):
    """
    Calculates the cosine similarity between two sets of tags.
    This is the dot product of the two sets of tags divided by the magnitude of them both.

    :param initial_tags: The tags for the first item.
    :param other_tags: The tags for the second item.
    :return cs: The cosine similarity number
    """
    all_tags = set.union(set(initial_tags.keys()), set(other_tags.keys()))

    #Get the tags vectors to perform the dot product on, set by default to 0 if the tag is not present in one of the items.
    initial_tags_vector = [initial_tags.get(tag, 0) for tag in all_tags]
    other_tags_vector = [other_tags.get(tag, 0) for tag in all_tags]

    #Use numpy to perform the dot product calculation
    dot_product = numpy.dot(initial_tags_vector, other_tags_vector)

    #Calculate the magnitudes of the two vectors of tags using numpy.
    initial_magnitude = numpy.sqrt(numpy.dot(initial_tags_vector, initial_tags_vector))
    other_magnitude = numpy.sqrt(numpy.dot(other_tags_vector, other_tags_vector))

    #Calculate the cosine similarity
    cs = dot_product / (initial_magnitude * other_magnitude)

    return cs

def title_sum(item1_title, item2_title):
    """
    Calculates the Levenshtein similarity between two titles. This works by calculating the number of character changes
    required to translate one title into another title. This is implemented using the Levenshtein Python module.
    :param item1_title: The first title string.
    :param item2_title: The second title string.
    :return: The Levenshtein ratio number.
    """
    return Levenshtein.ratio(item1_title, item2_title)

def extract_entities(title):
    """
    This function uses the spacy model to extract entities from the title of an item.
    :param title: The title of an item
    :return entities: A dictionary of entities containing the text as a key and the entity as a value.
    """
    #Get entities from title.
    title = nlp_entity(title)
    entities = {}

    #Store these entities as a dictionary, with the key as the text and the value as the entity label given by spacy.
    for string in title.ents:
        entities[string.text] = string.label_
    return entities

def entities_similarity(entities1, entities2):
    """
    Uses the spacy model to calculate the entity similarity. This is done by comparing the common entities to total entities
    to produce a ratio of entities in common between two items ranging from 0-1 . A higher value indicates stronger similarity
    between the two entities.
    :param entities1: A list of entities from the first item.
    :param entities2: A list of entities for the second item.
    :return: The ratio of common entities shared by both items.
    """
    common_entities = set(entities1.keys()).intersection(set(entities2.keys()))
    total_entities = len(entities1) + len(entities2)

    #Make sure to return 0 if no entities are identified.
    if total_entities == 0:
        return 0
    return len(common_entities) / (total_entities - len(common_entities))

#Prepare the graph to be JSONified.
def serialise_graph(graph):
    """
    This function serialises the graph in a format that can then be converted to JSON for rendering by D3.js on the front-end.
    :param graph: The Graph object created by networkx.
    :return: The nodes and edges of the graph in a JSON format.
    """
    nodes = [{"id": node} for node in graph.nodes()]
    links = []
    for u, v, data in graph.edges(data=True):
        links.append({
            "source": u,
            "target": v,
            "weight": data.get("weight")
        })
    return {
        "nodes": nodes,
        "links": links
    }


def database_info(nodes):
    """
    Generates the database info to be passed to the front end in JSON. This information is then used to provide information
    about the items in the knowledge graph visualisation.
    :param nodes: The nodes of the knowledge graph.
    :return db_info: A dictionary containing the node as a key and database info as the value.
    """
    db_info = {}

    #Iterate through nodes. split into parts, the first being the ID and the second being the type. Append to db_info.
    for node in nodes:
        split = node.split(" ")
        if split[1] == "book":
            entry = Books.query.filter_by(id=int(split[0])).first()
            db_info[node] = {
                'Title': entry.title,
                'Author': entry.author,
                'Year': entry.year,
                'Publisher': entry.publisher,
                'Cover': entry.cover,
            }
        elif split[1] == "film":
            entry = Films.query.filter_by(id=split[0]).first()
            db_info[node] = {
                'Title': entry.title,
                'Director': entry.director,
                'Year': entry.year,
                'Production Company': entry.production_company,
                'Cover': entry.cover,
            }
        else:
            entry = Games.query.filter_by(id=split[0]).first()
            db_info[node] = {
                'Title': entry.title,
                'Developer': entry.developer,
                'Year': entry.year,
                'Cover': entry.cover,
            }
    return db_info

