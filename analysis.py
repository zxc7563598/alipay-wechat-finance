import pandas as pd

def read_csv(alipay_path, wechat_path, output_path):
    try:
        # 读取 alipay.csv 文件，跳过前 24 行，从第 25 行开始
        alipay = pd.read_csv(alipay_path, skiprows=24, encoding='GBK')
        
        # 读取 wechat.csv 文件
        wechat = pd.read_csv(wechat_path, skiprows=16)

        # 必需的列名
        required_columns = ['交易订单号', '交易分类', '交易对方', '对方账号', '商品说明', '收/支', '金额', '收/付款方式', '交易状态', '备注', '交易时间']

        # 确保 alipay 数据包含必要的列
        if all(col in alipay.columns for col in required_columns):
            # 选择 alipay.csv 中需要的列
            alipay_selected = alipay[required_columns]
        else:
            print("alipay.csv 文件缺少必要的列。")
            raise ValueError("alipay.csv 列不完整")

        # 重命名 wechat.csv 中的列以匹配 required_columns
        wechat_columns_map = {
            '交易单号': '交易订单号', '交易类型': '交易分类', '商品': '商品说明', '金额(元)': '金额', '支付方式': '收/付款方式', '当前状态': '交易状态'
        }
        
        # 重命名 wechat 的列
        wechat.rename(columns=wechat_columns_map, inplace=True)

        # 对 wechat.csv 进行列重命名和缺失列填充
        wechat_selected = pd.DataFrame(columns=required_columns)  # 创建一个空的 DataFrame，列名为 required_columns
        
        # 复制 wechat.csv 中已有的列
        for col in wechat.columns:
            if col in required_columns:
                wechat_selected[col] = wechat[col]
        
        # 对于 wechat.csv 中没有的列，填充空值（NaN）
        for col in required_columns:
            if col not in wechat_selected.columns:
                wechat_selected[col] = "/"

        # 去掉 '收/支' 列中值为 '不计收支' 的行
        alipay_selected = alipay_selected[alipay_selected['收/支'] != '不计收支']
        wechat_selected = wechat_selected[wechat_selected['收/支'] != '/']

        # 去掉 '金额' 列中的 '¥' 或 '￥' 符号，以及千位分隔符，并转换为浮点数
        wechat_selected['金额'] = wechat_selected['金额'].str.replace(r'[¥￥,]', '', regex=True).astype(float)

        # 为 alipay_selected 和 wechat_selected 添加「分类」列
        alipay_selected['分类'] = '支付宝'
        wechat_selected['分类'] = '微信'

        # 将 alipay 和 wechat 数据合并
        combined_data = pd.concat([alipay_selected, wechat_selected], ignore_index=True)

        # 将合并后的 DataFrame 保存为新的 CSV 文件
        combined_data.to_csv(output_path, index=False)
        print(f"文件已成功保存为 '{output_path}'")
    except FileNotFoundError:
        print("文件未找到，请检查文件路径。")
    except pd.errors.ParserError:
        print("读取 CSV 文件时出现问题，请检查文件格式或编码。")
    except Exception as e:
        print(f"发生错误：{e}")

def generate_markdown(csv_file, output_file):
    # 自动检测文件编码
    import chardet
    with open(csv_file, 'rb') as f:
        result = chardet.detect(f.read())
        encoding = result['encoding']
    
    # 读取文件
    data = pd.read_csv(csv_file, encoding=encoding)
    
    # 去除金额列中的符号和千分位逗号，转换为数值型
    data['金额'] = data['金额'].replace({'¥': '', ',': ''}, regex=True).astype(float)

    # 计算本月消费总额和收入总额
    total_expense = data[data['收/支'] == '支出']['金额'].sum()
    total_income = data[data['收/支'] == '收入']['金额'].sum()

    # 计算每个分类的金额
    expense_by_transaction = data[data['收/支'] == '支出'].groupby('交易分类')['金额'].sum().sort_values(ascending=False)
    income_by_transaction = data[data['收/支'] == '收入'].groupby('交易分类')['金额'].sum().sort_values(ascending=False)

    # 计算本月结余
    total_balance = total_income - total_expense
    
    # 打印调试信息
    print(f"Total Expense: {total_expense}")
    print(f"Total Income: {total_income}")
    print(f"Total Balance: {total_balance}")
    
    # 生成 markdown 内容
    markdown_content = f"**本月消费总额**：￥{total_expense:.2f}  |  **本月收入总额**：￥{total_income:.2f}  |  **本月结余**：￥{total_balance:.2f}\n\n"


    # 消费类型分析
    markdown_content += "## 消费类型分析 💸\n\n"
    markdown_content += "以下是各消费交易分类与消费金额：\n\n"
    markdown_content += "| 交易分类   | 消费金额   |\n"
    markdown_content += "| ---------- | ---------- |\n"
    for transaction, amount in expense_by_transaction.items():
        markdown_content += f"| {transaction} | ￥{amount:.2f} |\n"
    
    markdown_content += "\n### 每个交易分类的详细记录：\n"
    for transaction in expense_by_transaction.index:
        markdown_content += f"\n#### {transaction}消费记录 💳\n"
        transaction_data = data[(data['收/支'] == '支出') & (data['交易分类'] == transaction)]
        markdown_content += "| 交易对方  |  金额  | 分类 | 交易时间 |\n"
        markdown_content += "| -------- | ----- | ------ | -------- |\n"
        for _, row in transaction_data.iterrows():
            markdown_content += f"| {row['交易对方']} | ￥{row['金额']:.2f} | {row['分类']} | {row['交易时间']} |\n"

    # 收入类型分析
    markdown_content += "\n## 收入类型分析 💵\n\n"
    markdown_content += "以下是各收入交易分类与收入金额：\n\n"
    markdown_content += "| 交易分类   | 收入金额   |\n"
    markdown_content += "| ---------- | ---------- |\n"
    for transaction, amount in income_by_transaction.items():
        markdown_content += f"| {transaction} | ￥{amount:.2f} |\n"
    
    markdown_content += "\n### 每个交易分类的详细记录：\n"
    for transaction in income_by_transaction.index:
        markdown_content += f"\n#### {transaction}收入记录 💼\n"
        transaction_data = data[(data['收/支'] == '收入') & (data['交易分类'] == transaction)]
        markdown_content += "| 交易对方  |  金额  | 分类 | 交易时间 |\n"
        markdown_content += "| -------- | ----- | ------ | -------- |\n"
        for _, row in transaction_data.iterrows():
            markdown_content += f"| {row['交易对方']} | ￥{row['金额']:.2f} | {row['分类']} | {row['交易时间']} |\n"

    # 生成收支明细
    markdown_content += "\n## 收支明细\n"
    data_sorted = data.sort_values(by='交易时间')
    markdown_content += "| 交易分类 | 分类 | 收/支 | 金额 | 交易对方 | 商品说明 | 对方账号 | 收/付款方式 | 交易状态 | 备注 | 交易时间 |\n"
    markdown_content += "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n"
    
    for _, row in data_sorted.iterrows():
        markdown_content += f"| {row['交易分类']} | {row['分类']} | {row['收/支']} | ￥{row['金额']:.2f} | {row['交易对方']} | {row['商品说明']} | {row['对方账号']} | {row['收/付款方式']} | {row['交易状态']} | {row['备注']} | {row['交易时间']} |\n"
    
    # 保存生成的 markdown 到文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(markdown_content)

    print(f"Markdown 已成功生成并保存为 '{output_file}'")

# 调用函数读取 CSV 文件并生成新的 CSV 文件
read_csv('./bill/alipay_record_20250201_091025.csv', './bill/微信支付账单(20250101-20250201)——【解压密码可在微信支付公众号查看】.csv', './bill/合并账单.csv')
# 调用函数生成 Markdown 文件
generate_markdown('./bill/合并账单.csv', './bill/账单.md')
