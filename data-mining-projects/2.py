import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import requests
import re
from snownlp import SnowNLP
import pymysql
global result
result = []
DB_CONFIG = {
    "host": "localhost",      # MySQL主机地址
    "port": 3306,             # 端口号
    "user": "root",           # 用户名
    "password": "1234",     # 密码（需替换为你的实际密码）
    "database": "test", # 数据库名（需提前创建或自动创建）
    "charset": "utf8mb4"      # 字符集（支持中文）
}
# 获取数据按钮
def on_data_button_click():
    global result
    result.clear()
    word = word_entry.get().strip()
    if not word:
        messagebox.showerror("错误", "请输入爬取关键词")
        return
    web = web_type_var.get()
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                             'AppleWebKit/537.36 (KHTML, like Gecko) '
                             'Chrome/69.0.3497.100 Safari/537.36'}

    if web == "百度":
        url = 'http://www.baidu.com/s?tn=news&rtt=1&wd=' + word
        id = 1
        try:
            res = requests.get(url, headers=headers, timeout=10)
            res.encoding = res.apparent_encoding
            data = res.text
            p_title = '<h3 class="news-title_1YtI1 ">.*?>(.*?)</a>'
            title = re.findall(p_title, data, re.S)
            for t in title:
                t = t.strip()
                t = re.sub('<.*?>', '', t)
                s = SnowNLP(t)
                data = (id, t, s.sentiments)
                result.append(data)
                id = id + 1
            print(result)
        except Exception as e:
            messagebox.showerror("错误", f"数据爬取出错{e}")

    elif web == "360":
        url = 'https://news.so.com/ns?q=' + word + '&src=360portal&_re=0'
        id = 1
        try:
            res = requests.get(url, headers=headers, timeout=10)
            res.encoding = res.apparent_encoding
            data = res.text
            p_title = '<div class="g-txt-inner g-ellipsis">(.*?)</div>'
            title = re.findall(p_title, data, re.S)
            for t in title:
                t = t.strip()
                t = re.sub('<.*?>', '', t)
                s = SnowNLP(t)
                data = (id, t, s.sentiments)
                result.append(data)
                id = id + 1
            print(result)
        except Exception as e:
            messagebox.showerror("错误", f"数据爬取出错{e}")

    # 更新表格

    for item in data_table.get_children():
        data_table.delete(item)

    # 填充表格
    for i in range(len(result)):
        values = result[i]
        data_table.insert("", tk.END, values=values)

#数据分析及可视化展示
def analyze_sentiment():
    global result
    if not result:
        messagebox.showwarning("提示", "请先爬取数据")
        return

    # 提取所有评分
    scores = [item[2] for item in result]
    positive = sum(1 for s in scores if s >= 0.7)
    negative = sum(1 for s in scores if s <= 0.3)
    neutral = len(scores) - positive - negative

    # 绘制饼图
    ax.clear()
    labels = ['正面', '中性', '负面']
    sizes = [positive, neutral, negative]
    colors = ['#4CAF50', '#607D8B', '#FF4444']  # 绿、灰、红
    explode = (0.1, 0, 0)  # 突出正面部分

    ax.pie(sizes, explode=explode, labels=labels, colors=colors,
           autopct='%1.1f%%', shadow=True, startangle=90)
    ax.axis('equal')  # 保证饼图为正圆形
    ax.set_title('情感比例分布')
    canvas.draw()
#将爬取数据存入数据库
def save_to_mysql():
    global result
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # 创建数据库
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']}")
    conn.select_db(DB_CONFIG['database'])
    cursor.execute("DROP TABLE IF EXISTS news_sentiment")
    # 创建数据表
    create_table_sql = """
           CREATE TABLE IF NOT EXISTS news_sentiment (
               id INT PRIMARY KEY,
               title VARCHAR(500) NOT NULL,
               sentiment FLOAT NOT NULL
           )
           """
    cursor.execute(create_table_sql)
    conn.commit()
    cursor.close()
    conn.close()
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        insert_sql = """
            INSERT INTO news_sentiment (id, title, sentiment)
            VALUES (%s, %s, %s)
           """
        cursor.executemany(insert_sql, result)
        conn.commit()
        cursor.close()
        conn.close()
        messagebox.showinfo("操作成功", f"已成功存储 {len(result)} 条数据到MySQL")
        return True
    except Exception as e:
        messagebox.showerror("数据库错误", f"保存数据失败: {str(e)}")
        return False


# 设置中文字体支持
plt.rcParams["font.family"] = ["SimHei"]

# 创建主窗口
root = tk.Tk()
root.title("金融数据获取平台")
root.geometry("1200x800")
root.minsize(1000, 700)

# 设置主题颜色
bg_color = "#f0f5f9"
header_color = "#1e2022"
button_color = "#52616b"
button_hover_color = "#c9d6df"
text_color = "#1e2022"

# 创建主框架
main_frame = ttk.Frame(root, padding=10)
main_frame.pack(fill=tk.BOTH, expand=True)

# 主选项卡
tab_control = ttk.Notebook(main_frame)
tab_control.pack(fill=tk.BOTH, expand=True)

# 数据获取选项卡
data_tab = ttk.Frame(tab_control)
tab_control.add(data_tab, text="金融数据获取")

# 数据获取选项卡
# 控制面板
control_frame = ttk.LabelFrame(data_tab, text="参数设置", padding=10)
control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)

# 爬取关键词
ttk.Label(control_frame, text="爬取关键词:").pack(anchor=tk.W, pady=5)
word_entry = ttk.Entry(control_frame, width=20)
word_entry.pack(fill=tk.X, pady=2)

# 爬取网站
ttk.Label(control_frame, text="爬取网站:").pack(anchor=tk.W, pady=5)
web_type_var = tk.StringVar(value="百度")
web_type_frame = ttk.Frame(control_frame)
web_type_frame.pack(fill=tk.X, pady=2)
web_types = ["百度", "360"]
for i, dtype in enumerate(web_types):
    ttk.Radiobutton(web_type_frame, text=dtype, variable=web_type_var,
                    value=dtype).grid(row=i // 2, column=i % 2, sticky=tk.W, padx=5)

# 按钮
fetch_button = ttk.Button(control_frame, text="爬取数据")
fetch_button.pack(fill=tk.X, pady=20)
fetch_button.config(command=on_data_button_click)
#分析按钮
analyze_button = ttk.Button(control_frame, text="分析情感分布")
analyze_button.pack(fill=tk.X, pady=20)
analyze_button.config(command=analyze_sentiment)
# 按钮
fetch_button = ttk.Button(control_frame, text="存入MYSQL")
fetch_button.pack(fill=tk.X, pady=20)
fetch_button.config(command=save_to_mysql)
# 可视化
# 可视化区域
display_frame = ttk.Frame(data_tab)
display_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)

# 图表
figure, ax = plt.subplots(figsize=(8, 5))
canvas = FigureCanvasTkAgg(figure, master=display_frame)
canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

# 数据表格
table_frame = ttk.LabelFrame(display_frame, text="数据详情", padding=5)
table_frame.pack(fill=tk.BOTH, expand=True, pady=5)

# 创建表格
columns = ["编号", "标题", "舆情评分"]
data_table = ttk.Treeview(table_frame, columns=columns, show="headings")

widths = [100, 300, 200]
for i, col in enumerate(columns):
    data_table.heading(col, text=col)
    width = widths[i]
    data_table.column(col, width=width, anchor=tk.CENTER)

# 滚动条
scrollbar_y = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=data_table.yview)
scrollbar_x = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=data_table.xview)
data_table.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
data_table.pack(fill=tk.BOTH, expand=True)


# 运行主循环
root.mainloop()
