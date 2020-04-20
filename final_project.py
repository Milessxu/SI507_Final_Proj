import requests
import json
import secrets
import sqlite3
from bs4 import BeautifulSoup

DBName = 'history.db'

API_token = secrets.API_KEY
header = {'authorization': "Bearer " + API_token}

result = []
history = []
review_list = []
category_list = []
most_made_list = []

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

    if unique_ident in CACHE_DICTION:
        return CACHE_DICTION[unique_ident]
    else:
        resp = requests.get(baseurl, params, headers = header)
        CACHE_DICTION[unique_ident] = json.loads(resp.text)
        dumped_json_cache = json.dumps(CACHE_DICTION)
        fw = open(CACHE_FNAME,"w")
        fw.write(dumped_json_cache)
        fw.close()
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

# Save keyword in database

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
            'KeyWord' TEXT NOT NULL,
            'NumberOfSearch' INTEGER NOT NULL,
            'LastSearchOn' TEXT NOT NULL
            );
        '''
        cur.execute(create_table_statement)
        conn.commit()
        conn.close()

    else:
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
        baseurl = "https://api.yelp.com/v3/businesses/" + r["attributes"]["id"] + "/reviews"
        params = {}
        response = make_request_using_cache(baseurl,params = params)

        review_dic = {"name": r["name"], "reviews":[]}
        for review in response["reviews"]:
            review_dic["reviews"].append(review["text"])

        review_list.append(review_dic)
