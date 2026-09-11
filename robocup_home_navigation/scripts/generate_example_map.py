#!/usr/bin/env python3
"""从 WPR example.world 的静态碰撞盒生成可复现的二维初始地图。

正式比赛前仍应使用 mapping.launch.py 和 SLAM Toolbox 重新建图。本脚本只用于
让仓库自带的示例世界能够直接启动、测试 Nav2，不在运行时读取 Gazebo 真值。
"""

import argparse
import math
from pathlib import Path
import xml.etree.ElementTree as ET


def pose(element):
    node = element.find('pose')
    values = [float(value) for value in node.text.split()] if node is not None else []
    values += [0.0] * (6 - len(values))
    return values[:6]


def compose(parent, child):
    c, s = math.cos(parent[5]), math.sin(parent[5])
    return [
        parent[0] + c * child[0] - s * child[1],
        parent[1] + s * child[0] + c * child[1],
        parent[2] + child[2],
        0.0,
        0.0,
        parent[5] + child[5],
    ]


def main():
    parser = argparse.ArgumentParser(description='从 WPR SDF 生成示例占据栅格地图')
    parser.add_argument('world', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--resolution', type=float, default=0.05)
    parser.add_argument('--min-x', type=float, default=-5.5)
    parser.add_argument('--min-y', type=float, default=-4.5)
    parser.add_argument('--max-x', type=float, default=5.5)
    parser.add_argument('--max-y', type=float, default=4.5)
    parser.add_argument('--laser-height', type=float, default=0.34)
    args = parser.parse_args()

    root = ET.parse(args.world).getroot()
    width = math.ceil((args.max_x - args.min_x) / args.resolution)
    height = math.ceil((args.max_y - args.min_y) / args.resolution)
    pixels = [[254 for _ in range(width)] for _ in range(height)]

    boxes = []
    for model in root.findall('.//world/model'):
        if model.get('name') == 'ground_plane':
            continue
        static = (model.findtext('static') or 'false').strip().lower() == 'true'
        if not static:
            continue
        model_pose = pose(model)
        for link in model.findall('link'):
            link_pose = compose(model_pose, pose(link))
            for collision in link.findall('collision'):
                size = collision.find('geometry/box/size')
                if size is None:
                    continue
                sx, sy, sz = [float(value) for value in size.text.split()]
                collision_pose = compose(link_pose, pose(collision))
                # 二维 SLAM 只会记录激光平面真正扫到的截面。若把高于雷达的
                # 桌面也画进地图，实时扫描和静态地图会长期不一致，AMCL 容易漂移。
                bottom = collision_pose[2] - sz / 2.0
                top = collision_pose[2] + sz / 2.0
                if not bottom <= args.laser_height <= top or sx * sy < 0.0005:
                    continue
                boxes.append((collision_pose[0], collision_pose[1], collision_pose[5], sx, sy))

    for row in range(height):
        y = args.min_y + (row + 0.5) * args.resolution
        for col in range(width):
            x = args.min_x + (col + 0.5) * args.resolution
            for cx, cy, yaw, sx, sy in boxes:
                c, s = math.cos(yaw), math.sin(yaw)
                dx, dy = x - cx, y - cy
                local_x = c * dx + s * dy
                local_y = -s * dx + c * dy
                if abs(local_x) <= sx / 2.0 and abs(local_y) <= sy / 2.0:
                    pixels[row][col] = 0
                    break

    args.output.parent.mkdir(parents=True, exist_ok=True)
    # PGM 第一行对应图像上方，因此需要把地图的 y 方向翻转。
    with args.output.open('w', encoding='ascii') as stream:
        stream.write(f'P2\n{width} {height}\n255\n')
        for row in reversed(pixels):
            stream.write(' '.join(str(value) for value in row) + '\n')
    print(f'已生成 {args.output}：{width}x{height}，静态碰撞盒 {len(boxes)} 个')


if __name__ == '__main__':
    main()
