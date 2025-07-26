from qcloud_cos import CosConfig, CosS3Client
import json
import logging
import ssl
import os
from datetime import datetime
import re
import openpyxl
from openpyxl.styles import Font

# 禁用SSL证书验证（解决主机名不匹配问题）
ssl._create_default_https_context = ssl._create_unverified_context

# 配置详细日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# 使用您提供的临时凭证
config = CosConfig(
    Region='ap-beijing', #这里默认就行，后面具体到桶的时候会自动选择对应的区域
    Secret_id='YOUR_TMP_SECRET_ID',  #一般是AKID开头
    Secret_key='YOUR_TMP_SECRET_KEY',
    Token='YOUR_SESSION_TOKEN',
    #Scheme='https'  这个字段看情况，一般都是https，也不知道代码中有些http的没
)
# 创建客户端
client = CosS3Client(config)

def print_bucket_table(buckets):
    """打印存储桶表格"""
    print("\n" + "="*90)
    print(f"{'存储桶名称':<30} {'地域':<15} {'创建时间':<20} {'类型':<10}")
    print("="*90)
    for bucket in buckets:
        print(f"{bucket.get('Name'):<30} {bucket.get('Location'):<15} {bucket.get('CreationDate'):<20} {bucket.get('BucketType', 'cos'):<10}")
    print("="*90)

def download_file(client, bucket_name, bucket_region, file_key, save_path):
    """下载单个文件并显示URL"""
    # 构建文件URL
    file_url = f"https://{bucket_name}.cos.{bucket_region}.myqcloud.com/{file_key}"
    print(f"下载文件: {file_url}")
    
    # 确保保存目录存在
    local_path = os.path.join(save_path, os.path.basename(file_key))
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    
    try:
        # 下载文件
        client.download_file(
            Bucket=bucket_name,
            Key=file_key,
            DestFilePath=local_path
        )
        print(f"文件已下载到: {local_path}")
        return True
    except Exception as e:
        print(f"下载失败: {str(e)}")
        return False

def download_folder(client, bucket_name, bucket_region, folder_prefix, save_path):
    """下载文件夹中的所有文件"""
    print(f"开始下载文件夹: {folder_prefix}")
    
    # 确保文件夹前缀以/结尾
    if not folder_prefix.endswith('/'):
        folder_prefix += '/'
    
    # 获取文件夹中的所有对象
    marker = ''
    downloaded_files = 0
    
    while True:
        response = client.list_objects(
            Bucket=bucket_name,
            Prefix=folder_prefix,
            Marker=marker,
            MaxKeys=100
        )
        
        if 'Contents' not in response:
            print("文件夹为空")
            return 0
            
        # 下载每个文件
        for obj in response['Contents']:
            # 跳过文件夹本身
            if obj['Key'] == folder_prefix:
                continue
                
            # 下载文件
            file_url = f"https://{bucket_name}.cos.{bucket_region}.myqcloud.com/{obj['Key']}"
            print(f"下载: {file_url}")
            
            local_path = os.path.join(save_path, os.path.relpath(obj['Key'], folder_prefix))
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            try:
                client.download_file(
                    Bucket=bucket_name,
                    Key=obj['Key'],
                    DestFilePath=local_path
                )
                downloaded_files += 1
            except Exception as e:
                print(f"下载失败 ({obj['Key']}): {str(e)}")
        
        # 检查是否还有更多文件
        if response.get('IsTruncated') == 'false':
            break
            
        marker = response['Contents'][-1]['Key']
    
    print(f"文件夹下载完成，共下载 {downloaded_files} 个文件")
    return downloaded_files

def save_to_excel(bucket_name, objects, output_dir):
    """将对象列表保存到Excel文件"""
    # 确保输出目录存在
    bucket_dir = os.path.join(output_dir, bucket_name)
    os.makedirs(bucket_dir, exist_ok=True)
    
    # 创建Excel文件路径
    excel_path = os.path.join(bucket_dir, "objects.xlsx")
    
    # 创建工作簿和工作表
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "对象列表"
    
    # 添加标题行
    ws.append(["对象键", "大小(字节)", "最后修改时间"])
    
    # 设置标题行样式
    for cell in ws[1]:
        cell.font = Font(bold=True)
    
    # 添加数据
    for obj in objects:
        ws.append([obj.get('Key'), obj.get('Size'), obj.get('LastModified')])
    
    # 自动调整列宽
    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter
        for cell in col:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = (max_length + 2)
        ws.column_dimensions[column].width = adjusted_width
    
    # 保存文件
    wb.save(excel_path)
    print(f"对象列表已保存到: {excel_path}")
    return excel_path

try:
    # 列出所有存储桶
    print("="*50)
    print("获取存储桶列表...")
    print("="*50)
    
    response = client.list_buckets()
    
    # 解析存储桶列表
    if 'Buckets' in response and 'Bucket' in response['Buckets']:
        buckets = response['Buckets']['Bucket']
        owner = response.get('Owner', {})
        
        print(f"\n账户存储桶列表 (共 {len(buckets)} 个)")
        print(f"账户所有者: {owner.get('DisplayName', '未知')} ({owner.get('ID', '未知ID')})")
        
        # 主交互循环
        while True:
            # 打印存储桶列表
            print_bucket_table(buckets)
            
            print("\n" + "="*50)
            bucket_name = input("请输入要查看的存储桶名称 (或输入 'exit' 退出): ").strip()
            
            if bucket_name.lower() == 'exit':
                print("退出程序")
                break
                
            # 检查输入是否有效
            selected_bucket = next((b for b in buckets if b['Name'] == bucket_name), None)
            
            if not selected_bucket:
                print(f"错误: 存储桶 '{bucket_name}' 不存在于列表中")
                continue
                
            # 获取存储桶地域
            bucket_region = selected_bucket['Location']
            
            # 为特定存储桶创建新客户端
            print(f"为存储桶 '{bucket_name}' 创建客户端 (地域: {bucket_region})...")
            bucket_config = CosConfig(
                Region=bucket_region,
                Secret_id=config._secret_id,
                Secret_key=config._secret_key,
                Token=config._token,
                Scheme='https'
            )
            bucket_client = CosS3Client(bucket_config)
            
            try:
                print("\n获取存储桶内容...")
                objects_response = bucket_client.list_objects(
                    Bucket=bucket_name,
                    MaxKeys=1000  # 获取最多1000个对象
                )
                
                # 处理对象列表
                if 'Contents' in objects_response:
                    objects = objects_response['Contents']
                    total_objects = len(objects)
                    print(f"\n存储桶 '{bucket_name}' 包含 {total_objects} 个对象")
                    
                    # 对象数量超过100时保存到Excel
                    if total_objects > 100:
                        # 保存到Excel
                        excel_path = save_to_excel(bucket_name, objects, os.getcwd())
                        
                        # 在控制台显示前100个对象
                        print(f"\n显示前100个对象 (完整列表请查看Excel文件):")
                        print("\n{:<50} {:<10} {:<20}".format("对象键", "大小(字节)", "最后修改时间"))
                        print("-"*90)
                        for i, obj in enumerate(objects[:100]):
                            key = obj.get('Key')
                            # 截断过长的键
                            if len(key) > 48:
                                key = key[:45] + "..."
                            print("{:<50} {:<10} {:<20}".format(
                                key,
                                obj.get('Size'),
                                obj.get('LastModified')
                            ))
                        print(f"... 省略 {total_objects-100} 个对象 ...")
                        print(f"完整对象列表已保存到: {excel_path}")
                    else:
                        # 显示所有对象
                        print("\n{:<50} {:<10} {:<20}".format("对象键", "大小(字节)", "最后修改时间"))
                        print("-"*90)
                        for obj in objects:
                            key = obj.get('Key')
                            # 截断过长的键
                            if len(key) > 48:
                                key = key[:45] + "..."
                            print("{:<50} {:<10} {:<20}".format(
                                key,
                                obj.get('Size'),
                                obj.get('LastModified')
                            ))
                else:
                    print(f"存储桶 '{bucket_name}' 为空")
                    
                # 文件下载交互
                while True:
                    print("\n" + "="*50)
                    file_key = input("输入要下载的文件键 (或 'back' 返回存储桶列表): ").strip()
                    
                    if file_key.lower() == 'back':
                        print("返回存储桶列表")
                        break
                        
                    # 检查是否文件夹下载
                    if file_key.endswith('/'):
                        confirm = input(f"您要下载整个文件夹 '{file_key}' 吗? (y/n): ").lower()
                        if confirm != 'y':
                            print("取消文件夹下载")
                            continue
                            
                        # 设置保存路径
                        save_path = input("请输入本地保存目录 (默认: 当前目录): ").strip() or os.getcwd()
                        save_path = os.path.join(save_path, os.path.basename(file_key.rstrip('/')))
                        
                        # 下载文件夹
                        download_folder(bucket_client, bucket_name, bucket_region, file_key, save_path)
                    else:
                        # 设置保存路径
                        save_path = input("请输入本地保存目录 (默认: 当前目录): ").strip() or os.getcwd()
                        
                        # 下载单个文件
                        download_file(bucket_client, bucket_name, bucket_region, file_key, save_path)
                
            except Exception as e:
                print(f"访问存储桶内容失败: {str(e)}")
                print("可能原因: 权限不足或网络问题")
                
            finally:
                # 清理桶客户端
                del bucket_client
                
    else:
        print("\n错误: 响应中未找到存储桶信息")
        
except Exception as e:
    print("\n" + "="*50)
    print(f"操作失败: {str(e)}")
    print("="*50)
    import traceback
    traceback.print_exc()

finally:
    # 清理主客户端
    del client
    print("\n程序结束")
