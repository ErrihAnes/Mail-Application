from flask_login import login_user, logout_user
from mailapp.user.models import User
from flask import request, redirect, Blueprint
from mailapp.extentions import db
user = Blueprint('user',__name__)

def regester_route_login(app, db, bcrypt):
    @user.route('/api/auth/inscription',methods=['POST'])
    def inscription():
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('mail')
        print(email)
        phone = request.form.get('phone')
        hashedpassword = bcrypt.generate_password_hash(password)
        newuser = User(username=username,password=hashedpassword,email=email,phone=phone)
        db.session.add(newuser)
        db.session.commit()

        return f"user {username} created ! "
    @user.route('/api/auth/login',methods=['POST'])
    def login():
        username = request.form.get('username')
        password = request.form.get('password')
        print(username)
        user = User.query.filter(User.username == username).first()

        if bcrypt.check_password_hash(user.password, password):
            login_user(user)
            return 'loged in'
        else:
            return 'failed'
    @user.route('/api/auth/logout',methods=['GET'])
    def logout():
        logout_user()
        return 'loged out'