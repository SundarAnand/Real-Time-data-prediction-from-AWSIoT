# Required libraries
import paho.mqtt.client as paho
import ssl
import json
import sys
import pandas as pd
from keras.models import load_model
import warnings
warnings.filterwarnings("ignore")

# List to hold all the values
list_in_message=[]

# Defining the window size
window_size = 50

# Stride size
stride_size = 1

# Loading the model
model = load_model("jog_walk.h5")

# Defining a counter
count = 0

# Function to connect to the topic in the AWS IoT
def on_connect(client, userdata, flags, rc):
    print("Connection returned result: " + str(rc))
    client.subscribe("stm32/sensor", qos = 1)

# Function to be executed when we get a message in the topic -> real-time testing
def on_message(client, userdata, msg):
    global list_in_message, window_size, count, stride_size
    data = json.loads(msg.payload)

    # Updating the counter
    count = count + 1
    print (count)

    # Appending the data to a global list
    list_in_message.append(data)

    # For real-time testing, every 50 data -> Process and Pop the initial data
    if(len(list_in_message)>=window_size):

        # Converting the data to pandas df
        df = pd.DataFrame.from_records(list_in_message)
        
        # Getting the gyr y and converting it to numpy
        df = df[['gyr_y']]
        loaded_np = df[['gyr_y']].to_numpy()
        
        # Prediting
        loaded_np = loaded_np.reshape(1, 1, window_size)
        y_pred = model.predict(loaded_np)
        y_pred = y_pred[0][0]
        y_pred_rounded = (y_pred > 0.5).astype(int)
        
        # Calculating the probability
        if y_pred < 0.5:
            y_pred = 0.5 - y_pred
        else:
            y_pred = y_pred - 0.5
        y_pred = y_pred*2

        # Class definition
        class_list = ['walk', 'jog']

        # Getting the inference
        inference = class_list[y_pred_rounded]
        prob = y_pred

        # If confidance is less
        if y_pred <0.5:
            inference = "No Recognised Activity Found"

        # Printing the result
        print ([inference, prob])

        # Popping the first data
        list_in_message = list_in_message[stride_size:]
        #list_in_message.pop(0)


# MQTT connect credentials
mqttc = paho.Client()
mqttc.on_connect = on_connect
mqttc.on_message = on_message
awshost = "ap0risurn87nu-ats.iot.us-east-1.amazonaws.com"
awsport = 8883
caPath = "AmazonRootCA1.txt"
certPath = "5eb171f3d0-certificate.pem.crt"
keyPath= "5eb171f3d0-private.pem.key"
mqttc.tls_set(caPath, certfile=certPath, keyfile=keyPath, cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLSv1_2, ciphers=None)

# Connecting and calling the function in an infinite loop
mqttc.connect(awshost, awsport, keepalive=60)
mqttc.loop_forever()