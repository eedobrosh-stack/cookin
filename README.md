# Jarcud + Cookin 🍳
Pure-Python host for the Jarcud landing page and family apps, plus the Cookin
recipe site (Hebrew RTL) and family-vote API.

- Run: `python app.py` (PORT + DATA_DIR envs; defaults 10000, /var/data)
- Videos are NOT in the repo — they live on the Render persistent disk at $DATA_DIR/videos (uploaded via SSH).
- Deployed on Render at `jarcud.com`, `www.jarcud.com`, and `cookin.jarcud.com`.
- Main-domain routes: `/`, `/artifacts`, `/lielmali` (`/game` alias), and
  `/ilsummer` (`/summer` alias). Legacy `/cookin/*` URLs redirect to the
  matching `cookin.jarcud.com` URL.
