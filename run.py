from mailapp.app import create_app

flask_app = create_app()

if __name__ == '__main__':
    flask_app.run(debug=True,port=8000)