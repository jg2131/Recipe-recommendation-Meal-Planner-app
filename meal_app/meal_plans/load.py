from flask import Blueprint, render_template, request, redirect, url_for, session, current_app
from pathlib import Path
import json
from ..utilities import execute_mysql_query

# Blueprint responsible for loading saved meal plans or loading a single meal
load = Blueprint('load', __name__, template_folder='templates', static_folder='../static')

def candidate_dirs():
    """
    Return the possible folders where saved meal plans may exist.
    We check both the project-level folder and the app-level folder so the code works
    even if the app is run from different working directories.
    """
    app_root = Path(current_app.root_path)
    project_root = app_root.parent
    return [
        project_root / "saved_meal_plans",
        app_root / "saved_meal_plans",
    ]

def list_saved_plans():
    """
    Look for saved meal plans in the candidate folders.
    We accept both:
    - files ending in .json
    - files with no extension (older saves that may have been created differently)
    The function returns a sorted list of plan names shown in the UI.
    """
    names = set()
    for d in candidate_dirs():
        if not d.exists():
            continue

        # Add all .json plan files using the filename without extension
        for p in d.glob("*.json"):
            names.add(p.stem)

        # Also accept files without extension to support older saved plans
        for p in d.glob("*"):
            if p.is_file() and p.suffix == "":
                names.add(p.name)
    return sorted(names)

def resolve_plan_path(meal_plan: str) -> Path | None:
    """
    Try to locate the actual file for the requested plan name.
    We try both forms:
    - <name>.json
    - <name> (no extension)
    Returns the first match found, otherwise returns None.
    """
    for d in candidate_dirs():
        cand_json = d / f"{meal_plan}.json"
        if cand_json.exists():
            return cand_json
        cand_raw = d / meal_plan
        if cand_raw.exists():
            return cand_raw
    return None

@load.route('/load', methods=['GET', 'POST'])
def choose_meal_plan():
    # Get a list of saved plans from disk and a list of meals from the database
    meal_plans = list_saved_plans()
    rows = execute_mysql_query("SELECT Name FROM MealsTable ORDER BY Name ASC;", fetch="all") or []
    meals = [r["Name"] for r in rows]

    # If there are no saved plans and no meals in the database, show the empty page
    if not meal_plans and not meals:
        return render_template('no_meal_plans.html')

    if request.method == "POST":
        # Some templates may use 'Meal Plan' and others may use 'Meal_Plan', so accept both
        selected = request.form.get('Meal Plan') or request.form.get('Meal_Plan')
        if not selected:
            return redirect(url_for('load.choose_meal_plan'))

        # The dropdown may store values as 'plan:<name>' or 'meal:<name>' to avoid confusion
        # We also support plain names for backwards compatibility
        if selected.startswith('plan:'):
            name = selected.split(':', 1)[1]
            return redirect(url_for('load.load_meal_plan', meal_plan=name))
        if selected.startswith('meal:'):
            name = selected.split(':', 1)[1]
            return redirect(url_for('load.load_single_meal', meal=name))

        # If it is a plain name, treat it as a plan if it exists in saved plans
        if selected in meal_plans:
            return redirect(url_for('load.load_meal_plan', meal_plan=selected))
        return redirect(url_for('load.load_single_meal', meal=selected))

    # Show the load page with both lists so the user can choose what to load
    return render_template('load.html',
                           len_meal_plans=len(meal_plans), meal_plans=meal_plans,
                           len_meals=len(meals), meals=meals)

@load.route('/load/<meal_plan>', methods=['GET', 'POST'])
def load_meal_plan(meal_plan):
    # Find the saved plan file on disk
    plan_path = resolve_plan_path(meal_plan)
    if not plan_path:
        # If it does not exist, go back to the chooser page
        return redirect(url_for('load.choose_meal_plan'))

    # Load the JSON meal plan into the session so the display page can render it
    with plan_path.open("r", encoding="utf-8") as f:
        session['complete_ingredient_dict'] = json.load(f)

    return redirect(url_for('display.display_meal_plan'))


@load.route('/load/meal/<meal>', methods=['GET'])
def load_single_meal(meal):
    """Build a complete_ingredient_dict for a single meal from the DB and display it."""
    # Fetch ingredient buckets for the selected meal from the database
    row = execute_mysql_query(
        """
        SELECT Fresh_Ingredients, Tinned_Ingredients, Dry_Ingredients, Dairy_Ingredients
        FROM MealsTable WHERE Name = :name
        """,
        {"name": meal},
        fetch="one",
    )
    if not row:
        return redirect(url_for('load.choose_meal_plan'))

    # Convert JSON values into Python dictionaries, treating empty/null as {}
    def _loads(v):
        if v in (None, "", "null"):
            return {}
        return json.loads(v)

    # Build the same structure used by the create flow so the display page works normally
    complete_ingredient_dict = {
        "Fresh_Ingredients": _loads(row.get("Fresh_Ingredients")),
        "Tinned_Ingredients": _loads(row.get("Tinned_Ingredients")),
        "Dry_Ingredients": _loads(row.get("Dry_Ingredients")),
        "Dairy_Ingredients": _loads(row.get("Dairy_Ingredients")),
        "Extra_Ingredients": [],
        "Meal_List": [meal],
    }

    # Also include a per-meal breakdown so the display page can show detailed sections
    complete_ingredient_dict["Per_Meal_Ingredients"] = [{
        "Name": meal,
        "Fresh_Ingredients": complete_ingredient_dict["Fresh_Ingredients"],
        "Tinned_Ingredients": complete_ingredient_dict["Tinned_Ingredients"],
        "Dry_Ingredients": complete_ingredient_dict["Dry_Ingredients"],
        "Dairy_Ingredients": complete_ingredient_dict["Dairy_Ingredients"],
    }]

    # Store the result in the session and redirect to the display page
    session['complete_ingredient_dict'] = complete_ingredient_dict
    return redirect(url_for('display.display_meal_plan'))
