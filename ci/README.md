# Hardware-in-the-loop CI

The mosaic rig is four nRF52832 boards on one motherboard, each driving a GDEY042T81 400×300 panel. A self-hosted GitHub Actions runner on the rig Pi builds an app from the Zephyr workspace already on that machine, checks each board's FICR identity over SWD, saves the current flash locally, programs the new image, and can take a camera picture of the panels. This repository is public. The workflow never contains a LAN address, a hostname, a password, or a signing key. In these notes the machine is only "the rig Pi".

Slot letters, GPIO, and the identity words are the ones in [hardware/slot-map.md](../hardware/slot-map.md). The motherboard silkscreen is swapped top-to-bottom relative to those letters. The pipeline trusts FICR, not the silkscreen.

## What a run does

[`.github/workflows/hil.yml`](../.github/workflows/hil.yml) runs on the runner labels `self-hosted`, `linux`, `ARM64`, and `eink-mosaic`. It starts only from a push to `main` by the repository owner, or from a manual `workflow_dispatch` by that same owner. It does not run on pull requests.

One run at a time. A second run waits; an in-progress flash is not cancelled.

Steps, in order:

1. Check out this repo. The checkout token is not left on the runner.
2. `scripts/hil/build.sh` runs `west build -p always` for the selected app and board. Zephyr is the workspace at `$HOME/zephyrproject` (v4.4.0, west, and the arm SDK are expected to be installed there already). Apps are not in this repo. The app directory is `$EINK_APPS_DIR/<app>`, and `$EINK_APPS_DIR` defaults to `$HOME/zephyrproject/apps`.
3. `scripts/hil/ficr_check.sh` halts each board and reads FICR `DEVICEADDR[0]` at `0x100000A4`. That is the identity word in the slot map (A `f15c2668`, B `944d9a60`, C `b0749cd0`, D `4bdf4558`). If any board does not match [ci/expected/slots.json](expected/slots.json), the run stops and nothing is programmed.
4. `scripts/hil/backup.sh` dumps each flash image with OpenOCD `dump_image` into `$HOME/hil-runs/<run-id>/backups/`. Default length is 512 KiB (`0x80000` in the slot table). Override with `HIL_FLASH_BYTES` on the runner if a board is the smaller part.
5. `scripts/hil/flash.sh` programs `zephyr.hex` (or `zephyr.signed.hex` when the app build produced one) and runs OpenOCD `verify_image`. It will not program a slot that has no backup. `nRESET` is not used.
6. `scripts/hil/verify_camera.sh` runs when camera verification is on (the default, including pushes to `main`). It calls `$HOME/capture_avg` with a frame count and optional shutter and gain. That tool averages frames and runs its analyzer, writing `$HOME/oc_stack/<timestamp>/`. Images and the report are copied for upload. If `capture_avg` is not installed, this step skips and the run still succeeds.
7. If any step after the backup fails, `scripts/hil/rollback.sh` programs each backup back and verifies it. A failure before any backup exists does not invent a restore.

Tile order is B, A, C, D (tiles 0, 1, 2, 3). OpenOCD uses the configs in [hardware/openocd/](../hardware/openocd/) at the 500 kHz `linuxgpiod` / `gpiochip4` settings already in those files. SWD is one board at a time.

### Manual inputs

| Input | Default | Meaning |
|-------|---------|---------|
| `app` | `mosaic_block_diagram` | Directory name under the apps directory |
| `board` | `custom_nrf52832` | `west -b` board id. Change this if the app's board name differs. |
| `apps_dir` | empty, so `$HOME/zephyrproject/apps` | Absolute path on the runner |
| `verify_camera` | true | Set false to skip the camera |
| `camera_frames` | `4` | First argument to `capture_avg` |
| `camera_shutter` | empty | Optional second argument |
| `camera_gain` | empty | Optional third argument, used only with a shutter |

A push to `main` uses those defaults.

### Artifacts

GitHub stores only logs, the firmware sha256, and camera images or the skip note. Flash backups stay on the rig Pi under `$HOME/hil-runs/<run-id>/backups/` because a public artifact would publish the previous firmware. Camera pictures are public. Do not flash an image that shows a LAN address, a key, or any other secret on the panels.

## Security model

This is a public repository with a self-hosted runner that can reprogram hardware and can see the rig Pi's filesystem.

- `hil.yml` has no `pull_request` and no `pull_request_target` trigger. A pull request from a fork must not be able to start this job. [`.github/workflows/lint.yml`](../.github/workflows/lint.yml) is the workflow that runs on pull requests: shellcheck and a check of `slots.json`, on a GitHub-hosted Ubuntu runner, with no hardware access.
- The hardware job has `if: github.repository_owner == 'cydrollinger1968' && github.actor == 'cydrollinger1968'`. Someone else's dispatch or push skips the job.
- Workflow permissions are `contents: read`. The checkout does not leave its credential on disk.
- Only one hardware run is allowed at a time, and a running flash is not cancelled out from under the probes.
- MCUboot signing keys stay on the runner, in whatever path the app already uses. They are not committed, and they are not GitHub Actions secrets unless you later decide to change that. This workflow does not read `secrets.*`.
- Scripts use `set -euo pipefail`, do not call `sudo`, and do not embed passwords, Wi-Fi details, addresses, or hostnames. Home directories are `$HOME`.
- App and board inputs are checked before they are passed to west. The apps path must be absolute and must not contain `..`.
- FICR is checked before any programming. A mismatch refuses the flash.
- Backups are local. Rollback uses them only after a backup has been written.

In the repository settings, keep the default that workflows from outside collaborators need approval, and do not add a pull-request trigger to `hil.yml` later.

## Runner setup on the rig Pi

Do this once, as the normal user that already builds Zephyr and can open the panels' SWD lines. Do not register the runner as root. The service has to be that user so GPIO, the camera, and `$HOME/zephyrproject` are visible.

1. Confirm the tools the scripts call are already on `PATH` for that user: `openocd`, `west`, `python3`, `timeout`, and `sha256sum`. `west` may live in `$HOME/zephyrproject/.venv`; the build script activates that virtualenv when it is present. The Zephyr tree is `$HOME/zephyrproject` at v4.4.0 with the arm SDK. Apps live under `$HOME/zephyrproject/apps` unless you pass another directory.
2. Put the user in the `gpio` and `video` groups so SWD and the OV5647 camera work. Log out and back in after changing groups. The HIL scripts themselves never call `sudo`.

   ```bash
   sudo usermod -aG gpio,video "$USER"
   ```

3. On GitHub, open this repository's Settings, then Actions, then Runners, then New self-hosted runner. Choose Linux and ARM64. The page shows the current runner tarball and a short-lived registration token. Use those commands. Name the runner `eink-mosaic`. Do not put the machine's hostname in the runner name. Keep the default labels the page selects (`self-hosted`, `linux`, `ARM64`) and add `eink-mosaic`.
4. Install and start the service as that same user, from the runner directory:

   ```bash
   ./svc.sh install
   ./svc.sh start
   ```

   `svc.sh install` may ask for administrator rights once to register a systemd unit. The unit's user must be the account from step 1, not root. The registration token is typed into `config.sh` when GitHub shows it. It is not stored in this repo.
5. The runner should show Idle with labels `self-hosted`, `linux`, `ARM64`, and `eink-mosaic`.
6. Run the workflow once by hand (Actions, Hardware in the loop, Run workflow) before relying on pushes. Set `board` to the west board id the app actually uses if it is not `custom_nrf52832`. Set `verify_camera` false until `$HOME/capture_avg` is in place, or leave it true: a missing tool is skipped.

A push to `main` by the owner queues a hardware run. Register the runner before merging workflow changes you want exercised, or cancel the queued run if the runner is not ready yet.

## Files

| Path | Role |
|------|------|
| `.github/workflows/hil.yml` | Hardware workflow |
| `.github/workflows/lint.yml` | Shellcheck and slot-table check, safe on pull requests |
| `scripts/hil/common.sh` | Slot table, OpenOCD wrapper, run directory |
| `scripts/hil/build.sh` | `west build -p always` |
| `scripts/hil/ficr_check.sh` | Identity check; refuse to flash on mismatch |
| `scripts/hil/backup.sh` | `dump_image` into the local run directory |
| `scripts/hil/flash.sh` | `program` then `verify_image` |
| `scripts/hil/verify_camera.sh` | Optional `capture_avg` hook |
| `scripts/hil/rollback.sh` | Restore local backups after a failure |
| `ci/expected/slots.json` | Letter, FICR word, OpenOCD config, tile index |
