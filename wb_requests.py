from imports import *

manager = urllib3.PoolManager()


def get_auth():
    try:
        auth_file = open("auth")
        auth3, x_supplier_id = auth_file.readlines()
        auth3 = auth3[:-1]

    except FileNotFoundError:
        print("файл аутенификации не был найден, поэтому он будет создан")
        auth3, x_supplier_id = get_auth_data()
        auth_file = open("auth", "w")
        auth_file.write(auth3 + "\n" + x_supplier_id)

    else:
        test_auth = get_wb_token(auth3)
        if "ERROR:" in test_auth:
            print(test_auth)
            auth3, x_supplier_id = get_auth_data()
            auth_file = open("auth", "w")
            auth_file.write(auth3 + "\n" + x_supplier_id)
    return auth3, x_supplier_id


def get_wb_token(auth3):
    headers = {
        "Host": "seller.wildberries.ru",
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Cookie": f"WILDAUTHNEW_V3={auth3}"
    }
    body = '{"device":""}'
    response = manager.request("POST", url="https://seller.wildberries.ru/passport/api/v2/auth/wild_v3_upgrade",
                               headers=headers, body=body)
    i = 0
    while response.status != 200 and i < 3:
        i += 1
        response = manager.request("POST", url="https://seller.wildberries.ru/passport/api/v2/auth/wild_v3_upgrade",
                                   headers=headers, body=body)
    if response.status != 200:
        return f"ERROR: не удалось получить WBToken\nstatus: {response.status}\ndata: {response.data.decode('utf-8')}\nheaders: {response.headers}"
    else:
        if "set-cookie" in response.headers.keys():
            wb_token = response.headers['set-cookie'].split(';')[0]
            if 'WBToken' not in wb_token:
                return f"ERROR: параметр set-cookie не содержит в себе WBToken\nset-cookie: {response.headers['set_cookies']}"
            else:
                return wb_token
        else:
            return f"ERROR: полученный отсервера ответ не содердит в себе заголовка set-cookie\nheaders: {response.headers}"


def get_auth_data():
    driver = webdriver.Firefox(executable_path=GeckoDriverManager().install())
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
    # auth3 = "58A619BAF19A517EBC742D11356936FE54AF84DA6745DABDF8FACD756A179DF301D47B0EA7F9745876CF427149F3CE1277402F55D02482219E8324416D7378204D375982CF683B45ADC201B0107F1199B79EC7982D641CAE788689B30BED809BEFC487801BE3509476292F72B05667262E37607AA0F6E2BADFEACBB1ADAD15435BA4212F6598E473EB21B18220B54949D61EB03391A0A8EEDA7F24CC0A73C8FB55088DD6ACCACD6CC8732C9BD340E51FFDF7CBDE9C5FE29EB5417A3C8E5CBB03D7D12BE4CCD32EE0C67D106F2E47D18A55BB67CF5C62112C8C0B78F41AFCAD7E064232DE37D01F3AE13FD2C96B88108BDBBED8EF8AE0161FCB7CC1F0EA3507BC2C0CB3CCFF6788EC1C288F5BDB6CD945D72BC11D34B64C62DAA0FE7FB0A780678689CB2A7CFC9AA8608848DAAAC2C09FB8729FDB54D46AB1027182D2D0307141B99526187163F04FEFF810E9A4213AB6155D3617 "

    wb_token = get_wb_token(auth3)
    if "ERROR:" in wb_token:
        return wb_token
    headers = {
        "Host": "seller.wildberries.ru",
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Cookie": wb_token
    }
    body = '[{"method":"getUserSuppliers","params":{},"id":"json-rpc_3","jsonrpc":"2.0"}]'
    response = manager.request("POST", url="https://seller.wildberries.ru/ns/suppliers/suppliers-portal-core/suppliers", headers=headers, body=body)
    i = 0
    while response.status != 200 and i < 3:
        i += 1
        response = manager.request("POST",
                                   url="https://seller.wildberries.ru/ns/suppliers/suppliers-portal-core/suppliers",
                                   headers=headers, body=body)
    if response.status != 200:
        return f"ERROR: не удалось получить x-supplier-id\nstatus: {response.status}\ndata: {response.data.decode('utf-8')}\nheaders: {response.headers}"
    try:
        suppliers_data = json.loads(response.data)
    except json.JSONDecodeError:
        return "ERROR: в ответе x-supplier-data содержится ошибка"
    x_supplier_id = suppliers_data[0]['result']['suppliers'][0]['id']
    return auth3, x_supplier_id


def get_limits(auth3, x_supplier_id, from_time, to_time, warehouse_id):
    wb_token = get_wb_token(auth3)
    headers = {
        "Host": "seller.wildberries.ru",
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Cookie": f"{wb_token};x-supplier-id={x_supplier_id}"
    }
    url = f"https://seller.wildberries.ru/ns/supply/supply-manager/api/v1/goodincomes/limits?from={from_time}&to={to_time}&warehouseId={warehouse_id}"
    response = manager.request('GET', url=url, headers=headers)
    i = 0
    while response.status != 200 and i < 3:
        i += 1
        response = manager.request('GET', url=url, headers=headers)
    if response.status != 200:
        return f"ERROR: не удалось получить данные о лимитах\nstatus: {response.status}\ndata: {response.data.decode('utf-8')}\nheaders: {response.headers}\nurl: {url}"
    try:
        limits_data = json.loads(response.data)
    except json.JSONDecodeError:
        return f"ERROR: в ответе limits содержится ошибка\ndata: {response.data.decode('utf-8')}"
    try:
        limits = {datetime.datetime.strptime(limit['date'][:10], "%Y-%m-%d").date(): {key: value for key, value in zip(limit.keys(), limit.values()) if key != 'date'} for limit in limits_data['data']['limits']}
    except KeyError:
        return f"ERROR: в ответе limits содержится ошибка\ndata: {response.data.decode('utf-8')}"
    return limits
