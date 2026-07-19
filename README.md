# 朝陽 AI 校園導覽員 (CYUT AI Guide)

> 畢業專題：整合語音辨識、地圖定位、生成式 AI 的校園導覽 App

![](https://img.shields.io/badge/React_Native-20232A?style=for-the-badge&logo=react)
![](https://img.shields.io/badge/Expo-000020?style=for-the-badge&logo=expo)
![](https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask)
![](https://img.shields.io/badge/Google_Gemini-4285F4?style=for-the-badge&logo=google)

## 功能亮點
- **語音問答**：按住說話，AI 即時回覆校園資訊
- **文字輸入**：鍵盤輸入也能通
- **地圖連動**：問到建築物時，自動在地圖上標示位置並運鏡
- **圖片輔助**：AI 可回傳樓層平面圖或示意圖，支援縮放拖曳
- **多語系**：繁體中文、英文、日文即時切換
- **資料庫整合**：內建完整朝陽科大建築資訊（座標、電話、開放時間、位置描述）

## 技術架構

[手機 App] ←→ [Flask API] ←→ [Google Gemini + Search Grounding] ↑ ↑ (expo-av) (校園建築 JSON 資料庫)

- 前端：React Native + Expo (expo-av, react-native-maps, react-native-reanimated)
- 後端：Python Flask，透過 ngrok 建立公網端點
- AI 核心：Google Gemini (`gemini-3.5-flash`) + Google Search Retrieval 以確保回答正確性
- 地圖：Google Maps 嵌入，動態 Marker 與動畫平移

## 如何在本機執行
一、專題功能簡述

本系統為一款智慧校園導覽行動App，結合生成式AI與平面圖辨識技術，提供以下核心功能：

1. 語音 / 文字雙輸入查詢
   - 使用者可長按錄音按鈕以語音提問，或直接輸入文字。
   - 支援繁體中文、英文、日文三種語言，隨時切換介面語言與回答語言。

2. 智慧意圖解析
   - AI 自動從使用者問題中辨識出目標建築物、樓層與教室代號。
   - 例：「我要去 G304」→ 人文與科技大樓 3 樓 304 教室。

3. 平面圖實時辨識與標記
   - 系統動態載入該建築該樓層的平面圖，由 Gemini 多模態模型「看圖」尋找教室。
   - 自動在圖上以紅色方框標示教室位置，使用者可雙指縮放、拖曳查看細節。

4. Google Maps 整合
   - 查詢建築時，自動顯示地圖定位，並提供詳細資訊（地址、開放時間、電話、位置描述）。

5. 跨平台 App
   - 使用 React Native (Expo) 開發，可同時運行於 Android 與 iOS 裝置。

二、安裝程式說明

--- 後端 (Flask Server) ---

前置需求：
  Python 3.10+ 環境，建議使用虛擬環境 (venv 或 conda)

步驟：
1. 安裝相依套件
   pip install google-genai flask flask-cors Pillow

   ※ 若專案內有 requirements.txt，可執行：
   pip install -r requirements.txt

2. 設定 Gemini API Key
   於執行環境設定環境變數：
   - Windows (cmd)：set GOOGLE_API_KEY=你的金鑰
   - macOS/Linux：export GOOGLE_API_KEY="你的金鑰"
   金鑰申請網址：https://aistudio.google.com/apikey

3. 確保平面圖資料夾存在
   將所有校園平面圖放置於與 app.py 同目錄下的 floor_plan_image/ 資料夾中。
   平面圖檔名規則：{建築代號}-{樓層}.jpg (如 G-3.jpg、M-B1.JPG)
   ※ 支援副檔名 .jpg / .jpeg / .png

4. 啟動後端伺服器
   python app.py
   伺服器將運行於 http://0.0.0.0:5000

--- 前端 (React Native App) ---

前置需求：
  Node.js (建議 18 LTS 以上)
  Expo CLI 環境 (或使用 npx expo)
  手機安裝 Expo Go App (或建立 native build)

步驟：
1. 切換至前端專案目錄
   本專案提供兩個版本，請擇一使用：
   - 基礎版：主要程式/
   - 手勢縮放版 (建議)：cyut_app/

   以下以 cyut_app/ 為例。

2. 安裝相依套件
   cd cyut_app
   npm install

3. 修改後端 API 位址
   編輯 App.js，找到：
   const API_URL = 'YOUR_BACKEND_URL/ask_guide';
   將其中的 ngrok 網址更換為你的後端實際位址（若後端在本機，需使用 ngrok 網址或同網路下的
   本機 IP，例如 http://192.168.x.x:5000）。
   ※ 注意：使用 http 協定時，Android 需在 AndroidManifest.xml 中設定 usesCleartextTraffic="true"
      (本專案已預設開啟)。

4. 啟動 Expo 開發伺服器
   npx expo start
   終端機將顯示 QR Code，使用手機 Expo Go 掃描即可運行。

5. (選用) 建立獨立 APK
   可執行以下指令建立 Android APK：
   npx eas build -p android --profile preview
   或使用本地指令：
   npx expo run:android

## 畫面截圖
<img width="339" height="753" alt="image" src="https://github.com/user-attachments/assets/90db6bb2-c1e2-47d6-8fd5-8b756b734035" />
<img width="339" height="753" alt="image" src="https://github.com/user-attachments/assets/3fe49383-8b73-4667-babd-337065ec79a7" />
<img width="700" height="500" alt="image" src="https://github.com/user-attachments/assets/05edb28b-6eb5-4f5c-9645-24c1e330768b" />


## 專案結構

├── frontend-expo-router/ # 新版 Expo Router 前端\n
├── backend/ # Flask API + 建築資料庫\n
├── android/ # Android 原生設定 (需填入 API key) ，於android\app\src\main\AndroidManifest.xml 中設定自己的gemini_API<meta-data android:name="com.google.android.geo.API_KEY" android:value="YOUR_GOOGLE_MAPS_API_KEY"/>\n
└── README.md

## 注意事項
- 本專案未包含 Google Maps API Key 及 Gemini API Key，請自行申請並填入對應位置
- 後端網址因 ngrok 會變動，請在 `App.js` 中修改 `API_URL`

## 授權
本專案僅供學術展示，未開放商業用途。
