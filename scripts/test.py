import requests
import warnings
from time import time

warnings.filterwarnings("ignore")


def get_public_ip():
    try:
        response = requests.get(
            "https://api64.ipify.org?format=json",
            verify=False,
            headers={"X-Forwarded-For": "201.162.66.5"},
        )
        if response.status_code == 200:
            data = response.json()
            public_ip = data["ip"]
            return public_ip
        else:
            print("Error getting public IP address.")
            return None
    except Exception as e:
        print("Error:", e)
        return None


def test_docket():
    try:
        response = requests.get(
            "https://conteudo.cbf.com.br/sumulas/2023/1421se.pdf",
            verify=False,
            headers={"X-Forwarded-For": "201.162.66.5"},
        )
        if response.status_code == 200:
            data = response.content
            return data
        else:
            print("Error trying to catch docket.")
            return None
    except Exception as e:
        print("Error:", e)
        return None


if __name__ == "__main__":
    print("Testing")
    t = time()
    public_ip = get_public_ip()
    tf = time()
    if public_ip:
        print(f"Your public IP address is: {public_ip}")
        print(f"Total time to request: {tf - t:.2f} seconds.")

    t = time()
    data = test_docket()
    tf = time()
    if data:
        print(data)
        print(f"Total time to catch docket: {tf - t:.2f} seconds.")
