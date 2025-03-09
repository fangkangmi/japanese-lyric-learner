from dotenv import load_dotenv
from openai import OpenAI
import os
import time

# 加载环境变量
load_dotenv()

# 初始化 OpenAI 客户端
client = OpenAI(
    base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
)

# 确保输出文件夹存在
os.makedirs("output", exist_ok=True)

# 定义分段处理函数
def process_lyrics_in_batches(lyrics, batch_size=4):
    """
    将歌词分成若干小段，每段包含指定数量的行。
    :param lyrics: 歌词列表，每行歌词为一个元素。
    :param batch_size: 每段包含的行数。
    :return: 分段后的歌词列表。
    """
    return [lyrics[i:i + batch_size] for i in range(0, len(lyrics), batch_size)]

def analyze_lyrics_batch(batch):
    # 定义系统消息的任务描述
    system_message = '''
你是一位日语导师，正在教一个对日语歌曲感兴趣的中国学生学习日语。学生会从歌曲中摘抄一些句子，向你提问。你的任务是：
1. 提供逐句的准确翻译。
2. 详细解释每句的语法和关键词汇。
3. 输出格式要求如下：
   - 每句歌词单独列出。
   - 翻译和语法解释分开。
   - 关键词汇和语法点用清晰的项目符号标注。
'''

    # 预先处理歌词的换行连接
    lyrics = '\n'.join(batch)
    
    try:
        response = client.chat.completions.create(
            model="qwen-plus",
            messages=[
                {'role': 'system', 'content': system_message},
                {'role': 'user', 'content': f"""请按照上述要求逐句分析以下歌词：\n{lyrics}"""}
            ]
        )
        time.sleep(1)  # 添加延迟以避免速率限制
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error occurred while processing batch: {batch}")
        print(f"Error details: {e}")
        return "Error: Unable to process this batch."

# 主函数
def main(input_file, output_file):
    """
    主程序：读取歌词文件，分段处理并保存结果。
    :param input_file: 输入歌词文件路径。
    :param output_file: 输出解析结果文件路径。
    """
    # 读取歌词文件
    with open(input_file, 'r', encoding='utf-8') as f:
        lyrics = f.readlines()
    lyrics = [line.strip() for line in lyrics if line.strip()]  # 去除空行

    # 分段处理歌词
    batches = process_lyrics_in_batches(lyrics, batch_size=4)

    # 保存解析结果
    with open(output_file, 'w', encoding='utf-8') as f:
        for i, batch in enumerate(batches, start=1):
            print(f"Processing batch {i}...")
            analysis = analyze_lyrics_batch(batch)
            
            # 打印结果
            print(f"\nBatch {i} Analysis:\n{analysis}\n")
            
            # 写入文件
            f.write(f"Batch {i}:\n")
            f.write(analysis)
            f.write("\n\n")  # 每批之间留空行

    print(f"Analysis completed and saved to {output_file}")

# 运行主程序
if __name__ == "__main__":
    input_file = "original_song/dryflower.txt"  # 输入歌词文件路径
    output_file = "output/dryflower_analysis.txt"  # 输出解析结果文件路径
    main(input_file, output_file)