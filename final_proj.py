import requests
import json
import secrets
import sqlite3
from bs4 import BeautifulSoup
from flask import Flask, render_template

API_token = secrets.API_KEY
header = {'authorization': "Bearer " + API_token}


DBName = 'search_history.db'

result = []
history = []
review_list = []
category_list = []
most_made_list = []


# Caching data

CACHE_FNAME = 'cache_rests.json'
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

    if unique_ident in CACHE_DICTION:
        return CACHE_DICTION[unique_ident]

    else:
        resp = requests.get(baseurl, params, headers = header)
        CACHE_DICTION[unique_ident] = json.loads(resp.text)
        dumped_json_cache = json.dumps(CACHE_DICTION)
        fw = open(CACHE_FNAME,"w")
        fw.write(dumped_json_cache)
        fw.close() # Close the open file
        return CACHE_DICTION[unique_ident]


# get data from API

def getYelp(search_term, location = "Ann Arbor", sort_rule = "rating"):
    global API_token
    global result
    baseurl = "https://api.yelp.com/v3/businesses/search"
    params = {}
    params['term'] = search_term
    params['location'] = location
    params['sort_by'] = sort_rule
    header = {'authorization': "Bearer " + API_token}

    response = make_request_using_cache(baseurl,params = params)

    aggregate_dic = {}

    result_list = []
    for item in response["businesses"]:
        aggregate_dic = {"name":item["name"], "attributes":{}} 
        aggregate_dic["attributes"]["rating"] = item["rating"]
        aggregate_dic["attributes"]["lon"] = item["coordinates"]["longitude"]
        aggregate_dic["attributes"]["lat"] = item["coordinates"]["latitude"]
        aggregate_dic["attributes"]["id"] = item["id"]
        result_list.append(aggregate_dic)

    saveSearch(search_term)

    result = result_list 


# Save search keyword in the database

def saveSearch(keyword):
    global DBName

    conn = sqlite3.connect(DBName)
    cur = conn.cursor()

    if len(CACHE_DICTION) == 0:

        statement = '''
            DROP TABLE IF EXISTS 'History'
        '''
        cur.execute(statement)
        conn.commit()

        create_table_statement = '''
            CREATE TABLE 'History' (
            'ID' INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            'Keyword' TEXT NOT NULL,
            'Count' INTEGER NOT NULL,
            'LastTime' TEXT NOT NULL
            );
        '''
        cur.execute(create_table_statement)
        conn.commit()
        conn.close()

    else:
        statement = '''
            SELECT Keyword, Count
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
                INSERT INTO 'History' ('ID', 'Keyword', 'Count', 'LastTime')
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            '''
            insersion = (None, keyword, count, )
            cur.execute(statement, insersion)
            conn.commit()

        else:
            count = str(int(current_dict[keyword]["count"]) + 1)
            statement = '''
                UPDATE History
                SET Count = ?, LastTime = CURRENT_TIMESTAMP
                WHERE Keyword = ?
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
        SELECT Keyword, Count, LastTime
        FROM History
        ORDER BY Count DESC
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
        baseurl = "https://api.yelp.com/v3/businesses/" + r["attributes"]["id"] + "/reviews"
        params = {}
        response = make_request_using_cache(baseurl,params = params)

        review_dic = {"name": r["name"], "reviews":[]}
        for review in response["reviews"]:
            review_dic["reviews"].append(review["text"])

        review_list.append(review_dic)


# Recipe crawling

CACHE_FNAME_R = 'cache_recipes.json'

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
    else:
        print("Making a request for new data...")
        resp = requests.get(url)
        CACHE_DICTION_R[url] = resp.text
        dumped_json_cache = json.dumps(CACHE_DICTION_R)
        fw = open(CACHE_FNAME_R,"w")
        fw.write(dumped_json_cache)
        fw.close()
        return CACHE_DICTION_R[url]

def getRecipeCategory():

    global category_list

    url = "https://www.allrecipes.com/recipes/"
    html = make_request_using_cache_recipe(url)
    soup = BeautifulSoup(html, 'html.parser')

    div = soup.find_all('div', class_ = 'all-categories-col')  
    section_list = []
    for col in div:
        section = col.find_all('section')
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

    global most_made_list

    baseurl = url
    html = make_request_using_cache_recipe(baseurl)
    soup = BeautifulSoup(html,'html.parser')

    links = soup.find_all("li", class_ = "list-recipes__recipe")

    count = 0
    temp_list = []
    for li in links[0:3]:
        count += 1
        recipe_url = li.find('a')['href']
        recipe_name = li.find('h3').text
        recipe_star = str(li.find('span', class_ = "stars")['data-ratingstars'])[0:3]
        recipe_freq = li.find('format-large-number')['number']
        x = (count, recipe_name,recipe_url,recipe_star,recipe_freq)
        temp_list.append(x)
    most_made_list = temp_list
