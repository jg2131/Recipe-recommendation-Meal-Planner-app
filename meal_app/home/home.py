from flask import Blueprint, render_template, request, redirect, url_for

# Create a Blueprint for the home page of the application
# This blueprint handles the main menu and navigation
home = Blueprint('home', __name__, template_folder="templates", static_folder='../static')

# Define the route for the home page
# This page handles both displaying the menu and processing button clicks
@home.route("/", methods=['GET', 'POST'])
def index():
    # If the user clicks a button on the home page, handle the action
    if request.method == "POST":
        if request.form['submit'] == 'Add Meal':
            return redirect(url_for('add.index'))
        elif request.form['submit'] == 'Edit Meal':
            return redirect(url_for('edit.index'))
        elif request.form['submit'] == 'Get Meal Info':
            return redirect(url_for('find.index'))
        elif request.form['submit'] == 'Search Ingredients':
            return redirect(url_for('search.index'))
        elif request.form['submit'] == 'List Meals':
            return redirect(url_for('list_meals.index'))
        elif request.form['submit'] == 'Create Meal Plan':
            return redirect(url_for('create.create_meal_plan'))
        elif request.form['submit'] == 'Load Meal Plan':
            return redirect(url_for('load.choose_meal_plan'))
        elif request.form['submit'] == 'Delete Meal Plan':
            return redirect(url_for('delete.delete_meal_plan'))

    # If the page is accessed normally, display the home screen
    return render_template('index.html')
