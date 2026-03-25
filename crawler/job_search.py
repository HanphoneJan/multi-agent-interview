# 导入自动化
from DrissionPage import ChromiumPage, ChromiumOptions
import csv
import time

citys = {'上海': 538, '北京': 530, '广州': 763, '深圳': 765, '天津': 531,
         '武汉': 736, '西安': 854, '成都': 801, '南京': 635, '杭州': 653,
         '重庆': 551, '厦门': 682, '全国': 489}


def search_jobs(address, major, career_direction):
    """
    搜索职位信息并保存到CSV文件，返回两次搜索各前5条合并的10条结果
    :param address: 城市名称，如'上海'
    :param major: 专业关键词，如'数据'
    :param career_direction: 职业方向关键词，如'设计'
    :return: 合并后的职位信息列表
    """
    # 获取城市编码，如果找不到则使用全国编码
    city_code = citys.get(address, citys['全国'])

    # 准备CSV文件
    f = open('jobs.csv', mode='w', encoding='utf-8', newline='')
    csv_writer = csv.DictWriter(f, fieldnames=[
        '职位',
        '薪资',
        '公司',
        '城市',
        '区域',
        '学历',
        '领域',
        '规模',
        '链接',
        '搜索条件'  # 记录是哪种搜索类型的结果
    ])
    csv_writer.writeheader()
    # 创建 ChromiumOptions 对象
    co = ChromiumOptions()

    # 不能使用无头模式
    # co.headless()
    # co.set_argument('--no-sandbox')

    dp = ChromiumPage(co)
    dp.listen.start('/search/positions')

    # 构建基础搜索URL
    base_search_url = f'https://www.zhaopin.com/sou/jl{city_code}/p2'

    all_jobs = []  # 存储所有合并的结果

    # 先处理专业关键词搜索
    print(f'正在搜索类型: 专业, 关键词: {major}')
    dp.get(base_search_url)
    time.sleep(2)
    dp.ele('css:.query-search__content-input').input(major)
    dp.ele('css:.query-search__content-button').click()

    dp.scroll.to_bottom()
    # 点击上一页
    dp.ele('css:.soupager__btn').click()
    dp.scroll.to_bottom()
    print('正在采集专业关键词第1页数据')
    resp = dp.listen.wait()

    json_data = resp.response.body
    job_list = json_data['data']['list']
    # 取前5条结果
    major_jobs = job_list[:5]
    for index in major_jobs:
        dit = {
            '职位': index['name'],
            '薪资': index['salary60'],
            '公司': index['companyName'],
            '城市': index['workCity'],
            '区域': index['cityDistrict'],
            '学历': index['education'],
            '领域': index['industryName'],
            '规模': index['companySize'],
            '链接': index['companyUrl'],
            '搜索条件': '专业'
        }
        csv_writer.writerow(dit)
        all_jobs.append(dit)
        print(dit)

    # 再处理职业方向关键词搜索
    print(f'正在搜索类型: 方向, 关键词: {career_direction}')
    dp.get(base_search_url)
    time.sleep(2)
    dp.ele('css:.query-search__content-input').input(career_direction)
    dp.ele('css:.query-search__content-button').click()

    dp.scroll.to_bottom()
    # 点击上一页
    dp.ele('css:.soupager__btn').click()
    dp.scroll.to_bottom()
    print('正在采集职业方向关键词第1页数据')
    resp = dp.listen.wait()

    json_data = resp.response.body
    job_list = json_data['data']['list']
    # 取前5条结果
    direction_jobs = job_list[:5]
    for index in direction_jobs:
        dit = {
            '职位': index['name'],
            '薪资': index['salary60'],
            '公司': index['companyName'],
            '城市': index['workCity'],
            '区域': index['cityDistrict'],
            '学历': index['education'],
            '领域': index['industryName'],
            '规模': index['companySize'],
            '链接': index['companyUrl'],
            '搜索条件': '职业意向'
        }
        csv_writer.writerow(dit)
        all_jobs.append(dit)
        print(dit)

    f.close()
    return all_jobs  # 返回合并后的结果


if __name__ == '__main__':
    # 测试代码
    results = search_jobs('北京', '数据', '设计')
    print(f'\n合并后的10条结果: {results}')