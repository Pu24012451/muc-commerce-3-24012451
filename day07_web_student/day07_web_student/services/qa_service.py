from pathlib import Path

import pandas as pd


def answer_question(base_dir: Path, question: str) -> str:
    data_dir = base_dir / "data"
    
    # 读取所有数据
    metrics_df = pd.read_csv(data_dir / "overall_metrics.csv", encoding="utf-8-sig")
    metrics = dict(zip(metrics_df["指标"], metrics_df["数值"]))
    
    category_df = pd.read_csv(data_dir / "category_analysis.csv", encoding="utf-8-sig")
    segment_df = pd.read_csv(data_dir / "segment_analysis.csv", encoding="utf-8-sig")
    
    normalized = question.replace(" ", "").lower()
    
    # 1. 总体规模 - 用户数
    if any(word in normalized for word in ["多少用户", "用户数", "总用户", "多少人"]):
        return f"数据集中共有{int(metrics['用户数']):,}名用户。"
    
    # TODO 4-1：补充"流失率""偏好品类""生命周期风险"和"订单"四类问答。
    
    # 2. 流失情况 - 流失率和流失人数
    if any(word in normalized for word in ["流失率", "流失情况", "流失多少", "流失人数"]):
        churn_rate = (int(metrics['流失人数']) / int(metrics['用户数']) * 100) if int(metrics['用户数']) > 0 else 0
        return f"总体流失率为 {churn_rate:.1f}%，流失人数为 {int(metrics['流失人数']):,} 人。"
    
    # 3. 偏好品类 - 哪个品类用户最多
    if any(word in normalized for word in ["品类", "哪个品类", "最多用户", "偏好", "最多人"]):
        # 找出用户数最多的品类
        max_idx = category_df['用户数'].idxmax()
        top_category = category_df.loc[max_idx, 'PreferedOrderCat']
        top_users = int(category_df.loc[max_idx, '用户数'])
        return f"用户最多的偏好品类是「{top_category}」，共有 {top_users:,} 名用户。"
    
    # 4. 生命周期风险 - 哪个阶段风险最高
    if any(word in normalized for word in ["生命周期", "阶段", "风险最高", "哪个阶段", "流失最高"]):
        # 找出流失率最高的阶段
        max_idx = segment_df['流失率'].idxmax()
        top_segment = segment_df.loc[max_idx, 'TenureGroup']
        top_churn_rate = segment_df.loc[max_idx, '流失率'] * 100
        top_users = int(segment_df.loc[max_idx, '用户数'])
        return f"流失率最高的生命周期阶段是「{top_segment}」，流失率为 {top_churn_rate:.1f}%，该阶段有 {top_users:,} 名用户。"
    
    # 5. 订单情况 - 平均订单数
    if any(word in normalized for word in ["订单", "平均订单", "订单数", "下单"]):
        # 从category_df计算加权平均
        weighted_orders = (category_df['用户数'] * category_df['平均订单数']).sum()
        total_users = category_df['用户数'].sum()
        avg_orders = weighted_orders / total_users if total_users > 0 else 0
        
        # 计算中位数（从category_df计算）
        # 使用加权中位数的近似计算
        sorted_df = category_df.sort_values('平均订单数')
        cumsum = 0
        median_orders = 0
        half_total = total_users / 2
        for _, row in sorted_df.iterrows():
            cumsum += row['用户数']
            if cumsum >= half_total:
                median_orders = row['平均订单数']
                break
        
        return f"平均订单数为 {avg_orders:.2f} 单，订单数中位数为 {median_orders:.2f} 单。"
    
    # 6. 不支持的问题 - 友好提示
    return (
        "抱歉，我目前只能回答以下几类问题：\n"
        "1. 总体规模：系统中有多少用户？\n"
        "2. 流失情况：总体流失率是多少？\n"
        "3. 偏好品类：哪个品类用户最多？\n"
        "4. 生命周期：哪个阶段风险最高？\n"
        "5. 订单情况：平均订单数是多少？\n"
        "请换一种更具体的问法。"
    )