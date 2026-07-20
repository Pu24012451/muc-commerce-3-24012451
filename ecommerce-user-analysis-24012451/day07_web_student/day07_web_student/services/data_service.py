from pathlib import Path

import pandas as pd


def _read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, encoding="utf-8-sig")


def load_dashboard_data(base_dir: Path, selected_category: str = "全部") -> dict:
    data_dir = base_dir / "data"
    metrics_df = _read_csv(data_dir / "overall_metrics.csv")
    category_df = _read_csv(data_dir / "category_analysis.csv")
    segment_df = _read_csv(data_dir / "segment_analysis.csv")

    metric_map = dict(zip(metrics_df["指标"], metrics_df["数值"]))
    
    # TODO 2-1：在已有两张指标卡基础上，增加"总体流失率"和"平均订单数"。
    total_users = int(metric_map['用户数'])
    churned_users = int(metric_map['流失人数'])
    
    # 计算总体流失率
    churn_rate = (churned_users / total_users * 100) if total_users > 0 else 0
    
    # 计算平均订单数（从category_df计算加权平均）
    weighted_orders = (category_df['用户数'] * category_df['平均订单数']).sum()
    total_users_for_avg = category_df['用户数'].sum()
    avg_orders = weighted_orders / total_users_for_avg if total_users_for_avg > 0 else 0
    
    metrics = [
        {"label": "总用户数", "value": f"{total_users:,}", "note": "人"},
        {"label": "流失用户", "value": f"{churned_users:,}", "note": "人"},
        {"label": "总体流失率", "value": f"{churn_rate:.1f}", "note": "%"},
        {"label": "平均订单数", "value": f"{avg_orders:.2f}", "note": "单"},
    ]

    categories = ["全部", *category_df["PreferedOrderCat"].tolist()]
    table_df = category_df.copy()
    
    # TODO 3-1：选择具体品类后筛选table_df。
    if selected_category != "全部":
        table_df = table_df[table_df["PreferedOrderCat"] == selected_category]

    table_df = table_df.rename(
        columns={
            "PreferedOrderCat": "偏好品类",
            "用户数": "用户数",
            "流失率": "流失率",
            "平均订单数": "平均订单数",
        }
    )[["偏好品类", "用户数", "流失率", "平均订单数"]]
    table_df["流失率"] = table_df["流失率"].map(lambda value: f"{value:.1%}")
    table_df["平均订单数"] = table_df["平均订单数"].map(lambda value: f"{value:.2f}")

    # TODO 2-2：找出流失率最高的生命周期阶段，并生成一句数据观察。
    # 找出流失率最高的生命周期阶段
    highest_churn_idx = segment_df['流失率'].idxmax()
    highest_segment = segment_df.loc[highest_churn_idx, 'TenureGroup']  # 改这里
    highest_churn_rate = segment_df.loc[highest_churn_idx, '流失率'] * 100
    segment_user_count = int(segment_df.loc[highest_churn_idx, '用户数'])
    
    insight = (
        f"生命周期阶段「{highest_segment}」的流失率最高，达到 {highest_churn_rate:.1f}%，"
        f"该阶段共有 {segment_user_count:,} 名用户。建议重点关注该阶段的用户留存策略，"
        f"分析流失原因并制定针对性的干预措施。"
    )

    return {
        "metrics": metrics,
        "categories": categories,
        "category_rows": table_df.to_dict("records"),
        "insight": insight,
    }