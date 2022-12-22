# ref https://github.com/thankjura/beat-audio-player-rs

# beat-audio-player [WIP]

Simple audioplayer for GNOME.

![](data/screenshots/1.png?raw=true&v=2)

![](data/screenshots/2.png?raw=true&v=2)

## Packaging status

### Fedora

Available in [COPR](https://copr.fedorainfracloud.org/coprs/atim/beat-audio-player/):

```
sudo dnf copr enable atim/beat-audio-player -y
sudo dnf install beat-audio-player
```

## Build from source

### Flatpak

```sh
flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo

flatpak install runtime/org.gnome.Sdk/x86_64/3.36

git clone https://github.com/thankjura/beat-audio-player.git

cd beat-audio-player

git submodule update --init --recursive

mkdir -p $HOME/Projects/flatpak/repo

flatpak-builder --repo=$HOME/Projects/flatpak/repo --force-clean --ccache build-dir ru.slie.beat.yaml

flatpak remote-add --no-gpg-verify local-repo $HOME/Projects/flatpak/repo

flatpak install ru.slie.beat
```
