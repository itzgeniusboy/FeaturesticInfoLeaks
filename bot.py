import telebot
from telebot import types
import json, os, time, requests
from flask import Flask
from threading import Thread
from datetime import datetime
import pytz
import concurrent.futures
from num import get_number_details

# ===== CONFIG =====
BOT_TOKEN = "8741964335:AAF7wdSGmcVdEadFw3RlryIA9yeBUuUsA6w"
ADMIN_ID = 1969067694  # INTEGER
CHANNEL_1_LINK = "https://t.me/FeaturesticLeaks"
CHANNEL_2_LINK = "https://t.me/OneCoreEngine"
CHANNEL_1_ID = "-1002278499725"
CHANNEL_2_ID = "-1002265779523"
CREDIT_LINE = "Developed By @FeaturesticLeaks"

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)
DATA_FILE = "database.json"
IST = pytz.timezone('Asia/Kolkata')

# ===== DATABASE =====
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            try:
                return json.load(f)
            except:
                return {"users": {}, "stats": {"total_searches": 0, "total_users": 0}}
    return {"users": {}, "stats": {"total_searches": 0, "total_users": 0}}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# ===== CHECK CREDITS =====
def has_credits(user_id):
    if user_id == ADMIN_ID:
        return True
    data = load_data()
    uid = str(user_id)
    user = data.get("users", {}).get(uid, {})
    if user.get("unlimited", False):
        return True
    return user.get('credits', 0) >= 1

def deduct_credit(user_id):
    if user_id == ADMIN_ID:
        return
    data = load_data()
    uid = str(user_id)
    if uid in data.get("users", {}):
        if data["users"][uid].get("unlimited", False):
            return
        data["users"][uid]['credits'] = max(0, data["users"][uid].get('credits', 0) - 1)
        save_data(data)

def get_credits_display(user_id):
    if user_id == ADMIN_ID:
        return "Unlimited"
    data = load_data()
    uid = str(user_id)
    user = data.get("users", {}).get(uid, {})
    if user.get("unlimited", False):
        return "Unlimited"
    return user.get('credits', 0)

def get_current_time():
    return datetime.now(IST).strftime('%d-%m-%Y %I:%M:%S %p')

# ===== FORCE SUBSCRIBE =====
def is_subscribed(user_id):
    if user_id == ADMIN_ID:
        return True
    try:
        status1 = bot.get_chat_member(CHANNEL_1_ID, user_id).status
        status2 = bot.get_chat_member(CHANNEL_2_ID, user_id).status
        return status1 in ['member', 'administrator', 'creator'] and status2 in ['member', 'administrator', 'creator']
    except:
        return False

# ===== SEARCH HANDLER =====
@bot.message_handler(func=lambda m: m.text and (m.text.isdigit() or m.text.startswith('/info')))
def handle_search(message):
    user_id = message.from_user.id
    if not is_subscribed(user_id):
        return start_cmd(message)
    
    number = message.text.replace('/info', '').strip()
    if not number.isdigit():
        return bot.reply_to(message, "❌ Only phone numbers allowed. Example: 9852108915")
    
    if not has_credits(user_id):
        return bot.reply_to(message, "❌ Aapke paas credits nahi hain! Refer friends to earn.")
    
    msg = bot.reply_to(message, "⏳ Searching... Please wait")
    
    try:
        # API Call with 10s Timeout
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(get_number_details, number)
            try:
                result = future.result(timeout=10)
            except concurrent.futures.TimeoutError:
                bot.edit_message_text("❌ Timeout! API not responding. Try again later.", message.chat.id, msg.message_id)
                return
        
        if result and result.get("status") == "success":
            info = result.get("data", {})
            output = f"""✅ Success!

📱 Phone Number: {number}
🆔 Telegram ID: {info.get('telegram_id', 'N/A')}
👤 Name: {info.get('name', 'Unknown')}
🌍 Country: {info.get('country', 'N/A')}
📞 Code: {info.get('country_code', 'N/A')}

💎 Remaining Points: {get_credits_display(user_id)}
🕐 Time: {get_current_time()}

{CREDIT_LINE}"""
            
            bot.edit_message_text(output, message.chat.id, msg.message_id)
            deduct_credit(user_id)
            
            # Update stats
            data = load_data()
            data["stats"]["total_searches"] += 1
            uid = str(user_id)
            if uid in data["users"]:
                data["users"][uid]["search_history"].append(number)
            save_data(data)
        else:
            bot.edit_message_text("❌ No data found for this number!", message.chat.id, msg.message_id)
            
    except Exception as e:
        bot.edit_message_text(f"❌ Error: {str(e)}", message.chat.id, msg.message_id)

# ===== START COMMAND =====
@bot.message_handler(commands=['start'])
def start_cmd(message):
    user_id = message.from_user.id
    uid = str(user_id)
    
    data = load_data()
    
    # Handle Referral
    args = message.text.split()
    referrer_id = args[1] if len(args) > 1 else None
    
    if uid not in data["users"]:
        data["users"][uid] = {
            "credits": 5, 
            "unlimited": True if user_id == ADMIN_ID else False,
            "referrals": 0,
            "referred_by": referrer_id,
            "search_history": [],
            "join_date": get_current_time()
        }
        data["stats"]["total_users"] += 1
        
        if referrer_id and referrer_id in data["users"] and referrer_id != uid:
            data["users"][referrer_id]["credits"] += 5
            data["users"][referrer_id]["referrals"] += 1
            try:
                bot.send_message(referrer_id, f"🎁 Referral Successful! You got 5 credits.")
            except: pass
            
        save_data(data)
    
    if not is_subscribed(user_id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Channel 1", url=CHANNEL_1_LINK))
        markup.add(types.InlineKeyboardButton("Channel 2", url=CHANNEL_2_LINK))
        markup.add(types.InlineKeyboardButton("✅ Check Join", callback_data="check_join"))
        bot.send_message(message.chat.id, "❌ Aapne dono channels join nahi kiye hain!\n\nPlease join both channels to use the bot.", reply_markup=markup)
    else:
        markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        markup.add(types.KeyboardButton("🔍 Search"), types.KeyboardButton("👤 Profile"))
        markup.add(types.KeyboardButton("💰 Points"), types.KeyboardButton("🎁 Referral"))
        markup.add(types.KeyboardButton("📞 Support"), types.KeyboardButton("❓ Help"))
        
        bot.send_message(message.chat.id, f"Welcome! Send phone number to search.\nCredits: {get_credits_display(user_id)}", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "check_join")
def check_join(call):
    if is_subscribed(call.from_user.id):
        bot.answer_callback_query(call.id, "✅ Success!")
        bot.edit_message_text("Aapne channels join kar liye hain!", call.message.chat.id, call.message.message_id)
        start_cmd(call.message)
    else:
        bot.answer_callback_query(call.id, "❌ Join both channels first!", show_alert=True)

# ===== ADMIN COMMANDS =====
@bot.message_handler(commands=['givecredits', 'add'])
def give_credits(message):
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
            bot.send_message(message.chat.id, "❌ User not found.")
    except:
        bot.send_message(message.chat.id, "Usage: /add <user_id> <amount>")

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

# ===== BUTTON HANDLERS =====
@bot.message_handler(func=lambda m: True)
def handle_buttons(message):
    user_id = message.from_user.id
    if not is_subscribed(user_id):
        return start_cmd(message)
    
    text = message.text
    if text == "🔍 Search":
        bot.send_message(message.chat.id, "📱 Send phone number to search\nExample: 9852108915")
    
    elif text == "👤 Profile":
        uid = str(user_id)
        data = load_data()
        user = data["users"].get(uid, {})
        
        profile_text = f"""👤 PROFILE

🆔 ID: {user_id}
💎 Points: {get_credits_display(user_id)}
👥 Referrals: {user.get('referrals', 0)}
👑 Status: {'Unlimited' if (user_id == ADMIN_ID or user.get('unlimited')) else 'Normal'}"""
        bot.send_message(message.chat.id, profile_text)

    elif text == "💰 Points":
        bot.send_message(message.chat.id, f"💎 Your Points: {get_credits_display(user_id)}")

    elif text == "🎁 Referral":
        ref_link = f"https://t.me/{(bot.get_me().username)}?start={user_id}"
        bot.send_message(message.chat.id, f"🎁 Your Referral Link:\n`{ref_link}`", parse_mode="Markdown")

    elif text == "📞 Support":
        bot.send_message(message.chat.id, "📞 Support: @FeaturesticLeaks")

    elif text == "❓ Help":
        bot.send_message(message.chat.id, "🔍 Send any phone number to search!\nExample: 9852108915")

# ===== WEB SERVER =====
@app.route('/')
def home():
    return "Bot Running!"

def run():
    port = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=port)

# ===== MAIN =====
if __name__ == "__main__":
    try:
        bot.remove_webhook()
        time.sleep(1)
        Thread(target=run).start()
        print("✅ Bot Started!")
        bot.infinity_polling(skip_pending=True)
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(5)
