import requests
import os
import json
import time

# 从 GitHub Secrets 读取配置
CF_API_TOKEN    = os.environ["CF_API_TOKEN"]
CF_ZONE_ID      = os.environ["CF_ZONE_ID"]
CF_DNS_NAME     = os.environ["CF_DNS_NAME"]
QY_WEBHOOK      = os.environ.get("QY_WEBHOOK", "")

def get_cf_speed_test_ip():
    try:
        # 获取优选IP
        response = requests.get('https://ip.164746.xyz/ipTop.html', timeout=10)
        return response.text if response.status_code == 200 else None
    except:
        return None

def update_cf_dns(ip):
    # 获取 DNS 记录 ID
    url = f'https://api.cloudflare.com/client/v4/zones/{CF_ZONE_ID}/dns_records'
    headers = {'Authorization': f'Bearer {CF_API_TOKEN}', 'Content-Type': 'application/json'}
    
    records = requests.get(url, headers=headers).json().get('result', [])
    record_ids = [r['id'] for r in records if r['name'] == CF_DNS_NAME]
    
    if not record_ids:
        return "❌ 未找到域名记录"

    # 更新记录
    update_url = f"{url}/{record_ids[0]}"
    data = {'type': 'A', 'name': CF_DNS_NAME, 'content': ip}
    res = requests.put(update_url, headers=headers, json=data)
    return f"✅ DNS 更新成功\n**新 IP**: `{ip}`" if res.status_code == 200 else "❌ DNS 更新失败"

def push_to_wechat(content):
    webhook = os.environ.get("QY_WEBHOOK") or QY_WEBHOOK
    if not webhook: return

    # 降级为最基础的文本模式，测试微信兼容性
    data = {
        "msgtype": "text",
        "text": {
            "content": f"🚀 IP优选更新成功！\n最新运行结果：\n{content}"
        }
    }
    requests.post(webhook, json=data)

def main():
    ip_str = get_cf_speed_test_ip()
    if ip_str:
        # 默认取第一个最快的 IP
        first_ip = ip_str.split(',')[0]
        status = update_cf_dns(first_ip)
        push_to_wechat(status)
        print(f"执行完毕: {status}")

if __name__ == '__main__':
    main()
