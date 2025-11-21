# PDF to JSON Converter

一个功能强大的Python模块，可将PDF文件转换为结构化的JSON格式，保留文本和图片的相对位置，并支持AI驱动的图片内容分析。

**重要说明**：本模块依赖 `ks_infrastructure` 基础设施服务模块提供 Vision 服务，确保先安装该依赖。

## 特性

- ✅ **保留相对位置**：按照PDF中的垂直位置排序，保持文本和图片的原始顺序
- ✅ **AI图片分析**：使用阿里云Qwen视觉大模型分析图片内容（通过 ks_infrastructure 服务）
- ✅ **智能缓存**：自动缓存重复图片的分析结果，避免重复调用API
- ✅ **表格识别**：将图片中的表格转换为Markdown格式
- ✅ **忽略UI元素**：专注于实质性内容，自动忽略logo、icon等装饰性元素
- ✅ **简洁输出**：以段落形式输出，按页分组

## 项目结构

```
pdf2json/
├── pdf_to_json/          # 核心模块
│   ├── __init__.py           # 模块初始化
│   └── converter.py          # 转换器实现（使用 ks_infrastructure）
├── test/                     # 测试目录
│   └── test_pdf2json.py      # 测试脚本
├── requirements.txt          # 依赖列表
└── README.md                 # 本文件
```

## 安装依赖

本模块依赖 `ks_infrastructure` 基础设施服务模块提供 Vision 服务。

```bash
# 1. 安装 ks_infrastructure 模块
pip install -e ../ks_infrastructure

# 2. 安装 pdf_to_json 的依赖
pip install -r requirements.txt
```

或者一次性安装：

```bash
pip install PyMuPDF -e ../ks_infrastructure
```


## 使用方法

### 1. 作为Python模块使用

#### 基本用法（仅提取文本）

```python
from pdf_to_json import PDFToJSONConverter

# 创建转换器实例
converter = PDFToJSONConverter()

# 转换PDF为字典
result = converter.convert("document.pdf")
print(f"提取了 {result['total_pages']} 页")

# 访问内容
for page in result['pages']:
    print(f"第 {page['page_number']} 页：")
    for paragraph in page['paragraphs']:
        print(paragraph)
```

#### 启用AI图片分析

```python
from pdf_to_json import PDFToJSONConverter

# 使用API Key初始化
converter = PDFToJSONConverter(api_key="your-dashscope-api-key")

# 转换并分析图片
result = converter.convert(
    "document.pdf",
    analyze_images=True,  # 启用AI分析
    verbose=True          # 显示进度
)
```

#### 直接保存为JSON文件

```python
from pdf_to_json import PDFToJSONConverter

converter = PDFToJSONConverter()
converter.convert_to_file(
    pdf_path="input.pdf",
    output_path="output.json",
    analyze_images=False
)
```

#### 获取JSON字符串

```python
from pdf_to_json import PDFToJSONConverter

converter = PDFToJSONConverter()
json_string = converter.convert_to_json_string("document.pdf")
print(json_string)
```

### 2. 使用命令行工具

```bash
# 基本转换（仅文本）
python pdf_to_json.py document.pdf

# 启用AI图片分析
export DASHSCOPE_API_KEY=your-api-key
python pdf_to_json.py document.pdf --analyze-images

# 保存到文件
python pdf_to_json.py document.pdf > output.json
```

### 3. 运行测试

```bash
# 运行完整测试套件
python test_converter.py sample.pdf

# 带AI分析的测试
export DASHSCOPE_API_KEY=your-api-key
python test_converter.py sample.pdf
```

## 输出格式

```json
{
  "total_pages": 2,
  "pages": [
    {
      "page_number": 1,
      "paragraphs": [
        "第一段文本内容",
        "| 表头1 | 表头2 | 表头3 |\n|-------|-------|-------|\n| 数据1 | 数据2 | 数据3 |",
        "第二段文本内容"
      ]
    },
    {
      "page_number": 2,
      "paragraphs": [
        "第二页的内容"
      ]
    }
  ]
}
```

## API文档

### PDFToJSONConverter

#### 初始化参数

- `api_key` (str, optional): 阿里云DashScope API密钥，默认从环境变量 `DASHSCOPE_API_KEY` 读取
- `base_url` (str, optional): API基础URL，默认为阿里云DashScope地址

#### 方法

##### `convert(pdf_path, analyze_images=False, verbose=False)`

转换PDF为字典格式。

**参数：**
- `pdf_path` (str): PDF文件路径
- `analyze_images` (bool): 是否启用AI图片分析
- `verbose` (bool): 是否显示进度信息

**返回：**
- `dict`: 包含页面和段落的结构化字典

##### `convert_to_json_string(pdf_path, analyze_images=False, verbose=False, indent=2)`

转换PDF为JSON字符串。

**参数：**
- `pdf_path` (str): PDF文件路径
- `analyze_images` (bool): 是否启用AI图片分析
- `verbose` (bool): 是否显示进度信息
- `indent` (int): JSON缩进级别

**返回：**
- `str`: JSON格式字符串

##### `convert_to_file(pdf_path, output_path, analyze_images=False, verbose=False, indent=2)`

转换PDF并保存为JSON文件。

**参数：**
- `pdf_path` (str): PDF文件路径
- `output_path` (str): 输出JSON文件路径
- `analyze_images` (bool): 是否启用AI图片分析
- `verbose` (bool): 是否显示进度信息
- `indent` (int): JSON缩进级别

## 环境变量

- `DASHSCOPE_API_KEY`: 阿里云DashScope API密钥（仅在使用AI图片分析时需要）

## 性能优化

- **图片缓存**：同一图片在多个位置出现时，只会分析一次
- **按需分析**：只有启用 `analyze_images=True` 时才会调用AI接口
- **流式处理**：逐页处理，避免内存占用过大

## 注意事项

1. **AI图片分析需要API密钥**：请确保设置了 `DASHSCOPE_API_KEY` 环境变量
2. **API调用成本**：启用图片分析会产生API调用费用
3. **处理时间**：大型PDF文件或包含大量图片时，处理可能需要较长时间
4. **表格识别**：AI会尝试将图片中的表格转换为Markdown格式

## 示例场景

### 场景1：批量处理PDF文件

```python
from pdf_to_json import PDFToJSONConverter
import os

converter = PDFToJSONConverter()

pdf_dir = "pdfs/"
output_dir = "json_output/"

for filename in os.listdir(pdf_dir):
    if filename.endswith(".pdf"):
        pdf_path = os.path.join(pdf_dir, filename)
        json_path = os.path.join(output_dir, filename.replace(".pdf", ".json"))

        print(f"Processing: {filename}")
        converter.convert_to_file(pdf_path, json_path, verbose=True)
```

### 场景2：提取特定页面的内容

```python
from pdf_to_json import PDFToJSONConverter

converter = PDFToJSONConverter()
result = converter.convert("document.pdf")

# 获取第3页的所有段落
page_3_paragraphs = result['pages'][2]['paragraphs']
for para in page_3_paragraphs:
    print(para)
```

### 场景3：与其他系统集成

```python
from pdf_to_json import PDFToJSONConverter
import requests

converter = PDFToJSONConverter()
result = converter.convert("document.pdf", analyze_images=True)

# 发送到API
response = requests.post(
    "https://your-api.com/documents",
    json=result
)
```

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！

## 更新日志

### v1.0.0 (2025-01-18)
- 初始版本发布
- 支持文本和图片位置保留
- 集成Qwen视觉大模型
- 智能图片缓存机制
- 表格识别和Markdown输出
