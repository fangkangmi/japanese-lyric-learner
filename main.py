from dotenv import load_dotenv
from openai import OpenAI
import os
import re
import time

# 加载环境变量
load_dotenv()

# 获取环境变量
api_key = os.getenv("OPENAI_API_KEY")
model_name = os.getenv("MODEL_NAME", "gpt-4o")  # 默认使用 gpt-3.5-turbo
base_url = os.getenv("BASE_URL", "https://api.openai.com/v1")  # 默认使用 OpenAI 的 API URL

# 初始化 OpenAI 客户端
client = OpenAI(
    api_key=api_key,
    base_url=base_url,
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
  你是一位专业的日语导师，正在教一个对日语歌曲感兴趣的中国学生学习日语。学生会从歌曲中摘抄一些句子，向你提问。你的任务是：

  1. **逐句精准翻译** - 提供自然流畅的中文翻译
  2. **深度语法解析** - 详细解释每个语法点，包括：
     - 动词变形（ます形、て形、た形等）
     - 助词用法（が、を、に、で、へ等）
     - 句型结构（～たい、～ている、～なければならない等）
     - 敬语和口语表达的区别
  3. **词汇学习重点** - 标注重要词汇：
     - 汉字读音（假名标注）
     - 词性分类（动词、形容词、名词等）
     - 常用搭配和惯用语
  4. **文化背景补充** - 简要解释歌词中的文化典故或日本特有的表达方式
  5. **学习建议** - 指出值得记忆的语法点和表达

  输出格式要求：
  - 每句歌词单独列出
  - 翻译和语法解释分开
  - 关键词汇和语法点用清晰的项目符号标注
  - 避免在末尾添加总结性内容

  示范输入：
  大胆不敵にハイカラ革命
  磊々落々 反戦国家

  示范输出：

  #### 大胆不敵にハイカラ革命
  - **翻译**：大胆无畏地进行一场华丽的革命
  - **语法解析**:
    - *大胆不敵（だいたんふてき）*: 形容动词，意为"大胆而无所畏惧"
    - *に*: 助词，表示方式或状态，"以...的方式"
    - *ハイカラ*: 外来词，来自英语"high collar"，引申为"时尚、新潮"
    - *革命（かくめい）*: 名词，"革命"
  - **学习要点**:
    - 注意「に」表示方式的用法
    - 「ハイカラ」是明治维新时期流行的词汇

---

'''

    # 预先处理歌词的换行连接
    lyrics = '\n'.join(batch)
    
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {'role': 'system', 'content': system_message},
                {'role': 'user', 'content': f"""请按照上述要求逐句分析以下歌词：\n{lyrics}"""}
            ]
        )
        time.sleep(0.5)
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
    主程序：读取 original_song 文件夹及其子文件夹中的所有歌词文件，逐个生成分析结果文件。
    如果 output 文件夹中已存在对应的 _analysis.txt 文件，则跳过处理。
    """
    # 定义输入和输出文件夹
    input_folder = "original_song"
    output_folder = "output"

    # 获取所有子文件夹（包括根文件夹）
    subfolders = [d for d in os.listdir(input_folder) if os.path.isdir(os.path.join(input_folder, d))]
    subfolders.append("")  # 添加根文件夹

    # 遍历每个子文件夹
    for subfolder in subfolders:
        input_subfolder = os.path.join(input_folder, subfolder)
        output_subfolder = os.path.join(output_folder, subfolder)

        # 确保输出子文件夹存在
        os.makedirs(output_subfolder, exist_ok=True)

        # 获取子文件夹中的所有 .txt 文件
        if os.path.exists(input_subfolder):
            song_files = [f for f in os.listdir(input_subfolder) if f.endswith(".txt")]
        else:
            print(f"Skipping {subfolder} (folder does not exist)")
            continue

        # 遍历每个歌词文件
        for song_file in song_files:
            input_file = os.path.join(input_subfolder, song_file)
            output_file = os.path.join(output_subfolder, f"{os.path.splitext(song_file)[0]}_analysis.txt")

            # 检查输出文件是否已存在
            if os.path.exists(output_file):
                print(f"Skipping {song_file} in {subfolder} (already processed)")
                continue

            print(f"Processing {song_file} in {subfolder}...")

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