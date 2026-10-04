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
pi-profile local --show
```

To update, pull the latest changes and copy the script again. Alternatively, symlink it so updates apply automatically:

```bash
ln -sf "$(pwd)/pi-profile" ~/.local/bin/pi-profile
```

## Usage

```bash
pi-profile {local|remote} [--show] [pi args...]
```

### Profiles

- `local` — loads extensions suitable for a local setup
- `remote` — loads extensions suitable for a remote setup

### Show what will be loaded

Use `--show` immediately after the profile name to preview the selected extensions without launching `pi`:

```bash
pi-profile local --show
pi-profile remote --show
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

`pi-profile` runs `pi list`, parses the available extensions, and then starts `pi` with the matching extension paths.

It skips certain extensions automatically depending on the selected profile. By default:

- `local` skips `pi-ssh-remote-autocomplete-fix`
- `remote` skips `pi-sandbox`

## Configuring excluded extensions

The exclusion list is defined in the `should_load()` function of the script, in the `blocked` dictionary:

```python
blocked = {
    "local": "pi-ssh-remote-autocomplete-fix",
    "remote": "pi-sandbox",
}
```

- Each key is a profile name (`local` or `remote`).
- Each value is a substring. An extension is skipped if this substring appears in its source or path, as shown by `pi list`.

To change which extension is excluded, edit the installed script:

```bash
$EDITOR ~/.local/bin/pi-profile
```

For example, to skip `my-other-extension` in the `local` profile:

```python
blocked = {
    "local": "my-other-extension",
    "remote": "pi-sandbox",
}
```

Use the exact name (or a unique part of it) as it appears in `pi list`. Then check the result:

```bash
pi-profile local --show
```

Skipped extensions are marked `SKIP`.

> Note: each profile currently supports one substring. To exclude several extensions per profile, change `should_load()` to use a tuple of substrings, for example `any(b in extension for b in blocked[mode])`, and make each dictionary value a tuple.

If you installed with a symlink, edit the file in the cloned repository instead.

## Environment variables

- `NO_COLOR` — disable colored output
- `CLICOLOR_FORCE` — force colored output
- `PI_PROFILE_ASCII` — use ASCII output instead of Unicode checkmarks/crosses

## Notes

- `--show` only works as a `pi-profile` option when it appears immediately after `local` or `remote`.
- Any later `--show` is passed through to `pi`.

## Example

```bash
pi-profile local --show
pi-profile remote
```

## License

No license has been specified yet.
