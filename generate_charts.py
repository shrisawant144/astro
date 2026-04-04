import sys
import re
import argparse
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# ------------------------------------------------------------
# 1. Parse report – extracts planets, degrees, retro/combust/NB
# ------------------------------------------------------------
def parse_report(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()

    lagna_match = re.search(r'Lagna\s*:\s*([A-Za-z]+)', text)
    if not lagna_match:
        raise ValueError("Lagna not found")
    lagna = lagna_match.group(1).capitalize()

    pattern = r'Planets in Rasi \(D1\):.*?\n-+\n(.*?)(?:\n\n|\Z)'
    block = re.search(pattern, text, re.DOTALL)
    if not block:
        raise ValueError("Planets block not found")

    planets = {}
    for line in block.group(1).split('\n'):
        m = re.match(r'\s*(\w+):\s*([\d\.]+)°\s*([A-Za-z]+)\s*(.*)', line)
        if m:
            planet = m.group(1).strip()
            deg = float(m.group(2))
            sign = m.group(3).strip()
            suffix = m.group(4).strip()
            planets[planet] = {
                'sign': sign,
                'deg': deg,
                'retro': bool(re.search(r'\bR\b', suffix)),
                'combust': bool(re.search(r'\bC\b', suffix)),
                'neecha_bhanga': 'NB' in suffix,
            }
    return lagna, planets

SIGNS = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo",
         "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]

def get_house(lagna, sign):
    return (SIGNS.index(sign) - SIGNS.index(lagna)) % 12 + 1

def format_planet(planet, data):
    """Returns formatted name with markers: (R), (C), (NB)"""
    name = planet
    if data['retro']:
        name += '(R)'
    if data['combust']:
        name += '(C)'
    if data['neecha_bhanga']:
        name += '(N)'
    return name

# ------------------------------------------------------------
# 2. South Indian Chart – fixed 3x4 grid, black/white, readable
# ------------------------------------------------------------
def draw_south_indian(ax, planets, lagna, title):
    ax.set_aspect('equal')
    ax.axis('off')
    grid = [
        ["Aries", "Taurus", "Gemini", "Cancer"],
        ["Leo", "Virgo", "Libra", "Scorpio"],
        ["Sagittarius", "Capricorn", "Aquarius", "Pisces"]
    ]
    sign_planets = {s: [] for s in SIGNS}
    for p, data in planets.items():
        sign_planets[data['sign']].append((p, data))

    w, h = 1.2, 1.0
    for i, row in enumerate(grid):
        for j, sign in enumerate(row):
            x0, y0 = j * w, (2 - i) * h
            rect = patches.Rectangle((x0, y0), w, h, linewidth=1.5,
                                     edgecolor='black', facecolor='white')
            ax.add_patch(rect)
            ax.text(x0 + w/2, y0 + h - 0.1, sign,
                    ha='center', va='top', fontsize=10, fontweight='bold')
            plist = sign_planets[sign]
            if plist:
                lines = [format_planet(p, d) for p, d in plist]
                text = '\n'.join(lines)
                ax.text(x0 + w/2, y0 + h/2, text,
                        ha='center', va='center', fontsize=9, fontfamily='monospace')
            if sign == lagna:
                ax.text(x0 + w - 0.1, y0 + 0.05, "Lg",
                        ha='right', va='bottom', fontsize=8, color='red', fontweight='bold')
    ax.set_xlim(-0.2, 4*w + 0.2)
    ax.set_ylim(-0.2, 3*h + 0.2)
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)

# ------------------------------------------------------------
# 3. North Indian Chart – true diamond geometry, correct house mapping
# ------------------------------------------------------------
def draw_north_indian(ax, planets, lagna, title):
    ax.set_aspect('equal')
    ax.axis('off')

    # Map planets to houses
    house_planets = {}
    for p, data in planets.items():
        h = get_house(lagna, data['sign'])
        house_planets.setdefault(h, []).append((p, data))

    # Outer diamond (size 4)
    outer = [(0, 4), (4, 0), (0, -4), (-4, 0)]
    ax.add_patch(patches.Polygon(outer, closed=True, fill=False, linewidth=2.2, edgecolor='black'))

    # Inner diamond (size 2)
    inner = [(0, 2), (2, 0), (0, -2), (-2, 0)]
    ax.add_patch(patches.Polygon(inner, closed=True, fill=False, linewidth=1.6, edgecolor='black'))

    # ==== CORRECT DIAGONAL DIVISIONS (outer triangles) ====
    # Top outer vertex → inner left/right
    ax.plot([0, 2], [4, 0], color='black', linewidth=1.1)
    ax.plot([0, -2], [4, 0], color='black', linewidth=1.1)

    # Right outer vertex → inner top/bottom
    ax.plot([4, 0], [0, 2], color='black', linewidth=1.1)
    ax.plot([4, 0], [0, -2], color='black', linewidth=1.1)

    # Bottom outer vertex → inner left/right
    ax.plot([0, 2], [-4, 0], color='black', linewidth=1.1)
    ax.plot([0, -2], [-4, 0], color='black', linewidth=1.1)

    # Left outer vertex → inner top/bottom
    ax.plot([-4, 0], [0, 2], color='black', linewidth=1.1)
    ax.plot([-4, 0], [0, -2], color='black', linewidth=1.1)

    # ==== INNER DIVISION (the missing part) ====
    # Draw the two diagonals of the inner diamond → divides it into 4 proper inner houses
    ax.plot([-2, 2], [0, 0], color='black', linewidth=1.1)   # horizontal
    ax.plot([0, 0], [-2, 2], color='black', linewidth=1.1)   # vertical

    # House centers (fine-tuned for perfect visual balance)
    house_centers = {
        1:  (0.00,  3.05),   # Top
        2:  (2.15,  2.15),   # Top-right
        3:  (3.05,  0.00),   # Right
        4:  (2.15, -2.15),   # Bottom-right
        5:  (0.00, -3.05),   # Bottom
        6:  (-2.15, -2.15),  # Bottom-left
        7:  (-3.05,  0.00),  # Left
        8:  (-2.15,  2.15),  # Top-left
        9:  (-1.15,  0.00),  # Inner left
        10: (0.00,  -1.15),  # Inner bottom
        11: (1.15,   0.00),  # Inner right
        12: (0.00,   1.15),  # Inner top
    }

    for h, plist in house_planets.items():
        if h not in house_centers:
            continue
        cx, cy = house_centers[h]
        # Max 4 planets per house to avoid overflow
        lines = [format_planet(p, d) for p, d in plist][:4]
        text = '\n'.join(lines)
        
        ax.text(cx, cy, text, ha='center', va='center',
                fontsize=10, fontfamily='monospace', linespacing=1.05)

    # Optional faint house numbers (very common in North Indian charts)
    for h, (cx, cy) in house_centers.items():
        ax.text(cx * 0.72, cy * 0.72, str(h),
                ha='center', va='center',
                fontsize=8.5, color='gray', alpha=0.55)

    # Lagna marker
    ax.text(0, 3.82, "L", color='red', ha='center', va='center',
            fontsize=13, fontweight='bold')

    ax.set_xlim(-4.8, 4.8)
    ax.set_ylim(-4.8, 4.8)
    ax.set_title(title, fontsize=14, fontweight='bold', pad=25)

# ------------------------------------------------------------
# 4. Main
# ------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description='Generate traditional Vedic charts (North & South Indian).')
    parser.add_argument('file', help='Path to kundali report file')
    parser.add_argument('--output-prefix', default='kundali', help='Prefix for output PNG files')
    args = parser.parse_args()

    try:
        lagna, planets = parse_report(args.file)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

    print(f"Lagna: {lagna}, Planets: {list(planets.keys())}")

    # South Indian chart
    fig1, ax1 = plt.subplots(figsize=(8, 6))
    draw_south_indian(ax1, planets, lagna, f"South Indian Chart - {lagna} Lagna")
    plt.tight_layout()
    plt.savefig(f"{args.output_prefix}_south.png", dpi=200, bbox_inches='tight', facecolor='white')
    plt.close(fig1)
    print(f"Saved: {args.output_prefix}_south.png")

    # North Indian chart
    fig2, ax2 = plt.subplots(figsize=(8, 8))
    draw_north_indian(ax2, planets, lagna, f"North Indian Chart - {lagna} Lagna")
    plt.tight_layout()
    plt.savefig(f"{args.output_prefix}_north.png", dpi=200, bbox_inches='tight', facecolor='white')
    plt.close(fig2)
    print(f"Saved: {args.output_prefix}_north.png")

if __name__ == "__main__":
    main()