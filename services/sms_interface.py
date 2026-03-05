"""
SarvaSahay SMS Interface Handler
Menu-driven SMS navigation with multi-language support
"""

from typing import Dict, Any, Optional, List, Tuple
from enum import Enum
from datetime import datetime
import re


class SMSLanguage(str, Enum):
    """Supported SMS languages"""
    HINDI = "hindi"
    MARATHI = "marathi"
    ENGLISH = "english"
    TAMIL = "tamil"
    BENGALI = "bengali"
    TELUGU = "telugu"
    KANNADA = "kannada"
    GUJARATI = "gujarati"


class SMSMenuState(str, Enum):
    """SMS conversation states"""
    INITIAL = "initial"
    LANGUAGE_SELECTION = "language_selection"
    MAIN_MENU = "main_menu"
    PROFILE_CREATION = "profile_creation"
    PROFILE_AGE = "profile_age"
    PROFILE_GENDER = "profile_gender"
    PROFILE_CASTE = "profile_caste"
    PROFILE_INCOME = "profile_income"
    PROFILE_LAND = "profile_land"
    PROFILE_EMPLOYMENT = "profile_employment"
    PROFILE_LOCATION = "profile_location"
    PROFILE_FAMILY = "profile_family"
    SCHEME_DISCOVERY = "scheme_discovery"
    APPLICATION_STATUS = "application_status"


class SMSInterfaceHandler:
    """
    SMS interface handler for multi-channel user interaction
    Provides menu-driven navigation in local languages
    """
    
    def __init__(self, profile_service=None, eligibility_service=None):
        self.profile_service = profile_service
        self.eligibility_service = eligibility_service
        self.sessions = {}  # Store user sessions: phone_number -> session_data
        self.translations = self._load_translations()
    
    def process_sms(self, phone_number: str, message: str) -> str:
        """
        Process incoming SMS and return response
        
        Args:
            phone_number: User's phone number
            message: SMS message content
            
        Returns:
            Response message to send back
        """
        if not phone_number or not message:
            return self._get_error_message("english")
        
        # Normalize phone number
        phone_number = self._normalize_phone_number(phone_number)
        
        # Get or create session
        session = self._get_session(phone_number)
        
        # Process message based on current state
        message = message.strip().upper()
        
        # Check for special commands
        if message in ["PROFILE BANAO", "CREATE PROFILE", "प्रोफाइल बनाओ", "प्रोफाईल बनवा"]:
            # Set default language if not set
            if not session.get("language"):
                session["language"] = SMSLanguage.ENGLISH
            return self._start_profile_creation(phone_number, session)
        
        if message in ["HELP", "मदद", "मदत"]:
            return self._get_help_message(session.get("language", "english"))
        
        # Route to appropriate handler based on state
        state = session.get("state", SMSMenuState.INITIAL)
        
        if state == SMSMenuState.INITIAL:
            return self._handle_initial(phone_number, message, session)
        elif state == SMSMenuState.LANGUAGE_SELECTION:
            return self._handle_language_selection(phone_number, message, session)
        elif state == SMSMenuState.MAIN_MENU:
            return self._handle_main_menu(phone_number, message, session)
        elif isinstance(state, str) and state.startswith("PROFILE_"):
            return self._handle_profile_creation(phone_number, message, session)
        elif state in [SMSMenuState.PROFILE_AGE, SMSMenuState.PROFILE_GENDER, SMSMenuState.PROFILE_CASTE,
                       SMSMenuState.PROFILE_INCOME, SMSMenuState.PROFILE_LAND, SMSMenuState.PROFILE_EMPLOYMENT,
                       SMSMenuState.PROFILE_LOCATION, SMSMenuState.PROFILE_FAMILY]:
            return self._handle_profile_creation(phone_number, message, session)
        elif state == SMSMenuState.SCHEME_DISCOVERY:
            return self._handle_scheme_discovery(phone_number, message, session)
        else:
            return self._get_main_menu(session.get("language", "english"))
    
    def _handle_initial(self, phone_number: str, message: str, session: Dict) -> str:
        """Handle initial contact"""
        # Check if message is a number (language selection)
        if message.isdigit() and 1 <= int(message) <= 8:
            return self._handle_language_selection(phone_number, message, session)
        
        # Set state to language selection
        session["state"] = SMSMenuState.LANGUAGE_SELECTION
        self._save_session(phone_number, session)
        
        return self._get_language_selection_menu()
    
    def _handle_language_selection(self, phone_number: str, message: str, session: Dict) -> str:
        """Handle language selection"""
        language_map = {
            "1": SMSLanguage.HINDI,
            "2": SMSLanguage.MARATHI,
            "3": SMSLanguage.ENGLISH,
            "4": SMSLanguage.TAMIL,
            "5": SMSLanguage.BENGALI,
            "6": SMSLanguage.TELUGU,
            "7": SMSLanguage.KANNADA,
            "8": SMSLanguage.GUJARATI
        }
        
        selected_language = language_map.get(message)
        if not selected_language:
            return self._get_language_selection_menu()
        
        session["language"] = selected_language
        session["state"] = SMSMenuState.MAIN_MENU
        self._save_session(phone_number, session)
        
        return self._get_main_menu(selected_language)
    
    def _handle_main_menu(self, phone_number: str, message: str, session: Dict) -> str:
        """Handle main menu selection"""
        language = session.get("language", SMSLanguage.ENGLISH)
        
        if message == "1":
            return self._start_profile_creation(phone_number, session)
        elif message == "2":
            return self._start_scheme_discovery(phone_number, session)
        elif message == "3":
            return self._check_application_status(phone_number, session)
        elif message == "4":
            return self._get_help_message(language)
        else:
            return self._get_main_menu(language)
    
    def _start_profile_creation(self, phone_number: str, session: Dict) -> str:
        """Start profile creation workflow"""
        language = session.get("language", SMSLanguage.ENGLISH)
        
        # Initialize profile data
        session["state"] = SMSMenuState.PROFILE_AGE
        session["profile_data"] = {
            "phone_number": phone_number,
            "demographics": {},
            "economic": {},
            "location": {},
            "family": {}
        }
        self._save_session(phone_number, session)
        
        return self._translate("profile_age_prompt", language)
    
    def _handle_profile_creation(self, phone_number: str, message: str, session: Dict) -> str:
        """Handle profile creation steps"""
        state = session["state"]
        language = session.get("language", SMSLanguage.ENGLISH)
        profile_data = session.get("profile_data", {})
        
        if state == SMSMenuState.PROFILE_AGE:
            return self._handle_age_input(phone_number, message, session)
        elif state == SMSMenuState.PROFILE_GENDER:
            return self._handle_gender_input(phone_number, message, session)
        elif state == SMSMenuState.PROFILE_CASTE:
            return self._handle_caste_input(phone_number, message, session)
        elif state == SMSMenuState.PROFILE_INCOME:
            return self._handle_income_input(phone_number, message, session)
        elif state == SMSMenuState.PROFILE_LAND:
            return self._handle_land_input(phone_number, message, session)
        elif state == SMSMenuState.PROFILE_EMPLOYMENT:
            return self._handle_employment_input(phone_number, message, session)
        elif state == SMSMenuState.PROFILE_LOCATION:
            return self._handle_location_input(phone_number, message, session)
        elif state == SMSMenuState.PROFILE_FAMILY:
            return self._handle_family_input(phone_number, message, session)
        
        return self._get_main_menu(language)
    
    def _handle_age_input(self, phone_number: str, message: str, session: Dict) -> str:
        """Handle age input"""
        language = session.get("language", SMSLanguage.ENGLISH)
        
        try:
            age = int(message)
            if age < 0 or age > 150:
                return self._translate("invalid_age", language)
            
            session["profile_data"]["demographics"]["age"] = age
            session["state"] = SMSMenuState.PROFILE_GENDER
            self._save_session(phone_number, session)
            
            return self._translate("profile_gender_prompt", language)
        except ValueError:
            return self._translate("invalid_number", language)
    
    def _handle_gender_input(self, phone_number: str, message: str, session: Dict) -> str:
        """Handle gender input"""
        language = session.get("language", SMSLanguage.ENGLISH)
        
        gender_map = {"1": "male", "2": "female", "3": "other"}
        gender = gender_map.get(message)
        
        if not gender:
            return self._translate("profile_gender_prompt", language)
        
        session["profile_data"]["demographics"]["gender"] = gender
        session["state"] = SMSMenuState.PROFILE_CASTE
        self._save_session(phone_number, session)
        
        return self._translate("profile_caste_prompt", language)
    
    def _handle_caste_input(self, phone_number: str, message: str, session: Dict) -> str:
        """Handle caste input"""
        language = session.get("language", SMSLanguage.ENGLISH)
        
        caste_map = {"1": "General", "2": "OBC", "3": "SC", "4": "ST"}
        caste = caste_map.get(message)
        
        if not caste:
            return self._translate("profile_caste_prompt", language)
        
        session["profile_data"]["demographics"]["caste"] = caste
        session["profile_data"]["demographics"]["maritalStatus"] = "married"  # Default
        session["state"] = SMSMenuState.PROFILE_INCOME
        self._save_session(phone_number, session)
        
        return self._translate("profile_income_prompt", language)
    
    def _handle_income_input(self, phone_number: str, message: str, session: Dict) -> str:
        """Handle income input"""
        language = session.get("language", SMSLanguage.ENGLISH)
        
        try:
            income = int(message)
            if income < 0:
                return self._translate("invalid_income", language)
            
            session["profile_data"]["economic"]["annualIncome"] = income
            session["state"] = SMSMenuState.PROFILE_LAND
            self._save_session(phone_number, session)
            
            return self._translate("profile_land_prompt", language)
        except ValueError:
            return self._translate("invalid_number", language)
    
    def _handle_land_input(self, phone_number: str, message: str, session: Dict) -> str:
        """Handle land ownership input"""
        language = session.get("language", SMSLanguage.ENGLISH)
        
        try:
            land = float(message)
            if land < 0:
                return self._translate("invalid_land", language)
            
            session["profile_data"]["economic"]["landOwnership"] = land
            session["state"] = SMSMenuState.PROFILE_EMPLOYMENT
            self._save_session(phone_number, session)
            
            return self._translate("profile_employment_prompt", language)
        except ValueError:
            return self._translate("invalid_number", language)
    
    def _handle_employment_input(self, phone_number: str, message: str, session: Dict) -> str:
        """Handle employment status input"""
        language = session.get("language", SMSLanguage.ENGLISH)
        
        employment_map = {
            "1": "farmer",
            "2": "laborer",
            "3": "self-employed",
            "4": "unemployed"
        }
        employment = employment_map.get(message)
        
        if not employment:
            return self._translate("profile_employment_prompt", language)
        
        session["profile_data"]["economic"]["employmentStatus"] = employment
        session["state"] = SMSMenuState.PROFILE_LOCATION
        self._save_session(phone_number, session)
        
        return self._translate("profile_location_prompt", language)
    
    def _handle_location_input(self, phone_number: str, message: str, session: Dict) -> str:
        """Handle location input (state, district, village)"""
        language = session.get("language", SMSLanguage.ENGLISH)
        
        # Parse location: STATE,DISTRICT,VILLAGE
        parts = [p.strip() for p in message.split(",")]
        
        if len(parts) < 3:
            return self._translate("invalid_location", language)
        
        session["profile_data"]["location"] = {
            "state": parts[0],
            "district": parts[1],
            "block": parts[2] if len(parts) > 2 else parts[1],
            "village": parts[2] if len(parts) == 3 else parts[1]
        }
        session["state"] = SMSMenuState.PROFILE_FAMILY
        self._save_session(phone_number, session)
        
        return self._translate("profile_family_prompt", language)
    
    def _handle_family_input(self, phone_number: str, message: str, session: Dict) -> str:
        """Handle family size input"""
        language = session.get("language", SMSLanguage.ENGLISH)
        
        try:
            family_size = int(message)
            if family_size < 1:
                return self._translate("invalid_family", language)
            
            session["profile_data"]["family"] = {
                "size": family_size,
                "dependents": max(0, family_size - 1)
            }
            
            # Save profile
            profile_id = self._save_profile(session["profile_data"])
            
            # Reset session to main menu
            session["state"] = SMSMenuState.MAIN_MENU
            session["profile_id"] = profile_id
            self._save_session(phone_number, session)
            
            return self._translate("profile_created", language).format(profile_id=profile_id)
        except ValueError:
            return self._translate("invalid_number", language)
    
    def _start_scheme_discovery(self, phone_number: str, session: Dict) -> str:
        """Start scheme discovery"""
        language = session.get("language", SMSLanguage.ENGLISH)
        profile_id = session.get("profile_id")
        
        if not profile_id:
            return self._translate("no_profile", language)
        
        # Get eligible schemes (mock for now)
        schemes = self._get_eligible_schemes(profile_id)
        
        if not schemes:
            return self._translate("no_schemes", language)
        
        response = self._translate("schemes_found", language).format(count=len(schemes))
        for i, scheme in enumerate(schemes[:5], 1):  # Show top 5
            response += f"\n{i}. {scheme['name']} - ₹{scheme['benefit']}"
        
        return response
    
    def _check_application_status(self, phone_number: str, session: Dict) -> str:
        """Check application status"""
        language = session.get("language", SMSLanguage.ENGLISH)
        profile_id = session.get("profile_id")
        
        if not profile_id:
            return self._translate("no_profile", language)
        
        return self._translate("status_check", language)
    
    def _save_profile(self, profile_data: Dict) -> str:
        """Save profile using profile service"""
        if self.profile_service:
            return self.profile_service.create_profile(profile_data)
        return "DEMO-" + str(hash(str(profile_data)))[:8]
    
    def _get_eligible_schemes(self, profile_id: str) -> List[Dict]:
        """Get eligible schemes for profile"""
        # Mock implementation
        return [
            {"name": "PM-KISAN", "benefit": 6000},
            {"name": "Aadhaar Seeding", "benefit": 2000},
            {"name": "Crop Insurance", "benefit": 5000}
        ]
    
    def _get_session(self, phone_number: str) -> Dict:
        """Get or create user session"""
        # Normalize phone number for consistency
        phone_number = self._normalize_phone_number(phone_number)
        
        if phone_number not in self.sessions:
            self.sessions[phone_number] = {
                "state": SMSMenuState.INITIAL,
                "language": None,
                "created_at": datetime.utcnow().isoformat()
            }
        return self.sessions[phone_number]
    
    def _save_session(self, phone_number: str, session: Dict):
        """Save user session"""
        # Normalize phone number for consistency
        phone_number = self._normalize_phone_number(phone_number)
        session["updated_at"] = datetime.utcnow().isoformat()
        self.sessions[phone_number] = session
    
    def _normalize_phone_number(self, phone: str) -> str:
        """Normalize phone number format"""
        # Remove spaces, dashes, and country code
        cleaned = re.sub(r'[\s\-\+]', '', phone)
        if cleaned.startswith("91"):
            cleaned = cleaned[2:]
        return cleaned
    
    def _get_language_selection_menu(self) -> str:
        """Get language selection menu"""
        return """Welcome to SarvaSahay! भाषा चुनें / Select Language:
1. हिंदी (Hindi)
2. मराठी (Marathi)
3. English
4. தமிழ் (Tamil)
5. বাংলা (Bengali)
6. తెలుగు (Telugu)
7. ಕನ್ನಡ (Kannada)
8. ગુજરાતી (Gujarati)"""
    
    def _get_main_menu(self, language: str) -> str:
        """Get main menu in specified language"""
        return self._translate("main_menu", language)
    
    def _get_help_message(self, language: str) -> str:
        """Get help message"""
        return self._translate("help_message", language)
    
    def _get_error_message(self, language: str) -> str:
        """Get error message"""
        return self._translate("error_message", language)
    
    def _translate(self, key: str, language: str) -> str:
        """Translate message key to specified language"""
        return self.translations.get(language, {}).get(key, self.translations["english"].get(key, ""))
    
    def _load_translations(self) -> Dict[str, Dict[str, str]]:
        """Load translation strings"""
        return {
            "english": {
                "main_menu": "SarvaSahay Main Menu:\n1. Create Profile\n2. Find Schemes\n3. Check Status\n4. Help",
                "profile_age_prompt": "Enter your age (in years):",
                "profile_gender_prompt": "Select gender:\n1. Male\n2. Female\n3. Other",
                "profile_caste_prompt": "Select category:\n1. General\n2. OBC\n3. SC\n4. ST",
                "profile_income_prompt": "Enter annual income (in rupees):",
                "profile_land_prompt": "Enter land ownership (in acres, 0 if none):",
                "profile_employment_prompt": "Select employment:\n1. Farmer\n2. Laborer\n3. Self-employed\n4. Unemployed",
                "profile_location_prompt": "Enter location as: STATE,DISTRICT,VILLAGE",
                "profile_family_prompt": "Enter family size (number of members):",
                "profile_created": "Profile created! ID: {profile_id}\nReply with 2 to find schemes.",
                "invalid_age": "Invalid age. Please enter age between 0-150.",
                "invalid_number": "Invalid input. Please enter a number.",
                "invalid_income": "Invalid income. Please enter positive amount.",
                "invalid_land": "Invalid land area. Please enter positive value.",
                "invalid_location": "Invalid format. Use: STATE,DISTRICT,VILLAGE",
                "invalid_family": "Invalid family size. Must be at least 1.",
                "no_profile": "No profile found. Reply 1 to create profile.",
                "no_schemes": "No eligible schemes found. Update your profile.",
                "schemes_found": "Found {count} schemes for you:",
                "status_check": "Application status feature coming soon!",
                "help_message": "SarvaSahay Help:\n- Reply 1: Create profile\n- Reply 2: Find schemes\n- Reply 3: Check status\n- Reply HELP anytime",
                "error_message": "Error processing request. Reply HELP for assistance."
            },
            "hindi": {
                "main_menu": "सर्वसहाय मुख्य मेनू:\n1. प्रोफाइल बनाएं\n2. योजनाएं खोजें\n3. स्थिति जांचें\n4. मदद",
                "profile_age_prompt": "अपनी उम्र दर्ज करें (वर्षों में):",
                "profile_gender_prompt": "लिंग चुनें:\n1. पुरुष\n2. महिला\n3. अन्य",
                "profile_caste_prompt": "श्रेणी चुनें:\n1. सामान्य\n2. ओबीसी\n3. एससी\n4. एसटी",
                "profile_income_prompt": "वार्षिक आय दर्ज करें (रुपये में):",
                "profile_land_prompt": "भूमि स्वामित्व दर्ज करें (एकड़ में, यदि नहीं तो 0):",
                "profile_employment_prompt": "रोजगार चुनें:\n1. किसान\n2. मजदूर\n3. स्व-रोजगार\n4. बेरोजगार",
                "profile_location_prompt": "स्थान दर्ज करें: राज्य,जिला,गांव",
                "profile_family_prompt": "परिवार का आकार दर्ज करें (सदस्यों की संख्या):",
                "profile_created": "प्रोफाइल बनाई गई! आईडी: {profile_id}\nयोजनाएं खोजने के लिए 2 लिखें।",
                "invalid_age": "अमान्य उम्र। कृपया 0-150 के बीच उम्र दर्ज करें।",
                "invalid_number": "अमान्य इनपुट। कृपया संख्या दर्ज करें।",
                "invalid_income": "अमान्य आय। कृपया सकारात्मक राशि दर्ज करें।",
                "invalid_land": "अमान्य भूमि क्षेत्र। कृपया सकारात्मक मान दर्ज करें।",
                "invalid_location": "अमान्य प्रारूप। उपयोग करें: राज्य,जिला,गांव",
                "invalid_family": "अमान्य परिवार का आकार। कम से कम 1 होना चाहिए।",
                "no_profile": "कोई प्रोफाइल नहीं मिली। प्रोफाइल बनाने के लिए 1 लिखें।",
                "no_schemes": "कोई योग्य योजना नहीं मिली। अपनी प्रोफाइल अपडेट करें।",
                "schemes_found": "आपके लिए {count} योजनाएं मिलीं:",
                "status_check": "आवेदन स्थिति सुविधा जल्द आ रही है!",
                "help_message": "सर्वसहाय मदद:\n- 1 लिखें: प्रोफाइल बनाएं\n- 2 लिखें: योजनाएं खोजें\n- 3 लिखें: स्थिति जांचें\n- किसी भी समय HELP लिखें",
                "error_message": "अनुरोध संसाधित करने में त्रुटि। सहायता के लिए HELP लिखें।"
            },
            "marathi": {
                "main_menu": "सर्वसहाय मुख्य मेनू:\n1. प्रोफाईल तयार करा\n2. योजना शोधा\n3. स्थिती तपासा\n4. मदत",
                "profile_age_prompt": "तुमचे वय प्रविष्ट करा (वर्षांमध्ये):",
                "profile_gender_prompt": "लिंग निवडा:\n1. पुरुष\n2. स्त्री\n3. इतर",
                "profile_caste_prompt": "श्रेणी निवडा:\n1. सामान्य\n2. ओबीसी\n3. एससी\n4. एसटी",
                "profile_income_prompt": "वार्षिक उत्पन्न प्रविष्ट करा (रुपयांमध्ये):",
                "profile_land_prompt": "जमीन मालकी प्रविष्ट करा (एकरमध्ये, नसल्यास 0):",
                "profile_employment_prompt": "रोजगार निवडा:\n1. शेतकरी\n2. मजूर\n3. स्व-रोजगार\n4. बेरोजगार",
                "profile_location_prompt": "स्थान प्रविष्ट करा: राज्य,जिल्हा,गाव",
                "profile_family_prompt": "कुटुंबाचा आकार प्रविष्ट करा (सदस्यांची संख्या):",
                "profile_created": "प्रोफाईल तयार झाली! आयडी: {profile_id}\nयोजना शोधण्यासाठी 2 लिहा।",
                "invalid_age": "अवैध वय। कृपया 0-150 दरम्यान वय प्रविष्ट करा।",
                "invalid_number": "अवैध इनपुट। कृपया संख्या प्रविष्ट करा।",
                "invalid_income": "अवैध उत्पन्न। कृपया सकारात्मक रक्कम प्रविष्ट करा।",
                "invalid_land": "अवैध जमीन क्षेत्र। कृपया सकारात्मक मूल्य प्रविष्ट करा।",
                "invalid_location": "अवैध स्वरूप। वापरा: राज्य,जिल्हा,गाव",
                "invalid_family": "अवैध कुटुंब आकार। किमान 1 असणे आवश्यक आहे।",
                "no_profile": "प्रोफाईल सापडली नाही। प्रोफाईल तयार करण्यासाठी 1 लिहा।",
                "no_schemes": "कोणतीही पात्र योजना सापडली नाही। तुमची प्रोफाईल अपडेट करा।",
                "schemes_found": "तुमच्यासाठी {count} योजना सापडल्या:",
                "status_check": "अर्ज स्थिती वैशिष्ट्य लवकरच येत आहे!",
                "help_message": "सर्वसहाय मदत:\n- 1 लिहा: प्रोफाईल तयार करा\n- 2 लिहा: योजना शोधा\n- 3 लिहा: स्थिती तपासा\n- कधीही HELP लिहा",
                "error_message": "विनंती प्रक्रिया करताना त्रुटी. मदतीसाठी HELP लिहा।"
            }
        }
