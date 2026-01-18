from app.proto import output_pb2, personalInfo_pb2
import httpx
import json
import time
from google.protobuf import json_format, message
from Crypto.Cipher import AES
import base64
from pymongo import MongoClient
import os

# Constants
MAIN_KEY = base64.b64decode('WWcmdGMlREV1aDYlWmNeOA==')
MAIN_IV = base64.b64decode('Nm95WkRyMjJFM3ljaGpNJQ==')


# Region to flag mapping
REGION_FLAGS = {
    # Africa
    "ao": "🇦🇴", "bf": "🇧🇫", "bi": "🇧🇮", "bj": "🇧🇯", "bw": "🇧🇼", "cd": "🇨🇩", "cf": "🇨🇫", "cg": "🇨🇬", 
    "ci": "🇨🇮", "cm": "🇨🇲", "cv": "🇨🇻", "dj": "🇩🇯", "dz": "🇩🇿", "eg": "🇪🇬", "eh": "🇪🇭", "er": "🇪🇷", 
    "et": "🇪🇹", "ga": "🇬🇦", "gh": "🇬🇭", "gm": "🇬🇲", "gn": "🇬🇳", "gq": "🇬🇶", "gw": "🇬🇼", "ke": "🇰🇪", 
    "km": "🇰🇲", "lr": "🇱🇷", "ls": "🇱🇸", "ly": "🇱🇾", "ma": "🇲🇦", "mg": "🇲🇬", "ml": "🇲🇱", "mr": "🇲🇷", 
    "mu": "🇲🇺", "mw": "🇲🇼", "mz": "🇲🇿", "na": "🇳🇦", "ne": "🇳🇪", "ng": "🇳🇬", "rw": "🇷🇼", "sc": "🇸🇨", 
    "sd": "🇸🇩", "sl": "🇸🇱", "sn": "🇸🇳", "so": "🇸🇴", "ss": "🇸🇸", "sz": "🇸🇿", "td": "🇹🇩", "tg": "🇹🇬", 
    "tn": "🇹🇳", "tz": "🇹🇿", "ug": "🇺🇬", "za": "🇿🇦", "zm": "🇿🇲", "zw": "🇿🇼",
    
    # The Americas
    "ag": "🇦🇬", "ai": "🇦🇮", "ar": "🇦🇷", "aw": "🇦🇼", "bb": "🇧🇧", "bl": "🇧🇱", "bm": "🇧🇲", "bo": "🇧🇴", 
    "bq": "🇧🇶", "br": "🇧🇷", "bs": "🇧🇸", "bz": "🇧🇿", "ca": "🇨🇦", "cl": "🇨🇱", "co": "🇨🇴", "cr": "🇨🇷", 
    "cu": "🇨🇺", "cw": "🇨🇼", "dm": "🇩🇲", "do": "🇩🇴", "ec": "🇪🇨", "fk": "🇫🇰", "gd": "🇬🇩", "gf": "🇬🇫", 
    "gp": "🇬🇵", "gt": "🇬🇹", "gy": "🇬🇾", "hn": "🇭🇳", "ht": "🇭🇹", "jm": "🇯🇲", "kn": "🇰🇳", "ky": "🇰🇾", 
    "lc": "🇱🇨", "mf": "🇲🇫", "mq": "🇲🇶", "ms": "🇲🇸", "mx": "🇲🇽", "ni": "🇳🇮", "pa": "🇵🇦", "pe": "🇵🇪", 
    "pm": "🇵🇲", "pr": "🇵🇷", "py": "🇵🇾", "sr": "🇸🇷", "sv": "🇸🇻", "sx": "🇸🇽", "tc": "🇹🇨", "tt": "🇹🇹", 
    "us": "🇺🇸", "uy": "🇺🇾", "ve": "🇻🇪", "vg": "🇻🇬", "vi": "🇻🇮",
    
    # Asia & The Middle East
    "ae": "🇦🇪", "af": "🇦🇫", "az": "🇦🇿", "bd": "🇧🇩", "bh": "🇧🇭", "bn": "🇧🇳", "bt": "🇧🇹", "cn": "🇨🇳", 
    "hk": "🇭🇰", "id": "🇮🇩", "il": "🇮🇱", "in": "🇮🇳", "ind": "🇮🇳", "iq": "🇮🇶", "ir": "🇮🇷", "jo": "🇯🇴", 
    "jp": "🇯🇵", "kg": "🇰🇬", "kh": "🇰🇭", "kp": "🇰🇵", "kr": "🇰🇷", "kw": "🇰🇼", "kz": "🇰🇿", "la": "🇱🇦", 
    "lb": "🇱🇧", "lk": "🇱🇰", "mm": "🇲🇲", "mn": "🇲🇳", "mo": "🇲🇴", "mv": "🇲🇻", "my": "🇲🇾", "np": "🇳🇵", 
    "om": "🇴🇲", "ph": "🇵🇭", "pk": "🇵🇰", "ps": "🇵🇸", "qa": "🇶🇦", "ru": "🇷🇺", "sa": "🇸🇦", "sg": "🇸🇬", 
    "sy": "🇸🇾", "th": "🇹🇭", "tj": "🇹🇯", "tl": "🇹🇱", "tm": "🇹🇲", "tr": "🇹🇷", "tw": "🇹🇼", "uz": "🇺🇿", 
    "vn": "🇻🇳", "ye": "🇾🇪",
    
    # Europe
    "ad": "🇦🇩", "al": "🇦🇱", "am": "🇦🇲", "at": "🇦🇹", "ba": "🇧🇦", "be": "🇧🇪", "bg": "🇧🇬", "by": "🇧🇾", 
    "ch": "🇨🇭", "cq": "🇨🇶", "cy": "🇨🇾", "cz": "🇨🇿", "de": "🇩🇪", "dk": "🇩🇰", "ea": "🇪🇦", "ee": "🇪🇪", 
    "es": "🇪🇸", "eu": "🇪🇺", "fi": "🇫🇮", "fr": "🇫🇷", "gb": "🇬🇧", "ge": "🇬🇪", "gg": "🇬🇬", "gi": "🇬🇮", 
    "gr": "🇬🇷", "hr": "🇭🇷", "hu": "🇭🇺", "ie": "🇮🇪", "im": "🇮🇲", "is": "🇮🇸", "it": "🇮🇹", "je": "🇯🇪", 
    "li": "🇱🇮", "lt": "🇱🇹", "lu": "🇱🇺", "lv": "🇱🇻", "mc": "🇲🇨", "md": "🇲🇩", "me": "🇲🇪", "mk": "🇲🇰", 
    "mt": "🇲🇹", "nl": "🇳🇱", "no": "🇳🇴", "pl": "🇵🇱", "pt": "🇵🇹", "ro": "🇷🇴", "rs": "🇷🇸", "se": "🇸🇪", 
    "si": "🇸🇮", "sk": "🇸🇰", "sm": "🇸🇲", "ua": "🇺🇦", "va": "🇻🇦", "xk": "🇽🇰", "eng": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", 
    "sct": "🏴󠁧󠁢󠁳󠁣󠁴󠁿", "wls": "🏴󠁧󠁢󠁷󠁬󠁳󠁿",
    
    # Oceania, Island Nations & Territories
    "ac": "🇦🇨", "aq": "🇦🇶", "as": "🇦🇸", "au": "🇦🇺", "ax": "🇦🇽", "bv": "🇧🇻", "cc": "🇨🇨", "ck": "🇨🇰", 
    "cp": "🇨🇵", "cx": "🇨🇽", "dg": "🇩🇬", "fj": "🇫🇯", "fm": "🇫🇲", "gl": "🇬🇱", "gs": "🇬🇸", "gu": "🇬🇺", 
    "hm": "🇭🇲", "ic": "🇮🇨", "io": "🇮🇴", "ki": "🇰🇮", "mh": "🇲🇭", "mp": "🇲🇵", "nc": "🇳🇨", "nf": "🇳🇫", 
    "nr": "🇳🇷", "nu": "🇳🇺", "nz": "🇳🇿", "pf": "🇵🇫", "pg": "🇵🇬", "pn": "🇵🇳", "pw": "🇵🇼", "re": "🇷🇪", 
    "sb": "🇸🇧", "sh": "🇸🇭", "sj": "🇸🇯", "st": "🇸🇹", "ta": "🇹🇦", "tf": "🇹🇫", "tk": "🇹🇰", "to": "🇹🇴", 
    "tv": "🇹🇻", "um": "🇺🇲", "vc": "🇻🇨", "vu": "🇻🇺", "wf": "🇼🇫", "ws": "🇼🇸", "yt": "🇾🇹"
}

# Prime level to Discord emoji mapping
PRIME_ICONS = {
    1: "<:prime_1:1432065617246294208>",
    2: "<:prime_2:1432065635608690778>",
    3: "<:prime_3:1432065651530272928>",
    4: "<:prime_4:1432065675521691758>",
    5: "<:prime_5:1432065689597771887>",
    6: "<:prime_6:1432065707863965758>",
    7: "<:prime_7:1432065724184264704>",
    8: "<:prime_8:1432065741980565594>"
}

# MongoDB connection
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client.info_xpert
tokens_collection = db.tokens

async def json_to_proto(json_data: str, proto_message: message.Message) -> bytes:
    """Convert JSON data to protobuf bytes"""
    json_format.ParseDict(json.loads(json_data), proto_message)
    return proto_message.SerializeToString()

def pad(text: bytes) -> bytes:
    """Add PKCS7 padding to text"""
    padding_length = AES.block_size - (len(text) % AES.block_size)
    padding = bytes([padding_length] * padding_length)
    return text + padding

def aes_cbc_encrypt(key: bytes, iv: bytes, plaintext: bytes) -> bytes:
    """Encrypt data using AES-CBC"""
    aes = AES.new(key, AES.MODE_CBC, iv)
    padded_plaintext = pad(plaintext)
    return aes.encrypt(padded_plaintext)

def decode_protobuf(encoded_data: bytes, message_type: message.Message) -> message.Message:
    """Decode protobuf data"""
    message_instance = message_type()
    message_instance.ParseFromString(encoded_data)
    return message_instance

def get_jwt_tokens():
    """Get JWT tokens from database for allowed regions"""
    allowed_regions = {"bd", "pk", "ind", "us"}
    tokens_cursor = tokens_collection.find({"region": {"$in": list(allowed_regions)}})
    
    tokens = {}
    for doc in tokens_cursor:
        region = doc.get("region")
        token = doc.get("token")
        if region and token:
            tokens[region] = token
    return tokens

def get_url(region):
    if region == "ind":
        return "https://client.ind.freefiremobile.com"
    elif region in {"br", "us", "sac", "na"}:
        return "https://client.us.freefiremobile.com"
    else:
        return "https://clientbp.ggblueshark.com"

def build_headers(token):
    return {
        'User-Agent': "Dalvik/2.1.0 (Linux; U; Android 9; ASUS_Z01QD Build/PI",
        'Connection': "Keep-Alive",
        'Accept-Encoding': "gzip",
        'Content-Type': "application/x-www-form-urlencoded",
        'Expect': "100-continue",
        'Authorization': f"Bearer {token}",
        'X-Unity-Version': "2018.4.11f1",
        'X-GA': "v1 1",
        'ReleaseVersion': "OB52",
    }

   

def format_response_data(data, region):
    """Format response data to include region flags and prime icons"""
    if isinstance(data, dict):
        # Format region with flag
        if 'region' in data:
            region_code = data['region'].lower()
            flag = REGION_FLAGS.get(region_code, "")
            if flag:
                data['region'] = f"{data['region']} {flag}"
        
        # Format prime level with icon
        if 'primeLevel' in data and isinstance(data['primeLevel'], dict):
            prime_level = data['primeLevel'].get('primeLevel')
            if prime_level and prime_level in PRIME_ICONS:
                data['primeLevel']['primeLevel'] = f"{prime_level} {PRIME_ICONS[prime_level]}"
        
        # Recursively format nested dictionaries
        for key, value in data.items():
            if isinstance(value, dict):
                data[key] = format_response_data(value, region)
            elif isinstance(value, list):
                data[key] = [format_response_data(item, region) if isinstance(item, dict) else item for item in value]
    
    return data

async def GetAccountInformation(ID, UNKNOWN_ID, endpoint):
    """Get account information from Free Fire API"""
    try:
        # Create JSON payload
        json_data = json.dumps({
            "a": ID,
            "b": UNKNOWN_ID
        })
        
        # Get tokens from database
        tokens = get_jwt_tokens()
        if not tokens:
            return {
                "error": "No tokens found in database",
                "message": "Service temporarily unavailable"
            }

        # Try regions in priority order
        # Try regions in priority order; ensure we include 'us' so tokens in DB are used
        region_priority = ["bd", "pk", "ind", "us", "na"]
        successful_region = None
        
        for region in region_priority:
            token = tokens.get(region)
            if not token:
                continue
                
            try:
                # Prepare request data
                server_url = get_url(region)
                headers = build_headers(token)
                encoded_result = await json_to_proto(json_data, output_pb2.PlayerInfoByLokesh())
                payload = aes_cbc_encrypt(MAIN_KEY, MAIN_IV, encoded_result)
                
                # Make API request
                async with httpx.AsyncClient() as client:
                    response = await client.post(server_url + endpoint, data=payload, headers=headers)
                    response.raise_for_status()
                    
                    # Decode response
                    message = decode_protobuf(response.content, personalInfo_pb2.PersonalInfoByLokesh)
                    
                    if hasattr(message, 'developer_info'):
                        # Create developer info object
                        dev_info = personalInfo_pb2.DeveloperInfo()
                        dev_info.developer_name = "Sukh Daku"  
                        dev_info.signature = "Sukh Daku — Always learning 💻 Full-stack Developer "
                        dev_info.do_not_remove_credits = True
                        
                        # Assign to message
                        message.developer_info.CopyFrom(dev_info)
                    
                    # Convert to JSON and format with flags/icons
                    json_data = json.loads(json_format.MessageToJson(message))
                    successful_region = region
                    return format_response_data(json_data, successful_region)
                    
            except Exception as e:
                # Continue to next region if current one fails
                continue
        
        # If all regions failed
        return {
            "error": "All regions failed",
            "message": "Unable to fetch account information"
        }

    except Exception as e:
        return {
            "error": "Failed to get account info",
            "reason": str(e)
        }
