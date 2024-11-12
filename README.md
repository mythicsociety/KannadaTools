### To create environment and install packages

To create your virtual environment, go into your project and run:
python -m venv .venv

Once the command is finished, your virtual environment will be ready. Next, you can "activate" it by running the activation script.
.\.venv\Scripts\activate 

Once activated, you will see the name of the environment within the terminal.

Now, you will be able to install packages and run Python within the environment without interfering with packages installed globally.

pip install -r requirements.txt

Once you are finished, just use the deactivate command to exit the virtual environment.
.\.venv\Scripts\deactivate 

use pip freeze > requirements.txt to automatically take the packages list and store it in requirements.txt file.

### To launch streamlit app
streamlit run .\misread_letter.py

### To launch uvicorn with swagger API
uvicorn main:app --reload

Browse to http://127.0.0.1:8000/docs#/default to view available APIs