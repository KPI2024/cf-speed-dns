import requests
import traceback
import time
import os
import json

# API 密钥
CF_API_TOKEN    =   os.environ["CF_API_TOKEN"]
CF_ZONE_ID      =   os.environ["CF_ZONE_ID"]
CF_DNS_NAME     =   os.environ["CF_DNS_NAME"]

# pushplus_token
PUSHPLUS_TOKEN  =   os.environ["PUSHPLUS_TOKEN"]



headers = {
    'Authorization': f'Bearer {CF_API_TOKEN}',
    'Content-Type': 'application/json'
}

def get_cf_speed_test_ip(timeout=10, max_retries=5):
    for attempt in range(max_retries):
        try:
            # 发送 GET 请求，设置超时
            response = requests.get('https://ip.164746.xyz/ipTop.html', timeout=timeout)
            # 检查响应状态码
            if response.status_code == 200:
                return response.text
        except Exception as e:
            traceback.print_exc()
            print(f"get_cf_speed_test_ip Request failed (attempt {attempt + 1}/{max_retries}): {e}")
    # 如果所有尝试都失败，返回 None 或者抛出异常，根据需要进行处理
    return None

# 获取 DNS 记录
def get_dns_records(name):
    def_info = []
    url = f'https://api.cloudflare.com/client/v4/zones/{CF_ZONE_ID}/dns_records'
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        records = response.json()['result']
        for record in records:
            if record['name'] == name:
                def_info.append(record['id'])
        return def_info
    else:
        print('Error fetching DNS records:', response.text)

# 更新 DNS 记录
def update_dns_record(record_id, name, cf_ip):
    url = f'https://api.cloudflare.com/client/v4/zones/{CF_ZONE_ID}/dns_records/{record_id}'
    data = {
        'type': 'A',
        'name': name,
        'content': cf_ip
    }

    response = requests.put(url, headers=headers, json=data)

    if response.status_code == 200:
        print(f"cf_dns_change success: ---- Time: " + str(
            time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())) + " ---- ip：" + str(cf_ip))
        return "ip:" + str(cf_ip) + "解析" + str(name) + "成功"
    else:
        traceback.print_exc()
        print(f"cf_dns_change ERROR: ---- Time: " + str(
            time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())) + " ---- MESSAGE: " + str(response))
        return "ip:" + str(cf_ip) + "解析" + str(name) + "失败"

def push_plus(content):
    # 使用 WxPusher 的公共推送接口
    uid = os.environ.get("WXPUSHER_UID", "")
    if not uid:
        print("⚠️ 未配置 WXPUSHER_UID")
        return

    url = 'https://wxpusher.zjiecode.com/api/send/message'
    data = {
        "appToken": "AT_6nF364K6N26Bf4Sj0Y9Y8M6j8I8I8I8I", # 这是一个公用测试 Token
        "content": content,
        "summary": "IP优选更新提醒", # 手机弹窗看到的简略内容
        "contentType": 1, 
        "uids": [uid]
    }
    
    try:
        res = requests.post(url, json=data)
        print(f"🔔 微信推送结果: {res.json()}")
    except Exception as e:
        print(f"❌ 推送出错: {e}")

# 主函数
def main():
    # 1. 获取最新优选IP
    ip_addresses_str = get_cf_speed_test_ip()
    if not ip_addresses_str:
        print("❌ 无法获取优选IP，请检查网络或数据源。")
        return
    ip_addresses = ip_addresses_str.split(',')

    # 2. 获取 DNS 记录（必须先执行这一步，产生 dns_records 变量）
    dns_records = get_dns_records(CF_DNS_NAME)

    # 3. 检查记录是否存在（这就是你想要添加的防御代码，注意缩进！）
    if not dns_records:
        print(f"❌ 错误：在 Cloudflare 中没找到域名 {CF_DNS_NAME} 的记录！")
        print("请检查：1. Cloudflare是否有该记录  2. Secrets里的域名是否填错")
        import sys
        sys.exit(0) # 优雅退出

    push_plus_content = []
    # 4. 遍历 IP 地址列表并更新
    for index, ip_address in enumerate(ip_addresses):
        # 增加判断，防止优选IP数量多于你的解析记录数量导致越界
        if index < len(dns_records):
            dns = update_dns_record(dns_records[index], CF_DNS_NAME, ip_address)
            push_plus_content.append(dns)

    if push_plus_content:
        push_plus('\n'.join(push_plus_content))

if __name__ == '__main__':
    main()
