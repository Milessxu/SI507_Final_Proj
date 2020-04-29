from flask import Flask, render_template, request, redirect
import final_proj

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/restaurants", methods = ["GET","POST"])
def restaurants():
    return render_template("restaurants.html")

@app.route("/searchrestaurant", methods = ["GET", "POST"])
def searchrestaurants():
    return render_template("keyword_search.html")

@app.route("/searchkeyword", methods = ['GET', "POST"])
def search():
    keyword = request.form['keyword']
    print(keyword)
    final_proj.getYelp(keyword)
    return redirect("/result")

@app.route("/result", methods = ["GET","POST"])
def result():
    return render_template("result.html",result = final_proj.result)

@app.route("/review", methods = ["GET", "POST"])
def review():
    final_proj.getReview()
    return render_template("review.html", review = final_proj.review_list)

@app.route("/history", methods = ["GET","POST"])
def history():
    final_proj.returnHistory()
    return render_template("history.html",history = final_proj.history)

@app.route("/recipecategory", methods = ["GET", "POST"])
def category():
    final_proj.getRecipeCategory()
    return render_template("recipecategory.html", category = final_proj.category_list)

@app.route("/mostmade", methods = ["GET","POST"])
def recipe():
    url = request.form["type"]
    final_proj.getMostMade(url)
    return render_template("mostmade.html", recipe = final_proj.most_made_list)


if __name__=="__main__":
    app.run(debug=True)
