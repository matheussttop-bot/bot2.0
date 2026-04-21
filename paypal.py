import requests

CLIENT_ID = "AVgKcL-ogJwwEfzeCko0IjaZrpbvSXs72gKlHSdI8-JsD30I_WU05ga2Ti2Z_lAkfh9gevq9qPxJTrGY"
SECRET = "EHc2ffBa76xUNLFpyd6LDoxtVOg6EyXJdORKZzNMhY6x6SXivEy95Ul5laGS6Pg9R--3Y2agt8bUrr-J"

def get_token():
    r = requests.post(
        "https://api-m.sandbox.paypal.com/v1/oauth2/token",
        auth=(CLIENT_ID, SECRET),
        data={"grant_type": "client_credentials"}
    )
    return r.json()["access_token"]

def create_payment(user_id, plano, valor):
    token = get_token()

    r = requests.post(
        "https://api-m.sandbox.paypal.com/v2/checkout/orders",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        json={
            "intent": "CAPTURE",
            "purchase_units": [{
                "amount": {
                    "currency_code": "USD",
                    "value": valor
                },
                "custom_id": f"{user_id}|{plano}"
            }],
            "application_context": {
                "return_url": "https://google.com",
                "cancel_url": "https://google.com"
            }
        }
    )

    data = r.json()

    for link in data["links"]:
        if link["rel"] == "approve":
            return link["href"]