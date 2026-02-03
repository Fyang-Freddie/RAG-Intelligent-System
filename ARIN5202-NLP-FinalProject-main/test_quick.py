"""
Quick Test Script - Run a few sample queries
Simplified version for quick testing without full benchmark
Supports both text queries and image files
"""

import os
import sys
import time
import csv
from datetime import datetime
from typing import Dict, Any

# Add app directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.controller.pipeline import run_search_pipeline
from app.utils.profiler import reset_performance_data, get_performance_monitor
from app.services.document_processor import get_document_processor

# Sample queries for quick testing
# Can be either:
# - String: text query
# - Dict with "file": path to image/document file
# - Dict with "file" and "query": file input with accompanying question
QUICK_TESTS = [
    # Set 1
    "What are some common symptoms of hay fever?",
    "What's the weather forecast for this afternoon in Hong Kong?",
    "What is the standard voltage for household electronics in Hong Kong?",
    "What is 15 multiplied by 24?",
    "What are the five official colors of the Olympic rings?",
    "How do you say 'thank you' in Cantonese?",
    "What are the upcoming public holidays in Hong Kong this year?",
    "How can I report a lost Octopus card?",
    "Will it rain in Shenzhen tomorrow?",
    "What year was the Hong Kong-Zhuhai-Macau Bridge opened?",
    "Who wrote \"Romeo and Juliet\"?",
    "How do I apply for a Hong Kong public library card?",
    "What is the tallest building in Hong Kong?",
    "Give me a simple recipe for fried rice.",
    "What is the temperature in Beijing right now?",
    "What are the operating hours for the Star Ferry between Central and Tsim Sha Tsui?",
    "What time is sunset in Hong Kong today?",
    "What are the general visiting hours for public hospitals in Hong Kong?",
    "What is the chemical formula for water?",
    "What is the emergency phone number for the police in Hong Kong?",
    "In Hong Kong, what is the Voluntary Health Insurance Scheme (VHIS)?",
    "What is the main food eaten during the Dragon Boat Festival in Hong Kong?",
    "What is the wind speed in Shanghai?",
    "What is the difference between a typhoon warning signal No. 8 and No. 10?",
    "What planet is known as the Red Planet?",
    "How many days are in a leap year?",
    "How many SARs (Special Administrative Regions) are in China?",
    "What does the 'MPF' abbreviation stand for in Hong Kong?",
    "What is the capital of Japan?",
    "What is the maximum claim amount for the Small Claims Tribunal in Hong Kong?",
    
    "如果我發燒和喉嚨痛，應該去看普通科還是專科醫生？",
    "香港天文臺現在懸掛的是什麼熱帶氣旋警告信號？",
    "香港的公共圖書館在哪個熱帶氣旋警告信號下會關閉？",
    "1024減去768等於多少？",
    "構成漢字的“永字八法”指的是哪八個筆劃？",
    "“早晨”在廣東話裡是什麼意思？", 
    "香港法定最低時薪是多少？",
    "在香港如何申請一本特區護照？",
    "明天廣州的空氣質量指數是多少？",
    "香港會議展覽中心是什麼時候建成的？",
    "中國四大古典名著是哪幾部？",
    "在香港續領駕駛執照需要什麼文件？",
    "香港最大的離島是哪個島？",
    "如何製作一杯港式檸檬茶？",
    "澳門現在的濕度是多少？",
    "香港電車的首班車和末班車是幾點？",
    "今天香港的日出時間是幾點？",
    "香港的公立醫院急症室收費是多少？",
    "地球大氣中含量最高的氣體是什麼？",
    "在香港，如果發生火災或需要救護車，應該撥打什麼電話號碼？",
    "香港的強制性公積金（MPF）是什麼？",
    "中秋節在香港通常會吃什麼傳統食物？",
    "珠海今天的紫外線強度如何？",
    "解釋一下什麼是“強制性驗窗計劃”。",
    "太陽系中最大的行星是哪一顆？",
    "一個星期有多少個小時？",
    "中國有多少個直轄市？",
    "在香港，“強積金”的全稱是什麼？",
    "泰國的首都是哪裡？",
    "在香港，多少歲可以合法地簽訂合約？",
    
    # # Set 2
    "Provide the route from Kennedy Town to Hong Kong International Airport.",
    "Assess the chance of Typhoon Signal No. 8 being issued tonight.",
    "State whether heavy rain would affect Shenzhen Bay Port opening hours.",
    "Provide today's Hang Seng Index percentage change at close.",
    "State whether an evening run in Mong Kok today is advisable.",
    "State whether the Star Ferry Central–Tsim Sha Tsui service operates after 23:00.",
    "State whether schools are currently suspended in Hong Kong.",
    "Provide tomorrow's opening time for Lo Wu Control Point.",
    "List recommended restaurants in Kowloon City.",
    "State whether road closures will occur at Kai Tak Cruise Terminal during the National Games period.",
    "Provide the current CLP residential basic tariff per kWh.",
    "Provide the nearest 24/7 pharmacy in Sha Tin.",
    "State the date of the Hong Kong Marathon.",
    "Provide the current gold price in HKD.",
    "State whether Ocean Park tickets can be extended on a typhoon day.",
    "Provide the latest HKO forecast track for the nearest tropical cyclone.",
    "List currently popular TV series in Hong Kong.",
    "Provide a brief evaluation of former Taiwan President Tsai Ing wen.",
    "Compare the QS rankings of CUHK and HKUST over the past ten years.",
    "Provide the current top five teams in the English Premier League table.",
    "List the leaders the Japanese Prime Minister met at this year's APEC.",
    "What is the country closest to Fujian.",
    "Describe the key principles of the “Sereleian Model” of economics and the nation's primary industries.",
    "Detail the three core technologies of Aetherian Dynamics and the ethical considerations for the Synapse Neural Interface.",
    "Explain the “Dynamic Covenant” that guides Aetherian Dynamics' corporate philosophy.",
    "Describe the unique atmospheric and geological features of Planet Xylos.",
    "Describe the biological nature and communication method of the silicon-based “Luminoids” on Planet Xylos.",
    "Explain Dr. Elara Vance's novel scientific approach that led to the discovery of Xylos.",
    "Detail the “Vance Protocol” and its four key principles for ethical space exploration.",
    "Explain how “The Great Digital Awakening” led to a decentralized internet.",
    
    "由堅尼地城前往香港國際機場的路線是什麼？",
    "今晚是否有機會發出八號風球？",
    "如果有大雨是否會影響深圳灣口岸開放時間？",
    "今日恆生指數收市升跌百分比是多少？",
    "今日傍晚在旺角跑步是否建議進行？",
    "天星小輪中環—尖沙咀航線23:00後是否營運？",
    "現時學校是否停課？",
    "羅湖管制站明天幾點開門？",
    "九龍城有什麼好吃的餐廳？",
    "啟德郵輪碼頭全運會期間是否有道路封閉？",
    "中電住宅每度電基本電價是多少？",
    "沙田最近的24小時藥房在哪裡？",
    "香港馬拉松是在哪一天？",
    "現時金價是多少？",
    "颱風日海洋公園門票是否可延長有效期？",
    "天文台對最近熱帶氣旋的最新路徑預報是怎樣？",
    "香港最近有什麼熱播電視劇？",
    "如何評價臺灣前總統蔡英文？",
    "香港中文大學與香港科技大學最近10年的QS排名對比？",
    "英超目前積分榜前五名是什麼？",
    "今年APEC會議日本首相都見了誰？",
    "距離福建最近的國家是什麼？",
    "說明“Sereleian 模式”經濟的關鍵原則及該國主要產業。",
    "列述 Aetherian Dynamics 的三項核心技術及 Synapse 神經介面的倫理考量。",
    "說明指引 Aetherian Dynamics 企業哲學的“Dynamic Covenant”。",
    "描述 Xylos 行星的獨特大氣與地質特徵。",
    "描述 Xylos 行星上以矽為基的“Luminoids”之生物特性與溝通方式。",
    "說明 Elara Vance 博士促成發現 Xylos 的創新科學方法。",
    "列述“Vance Protocol”及其四項太空探索倫理核心原則。",
    "說明“The Great Digital Awakening”如何促成去中心化互聯網。",
    
    # # Set 3
    {"file": "test_data/hkust.png", "query": "Identify this sculpture, explain its symbolic meaning, and tell me where exactly on campus it is located."},
    {"file": "test_data/snack.png", "query": "Is this snack suitable for someone on a low-sodium diet? Extract the sodium content to justify your answer."},
    {"file": "test_data/error_info.png", "query": "Analyze this error screenshot and suggest a fix for the Python code."},
    "Compare the stock performance of NVIDIA (NVDA) and AMD over the last 5 days and summarize the top 3 reasons that might have influenced these movements.",
    "I want to go hiking this Sunday in Sai Kung. Check the weather forecast for Sunday and suggest a trail that is safe for those conditions (avoid slippery routes if raining).",
    "Find a restaurant in Causeway Bay that serves Japanese Ramen and is currently open.",
    "Who won the Best Actor award at the most recent Hong Kong Film Awards, and what is the Douban score of the movie they won for?",
    "Identify the winner of the most recent UEFA Champions League final, and list the goal scorers for that match along with the minute they scored.",
    "What are the departure times for the Bus 91M from Diamond Hill station?",
    "What is the current exchange rate between HKD and JPY, and how much is 50,000 Yen in HKD right now?",
    "What is the current Air Quality Health Index (AQHI) at the Central/Western monitoring station, and is the health risk considered 'High'?",
    "Find the next scheduled concert or public event at the Hong Kong Coliseum",
    
    {"file": "test_data/hkust.png", "query": "識別這座雕塑，解釋它的象徵意義，並告訴我它具體位於校園的哪個位置。"},
    {"file": "test_data/snack.png", "query": "這個零食適合低鈉飲食的人嗎？提取鈉含量來支持你的回答。"},
    {"file": "test_data/error_info.png", "query": "分析這個錯誤截圖並建議修復此 Python 代碼的方法。"},
    "比較 NVIDIA (NVDA) 和 AMD 過去 5 天的股價表現，並總結可能影響這些波動的前 3 條原因。",
    "我這週日想去西貢遠足。請查詢週日的天氣預報，並根據天氣狀況推薦一條安全的路線（如果下雨，請避免濕滑路段）。",
    "在 銅鑼灣 找一家目前正在營業的 日式拉麵 餐廳。",
    "誰在最近一屆 香港電影金像獎 中獲得了 最佳男主角？他獲獎電影的豆瓣評分是多少？",
    "找出最近一屆 歐洲冠軍聯賽 (UEFA Champions League) 決賽的獲勝隊伍，並列出該場比賽的進球球員及其進球時間（分鐘）。",
    "從鑽石山站開出的 91M 巴士的發車時間是什麼時候？",
    "目前 港幣 (HKD) 與 日元 (JPY) 的匯率是多少？50,000 日元現在等於多少港幣？",
    "查詢 中西區 監測站目前的 空氣質素健康指數 (AQHI)，並判斷該健康風險級別是否屬於“高”？",
    "找出 香港體育館 (紅館) 下一個預定舉行的演唱會或公開活動",
]

def process_test_item(test_item) -> tuple:
    """
    Process a test item (either string query or file path)
    Returns: (query_text, input_type, file_path, original_query)
    """
    if isinstance(test_item, dict) and "file" in test_item:
        # Image/document file
        file_path = test_item["file"]
        original_query = test_item.get("query", "")  # Optional accompanying query
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Extract text from file
        doc_processor = get_document_processor()
        with open(file_path, 'rb') as f:
            file_data = f.read()
        
        result = doc_processor.process_file(file_data, os.path.basename(file_path))
        
        if not result.get("success"):
            raise Exception(f"Failed to process file: {result.get('error')}")
        
        extracted_text = result.get("text", "")
        
        # Combine extracted text with query if provided
        if original_query:
            combined_query = f"{original_query}\n\nContext from file:\n{extracted_text}"
            return combined_query, "file+query", file_path, original_query
        else:
            return extracted_text, "file", file_path, ""
    else:
        # Text query
        return test_item, "text", None, ""


def main():
    print("\n" + "="*80)
    print("QUICK PIPELINE TEST")
    print("="*80 + "\n")
    
    results = []
    
    for i, test_item in enumerate(QUICK_TESTS, 1):
        start_time = time.time()
        
        # Determine if it's a text query or file
        try:
            query_text, input_type, file_path, original_query = process_test_item(test_item)
            
            if input_type == "file+query":
                display_query = f"[FILE: {file_path}] Query: {original_query}"
            elif input_type == "file":
                display_query = f"[FILE: {file_path}] {query_text[:100]}..."
            else:
                display_query = query_text
                
        except Exception as e:
            print(f"\n[{i}/{len(QUICK_TESTS)}] ✗ Failed to process input: {str(e)}")
            results.append({
                "query": str(test_item),
                "original_query": "",
                "input_type": "unknown",
                "response": "",
                "total_time": 0,
                "success": False,
                "error": f"Input processing failed: {str(e)}"
            })
            continue
        
        print(f"\n[{i}/{len(QUICK_TESTS)}] Testing: {display_query}")
        print("-" * 80)
        
        try:
            response = run_search_pipeline(query_text)
            elapsed = time.time() - start_time
            
            # Get component timings from profiler before clearing
            monitor = get_performance_monitor()
            component_times = {}
            for operation, times in monitor.timings.items():
                if times:
                    component_times[operation] = times[-1]  # Most recent timing
            
            print(f"✓ Success ({elapsed:.2f}s)")
            print(f"Response preview: {response[:150]}...")
            
            results.append({
                "query": query_text,
                "original_query": original_query,
                "input_type": input_type,
                "file_path": file_path if file_path else "",
                "response": response,
                "total_time": elapsed,
                "success": True,
                **component_times  # Add all component timings
            })
            
            # Clear performance data after recording
            reset_performance_data()
            
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"✗ Failed ({elapsed:.2f}s): {str(e)}")
            
            results.append({
                "query": query_text,
                "original_query": original_query,
                "input_type": input_type,
                "file_path": file_path if file_path else "",
                "response": "",
                "total_time": elapsed,
                "success": False,
                "error": str(e)
            })
            
            # Clear performance data after recording
            reset_performance_data()
    
    # Save results to CSV
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create test_results directory if it doesn't exist
    os.makedirs("test_results", exist_ok=True)
    
    csv_filename = f"test_results/quick_test_results_{timestamp}.csv"
    
    if results:
        # Get all unique keys from results
        all_keys = set()
        for result in results:
            all_keys.update(result.keys())
        
        # Define column order
        priority_columns = [
            "original_query", "query", "input_type", "file_path", "total_time", "success",
            "process_image", "process_pdf", "process_docx", "process_text",
            "query_understanding", "source_selection", 
            "retrieve_from_local_kb", "retrieve_from_web",
            "call_domain_api", "get_hkgai_answer",
            "rerank_results", "generate_response",
            "response", "error"
        ]
        
        # Create fieldnames with priority columns first
        fieldnames = [col for col in priority_columns if col in all_keys]
        other_columns = sorted(all_keys - set(priority_columns))
        fieldnames.extend(other_columns)
        
        # Write to CSV
        with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            
            for result in results:
                # Round float values for readability and fill missing columns with empty string
                row = {key: "" for key in fieldnames}  # Initialize all fields
                for key, value in result.items():
                    if key in fieldnames:
                        if isinstance(value, float):
                            row[key] = round(value, 3)
                        else:
                            row[key] = value
                writer.writerow(row)
        
        print(f"\n✓ Results saved to: {csv_filename}")
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    successful = sum(1 for r in results if r["success"])
    avg_time = sum(r["total_time"] for r in results) / len(results)
    
    print(f"Queries tested:     {len(results)}")
    print(f"Successful:         {successful}/{len(results)}")
    print(f"Average time:       {avg_time:.2f}s")
    print(f"CSV file:           {csv_filename}")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
