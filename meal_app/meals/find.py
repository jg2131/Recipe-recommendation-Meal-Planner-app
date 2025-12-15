from flask import Blueprint, render_template, request, redirect, url_for
import json
from ..utilities import execute_mysql_query

# Blueprint responsible for finding and viewing details of a single meal
find = Blueprint('find', __name__, template_folder='templates', static_folder='../static')


@find.route('/find', methods=['GET', 'POST'])
def index():
    # Fetch all meal names so the user can select one to view
    query_string = "SELECT Name FROM MealsTable;"
    results = execute_mysql_query(query_string)
    meals = [result['Name'] for result in results]

    if request.method == "POST":
        # Read the selected meal from the form and redirect to its detail page
        details = request.form
        query_string = "SELECT * FROM MealsTable WHERE Name = :meal"
        results = execute_mysql_query(query_string, {"meal": details['Meal']}, fetch="all")
        return redirect(url_for('find.some_meal_page', meal=results[0]['Name']))

    # Show the meal selection page
    return render_template(
        'find.html',
        len_meals=len(meals),
        meals=meals
    )


@find.route('/find/<meal>', methods=['GET', 'POST'])
def some_meal_page(meal):
    if request.method == "GET":
        # Fetch full details for the selected meal from the database
        query = "SELECT * FROM MealsTable WHERE Name = :meal"
        result = execute_mysql_query(query, {"meal": meal}, fetch="all")

        # If the meal does not exist, return a 404 error
        if not result:
            return f"No meal found with name {meal}", 404

        row = result[0]

        # Build location information (either website or book/page)
        location_details = {}
        if row.get('Website') is None or row.get('Website') == '':
            location_details['Book'] = row.get('Book')
            location_details['Page'] = row.get('Page')
        else:
            location_details['Website'] = row.get('Website')

        # Parse ingredient JSON fields into lists for rendering
        fresh_ingredients = [
            list(json.loads(row['Fresh_Ingredients']).keys()),
            list(json.loads(row['Fresh_Ingredients']).values())
        ]
        tinned_ingredients = [
            list(json.loads(row['Tinned_Ingredients']).keys()),
            list(json.loads(row['Tinned_Ingredients']).values())
        ]
        dry_ingredients = [
            list(json.loads(row['Dry_Ingredients']).keys()),
            list(json.loads(row['Dry_Ingredients']).values())
        ]
        dairy_ingredients = [
            list(json.loads(row['Dairy_Ingredients']).keys()),
            list(json.loads(row['Dairy_Ingredients']).values())
        ]

        # Import master ingredient lists to determine correct units for display
        from ..variables import (
            fresh_ingredients as FRESH_LIST,
            tinned_ingredients as TINNED_LIST,
            dry_ingredients as DRY_LIST,
            dairy_ingredients as DAIRY_LIST,
        )

        # Build a mapping of ingredient name to its unit (g, ml, tins, etc.)
        units_map = {}
        for name, unit in (FRESH_LIST + TINNED_LIST + DRY_LIST + DAIRY_LIST):
            units_map[name] = unit

        # Format ingredient values with their appropriate units
        def _format_with_unit(val, name):
            unit = units_map.get(name)
            if not unit:
                return str(val)

            # Convert value to number when possible for cleaner formatting
            try:
                num = float(val)
                num_disp = int(num) if num.is_integer() else num
            except (TypeError, ValueError):
                return f"{val} {unit}"

            # Handle singular/plural for tins
            if unit == "tins":
                return f"{num_disp} {'tin' if num == 1 else 'tins'}"

            # For other units, simply append the unit label
            return f"{num_disp} {unit}"

        # Apply unit formatting to each ingredient category
        fresh_ingredients[1] = [
            _format_with_unit(fresh_ingredients[1][idx], fresh_ingredients[0][idx])
            for idx, _ in enumerate(fresh_ingredients[1])
        ]

        tinned_ingredients[1] = [
            _format_with_unit(tinned_ingredients[1][idx], tinned_ingredients[0][idx])
            for idx, _ in enumerate(tinned_ingredients[1])
        ]

        dry_ingredients[1] = [
            _format_with_unit(dry_ingredients[1][idx], dry_ingredients[0][idx])
            for idx, _ in enumerate(dry_ingredients[1])
        ]

        dairy_ingredients[1] = [
            _format_with_unit(dairy_ingredients[1][idx], dairy_ingredients[0][idx])
            for idx, _ in enumerate(dairy_ingredients[1])
        ]

        # Render the results page showing meal details and formatted ingredients
        return render_template(
            'find_results.html',
            meal_name=meal,
            location_details=location_details, location_keys=location_details.keys(),
            staple=row.get('Staple'),
            len_fresh_ingredients=len(fresh_ingredients[0]),
            fresh_ingredients_keys=fresh_ingredients[0],
            fresh_ingredients_values=fresh_ingredients[1],
            len_tinned_ingredients=len(tinned_ingredients[0]),
            tinned_ingredients_keys=tinned_ingredients[0],
            tinned_ingredients_values=tinned_ingredients[1],
            len_dry_ingredients=len(dry_ingredients[0]),
            dry_ingredients_keys=dry_ingredients[0],
            dry_ingredients_values=dry_ingredients[1],
            len_dairy_ingredients=len(dairy_ingredients[0]),
            dairy_ingredients_keys=dairy_ingredients[0],
            dairy_ingredients_values=dairy_ingredients[1]
        )
    else:
        # For POST or unexpected access, redirect back to the search page
        return redirect(url_for('find.index'))
