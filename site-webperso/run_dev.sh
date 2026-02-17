#!/bin/bash
export npm_config_cache="/Users/oliviercloutier/Desktop/motherload_projet/.npm-cache"
export XDG_CONFIG_HOME="/Users/oliviercloutier/Desktop/motherload_projet/.config"
export PATH="/opt/homebrew/bin:/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/System/Cryptexes/App/usr/bin:/usr/bin:/bin:/usr/sbin:/sbin:/var/run/com.apple.security.cryptexd/codex.system/bootstrap/usr/local/bin:/var/run/com.apple.security.cryptexd/codex.system/bootstrap/usr/bin:/var/run/com.apple.security.cryptexd/codex.system/bootstrap/usr/appleinternal/bin:/opt/pmk/env/global/bin"
[ -s "/Users/oliviercloutier/.nvm/nvm.sh" ] && \. "/Users/oliviercloutier/.nvm/nvm.sh"

echo "Installing with Local Cache..."
npm install

echo "Starting Dev Server..."
npm run dev
