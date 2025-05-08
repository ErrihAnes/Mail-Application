from flask_login import UserMixin

from mailapp.extentions import db

class User(db.Model,UserMixin):
    __tablename__ = 'user'

    uid = db.Column(db.Integer,primary_key=True)
    username=db.Column(db.String,nullable=False)
    password = db.Column(db.String,nullable=False)
    email = db.Column(db.String, nullable=False)
    phone = db.Column(db.Integer,nullable=False)
    def __repr__(self):
        return f'user : {self.username} , mail : {self.email}'
    def get_id(self):
        return self.uid