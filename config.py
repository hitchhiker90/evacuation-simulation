# COMP702 - Evacuation Simulation
# Lukasz Przybyla

import os
from datetime import datetime

# A global variable that prevents premature initialization
serverReady = False

# Current directory
CURRENT_DIR = os.getcwd()

# Log file path
logFilePath = CURRENT_DIR + '/logs/log ' + str(datetime.now())[:13] + '-'\
                                           + str(datetime.now())[14:16] + '-'\
                                           + str(datetime.now())[17:19] + '.txt'