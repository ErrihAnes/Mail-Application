from mailapp.extentions import db
from sqlalchemy.orm import relationship

class Domain(db.Model):
    __tablename__ = 'domains'
    did = db.Column(db.Integer,primary_key=True)
    user_id=db.Column(db.Integer, db.ForeignKey('user.uid'),nullable=False)
    domain = db.Column(db.String,nullable=False)
    prompt = db.Column(db.String, nullable=False)
    themeautoreply = db.Column(db.String,nullable=False)
    replyautoreply = db.Column(db.String, nullable=False)

    #relation user avec domain
    user = db.relationship('User',backref='domains')

    def getid(self):
        return self.did