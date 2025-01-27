@echo off
echo creating virtual environment...
python -m venv venv
echo virutal environment created!
echo running virutal environment...
call venv\Scripts\activate
echo isntalling dependencies
pip install -r requirements.txt
pause