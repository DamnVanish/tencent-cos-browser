# 腾讯云 COS browser 临时凭据版

## 项目概述

此脚本是我用ai快速写的一个用于在只有临时凭据（也就是sts，临时密钥由 TmpSecretId、TmpSecretKey 和 Token 三部分组成）的情况下访问cos的存储桶的小脚本，没啥技术含量，只是我看那个云资产管理工具没有提供腾讯云的临时凭据接管的方法没办法只能看官方文档搓一个🤡🤡🤡

## 主要功能

- ✅ **存储桶枚举**：列出账户所有存储桶及其元数据
- 🔍 **对象分析**：查看存储桶内容并识别潜在敏感文件
- ⬇️ **文件下载**：支持单个文件和整个文件夹下载
- 📊 **数据导出**：自动将大型对象列表导出到Excel文件方便观看
- 🔐 **凭证管理**：临时凭证安全使用和自动清理
- 📁 **结果组织**：按存储桶名称自动创建目录结构

## 渗透测试应用场景

1. **云凭证泄露利用**：当获取临时访问密钥时，快速评估凭证权限范围
2. **存储桶权限审计**：检查存储桶ACL配置错误和公开访问风险
3. **敏感数据识别**：扫描存储桶中可能的配置文件、备份文件和日志文件
4. **数据外泄取证**：下载关键证据文件用于后续分析
5. **红队行动支持**：在授权渗透测试中快速评估云存储风险

## 安装与使用

### 推荐使用虚拟环境

为避免依赖冲突，强烈建议使用Python虚拟环境运行本项目：

```bash
# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
# Windows:
.\.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 运行工具

```bash
python cos_explorer.py
```

### 配置凭证

编辑 `cos_explorer.py` 文件，在以下位置替换为您的临时凭证：

```python
config = CosConfig(
    Region='ap-beijing',
    Secret_id='YOUR_TMP_SECRET_ID',
    Secret_key='YOUR_TMP_SECRET_KEY',
    Token='YOUR_SESSION_TOKEN',
    #Scheme='https'
)
```

## 使用示例

```bash
# 列出所有存储桶
==========================================================================================
存储桶名称                    地域            创建时间              类型
==========================================================================================
xxxxx-1306817765            ap-chengdu     2023-06-18T15:09:21Z  cos
yyyyy-1306817765            ap-nanjing     2023-06-12T08:54:26Z  cos
backup-1306817765           ap-shanghai    2023-08-01T10:15:33Z  cos

# 选择存储桶查看内容
请输入要查看的存储桶名称 (或输入 'exit' 退出): xxxxx-1306817765

# 查看对象列表
存储桶 'xxxxx-1306817765' 包含 1205 个对象
显示前100个对象 (完整列表请查看Excel文件):

对象键                                                大小(字节)     最后修改时间
----------------------------------------------------------------------------------
config/database.yml                               1024        2025-07-25T08:12:45.000Z
backups/db.sql.gz                                 5242880     2025-07-24T22:15:30.000Z
logs/access.log                                   20480       2025-07-26T10:30:15.000Z
... (显示前100个对象)...
完整对象列表已保存到: /path/to/xxxxx-1306817765/objects.xlsx

# 下载文件
输入要下载的文件键: config/database.yml
下载文件: https://xxxxx-1306817765.cos.ap-nanjing.myqcloud.com/config/database.yml
文件已下载到: /downloads/config/database.yml

# 下载文件夹
输入要下载的文件键: backups/
您要下载整个文件夹 'backups/' 吗? (y/n): y
开始下载文件夹: backups/
下载: https://xxxxx-1306817765.cos.ap-nanjing.myqcloud.com/backups/db.sql.gz
下载: https://xxxxx-1306817765.cos.ap-nanjing.myqcloud.com/backups/app.tar
...
文件夹下载完成，共下载 15 个文件
```

## 渗透测试技巧

1. **敏感文件扫描**：重点关注以下文件类型：
   - 配置文件：`.env`, `config.*`, `*.yml`, `*.properties`
   - 数据库备份：`*.sql`, `*.dump`, `*.bak`
   - 日志文件：`*.log`, `access.*`
   - 凭据文件：`credentials.*`, `*.pem`, `*.key`

2. **权限提升尝试**：
   - 检查存储桶ACL：`client.get_bucket_acl()`
   - 尝试写入可执行文件：`.php`, `.jsp`, `.sh`
   - 寻找跨账户访问可能性

3. **数据泄露风险评估**：
   - 检查公开访问配置
   - 识别包含PII/PHI数据的文件
   - 评估存储桶中数据的敏感级别

## 安全与合规

- ⚠️ **仅用于授权测试**：在未获得明确授权的情况下使用此工具可能违反法律
- 🔒 **最小权限原则**：使用仅具有必要权限的临时凭证
- 🗑️ **数据清理**：测试完成后删除所有下载的文件
- 📝 **操作审计**：记录所有执行的操作以便审查

## 依赖安装

创建 `requirements.txt` 文件：

```
cos-python-sdk-v5==1.9.21
openpyxl==3.1.2
requests==2.31.0
urllib3==2.0.4
```

安装依赖：

```bash
pip install -r requirements.txt
```

## 项目结构

```
.
├── cos_explorer.py          # 主程序
├── requirements.txt         # 依赖列表
├── README.md                # 项目文档
└── .gitignore               # Git忽略文件
```
## 演示
<img width="1829" height="1262" alt="image" src="https://github.com/user-attachments/assets/61345401-2a06-444e-9923-c0f906fb8f9a" />
<img width="2460" height="460" alt="image" src="https://github.com/user-attachments/assets/7dae8f44-a84f-499b-b9b5-6b809c216250" />


## 贡献与反馈

欢迎提交Issue和Pull Request

## 免责声明

本工具仅用于授权安全测试和教育目的。使用者应确保遵守所有适用法律，并获得目标系统的明确授权。开发者对工具的滥用不承担任何责任。

---

**使用此工具即表示您同意对自己的行为负全部责任，并确保在合法授权的范围内使用。**
