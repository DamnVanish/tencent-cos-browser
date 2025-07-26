from qcloud_cos import CosConfig, CosS3Client, CosServiceError
import json
import logging
import ssl
import os
from datetime import datetime
import openpyxl
from openpyxl.styles import Font
import mimetypes
import time

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

def upload_file(client, bucket_name, bucket_region, local_path, object_key):
    """上传文件到存储桶并显示URL"""
    # 检查文件是否存在
    if not os.path.isfile(local_path):
        print(f"错误: 本地文件 '{local_path}' 不存在")
        return None
    
    # 构建目标URL
    object_url = f"https://{bucket_name}.cos.{bucket_region}.myqcloud.com/{object_key}"
    print(f"上传文件: {local_path} → {object_url}")
    
    try:
        # 自动检测MIME类型
        mime_type, _ = mimetypes.guess_type(local_path)
        if not mime_type:
            mime_type = 'application/octet-stream'
        
        # 上传文件
        response = client.upload_file(
            Bucket=bucket_name,
            LocalFilePath=local_path,
            Key=object_key,
            PartSize=10,
            MAXThread=10,
            EnableMD5=False,
            Metadata={
                'Content-Type': mime_type
            }
        )
        
        # 检查上传结果
        if 'ETag' in response:
            print(f"上传成功! ETag: {response['ETag']}")
            return object_url
        else:
            print("上传失败: 未知错误")
            return None
            
    except CosServiceError as e:
        print(f"上传失败 (服务错误): {e.get_error_code()} - {e.get_error_msg()}")
        return None
    except Exception as e:
        print(f"上传失败: {str(e)}")
        return None

def save_to_excel(bucket_name, objects, output_dir):
    """将对象列表保存到Excel文件"""
    # 确保输出目录存在
    bucket_dir = os.path.join(output_dir, bucket_name)
    os.makedirs(bucket_dir, exist_ok=True)
    
    # 生成带时间戳的文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    excel_filename = f"objects-{timestamp}.xlsx"
    excel_path = os.path.join(bucket_dir, excel_filename)
    
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

def delete_file(client, bucket_name, bucket_region, object_key):
    """删除存储桶中的文件"""
    # 构建文件URL
    object_url = f"https://{bucket_name}.cos.{bucket_region}.myqcloud.com/{object_key}"
    print(f"准备删除文件: {object_url}")
    
    # 确认删除
    confirm = input(f"确定要永久删除 '{object_key}' 吗? (y/n): ").lower()
    if confirm != 'y':
        print("取消删除操作")
        return False
    
    try:
        # 删除文件
        response = client.delete_object(
            Bucket=bucket_name,
            Key=object_key
        )
        
        print(f"文件删除成功: {object_key}")
        return True
        
    except CosServiceError as e:
        print(f"删除失败 (服务错误): {e.get_error_code()} - {e.get_error_msg()}")
        return False
    except Exception as e:
        print(f"删除失败: {str(e)}")
        return False

def delete_folder(client, bucket_name, bucket_region, folder_prefix):
    """删除文件夹及其所有内容"""
    # 确保文件夹前缀以/结尾
    if not folder_prefix.endswith('/'):
        folder_prefix += '/'
    
    print(f"准备删除文件夹: {folder_prefix}")
    
    # 确认删除
    confirm = input(f"确定要永久删除文件夹 '{folder_prefix}' 及其所有内容吗? (y/n): ").lower()
    if confirm != 'y':
        print("取消删除操作")
        return False
    
    try:
        # 获取文件夹中的所有对象
        marker = ''
        deleted_files = 0
        
        while True:
            response = client.list_objects(
                Bucket=bucket_name,
                Prefix=folder_prefix,
                Marker=marker,
                MaxKeys=1000
            )
            
            if 'Contents' not in response:
                print("文件夹为空，无需删除")
                return 0
                
            # 准备删除列表
            delete_list = []
            for obj in response['Contents']:
                delete_list.append({'Key': obj['Key']})
                
            # 批量删除
            if delete_list:
                delete_result = client.delete_objects(
                    Bucket=bucket_name,
                    Delete={'Objects': delete_list}
                )
                deleted_files += len(delete_list)
                print(f"已删除 {len(delete_list)} 个文件")
            
            # 检查是否还有更多文件
            if response.get('IsTruncated') == 'false':
                break
                
            marker = response['Contents'][-1]['Key']
        
        print(f"文件夹删除完成，共删除 {deleted_files} 个文件")
        return deleted_files
        
    except Exception as e:
        print(f"删除文件夹失败: {str(e)}")
        return 0

def print_help():
    """打印帮助信息"""
    print("\n可用命令:")
    print("  back       - 返回存储桶列表")
    print("  upload     - 上传文件到当前存储桶")
    print("  download   - 下载文件或文件夹")
    print("  delete     - 删除文件或文件夹")
    print("  refresh    - 刷新当前存储桶对象列表")
    print("  exit       - 退出程序")
    print("  help       - 显示此帮助信息")

def print_upload_help():
    """打印上传帮助信息"""
    print("\n上传文件格式:")
    print("  [本地文件路径] [存储桶路径]")
    print("示例:")
    print("  C:\\test.txt test/test.txt")
    print("  /tmp/test.txt test/test.txt")

def print_delete_help():
    """打印删除帮助信息"""
    print("\n删除操作格式:")
    print("  [文件键]       - 删除单个文件")
    print("  [文件夹键/]    - 删除整个文件夹")
    print("示例:")
    print("  index/index.html")
    print("  index/")

def display_bucket_objects(bucket_client, bucket_name, bucket_region):
    """显示存储桶对象列表"""
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
        return objects
    else:
        print(f"存储桶 '{bucket_name}' 为空")
        return []
    
    return objects

try:
    
    # 列出所有存储桶
    print("="*50)
    print("腾讯云 COS 渗透测试工具")
    print("功能: 存储桶枚举 | 文件下载 | 文件上传 | 敏感数据识别")
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
            bucket_name = input("请输入要操作的存储桶名称 (或输入 'exit' 退出): ").strip()
            
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
                # 显示存储桶对象
                objects = display_bucket_objects(bucket_client, bucket_name, bucket_region)
                    
                # 文件操作交互
                while True:
                    print("\n" + "="*50)
                    print("文件操作菜单 (输入 'help' 查看命令)")
                    print("="*50)
                    command = input("请输入命令: ").strip()
                    
                    if command.lower() == 'back':
                        print("返回存储桶列表")
                        break
                        
                    elif command.lower() == 'exit':
                        print("退出程序")
                        exit()
                        
                    elif command.lower() == 'help':
                        print_help()
                        
                    elif command.lower() == 'refresh':
                        print("刷新存储桶对象列表...")
                        objects = display_bucket_objects(bucket_client, bucket_name, bucket_region)
                        
                    elif command.lower() == 'upload':
                        print_upload_help()
                        upload_cmd = input("请输入上传命令 (本地路径 存储桶路径): ").strip()
                        parts = upload_cmd.split(maxsplit=1)
                        
                        if len(parts) < 2:
                            print("错误: 参数不足，需要两个路径参数")
                            continue
                            
                        local_path = parts[0]
                        object_key = parts[1]
                        
                        # 执行上传
                        uploaded_url = upload_file(bucket_client, bucket_name, bucket_region, local_path, object_key)
                        
                        if uploaded_url:
                            print(f"上传文件访问URL: {uploaded_url}")
                            
                            # 刷新对象列表
                            print("\n刷新存储桶对象列表...")
                            time.sleep(2)  # 等待文件上传完成
                            objects = display_bucket_objects(bucket_client, bucket_name, bucket_region)
                            
                            # 检查新上传的文件是否在列表中
                            new_file_exists = any(obj['Key'] == object_key for obj in objects)
                            if new_file_exists:
                                print(f"新上传的文件 '{object_key}' 已在对象列表中")
                            else:
                                print(f"警告: 新上传的文件 '{object_key}' 未在对象列表中找到")
                        
                    elif command.lower() == 'download':
                        file_key = input("请输入要下载的文件键: ").strip()
                        
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
                        
                    elif command.lower() == 'delete':
                        print_delete_help()
                        object_key = input("请输入要删除的文件或文件夹键: ").strip()
                        
                        # 检查是否文件夹删除
                        if object_key.endswith('/'):
                            # 删除文件夹
                            deleted_count = delete_folder(bucket_client, bucket_name, bucket_region, object_key)
                            if deleted_count > 0:
                                # 刷新对象列表
                                print("\n刷新存储桶对象列表...")
                                time.sleep(2)  # 等待删除完成
                                objects = display_bucket_objects(bucket_client, bucket_name, bucket_region)
                        else:
                            # 删除单个文件
                            if delete_file(bucket_client, bucket_name, bucket_region, object_key):
                                # 刷新对象列表
                                print("\n刷新存储桶对象列表...")
                                time.sleep(2)  # 等待删除完成
                                objects = display_bucket_objects(bucket_client, bucket_name, bucket_region)
                    
                    else:
                        print("未知命令，输入 'help' 查看可用命令")
            
            except Exception as e:
                print(f"操作失败: {str(e)}")
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
