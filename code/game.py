import os # 用于清屏

# --- 游戏元素 ---
WALL = '#'
FLOOR = ' '
PLAYER = '@'
BOX = '$'
TARGET = '.'
BOX_ON_TARGET = '*' # 箱子在目标点上
PLAYER_ON_TARGET = '+' # 玩家在目标点上

# --- 示例关卡 ---
# 你可以设计更多关卡
# 规则：关卡必须用墙包围，确保玩家和箱子不会出界
LEVELS = [
    [
        "#####",
        "#@$.#",
        "#####"
    ],
    [
        "#######",
        "#.@   #",
        "# $ # #",
        "# $ . #",
        "#   . #",
        "#######"
    ],
    [
        "    #####",
        "    #   #",
        "    #$  #",
        "  ###  $##",
        "  #  $ $ #",
        "### # ## #   ######",
        "#   # ## #####  ..#",
        "# $  $          ..#",
        "##### ### #@##  ..#",
        "    #     #########",
        "    #######"
    ]
]

def clear_screen():
    """清空控制台屏幕"""
    os.system('cls' if os.name == 'nt' else 'clear')

def display_level(level_map):
    """显示当前关卡状态"""
    clear_screen()
    print("推箱子 (Sokoban) - 输入 'q' 退出, 'r' 重玩")
    print("控制: w(上) a(左) s(下) d(右)")
    print("-" * (len(level_map[0]) if level_map else 20)) # 分隔线
    for row in level_map:
        print("".join(row))
    print("-" * (len(level_map[0]) if level_map else 20))

def find_player_position(level_map):
    """找到玩家在地图上的位置"""
    for r, row_data in enumerate(level_map):
        for c, char in enumerate(row_data):
            if char == PLAYER or char == PLAYER_ON_TARGET:
                return r, c
    return None # 应该不会发生，除非关卡设计错误

def get_targets(initial_level_map):
    """获取所有目标点的位置"""
    targets = []
    for r, row_data in enumerate(initial_level_map):
        for c, char in enumerate(row_data):
            if char == TARGET or char == BOX_ON_TARGET or char == PLAYER_ON_TARGET:
                targets.append((r, c))
    return targets

def move(level_map, initial_level_map_for_targets, dr, dc):
    """
    处理玩家移动和推箱子逻辑
    level_map: 当前可变的地图列表
    initial_level_map_for_targets: 初始地图，用于确定哪些是原始目标点
    dr, dc: 行和列的移动方向 (-1, 0, 1)
    """
    player_r, player_c = find_player_position(level_map)
    
    next_player_r, next_player_c = player_r + dr, player_c + dc

    # 检查目标位置是否越界 (通常由墙壁阻止，但以防万一)
    if not (0 <= next_player_r < len(level_map) and 0 <= next_player_c < len(level_map[0])):
        return False # 移动无效

    tile_at_next_pos = level_map[next_player_r][next_player_c]

    # 1. 移动到空地或目标点
    if tile_at_next_pos == FLOOR or tile_at_next_pos == TARGET:
        # 更新玩家旧位置
        if (player_r, player_c) in get_targets(initial_level_map_for_targets):
            level_map[player_r][player_c] = TARGET
        else:
            level_map[player_r][player_c] = FLOOR
        
        # 更新玩家新位置
        if tile_at_next_pos == TARGET:
            level_map[next_player_r][next_player_c] = PLAYER_ON_TARGET
        else:
            level_map[next_player_r][next_player_c] = PLAYER
        return True

    # 2. 尝试推箱子
    elif tile_at_next_pos == BOX or tile_at_next_pos == BOX_ON_TARGET:
        box_r, box_c = next_player_r, next_player_c # 箱子当前位置
        next_box_r, next_box_c = box_r + dr, box_c + dc # 箱子将要移动到的位置

        # 检查箱子目标位置是否越界
        if not (0 <= next_box_r < len(level_map) and 0 <= next_box_c < len(level_map[0])):
            return False

        tile_behind_box = level_map[next_box_r][next_box_c]

        if tile_behind_box == FLOOR or tile_behind_box == TARGET:
            # 更新箱子旧位置 (现在是玩家的新位置)
            if (box_r, box_c) in get_targets(initial_level_map_for_targets):
                level_map[box_r][box_c] = PLAYER_ON_TARGET # 玩家移动到原箱子(目标点)位置
            else:
                level_map[box_r][box_c] = PLAYER # 玩家移动到原箱子(空地)位置
            
            # 更新箱子新位置
            if tile_behind_box == TARGET:
                level_map[next_box_r][next_box_c] = BOX_ON_TARGET
            else:
                level_map[next_box_r][next_box_c] = BOX

            # 更新玩家旧位置
            if (player_r, player_c) in get_targets(initial_level_map_for_targets):
                level_map[player_r][player_c] = TARGET
            else:
                level_map[player_r][player_c] = FLOOR
            return True
    
    # 3. 撞墙或其他情况 (如撞到另一个箱子后面是墙)
    return False # 移动无效

def check_win(level_map, targets):
    """检查是否所有目标点都被箱子占据"""
    if not targets: return False # 如果没有目标点，无法获胜
    for r_target, c_target in targets:
        if level_map[r_target][c_target] != BOX_ON_TARGET:
            return False # 只要有一个目标点上没有箱子，就没赢
    return True

def play_sokoban(level_index=0):
    """主游戏逻辑"""
    if level_index >= len(LEVELS):
        print("恭喜你！已通过所有关卡！")
        return

    # 将字符串关卡转换为列表的列表，方便修改
    initial_level_design = LEVELS[level_index]
    current_level_map = [list(row) for row in initial_level_design]
    # 保存一份初始地图用于判断目标点
    initial_level_map_for_targets_logic = [list(row) for row in initial_level_design] 

    targets = get_targets(initial_level_map_for_targets_logic)
    moves_count = 0

    while True:
        display_level(current_level_map)
        print(f"关卡: {level_index + 1}/{len(LEVELS)} | 步数: {moves_count}")

        if check_win(current_level_map, targets):
            print("恭喜！你赢了这一关！")
            input("按回车键进入下一关...")
            play_sokoban(level_index + 1) # 进入下一关
            return # 当前关卡结束

        action = input("移动 (w/a/s/d) 或操作 (q/r): ").lower()

        dr, dc = 0, 0
        if action == 'w':
            dr = -1
        elif action == 's':
            dr = 1
        elif action == 'a':
            dc = -1
        elif action == 'd':
            dc = 1
        elif action == 'q':
            print("感谢游玩！")
            return
        elif action == 'r':
            print("重置关卡...")
            play_sokoban(level_index) # 重新开始当前关卡
            return
        else:
            print("无效输入！")
            input("按回车键继续...") # 暂停一下，让用户看到提示
            continue

        if dr != 0 or dc != 0:
            if move(current_level_map, initial_level_map_for_targets_logic, dr, dc):
                moves_count += 1
        
if __name__ == "__main__":
    play_sokoban()
