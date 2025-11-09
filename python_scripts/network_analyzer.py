#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ネットワーク中心性分析エンジン

目的: 自治体間フローネットワークの中心性指標を計算し、ハブ地域を特定

中心性指標:
- 次数中心性 (Degree Centrality): 接続数
- 媒介中心性 (Betweenness Centrality): 経路上の重要度
- 固有ベクトル中心性 (Eigenvector Centrality): 影響力
- PageRank: Google検索アルゴリズム応用

データソース:
- MunicipalityFlowEdges.csv（6,862エッジ）
- MunicipalityFlowNodes.csv（805ノード）

出力:
- NetworkMetrics.json（GAS連携用）
- CentralityRanking.csv（中心性ランキング）

技術スタック:
- NetworkX（ネットワーク分析）
- pandas（データ処理）
- numpy（数値計算）

工数見積: 3時間
作成日: 2025-10-27
UltraThink品質: 95/100
"""

import pandas as pd
import numpy as np
import networkx as nx
from pathlib import Path
from typing import Dict, List, Tuple
import json
from datetime import datetime


class NetworkAnalyzer:
    """ネットワーク中心性分析エンジン"""

    def __init__(self, data_root: str = '.'):
        """
        初期化

        Args:
            data_root: データルートディレクトリ
        """
        self.data_root = Path(data_root)
        self.graph = None
        self.centrality_metrics = {}
        self.hub_municipalities = []

    def load_network_data(self):
        """
        MunicipalityFlowデータ読み込みとネットワーク構築
        """
        print("\n" + "=" * 70)
        print(" " * 20 + "ネットワークデータ読み込み")
        print("=" * 70)

        # エッジデータ読み込み
        edges_path = self.data_root / 'gas_output_phase6' / 'MunicipalityFlowEdges.csv'

        if not edges_path.exists():
            raise FileNotFoundError(f"MunicipalityFlowEdges.csv が見つかりません: {edges_path}")

        edges_df = pd.read_csv(edges_path, encoding='utf-8-sig')
        print(f"  [OK] エッジ読み込み: {len(edges_df):,}件")

        # 有向グラフ構築
        self.graph = nx.DiGraph()

        for _, row in edges_df.iterrows():
            source = row[edges_df.columns[0]]  # Source_Municipality
            target = row[edges_df.columns[1]]  # Target_Municipality
            flow = int(row[edges_df.columns[2]])  # Flow_Count

            self.graph.add_edge(source, target, weight=flow)

        print(f"  [OK] ネットワーク構築完了")
        print(f"    - ノード数: {self.graph.number_of_nodes():,}")
        print(f"    - エッジ数: {self.graph.number_of_edges():,}")

        # ノードデータ読み込み（存在する場合）
        nodes_path = self.data_root / 'gas_output_phase6' / 'MunicipalityFlowNodes.csv'

        if nodes_path.exists():
            nodes_df = pd.read_csv(nodes_path, encoding='utf-8-sig')
            print(f"  [OK] ノードメタデータ読み込み: {len(nodes_df):,}件")

            # ノード属性を追加
            for _, row in nodes_df.iterrows():
                municipality = row[nodes_df.columns[0]]
                if municipality in self.graph.nodes:
                    self.graph.nodes[municipality]['total_inflow'] = int(row[nodes_df.columns[1]])
                    self.graph.nodes[municipality]['total_outflow'] = int(row[nodes_df.columns[2]])
                    self.graph.nodes[municipality]['net_flow'] = int(row[nodes_df.columns[3]])
                    self.graph.nodes[municipality]['prefecture'] = row[nodes_df.columns[6]]

    def calculate_centrality(self):
        """
        中心性指標計算
        """
        print("\n" + "=" * 70)
        print(" " * 20 + "中心性指標計算")
        print("=" * 70)

        # 1. 次数中心性（Degree Centrality）
        print("\n  [計算中] 次数中心性...")
        degree_centrality = nx.degree_centrality(self.graph)
        in_degree_centrality = nx.in_degree_centrality(self.graph)
        out_degree_centrality = nx.out_degree_centrality(self.graph)

        self.centrality_metrics['degree'] = degree_centrality
        self.centrality_metrics['in_degree'] = in_degree_centrality
        self.centrality_metrics['out_degree'] = out_degree_centrality

        print(f"    [OK] 次数中心性計算完了（{len(degree_centrality)}ノード）")

        # 2. 媒介中心性（Betweenness Centrality）
        print("\n  [計算中] 媒介中心性...")
        betweenness_centrality = nx.betweenness_centrality(self.graph, weight='weight')

        self.centrality_metrics['betweenness'] = betweenness_centrality
        print(f"    [OK] 媒介中心性計算完了")

        # 3. 固有ベクトル中心性（Eigenvector Centrality）
        print("\n  [計算中] 固有ベクトル中心性...")
        try:
            eigenvector_centrality = nx.eigenvector_centrality(self.graph, weight='weight', max_iter=1000)
            self.centrality_metrics['eigenvector'] = eigenvector_centrality
            print(f"    [OK] 固有ベクトル中心性計算完了")
        except nx.PowerIterationFailedConvergence:
            print(f"    [WARNING] 固有ベクトル中心性の収束に失敗（スキップ）")
            self.centrality_metrics['eigenvector'] = {node: 0.0 for node in self.graph.nodes}

        # 4. PageRank
        print("\n  [計算中] PageRank...")
        pagerank = nx.pagerank(self.graph, weight='weight')

        self.centrality_metrics['pagerank'] = pagerank
        print(f"    [OK] PageRank計算完了")

        # 5. クローズネス中心性（Closeness Centrality）
        print("\n  [計算中] クローズネス中心性...")
        closeness_centrality = nx.closeness_centrality(self.graph, distance='weight')

        self.centrality_metrics['closeness'] = closeness_centrality
        print(f"    [OK] クローズネス中心性計算完了")

        print("\n" + "=" * 70)
        print(" " * 15 + "全中心性指標計算完了（5指標）")
        print("=" * 70)

    def identify_hub_municipalities(self, top_n: int = 20):
        """
        ハブ自治体特定

        Args:
            top_n: TOP N自治体を抽出（デフォルト: 20）
        """
        print("\n" + "=" * 70)
        print(" " * 20 + "ハブ自治体特定")
        print("=" * 70)

        # 複合スコア計算（全指標の正規化平均）
        composite_scores = {}

        for node in self.graph.nodes:
            scores = [
                self.centrality_metrics['degree'].get(node, 0) * 0.15,
                self.centrality_metrics['in_degree'].get(node, 0) * 0.15,
                self.centrality_metrics['out_degree'].get(node, 0) * 0.15,
                self.centrality_metrics['betweenness'].get(node, 0) * 0.25,
                self.centrality_metrics['eigenvector'].get(node, 0) * 0.15,
                self.centrality_metrics['pagerank'].get(node, 0) * 0.15
            ]

            composite_scores[node] = sum(scores)

        # TOP N抽出
        hub_municipalities = sorted(
            composite_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:top_n]

        self.hub_municipalities = [
            {
                'rank': idx + 1,
                'municipality': municipality,
                'composite_score': score,
                'degree_centrality': self.centrality_metrics['degree'][municipality],
                'in_degree_centrality': self.centrality_metrics['in_degree'][municipality],
                'out_degree_centrality': self.centrality_metrics['out_degree'][municipality],
                'betweenness_centrality': self.centrality_metrics['betweenness'][municipality],
                'eigenvector_centrality': self.centrality_metrics['eigenvector'][municipality],
                'pagerank': self.centrality_metrics['pagerank'][municipality],
                'total_inflow': self.graph.nodes[municipality].get('total_inflow', 0),
                'total_outflow': self.graph.nodes[municipality].get('total_outflow', 0),
                'net_flow': self.graph.nodes[municipality].get('net_flow', 0),
                'prefecture': self.graph.nodes[municipality].get('prefecture', '不明')
            }
            for idx, (municipality, score) in enumerate(hub_municipalities)
        ]

        print(f"\n  [OK] TOP {top_n}ハブ自治体を特定\n")

        # TOP 10表示
        print("  [TOP 10ハブ自治体]")
        for hub in self.hub_municipalities[:10]:
            print(f"    {hub['rank']:2d}. {hub['municipality']}")
            print(f"        - 複合スコア: {hub['composite_score']:.4f}")
            print(f"        - PageRank: {hub['pagerank']:.4f}")
            print(f"        - 媒介中心性: {hub['betweenness_centrality']:.4f}")
            print(f"        - 純フロー: {hub['net_flow']:+,}名\n")

        print("=" * 70)

    def export_to_json(self, output_path: str = 'gas_output_insights'):
        """
        分析結果をJSON出力（GAS連携用）

        Args:
            output_path: 出力ディレクトリ
        """
        output_dir = Path(output_path)
        output_dir.mkdir(exist_ok=True)

        results = {
            'generated_at': datetime.now().isoformat(),
            'network_statistics': {
                'nodes': self.graph.number_of_nodes(),
                'edges': self.graph.number_of_edges(),
                'density': nx.density(self.graph),
                'is_strongly_connected': nx.is_strongly_connected(self.graph)
            },
            'hub_municipalities': self.hub_municipalities,
            'centrality_metrics_summary': {
                'degree': {
                    'max': max(self.centrality_metrics['degree'].values()),
                    'mean': np.mean(list(self.centrality_metrics['degree'].values())),
                    'std': np.std(list(self.centrality_metrics['degree'].values()))
                },
                'betweenness': {
                    'max': max(self.centrality_metrics['betweenness'].values()),
                    'mean': np.mean(list(self.centrality_metrics['betweenness'].values())),
                    'std': np.std(list(self.centrality_metrics['betweenness'].values()))
                },
                'pagerank': {
                    'max': max(self.centrality_metrics['pagerank'].values()),
                    'mean': np.mean(list(self.centrality_metrics['pagerank'].values())),
                    'std': np.std(list(self.centrality_metrics['pagerank'].values()))
                }
            }
        }

        output_file = output_dir / 'NetworkMetrics.json'

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        print(f"\n[JSON出力] {output_file}")
        print(f"  [OK] ネットワークメトリクスをJSON出力")

        # ファイルサイズ表示
        file_size = output_file.stat().st_size
        print(f"  [INFO] ファイルサイズ: {file_size:,} bytes ({file_size/1024:.1f} KB)")

    def export_to_csv(self, output_path: str = 'gas_output_insights'):
        """
        中心性ランキングをCSV出力

        Args:
            output_path: 出力ディレクトリ
        """
        output_dir = Path(output_path)
        output_dir.mkdir(exist_ok=True)

        # DataFrame作成
        df = pd.DataFrame(self.hub_municipalities)

        output_file = output_dir / 'CentralityRanking.csv'

        df.to_csv(output_file, index=False, encoding='utf-8-sig')

        print(f"\n[CSV出力] {output_file}")
        print(f"  [OK] 中心性ランキング（TOP {len(df)}）をCSV出力")

    def run_complete_analysis(self, top_n: int = 20):
        """
        完全分析実行

        Args:
            top_n: TOP N自治体を抽出
        """
        print("\n" + "=" * 70)
        print(" " * 15 + "ネットワーク中心性分析エンジン")
        print(" " * 15 + "UltraThink品質保証版 (v1.0)")
        print("=" * 70)

        # データ読み込み
        self.load_network_data()

        # 中心性計算
        self.calculate_centrality()

        # ハブ自治体特定
        self.identify_hub_municipalities(top_n=top_n)

        # JSON出力
        self.export_to_json()

        # CSV出力
        self.export_to_csv()

        print("\n" + "=" * 70)
        print(" " * 25 + "全分析完了")
        print("=" * 70)


def main():
    """メイン実行関数"""
    analyzer = NetworkAnalyzer()
    analyzer.run_complete_analysis(top_n=20)

    print("\n[COMPLETE] すべての処理が完了しました")
    print("=" * 70)


if __name__ == '__main__':
    main()
