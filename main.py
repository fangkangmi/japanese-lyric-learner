from dotenv import load_dotenv
from openai import OpenAI
import os
import re

# 加载环境变量
load_dotenv()

# 初始化 OpenAI 客户端
client = OpenAI(
    base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
)

# 确保输入和输出文件夹存在
os.makedirs("original_song", exist_ok=True)
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
4. 请严格按照要求逐句分析歌词，不要在分析结果的末尾添加任何总结性或额外的内容。
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
        analysis = response.choices[0].message.content.strip()
        
        # 清理不必要的结尾语句
        analysis = remove_unwanted_endings(analysis)
        return analysis
    except Exception as e:
        print(f"Error occurred while processing batch: {batch}")
        print(f"Error details: {e}")
        return "Error: Unable to process this batch."

# 清理不必要的结尾语句
def remove_unwanted_endings(text):
    """
    移除分析结果中的总结性或额外内容。
    :param text: 原始分析结果。
    :return: 清理后的分析结果。
    """
    # 定义需要移除的模式
    patterns_to_remove = [
        r"希望这些解析对你理解歌词有所帮助.*",  # 匹配总结性语句
        r"如果有其他问题，随时提问哦.*",       # 匹配鼓励提问的语句
        r"---\s*希望.*",                      # 匹配分割线后跟随的总结性内容
    ]
    
    for pattern in patterns_to_remove:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)
    
    # 去除多余的空行
    text = re.sub(r"\n\s*\n", "\n\n", text).strip()
    return text

# 主函数
def main():
    """
    主程序：读取 original_song 文件夹中的所有歌词文件，逐个生成分析结果文件。
    如果 output 文件夹中已存在对应的 _analysis.txt 文件，则跳过处理。
    """
    # 获取 original_song 文件夹中的所有 .txt 文件
    input_folder = "original_song"
    output_folder = "output"
    song_files = [f for f in os.listdir(input_folder) if f.endswith(".txt")]

    # 遍历每个歌词文件
    for song_file in song_files:
        input_file = os.path.join(input_folder, song_file)
        output_file = os.path.join(output_folder, f"{os.path.splitext(song_file)[0]}_analysis.txt")

        # 检查输出文件是否已存在
        if os.path.exists(output_file):
            print(f"Skipping {song_file} (already processed)")
            continue

        print(f"Processing {song_file}...")

        # 读取歌词文件
        with open(input_file, 'r', encoding='utf-8') as f:
            lyrics = f.readlines()
        lyrics = [line.strip() for line in lyrics if line.strip()]  # 去除空行

        # 分段处理歌词
        batches = process_lyrics_in_batches(lyrics, batch_size=4)

        # 保存解析结果
        with open(output_file, 'w', encoding='utf-8') as f:
            for i, batch in enumerate(batches, start=1):
                print(f"Processing batch {i} of {song_file}...")
                analysis = analyze_lyrics_batch(batch)
                
                # 打印结果
                print(f"\nBatch {i} Analysis:\n{analysis}\n")
                
                # 写入文件
                f.write(analysis)
                f.write("\n\n")  # 每批之间留空行

        print(f"Analysis completed and saved to {output_file}")

# 运行主程序
if __name__ == "__main__":
    main()