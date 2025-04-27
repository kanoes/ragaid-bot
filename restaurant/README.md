# restaurant — レストランのグリッド・レイアウト解析

`restaurant` サブパッケージは、2D グリッドによるレストラン環境のモデリング機能を提供します。ロボットの経路探索・配達シミュレーションの基盤となるモジュールです。

---

## ディレクトリ構成

```text
restaurant/
├─ restaurant_layout.py    # レイアウト解析、空き地判定、隣接セル探索、可視化など
├─ restaurant.py           # レイアウトをラップし、名称を付加するクラス
├─ layouts.json            # 複数のプリセットレイアウト例
├─ README.md               # 本ドキュメント
└─ __init__.py             # パッケージエントリーポイント
```

---

## レイアウト形式について

- 数値マトリクス：`layouts.json` 内では整数値でレイアウトを表現しています。各セルの意味は以下の通りです。
  - `0`：空き地
  - `1`：壁・障害物
  - `2`～`99`：テーブル番号
  - `100`：キッチン（厨房）
  - `200`：駐車スポット（パーキング）

---

## 主なAPI一覧

```python
layout = rest.layout
layout.is_free((x, y))         # 指定座標が通行可能かどうかを判定
layout.neighbors((x, y))       # 上下左右の通行可能な隣接セルを取得
layout.tables                  # テーブル位置の辞書（例: {'A': (1,2)}）
layout.kitchen                 # キッチン座標リスト
layout.parking                 # 駐車スポット座標
layout.display()               # ASCII形式でレイアウトを出力
```

---

## 改善提案

- `restaurant_layout.py` にて、動的障害物対応やさらなる突発イベントへの拡張を推奨
