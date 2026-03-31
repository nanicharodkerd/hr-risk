import pandas as pd
import numpy as np
import joblib
import os

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib import font_manager, rcParams

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, roc_auc_score, roc_curve, auc
from xgboost import XGBClassifier

rcParams['font.family'] = 'Tahoma'
rcParams['axes.unicode_minus'] = False

#confic
xls = pd.ExcelFile("ข้อมูลทดสอบ v3.xlsx")

sheet_names = {
    "แพทย์": "doctor",
    "พยาบาลวิชาชีพ": "nurse",
    "ทันตแพทย์": "dentist",
    "เภสัชกร": "pharmacist"
}

BASE_DIR = "exported_model"
os.makedirs(BASE_DIR, exist_ok=True)


#data prep
def prepare_data(df):
    df = df.copy()

    # ---- clean string ----
    df['สถานะตำแหน่ง'] = (
        df['สถานะตำแหน่ง']
        .astype(str)
        .str.strip()
    )

    # ---- map ลาออก ----
    df['ลาออก'] = np.where(
        df['สถานะตำแหน่ง'].str.contains('ว่าง'),
        1,
        0
    )

    # ถ้าอยากมั่นใจว่าเหลือข้อมูลจริง
    df = df[df['สถานะตำแหน่ง'].str.contains('ครอง|ว่าง')]

    num_cols = [
        'เงินเดือนรวม',
        'ตามจ.18เขต',
        'อายุ',
        'อายุราชการ',
        'ปีที่เหลือก่อนเกษียณ'
    ]

    cat_cols = [
        'ตามจ.18ประเภทตำแหน่ง',
        'ตามจ.18ระดับตำแหน่ง',
        'ประเภทบุคลากร',
        'ตามจ.18จังหวัด',
        'ตามจ.18ประเภทหน่วยงาน',
        'เพศ'
    ]

    # ---- สร้าง column กันพัง ----
    for col in num_cols + cat_cols:
        if col not in df.columns:
            df[col] = np.nan

    df = df[num_cols + cat_cols + ['ลาออก']]

    return df, num_cols, cat_cols

#model build
def build_models(num_cols, cat_cols, y_train):
    preprocess = ColumnTransformer([
        ("num", Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler())
        ]), num_cols),
        ("cat", Pipeline([
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore"))
        ]), cat_cols)
    ])

    CLASS_WEIGHT = {0: 1, 1: 6}
    scale_pos_weight = (y_train == 0).sum() / (y_train == 1).sum()

    return {
        "logistic": Pipeline([
            ("preprocess", preprocess),
            ("model", LogisticRegression(max_iter=1000, class_weight=CLASS_WEIGHT))
        ]),
        "decision_tree": Pipeline([
            ("preprocess", preprocess),
            ("model", DecisionTreeClassifier(max_depth=6, class_weight=CLASS_WEIGHT))
        ]),
        "random_forest": Pipeline([
            ("preprocess", preprocess),
            ("model", RandomForestClassifier(
                n_estimators=200, max_depth=8,
                class_weight=CLASS_WEIGHT, n_jobs=-1
            ))
        ]),
        "xgboost": Pipeline([
            ("preprocess", preprocess),
            ("model", XGBClassifier(
                n_estimators=400,
                max_depth=4,
                learning_rate=0.05,
                subsample=0.8,
                colsample_bytree=0.8,
                min_child_weight=5,
                gamma=0.2,
                scale_pos_weight=scale_pos_weight,
                eval_metric="logloss",
                random_state=42
            ))
        ])
    }

#train loop
for sheet, folder in sheet_names.items():
    print(f"Training : {sheet}")

    df_raw = pd.read_excel(xls, sheet_name=sheet)
    df, num_cols, cat_cols = prepare_data(df_raw)

    X = df[num_cols + cat_cols]
    y = df['ลาออก']

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    models = build_models(num_cols, cat_cols, y_train)

    save_dir = os.path.join(BASE_DIR, folder)
    os.makedirs(save_dir, exist_ok=True)

    for name, model in models.items():
        print(f"\n{name}")

        model.fit(X_train, y_train)

        # ===== evaluate =====
        y_prob = model.predict_proba(X_test)[:, 1]
        y_pred = (y_prob >= 0.3).astype(int)

        print(classification_report(y_test, y_pred))

        roc_auc = roc_auc_score(y_test, y_prob)
        print("ROC-AUC:", roc_auc)

        # ===== ROC Curve =====
        fpr, tpr, _ = roc_curve(y_test, y_prob)
        roc_auc_value = auc(fpr, tpr)

        plt.figure()
        plt.plot(fpr, tpr, label=f'ROC Curve (AUC = {roc_auc_value:.3f})')
        plt.plot([0, 1], [0, 1], linestyle='--', label='Random Guess')
        plt.xlabel('False Positive Rate')
        plt.ylabel('True Positive Rate')
        plt.title(f'ROC Curve : {sheet} - {name}')
        plt.legend(loc='lower right')
        plt.grid(True)

        #save รูป
        roc_path = f"{save_dir}/{name}_roc_curve.png"
        plt.savefig(roc_path, dpi=300, bbox_inches='tight')
        plt.close()

        #risk score
        y_all_prob = model.predict_proba(X)[:, 1]

        df_result = df_raw.copy()
        df_result["risk_score"] = (y_all_prob * 100).round(1)

        df_result["risk_level"] = pd.cut(
            df_result["risk_score"],
            bins=[0, 40, 70, 100],
            labels=["ต่ำ", "เฝ้าระวัง", "สูง"]
        )

        #export risk
        risk_path = f"{save_dir}/{name}_risk.xlsx"
        df_result.sort_values("risk_score", ascending=False)\
                 .to_excel(risk_path, index=False)

        #export model
        joblib.dump(model, f"{save_dir}/{name}.joblib")


print(f"จำนวนข้อมูลหลัง clean = {len(df)}")

if len(df) < 10:
    raise ValueError("ข้อมูลน้อยเกินไปหลัง cleaning กรุณาตรวจสอบสถานะตำแหน่ง")

print("\n Train & Export")