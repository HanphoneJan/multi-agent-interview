import json
from learning_manager.job_search import search_jobs
from learning_manager.ai_suggestion import SparkAIHTTPEngine

def generate_career_suggestion(address: str, university: str, major: str, career_direction: str) -> dict:
    """
    获取职业规划建议，包括职位搜索结果和AI分析建议

    :param address: 城市名称
    :param university: 毕业院校
    :param major: 专业
    :param career_direction: 职业方向
    :return: 包含职位信息和AI建议的字典
    """
    # 1. 调用job_search获取职位信息
    print(f"正在搜索{address}地区{major}专业和{career_direction}方向的职位...")
    jobs = search_jobs(address, major, career_direction)

    # 2. 准备AI提示词
    prompt = f"""
    请根据以下用户信息和职位数据，提供专业的职业规划建议：

    用户背景：
    - 所在城市：{address}
    - 毕业院校：{university}
    - 所学专业：{major}
    - 职业方向兴趣：{career_direction}

    相关职位搜索结果（共{len(jobs)}条）：
    {json.dumps(jobs, ensure_ascii=False, indent=2)}

    请从以下方面提供详细建议：
    1. 职业发展路径：根据用户专业和兴趣方向，建议适合的发展路径
    2. 技能提升建议：针对目标职位所需的技能差距，提出学习建议
    3. 城市选择分析：分析当前城市与职位匹配度，是否需要考虑其他城市
    4. 薪资预期：根据搜索结果，给出合理的薪资预期范围
    5. 长期规划：3-5年的职业发展建议

    要求：
    - 分析具体，结合搜索结果中的职位要求
    - 建议实用可操作
    - 分点列出，条理清晰
    - 适当鼓励，保持积极语气
    """

    # 3. 调用AI接口获取建议
    print("正在获取AI职业规划建议...")
    ai_engine = SparkAIHTTPEngine()
    response = ai_engine.generate_response(
        user_query=prompt,
        temperature=0.7,
        max_tokens=1500
    )

    if not response["success"]:
        print(f"获取AI建议失败: {response['error']}")
        ai_advice = "抱歉，获取职业规划建议时出现错误。"
    else:
        ai_advice = response["content"]

    # 4. 整理返回结果
    result = {
        "user_info": {
            "address": address,
            "university": university,
            "major": major,
            "career_direction": career_direction
        },
        "job_results": jobs,
        "career_advice": ai_advice
    }

    return result


if __name__ == "__main__":
    # 测试代码
    test_data = {
        "address": "广州",
        "university": "电子科技大学",
        "major": "软件工程",
        "career_direction": "具身智能"
    }

    print("开始职业规划分析...")
    result = generate_career_suggestion(
        address=test_data["address"],
        university=test_data["university"],
        major=test_data["major"],
        career_direction=test_data["career_direction"]
    )

    print("\n=== 职位搜索结果 ===")
    for i, job in enumerate(result["job_results"], 1):
        print(f"{i}. {job['职位']} - {job['公司']} ({job['薪资']})")

    print("\n=== AI职业规划建议 ===")
    print(result["career_advice"])