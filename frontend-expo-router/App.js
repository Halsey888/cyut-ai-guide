import React, { useState, useRef } from 'react';
import { StyleSheet, Text, View, TouchableOpacity, FlatList, ActivityIndicator, Alert, SafeAreaView, TextInput, KeyboardAvoidingView, Platform, Image, Modal } from 'react-native';
import { Audio } from 'expo-av';
import { Picker } from '@react-native-picker/picker';
import MapView, { Marker } from 'react-native-maps';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { Gesture, GestureDetector } from 'react-native-gesture-handler';
import Animated, { useSharedValue, useAnimatedStyle } from 'react-native-reanimated';

const API_URL = 'YOUR_BACKEND_URL/ask_guide';

const ZoomableImage = ({ source }) => {
  const scale = useSharedValue(1);
  const savedScale = useSharedValue(1);

  const translateX = useSharedValue(0);
  const translateY = useSharedValue(0);
  const savedTranslateX = useSharedValue(0);
  const savedTranslateY = useSharedValue(0);

  const pinchGesture = Gesture.Pinch()
    .onUpdate((e) => {
      scale.value = savedScale.value * e.scale;
    })
    .onEnd(() => {
      savedScale.value = scale.value;
    });

  const panGesture = Gesture.Pan()
    .minPointers(1)
    .maxPointers(1)
    .onUpdate((e) => {
      translateX.value = savedTranslateX.value + e.translationX;
      translateY.value = savedTranslateY.value + e.translationY;
    })
    .onEnd(() => {
      savedTranslateX.value = translateX.value;
      savedTranslateY.value = translateY.value;
    });

  const composedGesture = Gesture.Simultaneous(panGesture, pinchGesture);

  const animatedStyle = useAnimatedStyle(() => ({
    transform: [
      { translateX: translateX.value },
      { translateY: translateY.value },
      { scale: scale.value },
    ],
  }));

  return (
    <GestureDetector gesture={composedGesture}>
      <Animated.View style={{ flex: 1, alignItems: 'center', justifyContent: 'center' }}>
        <Animated.Image
          source={source}
          style={[{ width: '100%', height: '100%' }, animatedStyle]}
          resizeMode="contain"
        />
      </Animated.View>
    </GestureDetector>
  );
};

export default function App() {
  const [inputText, setInputText] = useState(''); // 輸入框狀態
  const [recording, setRecording] = useState();
  const [isProcessing, setIsProcessing] = useState(false);
  const [messages, setMessages] = useState([
    { id: '1', text: '您好！我是朝陽科大 AI 導覽員，請問有什麼我可以幫您的？', sender: 'ai' }
  ]);
  const [langCode, setLangCode] = useState('zh-TW');

  const [modalVisible, setModalVisible] = useState(false);
  const [selectedImageUri, setSelectedImageUri] = useState(null);

  const handleImagePress = (base64) => {
    setSelectedImageUri(`data:image/jpeg;base64,${base64}`);
    setModalVisible(true);
  };

  // --- 地圖相關 State ---
  const mapRef = useRef(null);
  const [targetMarker, setTargetMarker] = useState(null);
  const [showMap, setShowMap] = useState(false); // 控制地圖顯示/隱藏

  // --- 傳送純文字功能 ---
  async function sendTextMessage() {
    if (!inputText.trim()) return;

    const userMsgId = Date.now().toString();
    const currentText = inputText;
    setMessages(prev => [...prev, { id: userMsgId, text: currentText, sender: 'user' }]);
    setInputText(''); // 清空輸入框
    setIsProcessing(true);

    try {
      const response = await fetch(`${API_URL.replace('ask_guide', 'ask_text')}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: currentText, lang_code: langCode }),
      });
      const data = await response.json();
      handleAIResponse(data);
    } catch (error) {
      Alert.alert('連線失敗', '無法傳送文字訊息');
    } finally {
      setIsProcessing(false);
    }
  }

  // --- 抽離處理回傳資料的邏輯 ---
  function handleAIResponse(data) {
    if (data.status === 'success') {
      setMessages(prev => [...prev, { 
        id: Date.now().toString(), 
        text: data.answer_text, 
        sender: 'ai',
        imageBase64: data.image_base64 || null // 存入圖片資料
      }]);

      if (data.coordinates && data.coordinates.lat) {
        const newPoint = { latitude: data.coordinates.lat, longitude: data.coordinates.lng };
        setTargetMarker(newPoint);
        setShowMap(true);
        setTimeout(() => {
          mapRef.current?.animateToRegion({ ...newPoint, latitudeDelta: 0.003, longitudeDelta: 0.003 }, 1000);
        }, 500);
      }
    }
  }

  // --- 錄音功能 ---
  async function startRecording() {
    try {
      const permission = await Audio.requestPermissionsAsync();
      if (permission.status !== 'granted') {
        Alert.alert('權限不足', '請允許麥克風權限以使用導覽功能');
        return;
      }
      await Audio.setAudioModeAsync({ allowsRecordingIOS: true, playsInSilentModeIOS: true });
      const { recording } = await Audio.Recording.createAsync(Audio.RecordingOptionsPresets.HIGH_QUALITY);
      setRecording(recording);
    } catch (err) {
      Alert.alert('失敗', '無法啟動錄音');
    }
  }

  async function stopAndSend() {
    if (!recording) return;
    setRecording(undefined);
    await recording.stopAndUnloadAsync();
    const uri = recording.getURI();
    const userMsgId = Date.now().toString();
    setMessages(prev => [...prev, { id: userMsgId, text: '🎤 正在聽您說話...', sender: 'user' }]);
    setIsProcessing(true);
    uploadAudio(uri, userMsgId);
  }

  // --- 上傳 API ---
  async function uploadAudio(uri, msgId) {
    const formData = new FormData();
    formData.append('audio', { uri: uri, type: 'audio/m4a', name: 'recording.m4a' });
    formData.append('lang_code', langCode);

    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        body: formData,
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      const data = await response.json();

      if (data.status === 'success') {
        setMessages(prev => prev.map(m => m.id === msgId ? { ...m, text: '🎤 (語音訊息已傳送)' } : m));
        setMessages(prev => [...prev, { id: (Date.now() + 1).toString(), text: data.answer_text, sender: 'ai',imageBase64: data.image_base64 || null }]);

        // 處理地圖連動與顯示
        if (data.coordinates && data.coordinates.lat) {
          const newPoint = {
            latitude: data.coordinates.lat,
            longitude: data.coordinates.lng,
          };
          setTargetMarker(newPoint);
          setShowMap(true); // 自動開啟地圖
          
          // 等待地圖渲染後執行移動動畫
          setTimeout(() => {
            mapRef.current?.animateToRegion({
              ...newPoint, //  修正語法：需使用 ... 展開
              latitudeDelta: 0.003,
              longitudeDelta: 0.003,
            }, 1000);
          }, 500);
        }
      } else {
        Alert.alert('辨識失敗', data.message || '請再試一次');
      }
    } catch (error) {
      Alert.alert('連線失敗', '後端伺服器未啟動或網址錯誤');
    } finally {
      setIsProcessing(false);
    }
  }

  const renderItem = ({ item }) => (
    <View style={[styles.bubble, item.sender === 'user' ? styles.userBubble : styles.aiBubble]}>
      <Text style={[styles.bubbleText, item.sender === 'user' ? { color: '#fff' } : { color: '#000' }]}>
        {item.text}
      </Text>

      {/* 如果這則訊息帶有圖片，就把它渲染出來 */}
      {item.imageBase64 && (
        <TouchableOpacity onPress={() => handleImagePress(item.imageBase64)} activeOpacity={0.8}>
          <Image
            source={{ uri: `data:image/jpeg;base64,${item.imageBase64}` }}
            style={styles.chatImage}
          />
        </TouchableOpacity>
      )}
    </View>
  );

  return (
    <GestureHandlerRootView style={styles.container}>
      <View style={styles.container}>
        <SafeAreaView style={styles.container}>
          <KeyboardAvoidingView 
            behavior={Platform.OS === "ios" ? "padding" : "height"} 
            style={{ flex: 1 }}
          >
          <View style={styles.header}>
            <Text style={styles.title}>朝陽 AI 導覽員</Text>
            <Picker selectedValue={langCode} style={styles.picker} onValueChange={(val) => setLangCode(val)}>
              <Picker.Item label="繁體中文" value="zh-TW" />
              <Picker.Item label="English" value="en-US" />
              <Picker.Item label="日本語" value="ja-JP" />
            </Picker>
          </View>

          <FlatList
            data={messages}
            keyExtractor={item => item.id}
            renderItem={renderItem}
            contentContainerStyle={styles.chatArea}
          />

          {/* 地圖區塊 - 僅在 showMap 為 true 時顯示 */}
          {showMap && (
            <View style={styles.mapContainer}>
              <MapView
                ref={mapRef}
                style={styles.map}
                initialRegion={{
                  latitude: 24.0689,
                  longitude: 120.7145,
                  latitudeDelta: 0.01,
                  longitudeDelta: 0.01,
                }}
              >
                {targetMarker && <Marker coordinate={targetMarker} title="目標位置" />}
              </MapView>
              
              {/* 隱藏地圖按鈕 */}
              <TouchableOpacity 
                style={styles.hideMapBtn} 
                onPress={() => setShowMap(false)}
              >
                <Text style={styles.hideMapBtnText}>隱藏地圖 ✕</Text>
              </TouchableOpacity>
            </View>
          )}

          {/* 底部輸入區：整合語音與文字 */}
            <View style={styles.footer}>
              <View style={styles.inputRow}>
                <TextInput
                  style={styles.textInput}
                  placeholder="輸入問題..."
                  value={inputText}
                  onChangeText={setInputText}
                  multiline={false}
                />
                
                {inputText.length > 0 ? (
                  <TouchableOpacity style={styles.sendBtn} onPress={sendTextMessage}>
                    <Text style={styles.sendBtnText}>發送</Text>
                  </TouchableOpacity>
                ) : (
                  <TouchableOpacity 
                    style={[styles.miniRecordBtn, recording ? styles.recording : null]} 
                    onLongPress={startRecording}
                    onPressOut={stopAndSend}
                  >
                    <Text style={styles.miniBtnText}>{recording ? '...' : '🎤'}</Text>
                  </TouchableOpacity>
                )}
              </View>
              {isProcessing && <ActivityIndicator size="small" color="#007bff" style={{marginTop: 10}} />}
            </View>
          </KeyboardAvoidingView>
        </SafeAreaView>

        {/* 圖片放大 Modal */}
        <Modal
          animationType="fade"
          transparent={false}
          visible={modalVisible}
          onRequestClose={() => setModalVisible(false)}
        >
          <GestureHandlerRootView style={styles.modalContainer}>
              {/* 關閉按鈕保持原樣 */}
              <TouchableOpacity style={styles.closeButton} onPress={() => setModalVisible(false)}>
                <Text style={styles.closeButtonText}>✕ 關閉</Text>
              </TouchableOpacity>

              {selectedImageUri && (
                <ZoomableImage source={{ uri: selectedImageUri }} />
              )}
          </GestureHandlerRootView>
        </Modal>
      </View>
    </GestureHandlerRootView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f0f2f5' },
  header: { padding: 10, backgroundColor: '#fff', borderBottomWidth: 1, borderColor: '#ddd', flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  title: { fontSize: 20, fontWeight: 'bold', color: '#333' },
  picker: { width: 130 },
  chatArea: { padding: 15, paddingBottom: 30 },
  bubble: { padding: 15, borderRadius: 20, marginBottom: 12, maxWidth: '85%', elevation: 2, shadowColor: '#000', shadowOffset: { width: 0, height: 1 }, shadowOpacity: 0.1 },
  userBubble: { alignSelf: 'flex-end', backgroundColor: '#007bff' },
  aiBubble: { alignSelf: 'flex-start', backgroundColor: '#fff' },
  bubbleText: { fontSize: 16, lineHeight: 22 },

  // 新增圖片樣式
  chatImage: {
    width: 250, // 限制圖片最大寬度
    height: 250,
    marginTop: 10,
    borderRadius: 8,
    resizeMode: 'contain', // 確保圖片完整顯示不被裁切
  },
  
  // 地圖相關樣式
  mapContainer: {
    width: '100%',
    height: 300, // 調高一點方便觀看
    position: 'relative', // 為了讓隱藏按鈕可以絕對定位在地圖上
  },
  map: { flex: 1 },
  hideMapBtn: {
    position: 'absolute',
    top: 10,
    right: 10,
    backgroundColor: 'rgba(0,0,0,0.6)',
    paddingVertical: 5,
    paddingHorizontal: 12,
    borderRadius: 15,
  },
  hideMapBtnText: { color: '#fff', fontSize: 12, fontWeight: 'bold' },

  footer: { padding: 25, alignItems: 'center', backgroundColor: '#fff', borderTopWidth: 1, borderColor: '#eee' },
  recordBtn: { backgroundColor: '#007bff', paddingVertical: 18, paddingHorizontal: 50, borderRadius: 35 },
  recording: { backgroundColor: '#ff4444', transform: [{ scale: 1.1 }] },
  btnText: { color: '#fff', fontSize: 18, fontWeight: 'bold' },

  inputRow: {
    flexDirection: 'row',
    alignItems: 'center',
    width: '100%',
    backgroundColor: '#fff',
    borderRadius: 25,
    paddingHorizontal: 15,
    borderWidth: 1,
    borderColor: '#ddd',
  },
  textInput: {
    flex: 1,
    height: 45,
    fontSize: 16,
  },
  sendBtn: {
    paddingHorizontal: 15,
    paddingVertical: 8,
    backgroundColor: '#007bff',
    borderRadius: 20,
    marginLeft: 10,
  },
  sendBtnText: { color: '#fff', fontWeight: 'bold' },
  miniRecordBtn: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#007bff',
    justifyContent: 'center',
    alignItems: 'center',
    marginLeft: 10,
  },
  miniBtnText: { color: '#fff', fontSize: 18 },

  closeButton: {
      position: 'absolute',
      top: 50,
      right: 20,
      zIndex: 10,
      backgroundColor: 'rgba(255,255,255,0.2)',
      paddingVertical: 8,
      paddingHorizontal: 16,
      borderRadius: 20,
  },
  closeButtonText: {
      color: '#fff',
      fontSize: 16,
      fontWeight: 'bold',
  },

  modalContainer: {
    flex: 1,
    backgroundColor: '#000',
  },
  closeButton: {
      position: 'absolute',
      top: 50,
      right: 20,
      zIndex: 10,
      backgroundColor: 'rgba(255,255,255,0.2)',
      paddingVertical: 8,
      paddingHorizontal: 16,
      borderRadius: 20,
  },
  closeButtonText: {
      color: '#fff',
      fontSize: 16,
      fontWeight: 'bold',
  },
});