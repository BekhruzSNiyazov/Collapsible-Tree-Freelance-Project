from flask import Flask, render_template, session, redirect, flash, request, url_for, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
import csv
import json

app = Flask(__name__)
app.secret_key = b"_5#y2L'F4Q8z\n\xec]/"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.sqlite3"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

login_message = "You need to login or sign up first!"

def generate_tree(keyword, keywords):
	tree = {}
	for word in keywords:
		if word[:len(keyword)] == keyword and len(word.split()) == len(keyword.split()) + 1:
			keywords.remove(word)
			try:
				tree["children"].append({"name": word})
				tree["name"] = keyword
			except:
				tree["name"] = keyword
				tree["children"] = []
				tree["children"].append({"name": word})
	if tree:
		for word in tree["children"]:
			children = remove_beginning(generate_tree(word["name"], keywords))
			if children:
				tree["children"][tree["children"].index(word)]["children"] = children["children"]
	return remove_beginning(tree)

def generate_csv(tree, level=0):
	content = ""
	try:
		end = "\n"
		tab = ","
		if level == 0: content += tree["name"] + end
		l = level
		for child in tree["children"]:
			content += tab + child["name"] + end
			content += tab + tab * level + generate_csv(child, level=l+1) + end
	except: pass
	return content

def remove_beginning(tree):
	if tree:
		try:
			for word in tree["children"]:
				wrd = {}
				if "children" in list(word.keys()):
					children = []
					for child in word["children"]:
						children.append(remove_beginning(child))
					wrd = {"name": word["name"].replace(word["name"].split()[0]+" ", ""), "children": children}
				else: wrd = {"name": word["name"].replace(word["name"].split()[0]+" ", "")}
				tree["children"][tree["children"].index(word)] = wrd
			return tree
		except: return tree

class User(db.Model):
	_id = db.Column(db.Integer, primary_key=True, unique=True)
	email = db.Column(db.String(255), unique=True)
	password = db.Column(db.String(255))

@app.route("/")
def index():
	if "email" in session:
		return render_template("index.html")
	flash(login_message)
	return redirect("/login")

@app.route("/tree")
def tree():
	keyword = request.args["keyword"]
	keywords = []
	with open("Demo_Data.csv", "r") as file:
		reader = csv.DictReader(file, delimiter=",")
		for row in reader: keywords.append(row.get("Keyword"))
	if keyword not in keywords: return render_template("not_found.html")	
	tree = remove_beginning(generate_tree(keyword, keywords))
	with open("static/data.json", "w") as file:
		file.write(json.dumps(tree))
	with open(keyword + "-tree.csv", "w") as file:
		file.write(generate_csv(tree))
	return render_template("search.html", keyword=keyword)

@app.route("/login")
def login():
	if "email" in session:
		flash("You are already logged in.")
		return redirect("/")
	return render_template("login.html")

@app.route("/logging", methods=["POST", "GET"])
def logging():
	message = "Incorrect email or password. Sign up if you haven't got an account yet."
	email = request.form["email"]
	password = request.form["password"]
	found_user = User.query.filter_by(email=email).first()
	if found_user:
		found_password = found_user.password == password
		if found_password:
			session["email"] = email
			return redirect("/")
		flash(message)
		return redirect("/login")
	flash(message)
	return redirect("/login")

@app.route("/signup")
def signup():
	if "email" in session:
		flash("You are already signed up.")
		return redirect("/")
	return render_template("signup.html")

@app.route("/signing", methods=["POST", "GET"])
def signing():
	email = request.form["email"]
	password = request.form["password"]
	apassword = request.form["apassword"]
	if password != apassword:
		flash("Passwords do not match. Try again.")
		return redirect("/signup")
	if User.query.filter_by(email=email).first():
		flash("This email is already taken. Try another one. Login if you have an account.")
		return redirect("/signup")
	user = User(email=email, password=password)
	db.session.add(user)
	db.session.commit()
	session["email"] = email
	return redirect("/")

@app.route("/logout")
def logout():
	session.pop("email", None)
	return redirect("/")

@app.route("/data")
def data():
	return open("static/data.json", "r").read()

@app.route("/download-<keyword>")
def download(keyword):
	return send_from_directory(directory=".", filename=keyword + "-tree.csv", as_attachment=True)

@app.route("/<error>")
def error(error):
	return redirect("/")

if __name__ == "__main__":
	db.create_all()
	app.run(debug=True)