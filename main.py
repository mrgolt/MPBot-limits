import urllib3

from imports import *

manager = urllib3.PoolManager()

def get_auth_data():
    driver = webdriver.Firefox(executable_path="geckodriver.exe")
    driver.get("https://www.wildberries.ru/security/login")
    print("войдите всвой аккаунт в создавшемся окне и нажмите в этом окне Enter")
    input()
    cookies = driver.get_cookies()

    auth3 = None
    for cookie in cookies:
        if cookie['name'] == 'WILDAUTHNEW_V3':
            auth3 = cookie['value']
    if not auth3:
        return "ERROR: куки файл аутентификаци не был получен"

    headers = {
        "Host": "seller.wildberries.ru",
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Cookie": f"WILDAUTHNEW_V3={auth3}"
    }
    body = '{"device":""}'
    manager.request("POST", url="https://seller.wildberries.ru/passport/api/v2/auth/wild_v3_upgrade", headers=headers, body=body)

    headers = {
        "Host": "seller.wildberries.ru",
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Cookie": f"WBToken={WBToken}"
    }
    body = '[{"method":"getUserSuppliers","params":{},"id":"json-rpc_3","jsonrpc":"2.0"}]'
    manager.request("POST", url="https://seller.wildberries.ru/ns/suppliers/suppliers-portal-core/suppliers", headers=headers, body=body)




def auth():
    try:
        auth_file = open("auth")
        auth3, supplier_id = auth_file.readlines()
    except FileNotFoundError:
        print("файл аутенификации не был найден, поэтому он будет создан")
        auth3, supplier_id = get_auth_data()

get_auth_data()