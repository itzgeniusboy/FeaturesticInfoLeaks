import telebot
from telebot import types
import json, os, time, requests
from flask import Flask
from threading import Thread
from datetime import datetime
import pytz
from num import get_number_details

# Configuration
BOT_TOKEN = "8741964335:AAFS0auD1MjbLynmtjGDKA3fXIwHpghxTnY"
ADMIN_ID = 1969067694
CHANNEL_1_LINK = "https://t.me/FeaturesticLeaks"
CHANNEL_2_LINK = "https://t.me/OneCoreEngine"
CHANNEL_1_ID = "-1002278499725"
CHANNEL_2_ID = "-1002265779523"

# API 2 config
API2_URL = "http://api.subhxcosmo.in/api"
API2_KEY = "ITACHI"

# Initialize bot
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

DB_FILE = "database.json"
IST = pytz.timezone('Asia/Kolkata')

# ===== DATA MANAGEMENT =====

def load_data():
    if not os.path.exists(DB_FILE):
        return {"users": {}, "stats": {"total_searches": 0, "total_users": 0}}
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=2)

# ===== UTILITIES =====

def is_subscribed(user_id):
    if user_id == ADMIN_ID:
        return True
    try:
        status1 = bot.get_chat_member(CHANNEL_1_ID, user_id).status
        status2 = bot.get_chat_member(CHANNEL_2_ID, user_id).status
        return status1 in ['member', 'administrator', 'creator'] and status2 in ['member', 'administrator', 'creator']
    except Exception:
        return False

def main_menu():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(
        types.KeyboardButton("🔍 Search"), types.KeyboardButton("👤 Profile"),
        types.KeyboardButton("💰 Points"), types.KeyboardButton("🎁 Referral"),
        types.KeyboardButton("🛒 Buy"), types.KeyboardButton("📜 History"),
        types.KeyboardButton("📞 Support"), types.KeyboardButton("❓ Help"),
        types.KeyboardButton("⚙️ Settings"), types.KeyboardButton("📋 Menu")
    )
    return markup

def detect_input_type(user_input):
    user_input = user_input.strip()
    if user_input.startswith('@'):
        return "username"
    if user_input.isdigit():
        if len(user_input) > 9: # Likely phone number or long ID
            return "phone_or_id"
        return "id"
    return "unknown"

def call_api2(term):
    try:
        params = {"key": API2_KEY, "type": "tg", "term": term}
        response = requests.get(API2_URL, params=params, timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return None

def merge_data(api1_res, api2_res):
    # Logic to combine results
    merged = {
        "phone": "N/A",
        "tg_id": "N/A",
        "name": "N/A",
        "username": "N/A",
        "country": "N/A",
        "country_code": "N/A",
        "bio": "N/A",
        "photo": "No",
        "last_seen": "N/A"
    }
    
    if api1_res and api1_res.get("status") == "success":
        data1 = api1_res.get("data", {})
        merged["phone"] = data1.get("phone", "N/A")
        merged["country"] = data1.get("country", "N/A")
        merged["country_code"] = data1.get("country_code", "N/A")

    if api2_res:
        # Assuming API 2 returns a list or dict with these fields
        # This structure depends on the actual API 2 response
        merged["phone"] = api2_res.get("phone", merged["phone"])
        merged["tg_id"] = api2_res.get("id", merged["tg_id"])
        merged["name"] = api2_res.get("name", "N/A")
        merged["username"] = api2_res.get("username", "N/A")
        merged["country"] = api2_res.get("country", merged["country"])
        merged["bio"] = api2_res.get("bio", "N/A")
        merged["photo"] = "Yes" if api2_res.get("has_photo") else "No"
        merged["last_seen"] = api2_res.get("last_seen", "recently")

    return merged

# ===== BOT HANDLERS =====

@bot.message_handler(commands=['start'])
def start(message):
    user_id = str(message.from_user.id)
    data = load_data()
    
    # Handle Referral
    args = message.text.split()
    referrer_id = args[1] if len(args) > 1 else None
    
    if user_id not in data["users"]:
        data["users"][user_id] = {
            "credits": 5,
            "referrals": 0,
            "referred_by": referrer_id,
            "search_history": [],
            "join_date": datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S")
        }
        data["stats"]["total_users"] += 1
        
        if referrer_id and referrer_id in data["users"] and referrer_id != user_id:
            data["users"][referrer_id]["credits"] += 5
            data["users"][referrer_id]["referrals"] += 1
            try:
                bot.send_message(referrer_id, f"🎁 Referral Successful! You got 5 credits for inviting {message.from_user.first_name}.")
            except: pass
            
        save_data(data)

    if not is_subscribed(message.from_user.id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Channel 1", url=CHANNEL_1_LINK))
        markup.add(types.InlineKeyboardButton("Channel 2", url=CHANNEL_2_LINK))
        markup.add(types.InlineKeyboardButton("✅ Joined", callback_data="check_join"))
        bot.send_message(message.chat.id, "❌ Aapne dono channels join nahi kiye hain!\n\nPlease join both channels to use the bot.", reply_markup=markup)
        return

    bot.send_message(message.chat.id, f"Welcome {message.from_user.first_name}! Use the menu below to navigate.", reply_markup=main_menu())

@bot.callback_query_handler(func=lambda call: call.data == "check_join")
def check_join(call):
    if is_subscribed(call.from_user.id):
        bot.answer_callback_query(call.id, "✅ Success! You can now use the bot.")
        bot.edit_message_text("Aapne channels join kar liye hain! Ab aap bot use kar sakte hain.", call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, "Main Menu:", reply_markup=main_menu())
    else:
        bot.answer_callback_query(call.id, "❌ Abhi bhi join nahi kiya!", show_alert=True)

@bot.message_handler(commands=['add'])
def add_credits(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        args = message.text.split()
        target_id = args[1]
        amount = int(args[2])
        data = load_data()
        if target_id in data["users"]:
            data["users"][target_id]["credits"] += amount
            save_data(data)
            bot.send_message(message.chat.id, f"✅ Added {amount} credits to {target_id}")
        else:
            bot.send_message(message.chat.id, "❌ User not found in database.")
    except:
        bot.send_message(message.chat.id, "Usage: /add <user_id> <amount>")

@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    if message.from_user.id != ADMIN_ID: return
    msg_text = message.text.replace('/broadcast', '').strip()
    if not msg_text: return
    data = load_data()
    count = 0
    for uid in data["users"]:
        try:
            bot.send_message(uid, msg_text)
            count += 1
            time.sleep(0.05)
        except: pass
    bot.send_message(message.chat.id, f"✅ Broadcast sent to {count} users.")

@bot.message_handler(commands=['stats'])
def stats(message):
    if message.from_user.id != ADMIN_ID: return
    data = load_data()
    text = f"📊 Bot Statistics:\n\nTotal Users: {data['stats']['total_users']}\nTotal Searches: {data['stats']['total_searches']}"
    bot.send_message(message.chat.id, text)

@bot.message_handler(func=lambda m: True)
def handle_all(message):
    user_id = str(message.from_user.id)
    if not is_subscribed(message.from_user.id):
        start(message)
        return

    text = message.text
    data = load_data()
    
    if text == "🔍 Search":
        bot.send_message(message.chat.id, "🔍 Enter Phone Number, Telegram ID, or Username to search:")
        bot.register_next_step_handler(message, process_search)
    
    elif text == "👤 Profile":
        user = data["users"].get(user_id, {})
        profile_text = (
            f"👤 User Profile\n\n"
            f"🆔 User ID: {user_id}\n"
            f"💎 Credits: {user.get('credits', 0)}\n"
            f"🤝 Referrals: {user.get('referrals', 0)}\n"
            f"📅 Joined: {user.get('join_date', 'N/A')}"
        )
        bot.send_message(message.chat.id, profile_text)

    elif text == "💰 Points":
        credits = data["users"].get(user_id, {}).get("credits", 0)
        bot.send_message(message.chat.id, f"💰 Current Balance: {credits} Credits")

    elif text == "🎁 Referral":
        ref_link = f"https://t.me/{(bot.get_me().username)}?start={user_id}"
        ref_text = (
            f"🎁 Referral System\n\n"
            f"Invite your friends and earn 5 credits per referral!\n\n"
            f"Your Link: `{ref_link}`"
        )
        bot.send_message(message.chat.id, ref_text, parse_mode="Markdown")

    elif text == "📜 History":
        history = data["users"].get(user_id, {}).get("search_history", [])[-10:]
        if not history:
            bot.send_message(message.chat.id, "📜 No search history found.")
        else:
            h_text = "📜 Last 10 Searches:\n\n" + "\n".join([f"• {h}" for h in history])
            bot.send_message(message.chat.id, h_text)

    elif text == "📞 Support":
        bot.send_message(message.chat.id, "📞 Support: @FeaturesticLeaks")

    elif text == "❓ Help":
        bot.send_message(message.chat.id, "❓ Help Section:\n\n1. Use Search to find details.\n2. Each search costs 1 credit.\n3. Refer friends to earn more credits.")

    elif text == "⚙️ Settings":
        bot.send_message(message.chat.id, "⚙️ Settings are coming soon!")

    elif text == "📋 Menu":
        bot.send_message(message.chat.id, "Main Menu:", reply_markup=main_menu())

def process_search(message):
    user_id = str(message.from_user.id)
    user_input = message.text
    data = load_data()
    
    if data["users"][user_id]["credits"] < 1:
        bot.send_message(message.chat.id, "❌ Aapke paas credits nahi hain! Please refer friends or buy credits.")
        return

    wait_msg = bot.send_message(message.chat.id, "⏳ Searching... Please wait.")
    
    # Deduct credit
    data["users"][user_id]["credits"] -= 1
    data["stats"]["total_searches"] += 1
    data["users"][user_id]["search_history"].append(user_input)
    save_data(data)

    try:
        # Dual API Call
        api1_res = get_number_details(user_input)
        api2_res = call_api2(user_input)
        
        if not api1_res and not api2_res:
            # Refund if both fail
            data = load_data()
            data["users"][user_id]["credits"] += 1
            save_data(data)
            bot.edit_message_text("❌ Search failed! Credits have been refunded.", message.chat.id, wait_msg.message_id)
            return

        merged = merge_data(api1_res, api2_res)
        
        output = (
            "✅ Success!\n\n"
            f"📱 Phone Number: {merged['phone']}\n"
            f"🆔 Telegram ID: {merged['tg_id']}\n"
            f"👤 Name: {merged['name']}\n"
            f"🗣️ Username: {merged['username']}\n"
            f"🌍 Country: {merged['country']}\n"
            f"📞 Country Code: {merged['country_code']}\n"
            f"📧 Bio: {merged['bio']}\n"
            f"🖼️ Profile Photo: {merged['photo']}\n"
            f"📅 Last Seen: {merged['last_seen']}\n\n"
            f"💎 Remaining Points: {data['users'][user_id]['credits']}\n"
            f"🕐 Time: {datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            "Developed By @FeaturesticLeaks"
        )
        
        bot.edit_message_text(output, message.chat.id, wait_msg.message_id)
        
    except Exception as e:
        # Refund on error
        data = load_data()
        data["users"][user_id]["credits"] += 1
        save_data(data)
        bot.edit_message_text(f"❌ An error occurred: {str(e)}. Credits refunded.", message.chat.id, wait_msg.message_id)

# ===== FLASK WEB SERVER =====

@app.route('/')
def home():
    return "Bot is Running!"

def run_flask():
    port = int(os.environ.get("PORT", 3000))
    app.run(host='0.0.0.0', port=port)

# ===== MAIN =====

if __name__ == "__main__":
    Thread(target=run_flask).start()
    print("Bot started...")
    bot.infinity_polling()
