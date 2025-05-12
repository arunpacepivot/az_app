import requests
import json
def get_product_details(product_url):
    url = "https://axesso-axesso-amazon-data-service-v1.p.rapidapi.com/amz/amazon-lookup-product"

    querystring = {"url":product_url}

    headers = {
        "x-rapidapi-key": "af4fbe3844mshf4344d73d9d4c4ep1f36d5jsn0e2c306346e7",
        "x-rapidapi-host": "axesso-axesso-amazon-data-service-v1.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)

    return json.loads(response.text)

def get_text(product_url):
    product_details = get_product_details(product_url)
    # Convert the product details JSON into a readable text format
    def json_to_text(data) -> str:
        text_lines = []
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, dict):
                    text_lines.append(f"{key}:")
                    text_lines.append(json_to_text(value))
                elif isinstance(value, list):
                    text_lines.append(f"{key}:")
                    for item in value:
                        if isinstance(item, dict):
                            text_lines.append(json_to_text(item))
                        else:
                            text_lines.append(f"  - {item}")
                else:
                    text_lines.append(f"{key}: {value}")
        elif isinstance(data, list):
            for i, item in enumerate(data):
                text_lines.append(f"Item {i}:")
                if isinstance(item, (dict, list)):
                    text_lines.append(json_to_text(item))
                else:
                    text_lines.append(f"  - {item}")
        else:
            text_lines.append(str(data))
        return "\n".join(text_lines)

    # Convert the product details JSON to text
    product_text = json_to_text(product_details)
    return product_text
    
    
if __name__ == "__main__":
    print(get_text("https://www.amazon.in/dp/B0CHYR58VF"))
