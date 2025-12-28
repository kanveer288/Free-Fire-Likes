from flask import Flask, request, jsonify, Response
import asyncio
import json
from pymongo import MongoClient
from google.protobuf.json_format import MessageToJson
from app.encryption import enc
from app.request_handler import make_request, send_multiple_requests

# -------------------------
# Flask init
# -------------------------
app = Flask(__name__)

# -------------------------
# MongoDB init
# -------------------------
client = MongoClient(
    "mongodb+srv://manat:sukh123@xpert.8w1vywl.mongodb.net/?appName=xpert"
)
db = client["test"]

# success count collection
state_collection = db["token_state"]

# -------------------------
# Region config
# -------------------------
REGION_CONFIG = {
    "IND": {
        "tokens": "region_IND",
        "url": "https://client.ind.freefiremobile.com/LikeProfile",
        "state": "IND"
    },
    "NX": {
        "tokens": "nx_tokens",
        "url": "https://client.us.freefiremobile.com/LikeProfile",
        "state": "NX"
    },
    "AG": {
        "tokens": "ag_tokens",
        "url": "https://clientbp.ggblueshark.com/LikeProfile",
        "state": "AG"
    }
}

# -------------------------
# Home
# -------------------------
@app.route("/")
def home():
    return "API is Alive (jwt_token fixed)", 200


# -------------------------
# Like API
# -------------------------
@app.route("/like", methods=["GET"])
def like_api():
    uid = request.args.get("uid")
    region = request.args.get("region", "").upper()

    if not uid or region not in REGION_CONFIG:
        return jsonify({
            "error": "uid and valid region (IND, NX, AG) required"
        }), 400

    try:
        config = REGION_CONFIG[region]
        tokens_collection = db[config["tokens"]]

        # 🔥 FIX: jwt_token read
        token_docs = list(
            tokens_collection.find({}, {"_id": 0, "jwt_token": 1})
        )

        if not token_docs:
            return jsonify({
                "error": f"No tokens found in {config['tokens']}"
            }), 500

        # use first token
        token = token_docs[0]["jwt_token"]

        encrypted_uid = enc(uid)

        # -------------------------
        # BEFORE likes
        # -------------------------
        before = make_request(encrypted_uid, region, token)
        if before is None:
            raise Exception("Failed to fetch player info (before)")

        before_data = json.loads(MessageToJson(before))
        before_likes = int(
            before_data.get("AccountInfo", {}).get("Likes", 0)
        )
        player_region = str(
            before_data.get("AccountInfo", {}).get("region", "")
        )

        # -------------------------
        # SEND LIKE REQUESTS
        # -------------------------
        asyncio.run(
            send_multiple_requests(
                uid,
                region,
                config["url"],
                token_docs
            )
        )

        # -------------------------
        # AFTER likes
        # -------------------------
        after = make_request(encrypted_uid, region, token)
        if after is None:
            raise Exception("Failed to fetch player info (after)")

        after_data = json.loads(MessageToJson(after))

        player_uid = int(
            after_data.get("AccountInfo", {}).get("UID", 0)
        )
        player_name = str(
            after_data.get("AccountInfo", {}).get("PlayerNickname", "")
        )
        after_likes = int(
            after_data.get("AccountInfo", {}).get("Likes", 0)
        )

        added = after_likes - before_likes
        status = 1 if added > 0 else 2

        # -------------------------
        # Success counter
        # -------------------------
        if status == 1:
            state_collection.update_one(
                {"region": config["state"]},
                {"$inc": {"success_count": 1}},
                upsert=True
            )

        state_doc = state_collection.find_one(
            {"region": config["state"]},
            {"success_count": 1}
        )

        success_count = state_doc.get("success_count", 0) if state_doc else 0

        # -------------------------
        # Response
        # -------------------------
        response = {
            "status": status,
            "message": "Like successful" if status == 1 else "No likes added",
            "player": {
                "uid": player_uid,
                "nickname": player_name,
                "region": player_region
            },
            "likes": {
                "before": before_likes,
                "after": after_likes,
                "added_by_api": added
            },
            "success_count": success_count,
            "token_collection_used": config["tokens"]
        }

        return Response(
            json.dumps(response, indent=2),
            mimetype="application/json"
        )

    except Exception as e:
        app.logger.error(f"Error: {e}")
        return jsonify({"error": str(e)}), 500


# -------------------------
# Run server
# -------------------------
if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True,
        use_reloader=False
    )
