"""
generate_data.py — builds train/data.csv: labeled example sentences for the
4 intents (ADD, REMOVE, SEARCH_ITEM, SEARCH_FILTER) with phrasing variety in
English, Spanish, and Hindi (romanized + Devanagari mix, matching what the
Web Speech API returns for hi-IN).

Dev-only. Run once to (re)generate train/data.csv, then run train.py.
"""
import csv
import itertools
import random

random.seed(7)

ITEMS_EN = ["milk", "bread", "eggs", "bananas", "apples", "rice", "chicken",
            "coffee", "sugar", "butter", "cheese", "yogurt", "onions",
            "tomatoes", "pasta", "toothpaste", "shampoo", "detergent",
            "orange juice", "water", "cereal", "olive oil", "spinach",
            "potatoes", "flour"]
ITEMS_ES = ["leche", "pan", "huevos", "platanos", "manzanas", "arroz",
            "pollo", "cafe", "azucar", "mantequilla", "queso", "yogur",
            "cebollas", "tomates", "pasta", "pasta de dientes", "champu",
            "detergente", "jugo de naranja", "agua", "cereal",
            "aceite de oliva", "espinacas", "papas", "harina"]
ITEMS_HI = ["doodh", "roti", "ande", "kele", "seb", "chawal", "chicken",
            "coffee", "cheeni", "makhan", "paneer", "dahi", "pyaz",
            "tamatar", "pasta", "toothpaste", "shampoo", "detergent",
            "santre ka juice", "pani", "cereal", "olive oil", "palak",
            "aloo", "atta"]

BRANDS = ["organic", "great value", "trader joe's", "kirkland", "365"]
SIZES = ["small", "large", "family size", "1 liter", "500g", "12 pack"]

ADD_TEMPLATES_EN = [
    "add {item} to my list",
    "add {item}",
    "i need {item}",
    "i need to buy {item}",
    "i want to buy {item}",
    "put {item} on the list",
    "can you add {item}",
    "we're out of {item}, add it",
    "add {qty} {item}",
    "get {qty} {item}",
    "buy {qty} {item}",
    "i want {qty} {item}",
    "add some {item}",
    "throw {item} on the list",
    "don't forget {item}",
    "remember to get {item}",
    "{qty} {item}",
    "{item}",
]
REMOVE_TEMPLATES_EN = [
    "remove {item} from my list",
    "remove {item}",
    "delete {item}",
    "take {item} off the list",
    "i don't need {item} anymore",
    "cancel {item}",
    "get rid of {item}",
    "scratch {item} off the list",
    "we already have {item}, remove it",
]
SEARCH_ITEM_TEMPLATES_EN = [
    "find {item}",
    "find me {item}",
    "search for {item}",
    "look up {item}",
    "show me {item}",
    "find {brand} {item}",
    "search for {brand} {item}",
    "find {item} in {size}",
    "look for {brand} {item} in {size}",
    "where can i find {item}",
]
SEARCH_FILTER_TEMPLATES_EN = [
    "find {item} under ${price}",
    "{item} under ${price}",
    "search {item} between ${price} and ${price2}",
    "show me {item} under ${price}",
    "find cheap {item} under ${price}",
    "{item} for less than ${price}",
    "find {brand} {item} under ${price}",
    "show {item} priced under ${price}",
    "find {item} between ${price} and ${price2}",
]

ADD_TEMPLATES_ES = [
    "agrega {item} a mi lista",
    "agregar {item}",
    "necesito {item}",
    "necesito comprar {item}",
    "quiero comprar {item}",
    "pon {item} en la lista",
    "puedes agregar {item}",
    "se nos acabo el {item}, agregalo",
    "agrega {qty} {item}",
    "compra {qty} {item}",
    "quiero {qty} {item}",
    "no olvides el {item}",
    "{qty} {item}",
    "{item}",
]
REMOVE_TEMPLATES_ES = [
    "quita {item} de mi lista",
    "elimina {item}",
    "borra {item}",
    "saca {item} de la lista",
    "ya no necesito {item}",
    "cancela {item}",
    "ya tenemos {item}, quitalo",
]
SEARCH_ITEM_TEMPLATES_ES = [
    "busca {item}",
    "buscame {item}",
    "encuentra {item}",
    "muestrame {item}",
    "busca {brand} {item}",
    "encuentra {item} en {size}",
    "donde puedo encontrar {item}",
]
SEARCH_FILTER_TEMPLATES_ES = [
    "busca {item} por menos de ${price}",
    "{item} por menos de ${price}",
    "busca {item} entre ${price} y ${price2}",
    "muestrame {item} por menos de ${price}",
    "encuentra {brand} {item} por menos de ${price}",
]

ADD_TEMPLATES_HI = [
    "{item} list mein add karo",
    "{item} add karo",
    "mujhe {item} chahiye",
    "{item} khareedna hai",
    "list mein {item} daalo",
    "{item} le aana",
    "{qty} {item} add karo",
    "{qty} {item} chahiye",
    "{item} mat bhoolna",
    "{qty} {item}",
    "{item}",
]
REMOVE_TEMPLATES_HI = [
    "{item} list se hatao",
    "{item} hatao",
    "{item} delete karo",
    "mujhe ab {item} nahi chahiye",
    "{item} cancel karo",
]
SEARCH_ITEM_TEMPLATES_HI = [
    "{item} dhundo",
    "{item} search karo",
    "mujhe {item} dikhao",
    "{brand} {item} dhundo",
    "{item} {size} mein dhundo",
]
SEARCH_FILTER_TEMPLATES_HI = [
    "{item} ${price} se kam mein dhundo",
    "{item} ${price} ke andar",
    "{item} ${price} aur ${price2} ke beech dhundo",
    "sasta {item} ${price} se kam mein",
]

QTYS = ["2", "3", "5", "a dozen", "2 bottles of", "5", "a bag of", "3 cans of"]


def fill(template, items):
    item = random.choice(items)
    qty = random.choice(QTYS)
    brand = random.choice(BRANDS)
    size = random.choice(SIZES)
    price = random.choice([2, 3, 4, 5, 8, 10, 15])
    price2 = price + random.choice([3, 5, 8])
    return template.format(item=item, qty=qty, brand=brand, size=size,
                            price=price, price2=price2)


def build_rows(templates, items, intent, lang, n):
    rows = []
    combos = list(itertools.product(templates, items))
    random.shuffle(combos)
    for template, _ in combos[:n]:
        text = fill(template, items)
        rows.append((text, intent, lang))
    return rows


def main():
    rows = []
    rows += build_rows(ADD_TEMPLATES_EN, ITEMS_EN, "ADD", "en", 45)
    rows += build_rows(ADD_TEMPLATES_ES, ITEMS_ES, "ADD", "es", 30)
    rows += build_rows(ADD_TEMPLATES_HI, ITEMS_HI, "ADD", "hi", 25)

    rows += build_rows(REMOVE_TEMPLATES_EN, ITEMS_EN, "REMOVE", "en", 45)
    rows += build_rows(REMOVE_TEMPLATES_ES, ITEMS_ES, "REMOVE", "es", 30)
    rows += build_rows(REMOVE_TEMPLATES_HI, ITEMS_HI, "REMOVE", "hi", 25)

    rows += build_rows(SEARCH_ITEM_TEMPLATES_EN, ITEMS_EN, "SEARCH_ITEM", "en", 45)
    rows += build_rows(SEARCH_ITEM_TEMPLATES_ES, ITEMS_ES, "SEARCH_ITEM", "es", 30)
    rows += build_rows(SEARCH_ITEM_TEMPLATES_HI, ITEMS_HI, "SEARCH_ITEM", "hi", 25)

    rows += build_rows(SEARCH_FILTER_TEMPLATES_EN, ITEMS_EN, "SEARCH_FILTER", "en", 45)
    rows += build_rows(SEARCH_FILTER_TEMPLATES_ES, ITEMS_ES, "SEARCH_FILTER", "es", 30)
    rows += build_rows(SEARCH_FILTER_TEMPLATES_HI, ITEMS_HI, "SEARCH_FILTER", "hi", 25)

    random.shuffle(rows)
    with open("train/data.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["text", "intent", "lang"])
        writer.writerows(rows)
    print(f"wrote {len(rows)} rows to train/data.csv")


if __name__ == "__main__":
    main()
