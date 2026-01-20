import cv2
import mediapipe as mp
import pyautogui
import numpy as np
import math
import time

# --- AYARLAR ---
cam_w, cam_h = 640, 480
frame_r = 60            # Kenar boşluğu
smoothening = 8         # Yumuşatma
CLICK_DISTANCE = 40     # Sol tık için parmak yakınlığı
SCROLL_SPEED = 10       # Kaydırma hızı (Yumruk modunda)

ploc_x, ploc_y = 0, 0
cloc_x, cloc_y = 0, 0

last_click_time = 0
click_delay = 0.5       # Tıklama ar bekleme süresi

screen_w, screen_h = pyautogui.size()

cap = cv2.VideoCapture(0)
cap.set(3, cam_w)
cap.set(4, cam_h)

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1)
mp_draw = mp.solutions.drawing_utils

tip_ids = [4, 8, 12, 16, 20]

def fingers_up_check(lm_list):
    """Hangi parmakların havada olduğunu döndürür"""
    fingers = []
    if lm_list[tip_ids[0]][1] < lm_list[tip_ids[0] - 1][1]: 
        fingers.append(1)
    else:
        fingers.append(0)

    for id in range(1, 5):
        if lm_list[tip_ids[id]][2] < lm_list[tip_ids[id] - 2][2]:
            fingers.append(1)
        else:
            fingers.append(0)
    return fingers

while True:
    success, img = cap.read() #kamera okuyor
    img = cv2.flip(img, 1)  # Aynalama
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB) # zorunlu BGR to RGB donuşumu
    results = hands.process(img_rgb) # elleri işle
    
    if results.multi_hand_landmarks:  
        for hand_landmarks in results.multi_hand_landmarks:
            mp_draw.draw_landmarks(img, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            
            lmList = []
            for id, lm in enumerate(hand_landmarks.landmark):
                h, w, c = img.shape
                cx, cy = int(lm.x * w), int(lm.y * h)
                lmList.append([id, cx, cy])
            
            if len(lmList) != 0:
                x1, y1 = lmList[8][1], lmList[8][2]   # İşaret
                x2, y2 = lmList[12][1], lmList[12][2] # Orta
                
                # Elin genel konumu için Orta Parmak Kökünü (Knuckle) alıyoruz (ID: 9)
                # Çünkü yumruk yapınca parmak uçları kaybolur, ama kök sabittir.
                hand_center_y = lmList[9][2]

                fingers = fingers_up_check(lmList)
                
                # Sınır karesi
                cv2.rectangle(img, (frame_r, frame_r), (cam_w - frame_r, cam_h - frame_r), (255, 0, 255), 2)

                # -------------------------------------------------------------
                # MOD 1: HAREKET (Sadece İşaret Açık) -> [?, 1, 0, 0, 0]
                # -------------------------------------------------------------
                if fingers[1] == 1 and fingers[2] == 0 and fingers[3] == 0:
                    x3 = np.interp(x1, (frame_r, cam_w - frame_r), (0, screen_w))
                    y3 = np.interp(y1, (frame_r, cam_h - frame_r), (0, screen_h))
                    
                    cloc_x = ploc_x + (x3 - ploc_x) / smoothening
                    cloc_y = ploc_y + (y3 - ploc_y) / smoothening
                    
                    pyautogui.moveTo(cloc_x, cloc_y)
                    ploc_x, ploc_y = cloc_x, cloc_y
                    cv2.circle(img, (x1, y1), 15, (255, 0, 255), cv2.FILLED)

                # -------------------------------------------------------------
                # MOD 2: SOL TIK (İşaret + Orta Açık) -> [?, 1, 1, 0, 0]
                # -------------------------------------------------------------
                elif fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 0:
                    length = math.hypot(x2 - x1, y2 - y1)
                    cv2.line(img, (x1, y1), (x2, y2), (255, 0, 255), 3)
                    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                    
                    # Mesafe kısaysa tıkla
                    if length < CLICK_DISTANCE:
                        cv2.circle(img, (cx, cy), 15, (0, 255, 0), cv2.FILLED)
                        if time.time() - last_click_time > click_delay:
                            pyautogui.click()
                            last_click_time = time.time()
                            print("Sol Tık")

                # -------------------------------------------------------------
                # MOD 3: SAĞ TIK (3 Parmak Açık) -> [?, 1, 1, 1, 0] -> YENİ İSTEK
                # -------------------------------------------------------------
                elif fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 1:
                    # Görsel geri bildirim
                    cv2.putText(img, "SAG TIK MODU", (150, 50), cv2.FONT_HERSHEY_PLAIN, 2, (0, 0, 255), 2)
                    
                    if time.time() - last_click_time > click_delay:
                        pyautogui.rightClick()
                        last_click_time = time.time()
                        print("Sağ Tık")

                # -------------------------------------------------------------
                # MOD 4: SCROLL (YUMRUK - 4 Parmak Kapalı) -> [?, 0, 0, 0, 0] -> YENİ İSTEK
                # -------------------------------------------------------------
                elif fingers[1] == 0 and fingers[2] == 0 and fingers[3] == 0 and fingers[4] == 0:
                    
                    # Yumruğun ekranın neresinde olduğuna bakıyoruz
                    # Ekranı dikeyde 3'e böldük gibi düşün.
                    
                    # YUKARI BÖLGE (Kamerada üst kısım) -> Sayfa Yukarı
                    if hand_center_y < cam_h / 2 - 50:
                        pyautogui.scroll(SCROLL_SPEED)
                        cv2.putText(img, "YUKARI KAYDIR", (20, 50), cv2.FONT_HERSHEY_PLAIN, 3, (0, 255, 0), 3)
                    
                    # AŞAĞI BÖLGE (Kamerada alt kısım) -> Sayfa Aşağı
                    elif hand_center_y > cam_h / 2 + 50:
                        pyautogui.scroll(-SCROLL_SPEED)
                        cv2.putText(img, "ASAGI KAYDIR", (20, 50), cv2.FONT_HERSHEY_PLAIN, 3, (0, 0, 255), 3)
                    
                    # ORTA BÖLGE -> Dur
                    else:
                        cv2.putText(img, "YUMRUK: SCROLL HAZIR", (20, 50), cv2.FONT_HERSHEY_PLAIN, 2, (255, 255, 0), 2)
                        # Yumruğun merkezini göster
                        cv2.circle(img, (lmList[9][1], lmList[9][2]), 15, (255, 255, 0), cv2.FILLED)

    cv2.imshow("Ahmet - V4 Custom Mouse", img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()