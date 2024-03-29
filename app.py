from flask import Flask, render_template, session, url_for, request, redirect, escape, flash
from flask import *
from datetime import datetime,date
import pymysql.cursors
import os

app = Flask(__name__)

app.secret_key = os.urandom(16)

try:
    connection = pymysql.connect(host="tsuts.tskoli.is", user="1609022560", password="mypassword", db="1609022560_verk7", charset="utf8mb4", cursorclass=pymysql.cursors.DictCursor)

except pymysql.OperationalError:
    print("\n\n\n#######\nDatabase virkar ekki\n#######\n\n\n")
    exit()

def inttomon(i):
    dicta = {
        "01": "janúar",
        "02": "febrúar",
        "03": "mars",
        "04": "apríl",
        "05": "maí",
        "06": "júní",
        "07": "júlí",
        "08": "ágúst",
        "09": "september",
        "10": "október",
        "11": "nóvember",
        "12": "desember"
    }
    return dicta[i]

def date(gotinput):
    obj = datetime.strptime(gotinput, "%Y-%m-%d %H:%M:%S")
    return obj.strftime(f"%d {inttomon(obj.strftime('%m'))} %Y klukkan %H:%M")

app.jinja_env.filters['date'] = date

@app.route("/")
def index():
    with connection.cursor() as cursor:
        sql = "select * from 1609022560_verk7.posts"
        cursor.execute(sql)
        listinn = cursor.fetchall()
        listinn = [i for i in listinn]
        listi = sorted(listinn, key=lambda k: k['posttime'], reverse=True) 
    return render_template("index.html", listi=listi, session=session)

@app.route("/login")
def login():
    return render_template("login.html")

@app.route('/login/submit', methods=['GET', 'POST'])
def loginsubmit():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        passwd = request.form.get('password')

        cursor = connection.cursor()
        cursor.execute("select count(*) from people where username=%s and passwd=%s",(username,passwd))
        result = cursor.fetchone() 
        print(result)

        if result["count(*)"] == 1:
            session['loggedin'] = username
            return redirect("/")
        else:
            error = 'Innskráning mistókst - reyndu aftur'
    return render_template('login.html', error=error)

@app.route("/signup")
def signup():
    return render_template("signup.html")

@app.route("/signup/submit", methods=["GET","POST"])
def subsignup():
    if request.method == "POST":
        sup = {
            "username":request.form["username"],
            "email":request.form["email"],
            "password":request.form["password"]
        }
    
    with connection.cursor() as cursor:
        sql = "select * from people"
        cursor.execute(sql)
        userlist = cursor.fetchall()
        for i in userlist:
            if i["username"] == sup["username"]:
                return render_template("signup.html", error="Þetta notendanafn er nú þegar í notkun")
            elif i["email"] == sup["email"]:
                return render_template("signup.html", error="Þetta netfang er nú þegar í notkun")

        else:
            skrainn = f"insert into people values ('{sup['username']}', '{sup['email']}', '{sup['password']}', 'none')"
            print(skrainn)
            cursor.execute(skrainn)
            connection.commit()
    return render_template("custom.html", content=f"Skráður, {sup['username']}!")

@app.route("/logout")
def logout():
    if not "loggedin" in session:
        return redirect("/")
    nafn = session["loggedin"]
    session.pop("loggedin")
    return render_template("custom.html", content="Þú hefur verið skráður út, %s" % nafn)

@app.route("/post")
def myposts():
    if "loggedin" in session:
        with connection.cursor() as cursor:
            sql = "select * from posts where username='%s'" % session["loggedin"]
            cursor.execute(sql)
            listi = cursor.fetchall()
            lenposts = len(listi)
            listi = [i for i in listi]
            posts = sorted(listi, key=lambda k: k['posttime'], reverse=True)
    else:
        return render_template("custom.html", content="Þú verður að vera skráður inn til að gera þetta")

    return render_template("myposts.html", posts=posts, lenposts=len(posts))

@app.route("/post/<id>")
def posts(id):
    with connection.cursor() as cursor:
        sql = "select * from posts where id='%s'" % id
        cursor.execute(sql)
        post = cursor.fetchone()
        post["posttime"] = str(post["posttime"])

    return render_template("post.html", post=post)

@app.route("/createpost")
def createpost():
    return render_template("createpost.html")

@app.route("/createpost/submit", methods=["GET","POST"])
def createsubmit():
    if session.get('loggedin') == None:
        return redirect("/")
    if request.method == "POST":
        data = {
            "title":request.form["title"],
            "post":request.form["post"]
        }

    username = session.get('loggedin')
    time = datetime.now()
    time = time.strftime("%Y-%m-%d %H:%M:%S")
    time = str(time)
    print(data["post"])
    with connection.cursor() as cursor:
        sql = f"insert into posts (username,posttime,content,title) values ('{username}','{time}', '{data['post']}', '{data['title']}')"
        cursor.execute(sql)
        connection.commit()

    return render_template("custom.html", content="Pósturinn hefur verið sendur")

@app.route("/breyta/<id>")
def breyta(id):
    nafn = session.get("loggedin")
    with connection.cursor() as cursor:
        sql = f"select * from posts where id={id}"
        cursor.execute(sql)
        post = cursor.fetchone()
        if post["username"] != nafn:
            return render_template("custom.html", content="Forbidden")
    return render_template("change.html", post=post)

@app.route("/breyta/<id>/submit", methods=["GET", "POST"])
def subbreyta(id):
    if request.method == "POST":
        data = {
            "title":request.form["title"],
            "post":request.form["post"]
        }
    with connection.cursor() as cursor:
        sql = f"select * from posts where id={id}"
        cursor.execute(sql)
        post = cursor.fetchone()
        nafn = session.get("loggedin")
        if post["username"] != nafn:
            return render_template("custom.html", content="Forbidden")
        sql = f"update posts set title='{data['title']}', content='{data['post']}' where id='{id}';"
        cursor.execute(sql)
    return redirect(f"/post/{id}")

@app.route("/eyda/<id>")
def eyda(id):
    nafn = session.get("loggedin")
    sql = f"delete from posts where id={id}"
    sql2 = f"select * from posts where id={id}"
    with connection.cursor() as cursor:
        cursor.execute(sql2)
        post = cursor.fetchone()
        if post["username"] != nafn:
            return render_template("custom.html", content="Forbidden")
        else:
            cursor.execute(sql)
            connection.commit()
    return render_template("custom.html", content="Pósti eytt!")

    

@app.errorhandler(404)
def pagenotfound(error):
    return render_template('pagenotfound.html')


if __name__ == "__main__":
    app.run(debug=True, use_reloader=True)
    #app.run(host="192.168.43.126")