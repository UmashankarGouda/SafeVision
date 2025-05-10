from flask import render_template

def home_view():
    return render_template('home.html')
