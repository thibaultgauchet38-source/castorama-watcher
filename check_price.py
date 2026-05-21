import os
import json
import re
from playwright.sync_api import sync_playwright
from twilio.rest import Client

# ============================================================
#  CONFIGURATION — à remplir avec tes valeurs
# ============================================================
PRODUCT_URL = os.environ.get("PRODUCT_URL", "https://www.castorama.fr/TON-ARTICLE")
PRICE_FILE  = "last_price.json"

TWILIO_SID    = os.environ["TWILIO_ACCOUNT_SID"]
TWILIO_TOKEN  = os.environ["TWILIO_AUTH_TOKEN"]
FROM_WHATSAPP = "whatsapp:+14155238886"          # numéro sandbox Twilio (fixe)
TO_WHATSAPP   = os.environ["TO_WHATSAPP_NUMBER"] # ex: whatsapp:+33612345678
# ============================================================


def get_price(url: str) -> float | None:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            locale="fr-FR",
        )
        page = context.new_page()

        try:
            page.goto(url, wait_until="networkidle", timeout=30_000)
        except Exception as e:
            print(f"❌ Erreur chargement page : {e}")
            browser.close()
            return None

        # Attendre que le composant prix soit rendu
        try:
            page.wait_for_selector(
                '[data-testid="product-price"], '
                '[class*="ProductPrice"], '
                '[class*="product-price"], '
                '[class*="priceWithTax"]',
                timeout=10_000,
            )
        except Exception:
            print("⚠️  Sélecteur prix non trouvé dans les 10 s — on tente quand même.")

        # Stratégie 1 : JSON-LD (le plus fiable, indépendant du CSS)
        ld_json = page.evaluate("""() => {
            const scripts = document.querySelectorAll('script[type="application/ld+json"]');
            for (const s of scripts) {
                try {
                    const data = JSON.parse(s.textContent);
                    const objs = Array.isArray(data) ? data : [data];
                    for (const obj of objs) {
                        if (obj.offers) {
                            const offer = Array.isArray(obj.offers) ? obj.offers[0] : obj.offers;
                            if (offer.price) return String(offer.price);
                        }
                        if (obj['@type'] === 'Offer' && obj.price) return String(obj.price);
                    }
                } catch {}
            }
            return null;
        }""")
        if ld_json:
            raw = ld_json.replace(",", ".").strip()
            m = re.search(r"[\d]+\.?\d*", raw)
            if m:
                browser.close()
                return float(m.group())

        # Stratégie 2 : balise meta og:price:amount
        meta_price = page.get_attribute('meta[property="product:price:amount"]', "content")
        if not meta_price:
            meta_price = page.get_attribute('meta[property="og:price:amount"]', "content")
        if meta_price:
            raw = meta_price.replace(",", ".").strip()
            m = re.search(r"[\d]+\.?\d*", raw)
            if m:
                browser.close()
                return float(m.group())

        # Stratégie 3 : sélecteurs CSS (fallback, peut évoluer)
        selectors = [
            '[data-testid="product-price"] [class*="amount"]',
            '[data-testid="product-price"] [class*="price"]',
            '[class*="ProductPrice"] [class*="amount"]',
            '[class*="ProductPrice"] [class*="price"]',
            '[class*="priceWithTax"]',
            '[class*="product-price"] [class*="amount"]',
            '[class*="price__amount"]',
            '[itemprop="price"]',
        ]
        for sel in selectors:
            try:
                el = page.query_selector(sel)
                if el:
                    raw = (
                        el.get_attribute("content")
                        or el.inner_text()
                    )
                    raw = raw.replace("\xa0", "").replace(" ", "").replace(",", ".").strip()
                    m = re.search(r"[\d]+\.?\d*", raw)
                    if m:
                        browser.close()
                        return float(m.group())
            except Exception:
                continue

        browser.close()

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
