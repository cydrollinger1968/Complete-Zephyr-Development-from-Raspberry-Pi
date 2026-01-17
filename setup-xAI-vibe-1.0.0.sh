#!/usr/bin/env bash
#        ╔════════════════════════════════════════════════════╗
#        ║   GROK CLI ROCKSTAR INSTALL – RPi 4 BOOKWORM 2026  ║
#        ║     "We don't do ordinary… we do legendary."       ║
#        ╚════════════════════════════════════════════════════╝
#                 ┌──────────────────────────────┐
#                 │   Cy – let's light this up!  │
#                 └──────────────────────────────┘

set -euo pipefail

echo ""
echo "  ██████╗ ██████╗  ██████╗ ██╗  ██╗       ██████╗██╗     ██╗"
echo " ██╔════╝██╔═══██╗██╔═══██╗██║ ██╔╝      ██╔════╝██║     ██║"
echo " ██║     ██║   ██║██║   ██║█████╔╝       ██║     ██║     ██║"
echo " ██║     ██║   ██║██║   ██║██╔═██╗       ██║     ██║     ╚═╝"
echo " ╚██████╗╚██████╔╝╚██████╔╝██║  ██╗      ╚██████╗███████╗██╗"
echo "  ╚═════╝ ╚═════╝  ╚═════╝ ╚═╝  ╚═╝       ╚═════╝╚══════╝╚═╝"
echo ""
echo "                Installing Grok CLI like a BOSS…"
echo "                Bozeman, Montana – January 17, 2026"
echo ""

# ────────────────────────────────────────────────────────────────
echo " [1/6]  Updating the system – no weak links allowed…"
sudo apt update -qq && sudo apt upgrade -yqq --no-install-recommends

# ────────────────────────────────────────────────────────────────
echo " [2/6]  Grabbing the essentials – curl, git, build tools…"
sudo apt install -yqq --no-install-recommends \
    curl git ca-certificates build-essential

# ────────────────────────────────────────────────────────────────
echo " [3/6]  Node.js check – if it ain't here, we summon it…"
if ! command -v node &> /dev/null; then
    echo "    → Summoning Node.js LTS…"
    curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
    sudo apt install -yqq nodejs
else
    echo "    → Node.js already locked & loaded ($(node --version))"
fi

# ────────────────────────────────────────────────────────────────
echo " [4/6]  Bun – because we move FAST around here…"
if ! command -v bun &> /dev/null; then
    echo "    → Installing Bun like it owes us money…"
    curl -fsSL https://bun.sh/install | bash
else
    echo "    → Bun already in the crew ($(bun --version))"
fi

export PATH="$HOME/.bun/bin:$PATH"
if ! grep -q 'bun/bin' ~/.bashrc; then
    echo 'export PATH="$HOME/.bun/bin:$PATH"' >> ~/.bashrc
    echo "    → PATH tattooed into ~/.bashrc"
fi

# ────────────────────────────────────────────────────────────────
echo " [5/6]  Dropping Grok CLI – the main event…"
bun add -g @vibe-kit/grok-cli

# ────────────────────────────────────────────────────────────────
if command -v grok &> /dev/null; then
    echo ""
    echo "  ╔════════════════════════════════════════════╗"
    echo "  ║          GROK CLI IS LIVE – ROCKSTAR MODE  ║"
    echo "  ╚════════════════════════════════════════════╝"
    echo ""
    grok --version
    echo ""
else
    echo "  [ERROR] grok command MIA after install. Call the roadies."
    exit 1
fi

# ────────────────────────────────────────────────────────────────
cat << 'EOF'

  FINAL BOSS INSTRUCTIONS – READ THIS LIKE YOUR NEXT GIG DEPENDS ON IT:

  1. Grab your xAI API key like it’s the last backstage pass:
     → https://console.grok.com → API keys

  2. Load the key – replace YOUR_KEY_HERE with the real deal:

     export GROK_API_KEY=YOUR_KEY_HERE

     # Make it permanent (because we don’t repeat ourselves):
     echo 'export GROK_API_KEY=YOUR_KEY_HERE' >> ~/.bashrc
     source ~/.bashrc

  3. Ignite:

     grok

     Or go full rockstar:
     grok "Yo Grok, let's crank the blinky sample to 64 Hz and OTA this bad boy!"

  You’re now running with the big dogs, Cy.
  Make some noise in Bozeman tonight.

EOF

echo "  Installation complete. Stage is yours. 🎸🔥"
echo ""