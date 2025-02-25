# alipay-wechat-finance
最近用思源笔记记东西上瘾，突然想每个月存一份收支记录进去。但手动整理账单太麻烦了，支付宝导出一份 CSV，微信又导出一份，格式还不一样，每次复制粘贴头都大。

干脆写了个 Python 脚本一键处理，核心就干两件事：  
1. 把俩平台的 CSV 账单合并到一起
2. 自动生成带分类表格的 Markdown（直接拖进思源就能渲染）

代码主要折腾了这些：  
- 支付宝账单前24行都是废话，直接 `skiprows=24` 跳过去，GBK 编码差点让我栽跟头
- 微信账单的列名和支付宝对不上，比如微信叫 **交易单号** ，支付宝叫 **交易订单号** ，通过 `rename` 强行对齐
- 两边金额都有 **¥** 符号和逗号（比如 ¥1,200），用正则 `[¥￥,]` 替换成数字
- 最后合并数据时发现微信少几个字段（比如“对方账号”），直接填个 pd.NA 占位

最爽的是生成 Markdown 的部分，pandas 分组统计消费类型，直接 for 循环拼字符串，出来效果长这样：

![生成样式示例，数据内容随机生成](https://raw.githubusercontent.com/zxc7563598/alipay-wechat-finance/refs/heads/main/doc/demo.png#pic_center)

# 使用说明
脚本依赖两个 Python 包：`pandas` 和 `chardet`。安装方法如下：  

```bash
pip install pandas chardet
```

**准备账单文件**

1. **支付宝账单**：  
   - 打开支付宝 App → 我的 → 账单 → 点击右上角「···」 → 开具交易流水证明 → 用于个人对账

2. **微信账单**：  
   - 打开微信 App → 我的 → 服务 → 钱包 → 账单 → 常见问题 → 下载账单 → 用于个人对账

将这两个文件放到脚本所在的文件夹中。

修改 `analysis.py` 第150行方法入参
```python
# 调用函数读取 CSV 文件并生成新的 CSV 文件
read_csv('支付宝账单路径.csv', '微信账单路径.csv', '生成合并账单路径')
# 调用函数生成 Markdown 文件
generate_markdown('生成合并账单路径.csv', '最终账单.md')
```

运行脚本，即可得到 `最终账单.md`
```python
python analysis.py 
```