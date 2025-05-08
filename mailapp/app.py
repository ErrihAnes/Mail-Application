from flask import Flask, jsonify
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, migrate
from flask_bcrypt import Bcrypt
from mailapp.user.routes import regester_route_login
from mailapp.extentions import db
from mailapp.mail.models import MailAccount
from mailapp.user.models import User
from mailapp.brain.routes import start_scheduler


def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///./database.db'
    app.secret_key='secret key'
    db.init_app(app)

    login_manager = LoginManager()
    login_manager.init_app(app)

    from mailapp.user.models import User
    @login_manager.user_loader
    def load_user(uid):
        try:
            return User.query.get(int(uid))
        except ValueError:
            return None
        except Exception as e:
            print(f"Erreur dans load_user: {e}")
            return None

    @login_manager.unauthorized_handler
    def unauthorized():
        return jsonify({"error": "Vous devez être connecté"}), 401


    bcrypt = Bcrypt(app)
    regester_route_login(app, db, bcrypt)
    ##
    from mailapp.user.routes import user
    app.register_blueprint(user, url_prefix='/user')

    from mailapp.mail.routes import mail
    app.register_blueprint(mail,url_prefix='/mail')

    from mailapp.brain.routes import brain
    app.register_blueprint(brain, url_prefix='/brain')
    with app.app_context():
        start_scheduler(app)

    migrate = Migrate(app,db)
    return app