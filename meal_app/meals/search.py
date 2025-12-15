from flask import Blueprint, render_template, request, redirect, url_for, session
import json
from ..utilities import execute_mysql_query

# Blueprint responsible for searching meals by ingredient
search = Blueprint('search', __name__, template_folder='templates', static_folder='../static')


@search.route('/search', methods=['GET', 'POST'])
def index():
    # Fetch ingredient JSON columns from the database to build dropdown lists
    query_string = """
    SELECT Fresh_Ingredients, Tinned_Ingredients, Dry_Ingredients, Dairy_Ingredients
    FROM MealsTable
    WHERE JSON_LENGTH(Fresh_Ingredients) > 0;
    """
    results = execute_mysql_query(query_string, fetch="all")

    # Collect unique ingredient names for each category across all meals
    fresh_ingredients = sorted({key for r in results for key in json.loads(r['Fresh_Ingredients']).keys()})
    tinned_ingredients = sorted({key for r in results for key in json.loads(r['Tinned_Ingredients']).keys()})
    dry_ingredients = sorted({key for r in results for key in json.loads(r['Dry_Ingredients']).keys()})
    dairy_ingredients = sorted({key for r in results for key in json.loads(r['Dairy_Ingredients']).keys()})

    if request.method == "POST":
        # Convert submitted form data into a dictionary
        details_dict = request.form.to_dict()

        ingredient = None
        json_key = None

        # Determine which ingredient category was selected by the user
        if "null" not in details_dict.get("Fresh_Ingredients", "null"):
            json_key = "Fresh_Ingredients"
            ingredient = details_dict[json_key]
        elif "null" not in details_dict.get("Tinned_Ingredients", "null"):
            json_key = "Tinned_Ingredients"
            ingredient = details_dict[json_key]
        elif "null" not in details_dict.get("Dry_Ingredients", "null"):
            json_key = "Dry_Ingredients"
            ingredient = details_dict[json_key]
        elif "null" not in details_dict.get("Dairy_Ingredients", "null"):
            json_key = "Dairy_Ingredients"
            ingredient = details_dict[json_key]

        if ingredient and json_key:
            # Build a query to find meals that contain the selected ingredient
            # This is safe because the ingredient name comes from controlled dropdown lists
            query = f"""
            SELECT *
            FROM MealsTable
            WHERE JSON_EXTRACT({json_key}, '$."{ingredient}"') IS NOT NULL;
            """
            results = execute_mysql_query(query, fetch="all")

            # Store matching meal names in the session so they can be displayed on the results page
            session['meal_list'] = [row['Name'] for row in results]

            return redirect(url_for('search.search_results', ingredient=ingredient))

    # For GET requests, show the ingredient selection page
    return render_template(
        'search.html',
        len_fresh_ingredients=len(fresh_ingredients), fresh_ingredients=fresh_ingredients,
        len_tinned_ingredients=len(tinned_ingredients), tinned_ingredients=tinned_ingredients,
        len_dry_ingredients=len(dry_ingredients), dry_ingredients=dry_ingredients,
        len_dairy_ingredients=len(dairy_ingredients), dairy_ingredients=dairy_ingredients
    )


@search.route('/search/<ingredient>', methods=['GET', 'POST'])
def search_results(ingredient):
    if request.method == "GET":
        # Try to read the list of matching meals from the session
        meals = session.pop('meal_list', None)

        if not meals:
            # Fallback: search for the ingredient across all ingredient categories directly
            query = f"""
            SELECT Name
            FROM MealsTable
            WHERE JSON_EXTRACT(Fresh_Ingredients, '$."{ingredient}"') IS NOT NULL
               OR JSON_EXTRACT(Tinned_Ingredients, '$."{ingredient}"') IS NOT NULL
               OR JSON_EXTRACT(Dry_Ingredients, '$."{ingredient}"') IS NOT NULL
               OR JSON_EXTRACT(Dairy_Ingredients, '$."{ingredient}"') IS NOT NULL;
            """
            results = execute_mysql_query(query, fetch="all")
            meals = [row['Name'] for row in results]

        # Render the results page showing meals that use the selected ingredient
        return render_template(
            'search_results.html',
            ingredient=ingredient,
            len_meals=len(meals),
            meals=meals
        )
    else:
        # Redirect back to the search page for non-GET requests
        return redirect(url_for('search.index'))
