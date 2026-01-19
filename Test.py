import cv2
import mediapipe as mp
import pyautogui
import numpy as np
import math # Matematiksel hesaplar için

# --- AYARLAR ---
cam_w, cam_h = 640, 480
frame_r = 100
smoothening = 5
CLICK_DISTANCE = 30  # Tıklama için parmakların ne kadar yakın olması gerektiği

ploc_x, ploc_y = 0, 0
cloc_x, cloc_y = 0, 0

screen_w, screen_h = pyautogui.size()

cap = cv2.VideoCapture(0)
cap.set(3, cam_w)
cap.set(4, cam_h)

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1)
mp_draw = mp.solutions.drawing_utils

while True:
    success, img = cap.read()
    img = cv2.flip(img, 1)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(img_rgb)
    
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_draw.draw_landmarks(img, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            
            # Koordinatları al
            lmList = []
            for id, lm in enumerate(hand_landmarks.landmark):
                h, w, c = img.shape
                cx, cy = int(lm.x * w), int(lm.y * h)
                lmList.append([id, cx, cy])
            
            # Eğer el tespit edildiyse
            if len(lmList) != 0:
                # İşaret (8) ve Orta (12) parmak uçlarının koordinatları
                x1, y1 = lmList[8][1], lmList[8][2]
                x2, y2 = lmList[12][1], lmList[12][2]
                
                # --- HAREKET (Sadece işaret parmağına göre) ---
                # Ekrana oranla
                x3 = np.interp(x1, (frame_r, cam_w - frame_r), (0, screen_w))
                y3 = np.interp(y1, (frame_r, cam_h - frame_r), (0, screen_h))
                
                # Yumuşat ve Hareket Ettir
                cloc_x = ploc_x + (x3 - ploc_x) / smoothening
                cloc_y = ploc_y + (y3 - ploc_y) / smoothening
                pyautogui.moveTo(cloc_x, cloc_y)
                ploc_x, ploc_y = cloc_x, cloc_y

                # --- TIKLAMA (Mesafe Hesabı) ---
                # İki parmak arasındaki mesafeyi hesapla (Hipotenüs)
                length = math.hypot(x2 - x1, y2 - y1)
                
                # Görselleştirelim: İki parmak arasına çizgi çek
                cv2.line(img, (x1, y1), (x2, y2), (255, 0, 255), 3)
                
                # Eğer mesafe kısaysa TIKLA
                if length < CLICK_DISTANCE:
                    # Görsel geri bildirim: Daire yeşil olsun
                    cv2.circle(img, (x1, y1), 15, (0, 255, 0), cv2.FILLED)
                    pyautogui.click()
                    # Çift tıklamayı önlemek için çok kısa bekleme eklenebilir ama şimdilik kalsın.
                else:
                    # Tıklamıyorsa daire kırmızı olsun
                    cv2.circle(img, (x1, y1), 15, (0, 0, 255), cv2.FILLED)

    cv2.imshow("Ahmet - AI Mouse", img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()