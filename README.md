# 腾讯云 COS browser 临时凭据版

## 项目概述

此脚本是我用ai快速写的一个用于在只有临时凭据（也就是sts，临时密钥由 TmpSecretId、TmpSecretKey 和 Token 三部分组成）的情况下访问cos的存储桶的小脚本，没啥技术含量，只是我看那个云资产管理工具没有提供腾讯云的临时凭据接管的方法没办法只能看官方文档搓一个🤡🤡🤡

## 功能特性

### 🔍 存储桶枚举
- 列出账户所有存储桶及元数据（地域、创建时间、类型）
- 显示存储桶所有者信息
- 表格化展示存储桶列表

### 📁 文件管理
- **文件上传**：支持本地文件上传到指定路径
- **文件下载**：支持单个文件或整个文件夹下载
- **文件删除**：支持删除单个文件或递归删除文件夹
- **自动刷新**：操作后自动刷新存储桶对象列表

### 📊 数据展示
- 智能分页显示（≤100直接显示，>100保存为Excel）
- 自动生成带时间戳的Excel报告（`objects-YYYYMMDD_HHMMSS.xlsx`）
- 对象键自动截断显示优化

### 🔐 安全特性
- 操作前二次确认（删除/文件夹操作）
- 完整的URL显示（上传/下载）
- 临时凭证自动清理

## 渗透测试用途

### 红队场景
- 验证临时凭证权限范围
- 测试存储桶ACL配置错误
- 识别敏感数据泄露
- 部署/清理测试文件
- 验证路径遍历漏洞


## 安装使用

### 环境要求
- Python 3.6+
- 腾讯云临时访问凭证（三个）

### 快速开始
```bash
# 克隆仓库
git clone https://github.com/DamnVanish/tencent-cos-browser.git
cd cos-penetration-tool

# 创建虚拟环境（推荐）
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
.\.venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 配置凭证
编辑cos_explorer.py中的config部分：
config = CosConfig(
    Region='ap-beijing',
    Secret_id='您的SecretId',
    Secret_key='您的SecretKey',
    Token='您的SessionToken',
    Scheme='https'
)

# 运行工具
python cos_explorer.py
```

## 使用示例

### 基本操作流程
```bash
# 1. 列出存储桶
==================================================
存储桶名称                    地域            创建时间              类型
==========================================================================================
test-bucket-1               ap-beijing      2023-01-15T08:00:00Z  cos
prod-backup-1250000000      ap-shanghai     2023-05-20T12:30:45Z  cos

# 2. 选择存储桶
请输入要操作的存储桶名称: prod-backup-1250000000

# 3. 查看内容
存储桶 'prod-backup-1250000000' 包含 125 个对象
显示前100个对象 (完整列表请查看Excel文件)...

# 4. 上传文件
请输入命令: upload
请输入上传命令: /tmp/test.txt test/test.txt
上传成功! 访问URL: https://prod-backup-1250000000.cos.ap-shanghai.myqcloud.com/test/test.txt

# 5. 删除文件
请输入命令: delete
请输入要删除的文件键: test/test.txt
文件删除成功
```

### 批量操作示例
```bash
# 递归下载文件夹
download config/
下载: https://xxx.cos.xxx.myqcloud.com/config/db.properties
下载: https://xxx.cos.xxx.myqcloud.com/config/redis.conf
共下载 8 个文件

# 递归删除文件夹
delete temp_uploads/
确定要永久删除文件夹 'temp_uploads/' 吗? (y/n): y
已删除 15 个文件
```

## 命令参考

| 命令       | 描述                          | 示例                      |
|------------|-------------------------------|--------------------------|
| upload     | 上传文件                      | upload local.txt remote.txt |
| download   | 下载文件/文件夹               | download config/          |
| delete     | 删除文件/文件夹               | delete test.php           |
| refresh    | 刷新对象列表                  | refresh                   |
| back       | 返回存储桶列表                | back                      |
| exit       | 退出程序                      | exit                      |
| help       | 显示帮助信息                  | help                      |

## 项目结构
```
.
├── cos_explorer.py          # 主程序
├── requirements.txt         # 依赖清单
├── README.md                # 本文档
└── .gitignore               # Git忽略配置
```

## 依赖清单
```text
cos-python-sdk-v5>=1.9.21    # 腾讯云官方SDK
openpyxl>=3.1.2              # Excel报告生成
requests>=2.31.0             # HTTP请求库
urllib3>=2.0.4               # URL处理库
```

## 注意事项

1. **合法使用**：仅用于授权测试，未经许可使用可能违反法律
2. **凭证安全**：妥善保管临时凭证，测试后立即撤销
3. **操作审计**：建议开启COS操作日志功能
4. **数据备份**：删除操作不可逆，重要数据请先备份

## 免责声明

本工具仅用于授权安全测试和教育目的。使用者应确保遵守所有适用法律，并获得目标系统的明确授权。开发者对工具的滥用不承担任何责任。

---

**使用此工具即表示您同意对自己的行为负全部责任，并确保在合法授权的范围内使用。**
