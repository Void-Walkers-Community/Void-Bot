from dotenv import load_dotenv
import os
 
load_dotenv()
 
TOKEN = os.environ["TOKEN"]
PREFIX = "!"
 
APPLICATION_CHANNEL_ID = int(os.environ["APPLICATION_CHANNEL_ID"])
PROOF_LOG_CHANNEL_ID   = int(os.environ["PROOF_LOG_CHANNEL_ID"])
AUDIT_LOG_CHANNEL_ID   = int(os.environ["AUDIT_LOG_CHANNEL_ID"])