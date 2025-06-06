from flask import Flask, render_template
from conversion_module import conversion_bp 
from scoring_module import scoring_bp 

app = Flask(__name__)
app.register_blueprint(conversion_bp, url_prefix="/api")
app.register_blueprint(scoring_bp, url_prefix="/api")

@app.route("/")
def index():
    return render_template("index.html")

if __name__ == '__main__':
    app.run(debug=True)