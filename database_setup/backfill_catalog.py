import json
from sqlalchemy import text
from meal_app import create_app, db
from meal_app.variables import (
    fresh_ingredients as VAR_FRESH,
    tinned_ingredients as VAR_TINNED,
    dry_ingredients as VAR_DRY,
    dairy_ingredients as VAR_DAIRY,
)

# These are the allowed tag names we want to make sure exist in the Tags table
TAGS = ['Spring/Summer', 'Autumn/Winter', 'Quick/Easy', 'Special']

# Insert the standard tags into the Tags catalog table if they are not already present
def ensure_tags(conn):
    for t in TAGS:
        conn.execute(text("INSERT IGNORE INTO Tags (Tag_Name) VALUES (:t)"), {"t": t})

# Insert an ingredient name into the Ingredients catalog table if it is valid and not already present
def upsert_ingredient_name(conn, name: str):
    if not name:
        return
    conn.execute(
        text("INSERT IGNORE INTO Ingredients (Ingredient_Name) VALUES (:n)"),
        {"n": name},
    )

# Take one ingredient bucket (fresh/tinned/dry/dairy) and extract ingredient names from it
# The bucket may come as a JSON string or a Python dictionary depending on how it was stored/read
def process_bucket(conn, bucket):
    if not bucket:
        return
    if isinstance(bucket, str):
        try:
            data = json.loads(bucket)
        except Exception:
            data = {}
    elif isinstance(bucket, dict):
        data = bucket
    else:
        data = {}
    for name in data.keys():
        upsert_ingredient_name(conn, name)

def main():
    # Create the Flask app so we can access the database through its application context
    app = create_app()
    with app.app_context():
        # Open a transaction so all inserts happen safely and get committed automatically
        with db.engine.begin() as conn:
            # Make sure the Tags table has the standard set of tag values
            ensure_tags(conn)

            # Read all ingredient buckets from MealsTable and use them to populate Ingredients catalog
            rows = conn.execute(text("SELECT Fresh_Ingredients, Tinned_Ingredients, Dry_Ingredients, Dairy_Ingredients FROM MealsTable")).mappings().all()
            for r in rows:
                process_bucket(conn, r.get("Fresh_Ingredients"))
                process_bucket(conn, r.get("Tinned_Ingredients"))
                process_bucket(conn, r.get("Dry_Ingredients"))
                process_bucket(conn, r.get("Dairy_Ingredients"))

    # Print a confirmation once catalogs have been refreshed
    print("✔ Catalogs refreshed: Ingredients, Tags.")

# Run the script only when executed directly (not when imported as a module)
if __name__ == "__main__":
    main()
