import phonenumbers
from phonenumbers import carrier, geocoder

def get_number_details(phone_number):
    """
    Returns a formatted string (full_report) with all details.
    """
    try:
        if not phone_number.startswith('+'):
            phone_number = '+' + phone_number
            
        parsed_number = phonenumbers.parse(phone_number)
        
        country = geocoder.description_for_number(parsed_number, "en")
        carrier_name = carrier.name_for_number(parsed_number, "en")
        
        report = (
            f"✅ <b>Search Result</b>\n"
            f"────────────────\n"
            f"📱 <b>Phone:</b> {phone_number}\n"
            f"👤 <b>Name:</b> User Name (Sample)\n"
            f"👨 <b>Father:</b> Father Name (Sample)\n"
            f"🏠 <b>Address:</b> Sample Address, City, Country\n"
            f"🌍 <b>Country:</b> {country}\n"
            f"📞 <b>Carrier:</b> {carrier_name}\n"
            f"🆔 <b>Telegram ID:</b> 123456789\n"
            f"────────────────\n"
            f"Developed By @FeaturesticLeaks"
        )
        return report
    except Exception as e:
        return f"❌ <b>Error:</b> {str(e)}"
