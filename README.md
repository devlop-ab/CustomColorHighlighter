# 🎨 Custom Highlighter

[![Package Control](https://img.shields.io/packagecontrol/dt/Custom%20Highlighter.svg)](https://packagecontrol.io/packages/Custom%20Highlighter)

## Installation

- **_Recommended_** - Using [Sublime Package Control](https://packagecontrol.io "Sublime Package Control")
    - <kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>P</kbd> then select `Package Control: Install Package`
    - install `Custom Highlighter`
- Alternatively, download the package from [GitHub](https://github.com/devlop-ab/custom-highlighter "Custom Highlighter") into your `Packages` folder and make sure to rename the directory to "Custom Highlighter".


## Usage

Any keywords you configure in the user settings will be highlighted

Add new elements in this format (in the colors key): `"keyword": "#f00"`

Those will be shown with colored background and gutter icons when they're found in
your documents.


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
  "user": {
    "gutter_icon": "fill"
  }
  ```

  ![Gutter Icon](screenshots/gutter_icon.png?raw=true)

- Highlighting the value region in the color can be enabled or disabled by
  using the `highlight_values` setting.


## License

Copyright (C) 2021 Johan Rosenson. All rights reserved.

MIT license

This plugin was initially a fork of
https://github.com/Kronuz/ColorHighlight
