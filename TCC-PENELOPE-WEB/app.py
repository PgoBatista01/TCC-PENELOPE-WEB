
from flask import Flask
from models.database import db
from controllers.routes import init_app

app = Flask(__name__, template_folder="views", static_folder="static")

app.config["SQLALCHEMY_DATABASE_URI"] = (
    "mysql+pymysql://root:@localhost/penelope?charset=utf8mb4"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "penelope-chave-local"
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

db.init_app(app)
init_app(app)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(debug=True)
