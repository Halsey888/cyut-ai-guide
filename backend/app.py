from flask import Flask, render_template, request, jsonify
import io,os
import json
from google import genai
from google.genai.types import GenerateContentConfig, Tool, GoogleSearchRetrieval
from flask_cors import CORS
from google.genai import types 
import re #re (正規表示式) 函式庫
import PIL.Image
from PIL import ImageDraw
import base64

# --- 校園建築資料庫 (保留你的資料) ---
CYUT_BUILDINGS = {
    "波錠紀念圖書館 (L)": {
        "prefix": "L",
        "address": "413 臺中市霧峰區吉峰東路 168 號",
        "position": "校園中心高處，位於行政大樓後方，面人文科技大樓左手邊，需經過中央階梯，或經右側斜坡。",
        "hours": "週一至週五 08:30 – 22:00；週六日 09:00 - 17:00",
        "phone": "+886 4 2332 3000 #3152",
        "google_maps": "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d1083.0476628161232!2d120.71355330170678!3d24.068995230036887!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x346924aa9545dca7%3A0x2458bb010ff472cb!2z5pyd6Zm956eR5oqA5aSn5a245rOi6Yyg57SA5b-15ZyW5pu46aSo!5e0!3m2!1szh-TW!2stw!4v1774193396640!5m2!1szh-TW!2stw",
        "lat": 24.06920, "lng": 120.71351
    },
    "行政大樓 (A)": {
        "prefix": "A",
        "address": "413 臺中市霧峰區吉峰東路 168 號",
        "position": "校門口進入後正前方第一棟建築，為校園核心行政中心。",
        "hours": "週一至週五 08:00 – 17:00",
        "phone": "+886 4 2332 3000",
        "google_maps": "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d455.3644254504628!2d120.71492274978807!3d24.069283442314987!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x346925004aee95bb%3A0x95f0b8304a044f67!2z5pyd6Zm956eR5oqA5aSn5a246KGM5pS_5aSn5qiT!5e0!3m2!1szh-TW!2stw!4v1774193482904!5m2!1szh-TW!2stw",
        "lat": 24.06955, "lng": 120.71470
    },
    "教學大樓 (T1)": {
        "prefix": "T1",
        "address": "413 臺中市霧峰區吉峰東路 168 號",
        "position": "校園內最核心的教學建築之一，位於校園中心地帶，校門口進入後左後方區域，位於宿舍大樓(門口對面)。教學大樓（T1）主要承載全校性的基礎教學任務與行政功能。它是學生進校後最常接觸的建築之一，許多通識課程、語文課程以及基礎學科的教學都在此進行。",
        "hours": "週一至週五 08:00 – 17:00",
        "phone": "+886 4 2332 3000",
        "google_maps": "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d382.91776975242294!2d120.71462210596603!3d24.06812545241694!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x346924aafa0541c1%3A0xb94b7a8c86f4d076!2z5pyd6Zm956eR5oqA5aSn5a245pWZ5a245aSn5qiT!5e0!3m2!1szh-TW!2stw!4v1777833930667!5m2!1szh-TW!2stw",
        "lat": 24.068189807804448, "lng": 120.71447888426512
    },
    "管理大樓 (T2)": {
        "prefix": "T2",
        "address": "413 臺中市霧峰區吉峰東路 168 號",
        "position": "位於校園右側區域（面對圖書館方向的左手邊），管理學院系所所在地。",
        "hours": "週一至週五 08:00 – 22:00 (依課程時間調整)",
        "phone": "+886 4 2332 3000 #7042",
        "google_maps": "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d1083.0482529789376!2d120.71323433150233!3d24.06892533305578!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x346925001444d2bd%3A0x648d75acd0dee299!2z5pyd6Zm956eR5oqA5aSn5a24566h55CG5aSn5qiT!5e0!3m2!1szh-TW!2stw!4v1774193208605!5m2!1szh-TW!2stw",
        "lat": 24.068775794690765, "lng": 120.71284041807773
    },
    "設計大樓 (D)": {
        "prefix": "D",
        "address": "413 臺中市霧峰區吉峰東路 168 號",
        "position": "位於校園右後側區域，正對管理大樓，入口於轉角處，包含建築、視覺傳達、工業設計等系所。",
        "hours": "週一至週五 08:00 – 22:00",
        "phone": "+886 4 2332 3000 #7502",
        "google_maps": "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d643.9870943383575!2d120.71324414633385!3d24.06837753046217!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x346925001e5a025f%3A0xe37bccfd24fba5bd!2z5pyd6Zm956eR5oqA5aSn5a246Kit6KiI5aSn5qiT!5e0!3m2!1szh-TW!2stw!4v1774193556261!5m2!1szh-TW!2stw",
        "lat": 24.06847145079084, "lng": 120.71360833879143
    },
    "理工大樓 (E)": {
        "prefix": "E",
        "address": "413 臺中市霧峰區吉峰東路 168 號",
        "position": "位於(面)行政大樓後方偏左側，在墊腳石書局左手邊。",
        "hours": "週一至週五 08:00 – 22:00",
        "phone": "+886 4 2332 3000 #7102",
        "google_maps": "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d643.9845226277881!2d120.7147160893158!3d24.068889786052182!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x346924aaeb7caa2b%3A0x88f84347fa4ac6fc!2z55CG5bel5a246Zmi!5e0!3m2!1szh-TW!2stw!4v1774193594189!5m2!1szh-TW!2stw",
        "lat": 24.069162046339333, "lng": 120.71535344818548
    },
    "資訊大樓 (M)": {
        "prefix": "M",
        "address": "413 臺中市霧峰區吉峰東路 168 號",
        "position": "位經行政大樓後右手邊，主要提供資訊學院教學與研究使用。",
        "hours": "週一至週五 08:00 – 22:00",
        "phone": "+886 4 2332 3000 #7162",
        "google_maps": "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d643.9815174752947!2d120.71402835593032!3d24.069488365368716!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x346924aaec2629c1%3A0x7cf113a6212a076!2z5pyd6Zm956eR5oqA5aSn5a24IOizh-ioiuiIh-mAmuioiuezuw!5e0!3m2!1szh-TW!2stw!4v1774193635149!5m2!1szh-TW!2stw",
        "lat": 24.069362186678536, "lng": 120.71409612205515
    },
    "人文與科技大樓 (G)": {
        "prefix": "G",
        "address": "413 臺中市霧峰區吉峰東路 168 號",
        "position": "位於校園右側，正對資訊大樓背面。",
        "hours": "週一至週五 08:00 – 22:00",
        "phone": "+886 4 2332 3000 #7242",
        "google_maps": "https://www.google.com/maps/embed?pb=!1m17!1m12!1m3!1d541.5205664132765!2d120.71362477109017!3d24.069768608207948!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m2!1m1!2zMjTCsDA0JzExLjMiTiAxMjDCsDQyJzQ5LjYiRQ!5e0!3m2!1szh-TW!2stw!4v1781244158990!5m2!1szh-TW!2stw",
        "lat": 24.0698137456664, "lng": 120.71378041308218
    },
    "航空大樓 (V)": {
        "prefix": "V",
        "address": "413 臺中市霧峰區吉峰東路 168 號",
        "position": "位於校園左側最末端，為近年新建大樓，包含飛航設備與模擬教室。",
        "hours": "週一至週五 08:00 – 17:00",
        "phone": "+886 4 2332 3000 #7902",
        "google_maps": "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d643.9906148981759!2d120.71435979708734!3d24.06767625823226!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x3469250014466033%3A0x9400e8fd701e6189!2z6Iiq56m65a246Zmi!5e0!3m2!1szh-TW!2stw!4v1774193735637!5m2!1szh-TW!2stw",
        "lat": 24.06736, "lng": 120.71471
    },
    "體育體育館 (S)": {
        "prefix": "S",
        "address": "413 臺中市霧峰區吉峰東路 168 號",
        "position": "位於校園左側，包含室內球場與健身中心。",
        "hours": "週一至週五 08:00 – 21:30 (假日依借用情況開放)",
        "phone": "+886 4 2332 3000 #7602",
        "google_maps": "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d643.986094178044!2d120.71490602025312!3d24.068576752276236!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x3469259198c6bb8d%3A0x7d5fac4f8428bae!2z5pyd6Zm956eR5oqA5aSn5a246auU6IKy6aSo!5e0!3m2!1szh-TW!2stw!4v1774193780310!5m2!1szh-TW!2stw",
        "lat": 24.0687316722084, "lng": 120.71540088449112
    },
    "第一餐廳 (一餐 R-113)": {
        "prefix": "R",
        "address": "413 臺中市霧峰區吉峰東路 168 號",
        "position": "位於宿舍大樓 (R 棟) 地下室，改名為「朝陽新天地」，提供自助餐、麵食與早午餐。",
        "hours": "週一至週五 06:30 – 19:30；週六日 08:00 – 13:00 (依學期調整)",
        "phone": "+886 4 2332 3000 #6065",
        "google_maps": "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d270.76518105967716!2d120.71406696346978!3d24.06744823261118!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x3469250069bf2701%3A0x6bcc0d676d2d6a46!2z56ys5LiA6aSQ5buz!5e0!3m2!1szh-TW!2stw!4v1778682581973!5m2!1szh-TW!2stw",
        "lat": 24.067422384983285, "lng": 120.71424478935177
    },
    "第二餐廳 (二餐)": {
        "prefix": "R",
        "address": "413 臺中市霧峰區吉峰東路 168 號",
        "position": "同樣位於宿舍大樓 (R 棟) 區域，鄰近第一餐廳，設有連鎖餐飲與小吃櫃位。",
        "hours": "週一至週五 11:00 – 20:00 (依店家而定)",
        "phone": "+886 4 2332 3000 #6065",
        "google_maps": "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d270.7649612955404!2d120.71363715111927!3d24.067552351174374!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x34692500148b5447%3A0xbf8e7645d42b2e2e!2z56ys5LqM6aSQ5buz!5e0!3m2!1szh-TW!2stw!4v1778682705997!5m2!1szh-TW!2stw",
        "lat": 24.06761751624477, "lng": 120.71383491263828
    },
    "第三餐廳 (三餐 T2-B107)": {
        "prefix": "T2",
        "address": "413 臺中市霧峰區吉峰東路 168 號",
        "position": "位於管理大樓 (T2) 地下室區域，主要服務管理學院師生，環境較為清幽。",
        "hours": "週一至週五 08:00 – 18:00",
        "phone": "+886 4 2332 3000 #7042",
        "google_maps": "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d227.68308127220018!2d120.71302080859941!3d24.06879411884797!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x34692500196861b5%3A0xd5353f7087be0c0e!2z56ys5LiJ6aSQ5buz!5e0!3m2!1szh-TW!2stw!4v1778682804541!5m2!1szh-TW!2stw",
        "lat": 24.06887585446926, "lng": 120.71302751412168
    },
    "宿舍大樓 (R 棟)": {
        "prefix": "R",
        "address": "413 臺中市霧峰區吉峰東路 168 號",
        "position": "第一學生宿舍。位於校園後方最高點，內含 7-11 超商、自動櫃員機及一、二餐廳。",
        "hours": "24 小時 (進出需門禁刷卡)；服務台 08:00 – 22:00",
        "phone": "+886 4 2332 3000 #1122",
        "google_maps": "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d321.995574003517!2d120.713871236248!3d24.06757006479852!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x34692500126d63ed%3A0xf4780819f51bb5df!2z5pyd6Zm956eR5oqA5aSn5a2456ys5LiA5a6_6IiN!5e0!3m2!1szh-TW!2stw!4v1778682903006!5m2!1szh-TW!2stw",
        "lat": 24.06763976678332, "lng": 120.71379916513987
    }
}

# --- 直接從 embed URL 解析經緯度 ---
def get_coords_from_embed_url(url: str):
    """
    直接從 Google Maps 的 embed URL 中解析出經緯度。
    範例: ...!2d120.7135533...!3d24.0689952...
    """
    if not url:
        return None

    # 匹配 !3d 後面的緯度 (latitude)
    lat_match = re.search(r'!3d(-?\d+\.\d+)', url)
    # 匹配 !2d 後面的經度 (longitude)
    lng_match = re.search(r'!2d(-?\d+\.\d+)', url)

    if lat_match and lng_match:
        try:
            lat = float(lat_match.group(1))
            lng = float(lng_match.group(1))
            return {"lat": lat, "lng": lng}
        except ValueError:
            return None

    return None

app = Flask(__name__)
CORS(app)

# --- AI 客戶端初始化 ---

gemini_client = genai.Client()
GEMINI_MODEL = 'gemini-3.5-flash' 
# 新增快取字典於檔案頂端
_IMAGE_CACHE = {}


# --- 核心 AI 邏輯重構為兩步驟流程 ---
def get_ai_core_response(user_text, target_lang_code):
    """
    採用兩步驟流程解決 API 限制：
    1. 意圖識別：判斷使用者是否在詢問特定建築。 (使用 JSON 模式，不使用 Tool)
    2. 答案生成：根據步驟 1 的結果，選擇性地使用本地資料或 Google Search Tool 生成答案。
    """
    final_coords = None
    answer_text = "抱歉，我現在有點問題，請稍後再試。" # 預設錯誤訊息
    found_image_base64 = None # 用來儲存要傳給前端的圖片 Base64

    # --- 步驟一：意圖識別 (JSON 模式, 無 Tool) ---
    building_names = list(CYUT_BUILDINGS.keys())


    # 抽出所有建築的 prefix 提示，讓 AI 變聰明
    prefix_hints = ", ".join([f"{v.get('prefix')}代表{k}" for k, v in CYUT_BUILDINGS.items() if v.get('prefix')])

    search_tool = types.Tool(google_search=types.GoogleSearch())
    SYSTEM_INSTRUCTION = f"""
    你的任務是分析使用者問題，判斷他們是否在詢問特定建築物或教室。
    你的回答必須是 JSON 格式，包含兩個鍵：
    1. "target_building": 建築物全名 (若無則為 null)。
    2. "target_floor": 樓層號碼 (純數字字串，若無則為 null)。請從教室代號判斷樓層，通常第一或前兩位數字代表樓層。
    3. "target_room": 教室完整號碼 (例如 "607", "304"，若無則為 null)。
    
    【建築物清單】:
    {json.dumps(building_names, ensure_ascii=False)}

    【教室代號提示】:
    如果使用者詢問特定教室代號，請對應到所屬大樓。例如：{prefix_hints}

    【範例】
    使用者: "管理大樓 T2 在哪？" -> {{"target_building": "管理大樓 (T2)", "target_floor": null}}
    使用者: "我要去 G304 教室" -> {{"target_building": "人文與科技大樓 (G)", "target_floor": "3"}}
    使用者: "T2501 怎麼走" -> {{"target_building": "管理大樓 (T2)", "target_floor": "5"}}
    使用者: "圖書館二樓有什麼" -> {{"target_building": "波錠紀念圖書館 (L)", "target_floor": "2"}}
    使用者: "一餐有什麼好吃的" -> {{"target_building": "第一餐廳 (一餐 R-113)", "target_floor": null, "target_room": null}}
    使用者: "我要去三餐" -> {{"target_building": "第三餐廳 (三餐 T2-B107)", "target_floor": null, "target_room": null}}
    使用者: "學校附近有什麼好吃的？" -> {{"target_building": null, "target_floor": null}}
    """

    target_building_name = None
    target_floor = None # 儲存樓層變數
    target_room = None

    config=GenerateContentConfig(
        system_instruction=SYSTEM_INSTRUCTION,
        response_mime_type= 'application/json',
        temperature=0.1
    )
    try:
        # 將 generation_config 和 system_instruction 作為頂層參數傳遞
        intent_response = gemini_client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[f"使用者問題：'{user_text}'"],
            config=config
        )
        intent_data = json.loads(intent_response.text)
        target_building_name = intent_data.get("target_building")

        # 抓取樓層號碼
        target_floor = intent_data.get("target_floor")
        target_room = intent_data.get("target_room")

        # 只要判斷是餐廳，就直接寫死樓層與目標名稱，略過 AI 的猜測
        if target_building_name == "第一餐廳 (一餐 R-113)":
            target_floor = "1"
            target_room = "第一餐廳(或一餐)"  # 讓第二階段的 AI 去圖上找這個關鍵字
        elif target_building_name == "第二餐廳 (二餐)":
            target_floor = "1"
            target_room = "第二餐廳(或二餐)"
        elif target_building_name == "第三餐廳 (三餐 T2-B107)":
            target_floor = "B1"  # 配合你的圖片命名 T2-B1.jpg
            target_room = "第三餐廳(或三餐)"

        # 看到 AI 有沒有抓對樓層
        print(f"步驟一 (意圖識別) 結果: 建築={target_building_name}, 樓層={target_floor}, 教室={target_room}")
    except Exception as e:
        print(f"步驟一 (意圖識別) 失敗: {e}")
        target_building_name = None

    # --- 步驟二：答案生成 ---

    # 情況 A: 識別出特定建築，使用本地資料庫生成答案
    if target_building_name and target_building_name in CYUT_BUILDINGS:
        building_info = CYUT_BUILDINGS[target_building_name]
        building_prefix = building_info.get("prefix") # 取得代號，例如 'G'

        # === 優化: 若無需定位教室，直接從資料庫回答 ===
        if not target_room:
            info = building_info
            answer_text = f"【{target_building_name}】\n"
            answer_text += f"地址：{info.get('address', '')}\n"
            answer_text += f"位置：{info.get('position', '')}\n"
            answer_text += f"開放時間：{info.get('hours', '')}\n"
            answer_text += f"電話：{info.get('phone', '')}"
            embed_url = info.get('google_maps')
            final_coords = get_coords_from_embed_url(embed_url)
            return answer_text, final_coords, None

        ANSWER_FROM_DATA_INSTRUCTION = f"""
        你是一位熱情的「朝陽科技大學」導覽員。
        請根據使用者問題和下方提供的【建築物詳細資料】（若有提供圖片，請一併參考平面圖），生成一個自然且有幫助的回答。
        如果使用者詢問特定教室，請根據提供的平面圖詳細說明它在幾樓、靠近哪個方位（例如：電梯出樓梯左轉等）。
        請用 '{target_lang_code}' 語言回答。

        重要指示：
        如果使用者有詢問特定教室 (例如 {target_room})，請你在平面圖上尋找該教室的位置。
        如果找到了，請在你的回答最後一行，嚴格以這個格式輸出該教室的邊界框座標：
        COORDS: [ymin, xmin, ymax, xmax]
        (座標數值範圍為 0 到 1000)。如果找不到就不要輸出 COORDS。

        【建築物詳細資料】:
        {json.dumps(building_info, ensure_ascii=False, indent=2)}
        """

        # 準備傳遞給 Gemini 的內容陣列
        contents_to_send = [
            f"使用者問題: '{user_text}'",
            "請根據你擁有的資料（包含文字與平面圖）來詳細回答這個問題。"
        ]

        img = None

        # 動態組合檔案路徑並讀取圖片
        if building_prefix and target_floor:
            # 設定支援的副檔名，以防圖片格式不同
            valid_extensions = ['.jpg', '.png', '.jpeg']
            image_found = False

            for ext in valid_extensions:
                # 組合路徑，例如：floor_plan_image/G-3.jpg
                dynamic_image_path = os.path.join("floor_plan_image", f"{building_prefix}-{target_floor}{ext}")

                if os.path.exists(dynamic_image_path):
                    try:
                        img = PIL.Image.open(dynamic_image_path)
                        contents_to_send.insert(0, img)  
                        print(f"已成功載入動態平面圖: {dynamic_image_path}")
                        # 把這張圖片轉成 Base64 字串，準備回傳給前端
                        # === 優化: 快取原始 Base64 ===
                        if dynamic_image_path not in _IMAGE_CACHE:
                            with open(dynamic_image_path, "rb") as image_file:
                                _IMAGE_CACHE[dynamic_image_path] = base64.b64encode(image_file.read()).decode('utf-8')
                        found_image_base64 = _IMAGE_CACHE[dynamic_image_path]

                        image_found = True
                        break 
                    except Exception as e:
                        print(f"讀取平面圖失敗 {dynamic_image_path}: {e}")

            if not image_found:
                print(f"找不到對應的樓層平面圖，預期檔名格式類似: {building_prefix}-{target_floor}.jpg")

        try:
            answer_response = gemini_client.models.generate_content(
                model=GEMINI_MODEL,
                contents=contents_to_send, # 這裡包含了文字與圖片(如果有的話)
                config=GenerateContentConfig(
                    system_instruction=ANSWER_FROM_DATA_INSTRUCTION
                )
            )
            raw_answer_text = answer_response.text

            #  解析 Gemini 回傳的座標，並在圖片上畫紅框
            answer_text = raw_answer_text
            if img:
                # 尋找是否包含 COORDS: [ymin, xmin, ymax, xmax]
                # # 從 Gemini 回覆中正則匹配 COORDS: [ymin, xmin, ymax, xmax]
                match = re.search(r'COORDS:\s*\[\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\]', raw_answer_text)
                if match:
                    ymin, xmin, ymax, xmax = map(int, match.groups())
                    width, height = img.size

                    # Gemini 的座標是 0-1000 的千分比，需轉換成實際像素
                    left = (xmin / 1000) * width
                    top = (ymin / 1000) * height
                    right = (xmax / 1000) * width
                    bottom = (ymax / 1000) * height

                    # 在圖片上畫一個明顯的紅色方框，線條粗細為 5
                    draw = ImageDraw.Draw(img)
                    draw.rectangle([left, top, right, bottom], outline="red", width=5)
                    print(f"已在圖片上標註位置: {target_room}")
                    print(f"COORDS: [ {left}, {top}, {right}, {bottom}]")

                    answer_text = re.sub(r'COORDS:\s*\[.*?\]', '', raw_answer_text).strip()

                # 將處理過的圖片 (有畫框或沒畫框) 轉成 Base64
                # === 優化: 降低儲存品質 ===
                    buffered = io.BytesIO()
                    img.save(buffered, format="JPEG", quality=60)
                    found_image_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
                    answer_text = re.sub(r'COORDS:\s*\[.*?\]', '', raw_answer_text).strip()
                else:
                    # 沒畫框，仍要回傳原圖
                    buffered = io.BytesIO()
                    img.save(buffered, format="JPEG", quality=60)
                    found_image_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')

            # 既然已確定建築物，就解析座標
            embed_url = building_info.get('google_maps')
            final_coords = get_coords_from_embed_url(embed_url)
            if final_coords:
                print(f"座標解析成功: {final_coords}")
            else:
                print(f"座標解析失敗，URL: {embed_url}")

        except Exception as e:
            print(f"步驟二 (從資料生成答案) 失敗: {e}")
            answer_text = "處理您的請求時發生錯誤。"

    # 情況 B: 未識別出特定建築，使用 Google Search 進行通用問答
    else:
        print("進入通用問答流程 (使用 Google Search)")
        search_tool = types.Tool(google_search=types.GoogleSearch())

        GENERAL_ANSWER_INSTRUCTION = f"""
        你是一位熱情的「朝陽科技大學」導覽員。
        盡力回答使用者的問題。如果問題與朝陽科大無關，也可以嘗試回答。
        如果不知道答案，請誠實地說不知道。
        請用 '{target_lang_code}' 語言回答。
        """
        config2=GenerateContentConfig(
            tools=[search_tool],
            system_instruction=GENERAL_ANSWER_INSTRUCTION
        )
        try:
            answer_response = gemini_client.models.generate_content(
                model=GEMINI_MODEL,
                contents=f"使用者問題: '{user_text}'",
                config=config2
            )
            answer_text = answer_response.text
        except Exception as e:
            print(f"步驟二 (通用問答) 失敗: {e}")
            answer_text = "抱歉，我無法搜尋相關資訊。"

    return answer_text, final_coords, found_image_base64
# --- Flask 路由 ---

# --- 路由 1：處理語音 ---
@app.route('/ask_guide', methods=['POST'])
def ask_guide():
    if 'audio' not in request.files:
        return jsonify({"status": "error", "message": "未接收到音訊"}), 400
    
    audio_file = request.files['audio']
    audio_data = audio_file.read()
    user_lang_code = request.form.get('lang_code', 'zh-TW')
    mime_type = audio_file.content_type or 'audio/m4a'

    try:
        # 第一步：音訊轉文字 (避免與 Search Tool 並存錯誤)
        audio_part = types.Part.from_bytes(data=audio_data, mime_type=mime_type)
        stt_response = gemini_client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[audio_part, "請將這段語音轉成簡短的文字指令。"],
        )
        user_text = stt_response.text
        
        # 第二步：呼叫核心思考邏輯
        final_text, final_coords, image_b64 = get_ai_core_response(user_text, user_lang_code)
        
        return jsonify({
            "status": "success",
            "answer_text": final_text,
            "coordinates": final_coords,
            "image_base64": image_b64 # 塞入 JSON 回傳
        })
    except Exception as e:
        print(f"語音處理錯誤: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# --- 路由 2：處理文字 (修正後) ---
@app.route('/ask_text', methods=['POST'])
def ask_text():
    # 這裡建議使用 get_json()
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "JSON 格式錯誤"}), 400
        
    user_text = data.get('text', '')
    user_lang_code = data.get('lang_code', 'zh-TW')

    try:
        # 直接跳到核心思考邏輯，不用再轉音訊
        final_text, final_coords, image_b64 = get_ai_core_response(user_text, user_lang_code)
        return jsonify({
            "status": "success", 
            "answer_text": final_text, 
            "coordinates": final_coords,
            "image_base64": image_b64 # 塞入 JSON 回傳
        })
    except Exception as e:
        print(f"文字處理錯誤: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)