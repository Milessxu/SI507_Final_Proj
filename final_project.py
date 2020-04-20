import requests
import json
import secrets
import sqlite3
from bs4 import BeautifulSoup
from flask import Flask, render_template



# GLOBAL VARIABLE
DBName = 'search.db'
## These varibles are used to pass value to the html files.
result = []
history = []
review_list = []
category_list = []
most_made_list = []


### YELP ###

# Originally I defined the class "restaurant" to store data retrieved from Yelp API
# so that I can use attributes (e.g., rating, location) in a more convenient way
# however, I later on thought it's okay just to use functions. so I commented out the class

# class restaurant():
#     def __init__(self, restaurant_dic):
#         self.name = restaurant_dic["name"]
#         self.rating = restaurant_dic["attributes"]["rating"]
#         self.id = restaurant_dic["attributes"]["id"]
#         self.lon = restaurant_dic["attributes"]["lon"]
#         self.lan = restaurant_dic["attributes"]["lan"]
#
#     def __str__(self):
#
#         return "{} / rating: {}".format(self.name, self.rating)

# API KEYS for Yelp

API_token = secrets.API_KEY
header = {'authorization': "Bearer " + API_token}

# Caching data

CACHE_FNAME = 'cache.json'
try:
    cache_file = open(CACHE_FNAME, 'r')
    cache_contents = cache_file.read()
    CACHE_DICTION = json.loads(cache_contents)
    cache_file.close()

except:
    CACHE_DICTION = {}

def params_unique_combination(baseurl, params_d, headers = header):
    alphabetized_keys = sorted(params_d.keys())
    res = []
    for k in alphabetized_keys:
        res.append("{}-{}".format(k, params_d[k]))
    return baseurl + "_".join(res)


def make_request_using_cache(baseurl, params, headers = header):
    global header
    unique_ident = params_unique_combination(baseurl,params)

    ## first, look in the cache to see if we already have this data
    if unique_ident in CACHE_DICTION:
        # print("Getting cached data...")
        return CACHE_DICTION[unique_ident]

    ## if not, fetch the data afresh, add it to the cache,
    ## then write the cache to file
    else:
        # print("Making a request for new data...")
        # Make the request and cache the new data
        resp = requests.get(baseurl, params, headers = header)
        CACHE_DICTION[unique_ident] = json.loads(resp.text)
        dumped_json_cache = json.dumps(CACHE_DICTION)
        fw = open(CACHE_FNAME,"w")
        fw.write(dumped_json_cache)
        fw.close() # Close the open file
        return CACHE_DICTION[unique_ident]


# get data from Yelp API

def getYelp(search_term, location = "Ann Arbor", sort_rule = "rating"):
    global API_token
    global result
    baseurl = "https://api.yelp.com/v3/businesses/search"
    params = {}
    params['term'] = search_term
    params['location'] = location
    params['sort_by'] = sort_rule
    # params['limit'] = 10
    # params["authorization"] = "Bearer " + API_token
    header = {'authorization': "Bearer " + API_token}

    # response = requests.get(baseurl,params=params, headers = header).text
    response = make_request_using_cache(baseurl,params = params)
    # result = json.loads(response)
    # print(result)

    aggregate_dic = {}

    result_list = []
    for item in response["businesses"]:
        # print(item["name"])
        aggregate_dic = {"name":item["name"], "attributes":{}}   # create a dic for each business
        aggregate_dic["attributes"]["rating"] = item["rating"]
        aggregate_dic["attributes"]["lon"] = item["coordinates"]["longitude"]
        aggregate_dic["attributes"]["lat"] = item["coordinates"]["latitude"]
        aggregate_dic["attributes"]["id"] = item["id"]
        result_list.append(aggregate_dic)

    saveSearch(search_term)

    result = result_list   # "result" has value here

# Save search keyword in the database
def saveSearch(keyword):
    global DBName

    # initate the database
    conn = sqlite3.connect(DBName)
    cur = conn.cursor()

    # Create new table
    if len(CACHE_DICTION) == 0:
        # Assuming user initates the program using the same computer,
        # if the CACHE_DICTION is empty, it means that he/she heasn't used this program before
        # Hence the program creates a new table "History"
        # If the CACHE_DICTOIN is not empty, then this step is skipped.

        statement = '''
            DROP TABLE IF EXISTS 'History'
        '''
        cur.execute(statement)
        conn.commit()

        create_table_statement = '''
            CREATE TABLE 'History' (
            'ID' INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            'KeyWord' TEXT NOT NULL,
            'NumberOfSearch' INTEGER NOT NULL,
            'LastSearchOn' TEXT NOT NULL
            );
        '''
        cur.execute(create_table_statement)
        conn.commit()
        conn.close()

    # Update/insert value
    else:
        # If the table already exists
        statement = '''
            SELECT KeyWord, NumberOfSearch
            FROM History
        '''
        cur.execute(statement)

        current_dict = {}
        current_list = []
        keyword_list = []
        for row in cur:
            keyword_list.append(row[0])
            current_dict[row[0]] = {}
            current_dict[row[0]]["search_term"] = row[0]
            current_dict[row[0]]["count"] = row[1]
            current_list.append(current_dict[row[0]])

        if keyword not in keyword_list:
            count = 1
            statement = '''
                INSERT INTO 'History' ('ID', 'KeyWord', 'NumberOfSearch', 'LastSearchOn')
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            '''
            insersion = (None, keyword, count, )
            cur.execute(statement, insersion)
            conn.commit()

        else:
            count = str(int(current_dict[keyword]["count"]) + 1)
            statement = '''
                UPDATE History
                SET NumberOfSearch = ?, LastSearchOn = CURRENT_TIMESTAMP
                WHERE KeyWord = ?
            '''
            insersion = (count, keyword)
            cur.execute(statement, insersion)
            conn.commit()

        conn.close()
        return None

# Return the search history from the database

def returnHistory():
    global DBName
    global history

    conn = sqlite3.connect(DBName)
    cur = conn.cursor()

    statement = '''
        SELECT SearchWord, NumberOfSearch, LastSearchOn
        FROM History
        ORDER BY NumberOfSearch DESC
        LIMIT 10
    '''

    cur.execute(statement)
    temp_list = []
    search_term = {}
    for row in cur:
        search_term = {"name": row[0], "num": row[1], "lastSearch": row[2]}
        temp_list.append(search_term)

    history = temp_list
    conn.close()


# Retrun the reviews of restaurants
def getReview():
    global review_list
    global result

    for r in result:
        # Get review for each restaurant
        baseurl = "https://api.yelp.com/v3/businesses/" + r["attributes"]["id"] + "/reviews"
        params = {}
        response = make_request_using_cache(baseurl,params = params)

        review_dic = {"name": r["name"], "reviews":[]}
        for review in response["reviews"]:
            review_dic["reviews"].append(review["text"])

        review_list.append(review_dic)


# Plot restaurants on map

def plotMap():
    global result

    lat_vals = []
    lon_vals = []
    text_vals = []

    for restaurant in result:
        lat_vals.append(restaurant["attributes"]['lat'])
        lon_vals.append(restaurant["attributes"]['lon'])
        text_vals.append(restaurant["name"])

        # set up data format
    data = [ dict(
        type = 'scattergeo',
        locationmode = 'USA-states',
        lon = lon_vals,
        lat = lat_vals,
        text = text_vals,
        mode = 'markers',
        marker = dict(
            size = 8,
            symbol = 'star',
            ))]

        # set up layout
        # min_lat = -90
        # max_lat = 90
        # min_lon = -180
        # max_lon = 180
        #
        # for str_v in lat_vals:
        #     v = float(str_v)
        #     if v < min_lat:
        #         min_lat = v
        #     if v > max_lat:
        #         max_lat = v
        # for str_v in lon_vals:
        #     v = float(str_v)
        #     if v < min_lon:
        #         min_lon = v
        #     if v > max_lon:
        #         max_lon = v
        #
        # max_range = max(abs(max_lat - min_lat), abs(max_lon - min_lon))
        # padding = max_range * .10
        # lat_axis = [min_lat - padding, max_lat + padding]
        # lon_axis = [min_lon - padding, max_lon + padding]
        # center_lat = (max_lat+min_lat) / 2
        # center_lon = (max_lon+min_lon) / 2

    layout = dict(title = 'Restaurants in Ann Arbor',
            geo = dict(scope='usa',projection=dict( type='albers usa' ),
            showland = True,
            landcolor = "rgb(250, 250, 250)",
            subunitcolor = "rgb(100, 217, 217)",
            countrycolor = "rgb(217, 100, 217)",
                # lataxis = {'range': lat_axis},
                # lonaxis = {'range': lon_axis},
            subunitwidth = 3),)

    fig = dict(data=data, layout=layout )
    py.plot( fig, validate=False, filename='state_map' )

### Recipe crawling

# Caching
CACHE_FNAME_R = 'cache_recipe.json'
try:
    cache_file_r = open(CACHE_FNAME_R, 'r')
    cache_contents_r = cache_file_r.read()
    CACHE_DICTION_R = json.loads(cache_contents_r)
    cache_file_r.close()

except:
    CACHE_DICTION_R = {}

def make_request_using_cache_recipe(url):

    if url in CACHE_DICTION_R:
            print("Getting cached data...")
            return CACHE_DICTION_R[url]

        ## if not, fetch the data afresh, add it to the cache,
        ## then write the cache to file
    else:
        print("Making a request for new data...")
        # Make the request and cache the new data
        resp = requests.get(url)
        CACHE_DICTION_R[url] = resp.text
        dumped_json_cache = json.dumps(CACHE_DICTION_R)
        fw = open(CACHE_FNAME_R,"w")
        fw.write(dumped_json_cache)
        fw.close() # Close the open file
        return CACHE_DICTION_R[url]

def getRecipeCategory():
    global category_list

    url = "https://www.allrecipes.com/recipes/"
    html = make_request_using_cache_recipe(url)
    soup = BeautifulSoup(html, 'html.parser')

    div = soup.find_all('div', class_ = 'all-categories-col')  # should return 4 columns
    section_list = []
    for col in div:
        section = col.find_all('section') #should return 2 sections without id
        for category in section:
            section_list.append(category)

    category_dic = {}
    temp_list = []
    for section in section_list:
        category_name = section.find('h3',class_="heading__h3").text
        category_dic = {"name":category_name,"subs":{}}

        sub_category = section.find_all('a')
        for sub in sub_category:
            sub_category_name = sub.text
            sub_category_url = sub['href']
            category_dic["subs"][sub_category_name] = sub_category_url

        temp_list.append(category_dic)
        category_list = temp_list

    return temp_list

def getMostMade(url):
    # category_dic, category_num, category
    # baseurl = category_dic[category_num][category]
    global most_made_list

    baseurl = url
    html = make_request_using_cache_recipe(baseurl)
    soup = BeautifulSoup(html,'html.parser')

    links = soup.find_all("li", class_ = "list-recipes__recipe")
    # print(links)

    count = 0
    temp_list = []
    for li in links[0:3]:
        count += 1
        # print(li)
        # div = li.find('div')
        recipe_url = li.find('a')['href']
        # print(recipe_url)
        recipe_name = li.find('h3').text
        # print(recipe_name)
        recipe_star = str(li.find('span', class_ = "stars")['data-ratingstars'])[0:3]
        recipe_freq = li.find('format-large-number')['number']
        x = (count, recipe_name,recipe_url,recipe_star,recipe_freq)
        temp_list.append(x)
    # print(most_made_list)
    most_made_list = temp_list