if flatpak remote-list --columns=name | grep -Fxq tuxemonRepo; then
    flatpak remote-delete tuxemonRepo
fi
flatpak remote-add tuxemonRepo tuxemonRepo --no-gpg-verify --if-not-exists
flatpak install tuxemonRepo org.tuxemon.Tuxemon