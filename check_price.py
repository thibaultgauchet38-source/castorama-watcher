import os
import json
import re
import requests
from bs4 import BeautifulSoup
from twilio.rest import Client

# ============================================================
#  CONFIGURATION — à remplir avec tes valeurs
# ============================================================
PRODUCT_URL = os.environ.get("PRODUCT_URL", "https://www.castorama.fr/TON-ARTICLE")
PRICE_FILE  = "last_price.json"

TWILIO_SID   = os.environ["TWILIO_ACCOUNT_SID"]
TWILIO_TOKEN = os.environ["TWILIO_AUTH_TOKEN"]
FROM_WHATSAPP = "whatsapp:+14155238886"          # numéro sandbox Twilio (fixe)
TO_WHATSAPP   = os.environ["TO_WHATSAPP_NUMBER"] # ex: whatsapp:+33612345678
# ============================================================


def get_price(url: str) -> float | None:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )
    }
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"❌ Erreur HTTP : {e}")
        return None

    soup = BeautifulSoup(resp.text, "html.parser")

    # Sélecteurs Castorama (testés — peuvent évoluer)
    candidates = [
        soup.select_one('[data-testid="product-price"] .price__amount'),
        soup.select_one('.price__amount'),
        soup.select_one('[class*="ProductPrice"] [class*="amount"]'),
        soup.select_one('meta[property="product:price:amount"]'),
    ]

    for tag in candidates:
        if tag is None:
            continue
        raw = tag.get("content") or tag.get_text()
        raw = raw.replace("\xa0", "").replace(" ", "").replace(",", ".").strip()
        match = re.search(r"[\d]+\.?\d*", raw)
        if match:
            return float(match.group())

    print("⚠️  Prix introuvable — le sélecteur a peut-être changé.")
    return None


def load_last_price() -> float | None:
    if os.path.exists(PRICE_FILE):
        with open(PRICE_FILE) as f:
            data = json.load(f)
            return data.get("price")
    return None


def save_price(price: float) -> None:
    with open(PRICE_FILE, "w") as f:
        json.dump({"price": price}, f)


def send_whatsapp(message: str) -> None:
    client = Client(TWILIO_SID, TWILIO_TOKEN)
    msg = client.messages.create(
        body=message,
        from_=FROM_WHATSAPP,
        to=TO_WHATSAPP,
    )
    print(f"✅ Notification envoyée (SID: {msg.sid})")


def main() -> None:
    print(f"🔍 Vérification du prix : {PRODUCT_URL}")
    current_price = get_price(PRODUCT_URL)

    if current_price is None:
        print("Impossible de récupérer le prix, on arrête.")
        return

    print(f"💶 Prix actuel : {current_price} €")
    last_price = load_last_price()

    if last_price is None:
        print(f"Premier relevé enregistré : {current_price} €")
        save_price(current_price)
        return

    print(f"📋 Dernier prix connu : {last_price} €")

    if current_price < last_price:
        diff = last_price - current_price
        message = (
            f"🎉 Baisse de prix sur Castorama !\n"
            f"Ancien prix : {last_price} €\n"
            f"Nouveau prix : {current_price} €\n"
            f"Économie : {diff:.2f} €\n"
            f"🔗 {PRODUCT_URL}"
        )
        print(message)
        send_whatsapp(message)
        save_price(current_price)
    elif current_price > last_price:
        print(f"📈 Prix en hausse ({last_price} € → {current_price} €), pas de notification.")
        save_price(current_price)
    else:
        print("Prix inchangé, rien à faire.")


if __name__ == "__main__":
    main()
