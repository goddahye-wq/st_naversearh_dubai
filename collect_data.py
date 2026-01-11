import os
import json
import urllib.request
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")

def get_header():
    return {
        "X-Naver-Client-Id": CLIENT_ID,
        "X-Naver-Client-Secret": CLIENT_SECRET,
        "Content-Type": "application/json"
    }

def save_to_csv(data_list, filename_prefix):
    timestamp = datetime.now().strftime("%Y%m%d")
    filename = f"raw_data/{filename_prefix}_{timestamp}.csv"
    if not data_list:
        print(f"No data to save for {filename_prefix}")
        return
    df = pd.DataFrame(data_list)
    df.to_csv(filename, index=False, encoding="utf-8-sig")
    print(f"Saved: {filename}")

def collect_datalab_search():
    print("Collecting Datalab Search Trends...")
    url = "https://openapi.naver.com/v1/datalab/search"
    body = {
        "startDate": "2025-01-01",
        "endDate": "2025-12-31",
        "timeUnit": "date",
        "keywordGroups": [
            {"groupName": "두바이 쫀득쿠키", "keywords": ["두바이 쫀득쿠키", "두바이쿠키"]},
            {"groupName": "두바이 초콜릿", "keywords": ["두바이 초콜릿", "두바이초코"]}
        ]
    }
    
    request = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), headers=get_header())
    try:
        response = urllib.request.urlopen(request)
        res_body = json.loads(response.read().decode("utf-8"))
        
        results = []
        for group in res_body['results']:
            title = group['title']
            for item in group['data']:
                results.append({
                    "date": item['period'],
                    "keyword_group": title,
                    "ratio": item['ratio']
                })
        save_to_csv(results, "dubai_search_trend_2025")
    except Exception as e:
        print(f"Error in Datalab Search: {e}")

def collect_shopping_insight():
    print("Collecting Shopping Insight...")
    url = "https://openapi.naver.com/v1/datalab/shopping/categories"
    # 식품(50000006)으로 테스트
    body = {
        "startDate": "2025-01-01",
        "endDate": "2025-12-31",
        "timeUnit": "date",
        "category": [
            {"name": "식품", "param": ["50000006"]}
        ]
    }
    
    request = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), headers=get_header())
    try:
        response = urllib.request.urlopen(request)
        res_body = json.loads(response.read().decode("utf-8"))
        
        results = []
        for group in res_body['results']:
            title = group['title']
            for item in group['data']:
                results.append({
                    "date": item['period'],
                    "category": title,
                    "ratio": item['ratio']
                })
        save_to_csv(results, "dubai_shopping_trend_2025")
    except Exception as e:
        print(f"Error in Shopping Insight: {e}")

def collect_search_api(api_type, keywords):
    print(f"Collecting Search API ({api_type})...")
    
    all_results = []
    for kw in keywords:
        encText = urllib.parse.quote(kw)
        url = f"https://openapi.naver.com/v1/search/{api_type}.json?query={encText}&display=100"
        
        request = urllib.request.Request(url)
        request.add_header("X-Naver-Client-Id", CLIENT_ID)
        request.add_header("X-Naver-Client-Secret", CLIENT_SECRET)
        
        try:
            response = urllib.request.urlopen(request)
            res_body = json.loads(response.read().decode("utf-8"))
            
            for item in res_body['items']:
                item['keyword'] = kw
                all_results.append(item)
        except Exception as e:
            print(f"Error in Search {api_type} for {kw}: {e}")
            
    save_to_csv(all_results, f"dubai_{api_type}_latest")

if __name__ == "__main__":
    if not CLIENT_ID or "YOUR" in CLIENT_ID:
        print("!!! ERROR: API keys are not set in .env file. Please update .env with valid credentials.")
    else:
        keywords = ["두바이 쫀득쿠키", "두바이 초콜릿"]
        collect_datalab_search()
        collect_shopping_insight()
        collect_search_api("blog", keywords)
        collect_search_api("shop", keywords)
        print("Data collection completed.")
