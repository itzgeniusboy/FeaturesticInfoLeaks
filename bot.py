import telebot
from telebot import types
import json, os, time, requests
from flask import Flask
from threading import Thread
from datetime import datetime
import pytz
from num import get_number_details

# Configuration
BOT_TOKEN = "8741964335:AAF7wdSGmcVdEadFw3RlryIA9yeBUuUsA6w"
ADMIN_ID = 1969067694
CHANNEL_1_LINK = "https://t.me/FeaturesticLeaks"
CHANNEL_2_LINK = "https://t.me/OneCoreEngine"
CHANNEL_1_ID = "-1002278499725"
CHANNEL_2_ID = "-1002265779523"
CREDIT_LINE = "Developed By @FeaturesticLeaks"

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
        try:
            return json.load(f)
        except:
            return {"users": {}, "stats": {"total_searches": 0, "total_users": 0}}

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
        types.KeyboardButton("📞 Support"), types.KeyboardButton("❓ Help")
    )
    return markup

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
            "unlimited": True if int(user_id) == ADMIN_ID else False,
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
        markup.add(types.InlineKeyboardButton("✅ Check Join", callback_data="check_join"))
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

@bot.message_handler(commands=['unlimited'])
def set_unlimited(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        args = message.text.split()
        target_id = args[1]
        data = load_data()
        if target_id in data["users"]:
            data["users"][target_id]["unlimited"] = True
            save_data(data)
            bot.send_message(message.chat.id, f"✅ User {target_id} is now UNLIMITED.")
        else:
            bot.send_message(message.chat.id, "❌ User not found.")
    except:
        bot.send_message(message.chat.id, "Usage: /unlimited <user_id>")

@bot.message_handler(commands=['remove_unlimited'])
def remove_unlimited(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        args = message.text.split()
        target_id = args[1]
        data = load_data()
        if target_id in data["users"]:
            data["users"][target_id]["unlimited"] = False
            save_data(data)
            bot.send_message(message.chat.id, f"✅ Unlimited status removed for {target_id}.")
        else:
            bot.send_message(message.chat.id, "❌ User not found.")
    except:
        bot.send_message(message.chat.id, "Usage: /remove_unlimited <user_id>")

@bot.message_handler(func=lambda m: True)
def handle_all(message):
    user_id = str(message.from_user.id)
    if not is_subscribed(message.from_user.id):
        start(message)
        return

    text = message.text
    data = load_data()
    
    if text == "🔍 Search":
        bot.send_message(message.chat.id, "📱 Send phone number to search\nExample: 9852108915")
        bot.register_next_step_handler(message, process_search)
    
    elif text == "👤 Profile":
        user = data["users"].get(user_id, {})
        status = "Unlimited" if user.get("unlimited") else "Normal"
        profile_text = (
            f"👤 User Profile\n\n"
            f"🆔 User ID: {user_id}\n"
            f"💎 Credits: {user.get('credits', 0)}\n"
            f"⚡ Status: {status}\n"
            f"🤝 Referrals: {user.get('referrals', 0)}\n"
            f"📅 Joined: {user.get('join_date', 'N/A')}"
        )
        bot.send_message(message.chat.id, profile_text)

    elif text == "💰 Points":
        user = data["users"].get(user_id, {})
        points = "Unlimited" if user.get("unlimited") else f"{user.get('credits', 0)} Credits"
        bot.send_message(message.chat.id, f"💰 Current Balance: {points}")

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
        bot.send_message(message.chat.id, f"📞 Support: @FeaturesticLeaks")

    elif text == "❓ Help":
        bot.send_message(message.chat.id, "❓ Help Section:\n\n1. Use Search to find details.\n2. Each search costs 1 credit (unless Unlimited).\n3. Refer friends to earn more credits.")

    elif text == "🛒 Buy":
        bot.send_message(message.chat.id, "🛒 Premium Plans:\n\n1. 50 Credits - ₹50\n2. 150 Credits - ₹100\n3. Unlimited (1 Month) - ₹250\n\nContact @FeaturesticLeaks to buy.")

def process_search(message):
    user_id = str(message.from_user.id)
    user_input = message.text.strip()
    data = load_data()
    
    if not user_input.isdigit():
        bot.send_message(message.chat.id, "❌ Only phone numbers allowed. Send: 9852108915")
        return

    user_data = data["users"].get(user_id, {})
    is_unlimited = user_data.get("unlimited", False)
    
    if not is_unlimited and user_data.get("credits", 0) < 1:
        bot.send_message(message.chat.id, "❌ Aapke paas credits nahi hain! Please refer friends or buy credits.")
        return

    wait_msg = bot.send_message(message.chat.id, "⏳ Searching... Please wait.")
    
    # Deduct credit if not unlimited
    if not is_unlimited:
        data["users"][user_id]["credits"] -= 1
    
    data["stats"]["total_searches"] += 1
    data["users"][user_id]["search_history"].append(user_input)
    save_data(data)

    try:
        # API Call
        res = get_number_details(user_input)
        
        if not res or res.get("status") != "success":
            # Refund if API fails and not unlimited
            if not is_unlimited:
                data = load_data()
                data["users"][user_id]["credits"] += 1
                save_data(data)
            bot.edit_message_text("❌ Search failed! Credits have been refunded.", message.chat.id, wait_msg.message_id)
            return

        info = res.get("data", {})
        points_display = "Unlimited" if is_unlimited else f"{data['users'][user_id]['credits']}"
        
        output = (
            "✅ Success!\n\n"
            f"📱 Phone Number: {info.get('phone', user_input)}\n"
            f"🆔 Telegram ID: {info.get('telegram_id', 'N/A')}\n"
            f"👤 Name: {info.get('name', 'N/A')}\n"
            f"🌍 Country: {info.get('country', 'N/A')}\n"
            f"📞 Code: {info.get('country_code', 'N/A')}\n\n"
            f"💎 Remaining Points: {points_display}\n"
            f"🕐 Time: {datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"{CREDIT_LINE}"
        )
        
        bot.edit_message_text(output, message.chat.id, wait_msg.message_id)
        
    except Exception as e:
        # Refund on error
        if not is_unlimited:
            data = load_data()
            data["users"][user_id]["credits"] += 1
            save_data(data)
        bot.edit_message_text(f"❌ An error occurred. Credits refunded.", message.chat.id, wait_msg.message_id)

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
