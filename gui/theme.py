"""
Shared colour palettes for MiniServer GUI.
Import get_colors(dark: bool) to retrieve the active palette.
"""

DARK: dict = {
    "bg":         "#0b0b0f",
    "surface":    "#111118",
    "surface2":   "#16161f",
    "surface3":   "#1c1c28",
    "border":     "#1e1e2c",
    "border2":    "#262636",
    "accent":     "#6c8fff",
    "accent_dim": "#6c8fff18",
    "accent_mid": "#6c8fff35",
    "text":       "#ddddf0",
    "text2":      "#a0a0c0",
    "muted":      "#484868",
    "dimmer":     "#252538",
    "success":    "#4ade80",
    "danger":     "#ff5e7a",
    "warn":       "#fbbf24",
    "mono":       "'JetBrains Mono','SF Mono','Consolas',monospace",
    "sans":       "'Segoe UI Variable','SF Pro Display','Inter','Segoe UI',sans-serif",
}

LIGHT: dict = {
    "bg":         "#f0f0f8",
    "surface":    "#ffffff",
    "surface2":   "#eaeaf4",
    "surface3":   "#e2e2ee",
    "border":     "#d4d4e8",
    "border2":    "#c4c4dc",
    "accent":     "#4c6fff",
    "accent_dim": "#4c6fff14",
    "accent_mid": "#4c6fff28",
    "text":       "#0e0e20",
    "text2":      "#484870",
    "muted":      "#8080b0",
    "dimmer":     "#c0c0d8",
    "success":    "#15803d",
    "danger":     "#dc2626",
    "warn":       "#b45309",
    "mono":       "'JetBrains Mono','SF Mono','Consolas',monospace",
    "sans":       "'Segoe UI Variable','SF Pro Display','Inter','Segoe UI',sans-serif",
}


def get_colors(dark: bool) -> dict:
    return DARK.copy() if dark else LIGHT.copy()