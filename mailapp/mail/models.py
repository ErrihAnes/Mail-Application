from mailapp.extentions import db
from sqlalchemy.orm import relationship


class MailAccount(db.Model):
    __tablename__ = 'mail_accounts'

    id = db.Column(db.Integer, primary_key=True)
    user_id=db.Column(db.Integer, db.ForeignKey('user.uid'),nullable=False)
    apppassword = db.Column(db.String, nullable=False)
    imaphost = db.Column(db.String,nullable=False)
    imapport = db.Column(db.String, nullable=False)
    smtphost = db.Column(db.String, nullable=False)
    smtpport = db.Column(db.String, nullable=False)

    # relation
    user = db.relationship('User', backref='mail_accounts')
    def getid(self):
        return self.id

