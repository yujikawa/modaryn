from jinja2 import Environment, FileSystemLoader
from typing import Optional, List
import json # jsonモジュールをインポート
import html # htmlモジュールをインポート

from modaryn.domain.model import DbtProject, DbtModel, ScoreStatistics
from . import OutputGenerator
from .graph import generate_visjs_graph_data # 新しく作成したモジュールをインポート

HTML_SCORE_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Modaryn Score and Scan Report</title>
    <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <style>
        body { font-family: sans-serif; margin: 2em; background-color: #f9f9f9; color: #333; }
        h1, h2 { color: #1a1a1a; border-bottom: 2px solid #eee; padding-bottom: 0.3em; }
        table { border-collapse: collapse; margin-top: 1.5em; width: 100%; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
        th { background-color: #f2f2f2; }
        tr:nth-child(even) { background-color: #fcfcfc; }
        tr:hover { background-color: #f1f1f1; }
        #searchInput {
            width: 100%;
            padding: 10px;
            margin-bottom: 20px;
            box-sizing: border-box;
            border: 1px solid #ccc;
            border-radius: 4px;
        }
        .sortable {
            cursor: pointer;
            position: relative;
        }
        .sortable::after {
            content: '';
            position: absolute;
            right: 8px;
            top: 50%;
            margin-top: -7px;
            width: 0; 
            height: 0; 
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            opacity: 0.3;
        }
        .sortable[data-sort-dir="asc"]::after {
            border-bottom: 5px solid #333;
            opacity: 1;
        }
        .sortable[data-sort-dir="desc"]::after {
            border-top: 5px solid #333;
            opacity: 1;
        }
        .summary-card {
            background-color: #fff;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 1em;
            margin-bottom: 1em;
        }
        #network-graph {
            width: 100%;
            height: 600px; /* グラフの高さ */
            border: 1px solid lightgray;
            margin-bottom: 2em;
        }
    </style>
</head>
<body>
    <h1>Modaryn Score and Scan Report</h1>

    {% if threshold is not none %}
    <div class="summary-card">
        <h2>CI Check Summary</h2>
        <p>Status: {% if problematic_models %}<span style="color: red; font-weight: bold;">FAILED</span>{% else %}<span style="color: green; font-weight: bold;">PASSED</span>{% endif %} - 
            {% if problematic_models %}{{ problematic_models|length }} models exceeded threshold.{% else %}All models are within the defined threshold.{% endif %}</p>
        <p>Total models checked: {{ models|length }}</p>
        <p>Threshold: {{ "%.3f"|format(threshold) }}</p>
    </div>
    {% endif %}

    {% if statistics %}
    <div class="summary-card">
        <h2>Score Statistics</h2>
        <ul>
            <li>Mean: {{ "%.3f"|format(statistics.mean) }}</li>
            <li>Median: {{ "%.3f"|format(statistics.median) }}</li>
            <li>Standard Deviation: {{ "%.3f"|format(statistics.std_dev) }}</li>
        </ul>
    </div>
    {% endif %}

    <h2>Model Lineage Graph</h2>
    <div id="network-graph"></div>
    
    <h2>Model Scores</h2>
    <input type="text" id="searchInput" onkeyup="filterTable()" placeholder="Search for models..">
    
    <table id="models-table">
        <thead>
            <tr>
                <th class="sortable" onclick="sortTable(0, 'number')" data-type="number">Rank</th>
                <th class="sortable" onclick="sortTable(1, 'string')" data-type="string">Model Name</th>
                <th class="sortable" onclick="sortTable(2, 'number')" data-type="number">{% if apply_zscore %}Score (Z-Score){% else %}Score (Raw){% endif %}</th>
                <th class="sortable" onclick="sortTable(3, 'number')" data-type="number">Quality Score</th>
                <th class="sortable" onclick="sortTable(4, 'number')" data-type="number">JOINs</th>
                <th class="sortable" onclick="sortTable(5, 'number')" data-type="number">CTEs</th>
                <th class="sortable" onclick="sortTable(6, 'number')" data-type="number">Conditionals</th>
                <th class="sortable" onclick="sortTable(7, 'number')" data-type="number">WHEREs</th>
                <th class="sortable" onclick="sortTable(8, 'number')" data-type="number">SQL Chars</th>
                <th class="sortable" onclick="sortTable(9, 'number')" data-type="number">Downstream Models</th>
                <th class="sortable" onclick="sortTable(10, 'number')" data-type="number">Col. Down</th>
                <th class="sortable" onclick="sortTable(11, 'number')" data-type="number">Tests</th>
                <th class="sortable" onclick="sortTable(12, 'number')" data-type="number">Coverage (%)</th>
            </tr>
        </thead>
        <tbody id="models-tbody">
        {% for model in models %}
        <tr>
            <td>{{ loop.index }}</td>
            <td>{{ model.model_name }}</td>
            <td>
                {% if apply_zscore %}
                    {{ "%.2f"|format(model.score) }}
                {% else %}
                    {{ "%.2f"|format(model.raw_score) }}
                {% endif %}
            </td>
            <td>{{ "%.2f"|format(model.quality_score) }}</td>
            <td>{{ model.complexity.join_count if model.complexity else '0' }}</td>
            <td>{{ model.complexity.cte_count if model.complexity else '0' }}</td>
            <td>{{ model.complexity.conditional_count if model.complexity else '0' }}</td>
            <td>{{ model.complexity.where_count if model.complexity else '0' }}</td>
            <td>{{ model.complexity.sql_char_count if model.complexity else '0' }}</td>
            <td>{{ model.downstream_model_count }}</td>
            <td>{{ model.downstream_column_count }}</td>
            <td>{{ model.test_count }}</td>
            <td>{{ "%.1f"|format(model.column_test_coverage) }}</td>
        </tr>
        {% endfor %}
        </tbody>
    </table>
    
    <script>
    function filterTable() {
        const input = document.getElementById("searchInput");
        const filter = input.value.toUpperCase();
        const tbody = document.getElementById("models-tbody");
        const rows = tbody.getElementsByTagName("tr");

        for (let i = 0; i < rows.length; i++) {
            const modelNameCell = rows[i].getElementsByTagName("td")[1];
            if (modelNameCell) {
                const txtValue = modelNameCell.textContent || modelNameCell.innerText;
                if (txtValue.toUpperCase().indexOf(filter) > -1) {
                    rows[i].style.display = "";
                } else {
                    rows[i].style.display = "none";
                }
            }       
        }
    }

    function sortTable(columnIndex, type) {
        const tbody = document.getElementById("models-tbody");
        const rows = Array.from(tbody.getElementsByTagName("tr"));
        const header = document.querySelectorAll("#models-table th.sortable")[columnIndex];
        
        let currentDir = header.getAttribute("data-sort-dir") || "desc";
        let newDir = currentDir === "asc" ? "desc" : "asc";
        
        document.querySelectorAll("#models-table th.sortable").forEach(th => th.removeAttribute("data-sort-dir"));
        header.setAttribute("data-sort-dir", newDir);

        rows.sort((a, b) => {
            const cellA = a.getElementsByTagName("td")[columnIndex].innerText;
            const cellB = b.getElementsByTagName("td")[columnIndex].innerText;
            
            let valA, valB;
            if (type === 'number') {
                valA = parseFloat(cellA.replace(/,/g, '')) || 0;
                valB = parseFloat(cellB.replace(/,/g, '')) || 0;
            } else {
                valA = cellA.toLowerCase();
                valB = cellB.toLowerCase();
            }

            if (valA < valB) {
                return newDir === "asc" ? -1 : 1;
            }
            if (valA > valB) {
                return newDir === "asc" ? 1 : -1;
            }
            return 0;
        });

        tbody.innerHTML = "";
        rows.forEach(row => tbody.appendChild(row));
    }
    
    // HTMLエスケープされた文字列をアンエスケープする関数
    function unescapeHtml(html) {
        var txt = document.createElement("textarea");
        txt.innerHTML = html;
        return txt.value;
    }

    // vis.js graph drawing
    document.addEventListener("DOMContentLoaded", function() {
        const container = document.getElementById("network-graph");
        
        // Pythonから渡されたJSON文字列をJavaScriptのテンプレートリテラルで直接埋め込み、JSON.parseでオブジェクトに戻す
        const nodesData = new vis.DataSet(JSON.parse(`{{ visjs_nodes | safe }}`));
        const edgesData = new vis.DataSet(JSON.parse(`{{ visjs_edges | safe }}`));

        const data = {
            nodes: nodesData,
            edges: edgesData
        };
        const options = {
            nodes: {
                shape: "box", // ノードの形状を四角に設定
                size: 20,     // ノードのサイズを大きくする
                font: {
                    size: 14, // フォントサイズを大きくする
                    color: '#333'
                },
                borderWidth: 2 // ノードの境界線を追加
            },
            edges: {
                arrows: {
                    to: {
                        enabled: true,
                        scaleFactor: 0.5
                    }
                },
                color: {
                    color: "#999",
                    highlight: "#333",
                    hover: "#333"
                },
                width: 2, // エッジの幅を大きくする
                smooth: {
                    type: "cubicBezier",
                    forceDirection: "vertical",
                    roundness: 0.4
                }
            },
            layout: {
                hierarchical: {
                    enabled: false // 階層レイアウトを一時的に無効にする
                }
            },
            physics: {
                enabled: true, // 物理シミュレーションを有効にする
                stabilization: {
                    iterations: 1000 // 安定化のための繰り返し回数を増やす
                }
            },
            interaction: {
                navigationButtons: true,
                keyboard: true,
                zoomView: true,
                dragView: true
            }
        };

        const network = new vis.Network(container, data, options);
        window.network = network; // グローバルスコープでアクセスできるようにする

        // ノードクリックイベントの追加（オプション）
        network.on("click", function (params) {
            if (params.nodes.length > 0) {
                const nodeId = params.nodes[0];
                const clickedNode = nodesData.get(nodeId);
                console.log("Clicked node details:", clickedNode);
            }
        });
    });
    </script>

</body>
</html>
"""


class HtmlOutput(OutputGenerator):
    def __init__(self):
        self.env = Environment(loader=FileSystemLoader('.'), autoescape=False) # autoescape=Falseに戻す
        self.env.filters['tojson'] = lambda obj: json.dumps(obj, separators=(',', ':')) # Jinja2環境にtojsonフィルターを追加。コンパクトなJSONを生成するように設定。

    def generate_report(self, project: DbtProject, problematic_models: Optional[List[DbtModel]] = None, threshold: Optional[float] = None, apply_zscore: bool = False, statistics: Optional[ScoreStatistics] = None) -> Optional[str]:
        sort_key = (lambda m: m.score) if apply_zscore else (lambda m: m.raw_score)
        
        sorted_models = sorted(
            project.models.values(), 
            key=lambda m: sort_key(m) if sort_key(m) is not None else -1,
            reverse=True
        )

        # vis.jsのグラフデータを生成
        visjs_nodes_data = generate_visjs_graph_data(project, apply_zscore=apply_zscore)
        visjs_nodes_json = json.dumps(visjs_nodes_data[0], separators=(',', ':'))
        visjs_edges_json = json.dumps(visjs_nodes_data[1], separators=(',', ':'))

        template = self.env.from_string(HTML_SCORE_TEMPLATE)
        return template.render(
            models=sorted_models, 
            apply_zscore=apply_zscore, 
            statistics=statistics, 
            problematic_models=problematic_models, 
            threshold=threshold,
            visjs_nodes=visjs_nodes_json, # html.escape()せずJSON文字列をそのまま渡す
            visjs_edges=visjs_edges_json  # html.escape()せずJSON文字列をそのまま渡す
        )

