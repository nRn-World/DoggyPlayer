# Doggy Player v1.1.78

Security release: the app window is now locked down (no direct system access from web content, no navigation away from the player), network requests made on behalf of playlists can no longer reach local or internal addresses, and the local media server only serves files the player itself opened. Activation codes are now stored on a server and new codes are long and unguessable; existing codes keep working. Favourites sync uses a safer key (your existing favourites are migrated automatically).
