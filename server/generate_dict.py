import json

# Top 50 common grocery items
common_items = [
    "milk", "water", "bread", "eggs", "potato", "potatoes", "tomato", "tomatoes", 
    "onion", "onions", "apple", "apples", "banana", "bananas", "rice", "sugar",
    "salt", "pepper", "chicken", "beef", "fish", "cheese", "butter", "oil",
    "coffee", "tea", "juice", "garlic", "ginger", "spinach", "carrot", "carrots",
    "lemon", "lemons", "orange", "oranges", "grape", "grapes", "yogurt", "flour",
    "pasta", "noodle", "noodles", "cereal", "soup", "soap", "shampoo", "toothpaste",
    "toilet paper", "detergent"
]

translations = {
    "fr": {
        "milk": "lait", "water": "eau", "bread": "pain", "eggs": "oeufs", 
        "potato": "pomme de terre", "potatoes": "pommes de terre", "tomato": "tomate", "tomatoes": "tomates",
        "onion": "oignon", "onions": "oignons", "apple": "pomme", "apples": "pommes", 
        "banana": "banane", "bananas": "bananes", "rice": "riz", "sugar": "sucre",
        "salt": "sel", "pepper": "poivre", "chicken": "poulet", "beef": "boeuf", 
        "fish": "poisson", "cheese": "fromage", "butter": "beurre", "oil": "huile",
        "coffee": "café", "tea": "thé", "juice": "jus", "garlic": "ail", 
        "ginger": "gingembre", "spinach": "épinards", "carrot": "carotte", "carrots": "carottes",
        "lemon": "citron", "lemons": "citrons", "orange": "orange", "oranges": "oranges", 
        "grape": "raisin", "grapes": "raisins", "yogurt": "yaourt", "flour": "farine",
        "pasta": "pâtes", "noodle": "nouille", "noodles": "nouilles", "cereal": "céréales", 
        "soup": "soupe", "soap": "savon", "shampoo": "shampooing", "toothpaste": "dentifrice",
        "toilet paper": "papier toilette", "detergent": "détergent"
    },
    "hi": {
        "milk": "दूध", "water": "पानी", "bread": "रोटी", "eggs": "अंडे", 
        "potato": "आलू", "potatoes": "आलू", "tomato": "टमाटर", "tomatoes": "टमाटर",
        "onion": "प्याज", "onions": "प्याज", "apple": "सेब", "apples": "सेब", 
        "banana": "केला", "bananas": "केले", "rice": "चावल", "sugar": "चीनी",
        "salt": "नमक", "pepper": "काली मिर्च", "chicken": "चिकन", "beef": "बीफ", 
        "fish": "मछली", "cheese": "पनीर", "butter": "मक्खन", "oil": "तेल",
        "coffee": "कॉफी", "tea": "चाय", "juice": "रस", "garlic": "लहसुन", 
        "ginger": "अदरक", "spinach": "पालक", "carrot": "गाजर", "carrots": "गाजर",
        "lemon": "नींबू", "lemons": "नींबू", "orange": "संतरा", "oranges": "संतरे", 
        "grape": "अंगूर", "grapes": "अंगूर", "yogurt": "दही", "flour": "आटा",
        "pasta": "पास्ता", "noodle": "नूडल", "noodles": "नूडल्स", "cereal": "अनाज", 
        "soup": "सूप", "soap": "साबुन", "shampoo": "शैम्पू", "toothpaste": "टूथपेस्ट",
        "toilet paper": "टॉयलेट पेपर", "detergent": "डिटर्जेंट"
    },
    "es": {
        "milk": "leche", "water": "agua", "bread": "pan", "eggs": "huevos", 
        "potato": "papa", "potatoes": "papas", "tomato": "tomate", "tomatoes": "tomates",
        "onion": "cebolla", "onions": "cebollas", "apple": "manzana", "apples": "manzanas", 
        "banana": "plátano", "bananas": "plátanos", "rice": "arroz", "sugar": "azúcar",
        "salt": "sal", "pepper": "pimienta", "chicken": "pollo", "beef": "carne", 
        "fish": "pescado", "cheese": "queso", "butter": "mantequilla", "oil": "aceite",
        "coffee": "café", "tea": "té", "juice": "jugo", "garlic": "ajo", 
        "ginger": "jengibre", "spinach": "espinacas", "carrot": "zanahoria", "carrots": "zanahorias",
        "lemon": "limón", "lemons": "limones", "orange": "naranja", "oranges": "naranjas", 
        "grape": "uva", "grapes": "uvas", "yogurt": "yogur", "flour": "harina",
        "pasta": "pasta", "noodle": "fideo", "noodles": "fideos", "cereal": "cereal", 
        "soup": "sopa", "soap": "jabón", "shampoo": "champú", "toothpaste": "pasta dental",
        "toilet paper": "papel higiénico", "detergent": "detergente"
    }
}

verbs = {
    "fr": {"ajouter": "add", "insérer": "add", "supprimer": "remove", "retirer": "remove", "enlever": "remove", "vider": "clear"},
    "hi": {"जोड़ें": "add", "जोड़े": "add", "डालना": "add", "डाल": "add", "हटाना": "remove", "हटाएं": "remove", "निकाल": "remove", "साफ": "clear", "रुकना": "remove"},
    "es": {"añadir": "add", "agregar": "add", "pon": "add", "eliminar": "remove", "quitar": "remove", "borrar": "remove", "vaciar": "clear"}
}

numbers = {
    "fr": {"un": "1", "une": "1", "deux": "2", "trois": "3", "quatre": "4", "cinq": "5", "six": "6", "sept": "7", "huit": "8", "neuf": "9", "dix": "10"},
    "hi": {"एक": "1", "दो": "2", "तीन": "3", "चार": "4", "पांच": "5", "छह": "6", "सात": "7", "आठ": "8", "नौ": "9", "दस": "10"},
    "es": {"uno": "1", "una": "1", "un": "1", "dos": "2", "tres": "3", "cuatro": "4", "cinco": "5", "seis": "6", "siete": "7", "ocho": "8", "nueve": "9", "diez": "10"}
}

units = {
    "fr": {"kilo": "kg", "kilos": "kg", "kilogramme": "kg", "gramme": "g", "grammes": "g", "litre": "l", "litres": "l", "millilitre": "ml", "millilitres": "ml", "bouteille": "bottles", "bouteilles": "bottles", "paquet": "packs", "paquets": "packs", "de": "of"},
    "hi": {"किलो": "kg", "किलोग्राम": "kg", "ग्राम": "g", "लीटर": "l", "मिलीलीटर": "ml", "बोतल": "bottles", "बोतलें": "bottles", "पैकेट": "packs", "का": "of", "की": "of", "के": "of"},
    "es": {"kilo": "kg", "kilos": "kg", "kilogramo": "kg", "gramo": "g", "gramos": "g", "litro": "l", "litros": "l", "mililitro": "ml", "mililitros": "ml", "botella": "bottles", "botellas": "bottles", "paquete": "packs", "paquetes": "packs", "de": "of"}
}

categories = {
    "fr": {"Dairy": "Produits laitiers", "Bakery": "Boulangerie", "Produce": "Fruits et Légumes", "Pantry": "Garde-manger", "Meat & Seafood": "Viande et Fruits de mer", "Beverages": "Boissons", "Personal Care": "Soins personnels", "Household": "Ménage", "Dry Fruits": "Fruits secs", "Other": "Autre"},
    "hi": {"Dairy": "डेयरी", "Bakery": "बेकरी", "Produce": "उत्पादन करना", "Pantry": "पेंट्री", "Meat & Seafood": "मांस और समुद्री भोजन", "Beverages": "पेय", "Personal Care": "व्यक्तिगत देखभाल", "Household": "घर-गृहस्थी", "Dry Fruits": "सूखे मेवे", "Other": "अन्य"},
    "es": {"Dairy": "Lácteos", "Bakery": "Panadería", "Produce": "Frutas y Verduras", "Pantry": "Despensa", "Meat & Seafood": "Carne y Mariscos", "Beverages": "Bebidas", "Personal Care": "Cuidado Personal", "Household": "Hogar", "Dry Fruits": "Frutos Secos", "Other": "Otro"}
}

with open("data/ui_translations.json", "r", encoding="utf-8") as f:
    ui_translations = json.load(f)

local_translations = {}
for lang in ["fr", "hi", "es"]:
    inputs = {}
    inputs.update(verbs[lang])
    inputs.update(numbers[lang])
    inputs.update(units[lang])
    
    # Add reverse translations for items (foreign -> english)
    for en_item, foreign_item in translations[lang].items():
        inputs[foreign_item.lower()] = en_item
        
    outputs = {}
    outputs.update(translations[lang])
    outputs.update(categories[lang])
    
    # Merge UI translations
    if lang in ui_translations:
        outputs.update(ui_translations[lang])
        
    local_translations[lang] = {
        "inputs": inputs,
        "outputs": outputs
    }

with open("data/local_translations.json", "w", encoding="utf-8") as f:
    json.dump(local_translations, f, ensure_ascii=False, indent=2)

print("Generated data/local_translations.json")
