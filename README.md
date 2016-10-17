errbot chatwork backend
=======================

# install
    git clone https://github.com/youske/errbot-backend-chatwork.git

# support
using chatwork API me, room, messages


# configulation
 
    config.py

    CHATWORK_IDENTITY = {
      'token':'xxxxxxxxxx' 
    }
   
    CHATWORK_SETTINGS = {
    }  

    Example. environment variables
    
    export CHATWORK_API_TOKEN=xxxxxxxxxxxx


    config.py
    CHATWORK_IDENTITY = {
    	"token": os.environ.get('CHATWORK_API_TOKEN')
    }



# development 
    pyenv install 3.5.2
    pyenv virtualenv 3.5.2 mybotproject
    cd mybotproject
    pyenv local mybotproject
   
    pip install errbot

    git clone errobot-backend-chatwork.git

    config.py
    EXTRA_BACKEND_DIR=<git repository directory>


# etc

chatwork api document

http://developer.chatwork.com/ja/endpoints.html
