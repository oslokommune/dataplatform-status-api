# status-api
API for tracking status through a asynchronous system

## Install/Setup
1. Install [Serverless Framework](https://serverless.com/framework/docs/getting-started/)
2. Setup venv
```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
3. Install Serverless plugins: `make init`
4. Install Python toolchain: `python3 -m pip install (--user) tox black pip-tools`
   - If running with `--user` flag, add `$HOME/.local/bin` to `$PATH`
