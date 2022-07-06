cd main
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" -kiosk -fullscreen https:127.0.0.1:443
start "" pipenv run app.py

