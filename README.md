# tmui

An interactive terminal UI to list, create, and attach to tmux sessions.

## Features

- List all tmux sessions
- Attach to existing sessions
- Create new named sessions
- Keyboard-driven interface
- Zero external dependencies (picotui is bundled)

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/tmui.git

# Create symlink for global access
ln -s /path/to/tmui/tmui ~/.local/bin/tmui
```

## Usage

```bash
tmui
```

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `a` | Attach to selected session |
| `n` | Create new session |
| `r` | Refresh session list |
| `q` | Quit |
| `Enter` | Attach to selected session |
| `Up/Down` | Navigate session list |
| `Tab` | Switch focus between elements |
| `Esc` | Cancel / Close dialog |

## Requirements

- Python 3.10+
- tmux

## License

MIT
