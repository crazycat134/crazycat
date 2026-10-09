"""批量重命名照片为「商品号.张号.JPG」（如 5.1.jpg、5.2.jpg）。

用法：
  1. 把一组照片文件拖到 rename_photos.bat 图标上
  2. 按提示输入商品号 N
  3. 文件按文件名排序后，依次改名为 N.1.jpg、N.2.jpg ...
     （相机默认 P1000001.JPG 之类的命名会自然按拍摄顺序排好）

规则：
  - 只处理 .jpg / .jpeg 文件，其他扩展名跳过
  - 文件名已是「N.M」格式的跳过（避免破坏已有分组）
  - 目标名已存在时跳过，不覆盖
"""
import re
import sys
from pathlib import Path

GROUP_RE = re.compile(r"^\d+\.\d+$")
JPEG_EXTS = (".jpg", ".jpeg")


def main() -> None:
    paths = [p for p in sys.argv[1:] if p]
    if not paths:
        print("没有收到文件。请把照片文件拖到 rename_photos.bat 图标上再运行。")
        return
    try:
        raw = input("请输入商品号 N（照片将改名为 N.1.jpg、N.2.jpg ...）：").strip()
    except EOFError:
        raw = ""
    if not raw.isdigit():
        print("商品号必须是整数，本次未改名。")
        return
    no = int(raw)

    files = []
    for p in paths:
        p = Path(p)
        if not p.is_file():
            print(f"[跳过] 不是文件：{p.name}")
            continue
        if p.suffix.lower() not in JPEG_EXTS:
            print(f"[跳过] 非 JPG/JPEG：{p.name}")
            continue
        files.append(p)
    if not files:
        print("没有可改名的 JPG 文件。")
        return

    files.sort(key=lambda p: p.name.lower())  # 按文件名排序，保证张号顺序
    renamed = []
    skipped = []
    i = 1
    for p in files:
        if GROUP_RE.match(p.stem):
            skipped.append((p.name, "已是「N.M」命名，跳过"))
            continue
        target = p.with_name(f"{no}.{i}.jpg")
        if target.exists():
            skipped.append((p.name, f"目标 {target.name} 已存在，跳过"))
            i += 1  # 该张号被占用，继续用下一个张号
            continue
        p.rename(target)
        renamed.append(f"{p.name}  ->  {target.name}")
        i += 1

    print(f"商品号 {no}：成功改名 {len(renamed)} 张")
    for line in renamed:
        print("  " + line)
    if skipped:
        print(f"跳过 {len(skipped)} 张：")
        for name, reason in skipped:
            print(f"  {name}（{reason}）")


if __name__ == "__main__":
    main()
