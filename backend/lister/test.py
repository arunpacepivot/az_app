import requests
url = "https://parazun-amazon-data.p.rapidapi.com/product/"

querystring = {"asin":"B097G95G1K","region":"US"}

headers = {
	"x-rapidapi-key": "af4fbe3844mshf4344d73d9d4c4ep1f36d5jsn0e2c306346e7",
	"x-rapidapi-host": "parazun-amazon-data.p.rapidapi.com"
}

response = requests.get(url, headers=headers, params=querystring)
# Check the status of the response
if response.status_code == 200:
    data=response.json()
else:
    print(f"Request failed with status code: {response.status_code}")



def extract_text_from_json(json_obj, text_list):
    if isinstance(json_obj, dict):
        for key, value in json_obj.items():
            extract_text_from_json(value, text_list)
    elif isinstance(json_obj, list):
        for item in json_obj:
            extract_text_from_json(item, text_list)
    elif isinstance(json_obj, str):
        text_list.append(json_obj)

text_list = []
extract_text_from_json(data, text_list)

