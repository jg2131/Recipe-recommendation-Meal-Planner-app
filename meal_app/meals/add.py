from flask import Blueprint, render_template, request, redirect, url_for
import json
from ..utilities import execute_mysql_query, parse_ingredients, get_tag_keys, get_tags
from ..variables import (
    staples_list,
    fresh_ingredients, tinned_ingredients, dry_ingredients, dairy_ingredients,
    tag_list
)

# Blueprint responsible for adding a new meal into the database
add = Blueprint('add', __name__, template_folder='templates', static_folder='../static')


@add.route('/add', methods=['GET', 'POST'])
def index():
    # Build the data needed to populate dropdowns and ingredient inputs on the Add Meal form
    context = {
        "len_staples": len(staples_list),
        "staples": staples_list,

        "len_fresh_ingredients": len(fresh_ingredients),
        "fresh_ingredients": [ing[0] for ing in fresh_ingredients],
        "fresh_ingredients_units": [ing[1] for ing in fresh_ingredients],

        "len_tinned_ingredients": len(tinned_ingredients),
        "tinned_ingredients": [ing[0] for ing in tinned_ingredients],
        "tinned_ingredients_units": [ing[1] for ing in tinned_ingredients],

        "len_dry_ingredients": len(dry_ingredients),
        "dry_ingredients": [ing[0] for ing in dry_ingredients],
        "dry_ingredients_units": [ing[1] for ing in dry_ingredients],

        "len_dairy_ingredients": len(dairy_ingredients),
        "dairy_ingredients": [ing[0] for ing in dairy_ingredients],
        "dairy_ingredients_units": [ing[1] for ing in dairy_ingredients],

        "len_tags": len(tag_list),
        "tags": tag_list,
    }

    if request.method == "POST":
        # Convert submitted form fields into a normal Python dictionary
        details_dict = request.form.to_dict()

        # Read and clean required fields
        name = (details_dict.get("Name") or "").strip()
        staple = (details_dict.get("Staple") or "").strip()

        # Make sure the meal has a name and staple category before inserting into the DB
        if not name or not staple:
            context["error"] = "Please enter a meal name and select a staple."
            return render_template("add.html", **context)

        # Collect tag selections and convert them into DB-ready boolean flags
        tag_values = [v for k, v in details_dict.items() if "Tag" in k]
        tags = get_tags(tag_values)

        # SQL query used to insert a new meal record
        query = """
        INSERT INTO MealsTable
        (Name, Staple,
         Fresh_Ingredients, Tinned_Ingredients, Dry_Ingredients, Dairy_Ingredients,
         Last_Made, Spring_Summer, Autumn_Winter, Quick_Easy, Special)
        VALUES
        (:name, :staple,
         :fresh_ing, :tinned_ing, :dry_ing, :dairy_ing,
         :last_made, :spring, :autumn, :quick, :special)
        """

        # Build parameters for the insert query using the submitted form data
        # Ingredient fields are parsed into JSON strings before being stored in the database
        params = {
            "name": name,
            "staple": staple,
            "fresh_ing": parse_ingredients(details_dict, "Fresh "),
            "tinned_ing": parse_ingredients(details_dict, "Tinned "),
            "dry_ing": parse_ingredients(details_dict, "Dry "),
            "dairy_ing": parse_ingredients(details_dict, "Dairy "),
            "last_made": "2021-01-01",  # placeholder
            "spring": tags["Spring_Summer"],
            "autumn": tags["Autumn_Winter"],
            "quick": tags["Quick_Easy"],
            "special": tags["Special"],
        }

        # Run the insert and show any database error on the page if it happens
        try:
            execute_mysql_query(query, params, fetch="none")
        except Exception as e:
            context["error"] = f"Database error: {e}"
            return render_template("add.html", **context)

        # After successfully adding the meal, redirect to a confirmation page
        return redirect(url_for("add.confirmation", meal=name))

    # For GET requests, simply show the Add Meal form
    return render_template("add.html", **context)


@add.route('/add_confirmation/<meal>', methods=['GET', 'POST'])
def confirmation(meal):
    if request.method == "GET":
        # Fetch the meal row from the database to display it back to the user
        query_string = "SELECT * FROM MealsTable WHERE Name = :meal"
        result = execute_mysql_query(query_string, {"meal": meal}, fetch="all")

        # If no data is found, return a 404 response
        if not result:
            return f"No meal found with name {meal}", 404

        row = result[0]

        # Build the location/source information (Website OR Book+Page) for the template
        location_details = {}
        if row.get('Website'):
            location_details['Website'] = row['Website']
        elif row.get('Book'):
            location_details['Book'] = row.get('Book', '')
            location_details['Page'] = row.get('Page', '')
        else:
            # Keep a safe default so the template can render without crashing
            location_details['Website'] = ''

        # Load ingredient JSON from database columns into Python dictionaries
        fresh = json.loads(row['Fresh_Ingredients']) if row.get('Fresh_Ingredients') else {}
        tinned = json.loads(row['Tinned_Ingredients']) if row.get('Tinned_Ingredients') else {}
        dry = json.loads(row['Dry_Ingredients']) if row.get('Dry_Ingredients') else {}
        dairy = json.loads(row['Dairy_Ingredients']) if row.get('Dairy_Ingredients') else {}

        # Convert dictionaries into key/value lists for easy rendering in HTML tables
        fresh_ingredients_data = [list(fresh.keys()), list(fresh.values())]
        tinned_ingredients_data = [list(tinned.keys()), list(tinned.values())]
        dry_ingredients_data = [list(dry.keys()), list(dry.values())]
        dairy_ingredients_data = [list(dairy.keys()), list(dairy.values())]

        # Convert stored tag flags into the list of tag labels expected by the template
        tags_raw = [
            {"Spring/Summer": row.get('Spring_Summer')},
            {"Autumn/Winter": row.get('Autumn_Winter')},
            {"Quick/Easy": row.get('Quick_Easy')},
            {"Special": row.get('Special')},
        ]
        tags = get_tag_keys(tags_raw)

        # Render the confirmation page showing the meal that was just added
        return render_template(
            'add_confirmation.html',
            meal_name=meal,
            location_details=location_details, location_keys=location_details.keys(),
            staple=row.get('Staple', ''),
            len_fresh_ingredients=len(fresh_ingredients_data[0]), fresh_ingredients_keys=fresh_ingredients_data[0], fresh_ingredients_values=fresh_ingredients_data[1],
            len_tinned_ingredients=len(tinned_ingredients_data[0]), tinned_ingredients_keys=tinned_ingredients_data[0], tinned_ingredients_values=tinned_ingredients_data[1],
            len_dry_ingredients=len(dry_ingredients_data[0]), dry_ingredients_keys=dry_ingredients_data[0], dry_ingredients_values=dry_ingredients_data[1],
            len_dairy_ingredients=len(dairy_ingredients_data[0]), dairy_ingredients_keys=dairy_ingredients_data[0], dairy_ingredients_values=dairy_ingredients_data[1],
            len_tags=len(tags), tags=tags,
        )

    # If the user clicks the return button (POST), send them back to the Add Meal page
    return redirect(url_for('add.index'))
