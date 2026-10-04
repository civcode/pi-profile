# pi-profile

`pi-profile` is a small wrapper around [`pi`](https://github.com/hiromi-kyoda/pi) that loads different extension sets depending on whether you want a **local** or **remote** profile.

It can also show you which extensions will be loaded before launching `pi`.

## Requirements

- Python 3
- [`pi`](https://github.com/hiromi-kyoda/pi) installed and available on your `PATH`

## Installation

### Option 1: Clone the repository

```bash
git clone https://github.com/civcode/pi-profile.git
cd pi-profile
chmod +x pi-profile
```

Then run it directly:

```bash
./pi-profile local
```

### Option 2: Put it on your PATH

Copy the `pi-profile` script somewhere on your `PATH`, for example:

```bash
sudo cp pi-profile /usr/local/bin/pi-profile
sudo chmod +x /usr/local/bin/pi-profile
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

It skips certain extensions automatically depending on the selected profile:

- `local` skips `pi-ssh-remote-autocomplete-fix`
- `remote` skips `pi-sandbox`

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
