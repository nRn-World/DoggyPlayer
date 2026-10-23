# winget manifest

Manifest for `winget install nRnWorld.DoggyPlayer` (schema 1.6.0). Winget packages live in
[microsoft/winget-pkgs](https://github.com/microsoft/winget-pkgs); these files are the source for the pull request.

## First submission

1. Fork `microsoft/winget-pkgs`.
2. Copy `nRnWorld.DoggyPlayer/1.1.77/` to `manifests/n/nRnWorld/DoggyPlayer/1.1.77/` in the fork.
3. Check it: `winget validate manifests\n\nRnWorld\DoggyPlayer\1.1.77` (and optionally `winget install --manifest <folder>` in a clean VM).
4. Open the pull request. The bot runs automated checks and a moderator reviews it.

## New versions

```powershell
wingetcreate update nRnWorld.DoggyPlayer --version <new> --urls https://github.com/nRn-World/DoggyPlayer/releases/download/v<new>/Doggy-Player-Setup-<new>.exe --submit
```

The SHA256 of each installer is also listed on the release page next to the asset.
