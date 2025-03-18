import os
import json
from openai import OpenAI
from collections import defaultdict
from openai import OpenAI
from dotenv import load_dotenv, find_dotenv

# 加载环境变量
_ = load_dotenv(find_dotenv()) 
openai_api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=openai_api_key)

# 商品的数据文件
products_file = 'products_zh.json'

# 分隔符
delimiter = "####"


# 使用 ChatCompletion 接口
def get_completion_from_messages(messages, 
                                 model ="gpt-4o-mini", 
                                 temperature=0, 
                                 max_tokens=1000):
    '''
    封装一个支持更多参数的自定义访问 gpt-4o-mini的函数

    参数: 
    messages: 这是一个消息列表，每个消息都是一个字典，包含 role(角色）和 content(内容)。角色可以是'system'、'user' 或 'assistant’，内容是角色的消息。
    model: 调用的模型，默认为gpt-4o-mini(ChatGPT)
    temperature: 这决定模型输出的随机程度，默认为0，表示输出将非常确定。增加温度会使输出更随机。
    max_tokens: 这决定模型输出的最大的 token 数。
    '''
    response = client.chat.completions.create(
        model= model,
        messages=messages,
        temperature=temperature, # 这决定模型输出的随机程度
        max_tokens=max_tokens, # 这决定模型输出的最大的 token 数
    )
    return response.choices[0].message.content


# 获取商品数据
def get_products():
    with open(products_file, 'r') as file:
        products = json.load(file)
    return products


# 获取商品和目录
def get_products_and_category():
    products = get_products()
    products_by_category = defaultdict(list)
    for product_name, product_info in products.items():
        category = product_info.get('类别')
        if category:
            products_by_category[category].append(product_info.get('名称'))
    
    return dict(products_by_category)

# 从用户问题中抽取商品和类别
def find_category_and_product(user_input, products_and_category):
    delimiter = "####"
    system_message = f"""
    你将提供服务查询。
    服务查询将使用{delimiter}字符分隔。

    仅输出一个 Python 对象列表，其中每个对象具有以下格式：
        'category': <必须是在下面的允许产品列表中找到的类别>;
        'products': <必须是在下面的允许产品列表中找到的产品>;

    类别和产品必须在客户输入中找到。
    如果客户输入提及了类别，则将其与允许产品列表中的所有正确产品相关联。
    如果客户输入提及了产品，则将其与允许类别中的正确类别相关联。
    如果未找到符合要求的产品或类别，则输出空列表。

    仅输出 Python 对象列表，不包含其他字符信息。

    允许的产品以JSON格式提供。
    每个项的键表示类别。
    每个项的值是该类别中的产品列表。
    允许的产品：{products_and_category}
    
    """
    messages =  [  
    {'role':'system', 'content': system_message},    
    {'role':'user', 'content': f"{delimiter}{user_input}{delimiter}"},  
    ] 
    return get_completion_from_messages(messages)


# 将输入的字符串转换为 Python 列表
def read_string_to_list(input_string):
    """
    将输入的字符串转换为 Python 列表。

    参数:
    input_string: 输入的字符串，应为有效的 JSON 格式。

    返回:
    list 或 None: 如果输入字符串有效，则返回对应的 Python 列表，否则返回 None。
    """
    if input_string is None:
        return None

    try:
        # 将输入字符串中的单引号替换为双引号，以满足 JSON 格式的要求
        input_string = input_string.replace("'", "\"")  
        data = json.loads(input_string)
        return data
    except json.JSONDecodeError:
        print("Error: Invalid JSON string")
        return None   


# 根据产品名称获取产品
def get_product_by_name(name):
    """
    根据产品名称获取产品

    参数:
    name: 产品名称
    """
    products = get_products()
    return products.get(name, None)


# 根据类别获取产品
def get_products_by_category(category):
    """
    根据类别获取产品

    参数:
    category: 产品类别
    """
    products = get_products()
    return [product for product in products.values() if product["类别"] == category]  



# 根据输入的数据列表生成包含产品或类别信息的字符串
def generate_output_string(data_list):
    """
    根据输入的数据列表生成包含产品或类别信息的字符串。

    参数:
    data_list: 包含字典的列表，每个字典都应包含 "products" 或 "category" 的键。

    返回:
    output_string: 包含产品或类别信息的字符串。
    """
    # 初始化输出字符串
    output_string = ""

    if data_list is None:
        return output_string

    for data in data_list:
        try:
            if "products" in data:
                products_list = data["products"]
                for product_name in products_list:
                    product = get_product_by_name(product_name)
                    if product:
                        output_string += json.dumps(product, indent=4, ensure_ascii=False) + "\n"
                    else:
                        print(f"错误: 商品 '{product_name}' 未找到")
            elif "category" in data:
                category_name = data["category"]
                category_products = get_products_by_category(category_name)
                for product in category_products:
                    output_string += json.dumps(product, indent=4, ensure_ascii=False) + "\n"
            else:
                print("错误：非法的商品格式")
        
        except Exception as e:
            print(f"错误: {e}")

    return output_string 
       