import cv2
import mediapipe as mp
import numpy as np
import joblib
from sklearn.ensemble import RandomForestClassifier
import os

def extract_features(landmarks):
    points = np.array([[lm.x, lm.y] for lm in landmarks.landmark])
    # Normalize points relative to wrist (index 0)
    base = points[0]
    points = points - base
    # Scale points based on the max distance to the wrist
    max_dist = np.max(np.linalg.norm(points, axis=1))
    if max_dist > 0:
        points = points / max_dist
    return points.flatten().tolist()

def main():
    cap = cv2.VideoCapture(0)
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(static_image_mode=False, max_num_hands=1, min_detection_confidence=0.7)
    mp_draw = mp.solutions.drawing_utils

    data = []
    labels = []

    print("=== Coleta de Dados para Treinamento de Gestos ===")
    print("Pressione 'r' para salvar Pedra (Rock)")
    print("Pressione 'p' para salvar Papel (Paper)")
    print("Pressione 's' para salvar Tesoura (Scissors)")
    print("Pressione 't' para treinar e salvar o modelo")
    print("Pressione 'q' para sair sem salvar")
    print("DICA: Colete pelo menos 30 amostras de cada gesto em diferentes ângulos e distâncias.")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb_frame)

        features = None
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                features = extract_features(hand_landmarks)

        # UI Overlay
        cv2.putText(frame, f"Amostras Totais: {len(data)}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        counts = {label: labels.count(label) for label in set(labels)}
        y_offset = 60
        for k, v in counts.items():
            cv2.putText(frame, f"{k}: {v}", (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
            y_offset += 30

        cv2.imshow("Captura de Dados - Pressione r, p, s, t ou q", frame)
        key = cv2.waitKey(1) & 0xFF

        if key == ord('q'):
            print("Saindo sem salvar...")
            break
        elif key == ord('t'):
            if len(data) < 10:
                print("Poucos dados! Tente coletar mais amostras antes de treinar.")
            else:
                print("Treinando o modelo RandomForest...")
                clf = RandomForestClassifier(n_estimators=100, random_state=42)
                clf.fit(data, labels)
                
                # Save in the same directory as the script
                save_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gesture_model.pkl")
                joblib.dump(clf, save_path)
                print(f"Modelo salvo com sucesso em: {save_path}")
                break
        elif features is not None:
            if key == ord('r'):
                data.append(features)
                labels.append('rock')
                print("Salvo: rock")
            elif key == ord('p'):
                data.append(features)
                labels.append('paper')
                print("Salvo: paper")
            elif key == ord('s'):
                data.append(features)
                labels.append('scissors')
                print("Salvo: scissors")

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
