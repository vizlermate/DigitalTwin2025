from flask import Flask, request, jsonify
from queue import Queue
import threading
import uuid
import random
import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder

app = Flask(__name__)

model = joblib.load("Python/models/bike_demand_model.pkl")
le = joblib.load("Python/models/le.pkl")
print(le.transform(["W 21 St & 6 Ave"]))

# Endpoint to check job status
@app.route('/predict', methods=['POST', 'PUT'])
def predict():
    data = request.get_data()
    data = data.decode("utf-8")
    values = data.split("||")
    d = {'day_of_week': [int(values[0])], 'hour': [int(values[1])], 'station_id': le.transform([values[2].replace(u'\u200b', '')])}
    df = pd.DataFrame(data=d)
    print(model.predict(df)[0])
    return jsonify({"prediction": model.predict(df)[0]})



if __name__ == '__main__':
    app.run(port=5000)