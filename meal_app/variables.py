# meal_app/variables.py

def variable_printer(variable_name, variable):
    """
    Helper function for debugging.
    Prints the variable name, its type, and its contents.
    """
    print(variable_name, "type:", type(variable), "content:")
    print(variable)


# List of books or sources from which meals can come
# This is used in Add/Edit meal forms
book_list = sorted(
    [
        "",
        "Home",
        "Sanjeev Kapoor",
        "Tarla Dalal",
    ]
)

# List of staple categories used to group meals
staples_list = sorted(
    [
        "",
        "Bread",
        "Cereal",   # used mainly for dishes like Poha
        "Rice",
    ]
)

# Fresh vegetables and herbs along with their common measurement units
fresh_ingredients = sorted(
    [
        ["Beans (Green)", "g"],
        ["Carrots", "g"],
        ["Cauliflower", "g"],
        ["Cilantro", "g"],
        ["Curry Leaves", "g"],
        ["Drumstick (Moringa)", "pcs"],
        ["Garlic", "cloves"],
        ["Ginger", "g"],
        ["Green Chilies", "pcs"],
        ["Lemon", "pcs"],
        ["Mint", "g"],
        ["Onions (Red)", "bulbs"],
        ["Onions (White)", "bulbs"],
        ["Peas", "g"],
        ["Peppers (Green)", "g"],
        ["Potatoes (Baking)", "g"],
        ["Potatoes (New)", "g"],
        ["Spinach", "g"],
        ["Tomatoes", "g"],
    ]
)

# Ingredients that usually come packaged or tinned
tinned_ingredients = sorted(
    [
        ["Chickpeas", "tins"],
        ["Coconut Milk", "tins"],
        ["Kidney Beans", "tins"],
        ["Plum Tomatoes", "tins"],
        ["Tamarind Paste", "tbsp"],
        ["Tomato Puree", "tbsp"],
    ]
)

# Dry ingredients such as grains, flours, lentils, and spice mixes
dry_ingredients = sorted(
    [
        ["Basmati Rice", "g"],
        ["Biryani Masala", "tsp"],
        ["Bread Rolls", "pcs"],
        ["Cashew Nuts", "g"],
        ["Chole Masala", "tsp"],
        ["Coriander Powder", "tsp"],
        ["Cumin Seeds", "tsp"],
        ["Flour (Maida)", "g"],
        ["Gram Flour (Besan)", "g"],
        ["Idli Rava", "g"],
        ["Masoor Dal", "g"],
        ["Mustard Seeds", "tsp"],
        ["Peanuts", "g"],
        ["Poha (Flattened Rice)", "g"],
        ["Rajma Masala", "tsp"],
        ["Sambar Powder", "tsp"],
        ["Semolina", "g"],
        ["Toor Dal", "g"],
        ["Turmeric", "tsp"],
        ["Whole Spices (Pulao Mix)", "tsp"],
        ["Whole Wheat Flour", "g"],
    ]
)

# Dairy products and cooking fats
dairy_ingredients = sorted(
    [
        ["Butter", "g"],
        ["Cream", "ml"],
        ["Ghee", "g"],
        ["Paneer", "g"],
        ["Yogurt", "ml"],
    ]
)

# Extra pantry items that are commonly used but not tied to a single meal
extras = sorted(
    [
        "Cooking Oil",
        "Salt",
        "Sugar",
        "Red Chilli Powder",
        "Black Pepper",
        "Cumin Powder",
        "Coriander Powder",
        "Garam Masala",
        "Chaat Masala",
        "Curry Powder",
        "Rice Flour",
        "Corn Flour",
        "Fenugreek Seeds",
        "Fenugreek Leaves (Kasuri Methi)",
        "Cardamom Pods",
        "Cinnamon Sticks",
        "Cloves",
        "Bay Leaves",
        "Jaggery",
        "Tamarind",
        "Pickle",
        "Papad",
        "Tea Leaves",
        "Coffee",
    ]
)

# List of ingredients that are usually measured in grams
# This is used by backend logic when formatting quantities
gram_list = sorted(
    [
        "Beans (Green)",
        "Carrots",
        "Cauliflower",
        "Cilantro",
        "Curry Leaves",
        "Ginger",
        "Mint",
        "Peas",
        "Peppers (Green)",
        "Potatoes (Baking)",
        "Potatoes (New)",
        "Spinach",
        "Tomatoes",
        "Basmati Rice",
        "Cashew Nuts",
        "Flour (Maida)",
        "Gram Flour (Besan)",
        "Masoor Dal",
        "Peanuts",
        "Poha (Flattened Rice)",
        "Semolina",
        "Toor Dal",
        "Whole Wheat Flour",
        "Butter",
        "Ghee",
        "Paneer",
    ]
)

# Tags shown to users in the UI
tag_list = [
    "Spring/Summer",
    "Autumn/Winter",
    "Quick/Easy",
    "Special",
]

# Corresponding database column names for the tags
tag_list_backend = [
    "Spring_Summer",
    "Autumn_Winter",
    "Quick_Easy",
    "Special",
]
