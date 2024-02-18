flatpak remote-delete tuxemonRepo
flatpak remote-add tuxemonRepo tuxemonRepo --no-gpg-verify --if-not-exists
flatpak install tuxemonRepo org.tuxemon.Tuxemon