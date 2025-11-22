"""
CSVアップロード後の都道府県・市区町村初期化を修正
"""

with open('mapcomplete_dashboard/mapcomplete_dashboard.py', 'r', encoding='utf-8') as f:
    content = f.read()

# handle_upload関数の修正
# Line 100-109を置換
old_code = '''                # 都道府県リスト抽出
                if 'prefecture' in self.df.columns:
                    self.prefectures = sorted(self.df['prefecture'].dropna().unique().tolist())
                    # 最初の都道府県を自動選択
                    if len(self.prefectures) > 0:
                        self.selected_prefecture = self.prefectures[0]

                print(f"[SUCCESS] CSVロード成功: {self.total_rows}行 x {len(self.df.columns)}列")
                print(f"[INFO] 都道府県数: {len(self.prefectures)}")
                print(f"[INFO] 初期選択: {self.selected_prefecture}")'''

new_code = '''                # 都道府県リスト抽出
                if 'prefecture' in self.df.columns:
                    self.prefectures = sorted(self.df['prefecture'].dropna().unique().tolist())
                    # 最初の都道府県を自動選択して市区町村リストも初期化
                    if len(self.prefectures) > 0:
                        first_pref = self.prefectures[0]
                        self.selected_prefecture = first_pref

                        # 市区町村リスト初期化
                        if 'municipality' in self.df.columns:
                            filtered = self.df[self.df['prefecture'] == first_pref]
                            self.municipalities = sorted(filtered['municipality'].dropna().unique().tolist())

                print(f"[SUCCESS] CSVロード成功: {self.total_rows}行 x {len(self.df.columns)}列")
                print(f"[INFO] 都道府県数: {len(self.prefectures)}")
                print(f"[INFO] 初期選択: {self.selected_prefecture}")
                print(f"[INFO] 市区町村数: {len(self.municipalities)}")'''

content = content.replace(old_code, new_code)

with open('mapcomplete_dashboard/mapcomplete_dashboard.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("修正完了: CSVアップロード後の都道府県・市区町村初期化を追加")
