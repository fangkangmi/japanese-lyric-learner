from dotenv import load_dotenv
from openai import OpenAI
import os
import re
import time
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# 加载环境变量
load_dotenv()

# 获取环境变量
api_key = os.getenv("OPENAI_API_KEY")
model_name = os.getenv("MODEL_NAME", "gpt-5")  # 默认使用 gpt-5
base_url = os.getenv("BASE_URL", "https://api.openai.com/v1")

# 初始化 OpenAI 客户端
client = OpenAI(
    api_key=api_key,
    base_url=base_url,
)

# 确保输入和输出文件夹存在
os.makedirs("original_song", exist_ok=True)
os.makedirs("output", exist_ok=True)

# 线程安全的进度追踪器
class ProgressTracker:
    def __init__(self, total_files, total_batches):
        self.total_files = total_files
        self.total_batches = total_batches
        self.processed_files = 0
        self.processed_batches = 0
        self.lock = threading.Lock()
        self.start_time = time.time()

    def update_batch(self):
        with self.lock:
            self.processed_batches += 1
            elapsed = time.time() - self.start_time
            batches_per_sec = self.processed_batches / elapsed if elapsed > 0 else 0
            remaining_batches = self.total_batches - self.processed_batches
            eta = remaining_batches / batches_per_sec if batches_per_sec > 0 else 0

            print(f"Progress: {self.processed_batches}/{self.total_batches} batches "
                  f"({self.processed_batches/self.total_batches*100:.1f}%) - "
                  f"ETA: {eta:.1f}s")

    def update_file(self, filename):
        with self.lock:
            self.processed_files += 1
            print(f"✓ Completed {filename} ({self.processed_files}/{self.total_files} files)")

# 定义分段处理函数
def process_lyrics_in_batches(lyrics, batch_size=4):
    """
    将歌词分成若干小段，每段包含指定数量的行。
    :param lyrics: 歌词列表，每行歌词为一个元素。
    :param batch_size: 每段包含的行数。
    :return: 分段后的歌词列表。
    """
    return [lyrics[i:i + batch_size] for i in range(0, len(lyrics), batch_size)]

def analyze_lyrics_batch(batch, batch_num, song_name, progress_tracker):
    """
    分析歌词批次（线程安全版本）
    """
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
  4. **文化背景补充** - 简要解释歌词中的文化典故或日本特有的表达方式(if applicable)
  5. **学习建议** - 指出值得记忆的语法点和表达(if applicable)

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
        # 移除固定的sleep，使用更智能的速率限制
        analysis = response.choices[0].message.content.strip()

        # 清理不必要的结尾语句
        analysis = remove_unwanted_endings(analysis)
        progress_tracker.update_batch()
        return analysis
    except Exception as e:
        print(f"Error occurred while processing batch {batch_num} of {song_name}: {e}")
        progress_tracker.update_batch()
        return f"Error: Unable to process batch {batch_num}."

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

def process_song_parallel(song_file, subfolder, progress_tracker):
    """
    并行处理单个歌曲文件
    """
    try:
        input_folder = "original_song"
        output_folder = "output"

        input_file = os.path.join(input_folder, subfolder, song_file) if subfolder else os.path.join(input_folder, song_file)
        output_file = os.path.join(output_folder, subfolder, f"{os.path.splitext(song_file)[0]}_analysis.txt") if subfolder else os.path.join(output_folder, f"{os.path.splitext(song_file)[0]}_analysis.txt")

        # 检查输出文件是否已存在
        if os.path.exists(output_file):
            return f"Skipping {song_file} (already processed)"

        print(f"Processing {song_file} in {subfolder or 'root'}...")

        # 读取歌词文件
        with open(input_file, 'r', encoding='utf-8') as f:
            lyrics = f.readlines()
        lyrics = [line.strip() for line in lyrics if line.strip()]  # 去除空行

        # 分段处理歌词
        batches = process_lyrics_in_batches(lyrics, batch_size=4)

        # 使用线程池并行处理批次
        results = []
        with ThreadPoolExecutor(max_workers=4) as executor:  # 增加到4个并发批次处理
            future_to_batch = {
                executor.submit(analyze_lyrics_batch, batch, i+1, song_file, progress_tracker): (i+1, batch)
                for i, batch in enumerate(batches)
            }

            # 收集结果并保持顺序
            batch_results = {}
            for future in as_completed(future_to_batch):
                batch_num, batch = future_to_batch[future]
                try:
                    analysis = future.result()
                    batch_results[batch_num] = analysis
                except Exception as e:
                    print(f"Batch {batch_num} generated an exception: {e}")
                    batch_results[batch_num] = f"Error processing batch {batch_num}"

            # 按顺序整理结果
            for i in range(1, len(batches) + 1):
                results.append(batch_results[i])

        # 保存解析结果
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            for analysis in results:
                f.write(analysis)
                f.write("\n\n")  # 每批之间留空行

        progress_tracker.update_file(song_file)
        return f"Completed {song_file}"

    except Exception as e:
        return f"Error processing {song_file}: {e}"

def main():
    """
    主程序：使用并行处理加速分析
    """
    print("🚀 Starting parallel processing mode...")
    start_time = time.time()

    input_folder = "original_song"
    output_folder = "output"

    # 收集所有需要处理的文件
    songs_to_process = []

    # 获取所有子文件夹（包括根文件夹）
    subfolders = [d for d in os.listdir(input_folder) if os.path.isdir(os.path.join(input_folder, d))]
    subfolders.append("")  # 添加根文件夹

    # 遍历每个子文件夹收集文件
    for subfolder in subfolders:
        input_subfolder = os.path.join(input_folder, subfolder)
        if not os.path.exists(input_subfolder):
            continue

        song_files = [f for f in os.listdir(input_subfolder) if f.endswith(".txt")]
        for song_file in song_files:
            # 跳过已处理的文件
            output_file = os.path.join(output_folder, subfolder, f"{os.path.splitext(song_file)[0]}_analysis.txt") if subfolder else os.path.join(output_folder, f"{os.path.splitext(song_file)[0]}_analysis.txt")
            if not os.path.exists(output_file):
                songs_to_process.append((song_file, subfolder))

    if not songs_to_process:
        print("No new songs to process!")
        return

    # 计算总批次数量（估算）
    total_batches = 0
    for song_file, subfolder in songs_to_process:
        input_file = os.path.join(input_folder, subfolder, song_file) if subfolder else os.path.join(input_folder, song_file)
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                lines = len([line for line in f.readlines() if line.strip()])
            batches = (lines + 3) // 4  # 每4行一批
            total_batches += max(1, batches)
        except:
            total_batches += 1  # 保守估计

    print(f"📊 Found {len(songs_to_process)} songs to process, estimated {total_batches} total batches")
    print(f"🔄 Using parallel processing with up to 4 concurrent workers")

    # 创建进度追踪器
    progress_tracker = ProgressTracker(len(songs_to_process), total_batches)

    # 使用线程池并行处理所有歌曲
    with ThreadPoolExecutor(max_workers=4) as executor:  # 增加到4个并发工作者
        future_to_song = {
            executor.submit(process_song_parallel, song_file, subfolder, progress_tracker): (song_file, subfolder)
            for song_file, subfolder in songs_to_process
        }

        # 收集结果
        for future in as_completed(future_to_song):
            song_file, subfolder = future_to_song[future]
            try:
                result = future.result()
                print(f"✅ {result}")
            except Exception as e:
                print(f"❌ Error processing {song_file}: {e}")

    total_time = time.time() - start_time
    print(f"\n🎉 Parallel processing completed in {total_time:.1f} seconds!")
    print(f"📈 Average speed: {total_batches/total_time:.1f} batches/second")

# 运行主程序
if __name__ == "__main__":
    main()