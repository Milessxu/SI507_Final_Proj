1. User instructions:

1) Yelp:
- The user should register with a Yelp account and acquire the necessary "client_ID" and "API_KEY". Put them in your the "secrets.py" file accoordingly.

2) final_proj.py
- This is the code that realizes searching for restaurant nearby and save the retrieved data in "cache_rests.json" and "cache_recipes.json", while keeping the search history in "search_history.db".

3) app.py
- This is the code with all the flasks that the user can interact with: 

* Homepage: User choose to search for restaurants or the recipes provided by allrecipes.com.
* Keyword search page: User types in the key word that allows to serach
* Restaurant results page: It shows the top rated restaurants according to the keyword, with the rating provided.
* Restaurant review page: after the search results, user can further click to see the top reviews of the restaurants above.
* User can go back to the previous page or homepage directly when he/she wants.
* templates are all in the "templates" folder.

4) secrets.py
- It is left blank for the API key to be filled.

2. User guide:

1) Clone the repository to your local path
2) Acquire the Yelp API and copy them to the "secrets.py" file 
3) Open the IDE
4) Install flask
5) Run "final_proj.py" file first
6) Run "app.py" file
7) Open the page http://127.0.0.1:5000 on your browser

