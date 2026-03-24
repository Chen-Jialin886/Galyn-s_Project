import tkinter as tk
from tkinter import ttk, messagebox

import jieba
import numpy as np
import pdfplumber
from matplotlib.backends._backend_tk import NavigationToolbar2Tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tushare as ts
from datetime import datetime
import requests
import re
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from imageio.v2 import imread
global data, canvas, figure, literature_figure, literature_canvas
data = None
canvas = None
figure = None
literature_figure = None
literature_canvas = None

plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['font.sans-serif'] = ['SimHei']

# 获取数据按钮
def on_data_button_click():
    global data
    stock_code = stock_entry.get().strip()
    start_date = start_date_entry.get().strip()
    end_date = end_date_entry.get().strip()

    if not stock_code:
        messagebox.showerror("错误", "请输入股票代码")
        return

    if not start_date or not end_date:
        messagebox.showerror("错误", "请输入日期范围")
        return

    try:
        # 检查日期格式
        datetime.strptime(start_date, '%Y%m%d')
        datetime.strptime(end_date, '%Y%m%d')

        ts.set_token('9a5b271383c94e451908da9a07e5649d2bf6c3834bfb53f013e2c0be')
        pro = ts.pro_api()

        # 使用Tushare获取数据
        data = pro.daily(ts_code=stock_code, start_date=start_date, end_date=end_date)

        # 更新表格
        # 清除表格
        for item in data_table.get_children():
            data_table.delete(item)

        # 填充表格
        for index, row in data.iterrows():
            date_obj = datetime.strptime(row['trade_date'], '%Y%m%d')
            date_str = date_obj.strftime('%Y-%m-%d')
            values = (date_str, f"{row['open']:.2f}", f"{row['high']:.2f}",
                      f"{row['low']:.2f}", f"{row['close']:.2f}",
                      f"{int(row['vol']):,}")
            data_table.insert("", tk.END, values=values)

    except ValueError as ve:
        messagebox.showerror("错误", f"日期格式不正确，请使用YYYYMMDD格式: {str(ve)}")


# 获取文献按钮
def on_pdf_button_click():
    try:
        url = "https://www.alibabagroup.com/ir-annual-general-meetings"
        html = requests.get(url, verify=False)
        html.encoding = html.apparent_encoding
        data = html.text
        reg = r'<a class="annual-link right-pdf" href="(.*?)" target="_blank">'
        urls = re.findall(reg, data)
        number = 1
        for url in urls:
            r = requests.get(url)
            data = r.content
            file_name = f'pdf_{number}.pdf'
            fobj = open(file_name, "wb")
            fobj.write(data)
            fobj.close()
            number = number + 1
        messagebox.showinfo("完成", "下载任务完成")

    except Exception as e:
        messagebox.showerror("错误", f"下载过程中出错: {str(e)}")


#进行金融数据处理,走势图分析，并实现分析结果的可视化展示
def on_graph_click1():
    global data, canvas, figure
    if data is None or data.empty:
        messagebox.showwarning("警告", "请先获取数据")
        return

    figure.clear()
    df = data[['open', 'high', 'low', 'close', 'amount']]
    dates = data['trade_date'].tolist()

    ax = figure.add_subplot(111)
    ax.set_title("股价分析报告")
    ax.set_xlabel("日期")
    ax.set_ylabel("股价")
    ax.plot(dates, df['open'], "r-o", label="开盘价")
    ax.plot(dates, df['close'], "b-.*", label="收盘价")
    ax.plot(dates, df['high'], "g--^", label="最高价")
    ax.plot(dates, df['low'], "y:s", label="最低价")

    ax2 = ax.twinx()
    ax2.plot(dates, df['amount'], "m--", label="成交量")
    ax2.set_ylabel("成交量")

    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.legend()

    canvas.draw()
#股价指标相关性分析
def on_graph_click2():
    global data, canvas, figure
    if data is None or data.empty:
        messagebox.showwarning("警告", "请先获取数据")
        return

    figure.clear()
    df = data[['open', 'high', 'low', 'close', 'amount']]
    corr_matrix = df.corr()

    ax = figure.add_subplot(111)
    cax = ax.matshow(corr_matrix, vmin=-1, vmax=1)
    figure.colorbar(cax)

    ticks = np.arange(0, len(corr_matrix.columns), 1)
    ax.set_xticks(ticks)
    ax.set_yticks(ticks)
    ax.set_xticklabels(corr_matrix.columns)
    ax.set_yticklabels(corr_matrix.columns)

    plt.title("股价指标相关性分析")
    plt.tight_layout()

    canvas.draw()
#可视化词云展示
def generate_wordcloud():
    global literature_figure, literature_canvas
    fobj=pdfplumber.open("pdf_2.pdf")
    pages=fobj.pages
    text_all=[]
    for page in pages:
        text=page.extract_text()
        text_all.append(text)
    text_all=''.join(text_all)
    fobj.close()
    words=jieba.lcut(text_all)
    counts={}
    for word in words:
        if len(word)==1:
            continue
        else:
            counts[word]=counts.get(word,0)+1
    pic=imread('cloud.png')
    wc=WordCloud(mask=pic,font_path='msyh.ttc', #中文字体
                    repeat=False, #内容可以重复
                    background_color='white', #设置背景颜色
                    max_words=110, #设置最大词数
                    max_font_size=120, #设置字体最大值
                    min_font_size=10, #设置字体最小值
                    random_state=50, #设置配色方案
                    scale=10)
    wc.generate_from_frequencies(counts)
    literature_figure.clear()
    ax = literature_figure.add_subplot(111)
    ax.imshow(wc, interpolation='bilinear')
    ax.axis('off')
    ax.set_title("文献内容词云图", fontsize=14)

    literature_canvas.draw()
#可视化词频柱状图统计
def count_word_frequency():
    global literature_figure, literature_canvas
    fobj = pdfplumber.open("pdf_2.pdf")
    pages = fobj.pages
    text_all = []
    for page in pages:
        text = page.extract_text()
        text_all.append(text)
    text_all = ''.join(text_all)
    fobj.close()
    words = jieba.lcut(text_all)
    counts = {}
    excludes = set()
    with open("中文停用词.txt", "r", encoding="utf-8") as fobj:
        for i in fobj:
           i = i.strip()
           excludes.add(i)
    for word in words:
        if len(word) == 1:
            continue
        elif word in excludes:
            continue
        else:
            counts[word] = counts.get(word, 0) + 1


    items = list(counts.items())
    items.sort(key=lambda x: x[1], reverse=True)
    x_labels = []
    y_values = []
    for i in range(10):
        word, count = items[i]
        x_labels.append(word)
        y_values.append(count)
        plt.bar(word, count)
    literature_figure.clear()
    ax = literature_figure.add_subplot(111)
    ax.barh(x_labels, y_values, color='#3498db', height=0.6)
    ax.set_xlabel("出现次数", fontsize=12)
    ax.set_ylabel("词汇", fontsize=12)
    ax.set_title("高频词汇统计（前10名）", fontsize=14)
    ax.grid(axis='x', linestyle='--', alpha=0.7)


# 创建主窗口
root = tk.Tk()
root.title("金融数据与文献获取平台")
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

# 文献获取选项卡
literature_tab = ttk.Frame(tab_control)
tab_control.add(literature_tab, text="金融文献获取")

# 数据获取选项卡
# 控制面板参数设置
control_frame = ttk.LabelFrame(data_tab, text="", padding=10)
control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)

# 股票代码
ttk.Label(control_frame, text="股票代码:").pack(anchor=tk.W, pady=5)
stock_entry = ttk.Entry(control_frame, width=20)
stock_entry.pack(fill=tk.X, pady=2)

# 日期选择
ttk.Label(control_frame, text="开始日期 (YYYYMMDD):").pack(anchor=tk.W, pady=5)
start_date_entry = ttk.Entry(control_frame, width=20)
start_date_entry.pack(fill=tk.X, pady=2)

ttk.Label(control_frame, text="结束日期 (YYYYMMDD):").pack(anchor=tk.W, pady=5)
end_date_entry = ttk.Entry(control_frame, width=20)
end_date_entry.pack(fill=tk.X, pady=2)

# 按钮
fetch_button = ttk.Button(control_frame, text="获取数据")
fetch_button.pack(fill=tk.X, pady=20)
fetch_button.config(command=on_data_button_click)

# 按钮
fetch_button = ttk.Button(control_frame, text="股票走势可视化")
fetch_button.pack(fill=tk.X, pady=20)
fetch_button.config(command=on_graph_click1)
# 按钮
fetch_button = ttk.Button(control_frame, text="股票相关性可视化")
fetch_button.pack(fill=tk.X, pady=20)
fetch_button.config(command=on_graph_click2)

# 可视化
# 可视化区域
display_frame = ttk.Frame(data_tab)
display_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
# 图表区域
chart_frame = ttk.LabelFrame(display_frame, text="数据可视化", padding=5)
chart_frame.pack(fill=tk.BOTH, expand=True, pady=5, padx=5, ipady=10)

# 初始化图表（关键部分）
figure = plt.figure(figsize=(10, 5))
canvas = FigureCanvasTkAgg(figure, master=chart_frame)
canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
toolbar = NavigationToolbar2Tk(canvas, chart_frame)
toolbar.update()

# 数据表格
table_frame = ttk.LabelFrame(display_frame, text="数据详情", padding=5)
table_frame.pack(fill=tk.BOTH, expand=True, pady=5)

# 创建表格
columns = ["日期", "开盘价", "最高价", "最低价", "收盘价", "成交量"]
data_table = ttk.Treeview(table_frame, columns=columns, show="headings")
for col in columns:
    data_table.heading(col, text=col)
    width = 150
    data_table.column(col, width=width, anchor=tk.CENTER)

# 滚动条
scrollbar_y = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=data_table.yview)
scrollbar_x = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=data_table.xview)
data_table.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
data_table.pack(fill=tk.BOTH, expand=True)



# 文献可视化区域
literature_control_frame = ttk.LabelFrame(literature_tab, text="文献处理工具", padding=10)
literature_control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)

literature_button_frame = ttk.Frame(literature_control_frame, padding=10)
literature_button_frame.pack(fill=tk.X)

download_btn = ttk.Button(literature_button_frame, text="下载年度报告PDF", command=on_pdf_button_click)
download_btn.pack(fill=tk.X, pady=10)

wordcloud_btn = ttk.Button(literature_button_frame, text="生成词云图", command=generate_wordcloud)
wordcloud_btn.pack(fill=tk.X, pady=10)

frequency_btn = ttk.Button(literature_button_frame, text="统计高频词汇", command=count_word_frequency)
frequency_btn.pack(fill=tk.X, pady=10)
# 文献可视化区域
literature_display_frame = ttk.Frame(literature_tab, padding=10)
literature_display_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

literature_chart_frame = ttk.LabelFrame(literature_display_frame, text="文献分析可视化", padding=5)
literature_chart_frame.pack(fill=tk.BOTH, expand=True, pady=5)

literature_figure = plt.figure(figsize=(10, 6))
literature_canvas = FigureCanvasTkAgg(literature_figure, master=literature_chart_frame)
literature_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
literature_toolbar = NavigationToolbar2Tk(literature_canvas, literature_chart_frame)
literature_toolbar.update()
# 运行主循环
root.mainloop()
