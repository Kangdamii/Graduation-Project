from flask import Flask, g, render_template, Markup

app = Flask(__name__)
# app.debug = True
# app.jinja_env.trim.blocks = True



@app.route('/')
def mainDisplay():
    return render_template('main.html')

@app.route('/register')
def registerPage():
    return render_template('register.html')

# @app.before_request

# def before_request():
#     print("before_request")
#     g.str = "한글"

# @app.route("/tmpl")
# def t():
#     tit = Markup("<strong>Title<strong>")
#     mu = Markup("<h1>iii = <i>%s</i></h1>")
#     h = mu % "Italic"
#     print("h=", h)
#     return render_template('index.html', title = tit, mu = h)

# @app.route("/")
# def helloworld():
#     return "Hello Flask World!"

# @app.route("/gg")
# def helloworld2():
#     return "Hello Flask World!" + getattr(g, 'str', '111')


