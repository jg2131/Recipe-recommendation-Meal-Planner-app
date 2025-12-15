from flask import Blueprint, render_template, request, redirect, url_for
from pathlib import Path
from ..utilities import execute_mysql_query

# Blueprint responsible for deleting meals and saved meal plans
delete = Blueprint('delete', __name__, template_folder='templates', static_folder='../static')


def _list_meal_names() -> list[str]:
    # Fetch all meal names from the database so they can be shown for deletion
    rows = execute_mysql_query("SELECT Name FROM MealsTable ORDER BY Name ASC;", fetch="all") or []
    return [r["Name"] for r in rows]


def delete_meals(meal_names: list[str]) -> None:
    # Delete selected meals from the database using a parameterized query
    if not meal_names:
        return
    placeholders = ", ".join([f":n{i}" for i in range(len(meal_names))])
    params = {f"n{i}": name for i, name in enumerate(meal_names)}
    execute_mysql_query(
        f"DELETE FROM MealsTable WHERE Name IN ({placeholders})",
        params,
        fetch="none"
    )


# Directory where saved meal plans are stored as JSON files
SAVED_DIR = Path.cwd() / "saved_meal_plans"


def _valid_json_file(p: Path) -> bool:
    # Check that the file exists and is not empty
    try:
        return p.is_file() and p.stat().st_size > 0
    except Exception:
        return False


def _list_saved_names() -> list[str]:
    # Collect the names of all saved meal plans from the saved_meal_plans directory
    names = set()
    if SAVED_DIR.exists():
        for p in SAVED_DIR.glob("*.json"):
            if _valid_json_file(p):
                names.add(p.stem)
        for p in SAVED_DIR.glob("*"):
            if p.suffix == "" and _valid_json_file(p):
                names.add(p.name)
    return sorted(names)


def _resolve_plan_path(name: str) -> Path | None:
    # Determine the actual file path for a saved meal plan
    candidates: list[Path] = [
        SAVED_DIR / f"{name}.json",
        SAVED_DIR / name,
    ]
    for p in candidates:
        if p.exists():
            return p
    return None


def delete_plans(plan_names: list[str]) -> None:
    # Delete the selected meal plan files from disk
    for name in plan_names:
        p = _resolve_plan_path(name)
        if p:
            p.unlink(missing_ok=True)


@delete.route('/delete', methods=['GET', 'POST'])
def delete_meal_plan():
    # Get available meals and saved planners to display on the delete page
    meals = _list_meal_names()
    planners = _list_saved_names()

    # If there is nothing to delete, show a separate message page
    if not meals and not planners:
        return render_template('no_meal_plans.html')

    if request.method == "POST":
        submit = request.form.get('submit', '')

        # Handle deletion of meals stored in the database
        if submit == 'Delete Meals':
            selected = [v for k, v in request.form.items() if k.startswith('Meal ')]
            if not selected:
                return redirect(url_for('delete.delete_meal_plan'))
            delete_meals(selected)
            return render_template('delete_complete.html', message='Meals deleted')

        # Handle deletion of saved meal planner files
        if submit == 'Delete Meal Planner':
            selected = [v for k, v in request.form.items() if k.startswith('Plan ')]
            if not selected:
                return redirect(url_for('delete.delete_meal_plan'))
            delete_plans(selected)
            return render_template('delete_complete.html', message='Meal planners deleted')

        # Fallback redirect if no valid action was selected
        return redirect(url_for('delete.delete_meal_plan'))

    # For GET requests, show the delete page with available options
    return render_template('delete.html', meals=meals, planners=planners)
