import json
import os

categories_map = {
    "Dairy": ["milk", "cheese", "yogurt", "butter", "paneer", "dahi", "ghee", "lassi", "chaas", "shrikhand", "khoya", "mawa", "malai", "eggs", "cream", "sour cream", "cream cheese", "condensed milk", "evaporated milk", "ice cream", "whipped cream", "buttermilk", "kefir", "cottage cheese", "mozzarella", "cheddar", "parmesan", "feta", "brie", "camembert", "gouda", "swiss cheese", "provolone", "ricotta", "blue cheese", "margarine", "almond milk", "soy milk", "oat milk", "coconut milk"],
    "Bakery": ["bread", "roti", "flour", "atta", "bagels", "croissant", "muffins", "buns", "pita", "tortillas", "naan", "paratha", "pav", "baguette", "sourdough", "ciabatta", "focaccia", "rye bread", "whole wheat bread", "white bread", "multigrain bread", "pumpernickel", "brioche", "english muffins", "biscuits", "cookies", "cake", "pastry", "pie", "tart", "brownies", "donuts", "cupcakes", "waffles", "pancakes"],
    "Produce": ["bananas", "apples", "onions", "tomatoes", "spinach", "potatoes", "carrots", "cabbage", "cauliflower", "broccoli", "garlic", "ginger", "peas", "cucumber", "capsicum", "bell pepper", "lemons", "oranges", "grapes", "mangoes", "melon", "watermelon", "zucchini", "asparagus", "strawberries", "corn", "pumpkin", "cranberries", "sweet potatoes", "lettuce", "kale", "celery", "eggplant", "mushrooms", "radish", "turnip", "beetroot", "okra", "green beans", "avocado", "pineapple", "papaya", "kiwi", "peaches", "plums", "cherries", "blueberries", "raspberries", "blackberries", "pomegranate"],
    "Pantry": ["rice", "pasta", "noodles", "cereal", "olive oil", "sugar", "salt", "pepper", "lentils", "chickpeas", "quinoa", "honey", "stevia", "agave syrup", "soy sauce", "vinegar", "ketchup", "mayonnaise", "mustard", "cumin", "turmeric", "coriander", "chili powder", "garam masala", "baking powder", "baking soda", "vanilla extract", "yeast", "cornstarch", "cocoa powder", "chocolate chips", "peanut butter", "jam", "jelly", "marmalade", "syrup", "beans", "canned tomatoes", "tuna", "soup", "broth", "stock", "macaroni"],
    "Meat & Seafood": ["chicken", "pork", "beef", "fish", "shrimp", "prawns", "lamb", "mutton", "turkey", "duck", "bacon", "sausage", "ham", "salami", "pepperoni", "prosciutto", "hot dogs", "crab", "lobster", "scallops", "mussels", "clams", "oysters", "squid", "octopus", "salmon", "cod", "haddock", "trout", "halibut", "tilapia", "sardines", "anchovies", "mackerel"],
    "Beverages": ["coffee", "tea", "orange juice", "water", "pepsi", "coca-cola", "sprite", "fanta", "soda", "apple juice", "grape juice", "cranberry juice", "tomato juice", "lemonade", "iced tea", "green tea", "black tea", "herbal tea", "chamomile tea", "peppermint tea", "hot chocolate", "energy drink", "sports drink", "beer", "wine", "vodka", "whiskey", "rum", "gin", "tequila", "cider", "champagne", "kombucha", "smoothie", "milkshake"],
    "Personal Care": ["toothpaste", "shampoo", "soap", "conditioner", "body wash", "toothbrush", "deodorant", "lotion", "moisturizer", "sunscreen", "shaving cream", "razors", "mouthwash", "floss", "cotton swabs", "cotton balls", "makeup remover", "face wash", "cleanser", "toner", "serum", "acne cream", "lip balm", "perfume", "cologne", "hair spray", "hair gel", "hair mousse", "nail polish", "nail polish remover", "tampons", "pads", "panty liners", "diapers", "baby wipes"],
    "Household": ["detergent", "toilet paper", "tissue", "trash bags", "paper towels", "napkins", "dish soap", "sponge", "bleach", "fabric softener", "glass cleaner", "all-purpose cleaner", "floor cleaner", "toilet bowl cleaner", "air freshener", "laundry pods", "stain remover", "mop", "broom", "dustpan", "bucket", "vacuum bags", "batteries", "light bulbs", "matches", "lighters", "aluminum foil", "plastic wrap", "parchment paper", "ziploc bags", "tupperware", "sponges", "scouring pads", "gloves"],
    "Dry Fruits": ["almonds", "cashews", "walnuts", "pistachios", "raisins", "dates", "figs", "apricots", "prunes", "pecans", "macadamia nuts", "brazil nuts", "pine nuts", "hazelnuts", "chestnuts", "peanuts", "sunflower seeds", "pumpkin seeds", "chia seeds", "flax seeds", "hemp seeds", "sesame seeds", "poppy seeds", "dried cranberries", "dried cherries", "dried blueberries", "dried mango", "dried pineapple", "dried papaya", "dried coconut", "coconut flakes"],
    "Other": ["dog food", "cat food", "bird seed", "fish food", "pet toys", "cat litter", "dog treats", "cat treats", "maggi", "chips", "chocolate", "candy", "gum", "mints", "popcorn", "pretzels", "crackers", "rice cakes", "trail mix", "granola bars", "protein bars", "energy bars", "fruit snacks", "gummy bears", "marshmallows", "jelly beans", "licorice", "lollipops", "hard candy", "chewing gum", "breath mints", "ice", "charcoal", "firewood", "greeting cards", "wrapping paper", "tape", "scissors", "pens", "pencils", "notebooks", "envelopes", "stamps", "magazines", "newspapers", "books", "dvds", "cds", "video games"]
}

synonyms = {
    "coke": "coca-cola",
    "ande": "eggs",
    "kele": "bananas",
    "seb": "apples",
    "pyaz": "onions",
    "tamatar": "tomatoes",
    "palak": "spinach",
    "aloo": "potatoes",
    "chawal": "rice",
    "cheeni": "sugar",
    "santre ka juice": "orange juice",
    "pani": "water",
    "lemon": "lemons",
    "carrot": "carrots",
    "apple": "apples",
    "orange": "oranges",
    "mango": "mangoes",
    "potato": "potatoes",
    "tomato": "tomatoes",
    "onion": "onions",
    "banana": "bananas",
    "egg": "eggs",
    "grape": "grapes",
    "pea": "peas",
    "biscuit": "biscuits",
    "chip": "chips",
    "lentil": "lentils",
    "noodle": "noodles",
    "green chilli": "chili powder",
    "chilli": "chili powder",
    "chili": "chili powder",
    "sweet potato": "sweet potatoes",
    "strawberry": "strawberries",
    "dog food": "dog food",
    "toilet papers": "toilet paper"
}

items_json = {}
categories_json = {}

for cat, items_list in categories_map.items():
    for item in items_list:
        items_json[item] = item
        categories_json[item] = cat

for syn, canonical in synonyms.items():
    if canonical in items_json:
        items_json[syn] = canonical
        categories_json[syn] = categories_json[canonical]

os.makedirs("data", exist_ok=True)
with open("data/items.json", "w") as f:
    json.dump(items_json, f, indent=2)

with open("data/categories.json", "w") as f:
    json.dump(categories_json, f, indent=2)

print(f"Added {len(items_json)} items and {len(categories_json)} category mappings.")
