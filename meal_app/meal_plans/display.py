from flask import Blueprint, redirect, url_for, render_template, request, session
import os
import json
from datetime import datetime
from ..utilities import execute_mysql_query
import re

# Blueprint responsible for displaying a created meal plan and handling save/update actions
display = Blueprint('display', __name__, template_folder='templates', static_folder='../static')


def _safe_name(name: str) -> str:
    """Sanitize a user-provided name for use as a filename on Windows/Linux."""
    # Remove characters that are not safe in filenames and replace them with underscores
    name = re.sub(r"[^A-Za-z0-9 _\-]+", "_", name or "").strip()
    # If the name ends up empty, use a default filename
    return name or "Meal_Plan"


def save_meal_plan(complete_ingredient_dict, plan_name: str | None = None):
    """Saves created meal plan to the local saved_meal_plans directory.

    If plan_name is provided, use it (safely) for the filename; otherwise use a
    Windows-safe timestamp (no colon characters).
    """
    # Create the folder where meal plans will be saved if it does not exist yet
    if not os.path.exists('saved_meal_plans'):
        os.makedirs('saved_meal_plans')

    # Convert the meal plan dictionary into nicely formatted JSON text
    json_file = json.dumps(complete_ingredient_dict, indent=4)

    # Choose a filename base either from user input or a timestamp
    if plan_name:
        base = _safe_name(plan_name)
    else:
        base = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    filename = f"{base}.json"
    path = os.path.join('saved_meal_plans', filename)

    # If the filename already exists, add a timestamp so we don’t overwrite the existing file
    if os.path.exists(path):
        suffix = datetime.now().strftime("_%Y%m%d_%H%M%S")
        path = os.path.join('saved_meal_plans', f"{base}{suffix}.json")

    # Write the meal plan JSON to disk
    with open(path, "w", encoding="utf-8") as f:
        f.write(json_file)

    # Return an absolute path so it can be shown to the user on the confirmation page
    file_path = os.path.join(os.getcwd(), path)
    return file_path


def create_meal_info_table(rows):
    """Creates a nested list of meal information for rendering in display.html."""
    # Build a simple list format so the template can display a meal name + source info
    meal_info_list = []
    for meal in rows:
        name = meal.get('Name', '')
        website = meal.get('Website') or ''
        book = meal.get('Book') or ''
        page = meal.get('Page') or ''
        # Prefer website if available, otherwise fall back to book/page info
        meal_info_list.append(
            [name, website] if website else [name, f"{book}, page {page}"]
        )
    return meal_info_list


def append_ingredient_units(fresh_ingredients, tinned_ingredients, dry_ingredients, dairy_ingredients):
    """Appends unit suffixes to ingredient quantities where appropriate."""
    from ..variables import gram_list

    # Add units for fresh ingredients (grams or bulbs for onions)
    def _fresh_unit(val, name):
        if name in gram_list:
            return f"{val} g"
        if name in ("Onions (Red)", "Onions (White)"):
            return f"{val} bulbs"
        return str(val)

    fresh_ingredients[1] = [
        _fresh_unit(fresh_ingredients[1][idx], fresh_ingredients[0][idx])
        for idx, _ in enumerate(fresh_ingredients[1])
    ]

    # Add units for tinned ingredients (grams for some items, otherwise tin/tins)
    def _tinned_unit(val, name):
        if name in gram_list:
            return f"{val} g"
        try:
            num = float(val)
        except (TypeError, ValueError):
            return str(val)
        if num <= 1:
            return f"{int(num) if num.is_integer() else num} tin"
        return f"{int(num) if num.is_integer() else num} tins"

    tinned_ingredients[1] = [
        _tinned_unit(tinned_ingredients[1][idx], tinned_ingredients[0][idx])
        for idx, _ in enumerate(tinned_ingredients[1])
    ]

    # Add grams for dry ingredients that are measured in grams
    dry_ingredients[1] = [
        f"{dry_ingredients[1][idx]} g" if dry_ingredients[0][idx] in gram_list else str(dry_ingredients[1][idx])
        for idx, _ in enumerate(dry_ingredients[1])
    ]

    # Add grams for dairy items in gram_list, add ml for milk, otherwise keep as-is
    dairy_ingredients[1] = [
        (f"{dairy_ingredients[1][idx]} g" if dairy_ingredients[0][idx] in gram_list
         else f"{dairy_ingredients[1][idx]} ml" if str(dairy_ingredients[0][idx]) == 'Milk'
         else str(dairy_ingredients[1][idx]))
        for idx, _ in enumerate(dairy_ingredients[1])
    ]
    return fresh_ingredients, tinned_ingredients, dry_ingredients, dairy_ingredients


@display.route('/display', methods=['GET', 'POST'])
def display_meal_plan():
    # GET request is used to show the meal plan results
    if request.method == "GET":
        # Pull the meal plan dictionary from the session
        complete_ingredient_dict = session.pop('complete_ingredient_dict', None)
        if not complete_ingredient_dict:
            return redirect(url_for('create.create_meal_plan'))

        # Put it back so it remains available for POST actions like Save/Update Dates
        session['complete_ingredient_dict'] = complete_ingredient_dict

        # Get the list of meals selected by the user
        meal_list = complete_ingredient_dict.get('Meal_List', []) or []
        if not meal_list:
            # If no meals are present, redirect back to the create meal plan page
            return redirect(url_for('create.create_meal_plan'))

        # Build a safe parameterized IN clause to query info for only the selected meals
        placeholders = ", ".join([f":n{i}" for i in range(len(meal_list))])
        params = {f"n{i}": name for i, name in enumerate(meal_list)}

        # Fetch book/page/website details for the selected meals
        query_string = f"""
            SELECT Name, Book, Page, Website
            FROM MealsTable
            WHERE Name IN ({placeholders});
        """
        results = execute_mysql_query(query_string, params, fetch="all") or []
        info_meal_list = create_meal_info_table(results)

        # Build a dictionary mapping meal name -> info string so templates can access it easily
        info_by_name = {}
        for row in info_meal_list:
            if isinstance(row, list) and row:
                nm = row[0]
                info_by_name[nm] = row[1] if len(row) > 1 else ""

        # Build per-meal ingredient tables to show the shopping list meal-by-meal
        per_meal = complete_ingredient_dict.get('Per_Meal_Ingredients') or []
        meals_detailed = []
        for name in meal_list:
            # Find the ingredient breakdown for this meal
            m = next((x for x in per_meal if x.get('Name') == name), None)
            if not m:
                continue

            # Convert ingredient dictionaries into [names, values] lists for unit formatting
            fresh = [list((m.get('Fresh_Ingredients') or {}).keys()), list((m.get('Fresh_Ingredients') or {}).values())]
            tinned = [list((m.get('Tinned_Ingredients') or {}).keys()), list((m.get('Tinned_Ingredients') or {}).values())]
            dry = [list((m.get('Dry_Ingredients') or {}).keys()), list((m.get('Dry_Ingredients') or {}).values())]
            dairy = [list((m.get('Dairy_Ingredients') or {}).keys()), list((m.get('Dairy_Ingredients') or {}).values())]

            # Add units like g/ml/tin(s) to make the display easier to read
            fresh, tinned, dry, dairy = append_ingredient_units(fresh, tinned, dry, dairy)

            # Store everything in a template-friendly structure
            meals_detailed.append({
                'name': name,
                'info': info_by_name.get(name, ''),
                'fresh': list(zip(fresh[0], fresh[1])),
                'tinned': list(zip(tinned[0], tinned[1])),
                'dry': list(zip(dry[0], dry[1])),
                'dairy': list(zip(dairy[0], dairy[1])),
            })

        # If the plan doesn’t have per-meal details (e.g., older saved plans), show only the combined totals
        if not meals_detailed:
            combo_fresh = complete_ingredient_dict.get('Fresh_Ingredients') or {}
            combo_tinned = complete_ingredient_dict.get('Tinned_Ingredients') or {}
            combo_dry = complete_ingredient_dict.get('Dry_Ingredients') or {}
            combo_dairy = complete_ingredient_dict.get('Dairy_Ingredients') or {}

            fresh = [list(combo_fresh.keys()), list(combo_fresh.values())]
            tinned = [list(combo_tinned.keys()), list(combo_tinned.values())]
            dry = [list(combo_dry.keys()), list(combo_dry.values())]
            dairy = [list(combo_dairy.keys()), list(combo_dairy.values())]
            fresh, tinned, dry, dairy = append_ingredient_units(fresh, tinned, dry, dairy)

            meals_detailed.append({
                'name': 'Meal Plan',
                'info': '',
                'fresh': list(zip(fresh[0], fresh[1])),
                'tinned': list(zip(tinned[0], tinned[1])),
                'dry': list(zip(dry[0], dry[1])),
                'dairy': list(zip(dairy[0], dairy[1])),
            })

        # Render the display page with the detailed meal plan information
        return render_template(
            'display.html',
            meals_detailed=meals_detailed,
        )

    # POST request is used for actions like "Save" and "Update Dates"
    complete_ingredient_dict = session.pop('complete_ingredient_dict', None)
    if not complete_ingredient_dict:
        return redirect(url_for('create.create_meal_plan'))
    session['complete_ingredient_dict'] = complete_ingredient_dict

    submit_val = request.form.get('submit', '')
    if submit_val == 'Save':
        # Get the optional plan name from the form and save the meal plan as a JSON file
        plan_name = request.form.get('Plan_Name')
        file_path = save_meal_plan(complete_ingredient_dict, plan_name)
        return render_template('save_complete.html', file_path=file_path)

    if submit_val == 'Update Dates':
        # Use a Windows-safe date format and update Last_Made for meals in this plan
        date_now = datetime.now().strftime("%Y-%m-%d")
        meals = complete_ingredient_dict.get('Meal_List', [])
        if meals:
            for name in meals:
                execute_mysql_query(
                    "UPDATE MealsTable SET Last_Made = :dt WHERE Name = :name",
                    {"dt": date_now, "name": name},
                    fetch="none",
                )
        return redirect(url_for('display.display_meal_plan'))

    # If an unknown action is submitted, return the user back to the create page
    return redirect(url_for('create.create_meal_plan'))
