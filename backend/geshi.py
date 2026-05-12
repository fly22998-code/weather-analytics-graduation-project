import pandas as pd
import os

def fill_empty_aqi_in_excel():
    # 文件路径
    file_path = "./数据集.xlsx"
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")

    # 读取Excel文件
    try:
        df = pd.read_excel(file_path, sheet_name='Sheet1')
    except Exception as e:
        raise Exception(f"读取Excel失败: {str(e)}")

    # 处理空气质量指数为空的情况：填充为 '-'
    # 注意：确保列名与Excel中的实际列名一致（这里假设列名为“空气质量指数”）
    if '空气质量指数' in df.columns:
        # 将空值（NaN）替换为 '-'
        df['空气质量指数'] = df['空气质量指数'].fillna('-')
        print(f"已处理空值，共替换 {df[df['空气质量指数'] == '-'].shape[0]} 处空值")
    else:
        raise ValueError("Excel中未找到'空气质量指数'列，请检查列名是否正确")

    # 保存修改后的Excel（覆盖原文件，或指定新路径）
    try:
        # 覆盖原文件（注意：操作前建议备份）
        df.to_excel(file_path, sheet_name='Sheet1', index=False)
        print(f"修改完成，已保存至 {file_path}")
    except Exception as e:
        raise Exception(f"保存Excel失败: {str(e)}")

if __name__ == "__main__":
    fill_empty_aqi_in_excel()