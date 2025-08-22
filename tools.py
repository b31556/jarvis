import requests

with open(".env") as f:
    for line in f:
        if line.startswith("HASSTOKEN"):
            hasstoken = line.split("=")[1].strip().strip('"')
            break

def use(name,value):
    if name == "lights":
        light(value)


def light(value):


    url = "http://jundev.eu:8123/api/services/light/" + ("turn_off" if value == "off" else "turn_on")
    headers = {
        "Authorization": f"Bearer {hasstoken}",
        "Content-Type": "application/json"
    }
    payload ='{"entity_id": "light.lef"}'

    response = requests.post(url, headers=headers, data=payload)

    if response.ok:
        print("Light turned on successfully!")
    else:
        print(f"Failed to turn on light: {response.status_code} - {response.text}")
 