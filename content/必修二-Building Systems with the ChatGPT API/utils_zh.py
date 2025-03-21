import os
import json
from openai import OpenAI
from collections import defaultdict


from openai import OpenAI

from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv()) 

openai_api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=openai_api_key)

# 商品和目录的数据文件
products_file = 'products_zh.json'
categories_file = 'categories.json'

# 分隔符
delimiter = "####"
# 第二步（抽取商品）系统信息文本
step_2_system_message_content = f"""
    你将提供服务查询。
    服务查询将使用{delimiter}字符分隔。

    仅输出一个 Python 对象列表，其中每个对象具有以下格式：
        'category': <计算机和笔记本电脑、智能手机和配件、电视和家庭影院系统、游戏机和配件、音频设备、相机和摄像机>中的一个,
    或者
        'products': <必须是在下面的允许产品列表中找到的产品>

    类别和产品必须在客户输入中找到。
    如果提及了产品，则必须将其与允许产品列表中的正确类别相关联。
    如果未找到产品或类别，则输出空列表。

    允许的产品：

    计算机和笔记本电脑类别：
    TechPro Ultrabook
    BlueWave Gaming Laptop
    PowerLite Convertible
    TechPro Desktop
    BlueWave Chromebook

    智能手机和配件类别：
    SmartX ProPhone
    MobiTech PowerCase
    SmartX MiniPhone
    MobiTech Wireless Charger
    SmartX EarBuds

    电视和家庭影院系统类别：
    CineView 4K TV
    SoundMax Home Theater
    CineView 8K TV
    SoundMax Soundbar
    CineView OLED TV

    游戏机和配件类别：
    GameSphere X
    ProGamer Controller
    GameSphere Y
    ProGamer Racing Wheel
    GameSphere VR Headset

    音频设备类别：
    AudioPhonic Noise-Canceling Headphones
    WaveSound Bluetooth Speaker
    AudioPhonic True Wireless Earbuds
    WaveSound Soundbar
    AudioPhonic Turntable

    相机和摄像机类别：
    FotoSnap DSLR Camera
    ActionCam 4K
    FotoSnap Mirrorless Camera
    ZoomMaster Camcorder
    FotoSnap Instant Camera

    仅输出 Python 对象列表，不包含其他字符信息。
"""

step_2_system_message = {'role':'system', 'content': step_2_system_message_content}    

# 第四步（生成用户回答）的系统信息
step_4_system_message_content = f"""
    您是一家大型电子商店的客服助理。
    请以友好和乐于助人的口吻回答用户的问题，并尽量简洁明了。
    解答用户的问题后，请确保向用户提出相关的后续问题。
"""

step_4_system_message = {'role':'system', 'content': step_4_system_message_content}    

# 第六步（验证模型回答）的系统信息
step_6_system_message_content = f"""
    您是一个助理，用于评估客服代理的回复是否充分回答了客户问题，\
    并验证助理从产品信息中引用的所有事实是否正确。 
    产品信息、用户和客服代理的信息将使用三个反引号（即 ```)\
    进行分隔。 
    请以 Y 或 N 的字符形式进行回复，不要包含标点符号：\
    Y - 如果输出充分回答了问题并且回复正确地使用了产品信息\
    N - 其他情况。

    仅输出单个字母。
"""

step_6_system_message = {'role':'system', 'content': step_6_system_message_content}    

# 使用 ChatCompletion 接口
def get_completion_from_messages(messages, 
                                 model ="gpt-4o-mini", 
                                 temperature=0, 
                                 max_tokens=500):
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

# 获取目录数据
def get_categories():
    with open(categories_file, 'r') as file:
            categories = json.load(file)
    return categories

# 获取商品数据
def get_products():
    with open(products_file, 'r') as file:
        products = json.load(file)
    return products

# 获取商品列表
def get_product_list():
    """
    具体原理参见第四节课
    """
    products = get_products()
    product_list = []
    for product in products.keys():
        product_list.append(product)
    
    return product_list




# 获取商品和目录
def get_products_and_category():
    """
    具体原理参见第五节课
    """
    products = get_products()
    products_by_category = defaultdict(list)
    for product_name, product_info in products.items():
        category = product_info.get('category')
        if category:
            products_by_category[category].append(product_info.get('name'))
    
    return dict(products_by_category)


# 从用户问题中抽取商品和类别
def find_category_and_product(user_input,products_and_category):
    delimiter = "####"
    system_message = f"""
    您将获得客户服务查询。
    客户服务查询将使用{delimiter}字符分隔。
    输出一个可解析的Python列表，列表每一个元素是一个JSON对象，每个对象具有以下格式：
    'category': <包括以下几个类别：Computers and Laptops，Smartphones and Accessories，Televisions and Home Theater Systems，Gaming Consoles and Accessories，Audio Equipment，Cameras and Camcorders>
    以及
    'products': <必须是下面的允许产品列表中找到的产品列表>

    其中类别和产品必须在客户服务查询中找到。
    如果提到了产品，则必须将其与允许产品列表中的正确类别关联。
    如果未找到任何产品或类别，则输出一个空列表。
    除了列表外，不要输出其他任何信息！

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

# 相比上一个函数，可获取的商品直接在 template 中限定
def find_category_and_product_only(user_input,products_and_category):
    delimiter = "####"
    system_message = f"""
您将获得客户服务查询。
客户服务查询将使用{delimiter}字符作为分隔符。
请仅输出一个可解析的Python列表，列表每一个元素是一个JSON对象，每个对象具有以下格式：
'category': <包括以下几个类别：Computers and Laptops、Smartphones and Accessories、Televisions and Home Theater Systems、Gaming Consoles and Accessories、Audio Equipment、Cameras and Camcorders>,
以及
'products': <必须是下面的允许产品列表中找到的产品列表>

类别和产品必须在客户服务查询中找到。
如果提到了某个产品，它必须与允许产品列表中的正确类别关联。
如果未找到任何产品或类别，则输出一个空列表。
除了列表外，不要输出其他任何信息！

允许的产品：

Computers and Laptops category:
TechPro Ultrabook
BlueWave Gaming Laptop
PowerLite Convertible
TechPro Desktop
BlueWave Chromebook

Smartphones and Accessories category:
SmartX ProPhone
MobiTech PowerCase
SmartX MiniPhone
MobiTech Wireless Charger
SmartX EarBuds

Televisions and Home Theater Systems category:
CineView 4K TV
SoundMax Home Theater
CineView 8K TV
SoundMax Soundbar
CineView OLED TV

Gaming Consoles and Accessories category:
GameSphere X
ProGamer Controller
GameSphere Y
ProGamer Racing Wheel
GameSphere VR Headset

Audio Equipment category:
AudioPhonic Noise-Canceling Headphones
WaveSound Bluetooth Speaker
AudioPhonic True Wireless Earbuds
WaveSound Soundbar
AudioPhonic Turntable

Cameras and Camcorders category:
FotoSnap DSLR Camera
ActionCam 4K
FotoSnap Mirrorless Camera
ZoomMaster Camcorder
FotoSnap Instant Camera
    
只输出对象列表，不包含其他内容。
    """
    messages =  [  
    {'role':'system', 'content': system_message},    
    {'role':'user', 'content': f"{delimiter}{user_input}{delimiter}"},  
    ] 
    return get_completion_from_messages(messages)

# 从问题中抽取商品
def get_products_from_query(user_msg):
    """
    代码来自于第五节课
    """
    products_and_category = get_products_and_category()
    delimiter = "####"
    system_message = f"""
    您将获得客户服务查询。
    客户服务查询将使用{delimiter}字符作为分隔符。
    请仅输出一个可解析的Python列表，列表每一个元素是一个JSON对象，每个对象具有以下格式：
    'category': <包括以下几个类别：Computers and Laptops、Smartphones and Accessories、Televisions and Home Theater Systems、Gaming Consoles and Accessories、Audio Equipment、Cameras and Camcorders>,
    以及
    'products': <必须是下面的允许产品列表中找到的产品列表>

    类别和产品必须在客户服务查询中找到。
    如果提到了某个产品，它必须与允许产品列表中的正确类别关联。
    如果未找到任何产品或类别，则输出一个空列表。
    除了列表外，不要输出其他任何信息！

    允许的产品以JSON格式提供。
    每个项目的键表示类别。
    每个项目的值是该类别中的产品列表。

    以下是允许的产品：{products_and_category}

    """
    
    messages =  [  
    {'role':'system', 'content': system_message},    
    {'role':'user', 'content': f"{delimiter}{user_msg}{delimiter}"},  
    ] 
    category_and_product_response = get_completion_from_messages(messages)
    
    return category_and_product_response


# 商品信息的搜索
def get_product_by_name(name):
    products = get_products()
    return products.get(name, None)

def get_products_by_category(category):
    products = get_products()
    return [product for product in products.values() if product["category"] == category]

def get_mentioned_product_info(data_list):
    """
    具体原理参见第五、六节课
    """
    product_info_l = []

    if data_list is None:
        return product_info_l

    for data in data_list:
        try:
            if "products" in data:
                products_list = data["products"]
                for product_name in products_list:
                    product = get_product_by_name(product_name)
                    if product:
                        product_info_l.append(product)
                    else:
                        print(f"错误: 商品 '{product_name}' 未找到")
            elif "category" in data:
                category_name = data["category"]
                category_products = get_products_by_category(category_name)
                for product in category_products:
                    product_info_l.append(product)
            else:
                print("错误：非法的商品格式")
        except Exception as e:
            print(f"Error: {e}")

    return product_info_l


# 以下函数原理参见第五节课
def read_string_to_list(input_string):
    if input_string is None:
        return None

    try:
        input_string = input_string.replace("'", "\"")  # Replace single quotes with double quotes for valid JSON
        data = json.loads(input_string)
        return data
    except json.JSONDecodeError:
        print(input_string)
        print("错误：非法的 Json 格式")
        return None

def generate_output_string(data_list):
    output_string = ""

    if data_list is None:
        return output_string
    # print(data_list)
    for data in data_list:
        try:
            if "products" in data:
                # print(data)
                products_list = data["products"]
                for product_name in products_list:
                    product = get_product_by_name(product_name)
                    if product:
                        output_string += json.dumps(product, indent=4) + "\n"
                    else:
                        print(f"错误: 商品 '{product_name}' 没有找到")
            elif "category" in data:
                category_name = data["category"]
                category_products = get_products_by_category(category_name)
                for product in category_products:
                    output_string += json.dumps(product, indent=4) + "\n"
            else:
                print("错误：非法的商品格式")
        except Exception as e:
            print(f"Error: {e}")

    return output_string

# Example usage:
#product_information_for_user_message_1 = generate_output_string(category_and_product_list)
#print(product_information_for_user_message_1)
# 回答用户问题
def answer_user_msg(user_msg,product_info):
    """
    代码参见第五节课
    """
    delimiter = "####"
    system_message = f"""
    您是一家大型电子商店的客户服务助理。\
    请用友好和乐于助人的口吻回答问题，提供简洁明了的答案。\
    确保向用户提出相关的后续问题。
    """
    # user_msg = f"""
    # tell me about the smartx pro phone and the fotosnap camera, the dslr one. Also what tell me about your tvs"""
    messages =  [  
    {'role':'system', 'content': system_message},   
    {'role':'user', 'content': f"{delimiter}{user_msg}{delimiter}"},  
    {'role':'assistant', 'content': f"相关产品信息:\n{product_info}"},   
    ] 
    response = get_completion_from_messages(messages)
    return response

# 创建并存入商品数据
def create_products():
    # product information
    # fun fact: all these products are fake and were generated by a language model
    products = {
        "TechPro Ultrabook": {
            "name": "TechPro Ultrabook",
            "category": "Computers and Laptops",
            "brand": "TechPro",
            "model_number": "TP-UB100",
            "warranty": "1 year",
            "rating": 4.5,
            "features": ["13.3-inch display", "8GB RAM", "256GB SSD", "Intel Core i5 processor"],
            "description": "A sleek and lightweight ultrabook for everyday use.",
            "price": 799.99
        },
        "BlueWave Gaming Laptop": {
            "name": "BlueWave Gaming Laptop",
            "category": "Computers and Laptops",
            "brand": "BlueWave",
            "model_number": "BW-GL200",
            "warranty": "2 years",
            "rating": 4.7,
            "features": ["15.6-inch display", "16GB RAM", "512GB SSD", "NVIDIA GeForce RTX 3060"],
            "description": "A high-performance gaming laptop for an immersive experience.",
            "price": 1199.99
        },
        "PowerLite Convertible": {
            "name": "PowerLite Convertible",
            "category": "Computers and Laptops",
            "brand": "PowerLite",
            "model_number": "PL-CV300",
            "warranty": "1 year",
            "rating": 4.3,
            "features": ["14-inch touchscreen", "8GB RAM", "256GB SSD", "360-degree hinge"],
            "description": "A versatile convertible laptop with a responsive touchscreen.",
            "price": 699.99
        },
        "TechPro Desktop": {
            "name": "TechPro Desktop",
            "category": "Computers and Laptops",
            "brand": "TechPro",
            "model_number": "TP-DT500",
            "warranty": "1 year",
            "rating": 4.4,
            "features": ["Intel Core i7 processor", "16GB RAM", "1TB HDD", "NVIDIA GeForce GTX 1660"],
            "description": "A powerful desktop computer for work and play.",
            "price": 999.99
        },
        "BlueWave Chromebook": {
            "name": "BlueWave Chromebook",
            "category": "Computers and Laptops",
            "brand": "BlueWave",
            "model_number": "BW-CB100",
            "warranty": "1 year",
            "rating": 4.1,
            "features": ["11.6-inch display", "4GB RAM", "32GB eMMC", "Chrome OS"],
            "description": "A compact and affordable Chromebook for everyday tasks.",
            "price": 249.99
        },
        "SmartX ProPhone": {
            "name": "SmartX ProPhone",
            "category": "Smartphones and Accessories",
            "brand": "SmartX",
            "model_number": "SX-PP10",
            "warranty": "1 year",
            "rating": 4.6,
            "features": ["6.1-inch display", "128GB storage", "12MP dual camera", "5G"],
            "description": "A powerful smartphone with advanced camera features.",
            "price": 899.99
        },
        "MobiTech PowerCase": {
            "name": "MobiTech PowerCase",
            "category": "Smartphones and Accessories",
            "brand": "MobiTech",
            "model_number": "MT-PC20",
            "warranty": "1 year",
            "rating": 4.3,
            "features": ["5000mAh battery", "Wireless charging", "Compatible with SmartX ProPhone"],
            "description": "A protective case with built-in battery for extended usage.",
            "price": 59.99
        },
        "SmartX MiniPhone": {
            "name": "SmartX MiniPhone",
            "category": "Smartphones and Accessories",
            "brand": "SmartX",
            "model_number": "SX-MP5",
            "warranty": "1 year",
            "rating": 4.2,
            "features": ["4.7-inch display", "64GB storage", "8MP camera", "4G"],
            "description": "A compact and affordable smartphone for basic tasks.",
            "price": 399.99
        },
        "MobiTech Wireless Charger": {
            "name": "MobiTech Wireless Charger",
            "category": "Smartphones and Accessories",
            "brand": "MobiTech",
            "model_number": "MT-WC10",
            "warranty": "1 year",
            "rating": 4.5,
            "features": ["10W fast charging", "Qi-compatible", "LED indicator", "Compact design"],
            "description": "A convenient wireless charger for a clutter-free workspace.",
            "price": 29.99
        },
        "SmartX EarBuds": {
            "name": "SmartX EarBuds",
            "category": "Smartphones and Accessories",
            "brand": "SmartX",
            "model_number": "SX-EB20",
            "warranty": "1 year",
            "rating": 4.4,
            "features": ["True wireless", "Bluetooth 5.0", "Touch controls", "24-hour battery life"],
            "description": "Experience true wireless freedom with these comfortable earbuds.",
            "price": 99.99
        },

        "CineView 4K TV": {
            "name": "CineView 4K TV",
            "category": "Televisions and Home Theater Systems",
            "brand": "CineView",
            "model_number": "CV-4K55",
            "warranty": "2 years",
            "rating": 4.8,
            "features": ["55-inch display", "4K resolution", "HDR", "Smart TV"],
            "description": "A stunning 4K TV with vibrant colors and smart features.",
            "price": 599.99
        },
        "SoundMax Home Theater": {
            "name": "SoundMax Home Theater",
            "category": "Televisions and Home Theater Systems",
            "brand": "SoundMax",
            "model_number": "SM-HT100",
            "warranty": "1 year",
            "rating": 4.4,
            "features": ["5.1 channel", "1000W output", "Wireless subwoofer", "Bluetooth"],
            "description": "A powerful home theater system for an immersive audio experience.",
            "price": 399.99
        },
        "CineView 8K TV": {
            "name": "CineView 8K TV",
            "category": "Televisions and Home Theater Systems",
            "brand": "CineView",
            "model_number": "CV-8K65",
            "warranty": "2 years",
            "rating": 4.9,
            "features": ["65-inch display", "8K resolution", "HDR", "Smart TV"],
            "description": "Experience the future of television with this stunning 8K TV.",
            "price": 2999.99
        },
        "SoundMax Soundbar": {
            "name": "SoundMax Soundbar",
            "category": "Televisions and Home Theater Systems",
            "brand": "SoundMax",
            "model_number": "SM-SB50",
            "warranty": "1 year",
            "rating": 4.3,
            "features": ["2.1 channel", "300W output", "Wireless subwoofer", "Bluetooth"],
            "description": "Upgrade your TV's audio with this sleek and powerful soundbar.",
            "price": 199.99
        },
        "CineView OLED TV": {
            "name": "CineView OLED TV",
            "category": "Televisions and Home Theater Systems",
            "brand": "CineView",
            "model_number": "CV-OLED55",
            "warranty": "2 years",
            "rating": 4.7,
            "features": ["55-inch display", "4K resolution", "HDR", "Smart TV"],
            "description": "Experience true blacks and vibrant colors with this OLED TV.",
            "price": 1499.99
        },

        "GameSphere X": {
            "name": "GameSphere X",
            "category": "Gaming Consoles and Accessories",
            "brand": "GameSphere",
            "model_number": "GS-X",
            "warranty": "1 year",
            "rating": 4.9,
            "features": ["4K gaming", "1TB storage", "Backward compatibility", "Online multiplayer"],
            "description": "A next-generation gaming console for the ultimate gaming experience.",
            "price": 499.99
        },
        "ProGamer Controller": {
            "name": "ProGamer Controller",
            "category": "Gaming Consoles and Accessories",
            "brand": "ProGamer",
            "model_number": "PG-C100",
            "warranty": "1 year",
            "rating": 4.2,
            "features": ["Ergonomic design", "Customizable buttons", "Wireless", "Rechargeable battery"],
            "description": "A high-quality gaming controller for precision and comfort.",
            "price": 59.99
        },
        "GameSphere Y": {
            "name": "GameSphere Y",
            "category": "Gaming Consoles and Accessories",
            "brand": "GameSphere",
            "model_number": "GS-Y",
            "warranty": "1 year",
            "rating": 4.8,
            "features": ["4K gaming", "500GB storage", "Backward compatibility", "Online multiplayer"],
            "description": "A compact gaming console with powerful performance.",
            "price": 399.99
        },
        "ProGamer Racing Wheel": {
            "name": "ProGamer Racing Wheel",
            "category": "Gaming Consoles and Accessories",
            "brand": "ProGamer",
            "model_number": "PG-RW200",
            "warranty": "1 year",
            "rating": 4.5,
            "features": ["Force feedback", "Adjustable pedals", "Paddle shifters", "Compatible with GameSphere X"],
            "description": "Enhance your racing games with this realistic racing wheel.",
            "price": 249.99
        },
        "GameSphere VR Headset": {
            "name": "GameSphere VR Headset",
            "category": "Gaming Consoles and Accessories",
            "brand": "GameSphere",
            "model_number": "GS-VR",
            "warranty": "1 year",
            "rating": 4.6,
            "features": ["Immersive VR experience", "Built-in headphones", "Adjustable headband", "Compatible with GameSphere X"],
            "description": "Step into the world of virtual reality with this comfortable VR headset.",
            "price": 299.99
        },

        "AudioPhonic Noise-Canceling Headphones": {
            "name": "AudioPhonic Noise-Canceling Headphones",
            "category": "Audio Equipment",
            "brand": "AudioPhonic",
            "model_number": "AP-NC100",
            "warranty": "1 year",
            "rating": 4.6,
            "features": ["Active noise-canceling", "Bluetooth", "20-hour battery life", "Comfortable fit"],
            "description": "Experience immersive sound with these noise-canceling headphones.",
            "price": 199.99
        },
        "WaveSound Bluetooth Speaker": {
            "name": "WaveSound Bluetooth Speaker",
            "category": "Audio Equipment",
            "brand": "WaveSound",
            "model_number": "WS-BS50",
            "warranty": "1 year",
            "rating": 4.5,
            "features": ["Portable", "10-hour battery life", "Water-resistant", "Built-in microphone"],
            "description": "A compact and versatile Bluetooth speaker for music on the go.",
            "price": 49.99
        },
        "AudioPhonic True Wireless Earbuds": {
            "name": "AudioPhonic True Wireless Earbuds",
            "category": "Audio Equipment",
            "brand": "AudioPhonic",
            "model_number": "AP-TW20",
            "warranty": "1 year",
            "rating": 4.4,
            "features": ["True wireless", "Bluetooth 5.0", "Touch controls", "18-hour battery life"],
            "description": "Enjoy music without wires with these comfortable true wireless earbuds.",
            "price": 79.99
        },
        "WaveSound Soundbar": {
            "name": "WaveSound Soundbar",
            "category": "Audio Equipment",
            "brand": "WaveSound",
            "model_number": "WS-SB40",
            "warranty": "1 year",
            "rating": 4.3,
            "features": ["2.0 channel", "80W output", "Bluetooth", "Wall-mountable"],
            "description": "Upgrade your TV's audio with this slim and powerful soundbar.",
            "price": 99.99
        },
        "AudioPhonic Turntable": {
            "name": "AudioPhonic Turntable",
            "category": "Audio Equipment",
            "brand": "AudioPhonic",
            "model_number": "AP-TT10",
            "warranty": "1 year",
            "rating": 4.2,
            "features": ["3-speed", "Built-in speakers", "Bluetooth", "USB recording"],
            "description": "Rediscover your vinyl collection with this modern turntable.",
            "price": 149.99
        },

        "FotoSnap DSLR Camera": {
            "name": "FotoSnap DSLR Camera",
            "category": "Cameras and Camcorders",
            "brand": "FotoSnap",
            "model_number": "FS-DSLR200",
            "warranty": "1 year",
            "rating": 4.7,
            "features": ["24.2MP sensor", "1080p video", "3-inch LCD", "Interchangeable lenses"],
            "description": "Capture stunning photos and videos with this versatile DSLR camera.",
            "price": 599.99
        },
        "ActionCam 4K": {
            "name": "ActionCam 4K",
            "category": "Cameras and Camcorders",
            "brand": "ActionCam",
            "model_number": "AC-4K",
            "warranty": "1 year",
            "rating": 4.4,
            "features": ["4K video", "Waterproof", "Image stabilization", "Wi-Fi"],
            "description": "Record your adventures with this rugged and compact 4K action camera.",
            "price": 299.99
        },
        "FotoSnap Mirrorless Camera": {
            "name": "FotoSnap Mirrorless Camera",
            "category": "Cameras and Camcorders",
            "brand": "FotoSnap",
            "model_number": "FS-ML100",
            "warranty": "1 year",
            "rating": 4.6,
            "features": ["20.1MP sensor", "4K video", "3-inch touchscreen", "Interchangeable lenses"],
            "description": "A compact and lightweight mirrorless camera with advanced features.",
            "price": 799.99
        },
        "ZoomMaster Camcorder": {
            "name": "ZoomMaster Camcorder",
            "category": "Cameras and Camcorders",
            "brand": "ZoomMaster",
            "model_number": "ZM-CM50",
            "warranty": "1 year",
            "rating": 4.3,
            "features": ["1080p video", "30x optical zoom", "3-inch LCD", "Image stabilization"],
            "description": "Capture life's moments with this easy-to-use camcorder.",
            "price": 249.99
        },
        "FotoSnap Instant Camera": {
            "name": "FotoSnap Instant Camera",
            "category": "Cameras and Camcorders",
            "brand": "FotoSnap",
            "model_number": "FS-IC10",
            "warranty": "1 year",
            "rating": 4.1,
            "features": ["Instant prints", "Built-in flash", "Selfie mirror", "Battery-powered"],
            "description": "Create instant memories with this fun and portable instant camera.",
            "price": 69.99
        }
    }

    products_file = 'products.json'
    with open(products_file, 'w') as file:
        json.dump(products, file)
        
    return products
