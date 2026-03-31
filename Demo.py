import pandas as pd
import joblib

# Load models
models = {
    "Logistic": joblib.load("exported_model/logistic.joblib"),
    "Decision Tree": joblib.load("exported_model/decision_tree.joblib"),
    "Random Forest": joblib.load("exported_model/random_forest.joblib"),
    "XGBoost": joblib.load("exported_model/xgboost.joblib"),
}

# Mock user input
demo_input = pd.DataFrame([{
    'เงินเดือนรวม': 59830,
    'ตามจ.18เขต': 1,

    'ตามจ.18ตำแหน่งสายงาน': 'พยาบาล์',
    'ตามจ.18ประเภทตำแหน่ง': 'กลุ่มวิชาชีพ',
    'ตามจ.18ระดับตำแหน่ง': 'สายแพทย์',
    'ประเภทบุคลากร': 'ลูกจ้างชั่วคราว',
    'ตามจ.18จังหวัด': 'พะเยา',
    'ตามจ.18ประเภทหน่วยงาน': 'รพท.',

    'เงินเดือนรวม_missing': 0,
    'ตามจ.18เขต_missing': 0
}])

# Predict
for name, model in models.items():
    prob = model.predict_proba(demo_input)[0]

    stay = round(prob[0] * 100, 2)
    leave = round(prob[1] * 100, 2)

    print(f"\n=== {name} ===")
    print(f"โอกาสอยู่ต่อ: {stay} %")
    print(f"โอกาสลาออก: {leave} %")