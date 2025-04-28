"""
ユーティリティ関数
"""
import os
import json
from typing import Tuple, Optional, List, Dict, Any

from rich.panel import Panel
from rich.text import Text
from rich.box import ROUNDED
from rich.style import Style

from restaurant.restaurant_layout import RestaurantLayout
from restaurant.restaurant import Restaurant
from robot import AIEnhancedRobot, Robot
from robot.order import Order

from .constants import LAYOUT_DIR, RAG_KB_DIR, EMPTY_STYLE, WALL_STYLE, TABLE_STYLE, KITCHEN_STYLE, PARKING_STYLE, ERROR_STYLE


def available_layouts(layout_dir=LAYOUT_DIR):
    """
    利用可能なレストランレイアウトのリストを取得する
    """
    # 新しい形式のレイアウトファイルが存在するかチェック
    new_format_path = os.path.join(layout_dir, "layouts.json")
    if os.path.exists(new_format_path):
        try:
            with open(new_format_path, encoding="utf-8") as f:
                layouts_data = json.load(f)
                return [layout["name"] for layout in layouts_data["layouts"]]
        except (json.JSONDecodeError, KeyError) as e:
            print(f"新しい形式のレイアウトファイルの読み込みに失敗しました: {e}")
            return []
    
    # 古い形式のレイアウトファイルにフォールバック
    if os.path.exists(layout_dir):
        return sorted(os.path.splitext(f)[0] for f in os.listdir(layout_dir) if f.endswith(".json") and f != "layouts.json")
    return []

def parse_layout_from_strings(layout_name: str, layout_lines: List[str]):
    """
    文字列配列からレストランレイアウトを解析する
    
    Args:
        layout_name: レイアウト名
        layout_lines: レイアウト文字列配列
        
    Returns:
        dict: 解析されたレイアウト設定を含む
    """
    # 文字から数値へのマッピング
    char_map = {
        "#": 1, "＃": 1, "W": 1,    # 壁/障害物
        "*": 0, ".": 0,             # 空き地
        "台": 3,                    # キッチン
        "停": 4, "P": 4             # 駐車位置
    }
    
    # データ構造の初期化
    height = len(layout_lines)
    width = max(len(line.split()) for line in layout_lines) if height else 0
    grid = [[0] * width for _ in range(height)]
    table_positions = {}
    kitchen_positions = []
    parking_position = None
    
    # レイアウト文字列の解析
    for row, line in enumerate(layout_lines):
        tokens = line.split()
        for col, token in enumerate(tokens):
            if token in char_map:
                # 既知の記号
                value = char_map[token]
                grid[row][col] = value
                
                # 特殊位置の記録
                if value == 3:  # キッチン
                    kitchen_positions.append((row, col))
                elif value == 4:  # 駐車位置
                    parking_position = (row, col)
            elif token.isalpha() and len(token) == 1:
                # テーブル
                grid[row][col] = 2
                table_positions[token] = (row, col)
            else:
                # 未知の記号、空き地として処理
                grid[row][col] = 0
    
    return {
        "grid": grid,
        "table_positions": table_positions,
        "kitchen_positions": kitchen_positions,
        "parking_position": parking_position
    }

def display_restaurant_ascii(restaurant, restaurant_name=None):
    """
    ASCII形式でレストランレイアウトを表示する
    
    Args:
        restaurant: レストランオブジェクトまたはレストランレイアウトオブジェクト
        restaurant_name: レストラン名（オプション）
    """
    layout = getattr(restaurant, 'layout', restaurant)
    name = restaurant_name or getattr(restaurant, 'name', 'Restaurant')
    
    # 記号マッピング（数字コードに基づく）
    symbols = {
        0: ".",    # 空き地
        1: "#",    # 壁/障害物
        2: "?",    # テーブル（テーブル番号に置き換えられる）
        3: "?",    # キッチン
        4: "P",    # 駐車位置
        100: "K",  # キッチン（新形式）
        200: "P",  # 駐車位置（新形式）
    }
    
    # タイトルの表示
    print(f"レストランレイアウト: {name} ({layout.width}x{layout.height})")
    print("-" * (layout.width * 2 + 3))
    
    # テーブルIDの逆引き
    rev_tables = {pos: tid for tid, pos in layout.tables.items()}
    
    # レイアウトの表示
    for i in range(layout.height):
        print("|", end=" ")
        for j in range(layout.width):
            cell_value = layout.grid[i][j]
            if cell_value == 2 and (i, j) in rev_tables:
                # テーブルIDを表示
                print(rev_tables[(i, j)], end=" ")
            elif 2 <= cell_value <= 99:
                # 数字で表されるテーブルID（rev_tablesから取得、なければ?を表示）
                print(rev_tables.get((i, j), "?"), end=" ")
            else:
                # その他のタイプのセル
                print(symbols.get(cell_value, "?"), end=" ")
        print("|")
    
    print("-" * (layout.width * 2 + 3))

def load_restaurant(layout_name, layout_dir=LAYOUT_DIR):
    """
    レストランレイアウトを読み込む
    """
    new_format_path = os.path.join(layout_dir, "layouts.json")
    if not os.path.exists(new_format_path):
        raise FileNotFoundError(f"レイアウトファイルが見つかりません: {new_format_path}")

    with open(new_format_path, encoding="utf-8") as f:
        layouts_data = json.load(f)
    for layout in layouts_data["layouts"]:
        if layout["name"] == layout_name:
            cfg = RestaurantLayout.parse_layout_from_array(
                layout_name, layout["grid"]
            )
            return Restaurant(layout_name, RestaurantLayout(**cfg))

    raise KeyError(f"layouts.jsonに名前が{layout_name}のレイアウトが見つかりません")

def save_restaurant_layout(layout_data, layout_dir=LAYOUT_DIR):
    """
    レストランレイアウトをJSONファイルに保存する
    
    Args:
        layout_data: dict, レイアウトデータを含む
        layout_dir: 保存ディレクトリのパス
    
    Returns:
        str: 保存したファイルのパス
    """
    # ディレクトリが存在することを確認
    os.makedirs(layout_dir, exist_ok=True)
    
    # データの準備
    name = layout_data.get("name", "新しいレイアウト")
    grid = layout_data.get("grid", [])
    
    # layouts.jsonファイルが存在するかチェック
    layouts_path = os.path.join(layout_dir, "layouts.json")
    if os.path.exists(layouts_path):
        # 既存のレイアウトを読み込む
        try:
            with open(layouts_path, "r", encoding="utf-8") as f:
                layouts_data = json.load(f)
                layouts = layouts_data.get("layouts", [])
        except Exception:
            # 読み込みエラーの場合、新しいレイアウトリストを作成
            layouts = []
    else:
        layouts = []
    
    # 同名のレイアウトが既に存在するか確認
    layout_found = False
    for i, layout in enumerate(layouts):
        if layout.get("name") == name:
            # 既存のレイアウトを更新
            layouts[i] = {
                "name": name,
                "grid": grid
            }
            layout_found = True
            break
    
    # レイアウトが見つからなければ、新しく追加
    if not layout_found:
        layouts.append({
            "name": name,
            "grid": grid
        })
    
    # layouts.jsonに保存
    with open(layouts_path, "w", encoding="utf-8") as f:
        json.dump({"layouts": layouts}, f, ensure_ascii=False, indent=2)
    
    return layouts_path

def save_layouts_to_single_file(layouts: List[Dict[str, Any]], layout_dir=LAYOUT_DIR):
    """
    複数のレストランレイアウトを単一のlayouts.jsonファイルに保存する
    
    Args:
        layouts: レイアウトデータのリスト、各要素はnameとgridを含む
        layout_dir: 保存ディレクトリのパス
    
    Returns:
        str: 保存したファイルのパス
    """
    # ディレクトリが存在することを確認
    os.makedirs(layout_dir, exist_ok=True)
    
    # 保存するデータの準備
    save_data = {
        "layouts": layouts
    }
    
    # ファイルに保存
    file_path = os.path.join(layout_dir, "layouts.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(save_data, f, ensure_ascii=False, indent=2)
    
    return file_path

def delete_restaurant_layout(layout_name, layout_dir=LAYOUT_DIR):
    """
    レストランレイアウトファイルを削除する
    
    Args:
        layout_name: レイアウト名
        layout_dir: レイアウトファイルのディレクトリ
    
    Returns:
        bool: 削除に成功したかどうか
    """
    # 新形式ファイルをチェック
    new_format_path = os.path.join(layout_dir, "layouts.json")
    if os.path.exists(new_format_path):
        try:
            with open(new_format_path, "r", encoding="utf-8") as f:
                layouts_data = json.load(f)
                
            # 削除するレイアウトをフィルタリング
            layouts_data["layouts"] = [
                layout for layout in layouts_data["layouts"]
                if layout["name"] != layout_name
            ]
            
            # ファイルに書き戻す
            with open(new_format_path, "w", encoding="utf-8") as f:
                json.dump(layouts_data, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"新形式ファイルからレイアウトの削除に失敗しました: {e}")
            return False
    
    # 古い形式にフォールバック
    file_path = os.path.join(layout_dir, f"{layout_name}.json")
    if os.path.exists(file_path):
        os.remove(file_path)
        return True
    return False

def build_robot(use_ai, layout, restaurant_name="デフォルトレストラン"):
    """
    ロボットインスタンスを構築する
    """
    if use_ai:
        robot = AIEnhancedRobot(layout, robot_id=1, knowledge_dir=RAG_KB_DIR, restaurant_name=restaurant_name)
    else:
        robot = Robot(layout, robot_id=1, restaurant_name=restaurant_name)
        
    # ロボットの目標許容パラメータを設定
    robot.GOAL_TOLERANCE = 0  # 正確な位置に到達する必要がある
    
    return robot

def make_order(seq, table_id):
    """
    注文インスタンスを作成する
    """
    return Order(order_id=seq, table_id=table_id, prep_time=0)

def create_rich_layout(grid, height, width, tables, 
                       robot_position: Optional[Tuple[int, int]] = None,
                       highlight_path: Optional[list] = None):
    """
    リッチテキスト形式のレストランレイアウトを作成する
    
    Args:
        grid: レストラングリッドデータ
        height: グリッドの高さ
        width: グリッドの幅
        tables: テーブル位置の辞書
        robot_position: ロボットの現在位置（オプション）
        highlight_path: ハイライト表示するパスポイントのリスト（オプション）
    """
    # ハイライトポイントのセットを保存
    highlight_points = set(highlight_path or [])
    
    # 各要素のスタイルを定義
    cell_chars = {
        0: "  ",              # 空き地
        1: "██",              # 壁/障害物
        2: None,              # テーブル (特別処理)
        3: "厨",              # キッチン
        4: "停",              # 駐車位置
    }
    
    cell_styles = {
        0: EMPTY_STYLE,
        1: WALL_STYLE,
        2: TABLE_STYLE,
        3: KITCHEN_STYLE,
        4: PARKING_STYLE,
    }
    
    layout_text = Text()
    
    for x in range(height):
        for y in range(width):
            cell_type = grid[x][y]
            pos = (x, y)
            
            # 現在のポイントをハイライト表示する必要があるかチェック
            is_robot_pos = robot_position and pos == robot_position
            is_highlight = pos in highlight_points
            
            # セルテキストを取得
            if cell_type == 2:  # テーブルの特別処理
                cell_text = get_table_id(pos, tables)
            else:
                cell_text = cell_chars.get(cell_type, "??")
            
            # スタイルを取得
            style = cell_styles.get(cell_type, ERROR_STYLE)
            
            # ハイライト状況を処理
            if is_robot_pos:
                # ロボット位置には特別な記号と赤い背景を使用
                text_segment = Text("🤖", style=Style(bgcolor="red", color="white", bold=True))
            elif is_highlight:
                # パスポイントには特別な背景色を使用
                text_segment = Text(cell_text, style=Style(bgcolor="magenta", color="white"))
            else:
                # 通常のセル
                text_segment = Text(cell_text, style=style)
                
            layout_text.append(text_segment)
            
        # 行の終わりに改行を追加
        layout_text.append("\n")
        
    return layout_text

def get_table_id(pos, tables):
    """
    特定の位置に対応するテーブルIDを取得する
    """
    # 位置からテーブルIDを逆引き
    for tid, tpos in tables.items():
        if tpos == pos:
            return tid.center(2)
    return "テ"

def create_rich_restaurant_panel(restaurant, 
                                robot_position=None, 
                                highlight_path=None,
                                title_suffix=""):
    """
    リッチテキスト形式のレストランレイアウトパネルを作成する
    
    Args:
        restaurant: レストランオブジェクト
        robot_position: ロボットの現在位置（オプション）
        highlight_path: ハイライト表示するパス（オプション）
        title_suffix: タイトルの接尾辞（オプション）
    """
    layout = restaurant.layout
    
    title = f"{restaurant.name}"
    if title_suffix:
        title += f" - {title_suffix}"
        
    panel = Panel(
        create_rich_layout(
            layout.grid, 
            layout.height, 
            layout.width, 
            layout.tables,
            robot_position=robot_position,
            highlight_path=highlight_path
        ),
        title=f"[bold blue]{title}[/bold blue]",
        border_style="blue",
        box=ROUNDED,
        padding=(1, 2)
    )
    return panel 
