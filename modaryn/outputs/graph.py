from typing import List, Dict, Tuple

from modaryn.domain.model import DbtProject, DbtModel

def _get_node_color_by_score(score: float, max_score: float) -> str:
    """
    モデルのスコアに基づいてノードの色を決定します。
    スコアが高いほど赤に近く、低いほど緑に近くなります。
    """
    if max_score == 0:
        return "#ADD8E6"  # Light Blue for no score

    # スコアを0-1の範囲に正規化
    normalized_score = score / max_score
    
    # 色のグラデーション (緑 -> 黄 -> 赤)
    # HSL color space: Hue (0-360), Saturation (0-100), Lightness (0-100)
    # Hue: Green is around 120, Red is around 0.
    # We want to go from Green (low score) to Red (high score).
    # So, hue decreases as score increases.
    hue = (1 - normalized_score) * 120 # 120 (Green) to 0 (Red)
    return f"hsl({hue}, 70%, 50%)"


def generate_visjs_graph_data(dbt_project: DbtProject, apply_zscore: bool = False) -> Tuple[List[Dict], List[Dict]]:
    """
    DbtProjectオブジェクトからvis.jsが解釈できるノードとエッジのデータを生成します。
    """
    nodes: List[Dict] = []
    edges: List[Dict] = []

    # 全モデルの最大スコアを計算（色付けの正規化のため）
    # apply_zscoreフラグに応じてスコアを選択
    all_scores = [model.score if apply_zscore else model.raw_score for model in dbt_project.models.values()]
    max_score = max(all_scores) if all_scores else 0

    for unique_id, model in dbt_project.models.items():
        # apply_zscoreフラグに応じてスコアを選択
        current_score = model.score if apply_zscore else model.raw_score
        node_color = _get_node_color_by_score(current_score, max_score)
        
        nodes.append({
            "id": unique_id,
            "label": model.model_name,
            "title": (
                f"Model: {model.model_name}\\n"
                f"Score: {current_score:.2f}\\n"
                f"Complexity (JOINs: {model.complexity.join_count}, CTEs: {model.complexity.cte_count}, Conditionals: {model.complexity.conditional_count}, WHEREs: {model.complexity.where_count}, SQL Chars: {model.complexity.sql_char_count})\\n"
                f"Importance (Downstream: {model.downstream_model_count})\\n"
                f"Quality: {model.quality_score:.2f}"
            ) if model.complexity else f"Model: {model.model_name}\\nScore: {current_score:.2f}\\nQuality: {model.quality_score:.2f}",
            "color": node_color
        })

        # dependencies (parents) から edges を生成
        for parent_unique_id in model.dependencies:
            # 実際のparent_unique_idがモデルとして存在する場合のみエッジを追加
            if parent_unique_id in dbt_project.models:
                edges.append({
                    "from": parent_unique_id,
                    "to": unique_id,
                    "arrows": "to"
                })
    
    return nodes, edges
