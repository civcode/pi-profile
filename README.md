# pi-profile

`pi-profile` is a small wrapper around [`pi`](https://github.com/hiromi-kyoda/pi) that loads different extension sets depending on whether you want a **local** or **remote** profile.

It can also show you which extensions will be loaded before launching `pi`.

## Requirements

- Python 3
- [`pi`](https://github.com/hiromi-kyoda/pi) installed and available on your `PATH`

## Installation

Install the script into `~/.local/bin` (no `sudo` needed):

```bash
git clone https://github.com/civcode/pi-profile.git
cd pi-profile
mkdir -p ~/.local/bin
cp pi-profile ~/.local/bin/pi-profile
chmod +x ~/.local/bin/pi-profile
```

Make sure `~/.local/bin` is on your `PATH`. If it is not, add this to your `~/.bashrc` or `~/.zshrc`:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

Verify the installation:

```bash
pi-profile --show local
```

To update, pull the latest changes and copy the script again. Alternatively, symlink it so updates apply automatically:

```bash
ln -sf "$(pwd)/pi-profile" ~/.local/bin/pi-profile
```

## Usage

```bash
pi-profile [--show] {local|remote} [pi args...]
```

### Profiles

- `local` — loads extensions suitable for a local setup
- `remote` — loads extensions suitable for a remote setup

### Show what will be loaded

Use `--show` before the profile name to preview the selected extensions without launching `pi`:

```bash
pi-profile --show local
pi-profile --show remote
```

Example output:

```text
Found extensions:
  [✓ USE] npm: /home/user/.pi/extensions/npm
  [✗ SKIP] git: /home/user/.pi/extensions/pi-sandbox
```

### Launch `pi` with a profile

```bash
pi-profile local
pi-profile remote
```

Any additional arguments are passed through to `pi`:

```bash
pi-profile local -- some-command
```

## How it works

`pi-profile` runs `pi list`, parses the available extensions (including relative or absolute local package paths), deduplicates repeated resolved paths, and then starts `pi` with the matching extension paths.

Pi's `--no-extensions` option disables built-in extensions too. Since `pi list` does not list them, `pi-profile` discovers the currently installed built-ins **at every invocation** by resolving the `pi` executable and importing `../extensions/index.js` from its installed package. The registry's `builtInExtensions` export supplies the names used as `-e builtin:...` arguments for both profiles. There is **no hardcoded list**, so newly added or renamed built-ins are included automatically.

For example, if the registry contains `llama.cpp`, the preview from `pi-profile --show local` or `pi-profile --show remote` includes `builtin:llama.cpp`.

**Requirements:** Node.js must be on `PATH` and the Pi installation must expose the `builtInExtensions` array at that registry path. If discovery fails, the command exits with an error instead of starting Pi without its built-ins. This assumes Pi keeps its current registry layout; changes to the registry location or API require updating the discovery code.

**Filtering:** Both profiles include every discovered built-in by default. To exclude a particular built-in from a profile, add its full name (such as `"builtin:tool-search"`) to `BLOCKED_FOR_LOCAL` or `BLOCKED_FOR_REMOTE`. Explicit `-e` loading can override a built-in disabled in Pi's own settings; use the profile exclusion lists if needed.

It skips certain extensions automatically depending on the selected profile. By default:

- `local` skips `pi-ssh-remote-autocomplete-fix` and `pi-ssh-remote`
- `remote` skips `pi-sandbox`

## Configuring excluded extensions

The exclusion lists are defined near the top of the `pi-profile` script:

```python
# Package-name fragments excluded from the local profile.
# Match against the source shown by `pi list` or its resolved filesystem path.
BLOCKED_FOR_LOCAL = ["pi-ssh-remote-autocomplete-fix", "pi-ssh-remote"]

# Package-name fragments excluded from the remote profile.
# The sandbox extension is intended for the local profile only.
BLOCKED_FOR_REMOTE = ["pi-sandbox"]
```

Each constant is a list of substrings. An extension is skipped if **any** substring matches its source or path in `pi list`.

To change which extension is excluded, edit the installed script:

```bash
$EDITOR ~/.local/bin/pi-profile
```

For example, to also skip `my-other-extension` in the `local` profile:

```python
BLOCKED_FOR_LOCAL = [
    "pi-ssh-remote-autocomplete-fix",
    "pi-ssh-remote",
    "my-other-extension",
]
```

Use the exact name (or a unique part of it) as it appears in `pi list`. Then check the result:

```bash
pi-profile --show local
```

Skipped extensions are marked `SKIP`.

If you installed with a symlink, edit the file in the cloned repository instead.

## Environment variables

- `NO_COLOR` — disable colored output
- `CLICOLOR_FORCE` — force colored output
- `PI_PROFILE_ASCII` — use ASCII output instead of Unicode checkmarks/crosses

## Notes

- `--show` only works as a `pi-profile` option when it appears before `local` or `remote`.
- Any `--show` following the profile name is passed through to `pi`.

## Example

```bash
pi-profile --show local
pi-profile remote
```

## License

No license has been specified yet.
