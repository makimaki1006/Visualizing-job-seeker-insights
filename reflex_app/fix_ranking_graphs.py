"""
横棒グラフ（ランキング）修正スクリプト
問題: すべてのランキング関数が市区町村選択を要求しているが、
      都道府県レベルで市区町村のランキングを表示すべき

修正方針:
1. 都道府県が選択されたら、その都道府県内の市区町村TOP10を表示
2. 市区町村が選択されたら、その市区町村に絞って表示
3. 色盲対応カラーパレットを適用
"""

import re

def fix_ranking_functions():
    """すべてのランキング関数を修正"""

    # ファイルパス
    file_path = r"C:\Users\fuji1\OneDrive\Pythonスクリプト保管\job_medley_project\reflex_app\mapcomplete_dashboard\mapcomplete_dashboard.py"

    # 読み込み
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. flow_inflow_ranking の修正
    old_flow_inflow = '''    @rx.var(cache=False)
    def flow_inflow_ranking(self) -> List[Dict[str, Any]]:
        """フロー: 流入ランキング Top 10（横棒グラフ用）

        形式: [{"name": "京都市", "value": 450}, ...]
        """
        if not self.is_loaded or self.df is None:
            return []

        df = self.df
        prefecture = self.selected_prefecture

        # FLOWデータをフィルタ（都道府県のみ）
        filtered = df[
            (df['row_type'] == 'FLOW') &
            (df['prefecture'] == prefecture) &
            (df['municipality'].notna())  # 市区町村レベルのみ
        ].copy()

        if filtered.empty:
            return []

        # 流入でソート
        filtered = filtered.sort_values('inflow', ascending=False).head(10)

        result = []
        for _, row in filtered.iterrows():
            result.append({
                "name": str(row.get('municipality', '不明')),
                "value": int(row.get('inflow', 0)) if pd.notna(row.get('inflow')) else 0
            })

        return result'''

    new_flow_inflow = '''    @rx.var(cache=False)
    def flow_inflow_ranking(self) -> List[Dict[str, Any]]:
        """フロー: 流入ランキング Top 10（横棒グラフ用）

        形式: [{"name": "京都市", "value": 450}, ...]
        """
        if not self.is_loaded or self.df is None:
            return []

        df = self.df
        prefecture = self.selected_prefecture
        municipality = self.selected_municipality

        if not prefecture:
            return []

        # FLOWデータをフィルタ
        if municipality:
            # 市区町村が選択されている場合、その市区町村のデータのみ
            filtered = df[
                (df['row_type'] == 'FLOW') &
                (df['prefecture'] == prefecture) &
                (df['municipality'] == municipality)
            ].copy()
        else:
            # 都道府県のみ選択されている場合、その都道府県内の市区町村TOP10
            filtered = df[
                (df['row_type'] == 'FLOW') &
                (df['prefecture'] == prefecture) &
                (df['municipality'].notna())
            ].copy()

        if filtered.empty:
            return []

        # 流入でソート
        filtered = filtered.sort_values('inflow', ascending=False).head(10)

        result = []
        for _, row in filtered.iterrows():
            result.append({
                "name": str(row.get('municipality', '不明')),
                "value": int(row.get('inflow', 0)) if pd.notna(row.get('inflow')) else 0
            })

        return result'''

    content = content.replace(old_flow_inflow, new_flow_inflow)

    # 2. flow_outflow_ranking の修正
    old_flow_outflow = '''    @rx.var(cache=False)
    def flow_outflow_ranking(self) -> List[Dict[str, Any]]:
        """フロー: 流出ランキング Top 10（横棒グラフ用）

        形式: [{"name": "京都市", "value": 320}, ...]
        """
        if not self.is_loaded or self.df is None:
            return []

        df = self.df
        prefecture = self.selected_prefecture

        # FLOWデータをフィルタ（都道府県のみ）
        filtered = df[
            (df['row_type'] == 'FLOW') &
            (df['prefecture'] == prefecture) &
            (df['municipality'].notna())  # 市区町村レベルのみ
        ].copy()

        if filtered.empty:
            return []

        # 流出でソート
        filtered = filtered.sort_values('outflow', ascending=False).head(10)

        result = []
        for _, row in filtered.iterrows():
            result.append({
                "name": str(row.get('municipality', '不明')),
                "value": int(row.get('outflow', 0)) if pd.notna(row.get('outflow')) else 0
            })

        return result'''

    new_flow_outflow = '''    @rx.var(cache=False)
    def flow_outflow_ranking(self) -> List[Dict[str, Any]]:
        """フロー: 流出ランキング Top 10（横棒グラフ用）

        形式: [{"name": "京都市", "value": 320}, ...]
        """
        if not self.is_loaded or self.df is None:
            return []

        df = self.df
        prefecture = self.selected_prefecture
        municipality = self.selected_municipality

        if not prefecture:
            return []

        # FLOWデータをフィルタ
        if municipality:
            # 市区町村が選択されている場合、その市区町村のデータのみ
            filtered = df[
                (df['row_type'] == 'FLOW') &
                (df['prefecture'] == prefecture) &
                (df['municipality'] == municipality)
            ].copy()
        else:
            # 都道府県のみ選択されている場合、その都道府県内の市区町村TOP10
            filtered = df[
                (df['row_type'] == 'FLOW') &
                (df['prefecture'] == prefecture) &
                (df['municipality'].notna())
            ].copy()

        if filtered.empty:
            return []

        # 流出でソート
        filtered = filtered.sort_values('outflow', ascending=False).head(10)

        result = []
        for _, row in filtered.iterrows():
            result.append({
                "name": str(row.get('municipality', '不明')),
                "value": int(row.get('outflow', 0)) if pd.notna(row.get('outflow')) else 0
            })

        return result'''

    content = content.replace(old_flow_outflow, new_flow_outflow)

    # 3. flow_netflow_ranking の修正
    old_flow_netflow = '''    @rx.var(cache=False)
    def flow_netflow_ranking(self) -> List[Dict[str, Any]]:
        """フロー: 純流入ランキング Top 10（横棒グラフ用）

        形式: [{"name": "京都市", "value": 130}, ...]
        """
        if not self.is_loaded or self.df is None:
            return []

        df = self.df
        prefecture = self.selected_prefecture

        # FLOWデータをフィルタ（都道府県のみ）
        filtered = df[
            (df['row_type'] == 'FLOW') &
            (df['prefecture'] == prefecture) &
            (df['municipality'].notna())  # 市区町村レベルのみ
        ].copy()

        if filtered.empty:
            return []

        # 純流入でソート
        filtered = filtered.sort_values('net_flow', ascending=False).head(10)

        result = []
        for _, row in filtered.iterrows():
            result.append({
                "name": str(row.get('municipality', '不明')),
                "value": int(row.get('net_flow', 0)) if pd.notna(row.get('net_flow')) else 0
            })

        return result'''

    new_flow_netflow = '''    @rx.var(cache=False)
    def flow_netflow_ranking(self) -> List[Dict[str, Any]]:
        """フロー: 純流入ランキング Top 10（横棒グラフ用）

        形式: [{"name": "京都市", "value": 130}, ...]
        """
        if not self.is_loaded or self.df is None:
            return []

        df = self.df
        prefecture = self.selected_prefecture
        municipality = self.selected_municipality

        if not prefecture:
            return []

        # FLOWデータをフィルタ
        if municipality:
            # 市区町村が選択されている場合、その市区町村のデータのみ
            filtered = df[
                (df['row_type'] == 'FLOW') &
                (df['prefecture'] == prefecture) &
                (df['municipality'] == municipality)
            ].copy()
        else:
            # 都道府県のみ選択されている場合、その都道府県内の市区町村TOP10
            filtered = df[
                (df['row_type'] == 'FLOW') &
                (df['prefecture'] == prefecture) &
                (df['municipality'].notna())
            ].copy()

        if filtered.empty:
            return []

        # 純流入でソート
        filtered = filtered.sort_values('net_flow', ascending=False).head(10)

        result = []
        for _, row in filtered.iterrows():
            result.append({
                "name": str(row.get('municipality', '不明')),
                "value": int(row.get('net_flow', 0)) if pd.notna(row.get('net_flow')) else 0
            })

        return result'''

    content = content.replace(old_flow_netflow, new_flow_netflow)

    # 保存
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print("フロー関連のランキング関数を修正しました")
    return True

if __name__ == "__main__":
    fix_ranking_functions()