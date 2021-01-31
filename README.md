# 🎨 Custom Highlighter

[![Package Control](https://img.shields.io/packagecontrol/dt/Custom%20Highlighter.svg)](https://packagecontrol.io/packages/Custom%20Highlighter)
[![Package Control](https://img.shields.io/badge/license-MIT-green)](https://github.com/devlop-ab/custom-highlighter/blob/master/README.md)

![Description](screenshots/screenshot.png?raw=true)

Custom Highlighter lets you highlight any words you wish with any color you desire, it's based on (and inspired by) [Kronuz/ColorHighlight](https://github.com/Kronuz/ColorHighlight), but instead of coming with a preconfigured set of words/patterns to highlight, Custom Highlighter comes with zero assumptions and let you configure any color highlights you wish, as you wish.

This is **not a replacement** for _Kronuz/ColorHighlight_, but they do work great together for maximum coloring goodness.

## Installation

- **_Recommended_** - Using [Sublime Package Control](https://packagecontrol.io "Sublime Package Control")
    - <kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>P</kbd> then select `Package Control: Install Package`
    - install `Custom Highlighter`
- Alternatively, download the package from [GitHub](https://github.com/devlop-ab/custom-highlighter "Custom Highlighter") into your `Packages` folder and make sure to rename the directory to "Custom Highlighter".


## Usage

After installation, open up the settings (`Preferences > Package Settings > Custom Highlighter > Settings`) and configure it to fit you needs, entries are added as simple `key value` configurations, there is no regex support or wildcards when matching keywords, all keywords are matched exactly as configured.

Usage example for Tailwind:

```
{
    "colors": {
        "bg-green-100": "#BBF7D0",
        "text-amber-600": "#D97706",
        "text-cyan-600": "#0891B2",
    }
}
```

![Tailwind Example](screenshots/example-tailwind.png?raw=true)

## Configuration

- You can disable live highlight directly from the command palette:
  `Custom Highlighter: Disable Custom Highlighter`

- Open settings using the command palette:
  `Preferences: Custom Highlighter Settings - User`

- Gutter icons can be switched among three flavors (or disabled) by using
  the `gutter_icon` setting:

  + "circle" - Gutter icon with the color in a circle
  + "square" - Gutter icon with the color in a square
  + "fill" - Fill whole gutter with color

  ```
  "gutter_icon": "fill"
  ```

  ![Gutter Icon](screenshots/gutter_icon.png?raw=true)

- Highlighting the value region in the color can be enabled or disabled by
  using the `highlight_values` setting.


## License

Copyright (C) 2021 Johan Rosenson. All rights reserved.

MIT license

This plugin was initially a fork of
https://github.com/Kronuz/ColorHighlight
