from flask import Flask
from conversion_module import conversion_bp 
from scoring_module import scoring_bp 

app = Flask(__name__)
app.register_blueprint(conversion_bp, url_prefix="/api")
app.register_blueprint(scoring_bp, url_prefix="/api")

if __name__ == '__main__':
    app.run(debug=True)