import json
from sqlalchemy import text
from . import db


from sqlalchemy import text
from . import db

def execute_mysql_query(query_string, params=None, fetch="all"):
    """
    Execute a SQL query using SQLAlchemy and return results in dictionary form.

    query_string : SQL query with optional named parameters
    params       : dictionary of parameters for the query
    fetch        : controls how results are returned
                   - "all"  -> list of rows (default)
                   - "one"  -> single row or None
                   - "none" -> no return value (for INSERT/UPDATE/DELETE)
    """
    # Ensure params is always a dictionary
    params = params or {}

    # Validate fetch mode
    if fetch not in ("all", "one", "none"):
        fetch = "all"

    # Open a database transaction
    with db.engine.begin() as conn:
        result = conn.execute(text(query_string), params)

        # Determine whether the query returned rows
        try:
            returns_rows = result.returns_rows
        except AttributeError:
            # Fallback for older SQLAlchemy versions
            returns_rows = hasattr(result, "cursor") and getattr(result.cursor, "description", None)

        # If the query does not return rows, nothing needs to be fetched
        if not returns_rows:
            return None

        # Preferred path for newer SQLAlchemy versions
        try:
            mappings = result.mappings()
            if fetch == "one":
                row = mappings.first()
                return row if row is not None else None
            else:
                return list(mappings.all())
        except AttributeError:
            # Fallback path for older SQLAlchemy versions
            rows = result.fetchall()
            keys = result.keys()
            dict_rows = [dict(zip(keys, row)) for row in rows]

            if fetch == "one":
                return dict_rows[0] if dict_rows else None
            else:
                return dict_rows


def parse_ingredients(ingredients_dict, filter_word, remove_prefix=False):
    """
    Extract ingredient values from form data and convert them into JSON.

    ingredients_dict : dictionary of submitted form values
    filter_word      : prefix used to identify ingredient fields
    remove_prefix    : whether to remove the prefix from ingredient names

    Returns a JSON string representing ingredient name → quantity.
    """
    parsed_ingredient_dict = {}

    # Loop through all submitted form keys
    for key in list(ingredients_dict.keys()):
        if filter_word in key and ingredients_dict[key] != '':
            # Determine final ingredient name
            if not remove_prefix:
                new_key = key.replace(filter_word, '')
            else:
                new_key = key.removeprefix(filter_word)

            # Store ingredient quantity
            parsed_ingredient_dict[new_key] = ingredients_dict[key]

    # Convert dictionary into JSON for database storage
    return json.dumps(parsed_ingredient_dict)


def get_tag_keys(tags):
    """
    Convert stored tag flags into a list of active tag names.
    """
    tag_list = []
    for tag_dict in tags:
        if list(tag_dict.values())[0] == 1:
            tag_list.append(list(tag_dict.keys())[0])
    return tag_list


def get_tags(tags):
    """
    Convert selected tag names into a dictionary of database-ready flags.
    """
    from .variables import tag_list, tag_list_backend

    parsed_tags = {}

    # Mark selected tags as 1 and others as 0
    for tag in tag_list:
        if tag in tags:
            parsed_tags[tag.replace('/', '_')] = "1"
        else:
            parsed_tags[tag.replace('/', '_')] = "0"

    return parsed_tags


# Dictionary mapping ingredient names to emojis for UI display
INGREDIENT_EMOJIS = {
    # Fresh ingredients
    "Beans (Green)": "\U0001FAD8",
    "Carrots": "\U0001F955",
    "Cauliflower": "\U0001F966",
    "Cilantro": "\U0001F33F",
    "Curry Leaves": "\U0001F33F",
    "Drumstick (Moringa)": "\U0001F952",
    "Garlic": "\U0001F9C4",
    "Ginger": "\U0001FADA",
    "Green Chilies": "\U0001F336",
    "Lemon": "\U0001F34B",
    "Mint": "\U0001F33F",
    "Onions (Red)": "\U0001F9C5",
    "Onions (White)": "\U0001F9C5",
    "Peas": "\U0001FADB",
    "Peppers (Green)": "\U0001FAD1",
    "Potatoes (Baking)": "\U0001F954",
    "Potatoes (New)": "\U0001F954",
    "Spinach": "\U0001F96C",
    "Tomatoes": "\U0001F345",

    # Tinned and packaged ingredients
    "Chickpeas": "\U0001F96B",
    "Coconut Milk": "\U0001F965",
    "Kidney Beans": "\U0001FAD8",
    "Plum Tomatoes": "\U0001F345",
    "Tamarind Paste": "\U0001F963",
    "Tomato Puree": "\U0001F345",

    # Dry ingredients
    "Basmati Rice": "\U0001F35A",
    "Biryani Masala": "\U0001F9C2",
    "Bread Rolls": "\U0001F956",
    "Cashew Nuts": "\U0001F95C",
    "Chole Masala": "\U0001F9C2",
    "Coriander Powder": "\U0001F9C2",
    "Cumin Seeds": "\U0001F9C2",
    "Flour (Maida)": "\U0001F33E",
    "Gram Flour (Besan)": "\U0001F33E",
    "Idli Rava": "\U0001F33E",
    "Masoor Dal": "\U0001FAD8",
    "Mustard Seeds": "\U0001F9C2",
    "Peanuts": "\U0001F95C",
    "Poha (Flattened Rice)": "\U0001F35A",
    "Rajma Masala": "\U0001F9C2",
    "Sambar Powder": "\U0001F9C2",
    "Semolina": "\U0001F33E",
    "Toor Dal": "\U0001FAD8",
    "Turmeric": "\U0001F9C2",
    "Whole Spices (Pulao Mix)": "\U0001F9C2",
    "Whole Wheat Flour": "\U0001F33E",

    # Dairy and fats
    "Butter": "\U0001F9C8",
    "Cream": "\U0001F95B",
    "Ghee": "\U0001F9C8",
    "Paneer": "\U0001F9C0",
    "Yogurt": "\U0001F963",
}


def ingredient_emoji(name: str) -> str:
    """
    Return the emoji associated with an ingredient name.
    If no emoji exists, return an empty string.
    """
    if not name:
        return ""
    return INGREDIENT_EMOJIS.get(name, "")


def ingredient_with_emoji(name: str) -> str:
    """
    Jinja-friendly helper that returns the ingredient name
    with its emoji prepended, if available.
    """
    e = ingredient_emoji(name)
    return f"{e} {name}" if e else str(name)
