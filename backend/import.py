import pandas as pd
from django.core.exceptions import ImproperlyConfigured  # 修正拼写错误，添加空格
import os
from datetime import datetime

def import_weather_data():
    # 导入模型
    from weather_app.models import Weather

    # 文件路径（Excel文件）
    file_path = "./数据集.xlsx"
    if not os.path.exists(file_path):
        raise ImproperlyConfigured(f"文件不存在: {file_path}")

    # 读取Excel文件
    try:
        excel_file = pd.ExcelFile(file_path)
        df = excel_file.parse('Sheet1')  # 修正：使用括号调用方法
    except Exception as e:
        raise ImproperlyConfigured(f"读取Excel文件失败: {str(e)}")

    # 清理日期（提取 YYYY-MM-DD 部分）
    df['日期'] = df['日期'].str.extract(r'(\d{4}-\d{2}-\d{2})')[0]
    
    # 过滤无效日期
    df = df.dropna(subset=['日期'])
    
    # 验证日期格式
    valid_dates = []
    for date_str in df['日期']:
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
            valid_dates.append(True)
        except ValueError:
            valid_dates.append(False)
    df = df[valid_dates]

    # 批量导入数据库
    success_count = 0
    for idx, row in df.iterrows():
        try:
            Weather.objects.get_or_create(
                city=row['城市'],
                date=row['日期'],
                defaults={
                    'max_temp': row['最高温'],
                    'min_temp': row['最低温'],
                    'weather': row['天气'],
                    'wind': row['风力风向'],
                    'aqi': row['空气质量指数']
                }
            )
            success_count += 1
        except Exception as e:
            print(f"导入失败（行号: {idx}，数据: {row.to_dict()}），错误: {str(e)}")

    print(f"导入完成 - 成功: {success_count} 条, 总处理: {len(df)} 条")

if __name__ == "__main__":
    # 配置Django环境
    import django
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "weather_project.settings")
    django.setup()
    
    # 执行导入
    import_weather_data()