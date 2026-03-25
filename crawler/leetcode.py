import requests
import json
import csv
# 禁用 SSL 证书验证警告（可选，解决 requests 证书报错问题）
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# ------------------ 核心配置 ------------------
# LeetCode 题目列表接口（可获取题目基础信息）
LIST_API_URL = "https://leetcode.cn/api/problems/all/"
# 保存数据的 JSON 文件
OUTPUT_JSON = "leetcode_problems_info.json"
# 保存数据的 CSV 文件
OUTPUT_CSV = "leetcode_problems_info.csv"
# 请求头模拟浏览器，避免被拦截
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
}


# ------------------ 功能函数 ------------------
def fetch_problem_list():
    """获取 LeetCode 题目列表数据（通过官方 API）"""
    try:
        response = requests.get(
            LIST_API_URL,
            headers=HEADERS,
            verify=False  # 关闭 SSL 验证（解决证书问题）
        )
        if response.status_code == 200:
            return response.json()
        print(f"请求失败，状态码: {response.status_code}")
        return None
    except Exception as e:
        print(f"请求出错: {e}")
        return None


def parse_problem_info(problem_data):
    """解析题目数据，提取所需字段"""
    parsed = []
    # 难度映射关系：1->简单，2->中等，3->困难
    difficulty_map = {1: "easy", 2: "medium", 3: "hard"}

    for item in problem_data.get("stat_status_pairs", []):
        stat = item["stat"]
        # 提取核心字段
        info = {
            "question_id": stat["question_id"],
            "pass_rate": stat.get("total_acs") / stat.get("total_submitted") if stat.get("total_submitted") else 0,
            # 通过率（AC数/提交数）
            "solution_url": f"https://leetcode.cn/problems/{stat['question__title_slug']}/solution/",  # 题解链接
            "resource_id": 5,
            "question_url": f"https://leetcode.cn/problems/{stat['question__title_slug']}/",  # 题目链接
            "name": stat["question__title"],  # 题目名称
            "difficulty": difficulty_map.get(item["difficulty"]["level"], "Unknown"),
        }
        # 通过率转百分比（保留两位小数）
        info["pass_rate"] = f"{info['pass_rate'] * 100:.2f}%"
        parsed.append(info)
    return parsed


def save_to_json(data, filename):
    """将数据保存为 JSON 文件"""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"已保存 {len(data)} 条数据到 {filename}")


def save_to_csv(data, filename):
    """将数据保存为 CSV 文件"""
    if not data:
        print("没有数据可保存")
        return

    # 提取 CSV 文件的表头（使用字典的键）
    fieldnames = data[0].keys()

    with open(filename, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    print(f"已保存 {len(data)} 条数据到 {filename}")


# ------------------ 主流程 ------------------
def main():
    # 1. 获取题目列表数据
    problem_list = fetch_problem_list()
    if not problem_list:
        print("获取题目列表失败，程序终止")
        return

    # 2. 解析需要的字段
    parsed_info = parse_problem_info(problem_list)

    # 3. 保存到 JSON 文件
    save_to_json(parsed_info, OUTPUT_JSON)

    # 4. 保存到 CSV 文件
    save_to_csv(parsed_info, OUTPUT_CSV)


if __name__ == "__main__":
    main()