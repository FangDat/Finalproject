from PIL import Image, ImageDraw, ImageFont


def create_vertical_gradient_legend(title, color_stops, output_path):
    """
    Create a vertical gradient legend with smooth color transitions (top to bottom).
    color_stops: list of (color, label)
    """
    width = 300
    height = 400
    margin = 50
    bar_width = 50
    label_x_offset = 130

    img = Image.new("RGB", (width, height), color="white")
    draw = ImageDraw.Draw(img)

    try:
        font_title = ImageFont.truetype("Arial.ttf", 24)
        font_label = ImageFont.truetype("Arial.ttf", 17)
    except:
        font_title = ImageFont.load_default()
        font_label = ImageFont.load_default()

    # Draw title
    draw.text((margin, 15), title, fill="black", font=font_title)

    # Gradient setup
    gradient_height = height - 100
    y_start = 60
    n = len(color_stops) - 1

    # Draw gradient from top (first color) to bottom (last color)
    for j in range(gradient_height):
        ratio = j / gradient_height
        idx = int(ratio * n)
        c1 = color_stops[idx][0].lstrip('#')
        c2 = color_stops[min(idx + 1, n)][0].lstrip('#')

        # Interpolate color
        def interp(a, b):
            return int(int(a, 16) * (1 - (ratio * n - idx)) + int(b, 16) * (ratio * n - idx))

        r = interp(c1[0:2], c2[0:2])
        g = interp(c1[2:4], c2[2:4])
        b = interp(c1[4:6], c2[4:6])
        color = (r, g, b)

        y = y_start + j
        draw.line([(margin, y), (margin + bar_width, y)], fill=color)

    # Draw labels matching gradient order (top → bottom)
    step = gradient_height / (len(color_stops) - 1)
    for i, (color, label) in enumerate(color_stops):
        y = y_start + i * step
        draw.text((label_x_offset, y - 8), label, fill="black", font=font_label)

    img.save(output_path)
    print(f"✅ Vertical gradient legend saved: {output_path}")


if __name__ == "__main__":
    # -------------------------------
    # Temperature Legend
    # -------------------------------
    temp_stops = [
        ("#FFC228", "Hot"),
        ("#C2FF28", "Warm"),
        ("#23DDDD", "Comfortable"),
        ("#208CEC", "Cool"),
        ("#821692", "Very Cold"),
    ]
    create_vertical_gradient_legend(
        "Temperature",
        temp_stops,
        "legend_temperature.png"
    )

    # -------------------------------
    # Rainfall Legend
    # -------------------------------
    rain_stops = [
        ("#1414FF", "Heavy"),
        ("#5078E1", "Moderate"),
        ("#96BFFF", "Light"),
    ]
    create_vertical_gradient_legend(
        "Rainfall",
        rain_stops,
        "legend_rainfall.png"
    )
