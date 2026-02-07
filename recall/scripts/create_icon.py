"""生成Recall托盘图标 - 仅圆弧"""
from PIL import Image, ImageDraw

def create_recall_icon():
    """创建简洁的圆弧图标"""
    sizes = [16, 32, 48, 64, 128, 256]
    images = []

    for size in sizes:
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        center = size // 2
        line_width = max(2, size // 8)

        # 绘制圆形背景
        bg_radius = int(size * 0.46)
        draw.ellipse(
            [center - bg_radius, center - bg_radius,
             center + bg_radius, center + bg_radius],
            fill=(66, 133, 244, 255)  # 蓝色
        )

        # 仅绘制3/4圆弧
        arrow_color = (255, 255, 255, 255)
        arc_radius = int(size * 0.28)

        bbox = [center - arc_radius, center - arc_radius,
                center + arc_radius, center + arc_radius]
        draw.arc(bbox, start=45, end=315, fill=arrow_color, width=line_width)

        images.append(img)

    # 保存
    icon_path = "D:/BaiduSyncdisk/Desktop/recall/assets/icon.ico"
    images[0].save(
        icon_path,
        format='ICO',
        sizes=[(s, s) for s in sizes],
        append_images=images[1:]
    )
    print(f"图标已保存到: {icon_path}")

    png_path = "D:/BaiduSyncdisk/Desktop/recall/assets/icon.png"
    images[-1].save(png_path, format='PNG')
    print(f"PNG预览已保存到: {png_path}")

if __name__ == "__main__":
    create_recall_icon()
