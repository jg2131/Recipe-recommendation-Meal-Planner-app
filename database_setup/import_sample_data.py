import json
from pathlib import Path
from sqlalchemy import text
from meal_app import create_app, db

# Path to the JSON file that contains sample meal data
JSON_PATH = Path(__file__).resolve().parent / "sample_database_data.json"

# SQL statement to create the MealsTable if it does not already exist
# This table stores meal details, ingredients as JSON, and seasonal/tag flags
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS MealsTable (
  Meal_ID INT AUTO_INCREMENT PRIMARY KEY,
  Name VARCHAR(255) NOT NULL,
  Staple VARCHAR(100),
  Book VARCHAR(100),
  Page VARCHAR(10),
  Website VARCHAR(255),
  Fresh_Ingredients JSON NULL,
  Tinned_Ingredients JSON NULL,
  Dry_Ingredients JSON NULL,
  Dairy_Ingredients JSON NULL,
  Last_Made DATE NULL,
  Spring_Summer TINYINT(1) NOT NULL DEFAULT 0,
  Autumn_Winter TINYINT(1) NOT NULL DEFAULT 0,
  Quick_Easy   TINYINT(1) NOT NULL DEFAULT 0,
  Special      TINYINT(1) NOT NULL DEFAULT 0,
  UNIQUE KEY uk_meal_name (Name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""

# SQL statement used to insert a new meal or update it if the name already exists
INSERT_SQL = text("""
INSERT INTO MealsTable
  (Name, Staple, Book, Page, Website,
   Fresh_Ingredients, Tinned_Ingredients, Dry_Ingredients, Dairy_Ingredients,
   Last_Made, Spring_Summer, Autumn_Winter, Quick_Easy, Special)
VALUES
  (:Name, :Staple, :Book, :Page, :Website,
   :Fresh_Ingredients, :Tinned_Ingredients, :Dry_Ingredients, :Dairy_Ingredients,
   NULL, 0, 0, 0, 0)
ON DUPLICATE KEY UPDATE
  Staple=VALUES(Staple),
  Book=VALUES(Book),
  Page=VALUES(Page),
  Website=VALUES(Website),
  Fresh_Ingredients=VALUES(Fresh_Ingredients),
  Tinned_Ingredients=VALUES(Tinned_Ingredients),
  Dry_Ingredients=VALUES(Dry_Ingredients),
  Dairy_Ingredients=VALUES(Dairy_Ingredients);
""")

def main():
    # Check that the sample JSON file exists before continuing
    if not JSON_PATH.exists():
        raise FileNotFoundError(f"Could not find JSON file at: {JSON_PATH}")

    # Load meal data from the JSON file
    data = json.loads(JSON_PATH.read_text(encoding="utf-8"))

    # Create the Flask application so database access works correctly
    app = create_app()
    with app.app_context():
        # Create the MealsTable if it does not already exist
        with db.engine.begin() as conn:
            conn.execute(text(CREATE_TABLE_SQL))

            # Remove any existing rows so only the current sample data is stored
            conn.execute(text("TRUNCATE TABLE MealsTable"))

        # Insert or update each meal from the JSON file
        with db.engine.begin() as conn:
            for row in data:
                params = {
                    "Name": row.get("Name", ""),
                    "Staple": row.get("Staple", ""),
                    "Book": row.get("Book", ""),
                    "Page": row.get("Page", ""),
                    "Website": row.get("Website", ""),
                    "Fresh_Ingredients": json.dumps(row.get("Fresh_Ingredients", {})),
                    "Tinned_Ingredients": json.dumps(row.get("Tinned_Ingredients", {})),
                    "Dry_Ingredients": json.dumps(row.get("Dry_Ingredients", {})),
                    "Dairy_Ingredients": json.dumps(row.get("Dairy_Ingredients", {})),
                }
                conn.execute(INSERT_SQL, params)

    # Print confirmation once all data has been inserted successfully
    print(" Imported sample data into MealsTable.")

if __name__ == "__main__":
    main()
