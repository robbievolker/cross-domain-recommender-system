# Cross-Domain Recommender System

This project allows you to track the items you have read, watched and played. You can also add descriptive tags to these items and upvote tags other users have added. You can then generate visualisations of recommendations based on an input item, using this system to find out what to read, watch or play next!

This application works through the implementation of a recommender algorithm which uses the following three elements to determine recommendations:

- [Levenshtein distance](https://en.wikipedia.org/wiki/Levenshtein_distance): string distance between two strings.
- [Cosine similarity](https://en.wikipedia.org/wiki/Cosine_similarity): the similarity between two sets of tags represented as vectors.
- [Spacy NER Model](https://spacy.io/usage/models): which extracts the entities present in a string.




## Installation

To deploy this project, clone the archive and extract it. You will then need to install the dependencies required to run this project using pip. 

#### Pip
```bash
  pip install -r requirements.txt
```
Next enter your IDE and configure Python to run, and execute the project using the flask-script.py file. 

Go to https://localhost:5000 and the application should be running! If the database is not working, open a flask shell and input:
```python
db.create_all()
db.session.commit()
```
This should initialise the database required to run the application.

NOTE: If the profanity-check model does not work correctly, try installing: 

```bash
  pip install alt-profanity-check
```

as the original module may not work depending on the version of Python you have installed.


## Acknowledgements

### APIs
 - [Google Books API](https://developers.google.com/books)
 - [OMDb API](https://www.omdbapi.com/)
 - [IGDb API](https://www.igdb.com/api)


### Code
 - [Flask Mega Tutorial](https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-i-hello-world) for providing a basic Flask template for a web application
 - [Spacy](https://spacy.io/usage/models) for providing a pre-trained Named Entity Recognition model that forms part of the recommendation algorithm
 - [profanity-check](https://github.com/vzhou842/profanity-check) for providing a model for detecting profane content, this helped a lot with content moderation. 
  - [D3.js](https://d3js.org/) as the library used to visualise the recommendations. 

