from flask import Blueprint, render_template, request
import json
from datetime import datetime
from ..utilities import execute_mysql_query
from ..variables import tag_list

# Blueprint responsible for suggesting meals based on selected tags
inspire = Blueprint('inspire', __name__, template_folder='templates', static_folder='../static')


@inspire.route('/inspire', methods=['GET', 'POST'])
def index():
    if request.method == "POST":
        # Read submitted form data
        details = request.form

        # Replace "/" with "_" so the tag matches the database column name
        tag = details['Tag'].replace('/', '_')

        # Build a query to find meals matching the selected tag
        # This is safe because the tag comes from a predefined list
        query_string = f"""
        SELECT Name, Staple, Last_Made
        FROM MealsTable
        WHERE {tag} = 1
        ORDER BY Name;
        """

        # Execute the query and fetch all matching meals
        results = execute_mysql_query(query_string, fetch="all")

        # Extract meal names, staples, and last-made dates for display
        meal_names = [meal['Name'] for meal in results]
        staples = [meal['Staple'] for meal in results]
        last_date = [
            datetime.strftime(meal['Last_Made'], "%d-%m-%Y")
            if meal['Last_Made'] else ""
            for meal in results
        ]

        # Show the results page with the suggested meals
        return render_template(
            'inspire_results.html',
            tag=details['Tag'],
            len_meals=len(meal_names),
            meal_names=meal_names,
            staples=staples,
            last_date=last_date
        )

    # For GET requests, show the tag selection page
    return render_template(
        'inspire.html',
        len_tags=len(tag_list),
        tags=tag_list
    )
