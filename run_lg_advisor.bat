@echo off
setlocal

cd /d "%~dp0artifacts\lg-advisor"

set STREAMLIT_SERVER_HEADLESS=true
set STREAMLIT_SERVER_ADDRESS=127.0.0.1
set STREAMLIT_SERVER_PORT=8501

python -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501 --server.headless true
